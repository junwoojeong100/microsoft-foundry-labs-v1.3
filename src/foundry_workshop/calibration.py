import json
from pathlib import Path
from typing import Any

from .contracts import (
    digest,
    load_documents,
    localized_path,
    read_json,
    read_jsonl,
    safe_label,
    validate_cases,
    write_json,
)
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
    policy: bool = False,
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("Calibration calls a paid judge; explicitly pass --confirm-cost.")
    if policy:
        return calibrate_policy(
            root, settings, label, confirmed=confirmed, timeout=timeout,
            reference_catalog=reference_catalog,
        )
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


def verify_calibration(
    root: Path, label: str, evaluation_directory: Path, *, policy: bool = False
) -> dict[str, Any]:
    path = root / "outputs/judge-calibration" / safe_label(label)
    manifest = read_json(path / "manifest.json")
    if policy:
        return verify_policy_calibration(root, path, evaluation_directory)
    if manifest.get("mode") != "judge-calibration-fixture":
        raise ValueError("Calibration mode differs; explicitly select the matching policy mode.")
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


POLICY_CALIBRATION_MODE = "policy-judge-calibration-fixture"
POLICY_FIXTURE_VERSION = 1
CONTROL_KINDS = {
    "grounded-answer",
    "fabricated-amount",
    "counterfactual-reference",
    "justified-abstention",
    "irrelevant-refusal",
    "false-approval",
    "approval-boundary",
    "fabricated-citation",
}


def policy_calibration_inputs(
    fixture: dict[str, Any], corpus: list[dict[str, Any]], language: str
) -> tuple[list[dict[str, str]], list[list[dict[str, Any]]]]:
    from .policy_evaluation import POLICY_EVALUATORS, build_reference

    if (
        set(fixture) != {"fixture_version", "language", "counterfactual_document", "controls"}
        or fixture["fixture_version"] != POLICY_FIXTURE_VERSION
        or fixture["language"] != language
    ):
        raise ValueError("Use the explicit language/versioned policy calibration fixture.")
    alternative = fixture["counterfactual_document"]
    original = next(doc for doc in corpus if doc["id"] == "TRAVEL-2026")
    if (
        not isinstance(alternative, dict)
        or set(alternative) != set(original)
        or alternative["id"] != original["id"]
        or alternative == original
        or any(not isinstance(value, str) or not value.strip() for value in alternative.values())
    ):
        raise ValueError("A distinct, fully written calibration-only counterfactual source is required.")
    counterfactual = [
        alternative if doc["id"] == alternative["id"] else doc for doc in corpus
    ]
    controls = fixture["controls"]
    if (
        not isinstance(controls, list)
        or len(controls) != len(CONTROL_KINDS)
        or {control.get("control") for control in controls} != CONTROL_KINDS
    ):
        raise ValueError("Policy calibration must retain every positive, negative and counterfactual control.")
    validate_cases([control["case"] for control in controls], corpus)
    items = []
    for control in controls:
        if (
            set(control) != {"control", "case", "reference", "response", "expected_pass"}
            or control["reference"] not in {"original", "counterfactual"}
            or not isinstance(control["response"], str)
            or not control["response"].strip()
            or set(control["expected_pass"]) != set(POLICY_EVALUATORS)
            or any(type(value) is not bool for value in control["expected_pass"].values())
        ):
            raise ValueError("Every policy control needs an explicit response and three Boolean labels.")
        sources = corpus if control["reference"] == "original" else counterfactual
        case = control["case"]
        reference = build_reference(case, sources, sources, origin="calibration-fixture")
        items.append(
            {
                "case_id": case["case_id"],
                "query": case["question"],
                "response": control["response"],
                "context": json.dumps(sources, ensure_ascii=False),
                "ground_truth": json.dumps(reference, ensure_ascii=False),
            }
        )
    by_kind = {control["control"]: control for control in controls}
    positive, swapped = by_kind["grounded-answer"], by_kind["counterfactual-reference"]
    negative = by_kind["fabricated-amount"]
    if (
        positive["case"]["question"] != swapped["case"]["question"]
        or positive["response"] != swapped["response"]
        or positive["reference"] != "original"
        or swapped["reference"] != "counterfactual"
        or negative["reference"] != "original"
        or negative["case"]["question"] != positive["case"]["question"]
        or negative["response"] == positive["response"]
        or not all(positive["expected_pass"].values())
        or any(swapped["expected_pass"].values())
        or any(negative["expected_pass"].values())
        or any(
            {control["expected_pass"][name] for control in controls} != {True, False}
            for name in POLICY_EVALUATORS
        )
    ):
        raise ValueError("Calibration needs the same answer with swapped reference, and both label directions.")
    return items, [corpus, counterfactual]


