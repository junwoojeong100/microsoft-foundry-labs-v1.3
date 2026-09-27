from pathlib import Path
from typing import Any

from .contracts import digest, localized_path, read_json, read_jsonl, safe_label, write_json
from .native import evaluate_items, verified_native
from .profiles import model_deployments
from .settings import Settings


def calibration_summary(
    cases: list[dict[str, Any]], results: list[dict[str, Any]]
) -> dict[str, Any]:
    if not cases:
        raise ValueError("An empty calibration cannot pass.")
    expected = {case["case_id"]: case["expected_grounded"] for case in cases}
    if len(expected) != len(cases) or any(type(value) is not bool for value in expected.values()):
        raise ValueError("Calibration needs unique cases and explicit Boolean reference judgments.")
    if set(expected.values()) != {True, False}:
        raise ValueError("Calibration must include both correct and incorrect reference examples.")
    if len(results) != len(cases) or {item["case_id"] for item in results} != set(expected):
        raise ValueError("Calibration cannot omit, duplicate or substitute a fixture.")
    confusion = {"true_positive": 0, "true_negative": 0, "false_positive": 0, "false_negative": 0}
    for item in results:
        scores = item.get("results")
        if (
            not isinstance(scores, list)
            or len(scores) != 1
            or scores[0].get("name") != "groundedness"
        ):
            raise ValueError("Calibration requires exactly the pinned groundedness result.")
        actual = scores[0].get("passed")
        if type(actual) is not bool or scores[0].get("error"):
            raise ValueError("Missing/error calibration judgments cannot count as correct.")
        reference = expected[item["case_id"]]
        key = (
            "true_positive"
            if reference and actual
            else "true_negative"
            if not reference and not actual
            else "false_positive"
            if actual
            else "false_negative"
        )
        confusion[key] += 1
    correct = confusion["true_positive"] + confusion["true_negative"]
    return {
        "mode": "judge-calibration-fixture",
        "target_responses_generated": False,
        "total": len(cases),
        "correct": correct,
        "confusion": confusion,
        "gate_passed": correct == len(cases),
        "note": "Prewritten correct/incorrect answers test the judge, not an agent. Two cases do not certify general judge quality.",
    }


def calibrate(
    root: Path,
    settings: Settings,
    label: str,
    *,
    confirmed: bool,
    timeout: int,
    reference_catalog: Path | None = None,
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("Calibration calls a paid judge; explicitly pass --confirm-cost.")
    cases = read_jsonl(localized_path(root, "data/evaluation/calibration.jsonl", settings.language))
    if any(
        set(case) != {"case_id", "query", "context", "response", "expected_grounded"}
        or type(case["expected_grounded"]) is not bool
        for case in cases
    ):
        raise ValueError("Use the bundled, versioned calibration fixture contract.")
    path = root / "outputs/judge-calibration" / safe_label(label)
    path.mkdir(parents=True, exist_ok=True)
    manifest = {
        "mode": "judge-calibration-fixture",
        "dataset_hash": digest(cases),
        "target_responses_generated": False,
        "expected_rows": len(cases),
    }
    if settings.language != "ko":
        manifest["language"] = settings.language
    old = path / "manifest.json"
    if old.exists() and read_json(old) != manifest:
        raise ValueError("The calibration fixtures changed; use a new version/label.")
    write_json(old, manifest)
    write_json(path / "dataset.json", cases)
    items = [
        {key: case[key] for key in ("case_id", "query", "context", "response")} for case in cases
    ]
    evaluation = evaluate_items(
        settings,
        path,
        items,
        label=label,
        source_run_id=f"calibration-{label}",
        dataset_hash=manifest["dataset_hash"],
        forbidden_deployments=set(model_deployments(settings).values()),
        evaluator_names=("groundedness",),
        confirmed=confirmed,
        timeout=timeout,
        reference_catalog=reference_catalog,
    )
    _, native = verified_native(path)
    summary = calibration_summary(cases, native)
    write_json(path / "calibration.json", {**summary, "native_evaluation": evaluation})
    return {**summary, "native_evaluation": evaluation}


def verify_calibration(root: Path, label: str, evaluation_directory: Path) -> dict[str, Any]:
    path = root / "outputs/judge-calibration" / safe_label(label)
    manifest = read_json(path / "manifest.json")
    cases = read_json(path / "dataset.json")
    if manifest["dataset_hash"] != digest(cases):
        raise ValueError("Calibration input lineage changed.")
    state, scores = verified_native(path)
    if state.get("dataset_hash") != manifest["dataset_hash"]:
        raise ValueError(
            "The calibration judgment labels differ from the submitted fixture version."
        )
    target, _ = verified_native(evaluation_directory)
    if (
        state["project_endpoint"] != target["project_endpoint"]
        or state["judge_deployment"] != target["judge_deployment"]
    ):
        raise ValueError("The calibration used a different project or judge.")
    calibrated = read_json(path / "evaluator-catalog.json")
    groundedness = [
        item
        for item in read_json(evaluation_directory / "evaluator-catalog.json")
        if item["name"] == "groundedness"
    ]
    if digest(calibrated) != digest(groundedness):
        raise ValueError("The groundedness evaluator/version/threshold differs from calibration.")
    return calibration_summary(cases, scores)
