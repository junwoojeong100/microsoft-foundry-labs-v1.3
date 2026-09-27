import csv
import hashlib
import io
from pathlib import Path, PurePosixPath
from typing import Any

from .contracts import digest, load_documents, read_json, safe_label, write_json
from .extension_materials import files_for
from .settings import Settings, owned_prefix


def generated_csv_citation(raw: dict[str, Any]) -> dict[str, str]:
    calls = [item for item in raw.get("output", []) if item.get("type") == "code_interpreter_call"]
    if not calls or any(call.get("status") != "completed" for call in calls):
        raise ValueError("An actual completed Code Interpreter call is required.")
    containers = {
        call.get("container_id") for call in calls if isinstance(call.get("container_id"), str)
    }
    citations = [
        annotation
        for item in raw.get("output", [])
        if item.get("type") == "message"
        for content in item.get("content", [])
        if content.get("type") == "output_text"
        for annotation in content.get("annotations", [])
        if annotation.get("type") == "container_file_citation"
        and isinstance(annotation.get("filename"), str)
        and PurePosixPath(annotation["filename"]).name == "policy-summary.csv"
        and annotation.get("container_id") in containers
        and isinstance(annotation.get("file_id"), str)
        and annotation["file_id"]
    ]
    if len(citations) != 1:
        raise ValueError(
            "Expected exactly one policy-summary.csv citation from the actual code container."
        )
    return {key: citations[0][key] for key in ("file_id", "container_id", "filename")}


def validate_csv(content: bytes, documents: list[dict[str, Any]]) -> list[dict[str, str]]:
    if len(content) > 1_048_576:
        raise ValueError("The six-row generated CSV exceeds the workshop artifact limit.")
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    if reader.fieldnames != ["id", "title"]:
        raise ValueError("The generated CSV must contain exactly id,title columns.")
    rows = list(reader)
    expected = [{"id": item["id"], "title": item["title"]} for item in documents]
    if rows != expected:
        raise ValueError(
            "The generated CSV changed, omitted, reordered or duplicated canonical policy rows."
        )
    return rows


