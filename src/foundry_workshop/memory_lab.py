import json
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from .contracts import digest, load_cases, read_json, safe_label, write_json
from .settings import Settings, owned_prefix, require_env


def store_name(settings: Settings) -> str:
    return f"{owned_prefix()}-memory-{settings.language}"


def scope_name(settings: Settings, scope: str) -> str:
    if scope not in {"alpha", "beta"}:
        raise ValueError("Use one of the two synthetic scope labels: alpha or beta.")
    return f"{owned_prefix()}-{settings.language}-{scope}"


def ownership_path(root: Path, settings: Settings) -> Path:
    return root / "outputs/memory" / store_name(settings) / "ownership.json"


def plan(settings: Settings) -> dict[str, Any]:
    return {
        "mode": "local-memory-plan",
        "name": store_name(settings),
        "project_endpoint": settings.project_endpoint,
        "chat_model": settings.deployment,
        "embedding_model": require_env("AZURE_AI_EMBEDDING_DEPLOYMENT_NAME"),
        "default_ttl_seconds": 3600,
        "scopes": [scope_name(settings, scope) for scope in ("alpha", "beta")],
        "azure_requests_sent": False,
        "note": "Synthetic scope partitioning is not an authorization test between two real users.",
    }


def load_ownership(root: Path, settings: Settings) -> dict[str, Any]:
    path = ownership_path(root, settings)
    if not path.is_file():
        raise ValueError("Create this owned memory store from the same workshop copy first.")
    value = read_json(path)
    expected = plan(settings)
    if value.get("plan") != expected or not isinstance(value.get("items"), dict):
        raise ValueError("The memory ownership/configuration changed.")
    return value


def verify_absent(read: Callable[[], Any], message: str) -> None:
    from azure.core.exceptions import ResourceNotFoundError

    deadline = time.monotonic() + 10
    while True:
        try:
            read()
        except ResourceNotFoundError:
            return
        if time.monotonic() >= deadline:
            raise ValueError(message)
        time.sleep(1)


def verify_store(project: Any, settings: Settings, ownership: dict[str, Any]) -> dict[str, Any]:
    actual = project.beta.memory_stores.get(name=store_name(settings)).as_dict()
    if (
        actual.get("name") != store_name(settings)
        or (actual.get("metadata") or {}).get("workshop_owner") != ownership["owner"]
    ):
        raise ValueError(
            "The current memory store does not match this workshop's ownership marker."
        )
    definition = actual.get("definition", {})
    if (
        definition.get("chat_model") != settings.deployment
        or definition.get("embedding_model") != require_env("AZURE_AI_EMBEDDING_DEPLOYMENT_NAME")
        or definition.get("options", {}).get("default_ttl_seconds") != 3600
    ):
        raise ValueError(
            "Memory model bindings or retention changed; do not silently accept drift."
        )
    return actual


def create(project: Any, root: Path, settings: Settings, *, confirmed: bool) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("Creating a memory store requires --confirm-create.")
    from azure.ai.projects.models import MemoryStoreDefaultDefinition, MemoryStoreDefaultOptions
    from azure.core.exceptions import ResourceNotFoundError

    configuration = plan(settings)
    path = ownership_path(root, settings)
    if path.exists():
        raise ValueError("Preserve the existing memory ownership record; use a new prefix.")
    next(iter(project.agents.list(limit=1)), None)
    try:
        project.beta.memory_stores.get(name=store_name(settings))
    except ResourceNotFoundError:
        pass
    else:
        raise ValueError("The memory store name already exists; do not adopt or overwrite it.")
    owner = str(uuid4())
    result = project.beta.memory_stores.create(
        name=store_name(settings),
        description="Synthetic workshop memory scopes only; no real user or company data.",
        definition=MemoryStoreDefaultDefinition(
            chat_model=configuration["chat_model"],
            embedding_model=configuration["embedding_model"],
            options=MemoryStoreDefaultOptions(
                user_profile_enabled=True,
                chat_summary_enabled=False,
                procedural_memory_enabled=False,
                default_ttl_seconds=timedelta(hours=1),
            ),
        ),
        metadata={"workshop_owner": owner, "language": settings.language},
    )
    ownership = {"plan": configuration, "owner": owner, "created": result.as_dict(), "items": {}}
    write_json(path, ownership)
    return {
        "mode": "live-memory-store-created",
        "store": verify_store(project, settings, ownership),
        "ledger": str(path),
        "memory_items_created": False,
        "ttl_expiry_tested": False,
    }


def content_for(root: Path, settings: Settings, case_id: str, marker: str) -> str:
    cases = {case["case_id"]: case for case in load_cases(root, "dev", settings.language)}
    if case_id not in {"D01", "D02"}:
        raise ValueError(
            "Use D01 or D02 from the bundled dev set; no holdout or arbitrary personal data."
        )
    prefix = "Synthetic exercise marker" if settings.language == "en" else "합성 실습 표식"
    return f"{prefix} {marker}. {cases[case_id]['question']}"


