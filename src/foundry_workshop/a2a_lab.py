from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .compatibility import A2A_PROTOCOL
from .contracts import Answer, digest, load_documents, read_json, safe_label, write_json
from .settings import Settings, owned_prefix


def names(settings: Settings) -> dict[str, str]:
    prefix = owned_prefix()
    return {
        "target": f"{prefix}-a2a-target-{settings.language}",
        "caller": f"{prefix}-a2a-caller-{settings.language}",
        "connection": f"{prefix}-a2a-link-{settings.language}",
    }


def base_path(settings: Settings) -> str:
    return f"{settings.project_endpoint}/agents/{names(settings)['target']}/endpoint/protocols/a2a"


def ledger_path(root: Path, settings: Settings) -> Path:
    return root / "outputs/a2a" / names(settings)["target"] / "ownership.json"


def load_ownership(root: Path, settings: Settings) -> dict[str, Any]:
    path = ledger_path(root, settings)
    if not path.is_file():
        raise ValueError("Create this owned A2A target in the same workshop copy first.")
    value = read_json(path)
    if value.get("project_endpoint") != settings.project_endpoint or value.get("names") != names(
        settings
    ):
        raise ValueError("The A2A ownership record belongs to another project or prefix.")
    return value


def incoming_patch() -> dict[str, Any]:
    return {
        "agent_card": {
            "description": "Read-only guidance from six bundled synthetic travel policies. No booking, payment or approval.",
            "version": "1.0",
            "skills": [
                {
                    "id": "synthetic-policy",
                    "name": "Synthetic policy guidance",
                    "description": "Explain dates, limits, citations and prior approval requirements.",
                }
            ],
        },
        "agent_endpoint": {"protocol_configuration": {"responses": {}, "a2a": {}}},
    }


def incoming_update() -> dict[str, Any]:
    """Typed SDK arguments whose merge-patch body must equal incoming_patch()."""
    from azure.ai.projects.models import (
        A2AProtocolConfiguration,
        AgentCard,
        AgentCardSkill,
        AgentEndpointConfig,
        ProtocolConfiguration,
        ResponsesProtocolConfiguration,
    )

    card = incoming_patch()["agent_card"]
    return {
        "agent_card": AgentCard(
            description=card["description"],
            version=card["version"],
            skills=[AgentCardSkill(**skill) for skill in card["skills"]],
        ),
        "agent_endpoint": AgentEndpointConfig(
            protocol_configuration=ProtocolConfiguration(
                responses=ResponsesProtocolConfiguration(), a2a=A2AProtocolConfiguration()
            )
        ),
    }


def caller_definition(settings: Settings, instructions: str, connection_id: str) -> Any:
    from azure.ai.projects.models import A2AProtocolVersion, A2ATool, PromptAgentDefinition

    return PromptAgentDefinition(
        model=settings.deployment,
        instructions=instructions,
        tools=[
            A2ATool(
                project_connection_id=connection_id,
                a2a_version=A2AProtocolVersion.V1_0,
                send_credentials_for_agent_card=True,
            )
        ],
    )


def select_v1_interface(card: dict[str, Any], expected_url: str) -> dict[str, str]:
    interfaces = card.get("supportedInterfaces")
    if not isinstance(interfaces, list):
        raise ValueError("The actual A2A 1.0 card must expose supportedInterfaces.")
    selected = [
        item
        for item in interfaces
        if isinstance(item, dict)
        and item.get("protocolVersion") == "1.0"
        and item.get("protocolBinding") == "JSONRPC"
        and item.get("url") == expected_url
    ]
    if len(selected) != 1:
        raise ValueError(
            "The actual card has no unique matching A2A 1.0 JSONRPC interface; do not downgrade."
        )
    return {key: selected[0][key] for key in ("url", "protocolVersion", "protocolBinding")}


def card_request(project: Any, settings: Settings, path: str) -> dict:
    """GET the A2A protocol card; the management routes use typed SDK methods instead."""
    from azure.core.exceptions import HttpResponseError
    from azure.core.rest import HttpRequest

    if not path.startswith("/agents/") or "?" in path or ".." in path:
        raise ValueError("A2A requests must stay on the intended project agent path.")
    request = HttpRequest(
        "GET",
        settings.project_endpoint + path,
        headers={"A2A-Version": A2A_PROTOCOL.version},
    )
    response = project.send_request(request)
    if response.status_code != 200:
        raise HttpResponseError(
            message=f"A2A GET failed with HTTP {response.status_code}; no protocol downgrade.",
            response=response,
        )
    return response.json()


def plan(settings: Settings) -> dict[str, Any]:
    return {
        "mode": "local-a2a-plan",
        "names": names(settings),
        "target_base": base_path(settings),
        "card_url": base_path(settings) + "/agentCard/v1.0",
        "protocol": "1.0",
        "transport": "JSONRPC",
        "incoming_patch": incoming_patch(),
        "azure_requests_sent": False,
        "note": "The REST contract is explicit; no A2A 0.3 or cross-project fallback.",
    }


