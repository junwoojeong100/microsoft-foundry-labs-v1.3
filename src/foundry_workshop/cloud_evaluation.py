import json
import math
from pathlib import Path
from typing import Any

from .contracts import read_json, safe_label, write_json
from .evaluation import load_run, summarize
from .settings import Settings

EVALUATORS = ("groundedness", "relevance")
BUSINESS_EVALUATOR = "business_rubric"
BUSINESS_DIRECTORY = "foundry-business-rubric"
GRADER_PATH = Path(__file__).with_name("business_rubric_grader.py")


def business_evaluator_version(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "categories": ["quality"],
        "display_name": "Workshop business rubric (synthetic)",
        "description": (
            "Deterministic schema, decision, limit and citation checks for the synthetic "
            "travel-policy workshop; the same rules as the local evaluate command."
        ),
        "definition": {
            "type": "code",
            "code_text": GRADER_PATH.read_text(),
            "init_parameters": {
                "type": "object",
                "properties": {
                    "deployment_name": {"type": "string"},
                    "pass_threshold": {"type": "number"},
                },
                "required": ["deployment_name", "pass_threshold"],
            },
            "metrics": {
                "result": {
                    "type": "continuous",
                    "desirable_direction": "increase",
                    "min_value": 0.0,
                    "max_value": 1.0,
                }
            },
            "data_schema": {
                "type": "object",
                "required": ["item"],
                "properties": {
                    "item": {
                        "type": "object",
                        "properties": {
                            "answer_json": {"type": "string"},
                            "ground_truth": {"type": "string"},
                            "source_ids": {"type": "string"},
                        },
                    }
                },
            },
        },
    }


def ensure_business_evaluator(project: Any, prefix: str) -> dict[str, Any]:
    """Reuse the owned custom evaluator version with identical code, or create one (Preview)."""
    from azure.core.exceptions import ResourceNotFoundError

    name = prefix.replace("-", "_") + "_business_rubric"
    wanted = business_evaluator_version(name)
    try:
        versions = [item.as_dict() for item in project.beta.evaluators.list_versions(name=name)]
    except ResourceNotFoundError:
        versions = []
    for version in versions:
        if version.get("definition", {}).get("code_text") == wanted["definition"]["code_text"]:
            return {"evaluator_name": name, "definition": version}
    created = project.beta.evaluators.create_version(name=name, evaluator_version=wanted)
    return {"evaluator_name": name, "definition": created.as_dict()}


def normalize_results(
    items: list[dict[str, Any]], row_ids: list[str], evaluator_names: tuple[str, ...] = EVALUATORS
) -> list[dict[str, Any]]:
    if len(items) != len(row_ids):
        raise ValueError("Cloud evaluation must return exactly one result per submitted response.")
    normalized = []
    seen = set()
    for item in items:
        if item.get("status") in {"failed", "error", "errored"}:
            raise ValueError("A cloud evaluation output item failed.")
        source = item.get("datasource_item")
        row_id = source.get("case_id") if isinstance(source, dict) else None
        if row_id is None:
            position = str(item.get("datasource_item_id", ""))
            if not position.isdigit() or not 0 <= int(position) < len(row_ids):
                raise ValueError("Cannot map an evaluation output to its source case.")
            row_id = row_ids[int(position)]
        if row_id not in row_ids or row_id in seen:
            raise ValueError("Unknown or duplicate cloud evaluation case ID.")
        seen.add(row_id)
        results = item.get("results")
        if not isinstance(results, list):
            raise ValueError(f"Missing evaluator results for {row_id}.")
        returned = sorted(str(result.get("name")) for result in results if isinstance(result, dict))
        missing = sorted(set(evaluator_names) - set(returned))
        if missing:
            raise ValueError(
                f"Missing evaluator results for {row_id}: returned {returned}, missing {missing}."
            )
        if len(results) != len(evaluator_names) or set(returned) != set(evaluator_names):
            raise ValueError("Unexpected evaluator names.")
        for result in results:
            score = result.get("score")
            if (
                result.get("error")
                or type(result.get("passed")) is not bool
                or type(score) not in {int, float}
                or not math.isfinite(score)
            ):
                raise ValueError(
                    f"Evaluator {result.get('name')} returned "
                    f"{result.get('status') or 'an error'} for {row_id}, not a complete native "
                    "score/pass result. A skipped or errored judge row never counts as a pass."
                )
        normalized.append({"case_id": row_id, "results": results})
    return normalized