def put(
    project: Any,
    root: Path,
    settings: Settings,
    scope: str,
    case_id: str,
    *,
    confirmed_write: bool,
    confirmed_cost: bool,
    memory_id: str | None = None,
) -> dict[str, Any]:
    if not confirmed_write or not confirmed_cost:
        raise ValueError(
            "Memory writes may use the configured models; pass --confirm-write --confirm-cost."
        )
    ownership = load_ownership(root, settings)
    verify_store(project, settings, ownership)
    scoped = scope_name(settings, scope)
    if memory_id is not None:
        original = ownership["items"].get(memory_id)
        if not original or original.get("deleted") or original["scope"] != scoped:
            raise ValueError("Only a live item owned in this synthetic scope can be updated.")
        marker = original["marker"]
    else:
        marker = str(uuid4())
    content = content_for(root, settings, case_id, marker)
    if memory_id is None:
        item = project.beta.memory_stores.create_memory(
            name=store_name(settings), scope=scoped, content=content, kind="user_profile"
        )
        memory_id = item.memory_id
    else:
        item = project.beta.memory_stores.update_memory(
            name=store_name(settings), memory_id=memory_id, content=content
        )
    ownership["items"][memory_id] = {
        "scope": scoped,
        "case_id": case_id,
        "marker": marker,
        "content": content,
        "content_hash": digest(content),
        "deleted": False,
        "write_response": item.as_dict(),
    }
    write_json(ownership_path(root, settings), ownership)
    from azure.core.exceptions import ResourceNotFoundError

    deadline = time.monotonic() + 10
    while True:
        try:
            actual = project.beta.memory_stores.get_memory(
                name=store_name(settings), memory_id=memory_id
            ).as_dict()
        except ResourceNotFoundError:
            actual = None
        if actual is not None:
            if actual.get("scope") != scoped:
                raise ValueError("The actual memory item has a different scope.")
            if actual.get("content") == content:
                break
        if time.monotonic() >= deadline:
            raise ValueError(
                "The acknowledged memory write is not yet readable as requested; keep its recorded ID and do not create another item."
            )
        time.sleep(1)
    return {
        "mode": "live-memory-item",
        "item": actual,
        "case_id": case_id,
        "content_hash": digest(content),
    }


def inspect_scope(project: Any, root: Path, settings: Settings, scope: str) -> dict[str, Any]:
    ownership = load_ownership(root, settings)
    verify_store(project, settings, ownership)
    scoped = scope_name(settings, scope)
    items = [
        item.as_dict()
        for item in project.beta.memory_stores.list_memories(
            name=store_name(settings), scope=scoped
        )
    ]
    if any(item.get("scope") != scoped for item in items):
        raise ValueError("The service returned a memory from a different requested scope.")
    return {
        "mode": "read-only-memory-items",
        "scope": scoped,
        "items": items,
        "note": "The same authorized operator can select either synthetic scope; this is not proof of user authorization.",
    }