def target(project: Any, root: Path, settings: Settings, *, confirmed: bool) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("A new target and incoming endpoint require --confirm-create.")
    from azure.core.exceptions import ResourceNotFoundError

    from .cloud import create_prompt_agent

    selected = names(settings)
    if ledger_path(root, settings).exists():
        raise ValueError("Preserve this A2A run's ownership; do not recreate it.")
    next(iter(project.agents.list(limit=1)), None)
    try:
        project.agents.get(agent_name=selected["target"])
    except ResourceNotFoundError:
        pass
    else:
        raise ValueError("The A2A target name already exists.")
    created = create_prompt_agent(project, settings, root, selected["target"], confirmed=True)
    ownership = {
        "project_endpoint": settings.project_endpoint,
        "names": selected,
        "target_version": created["agent_version"],
        "caller_version": None,
        "incoming_enabled": False,
    }
    write_json(ledger_path(root, settings), ownership)
    response = project.agents.update_details(agent_name=selected["target"], **incoming_update())
    ownership["incoming_enabled"] = True
    ownership["endpoint_patch_response"] = response.as_dict()
    write_json(ledger_path(root, settings), ownership)
    return {
        **created,
        "target_base": base_path(settings),
        "connection_name": selected["connection"],
        "incoming_enabled": True,
        "ledger": str(ledger_path(root, settings)),
    }


def inspect(project: Any, root: Path, settings: Settings) -> dict[str, Any]:
    ownership = load_ownership(root, settings)
    actual_versions = [
        item.version for item in project.agents.list_versions(agent_name=names(settings)["target"])
    ]
    if actual_versions != [ownership["target_version"]]:
        raise ValueError(
            "The target has additional/different versions; its endpoint binding is no longer frozen."
        )
    card = card_request(
        project,
        settings,
        f"/agents/{names(settings)['target']}/endpoint/protocols/a2a/agentCard/v1.0",
    )
    evidence_path = ledger_path(root, settings).parent / "card-checks" / f"{uuid4().hex}.json"
    write_json(evidence_path, card)
    selected_interface = select_v1_interface(card, base_path(settings))
    return {
        "mode": "read-only-a2a-card",
        "target": names(settings)["target"],
        "target_version": ownership["target_version"],
        "card": card,
        "card_hash": digest(card),
        "selected_interface": selected_interface,
        "model_invoked": False,
    }


def caller(project: Any, root: Path, settings: Settings, *, confirmed: bool) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("Creating the relay caller requires --confirm-create.")
    from azure.core.exceptions import ResourceNotFoundError

    ownership = load_ownership(root, settings)
    inspect(project, root, settings)
    if ownership["caller_version"] is not None:
        raise ValueError("A caller is already recorded; do not create another version implicitly.")
    connection = project.connections.get(
        name=names(settings)["connection"], include_credentials=False
    )
    category = getattr(connection.type, "value", connection.type)
    if category != "RemoteA2A" or connection.target.rstrip("/") != base_path(settings):
        raise ValueError("The A2A connection does not target this owned agent's base path.")
    try:
        project.agents.get(agent_name=names(settings)["caller"])
    except ResourceNotFoundError:
        pass
    else:
        raise ValueError("The A2A caller name already exists.")
    instructions = (
        "Delegate the synthetic travel-policy question to the configured A2A specialist. Preserve its original policy IDs, dates and approval boundary. Do not book, pay or approve. Answer in English."
        if settings.language == "en"
        else "합성 출장 규정 질문을 연결된 A2A 전문 agent에 위임하세요. 원문 정책 ID·날짜·승인 경계를 유지하고 예약·지급·승인을 실행하지 않습니다. 한국어로 답하세요."
    )
    definition = caller_definition(settings, instructions, connection.id)
    agent = project.agents.create_version(
        agent_name=names(settings)["caller"], definition=definition
    )
    ownership.update(
        caller_version=agent.version,
        caller_request={"definition": definition.as_dict()},
        connection_id=connection.id,
        connection_target=connection.target,
    )
    write_json(ledger_path(root, settings), ownership)
    return {
        "mode": "live-a2a-caller-created",
        "agent_name": agent.name,
        "agent_version": agent.version,
        "target": names(settings)["target"],
        "requested_protocol": "1.0",
    }


