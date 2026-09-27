from pathlib import Path
from typing import Any

from .contracts import digest, safe_label, write_json
from .settings import Settings, owned_prefix


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
) -> dict[str, Any]:
    if not name.startswith(owned_prefix() + "-") or not dispatch_id.startswith("dispatch_"):
        raise ValueError("Inspect only an explicitly named owned routine and returned dispatch ID.")
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
    if (
        run.get("attempt_source") != "queued_dispatch"
        or run.get("phase") != "completed"
        or run.get("status") != "Finished"
        or not run.get("response_id")
    ):
        raise ValueError("The original manual dispatch has not completed with a response ID.")
    result = {
        "mode": "read-only-routine-delivery",
        "routine_name": name,
        "routine_enabled": routine["enabled"],
        "dispatch_id": dispatch_id,
        "run_id": run["id"],
        "run_status": run["status"],
        "response_id": run["response_id"],
        "agent_answer_verified": False,
        "response_retrieval": "not-attempted",
        "runs_hash": digest(runs),
        "manual_delivery_verified": True,
        "scheduled_trigger_verified": False,
        "new_model_request": False,
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
        "note": "A finished manual delivery is not proof of answer content or future timer firing. Cancelled future-timer attempts remain visible.",
    }
    if verify_response:
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
