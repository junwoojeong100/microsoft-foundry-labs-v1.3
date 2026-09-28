import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .contracts import digest, parse_json, safe_label, write_json
from .settings import Settings, credential_for, owned_prefix, require_env, require_uuid


def telemetry_query(name: str, response_id: str, started_at: int) -> str:
    if type(started_at) is not int or started_at <= 0:
        raise ValueError("A recorded routine start timestamp is required for telemetry lookup.")
    start = datetime.fromtimestamp(started_at, UTC) - timedelta(minutes=2)
    end = datetime.now(UTC) + timedelta(minutes=2)
    return (
        "AppGenAIContent\n"
        f"| where TimeGenerated between (datetime({start.isoformat()}) .. datetime({end.isoformat()}))\n"
        f"| where AgentName == {json.dumps(name)}\n"
        "| extend attributes = todynamic(Attributes)\n"
        f"| where tostring(attributes['gen_ai.response.id']) == {json.dumps(response_id)}\n"
        "| where tostring(attributes['gen_ai.operation.name']) == 'invoke_agent'\n"
        "| project TraceId, SpanId, AgentName, OutputMessages, Attributes\n"
    )


def validate_telemetry_response(
    raw: Any, name: str, response_id: str, project_id: str
) -> dict[str, Any]:
    from .benchmark import re_trace
    from .observability import normalize_log_rows

    rows = normalize_log_rows(raw)
    if len(rows) != 1:
        raise ValueError(
            "Expected one exact routine response trace; preserve missing/duplicate rows and "
            "retry the same response readback after ingestion, not another dispatch."
        )
    row = rows[0]
    attributes = parse_json(row["Attributes"]) if isinstance(row.get("Attributes"), str) else row.get("Attributes")
    if (
        not isinstance(attributes, dict)
        or row.get("AgentName") != name
        or attributes.get("gen_ai.response.id") != response_id
        or attributes.get("gen_ai.operation.name") != "invoke_agent"
        or str(attributes.get("gen_ai.azure_ai_project.id", "")).casefold() != project_id.casefold()
        or not re_trace(row.get("TraceId"))
        or not attributes.get("gen_ai.agent.version")
    ):
        raise ValueError("Telemetry does not identify the exact routine response, agent and project.")
    messages = parse_json(row["OutputMessages"]) if isinstance(row.get("OutputMessages"), str) else row.get("OutputMessages")
    if not isinstance(messages, list):
        raise ValueError("The routine trace has no recorded assistant output.")
    texts = [
        part["content"]
        for message in messages
        if isinstance(message, dict) and message.get("role") == "assistant"
        and message.get("finish_reason") == "stop"
        for part in message.get("parts", [])
        if isinstance(part, dict) and part.get("type") == "text"
        and isinstance(part.get("content"), str) and part["content"].strip()
    ]
    if not texts:
        raise ValueError("The routine trace contains no nonempty assistant text.")
    return {
        "answer": "\n".join(texts),
        "trace_id": row["TraceId"],
        "agent_reference": {
            "type": "agent_reference", "name": name,
            "version": str(attributes["gen_ai.agent.version"]),
        },
        "response_hash": digest(messages),
    }


def retrieve_telemetry(
    settings: Settings, directory: Path, name: str, run: dict[str, Any]
) -> dict[str, Any]:
    import httpx

    workspace = require_uuid("AZURE_LOG_ANALYTICS_WORKSPACE_ID")
    project_id = require_env("AZURE_AI_PROJECT_ID")
    query = telemetry_query(name, run["response_id"], run.get("started_at"))
    (directory / "response-query.kql").write_text(query, encoding="utf-8")
    print("Read-only exact-response telemetry query:\n```kql\n" + query + "```", flush=True)
    with credential_for(settings) as credential, httpx.Client(timeout=120, follow_redirects=False) as http:
        token = credential.get_token("https://api.loganalytics.io/.default")
        response = http.post(
            f"https://api.loganalytics.io/v1/workspaces/{workspace}/query",
            headers={"Authorization": "Bearer " + token.token},
            json={"query": query},
        )
    if not response.is_success:
        write_json(directory / "response-telemetry-error.json", {
            "status_code": response.status_code, "body": response.text,
        })
        response.raise_for_status()
    raw = parse_json(response.text)
    write_json(directory / "response-telemetry.json", raw)
    return {
        **validate_telemetry_response(raw, name, run["response_id"], project_id),
        "workspace_id": workspace,
        "query_hash": digest(query),
        "telemetry_hash": digest(raw),
    }