def validate_delegation(
    raw: dict[str, Any],
    accepted: dict[str, Any],
    root: Path,
    settings: Settings,
    connection_id: str,
) -> dict[str, Any]:
    definition = accepted.get("definition")
    tools = definition.get("tools") if isinstance(definition, dict) else None
    if (
        not isinstance(tools, list)
        or len(tools) != 1
        or not isinstance(tools[0], dict)
        or any(
            tools[0].get(key) != value
            for key, value in {
                "type": "a2a",
                "a2a_version": "1.0",
                "project_connection_id": connection_id,
            }.items()
        )
    ):
        raise ValueError(
            "The accepted caller definition is not the explicit owned A2A 1.0 configuration."
        )
    calls = [
        item
        for item in raw.get("output", [])
        if item.get("type") in {"a2a_call", "a2a_preview_call"}
    ]
    if (
        not calls
        or any(
            item.get("error")
            or item.get("status") != "completed"
            or item.get("name") != names(settings)["connection"]
            or not isinstance(item.get("call_id"), str)
            or not item["call_id"]
            for item in calls
        )
        or len({item["call_id"] for item in calls}) != len(calls)
    ):
        raise ValueError("No unique successful A2A delegation call was observed.")
    outputs = [
        item
        for item in raw.get("output", [])
        if item.get("type") in {"a2a_call_output", "a2a_preview_call_output"}
    ]
    if len(outputs) != len(calls) or {item.get("call_id") for item in outputs} != {
        item["call_id"] for item in calls
    }:
        raise ValueError("Every A2A call needs its actual matching target output.")
    source_ids = {item["id"] for item in load_documents(root, settings.language)}
    answers = []
    for item in outputs:
        if item.get("error") or item.get("status") != "completed":
            raise ValueError("An actual A2A target output failed.")
        answer = Answer.from_json(item["output"])
        if not set(answer.citations) <= source_ids:
            raise ValueError("The A2A target cited an unprovided policy.")
        answers.append(answer.to_dict())
    return {
        "a2a_calls": calls,
        "a2a_outputs": outputs,
        "target_answers": answers,
        "accepted_tool_type": "a2a",
        "accepted_a2a_version": "1.0",
        "observed_event_types": sorted({item["type"] for item in calls}),
        "protocol_packet_capture_performed": False,
    }


def verify_recorded(root: Path, settings: Settings, label: str) -> dict[str, Any]:
    directory = root / "outputs/a2a-runs" / safe_label(label)
    ownership = load_ownership(root, settings)
    raw = read_json(directory / "response.json")
    accepted = read_json(directory / "actual-caller-definition.json")
    binding = read_json(directory / "binding.json")
    if (
        accepted.get("name") != names(settings)["caller"]
        or accepted.get("version") != ownership["caller_version"]
    ):
        raise ValueError("The recorded accepted definition is not the intended caller/version.")
    selected = select_v1_interface(binding["card"], base_path(settings))
    result = {
        "mode": "validation-of-recorded-live-a2a",
        "azure_requests_sent": False,
        "original_response_hash": digest(raw),
        "accepted_definition_hash": digest(accepted),
        "response_id": raw.get("id"),
        "selected_interface": selected,
        **validate_delegation(raw, accepted, root, settings, ownership["connection_id"]),
        "note": "Original live request and failed initial verifier are preserved. This rechecks the actual payload without another model request.",
    }
    path = directory / "payload-validation.json"
    if path.exists():
        raise FileExistsError("Preserve the existing recorded-payload validation.")
    write_json(path, result)
    return result


def invoke(
    project: Any, client: Any, root: Path, settings: Settings, label: str, *, confirmed: bool
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("A2A calls both caller and target models; pass --confirm-cost.")
    from .cloud import response_metadata, response_with_payload
    from .toolbox import QUESTIONS

    ownership = load_ownership(root, settings)
    if not ownership["caller_version"]:
        raise ValueError("Create and record the A2A caller before invoking it.")
    binding = inspect(project, root, settings)
    directory = root / "outputs/a2a-runs" / safe_label(label)
    directory.mkdir(parents=True, exist_ok=False)
    request = {
        "input": QUESTIONS[settings.language],
        "tool_choice": "required",
        "store": False,
        "extra_body": {
            "agent_reference": {
                "type": "agent_reference",
                "name": names(settings)["caller"],
                "version": ownership["caller_version"],
            }
        },
    }
    write_json(directory / "request.json", request)
    write_json(directory / "binding.json", binding)
    accepted = project.agents.get_version(
        agent_name=names(settings)["caller"], agent_version=ownership["caller_version"]
    ).as_dict()
    write_json(directory / "actual-caller-definition.json", accepted)
    response, raw = response_with_payload(
        client, error_path=directory / "service-error.json", **request
    )
    write_json(directory / "response.json", raw)
    metadata = response_metadata(response)
    delegation = validate_delegation(raw, accepted, root, settings, ownership["connection_id"])
    result = {
        "mode": "live-a2a-agent-delegation",
        "language": settings.language,
        "caller": names(settings)["caller"],
        "caller_version": ownership["caller_version"],
        "target": names(settings)["target"],
        "target_version": ownership["target_version"],
        "requested_a2a_version": "1.0",
        "observed_card_version": binding["selected_interface"]["protocolVersion"],
        "observed_transport": binding["selected_interface"]["protocolBinding"],
        **delegation,
        "answer": response.output_text,
        **metadata,
        "recorded_at": datetime.now(UTC).isoformat(),
        "note": "The service may retain a2a_preview_call event names for an accepted a2a/1.0 definition. Configuration, selected card interface and matching target output are verified; wire packets are not captured. Caller usage is not combined caller/target cost.",
    }
    write_json(directory / "summary.json", result)
    return result
