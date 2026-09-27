import json
import math
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .contracts import digest, read_json, write_json
from .hosted import HostedBinding, HostedTransport
from .settings import Settings, credential_for, require_uuid


def trace_query(manifest: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    from .benchmark import re_trace

    ids = [row.get("trace_id") for row in rows]
    if (
        not ids
        or any(row["status"] != "ok" for row in rows)
        or not all(re_trace(value) for value in ids)
    ):
        raise ValueError(
            "Every expected Hosted response must have a real trace ID before complete trace verification."
        )
    if len(ids) != len(set(ids)):
        raise ValueError("Case-isolated benchmark requests must not share a trace ID.")
    start = datetime.fromisoformat(manifest["created_at"]) - timedelta(minutes=2)
    end = datetime.now(UTC) + timedelta(minutes=2)
    name = json.dumps(manifest["binding"]["name"])
    versioned = json.dumps(manifest["binding"]["name"] + ":" + manifest["binding"]["version"])
    return (
        f"let expected = dynamic({json.dumps(ids)});\n"
        "requests\n"
        f"| where timestamp between (datetime({start.isoformat()}) .. datetime({end.isoformat()}))\n"
        "| extend foundry_name = coalesce(tostring(customDimensions['gen_ai.agent.name']), "
        "tostring(customDimensions['azure.ai.agentserver.agent_name']))\n"
        "| extend agent_id = tostring(customDimensions['gen_ai.agent.id'])\n"
        f"| where foundry_name == {name} or agent_id == {versioned}\n"
        "| where operation_Id in (expected)\n"
        "| summarize matching_requests=count(), request_errors=countif(success == false), "
        "duration_ms=max(duration) by trace_id=operation_Id\n"
        "| project trace_id, matching_requests, request_errors, duration_ms\n"
    )


def normalize_log_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list) and all(isinstance(row, dict) for row in value):
        return value
    if not isinstance(value, dict) or value.get("error"):
        raise ValueError("The log query did not return a successful tabular response.")
    tables = value.get("tables")
    if not isinstance(tables, list) or len(tables) != 1:
        raise ValueError("Expected exactly one scoped trace-verification table.")
    columns = [column["name"] for column in tables[0]["columns"]]
    if len(columns) != len(set(columns)):
        raise ValueError("The query returned duplicate column names.")
    result = []
    for row in tables[0]["rows"]:
        if len(row) != len(columns):
            raise ValueError("The log-query row does not match its columns.")
        result.append(dict(zip(columns, row, strict=True)))
    return result