def policy_calibration_summary(
    fixture: dict[str, Any], results: list[dict[str, Any]]
) -> dict[str, Any]:
    from .policy_evaluation import (
        PASS_THRESHOLD,
        POLICY_EVALUATORS,
        POLICY_MODE,
        validate_policy_score,
    )

    controls = {control["case"]["case_id"]: control for control in fixture["controls"]}
    identifiers = [row["case_id"] for row in results]
    if len(identifiers) != len(controls) or len(identifiers) != len(set(identifiers)) or set(identifiers) != set(controls):
        raise ValueError("Policy calibration cannot omit, duplicate or substitute a control.")
    metrics = {
        name: {
            "true_positive": 0, "true_negative": 0, "false_positive": 0, "false_negative": 0
        }
        for name in POLICY_EVALUATORS
    }
    judgments = []
    for row in results:
        if len(row["results"]) != len(POLICY_EVALUATORS) or {
            score["name"] for score in row["results"]
        } != set(POLICY_EVALUATORS):
            raise ValueError("Policy calibration requires exactly three pinned policy judgments.")
        for score in row["results"]:
            validate_policy_score(score)
            expected = controls[row["case_id"]]["expected_pass"][score["name"]]
            actual = score["passed"]
            key = (
                "true_positive" if expected and actual
                else "true_negative" if not expected and not actual
                else "false_positive" if actual
                else "false_negative"
            )
            metrics[score["name"]][key] += 1
            judgments.append({
                "case_id": row["case_id"], "control": controls[row["case_id"]]["control"],
                "metric": score["name"], "expected_pass": expected,
                "actual_pass": actual, "score": score["score"], "matched": expected == actual,
            })
    return {
        "mode": POLICY_CALIBRATION_MODE,
        "policy_mode": POLICY_MODE,
        "fixture_version": POLICY_FIXTURE_VERSION,
        "target_responses_generated": False,
        "threshold": PASS_THRESHOLD,
        "direction": "higher-is-better-and-safer",
        "total_controls": len(controls),
        "total_judgments": len(judgments),
        "correct": sum(item["matched"] for item in judgments),
        "metrics": metrics,
        "judgments": judgments,
        "gate_passed": all(item["matched"] for item in judgments),
        "human_review_claimed": False,
        "production_approval": False,
        "note": "Prewritten controls test reference dependency and judge direction, not generated agent quality or broad safety.",
    }