def inspect_run(
    project: Any,
    client: Any,
    root: Path,
    settings: Settings,
    name: str,
    dispatch_id: str,
    label: str,
    *,
    verify_response: bool = False,
    response_source: str = "api",
    scheduled: bool = False,
) -> dict[str, Any]:
    if not name.startswith(owned_prefix() + "-") or not dispatch_id.startswith("dispatch_"):
        raise ValueError("Inspect only an explicitly named owned routine and returned dispatch ID.")
    if response_source not in {"api", "telemetry"}:
        raise ValueError("Select api or telemetry explicitly for routine response readback.")
    directory = root / "outputs/routine-inspections" / safe_label(label)
    directory.mkdir(parents=True, exist_ok=False)
    routine = project.beta.routines.get(name).as_dict()
    runs = [item.as_dict() for item in project.beta.routines.list_runs(name, limit=100)]
    write_json(directory / "routine.json", routine)
    write_json(directory / "runs.json", runs)
    matches = [run for run in runs if run.get("dispatch_id") == dispatch_id]
    if len(matches) != 1:
        raise ValueError("The exact manual dispatch does not have one unambiguous run record.")
    run = matches[0]
    cancelled_after_delivery = (
        scheduled
        and verify_response
        and response_source == "telemetry"
        and run.get("phase") == "cancelled"
        and run.get("status") == "Finished"
    )
    if (
        run.get("attempt_source") != ("timer_delivery" if scheduled else "queued_dispatch")
        or (run.get("phase") != "completed" and not cancelled_after_delivery)
        or run.get("status") != "Finished"
        or not run.get("response_id")
    ):
        raise ValueError("The requested delivery has not completed with a response ID.")
    if scheduled and (
        run.get("trigger_type") != "timer"
        or type(run.get("scheduled_fire_at")) is not int
        or type(run.get("triggered_at")) is not int
        or run["triggered_at"] < run["scheduled_fire_at"]
    ):
        raise ValueError("The run does not prove an actual scheduled timer firing.")
    result = {
        "mode": "read-only-routine-delivery",
        "routine_name": name,
        "routine_enabled": routine["enabled"],
        "dispatch_id": dispatch_id,
        "run_id": run["id"],
        "run_status": run["status"],
        "run_phase": run["phase"],
        "response_id": run["response_id"],
        "agent_answer_verified": False,
        "response_retrieval": "not-attempted",
        "runs_hash": digest(runs),
        "manual_delivery_verified": not scheduled,
        "scheduled_trigger_verified": scheduled,
        "new_model_request": False,
        "requires_exact_response_for_cancelled_phase": cancelled_after_delivery,
        "other_attempts": [
            {
                "id": item["id"],
                "attempt_source": item.get("attempt_source"),
                "status": item["status"],
                "phase": item.get("phase"),
            }
            for item in runs
            if item.get("dispatch_id") != dispatch_id
        ],
        "note": "Delivery and answer readback are verified separately. Cancelled/failed attempts remain visible; no replacement inference is performed.",
    }
    if verify_response and response_source == "telemetry":
        target = routine.get("action", {}).get("agent_name")
        if not isinstance(target, str) or not target.startswith(owned_prefix() + "-"):
            raise ValueError("Telemetry readback requires the exact owned routine target name.")
        result.update(
            **retrieve_telemetry(settings, directory, target, run),
            agent_answer_verified=True,
            response_retrieval="verified-telemetry",
        )
    elif verify_response:
        from openai import NotFoundError

        try:
            received = client.responses.with_raw_response.retrieve(run["response_id"])
        except NotFoundError as error:
            result["response_retrieval"] = "unavailable-http-404"
            write_json(directory / "response-error.json", error.response.json())
            write_json(directory / "summary.json", result)
            raise ValueError(
                "Delivery is recorded but its response is not retrievable under this credential. No answer verification or direct-call substitute is claimed."
            ) from error
        raw = received.http_response.json()
        write_json(directory / "response.json", raw)
        response = received.parse()
        if response.status != "completed" or not response.output_text:
            raise ValueError(
                "The routine delivered a response, but no complete answer was observed."
            )
        reference = raw.get("agent_reference")
        if not isinstance(reference, dict) or reference.get("name") != routine.get(
            "action", {}
        ).get("agent_name"):
            raise ValueError("The response agent reference does not match the routine target.")
        result.update(
            agent_answer_verified=True,
            response_retrieval="verified",
            response_status=response.status,
            agent_reference=reference,
            answer=response.output_text,
            response_hash=digest(raw),
        )
    write_json(directory / "summary.json", result)
    return result