def validate_trace_rows(value: Any, expected_ids: list[str]) -> list[dict[str, Any]]:
    rows = normalize_log_rows(value)
    ids = [row.get("trace_id") for row in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(expected_ids):
        raise ValueError("Missing, duplicate or unrelated traces cannot pass verification.")
    for row in rows:
        if (
            type(row.get("matching_requests")) is not int
            or row["matching_requests"] < 1
            or type(row.get("request_errors")) is not int
            or row["request_errors"] != 0
            or type(row.get("duration_ms")) not in {int, float}
            or not math.isfinite(row["duration_ms"])
            or row["duration_ms"] < 0
        ):
            raise ValueError("A trace query contains an error or unmeasured/invalid duration.")
    return rows


def write_trace_plan(root: Path, label: str) -> dict[str, Any]:
    from .benchmark import directory, load_matrix

    manifest, rows, _ = load_matrix(root, label)
    query = trace_query(manifest, rows)
    path = directory(root, label) / "trace-query.kql"
    path.write_text(query, encoding="utf-8")
    return {
        "label": label,
        "agent": manifest["binding"],
        "expected_traces": len(rows),
        "query": query,
        "query_file": str(path),
        "azure_queried": False,
        "trace_export_verified": False,
    }


def monitor_matrix(root: Path, label: str) -> dict[str, Any]:
    import httpx
    from azure.core.exceptions import AzureError

    from .benchmark import directory, load_matrix

    path = directory(root, label)
    if (path / "trace-verification.json").exists():
        return {**verified_traces(root, label), "cached_verified_evidence": True}
    prior = [
        path / name
        for name in ("trace-query.kql", "trace-query-result.json", "trace-query-error.json")
        if (path / name).is_file()
    ]
    if prior:
        attempts = path / "trace-attempts"
        attempts.mkdir(exist_ok=True)
        number = 1
        while (attempts / f"attempt-{number:03d}").exists():
            number += 1
        archived = attempts / f"attempt-{number:03d}"
        archived.mkdir()
        for artifact in prior:
            shutil.copy2(artifact, archived / artifact.name)
    manifest, rows, _ = load_matrix(root, label)
    settings = Settings.from_env()
    if settings.project_endpoint != manifest["runtime_contract"]["project_endpoint"]:
        raise ValueError("Query traces using the frozen matrix's project configuration.")
    application = require_uuid("AZURE_APPLICATION_INSIGHTS_APP_ID")
    subscription = require_uuid("AZURE_SUBSCRIPTION_ID")
    plan = write_trace_plan(root, label)
    print("Read-only Application Insights query:\n```kql\n" + plan["query"] + "```", flush=True)
    from .contracts import parse_json

    error_details: dict[str, Any] = {}
    try:
        with credential_for(settings) as credential:
            token = credential.get_token("https://api.applicationinsights.io/.default")
            with httpx.Client(timeout=180, follow_redirects=False) as client:
                response = client.post(
                    f"https://api.applicationinsights.io/v1/apps/{application}/query",
                    headers={"Authorization": "Bearer " + token.token},
                    json={"query": plan["query"]},
                )
        if not response.is_success:
            error_details = {"status_code": response.status_code, "body": response.text}
        response.raise_for_status()
    except (AzureError, httpx.HTTPError) as exc:
        write_json(
            path / "trace-query-error.json",
            {
                "error_type": type(exc).__name__,
                "query_hash": digest(plan["query"]),
                **error_details,
            },
        )
        raise ValueError(
            f"Scoped Application Insights query failed: {type(exc).__name__}; no alternate identity/resource was used."
        ) from exc
    raw = parse_json(response.text)
    write_json(path / "trace-query-result.json", raw)
    normalized = validate_trace_rows(raw, [row["trace_id"] for row in rows])
    receipt = {
        "source": "actual-scoped-application-insights-rest-query",
        "verified_at": datetime.now(UTC).isoformat(),
        "application_id": application,
        "subscription_id": subscription,
        "source_manifest_hash": digest(manifest),
        "source_responses_hash": manifest["responses_hash"],
        "query_hash": digest(plan["query"]),
        "result_hash": digest(raw),
        "verified_traces": len(normalized),
        "expected_traces": len(rows),
        "trace_export_verified": True,
        "note": "Incoming request duration is not summed with nested model/workflow spans.",
    }
    write_json(path / "trace-verification.json", receipt)
    return receipt


def verified_traces(root: Path, label: str) -> dict[str, Any]:
    from .benchmark import directory, load_matrix

    manifest, rows, _ = load_matrix(root, label)
    path = directory(root, label)
    receipt = read_json(path / "trace-verification.json")
    raw = read_json(path / "trace-query-result.json")
    query = (path / "trace-query.kql").read_text(encoding="utf-8")
    if (
        receipt.get("source")
        not in {
            "actual-azure-cli-application-insights-query",
            "actual-scoped-application-insights-rest-query",
        }
        or receipt.get("source_manifest_hash") != digest(manifest)
        or receipt.get("source_responses_hash") != manifest["responses_hash"]
        or receipt.get("query_hash") != digest(query)
        or receipt.get("result_hash") != digest(raw)
        or receipt.get("trace_export_verified") is not True
    ):
        raise ValueError("Trace verification lineage changed.")
    normalized = validate_trace_rows(raw, [row["trace_id"] for row in rows])
    if receipt["verified_traces"] != len(normalized) or receipt["expected_traces"] != len(rows):
        raise ValueError("The trace verification denominator changed.")
    return receipt


def stop_matrix_session(root: Path, settings: Settings, label: str) -> dict[str, Any]:
    from .benchmark import directory, load_matrix

    manifest, _, _ = load_matrix(root, label)
    if settings.project_endpoint != manifest["runtime_contract"]["project_endpoint"]:
        raise ValueError("Do not stop a recorded session through a different project.")
    binding = HostedBinding(**manifest["binding"])
    with HostedTransport(settings, binding) as transport:
        before = transport.project.agents.get_session(
            binding.name, manifest["session_id"]
        ).as_dict()
        indicator = before.get("version_indicator", {})
        if indicator.get("agent_version") != binding.version:
            raise ValueError("The recorded session is not bound to the recorded version.")
        already_idle = before.get("status") in {"idle", "stopped"}
        after = before if already_idle else transport.stop_session(manifest["session_id"])
    if after.get("status") not in {"idle", "stopped"}:
        raise ValueError("Stop was requested but a stopped/idle state was not yet confirmed.")
    receipt = {
        "label": label,
        "agent": binding.to_dict(),
        "session_id": manifest["session_id"],
        "confirmed_at": datetime.now(UTC).isoformat(),
        "status": after["status"],
        "stop_requested": not already_idle,
        "persistent_files_deleted": False,
        "shared_resources_deleted": False,
    }
    write_json(directory(root, label) / "session-cleanup.json", receipt)
    return receipt
