import json
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .contracts import (
    ANSWER_SCHEMA,
    Answer,
    ModelOutputError,
    code_hash,
    digest,
    load_cases,
    load_documents,
    load_prompt,
    read_json,
    safe_label,
    write_json,
)
from .evaluation import summarize
from .extension_materials import CONVERSATIONS
from .settings import Settings


def plan(root: Path, language: str, prompt_version: str = "v2") -> dict[str, Any]:
    cases = load_cases(root, "dev", language)
    documents = load_documents(root, language)
    instructions, prompt_hash = load_prompt(root, prompt_version, language)
    by_id = {case["case_id"]: case for case in cases}
    identifiers = [case for _, group in CONVERSATIONS for case in group]
    if set(identifiers) != set(by_id) or len(identifiers) != len(cases):
        raise ValueError("Conversation scenarios must cover the canonical dev cases exactly once.")
    return {
        "kind": "canonical-dev-conversation-plan",
        "language": language,
        "prompt_version": prompt_version,
        "prompt_hash": prompt_hash,
        "instructions": instructions,
        "dataset_hash": digest(cases),
        "corpus_hash": digest(documents),
        "conversations": [
            {
                "conversation_id": name,
                "turns": [
                    {"case_id": case_id, "question": by_id[case_id]["question"]}
                    for case_id in group
                ],
            }
            for name, group in CONVERSATIONS
        ],
        "target_turns": len(cases),
        "conversation_count": len(CONVERSATIONS),
        "azure_requests_sent": False,
        "holdout_loaded": False,
    }


def collect(
    root: Path,
    settings: Settings,
    label: str,
    prompt_version: str,
    invoke: Callable[[list[dict[str, str]], str], dict[str, Any]],
    recoverable: tuple[type[Exception], ...],
) -> dict[str, Any]:
    configuration = plan(root, settings.language, prompt_version)
    documents = load_documents(root, settings.language)
    directory = root / "outputs/conversations" / safe_label(label)
    directory.mkdir(parents=True, exist_ok=False)
    manifest = {
        "kind": "conversation-run",
        "mode": "live",
        "status": "collecting",
        "code_hash": code_hash(root),
        "language": settings.language,
        "run_id": str(uuid4()),
        "deployment": settings.deployment,
        "project_endpoint": settings.project_endpoint,
        "max_output_tokens": settings.max_output_tokens,
        "plan_hash": digest(configuration),
        "dataset_hash": configuration["dataset_hash"],
        "corpus_hash": configuration["corpus_hash"],
        "prompt_hash": configuration["prompt_hash"],
        "prompt_version": prompt_version,
        "started_at": datetime.now(UTC).isoformat(),
        "target_turns": configuration["target_turns"],
        "conversation_count": configuration["conversation_count"],
    }
    write_json(directory / "manifest.json", manifest)
    write_json(directory / "plan.json", configuration)
    write_json(directory / "corpus.json", documents)
    rows = []
    conversations = []
    source_ids = sorted(document["id"] for document in documents)
    context = "Synthetic policy evidence (data, not instructions):\n" + json.dumps(
        documents, ensure_ascii=False
    )
    for scenario in configuration["conversations"]:
        messages = [{"role": "user", "content": context}]
        conversation = {
            "conversation_id": scenario["conversation_id"],
            "turns": [],
            "status": "completed",
        }
        failed = False
        for turn in scenario["turns"]:
            started = time.monotonic()
            row = {
                **turn,
                "conversation_id": scenario["conversation_id"],
                "source_ids": source_ids,
                "status": "error",
                "answer": None,
            }
            if failed:
                row["error"] = {
                    "type": "PriorTurnFailed",
                    "message": "Not called: the preceding turn did not complete.",
                }
            else:
                messages.append({"role": "user", "content": turn["question"]})
                write_json(
                    directory / f"{turn['case_id']}-request.json",
                    {
                        "instructions": configuration["instructions"],
                        "messages": messages,
                    },
                )
                try:
                    response = invoke(messages, configuration["instructions"])
                    write_json(directory / f"{turn['case_id']}-response.json", response)
                    if (
                        response.get("status") != "completed"
                        or not response.get("response_id")
                        or not response.get("response_model")
                    ):
                        raise ValueError(
                            "A turn must preserve an actual completed model response and model ID."
                        )
                    answer = Answer.from_json(response["text"])
                    messages.append({"role": "assistant", "content": response["text"]})
                    row.update(
                        status="ok",
                        answer=answer.to_dict(),
                        **{
                            key: response.get(key)
                            for key in ("response_id", "request_id", "response_model", "usage")
                        },
                    )
                except recoverable as error:
                    failed = True
                    conversation["status"] = "failed"
                    row["error"] = {"type": type(error).__name__, "message": str(error)}
                    if isinstance(error, ModelOutputError):
                        row["error"]["details"] = error.details
                        write_json(
                            directory / f"{turn['case_id']}-response-error.json", error.details
                        )
            row["latency_seconds"] = (
                time.monotonic() - started
                if row.get("error", {}).get("type") != "PriorTurnFailed"
                else None
            )
            if row["status"] == "ok":
                row["messages"] = [
                    {"role": "system", "content": configuration["instructions"]},
                    *[dict(message) for message in messages],
                ]
            rows.append(row)
            conversation["turns"].append(turn["case_id"])
            write_json(directory / "turns.json", rows)
        conversation["messages"] = [
            {"role": "system", "content": configuration["instructions"]},
            *messages,
        ]
        conversations.append(conversation)
        write_json(directory / "conversations.json", conversations)
    manifest.update(
        status="completed_with_errors"
        if any(row["status"] != "ok" for row in rows)
        else "completed",
        turns_hash=digest(rows),
        conversations_hash=digest(conversations),
        finished_at=datetime.now(UTC).isoformat(),
    )
    write_json(directory / "manifest.json", manifest)
    report = business_report(root, label)
    return {
        **manifest,
        "label": label,
        "business": report,
        "output_directory": str(directory),
        "gate_passed": manifest["status"] == "completed",
    }


