import math
import statistics
from pathlib import Path
from typing import Any

from .contracts import Answer, digest, load_cases, read_json, read_jsonl, safe_label, write_json


def validate_matrix(rows: list[dict[str, Any]], cases: list[dict[str, Any]]) -> None:
    expected = {case["case_id"] for case in cases}
    actual = [row.get("case_id") for row in rows]
    if len(actual) != len(set(actual)) or set(actual) != expected or len(rows) != len(cases):
        raise ValueError("Response matrix has missing, duplicate or unexpected case IDs.")
    questions = {case["case_id"]: case["question"] for case in cases}
    for row in rows:
        if row.get("question") != questions[row["case_id"]]:
            raise ValueError(f"Question mismatch for {row['case_id']}.")
        if row.get("status") not in {"ok", "error"}:
            raise ValueError("Every response must be explicitly ok or error.")


def grade(row: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "completed": row.get("status") == "ok",
        "schema": False,
        "decision": False,
        "limit_krw": False,
        "required_citations": False,
        "citations_retrieved": False,
    }
    if checks["completed"]:
        try:
            answer = Answer.from_dict(row.get("answer"))
        except ValueError:
            return {"case_id": case["case_id"], "passed": False, "checks": checks}
        checks.update(
            schema=True,
            decision=answer.decision == case["expected_decision"],
            limit_krw=answer.limit_krw == case["expected_limit_krw"],
            required_citations=set(case["required_citations"]) <= set(answer.citations),
            citations_retrieved=bool(answer.citations)
            and set(answer.citations) <= set(row.get("source_ids", [])),
        )
    return {"case_id": case["case_id"], "passed": all(checks.values()), "checks": checks}


def summarize(rows: list[dict[str, Any]], cases: list[dict[str, Any]]) -> dict[str, Any]:
    validate_matrix(rows, cases)
    by_id = {row["case_id"]: row for row in rows}
    results = [grade(by_id[case["case_id"]], case) for case in cases]
    latencies = [
        row["latency_seconds"]
        for row in rows
        if type(row.get("latency_seconds")) in {int, float}
        and math.isfinite(row["latency_seconds"])
        and row["latency_seconds"] >= 0
    ]
    passed = sum(result["passed"] for result in results)
    token_usage = [row.get("usage") for row in rows]
    complete_usage = all(
        isinstance(usage, dict)
        and type(usage.get("input_tokens")) is int
        and type(usage.get("output_tokens")) is int
        for usage in token_usage
    )
    return {
        "total": len(cases),
        "passed": passed,
        "failed": len(cases) - passed,
        "errors": sum(row["status"] == "error" for row in rows),
        "pass_rate": passed / len(cases),
        "business_gate_passed": passed == len(cases),
        "latency_observations": len(latencies),
        "median_latency_seconds": statistics.median(latencies) if latencies else None,
        "input_tokens": sum(usage["input_tokens"] for usage in token_usage)
        if complete_usage
        else None,
        "output_tokens": sum(usage["output_tokens"] for usage in token_usage)
        if complete_usage
        else None,
        "checks": results,
        "limitations": "Deterministic schema/business checks, not a semantic correctness or safety certification.",
    }