def recall(
    project: Any,
    client: Any,
    root: Path,
    settings: Settings,
    scope: str,
    label: str,
    *,
    confirmed: bool,
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("Memory search and the following model request require --confirm-cost.")
    ownership = load_ownership(root, settings)
    verify_store(project, settings, ownership)
    scoped = scope_name(settings, scope)
    directory = root / "outputs/memory-runs" / safe_label(label)
    directory.mkdir(parents=True, exist_ok=False)
    question = (
        "What synthetic exercise marker and study question have I stored? Quote the remembered content. If no memory is available, say that you do not know."
        if settings.language == "en"
        else "저장해 둔 합성 실습 표식과 학습 질문은 무엇인가요? 기억된 내용을 인용하고 기억이 없으면 모른다고 답하세요."
    )
    request = {"name": store_name(settings), "scope": scoped, "items": question}
    write_json(directory / "request.json", request)
    result = project.beta.memory_stores.search_memories(**request).as_dict()
    write_json(directory / "search.json", result)
    memories = result.get("memories")
    if not isinstance(memories, list) or any(
        not isinstance(match, dict)
        or not isinstance(match.get("memory_item"), dict)
        or match["memory_item"].get("scope") != scoped
        for match in memories
    ):
        raise ValueError(
            "Memory search must preserve the current memories collection and requested scope."
        )
    active = {
        key: item
        for key, item in ownership["items"].items()
        if item["scope"] == scoped and not item["deleted"]
    }
    retrieved = [match["memory_item"] for match in memories]
    for item in retrieved:
        if (
            item.get("memory_id") not in active
            or item.get("content") != active[item["memory_id"]]["content"]
        ):
            raise ValueError(
                "Memory search returned unowned, changed or deleted synthetic content."
            )
    if active and not retrieved:
        raise ValueError(
            "A written synthetic memory was not retrieved. Preserve the empty result; do not invent recall."
        )
    instructions = (
        "Respond in English using only the supplied synthetic memory records. Do not invent a marker, infer another user's context, or perform an external action."
        if settings.language == "en"
        else "제공된 합성 기억만 사용해 한국어로 답하세요. 표식을 만들어 내거나 다른 scope의 내용을 추측하거나 외부 작업을 실행하지 않습니다."
    )
    response = client.responses.create(
        model=settings.deployment,
        instructions=instructions,
        input=json.dumps({"question": question, "memories": retrieved}, ensure_ascii=False),
        max_output_tokens=settings.max_output_tokens,
        store=False,
    )
    write_json(directory / "response.json", response.model_dump(mode="json"))
    from .cloud import response_metadata

    metadata = response_metadata(response)
    wrong_markers = [
        item["marker"]
        for item in ownership["items"].values()
        if item["scope"] != scoped and item["marker"] in response.output_text
    ]
    if wrong_markers:
        raise ValueError("The answer repeated a marker from another synthetic scope.")
    summary = {
        "mode": "live-api-backed-memory-recall",
        "language": settings.language,
        "scope": scoped,
        "retrieved_memory_ids": [item["memory_id"] for item in retrieved],
        "search_id": result.get("search_id"),
        "search_usage": result.get("usage"),
        "answer": response.output_text,
        **metadata,
        "native_agent_memory_tool_used": False,
        "input_hash": digest(request),
        "search_hash": digest(result),
        "instructions_hash": digest(instructions),
        "recorded_at": datetime.now(UTC).isoformat(),
        "note": "A fresh stateless model call receives actual managed-memory API results. No automatic memory extraction or real-user authorization test.",
    }
    write_json(directory / "summary.json", summary)
    return summary


def forget(
    project: Any, root: Path, settings: Settings, memory_id: str, *, confirmed: bool
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("Forgetting the owned memory item requires --confirm-delete.")
    from azure.core.exceptions import ResourceNotFoundError

    ownership = load_ownership(root, settings)
    verify_store(project, settings, ownership)
    item = ownership["items"].get(memory_id)
    if not item or item.get("deleted"):
        raise ValueError("Only a live item in the local ownership record can be deleted.")
    try:
        project.beta.memory_stores.get_memory(name=store_name(settings), memory_id=memory_id)
    except ResourceNotFoundError:
        item.update(
            deleted=True,
            delete_requested=False,
            absence_confirmed_at=datetime.now(UTC).isoformat(),
            absence_cause="not-attributed",
        )
        write_json(ownership_path(root, settings), ownership)
        return {
            "memory_id": memory_id,
            "delete_requested": False,
            "already_absent": True,
            "verified_absent": True,
            "note": "The item was absent before deletion (for example after retention). No new delete is claimed.",
        }
    deleted = project.beta.memory_stores.delete_memory(
        name=store_name(settings), memory_id=memory_id
    )
    item.update(
        delete_requested=True,
        delete_response=deleted.as_dict(),
        delete_requested_at=datetime.now(UTC).isoformat(),
    )
    write_json(ownership_path(root, settings), ownership)
    verify_absent(
        lambda: project.beta.memory_stores.get_memory(
            name=store_name(settings), memory_id=memory_id
        ),
        "The requested memory deletion is not yet verified; preserve the receipt rather than repeat the delete.",
    )
    item["deleted"] = True
    item["deleted_at"] = datetime.now(UTC).isoformat()
    write_json(ownership_path(root, settings), ownership)
    return {
        "memory_id": memory_id,
        "deleted": True,
        "delete_requested": True,
        "verified_absent": True,
    }


def cleanup(project: Any, root: Path, settings: Settings, *, confirmed: bool) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("Deleting the dedicated memory store requires --confirm-delete.")
    ownership = load_ownership(root, settings)
    verify_store(project, settings, ownership)
    if any(not item["deleted"] for item in ownership["items"].values()):
        raise ValueError("Forget the owned items first and inspect both synthetic scopes.")
    if any(inspect_scope(project, root, settings, scope)["items"] for scope in ("alpha", "beta")):
        raise ValueError("Unexpected memory items remain; review before deleting the store.")
    deleted = project.beta.memory_stores.delete(name=store_name(settings))
    write_json(ownership_path(root, settings).with_name("cleanup-request.json"), deleted.as_dict())
    verify_absent(
        lambda: project.beta.memory_stores.get(name=store_name(settings)),
        "The requested memory store deletion is not yet verified.",
    )
    result = {"store_name": store_name(settings), "deleted": True, "verified_absent": True}
    write_json(ownership_path(root, settings).with_name("cleanup.json"), result)
    return result