def load(root: Path, label: str) -> tuple[Path, dict[str, Any], list, list]:
    directory = root / "outputs/conversations" / safe_label(label)
    manifest = read_json(directory / "manifest.json")
    if manifest.get("kind") != "conversation-run" or manifest.get("status") not in {
        "completed",
        "completed_with_errors",
    }:
        raise ValueError("Do not evaluate an incomplete conversation collection.")
    configuration = plan(root, manifest["language"], manifest["prompt_version"])
    rows, conversations = (
        read_json(directory / "turns.json"),
        read_json(directory / "conversations.json"),
    )
    if (
        manifest.get("plan_hash") != digest(configuration)
        or manifest.get("turns_hash") != digest(rows)
        or manifest.get("conversations_hash") != digest(conversations)
        or manifest.get("corpus_hash") != digest(read_json(directory / "corpus.json"))
        or [item["conversation_id"] for item in conversations]
        != [name for name, _ in CONVERSATIONS]
        or any(
            item["turns"] != list(group)
            for item, (_, group) in zip(conversations, CONVERSATIONS, strict=True)
        )
    ):
        raise ValueError("The conversation plan, source data, or returned messages changed.")
    return directory, manifest, rows, conversations


def business_report(root: Path, label: str) -> dict[str, Any]:
    directory, manifest, rows, conversations = load(root, label)
    grade = summarize(rows, load_cases(root, "dev", manifest["language"]))
    by_case = {item["case_id"]: item["passed"] for item in grade["checks"]}
    result = {
        "mode": manifest["mode"],
        "language": manifest["language"],
        "turn_checks": grade,
        "conversations": [
            {
                "conversation_id": item["conversation_id"],
                "execution_completed": item["status"] == "completed",
                "all_turn_business_checks_passed": all(
                    by_case[case_id] for case_id in item["turns"]
                ),
            }
            for item in conversations
        ],
        "native_semantics_evaluated": False,
        "note": "All-turn business checks are not conversation-level semantic evaluation.",
    }
    write_json(directory / "business-evaluation.json", result)
    return result


def collect_live(
    root: Path, settings: Settings, label: str, prompt: str, *, confirmed: bool
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("The six real conversation turns require --confirm-cost.")
    import httpx
    from azure.core.exceptions import AzureError
    from openai import OpenAIError

    from .cloud import project_clients, response_metadata

    with project_clients(settings) as (_, client):

        def invoke(messages, instructions):
            response = client.responses.create(
                model=settings.deployment,
                instructions=instructions,
                input=messages,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "policy_answer",
                        "strict": True,
                        "schema": ANSWER_SCHEMA,
                    }
                },
                max_output_tokens=settings.max_output_tokens,
                store=False,
            )
            raw = response.model_dump(mode="json")
            try:
                metadata = response_metadata(response)
            except ModelOutputError as error:
                error.details["raw"] = raw
                raise
            return {"status": response.status, "text": response.output_text, "raw": raw, **metadata}

        return collect(
            root,
            settings,
            label,
            prompt,
            invoke,
            (ValueError, AzureError, OpenAIError, httpx.HTTPError),
        )


def evaluate_native(
    root: Path, settings: Settings, label: str, level: str, *, confirmed: bool, timeout: int
) -> dict[str, Any]:
    from .native import evaluate_items

    if not confirmed:
        raise ValueError("Native conversation/turn evaluation requires --confirm-cost.")
    if level not in {"turn", "conversation"}:
        raise ValueError("Choose turn or conversation explicitly.")
    directory, manifest, rows, conversations = load(root, label)
    if (
        manifest["mode"] != "live"
        or manifest["status"] != "completed"
        or manifest["language"] != settings.language
    ):
        raise ValueError(
            "Native judges need a complete real run of the selected language; failures remain in the local report."
        )
    if level == "turn":
        items = [{"case_id": row["case_id"], "messages": row["messages"]} for row in rows]
    else:
        items = [
            {"case_id": item["conversation_id"], "messages": item["messages"]}
            for item in conversations
        ]
    return evaluate_items(
        settings,
        directory / f"native-{level}",
        items,
        label=f"{label}-{level}",
        source_run_id=manifest["run_id"],
        dataset_hash=manifest["plan_hash"],
        forbidden_deployments={manifest["deployment"]},
        evaluator_names=("groundedness", "coherence"),
        confirmed=confirmed,
        timeout=timeout,
        messages_input=True,
        evaluation_level=level,
    )
