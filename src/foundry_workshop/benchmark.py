import html
import json
import logging
import math
import statistics
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from .contracts import (
    digest,
    load_cases,
    load_documents,
    read_json,
    read_jsonl,
    safe_label,
    validate_cases,
    write_json,
)
from .evaluation import grade
from .hosted import HostedBinding, HostedTransport, validate_request, validate_response
from .profiles import RuntimeProfile, runtime_contract
from .settings import Settings

LOGGER = logging.getLogger(__name__)
RUBRIC = {
    "id": "travel-business-v2",
    "version": 2,
    "required_pass_rate": 1.0,
    "checks": [
        "completed",
        "schema",
        "decision",
        "limit_krw",
        "required_citations",
        "citations_retrieved",
        "answer_contains_limit",
        "citations_relevant",
    ],
    "related_lodging_citations": ["APPROVAL-01", "RECEIPT-01"],
    "errors_remain_in_denominator": True,
}


def directory(root: Path, label: str) -> Path:
    return root / "outputs/benchmarks" / safe_label(label)


def grade_strict(row: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    import re

    result = grade(row, case)
    checks = result["checks"]
    checks.update(answer_contains_limit=False, citations_relevant=False)
    if checks["schema"]:
        answer = row["answer"]
        numbers = {
            value.replace(",", "") for value in re.findall(r"\d[\d,]*(?:\.\d+)?", answer["answer"])
        }
        for amount, multiplier in re.findall(r"(\d+(?:\.\d+)?)\s*(만|천)\s*원", answer["answer"]):
            value = Decimal(amount) * (10000 if multiplier == "만" else 1000)
            if value == value.to_integral_value():
                numbers.add(str(int(value)))
        expected = case["expected_limit_krw"]
        allowed = set(case["required_citations"])
        if any(value.startswith("TRAVEL-") for value in allowed):
            allowed.update(RUBRIC["related_lodging_citations"])
        checks["answer_contains_limit"] = expected is None or str(expected) in numbers
        checks["citations_relevant"] = set(answer["citations"]) <= allowed
    return {"case_id": case["case_id"], "passed": all(checks.values()), "checks": checks}


def wilson_interval(passed: int, total: int) -> list[float]:
    if total <= 0 or not 0 <= passed <= total:
        raise ValueError("A confidence interval needs a nonempty, valid denominator.")
    z = 1.959963984540054
    probability = passed / total
    denominator = 1 + z * z / total
    center = (probability + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(probability * (1 - probability) / total + z * z / (4 * total**2))
        / denominator
    )
    return [max(0.0, center - margin), min(1.0, center + margin)]


def summarize_matrix(
    rows: list[dict[str, Any]], cases: list[dict[str, Any]], model_keys: list[str]
) -> dict[str, Any]:
    expected = {(model, case["case_id"]) for model in model_keys for case in cases}
    actual = [(row.get("model_key"), row.get("case_id")) for row in rows]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError(
            "The full model-by-case matrix is required; missing/duplicate rows are not scored."
        )
    by_case = {case["case_id"]: case for case in cases}
    models = {}
    for model in model_keys:
        selected = [row for row in rows if row["model_key"] == model]
        checks = []
        for row in selected:
            if (
                row.get("status") not in {"ok", "error"}
                or row.get("question") != by_case[row["case_id"]]["question"]
            ):
                raise ValueError(
                    "Every matrix row needs the frozen question and an explicit status."
                )
            checks.append(grade_strict(row, by_case[row["case_id"]]))
        passed = sum(item["passed"] for item in checks)
        successful = [row for row in selected if row["status"] == "ok"]
        latencies = [
            row["latency_seconds"]
            for row in successful
            if type(row.get("latency_seconds")) in {int, float}
            and math.isfinite(row["latency_seconds"])
            and row["latency_seconds"] >= 0
        ]
        usage_complete = all(
            isinstance(row.get("usage"), dict)
            and all(
                type(row["usage"].get(key)) is int and row["usage"][key] >= 0
                for key in ("input_tokens", "output_tokens")
            )
            for row in selected
        )
        models[model] = {
            "total": len(selected),
            "passed": passed,
            "failed": len(selected) - passed,
            "errors": len(selected) - len(successful),
            "pass_rate": passed / len(selected),
            "illustrative_wilson_95": wilson_interval(passed, len(selected)),
            "business_gate_passed": passed == len(selected),
            "successful_latency_observations": len(latencies),
            "p50_success_latency_seconds": statistics.median(latencies) if latencies else None,
            "p95_success_latency_seconds": sorted(latencies)[math.ceil(len(latencies) * 0.95) - 1]
            if latencies
            else None,
            "input_tokens": sum(row["usage"]["input_tokens"] for row in selected)
            if usage_complete
            else None,
            "output_tokens": sum(row["usage"]["output_tokens"] for row in selected)
            if usage_complete
            else None,
            "observed_models": sorted(
                {
                    call["response_model"]
                    for row in successful
                    for call in row.get("model_calls", [])
                }
            ),
            "checks": checks,
        }
    return {
        "models": models,
        "expected_rows": len(expected),
        "actual_rows": len(rows),
        "errors": sum(value["errors"] for value in models.values()),
        "business_gate_passed": all(value["business_gate_passed"] for value in models.values()),
        "rubric": RUBRIC,
        "limitations": "Small synthetic set, not an SLA or statistical model ranking. Failed requests are not fast successful responses.",
    }


def load_matrix(root: Path, label: str):
    path = directory(root, label)
    manifest = read_json(path / "manifest.json")
    if manifest.get("kind") != "hosted-model-matrix" or manifest.get("mode") != "live":
        raise ValueError("This command requires an explicitly recorded live Hosted matrix.")
    if manifest.get("status") not in {"completed", "completed_with_errors"}:
        raise ValueError("An incomplete matrix cannot be scored or used as a candidate.")
    cases = read_json(path / "dataset.json")
    corpus = read_json(path / "corpus.json")
    validate_cases(cases, corpus)
    rows = read_jsonl(path / "responses.jsonl")
    for key, value in (
        ("dataset_hash", digest(cases)),
        ("corpus_hash", digest(corpus)),
        ("responses_hash", digest(rows)),
        ("runtime_contract_hash", digest(manifest["runtime_contract"])),
        ("rubric_hash", digest(RUBRIC)),
    ):
        if manifest.get(key) != value:
            raise ValueError(f"Frozen matrix {key} changed; do not silently recompute its meaning.")
    if manifest["expected_rows"] != len(cases) * len(manifest["model_keys"]) or manifest[
        "actual_rows"
    ] != len(rows):
        raise ValueError("The manifest's denominator does not match the frozen matrix.")
    for row in rows:
        if (
            row.get("run_id") != manifest["run_id"]
            or row.get("runtime_contract_hash") != manifest["runtime_contract_hash"]
        ):
            raise ValueError("Matrix row lineage differs from the run manifest.")
        if row.get("regression_source") != manifest["reviewed_regressions"].get(row["case_id"]):
            raise ValueError("The collected row did not preserve its reviewed-regression linkage.")
    summarize_matrix(rows, cases, manifest["model_keys"])
    return manifest, rows, cases


def reviewed_regressions(
    root: Path, label: str | None, cases: list[dict[str, Any]]
) -> dict[str, Any]:
    if label is None:
        return {}
    path = root / "outputs/regressions" / f"{safe_label(label)}.json"
    record = read_json(path)
    if record.get("status") != "approved-for-dev" or record.get("source_split") != "dev":
        raise ValueError("Only explicitly reviewed dev regressions may be consumed.")
    case = next((case for case in cases if case["case_id"] == record["case"]["case_id"]), None)
    if case != record["case"] or digest(case) != record["case_hash"]:
        raise ValueError("Regression questions or expected answers changed the frozen dataset.")
    source, source_rows, _ = load_matrix(root, record["source_label"])
    row = next((row for row in source_rows if row["row_id"] == record["source_row_id"]), None)
    if (
        not row
        or digest(row) != record["source_response_hash"]
        or digest(source) != record["source_manifest_hash"]
    ):
        raise ValueError("The reviewed regression's source lineage changed.")
    return {
        case["case_id"]: {"file": path.name, "hash": digest(record), "lineage": record["lineage"]}
    }


def collect_matrix(
    root: Path,
    settings: Settings,
    profile: RuntimeProfile,
    binding: HostedBinding,
    *,
    label: str,
    split: str,
    model_keys: list[str] | None = None,
    concurrency: int = 1,
    confirmed: bool,
    candidate: str | None = None,
    unlock_holdout: bool = False,
    regressions: str | None = None,
    transport_factory=HostedTransport,
    recoverable_errors: tuple[type[Exception], ...] = (ValueError, TimeoutError),
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("A Hosted matrix is billable; explicitly pass --confirm-cost.")
    if profile.protocol != "invocations":
        raise ValueError(
            "The matrix must target the typed Invocations profile, not a different Responses agent."
        )
    if type(concurrency) is not int or not 1 <= concurrency <= 4:
        raise ValueError("Matrix concurrency must be 1-4.")
    contract = runtime_contract(root, settings, profile)
    selected = sorted(contract["models"]) if model_keys is None else model_keys
    if (
        not selected
        or len(selected) != len(set(selected))
        or not set(selected) <= set(contract["models"])
    ):
        raise ValueError("Choose unique model keys from the explicit deployment map.")
    frozen = None
    if split == "holdout":
        if not unlock_holdout or not candidate or regressions:
            raise ValueError(
                "Freeze a dev candidate and unlock holdout explicitly; no regression harvesting."
            )
        previous, old_rows, old_cases = load_matrix(root, candidate)
        old_grade = summarize_matrix(old_rows, old_cases, previous["model_keys"])
        if previous["split"] != "dev" or not set(selected) <= set(previous["model_keys"]):
            raise ValueError("Holdout models must be selected from the frozen dev matrix.")
        if previous["runtime_contract"] != contract or previous["binding"] != binding.to_dict():
            raise ValueError(
                "Holdout must use the exact frozen code/prompt/models/retrieval and Hosted version."
            )
        if previous["concurrency"] != concurrency:
            raise ValueError("Holdout must retain the candidate's concurrency.")
        if any(not old_grade["models"][key]["business_gate_passed"] for key in selected):
            raise ValueError("Selected dev candidates must pass before opening holdout.")
        frozen = {"label": candidate, "manifest_hash": digest(previous), "model_keys": selected}
    elif split != "dev" or candidate or unlock_holdout:
        raise ValueError("Use dev for development, or an explicitly frozen holdout.")
    cases = load_cases(root, split, profile.language)
    row_ids = [f"{key}-{case['case_id']}" for key in selected for case in cases]
    if len(row_ids) != len(set(row_ids)):
        raise ValueError(
            "Model/case names produce ambiguous row IDs; choose unambiguous model keys."
        )
    if len(cases) * len(selected) > 160:
        raise ValueError("Review the request budget before exceeding 160 matrix rows.")
    reviewed = reviewed_regressions(root, regressions, cases)
    path = directory(root, label)
    path.mkdir(parents=True, exist_ok=False)
    manifest = {
        "kind": "hosted-model-matrix",
        "schema_version": 1,
        "mode": "live",
        "label": label,
        "run_id": "matrix-" + uuid.uuid4().hex,
        "created_at": datetime.now(UTC).isoformat(),
        "status": "collecting",
        "split": split,
        "model_keys": selected,
        "expected_rows": len(cases) * len(selected),
        "concurrency": concurrency,
        "runtime_contract": contract,
        "runtime_contract_hash": digest(contract),
        "binding": binding.to_dict(),
        "dataset_hash": digest(cases),
        "corpus_hash": digest(load_documents(root, profile.language)),
        "rubric_hash": digest(RUBRIC),
        "frozen_candidate": frozen,
        "reviewed_regressions": reviewed,
        "session_retained_at_collection_end": True,
    }
    write_json(path / "dataset.json", cases)
    write_json(path / "corpus.json", load_documents(root, profile.language))
    write_json(path / "manifest.json", manifest)
    rows = []
    with transport_factory(settings, binding) as transport:
        manifest["session_id"] = transport.create_session()
        write_json(path / "manifest.json", manifest)

        def invoke_one(case, model_key):
            payload = validate_request(
                {
                    "question": case["question"],
                    "case_id": case["case_id"],
                    "model_key": model_key,
                    "run_id": manifest["run_id"],
                },
                contract["models"],
            )
            common = {
                **payload,
                "row_id": f"{model_key}-{case['case_id']}",
                "runtime_contract_hash": manifest["runtime_contract_hash"],
                "regression_source": reviewed.get(case["case_id"]),
            }
            started = time.perf_counter()
            try:
                result, raw = transport.invoke(payload)
                write_json(path / "http" / f"{model_key}-{case['case_id']}.json", raw)
                validated = validate_response(result, payload, contract)
                if not re_trace(validated.get("trace_id")):
                    raise ValueError(
                        "A Hosted benchmark row needs its real nonzero trace ID; export verification remains separate."
                    )
                row = {**validated, **common, "status": "ok"}
            except recoverable_errors as exc:
                LOGGER.error("Matrix row failed %s: %s", common["row_id"], type(exc).__name__)
                row = {
                    **common,
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error": str(exc)
                    if isinstance(exc, ValueError)
                    else "Transport failed; inspect this row's retained diagnostic evidence.",
                }
            row["latency_seconds"] = round(time.perf_counter() - started, 6)
            return row

        with (path / "responses.jsonl").open("x", encoding="utf-8") as output:
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                for case in cases:
                    pending = [pool.submit(invoke_one, case, key) for key in selected]
                    for future in as_completed(pending):
                        row = future.result()
                        rows.append(row)
                        output.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
                        output.flush()
    manifest.update(
        status="completed_with_errors"
        if any(row["status"] == "error" for row in rows)
        else "completed",
        actual_rows=len(rows),
        responses_hash=digest(rows),
        completed_at=datetime.now(UTC).isoformat(),
    )
    write_json(path / "manifest.json", manifest)
    summary = summarize_matrix(rows, cases, selected)
    write_json(path / "business-evaluation.json", summary)
    return {
        **summary,
        "label": label,
        "gate_passed": summary["business_gate_passed"],
        "session_id": manifest["session_id"],
        "session_retained": True,
        "note": "Inspect actual traces, then stop only this recorded session. No deployment approval is granted.",
    }


def re_trace(value: Any) -> bool:
    import re

    return (
        isinstance(value, str)
        and bool(re.fullmatch(r"[0-9a-f]{32}", value))
        and int(value, 16) != 0
    )


def compare_matrices(root: Path, baseline: str, candidate: str) -> dict[str, Any]:
    old, old_rows, cases = load_matrix(root, baseline)
    new, new_rows, _ = load_matrix(root, candidate)
    old_grade = summarize_matrix(old_rows, cases, old["model_keys"])
    new_grade = summarize_matrix(new_rows, cases, new["model_keys"])
    if old["split"] != "dev" or new["split"] != "dev":
        raise ValueError("Do not rank or develop prompts on holdout results.")
    for key in ("dataset_hash", "corpus_hash", "model_keys", "concurrency", "rubric_hash"):
        if old[key] != new[key]:
            raise ValueError(f"Controlled matrix comparison requires identical {key}.")
    a, b = old["runtime_contract"], new["runtime_contract"]
    if a["profile"].get("language", "ko") != b["profile"].get("language", "ko"):
        raise ValueError("Controlled comparison requires the same explicit language.")
    for key in (
        "models",
        "project_endpoint",
        "inference_endpoint",
        "max_output_tokens",
        "code_hash",
        "retrieval_configuration",
    ):
        if a[key] != b[key]:
            raise ValueError(f"Controlled comparison changed runtime {key}.")
    for key in ("kind", "pattern", "retrieval", "api", "protocol"):
        if a["profile"][key] != b["profile"][key]:
            raise ValueError(f"Controlled comparison changed runtime profile {key}.")
    for model in old["model_keys"]:
        if (
            old_grade["models"][model]["observed_models"]
            != new_grade["models"][model]["observed_models"]
        ):
            raise ValueError("An observed model changed during a prompt/version-only comparison.")
    if (
        old["binding"]["name"] != new["binding"]["name"]
        or old["binding"]["endpoint"] != new["binding"]["endpoint"]
    ):
        raise ValueError("Compare explicit versions of the same Hosted endpoint.")
    indexed = {(row["model_key"], row["case_id"]): row for row in old_rows}
    changed = [
        row["row_id"]
        for row in new_rows
        if row.get("context_hash")
        != indexed[(row["model_key"], row["case_id"])].get("context_hash")
    ]
    result = {
        "baseline": baseline,
        "candidate": candidate,
        "baseline_metrics": old_grade,
        "candidate_metrics": new_grade,
        "changed_context_rows": changed,
        "isolated_prompt_comparison": not changed,
        "deployment_approved": False,
        "note": "Different evidence makes this end-to-end evidence, not an isolated model/prompt ranking.",
    }
    write_json(directory(root, candidate) / f"comparison-{safe_label(baseline)}.json", result)
    return result


def approve_regression(
    root: Path, source_label: str, row_id: str, output_label: str, reviewer: str, reason: str
) -> Path:
    manifest, rows, cases = load_matrix(root, source_label)
    if manifest["split"] != "dev":
        raise ValueError("Holdout cannot be harvested into development regressions.")
    if not reviewer.strip() or len(reason.strip()) < 15:
        raise ValueError(
            "Provide a reviewer and a specific review reason before promoting a dev case."
        )
    row = next((row for row in rows if row["row_id"] == row_id), None)
    if row is None:
        raise ValueError("Unknown source dev row.")
    case = next(case for case in cases if case["case_id"] == row["case_id"])
    path = root / "outputs/regressions" / f"{safe_label(output_label)}.json"
    record = {
        "status": "approved-for-dev",
        "source_split": "dev",
        "case": case,
        "case_hash": digest(case),
        "reviewer": reviewer.strip(),
        "review_reason": reason.strip(),
        "reviewer_identity_verified": False,
        "production_approval": False,
        "source_label": source_label,
        "source_row_id": row_id,
        "source_manifest_hash": digest(manifest),
        "source_response_hash": digest(row),
        "lineage": {
            "source_run_id": manifest["run_id"],
            "source_response_id": row.get("response_id"),
            "source_trace_id": row.get("trace_id"),
            "source_context_hash": row.get("context_hash"),
        },
        "reference_source": "Frozen original dev ground truth, never a model-generated answer.",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return path


def report_matrix(root: Path, label: str) -> Path:
    manifest, rows, cases = load_matrix(root, label)
    summary = summarize_matrix(rows, cases, manifest["model_keys"])
    language = manifest["runtime_contract"]["profile"].get("language", "ko")
    if language not in {"ko", "en"}:
        raise ValueError("The report must use the frozen matrix language.")
    english = language == "en"
    title = "Workshop evaluation" if english else "실습 평가"
    introduction = (
        "Business checks of actual Hosted responses. Native judges, trace export verification and human production approval are separate."
        if english
        else "실제 Hosted 응답의 업무 검사입니다. Native judge·trace export 확인·사람의 운영 승인은 별도입니다."
    )
    columns = (
        (
            "Model key",
            "Passed/total",
            "Errors",
            "p50 successful latency",
            "p95 successful latency",
            "Input/output tokens",
        )
        if english
        else ("모델 키", "통과/전체", "오류", "p50 성공 지연", "p95 성공 지연", "입력/출력 토큰")
    )
    body = [
        f"<!doctype html><html lang='{language}'><meta charset='utf-8'><title>{title}</title>",
        "<style>body{font:16px/1.6 system-ui;max-width:1200px;margin:32px auto;padding:0 20px}"
        "table{border-collapse:collapse;width:100%}td,th{border:1px solid #aaa;padding:8px}"
        "pre{white-space:pre-wrap} .fail{background:#fff1f0}</style>",
        f"<h1>{title}: {html.escape(label)}</h1>",
        f"<p>{introduction}</p>",
        "<table><tr>" + "".join(f"<th>{column}</th>" for column in columns) + "</tr>",
    ]
    for key, item in summary["models"].items():
        body.append(
            "<tr>"
            + "".join(
                f"<td>{html.escape(str(value))}</td>"
                for value in (
                    key,
                    f"{item['passed']}/{item['total']}",
                    item["errors"],
                    item["p50_success_latency_seconds"],
                    item["p95_success_latency_seconds"],
                    f"{item['input_tokens']} / {item['output_tokens']}",
                )
            )
            + "</tr>"
        )
    body += [
        "</table><p>"
        + (
            "None means unmeasured, not zero. Small synthetic samples do not prove an operational SLA or statistical superiority."
            if english
            else "None은 미측정이며 0이 아닙니다. 작은 합성 표본은 운영 SLA나 통계적 우월성을 증명하지 않습니다."
        )
        + "</p>",
        "<h2>" + ("All rows and failures" if english else "모든 행과 실패") + "</h2>",
    ]
    by_case = {case["case_id"]: case for case in cases}
    for row in rows:
        check = grade_strict(row, by_case[row["case_id"]])
        body.append(
            f'<section class="{"pass" if check["passed"] else "fail"}"><h3>{html.escape(row["row_id"])}</h3><pre>'
        )
        body.append(
            html.escape(
                json.dumps(
                    {
                        "question": row["question"],
                        "status": row["status"],
                        "answer": row.get("answer"),
                        "checks": check["checks"],
                        "error": row.get("error"),
                        "trace_id": row.get("trace_id"),
                        "response_id": row.get("response_id"),
                        "regression_source": row.get("regression_source"),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        )
        body.append("</pre></section>")
    body.append("</html>")
    target = directory(root, label) / "report.html"
    target.write_text("\n".join(body), encoding="utf-8")
    write_json(directory(root, label) / "business-evaluation.json", summary)
    return target


def native_items(root: Path, label: str):
    manifest, rows, cases = load_matrix(root, label)
    if any(row["status"] != "ok" for row in rows):
        raise ValueError(
            "Native evaluation requires every actual target response, not a success-only subset."
        )
    by_case = {case["case_id"]: case for case in cases}
    items = [
        {
            "case_id": row["row_id"],
            "query": row["question"],
            "response": row["answer"]["answer"],
            "context": json.dumps(row["documents"], ensure_ascii=False),
            "ground_truth": json.dumps(by_case[row["case_id"]], ensure_ascii=False),
        }
        for row in rows
    ]
    return manifest, items


def evaluate_matrix(
    root: Path,
    settings: Settings,
    label: str,
    *,
    confirmed: bool,
    timeout: int,
    reference: str | None = None,
    retry_failed: bool = False,
) -> dict[str, Any]:
    from .native import evaluate_items

    manifest, items = native_items(root, label)
    catalog = directory(root, reference) / "evaluator-catalog.json" if reference else None
    if reference:
        previous, _, _ = load_matrix(root, reference)
        if (
            previous["runtime_contract"]["project_endpoint"]
            != manifest["runtime_contract"]["project_endpoint"]
        ):
            raise ValueError("The reference evaluator must belong to the same project.")
    if settings.project_endpoint != manifest["runtime_contract"]["project_endpoint"]:
        raise ValueError("Do not evaluate this matrix in a different project.")
    return evaluate_items(
        settings,
        directory(root, label),
        items,
        label=label,
        source_run_id=manifest["run_id"],
        dataset_hash=manifest["dataset_hash"],
        forbidden_deployments=set(manifest["runtime_contract"]["models"].values()),
        evaluator_names=("groundedness", "relevance"),
        confirmed=confirmed,
        timeout=timeout,
        reference_catalog=catalog,
        retry_failed=retry_failed,
    )


def verify_release(
    root: Path,
    baseline: str,
    candidate: str,
    holdout: str,
    *,
    require_native: bool,
    require_traces: bool,
    calibration_label: str | None = None,
    require_native_pass: bool = False,
    require_regressions: bool = False,
) -> dict[str, Any]:
    from .calibration import verify_calibration
    from .native import verified_native
    from .observability import verified_traces

    compare_matrices(root, baseline, candidate)
    runs = {label: load_matrix(root, label) for label in (baseline, candidate, holdout)}
    selected, final = runs[candidate][0], runs[holdout][0]
    if final["split"] != "holdout" or final["frozen_candidate"] != {
        "label": candidate,
        "manifest_hash": digest(selected),
        "model_keys": final["model_keys"],
    }:
        raise ValueError("Holdout is not bound to this exact frozen candidate and model selection.")
    if (
        final["runtime_contract"] != selected["runtime_contract"]
        or final["binding"] != selected["binding"]
    ):
        raise ValueError("Holdout changed the pinned runtime/version.")
    grades = {
        label: summarize_matrix(rows, cases, manifest["model_keys"])
        for label, (manifest, rows, cases) in runs.items()
    }
    execution_ok = all(grade["errors"] == 0 for grade in grades.values())
    business_ok = all(
        grades[label]["models"][key]["business_gate_passed"]
        for label in (candidate, holdout)
        for key in final["model_keys"]
    )
    regressions = selected["reviewed_regressions"]
    if require_regressions and (
        not regressions
        or any(
            item["lineage"]["source_run_id"] != runs[baseline][0]["run_id"]
            for item in regressions.values()
        )
    ):
        raise ValueError(
            "The candidate must actually consume the reviewed baseline regression lineage."
        )
    native_status = {}
    if require_native or require_native_pass or calibration_label:
        evaluator_hashes = set()
        for label, (manifest, _, _) in runs.items():
            state, results = verified_native(directory(root, label))
            _, submitted = native_items(root, label)
            if (
                state["source_run_id"] != manifest["run_id"]
                or state["input_hash"] != digest(submitted)
                or state.get("dataset_hash") != manifest["dataset_hash"]
            ):
                raise ValueError("A native run is not bound to this frozen response matrix.")
            evaluator_hashes.add(state["evaluator_hash"])
            native_status[label] = {
                "evaluation_id": state["evaluation_id"],
                "run_id": state["run_id"],
                "rows": len(results),
                "failed_items": [
                    {"row_id": row["case_id"], "evaluator": item["name"], "score": item["score"]}
                    for row in results
                    for item in row["results"]
                    if not item["passed"]
                ],
            }
        if len(evaluator_hashes) != 1:
            raise ValueError("The cohorts did not use the same frozen evaluator/judge/thresholds.")
    traces = {label: verified_traces(root, label) for label in runs} if require_traces else {}
    calibration = (
        verify_calibration(root, calibration_label, directory(root, candidate))
        if calibration_label
        else None
    )
    row_models = {row["row_id"]: row["model_key"] for _, rows, _ in runs.values() for row in rows}
    native_quality_ok = (
        not any(
            row_models[item["row_id"]] in final["model_keys"]
            for label in (candidate, holdout)
            for item in native_status.get(label, {}).get("failed_items", [])
        )
        if native_status
        else None
    )
    gate = (
        execution_ok
        and business_ok
        and (not require_native_pass or native_quality_ok is True)
        and (calibration is None or calibration["gate_passed"])
    )
    report = {
        "gate_passed": gate,
        "execution_gate_passed": execution_ok,
        "business_gate_passed": business_ok,
        "native_quality_passed": native_quality_ok,
        "native_quality_required": require_native_pass,
        "selected_model_keys": final["model_keys"],
        "native": native_status,
        "regressions_consumed": regressions,
        "traces": traces,
        "calibration": calibration,
        "recommendation": "ready-for-human-review"
        if gate and native_quality_ok is not False
        else "review-native-findings"
        if gate
        else "reject",
        "deployment_approved": False,
        "holdout": "Final acceptance only; the bundled teaching set is already exposed.",
    }
    write_json(directory(root, holdout) / "release-verification.json", report)
    return report