def load_run(
    root: Path, label: str
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    directory = root / "outputs" / safe_label(label)
    manifest = read_json(directory / "manifest.json")
    if manifest.get("status") not in {"completed", "completed_with_errors"}:
        raise ValueError(f"{label}: incomplete collection; do not score a successful prefix.")
    cases = load_cases(root, manifest["split"], manifest.get("language", "ko"))
    rows = read_jsonl(directory / "responses.jsonl")
    if manifest["dataset_hash"] != digest(cases) or manifest["responses_hash"] != digest(rows):
        raise ValueError(f"{label}: dataset or recorded responses changed after collection.")
    validate_matrix(rows, cases)
    for row in rows:
        for key in ("mode", "deployment", "prompt_hash", "run_id", "retrieval"):
            if row.get(key) != manifest.get(key):
                raise ValueError(f"{label}: response/manifest {key} mismatch.")
    return manifest, rows, cases


def evaluate_run(root: Path, label: str) -> dict[str, Any]:
    manifest, rows, cases = load_run(root, label)
    result = {
        "label": label,
        "mode": manifest["mode"],
        "split": manifest["split"],
        **summarize(rows, cases),
    }
    write_json(root / "outputs" / label / "business-evaluation.json", result)
    return result


def compare_runs(root: Path, baseline: str, candidate: str, variable: str) -> dict[str, Any]:
    if variable not in {"prompt", "model"}:
        raise ValueError("Comparison variable must be prompt or model.")
    old, old_rows, cases = load_run(root, baseline)
    new, new_rows, _ = load_run(root, candidate)
    for key in (
        "split",
        "dataset_hash",
        "corpus_hash",
        "code_hash",
        "retrieval",
        "mode",
        "inference",
    ):
        if old[key] != new[key]:
            raise ValueError(f"Comparison requires identical {key}.")
    if old["split"] != "dev":
        raise ValueError("Use dev for comparisons. Holdout is for one final acceptance check.")
    fixed_key = "deployment" if variable == "prompt" else "prompt_hash"
    if old[fixed_key] != new[fixed_key]:
        raise ValueError(f"A {variable} comparison must keep {fixed_key} fixed.")
    if variable == "prompt" and old["observed_models"] != new["observed_models"]:
        raise ValueError("The observed model changed during a prompt-only comparison.")
    old_by_id = {row["case_id"]: row for row in old_rows}
    changed_contexts = [
        row["case_id"]
        for row in new_rows
        if row.get("context_hash") != old_by_id[row["case_id"]].get("context_hash")
    ]
    result = {
        "baseline": baseline,
        "candidate": candidate,
        "mode": new["mode"],
        "variable": variable,
        "baseline_metrics": summarize(old_rows, cases),
        "candidate_metrics": summarize(new_rows, cases),
        "changed_context_cases": changed_contexts,
        "note": "Human review and unused holdout are still required. This command never deploys a candidate.",
    }
    if new["mode"] != "live":
        result["note"] = "OFFLINE FIXTURES ONLY: these numbers do not measure an LLM or Azure."
    elif changed_contexts:
        result["note"] += (
            " Retrieval changed: this is an end-to-end comparison, not an isolated model ranking."
        )
    write_json(root / "outputs" / candidate / f"comparison-vs-{safe_label(baseline)}.json", result)
    return result


def acceptance_report(root: Path, candidate: str, holdout: str) -> dict[str, Any]:
    selected, selected_rows, selected_cases = load_run(root, candidate)
    final, final_rows, final_cases = load_run(root, holdout)
    if selected["mode"] != "live" or final["mode"] != "live":
        raise ValueError("Acceptance requires real runs, never offline teaching fixtures.")
    if selected["split"] != "dev" or final["split"] != "holdout":
        raise ValueError("Acceptance requires a dev candidate and a separate holdout.")
    frozen = final["frozen_candidate"]
    if not frozen or frozen != {
        "label": candidate,
        "run_id": selected["run_id"],
        "manifest_hash": digest(selected),
    }:
        raise ValueError("Holdout is not bound to this unchanged candidate.")
    for key in (
        "prompt_hash",
        "deployment",
        "observed_models",
        "corpus_hash",
        "code_hash",
        "retrieval",
        "inference",
    ):
        if selected[key] != final[key]:
            raise ValueError(f"Candidate and holdout differ in {key}.")
    candidate_grade = summarize(selected_rows, selected_cases)
    holdout_grade = summarize(final_rows, final_cases)
    passed = candidate_grade["business_gate_passed"] and holdout_grade["business_gate_passed"]
    report = {
        "candidate": candidate,
        "holdout": holdout,
        "candidate_grade": candidate_grade,
        "holdout_grade": holdout_grade,
        "business_gate_passed": passed,
        "recommendation": "ready-for-human-review" if passed else "reject",
        "deployment_approved": False,
        "cloud_judge_results_included": False,
        "note": "Review native cloud judges, answer meaning, permissions and operating costs separately.",
    }
    write_json(root / "outputs" / holdout / "acceptance.json", report)
    return report


def record_feedback(root: Path, label: str, case_id: str, reason: str) -> Path:
    manifest, rows, cases = load_run(root, label)
    if manifest["split"] != "dev" or manifest["mode"] != "live":
        raise ValueError("Only real dev responses can enter the trace-to-regression review queue.")
    if manifest.get("retrieval") == "none":
        raise ValueError(
            "A no-evidence diagnostic fails because evidence was removed; do not queue it as a regression."
        )
    if len(reason.strip()) < 15:
        raise ValueError("Write a specific review reason of at least 15 characters.")
    selected = next((row for row in rows if row["case_id"] == case_id), None)
    if selected is None:
        raise ValueError("Unknown case ID.")
    case = next(case for case in cases if case["case_id"] == case_id)
    destination = root / "outputs" / label / f"review-{safe_label(case_id.lower())}.json"
    with destination.open("x", encoding="utf-8") as handle:
        import json

        json.dump(
            {
                "case": case,
                "review_reason": reason.strip(),
                "approval_status": "pending-human-review",
                "lineage": {
                    "run_id": manifest["run_id"],
                    "case_id": case_id,
                    "response_id": selected.get("response_id"),
                    "request_id": selected.get("request_id"),
                    "trace_id": selected.get("trace_id"),
                    "prompt_hash": manifest["prompt_hash"],
                    "context_hash": selected.get("context_hash"),
                },
                "reference_source": "Existing synthetic dev reference, never the model answer.",
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )
        handle.write("\n")
    return destination