def evaluate_cloud(
    root: Path,
    settings: Settings,
    label: str,
    *,
    timeout: int,
    confirmed: bool,
    business_evaluator: bool = False,
    reference: str | None = None,
    retry_failed: bool = False,
) -> dict[str, Any]:
    from .native import evaluate_items

    if not confirmed:
        raise ValueError("Cloud judges are billable. Explicitly pass --confirm-cost.")
    if not 5 <= timeout <= 900:
        raise ValueError("Evaluation timeout must be 5-900 seconds.")
    label = safe_label(label)
    manifest, rows, cases = load_run(root, label)
    if manifest["mode"] != "live" or any(row["status"] != "ok" for row in rows):
        raise ValueError("Cloud evaluation requires a complete real run with no collection errors.")
    if manifest.get("retrieval") == "none":
        raise ValueError(
            "A no-evidence diagnostic stays local: with empty context, Groundedness skips rows, "
            "and a skipped row is not a pass. No cloud job was submitted."
        )
    by_id = {case["case_id"]: case for case in cases}
    items = []
    for row in rows:
        item = {
            "case_id": row["case_id"],
            "query": row["question"],
            "response": row["answer"]["answer"],
            "context": json.dumps(row["documents"], ensure_ascii=False),
            "ground_truth": json.dumps(
                {
                    key: by_id[row["case_id"]][key]
                    for key in ("expected_decision", "expected_limit_krw", "required_citations")
                },
                ensure_ascii=False,
            ),
        }
        if business_evaluator:
            item["answer_json"] = json.dumps(row["answer"], ensure_ascii=False)
            item["source_ids"] = json.dumps(row.get("source_ids", []), ensure_ascii=False)
        items.append(item)
    names = (*EVALUATORS, BUSINESS_EVALUATOR) if business_evaluator else EVALUATORS
    subdirectory = BUSINESS_DIRECTORY if business_evaluator else ""
    directory = root / "outputs" / label / subdirectory
    reference_directory = None
    if reference is not None:
        reference = safe_label(reference)
        if reference == label:
            raise ValueError("--reference must name a different, already evaluated run.")
        reference_manifest, _, _ = load_run(root, reference)
        if manifest["split"] != "dev" or reference_manifest["split"] != "dev":
            raise ValueError("Compare dev runs only; holdout is for one final acceptance check.")
        reference_directory = root / "outputs" / reference / subdirectory
        if not (reference_directory / "cloud-evaluation.json").is_file():
            raise ValueError(
                "Evaluate the reference label first with the same cloud-evaluate options."
            )
    custom_catalog = None
    if (
        business_evaluator
        and reference is None
        and not (directory / "evaluator-catalog.json").exists()
    ):
        from .cloud import project_clients
        from .settings import owned_prefix

        with project_clients(settings, preview=True) as (project, _client):
            custom_catalog = {
                BUSINESS_EVALUATOR: ensure_business_evaluator(project, owned_prefix())
            }
    result = evaluate_items(
        settings,
        directory,
        items,
        label=label,
        source_run_id=manifest["run_id"],
        dataset_hash=manifest["dataset_hash"],
        forbidden_deployments={manifest["deployment"]},
        evaluator_names=names,
        confirmed=confirmed,
        timeout=timeout,
        custom_catalog=custom_catalog,
        retry_failed=retry_failed,
        retry_advice=True,
        reference_catalog=reference_directory / "evaluator-catalog.json"
        if reference_directory
        else None,
        reference_state=reference_directory / "cloud-evaluation.json"
        if reference_directory
        else None,
    )
    if business_evaluator:
        local = {item["case_id"]: item["passed"] for item in summarize(rows, cases)["checks"]}
        cloud = {
            row["case_id"]: next(
                item["passed"] for item in row["results"] if item["name"] == BUSINESS_EVALUATOR
            )
            for row in read_json(directory / "cloud-evaluation-results.json")
        }
        mismatched = sorted(case for case, passed in local.items() if cloud.get(case) != passed)
        agreement = {
            "matched": len(local) - len(mismatched),
            "total": len(local),
            "mismatched_cases": mismatched,
            "local_business_passed": sum(local.values()),
            "note": "A mismatch means the Foundry grader and the local rules disagree; review it, do not pick one.",
        }
        write_json(directory / "business-rubric-agreement.json", agreement)
        result["business_rubric_agreement"] = agreement
        result["preview"] = (
            "Custom code-based evaluators were marked Preview on Microsoft Learn, checked 2026-09-23."
        )
    return result