def calibrate_policy(
    root: Path,
    settings: Settings,
    label: str,
    *,
    confirmed: bool,
    timeout: int,
    reference_catalog: Path | None,
) -> dict[str, Any]:
    from .cloud import project_clients
    from .policy_evaluation import (
        POLICY_EVALUATORS,
        POLICY_MODE,
        criteria_hash,
        ensure_policy_evaluators,
    )
    from .settings import owned_prefix, require_env

    if not confirmed or not 5 <= timeout <= 900:
        raise ValueError("Policy calibration requires --confirm-cost and a timeout of 5-900 seconds.")
    fixture = read_json(
        localized_path(root, "data/evaluation/policy-calibration.json", settings.language)
    )
    corpus = load_documents(root, settings.language)
    items, corpora = policy_calibration_inputs(fixture, corpus, settings.language)
    path = root / "outputs/judge-calibration" / safe_label(label)
    manifest = {
        "mode": POLICY_CALIBRATION_MODE,
        "policy_mode": POLICY_MODE,
        "criteria_hash": criteria_hash(),
        "fixture_version": POLICY_FIXTURE_VERSION,
        "language": settings.language,
        "dataset_hash": digest(fixture),
        "input_hash": digest(items),
        "source_corpora_hash": digest(corpora),
        "target_responses_generated": False,
        "expected_rows": len(items),
    }
    for name, value in (("manifest.json", manifest), ("dataset.json", fixture), ("corpus.json", corpus)):
        existing = path / name
        if existing.exists():
            if read_json(existing) != value:
                raise ValueError("Calibration metadata/fixtures changed; preserve this evidence and use a new label.")
        else:
            write_json(existing, value, overwrite=False)
    custom = None
    if reference_catalog is None and not (path / "evaluator-catalog.json").exists():
        with project_clients(settings, preview=True) as (project, _client):
            custom = ensure_policy_evaluators(
                project, owned_prefix(), require_env("AZURE_AI_EVALUATION_MODEL_DEPLOYMENT_NAME")
            )
    evaluation = evaluate_items(
        settings,
        path,
        items,
        label=label,
        source_run_id=f"policy-calibration-{label}",
        dataset_hash=manifest["dataset_hash"],
        forbidden_deployments=set(model_deployments(settings).values()),
        evaluator_names=POLICY_EVALUATORS,
        confirmed=confirmed,
        timeout=timeout,
        reference_catalog=reference_catalog,
        custom_catalog=custom,
        policy_reference_audit=True,
        policy_source_corpora=corpora,
    )
    _, scores = verified_native(path)
    summary = {**policy_calibration_summary(fixture, scores), "native_evaluation": evaluation}
    output = path / "calibration.json"
    if output.exists():
        if read_json(output) != summary:
            raise ValueError("Do not overwrite prior calibration evidence with changed results.")
    else:
        write_json(output, summary, overwrite=False)
    return summary


def verify_policy_calibration(
    root: Path, path: Path, evaluation_directory: Path
) -> dict[str, Any]:
    from .policy_evaluation import POLICY_MODE, criteria_hash

    manifest = read_json(path / "manifest.json")
    if (
        manifest.get("mode") != POLICY_CALIBRATION_MODE
        or manifest.get("policy_mode") != POLICY_MODE
        or manifest.get("criteria_hash") != criteria_hash()
        or manifest.get("fixture_version") != POLICY_FIXTURE_VERSION
        or manifest.get("target_responses_generated") is not False
    ):
        raise ValueError("A fresh, explicitly versioned policy calibration is required; legacy grounding is not enough.")
    fixture = read_json(path / "dataset.json")
    corpus = read_json(path / "corpus.json")
    language = manifest.get("language")
    bundled = read_json(localized_path(root, "data/evaluation/policy-calibration.json", language))
    if fixture != bundled or corpus != load_documents(root, language):
        raise ValueError("Calibration fixtures or original reference corpus differ from their frozen version.")
    items, corpora = policy_calibration_inputs(fixture, corpus, language)
    if (
        manifest.get("dataset_hash") != digest(fixture)
        or manifest.get("input_hash") != digest(items)
        or manifest.get("source_corpora_hash") != digest(corpora)
        or manifest.get("expected_rows") != len(items)
    ):
        raise ValueError("Policy calibration metadata/hash/denominator changed.")
    state, results = verified_native(path)
    target, _ = verified_native(evaluation_directory)
    target_corpora = read_json(evaluation_directory / "policy-source-corpora.json")
    if (
        state.get("input_hash") != digest(items)
        or state.get("dataset_hash") != digest(fixture)
        or state.get("policy_source_corpora_hash") != digest(corpora)
        or target.get("policy_mode") != POLICY_MODE
        or state["project_endpoint"] != target["project_endpoint"]
        or state["judge_deployment"] != target["judge_deployment"]
        or state["evaluator_hash"] != target["evaluator_hash"]
        or corpus not in target_corpora
    ):
        raise ValueError("Policy calibration must match the source language/corpus, criteria/version, threshold, project and judge.")
    return policy_calibration_summary(fixture, results)
