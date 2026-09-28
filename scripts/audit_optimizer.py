#!/usr/bin/env python3
"""Audit a saved policy Prompt Optimizer export without contacting Azure."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from foundry_workshop.calibration import verify_calibration  # noqa: E402
from foundry_workshop.contracts import (  # noqa: E402
    digest,
    parse_json,
    read_json,
    read_jsonl,
    safe_label,
    write_json,
)
from foundry_workshop.native import verified_native  # noqa: E402
from foundry_workshop.policy_evaluation import (  # noqa: E402
    PASS_THRESHOLD,
    POLICY_EVALUATORS,
    POLICY_MODE,
    optimizer_items,
    validate_policy_catalog,
    validate_policy_score,
)

OPTIMIZER_MAPPING = {
    "query": "{{item.query}}",
    "response": "{{sample.output_text}}",
    "ground_truth": "{{item.ground_truth}}",
}
OPTIONAL_MAPPING = {
    "tool_calls": "{{sample.tool_calls}}",
    "tool_definitions": "{{sample.tool_definitions}}",
}
CALIBRATION_FILES = (
    "manifest.json", "dataset.json", "corpus.json", "evaluator-catalog.json",
    "cloud-evaluation.json", "cloud-evaluation-raw.json", "cloud-evaluation-results.json",
    "policy-evaluation-inputs.json", "policy-source-corpora.json", "policy-reference-audit.json",
)


def identifier(value: Any) -> str:
    if type(value) not in {str, int} or isinstance(value, str) and not value.strip():
        raise ValueError("An explicit, nonempty string/integer item identifier is required.")
    return str(value)


def envelope(value: Any) -> dict[str, Any]:
    if not isinstance(value, str):
        raise ValueError("The original and echoed ground_truth must contain a JSON reference string.")
    parsed = parse_json(value)
    if not isinstance(parsed, dict) or parsed.get("schema") != POLICY_MODE:
        raise ValueError("Missing or malformed original policy reference envelope.")
    return parsed


def file_hashes(paths: dict[str, Path]) -> dict[str, str]:
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}


def prepared_rows(root: Path, dataset: Path, language: str) -> dict[str, dict[str, Any]]:
    original = read_jsonl(dataset)
    expected = {item["case_id"]: item for item in optimizer_items(root, language)}
    if len(original) != 6 or len(expected) != 6:
        raise ValueError("This audit requires all six original dev cases, never a holdout or subset.")
    by_query = {}
    seen = set()
    for item in original:
        if set(item) != {"case_id", "query", "context", "ground_truth"} or any(
            not isinstance(value, str) or not value.strip() for value in item.values()
        ):
            raise ValueError("Use the original prepared optimizer JSONL with separate query/context/ground_truth.")
        canonical = expected.get(item["case_id"])
        if (
            canonical is None
            or item["case_id"] in seen
            or item["query"] in by_query
            or item["query"] != canonical["query"]
            or parse_json(item["context"]) != parse_json(canonical["context"])
            or envelope(item["ground_truth"]) != envelope(canonical["ground_truth"])
        ):
            raise ValueError("Prepared dev cases or original source references changed, duplicated or are missing.")
        seen.add(item["case_id"])
        by_query[item["query"]] = item
    return by_query


def check_criteria(
    definition: dict[str, Any], catalog: list[dict[str, Any]], judge: str
) -> dict[str, dict[str, Any]]:
    validate_policy_catalog(catalog, judge)
    expected = {item["evaluator_name"]: item for item in catalog}
    criteria = definition.get("testing_criteria")
    if (
        not isinstance(criteria, list) or len(criteria) != len(POLICY_EVALUATORS)
        or any(not isinstance(criterion, dict) for criterion in criteria)
    ):
        raise ValueError("The optimizer must retain exactly the three calibrated policy evaluators.")
    seen = set()
    for criterion in criteria:
        name = criterion.get("name")
        calibrated = expected.get(name)
        if (
            calibrated is None
            or name in seen
            or criterion.get("type") != "azure_ai_evaluator"
            or criterion.get("evaluator_name") != name
            or criterion.get("evaluator_version") != calibrated["definition"]["version"]
        ):
            raise ValueError("Optimizer evaluator names/versions differ from the frozen calibrated catalog.")
        seen.add(name)
        parameters = criterion.get("initialization_parameters")
        if (
            not isinstance(parameters, dict)
            or not {"model", "pass_threshold"} <= set(parameters) <= {"model", "pass_threshold", "deployment_name"}
            or parameters["model"] != judge
            or parameters.get("deployment_name", judge) != judge
            or type(parameters["pass_threshold"]) not in {int, float}
            or parameters["pass_threshold"] != PASS_THRESHOLD
        ):
            raise ValueError("Optimizer judge/threshold differs from calibration; threshold must remain 4.")
        mapping = criterion.get("data_mapping")
        if (
            not isinstance(mapping, dict)
            or not set(OPTIMIZER_MAPPING) <= set(mapping) <= set(OPTIMIZER_MAPPING) | set(OPTIONAL_MAPPING)
            or any(mapping.get(key) != value for key, value in OPTIMIZER_MAPPING.items())
            or any(mapping[key] != OPTIONAL_MAPPING[key] for key in set(mapping) - set(OPTIMIZER_MAPPING))
        ):
            raise ValueError("Optimizer mapping must use item.ground_truth, not response/self-context.")
    return expected


def submitted_ids(run: dict[str, Any], original: dict[str, dict[str, Any]]) -> dict[str, str]:
    source = run.get("data_source")
    if not isinstance(source, dict) or source.get("type") != "azure_ai_target_completions":
        raise ValueError("The exported run must record actual target generation, not fixture responses.")
    template = source.get("input_messages", {}).get("template")
    if (
        not isinstance(template, list)
        or len(template) != 1
        or template[0].get("role") != "user"
        or template[0].get("content") != "{{item.query}}"
    ):
        raise ValueError("Optimizer target input must be query-only, not reference/oracle fields.")
    submitted = source.get("source", {}).get("content")
    if not isinstance(submitted, list) or len(submitted) != len(original):
        raise ValueError("Retain all six submitted optimizer inputs to verify provider item IDs.")
    mapped = {}
    queries = set()
    for row in submitted:
        item = row.get("item") if isinstance(row, dict) else None
        if not isinstance(item, dict):
            raise ValueError("A submitted optimizer input lacks its original item.")
        query = item.get("query")
        key = identifier(item.get("item_id"))
        if (
            query not in original or query in queries or key in mapped
            or envelope(item.get("ground_truth")) != envelope(original[query]["ground_truth"])
        ):
            raise ValueError("Submitted optimizer IDs/queries/references differ from the prepared dev dataset.")
        mapped[key] = query
        queries.add(query)
    return mapped


def audit_optimizer(
    root: Path,
    export_directory: Path,
    dataset: Path,
    calibration_label: str,
    *,
    language: str = "ko",
) -> dict[str, Any]:
    calibration_directory = root / "outputs/judge-calibration" / safe_label(calibration_label)
    paths = {
        "prepared_dataset": dataset,
        **{name: export_directory / f"{name}.json" for name in ("definition", "run", "output-items", "summary")},
        **{f"calibration/{name}": calibration_directory / name for name in CALIBRATION_FILES},
    }
    hashes = file_hashes(paths)
    original = prepared_rows(root, dataset, language)
    definition, run, outputs, summary = (
        read_json(paths[name]) for name in ("definition", "run", "output-items", "summary")
    )
    if (
        not isinstance(definition, dict) or not isinstance(run, dict)
        or not re.fullmatch(r"eval_[A-Za-z0-9_-]+", str(definition.get("id", "")))
        or not re.fullmatch(r"evalrun_[A-Za-z0-9_-]+", str(run.get("id", "")))
        or run.get("eval_id") != definition["id"]
        or run.get("status") != "completed" or run.get("error")
    ):
        raise ValueError("The exported evaluation/run IDs and completed status must agree.")
    if (
        not isinstance(outputs, list) or len(outputs) != len(original)
        or not isinstance(summary, dict)
        or summary.get("evaluation_id") != definition["id"]
        or summary.get("run_id") != run["id"]
        or summary.get("expected_rows") != 6 or summary.get("actual_rows") != len(outputs)
        or summary.get("definition_hash") != digest(definition)
        or summary.get("run_hash") != digest(run)
        or summary.get("output_items_hash") != digest(outputs)
    ):
        raise ValueError("Export hashes/counts changed or rows are missing/extra; preserve the original export.")
    # Verify the calibration's own audited source/fixture lineage, then bind this distinct export below.
    calibration = verify_calibration(
        root, calibration_label, calibration_directory, policy=True
    )
    state, calibrated_results = verified_native(calibration_directory)
    manifest = read_json(calibration_directory / "manifest.json")
    if not calibration["gate_passed"] or manifest["language"] != language:
        raise ValueError("Matching-language positive/negative/counterfactual calibration must pass.")
    catalog = read_json(calibration_directory / "evaluator-catalog.json")
    evaluators = check_criteria(definition, catalog, state["judge_deployment"])
    models = {name: set() for name in POLICY_EVALUATORS}
    for row in calibrated_results:
        for score in row["results"]:
            sample = score.get("sample")
            model = sample.get("model") if isinstance(sample, dict) else None
            if not isinstance(model, str) or not model.strip():
                raise ValueError("Calibration must retain the judge's reported model identity.")
            models[score["name"]].add(model)
    if any(len(values) != 1 for values in models.values()) or len(set.union(*models.values())) != 1:
        raise ValueError("Calibration must retain one frozen reported judge model across all criteria.")
    mapped = submitted_ids(run, original)
    target = run["data_source"].get("target", {})
    if (
        not isinstance(target, dict) or target.get("type") != "azure_ai_agent"
        or any(not isinstance(target.get(key), str) or not target[key].strip() for key in ("name", "version"))
    ):
        raise ValueError("The optimizer export needs the exact target agent name/version.")
    seen_cases, response_ids, output_ids, datasource_ids = set(), set(), set(), set()
    audited = []
    target_models = set()
    for output in outputs:
        source = output.get("datasource_item") if isinstance(output, dict) else None
        if (
            not isinstance(source, dict) or output.get("status") != "completed"
            or output.get("eval_id") != definition["id"] or output.get("run_id") != run["id"]
        ):
            raise ValueError("Every completed output must retain its source echo and evaluation/run IDs.")
        key = identifier(source["item_id"]) if "item_id" in source else None
        query = source.get("query") if "query" in source else mapped.get(key)
        if query not in original or key is not None and mapped.get(key) != query:
            raise ValueError("An echoed query/item_id cannot be matched exactly to the prepared input.")
        item = original[query]
        case_id = item["case_id"]
        output_id, datasource_id = identifier(output.get("id")), identifier(output.get("datasource_item_id"))
        response_id = source.get("response_id")
        if (
            case_id in seen_cases or output_id in output_ids or datasource_id in datasource_ids
            or not isinstance(response_id, str) or not re.fullmatch(r"resp_[A-Za-z0-9_-]+", response_id)
            or response_id in response_ids
            or "case_id" in source and source["case_id"] != case_id
        ):
            raise ValueError("Missing, duplicate or inconsistent case/output/response IDs cannot pass.")
        reference = envelope(source.get("ground_truth"))
        if reference != envelope(item["ground_truth"]):
            raise ValueError(f"Echoed ground_truth differs from the original reference for {case_id}.")
        text = source.get("sample.output_text")
        if (
            not isinstance(text, str) or not text.strip()
            or text in {source["ground_truth"], item["context"]}
            or reference["reference_id"] in text
        ):
            raise ValueError("Missing generated output or response-as-reference/oracle leakage cannot pass.")
        if source.get("agent_name") != target["name"] or source.get("agent_version") != target["version"]:
            raise ValueError("The response echo does not identify the original target agent version.")
        sample = output.get("sample")
        target_model = sample.get("model") if isinstance(sample, dict) else None
        if (
            not isinstance(sample, dict) or sample.get("error")
            or not isinstance(target_model, str) or not target_model.strip()
            or target_model == state["judge_deployment"]
            or any(target_model in values for values in models.values())
        ):
            raise ValueError("A successful target response must identify a model distinct from the judge.")
        results = output.get("results")
        if (
            not isinstance(results, list) or len(results) != len(evaluators)
            or any(not isinstance(score, dict) for score in results)
            or {score.get("name") for score in results} != set(evaluators)
        ):
            raise ValueError("Every row must preserve exactly all three original evaluator results.")
        for score in results:
            validate_policy_score(score)
            evaluator = evaluators[score["name"]]
            reason_ids = set(re.findall(r"policy-ref-[0-9a-f]{64}(?![A-Za-z0-9_-])", score["reason"]))
            if reason_ids != {reference["reference_id"]}:
                raise ValueError(f"Judge reason lacks the correct reference_id for {case_id}.")
            sample = score.get("sample")
            if not isinstance(sample, dict) or sample.get("model") not in models[evaluator["name"]]:
                raise ValueError("An optimizer judge's reported model differs from calibration.")
        seen_cases.add(case_id)
        response_ids.add(response_id)
        output_ids.add(output_id)
        datasource_ids.add(datasource_id)
        target_models.add(target_model)
        audited.append({
            "case_id": case_id,
            "match_method": "exact-query" if "query" in source else "verified-item-id",
            "verified_item_id": source.get("item_id"),
            "output_item_id": output["id"],
            "datasource_item_id": output["datasource_item_id"],
            "response_id": response_id,
            "agent_name": source["agent_name"],
            "agent_version": source["agent_version"],
            "reference_id": reference["reference_id"],
            "reference_hash": digest(reference),
            "source_hashes": reference["source_hashes"],
            "source_context_hash": reference["source_context_hash"],
            "original_output_item_hash": digest(output),
            "original_results": results,
        })
    if seen_cases != {item["case_id"] for item in original.values()} or hashes != file_hashes(paths):
        raise ValueError("A case is missing or input evidence changed during the read-only audit.")
    return {
        "mode": "read-only-optimizer-policy-audit",
        "validation_status": "valid",
        "policy_mode": POLICY_MODE,
        "proof_level": "source-echo+reason-reference-id+counterfactual-calibration",
        "internal_judge_requests_captured": False,
        "evaluation_id": definition["id"],
        "run_id": run["id"],
        "run_name": run.get("name"),
        "counts": {"requested": 6, "returned": len(outputs), "matched": len(seen_cases), "missing": 0, "extra": 0},
        "judge_deployment": state["judge_deployment"],
        "judge_reported_models": {key: sorted(value) for key, value in models.items()},
        "target_reported_models": sorted(target_models),
        "evaluator_hash": state["evaluator_hash"],
        "evaluators": [{
            "metric": entry["name"], "evaluator_name": name,
            "version": entry["definition"]["version"], "threshold": PASS_THRESHOLD,
            "passed": sum(score["passed"] for row in outputs for score in row["results"] if score["name"] == name),
            "total": 6,
        } for name, entry in evaluators.items()],
        "calibration": {
            "label": calibration_label, "summary": calibration,
            "evaluation_id": state["evaluation_id"], "run_id": state["run_id"],
            "reference_audit_hash": state["policy_reference_audit_hash"],
        },
        "artifacts": {name: {"path": str(path.resolve()), "sha256": hashes[name]} for name, path in paths.items()},
        "rows": audited,
        "new_model_requests": False,
        "holdout_loaded": False,
        "improvement_claimed": False,
        "candidate_generation_assessed": False,
        "production_approval": False,
        "note": (
            "All original exports and scores are unchanged. Source echoes, reason IDs and a separate "
            "counterfactual calibration establish reference dependence, not a capture of hidden judge "
            "requests, proof of improved prompts, new candidates, or general safety."
        ),
    }


def main(argv: list[str] | None = None, *, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-directory", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--calibration-label", required=True)
    parser.add_argument("--language", choices=("ko", "en"), default="ko")
    parser.add_argument("--output", type=Path, help="Optional new JSON report under outputs/; no overwrite. Otherwise print only.")
    args = parser.parse_args(argv)
    try:
        output = None
        if args.output:
            output = root / args.output
            if output.exists() or output.is_symlink():
                raise FileExistsError("The report already exists; preserve it and select a new output path.")
            if output.suffix != ".json" or not output.resolve().is_relative_to(root.resolve() / "outputs"):
                raise ValueError("The new audit report must be a JSON file under this project's outputs/.")
        report = audit_optimizer(
            root, root / args.export_directory, root / args.dataset,
            args.calibration_label, language=args.language,
        )
        if output:
            write_json(output, report, overwrite=False)
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