def run(
    project: Any,
    client: Any,
    root: Path,
    settings: Settings,
    label: str,
    *,
    confirmed_create: bool,
    confirmed_cost: bool,
) -> dict[str, Any]:
    if not confirmed_create or not confirmed_cost:
        raise ValueError(
            "Uploading synthetic data and using Code Interpreter requires --confirm-create --confirm-cost."
        )
    from azure.ai.projects.models import (
        AutoCodeInterpreterToolParam,
        CodeInterpreterTool,
        PromptAgentDefinition,
    )
    from azure.core.exceptions import ResourceNotFoundError

    from .cloud import response_metadata, response_with_payload

    directory = root / "outputs/code-interpreter" / safe_label(label)
    directory.mkdir(parents=True, exist_ok=False)
    name = f"{owned_prefix()}-code-{settings.language}-{digest(label)[:8]}"
    ownership = {
        "project_endpoint": settings.project_endpoint,
        "name": name,
        "version": None,
        "file_id": None,
        "container_ids": [],
        "language": settings.language,
    }
    write_json(directory / "ownership.json", ownership)
    try:
        project.agents.get(agent_name=name)
    except ResourceNotFoundError:
        pass
    else:
        raise ValueError("The dedicated Code Interpreter agent name already exists.")
    data = files_for(root, settings.language, owned_prefix())["policy-records.csv"]
    (directory / "policy-records.csv").write_bytes(data)
    upload = client.files.create(
        purpose="assistants",
        file=("policy-records.csv", io.BytesIO(data), "text/csv"),
    )
    ownership["file_id"] = upload.id
    write_json(directory / "ownership.json", ownership)
    agent = project.agents.create_version(
        agent_name=name,
        definition=PromptAgentDefinition(
            model=settings.deployment,
            instructions="Use Code Interpreter only on the supplied synthetic CSV. Do not access the network, install packages, or perform business actions. Preserve every input row exactly.",
            tools=[
                CodeInterpreterTool(container=AutoCodeInterpreterToolParam(file_ids=[upload.id]))
            ],
        ),
    )
    ownership["version"] = agent.version
    write_json(directory / "ownership.json", ownership)
    question = (
        "Read policy-records.csv with Code Interpreter. Create policy-summary.csv with exactly id,title columns and all six original rows in their original order. Provide the generated CSV download link. Do not change the text or invent rows."
        if settings.language == "en"
        else "Code Interpreter로 policy-records.csv를 읽으세요. id,title 열만 포함하고 원래 순서의 6행을 그대로 가진 policy-summary.csv를 생성해 다운로드 링크를 주세요. 내용을 바꾸거나 행을 만들지 마세요."
    )
    request = {
        "input": question,
        "tool_choice": "required",
        "store": False,
        "extra_body": {
            "agent_reference": {"type": "agent_reference", "name": name, "version": agent.version}
        },
    }
    write_json(directory / "request.json", request)
    response, raw = response_with_payload(
        client, error_path=directory / "service-error.json", **request
    )
    write_json(directory / "response.json", raw)
    ownership["container_ids"] = sorted(
        {
            item["container_id"]
            for item in raw.get("output", [])
            if item.get("type") == "code_interpreter_call"
            and isinstance(item.get("container_id"), str)
            and item["container_id"]
        }
    )
    write_json(directory / "ownership.json", ownership)
    citation = generated_csv_citation(raw)
    result_file = client.containers.files.content.retrieve(
        file_id=citation["file_id"], container_id=citation["container_id"]
    )
    content = result_file.read()
    (directory / "policy-summary.csv").write_bytes(content)
    rows = validate_csv(content, load_documents(root, settings.language))
    result = {
        "mode": "live-code-interpreter",
        "language": settings.language,
        "agent_name": name,
        "agent_version": agent.version,
        "source_file_id": upload.id,
        "generated_file": citation,
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "generated_sha256": hashlib.sha256(content).hexdigest(),
        "verified_rows": len(rows),
        "answer": response.output_text,
        **response_metadata(response),
        "note": "Actual code execution and generated-file verification, not policy-answer quality or zero-cost execution.",
    }
    write_json(directory / "summary.json", result)
    return result


def cleanup(
    project: Any, client: Any, root: Path, settings: Settings, label: str, *, confirmed: bool
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("Owned agent/file/container cleanup requires --confirm-delete.")
    directory = root / "outputs/code-interpreter" / safe_label(label)
    ownership = read_json(directory / "ownership.json")
    expected = f"{owned_prefix()}-code-{settings.language}-{digest(label)[:8]}"
    if (
        ownership.get("project_endpoint") != settings.project_endpoint
        or ownership.get("name") != expected
    ):
        raise ValueError("The Code Interpreter ownership record does not match this project/name.")
    from azure.core.exceptions import ResourceNotFoundError
    from openai import NotFoundError

    if ownership["version"]:
        versions = [item.version for item in project.agents.list_versions(agent_name=expected)]
        if versions != [ownership["version"]]:
            raise ValueError("Other agent versions exist; do not delete shared work.")
        project.agents.delete(agent_name=expected)
        try:
            project.agents.get(agent_name=expected)
        except ResourceNotFoundError:
            pass
        else:
            raise ValueError("The owned temporary agent remains after deletion.")
    for container_id in ownership["container_ids"]:
        client.containers.delete(container_id)
        try:
            client.containers.retrieve(container_id)
        except NotFoundError:
            pass
        else:
            raise ValueError("The owned code container remains after deletion.")
    if ownership["file_id"]:
        deleted = client.files.delete(ownership["file_id"])
        if deleted.deleted is not True:
            raise ValueError("The uploaded source file deletion was not confirmed.")
        try:
            client.files.retrieve(ownership["file_id"])
        except NotFoundError:
            pass
        else:
            raise ValueError("The uploaded synthetic source remains after deletion.")
    result = {
        "cleanup_requested_for": ownership,
        "local_evidence_retained": True,
        "shared_project_or_models_deleted": False,
        "verified_absent": True,
        "note": "Owned object absence is verified; delayed/residual billing still needs separate review.",
    }
    write_json(directory / "cleanup.json", result)
    return result
