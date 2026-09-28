import copy
import json
import os
import shlex
import unittest
from dataclasses import replace
from unittest.mock import patch

from foundry_workshop.benchmark import (
    collect_matrix,
    directory,
    grade_strict,
    load_matrix,
    native_items,
    verify_release,
)
from foundry_workshop.cli import parser
from foundry_workshop.contracts import digest, load_cases, load_documents, read_json, write_json
from foundry_workshop.knowledge import evidence
from foundry_workshop.policy_evaluation import POLICY_EVALUATORS, POLICY_MODE, load_lab_cases
from foundry_workshop.profiles import RuntimeProfile, runtime_contract

from . import ROOT, workspace
from .test_benchmark import MODELS, UnitTransport, binding, settings


class LabTransport(UnitTransport):
    def __init__(self, root, profile, fail=None):
        self.contract = runtime_contract(root, replace(settings(), language=profile.language), profile)
        self.cases = {case["case_id"]: case for case in load_lab_cases(root, profile.language)}
        self.context = evidence(load_documents(root, profile.language), "unit-test")
        self.fail, self.text, self.requests = fail, None, []


class PolicyBenchmarkTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {
            "WORKSHOP_MODEL_DEPLOYMENTS_JSON": json.dumps(MODELS),
        }, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def collect(self, root, *, language="ko", fail=None):
        profile = RuntimeProfile(protocol="invocations", language=language)
        transport = LabTransport(root, profile, fail=fail)
        result = collect_matrix(
            root, replace(settings(), language=language), profile, binding(), label="diagnostic", split="dev",
            suite="policy-lab", model_keys=["alpha"], confirmed=True,
            transport_factory=lambda *_: transport,
        )
        return result, transport

    def test_explicit_bilingual_diagnostics_preserve_query_only_requests_and_original_dev(self):
        for language in ("ko", "en"):
            with self.subTest(language=language), workspace() as root:
                before = digest(load_cases(root, "dev", language))
                result, transport = self.collect(root, language=language)
                manifest, rows, cases = load_matrix(root, "diagnostic")
                self.assertEqual(result["actual_rows"], 8)
                self.assertEqual(result["policy_lab_counts"]["requested"], 8)
                self.assertEqual(result["policy_lab_counts"]["returned"], 8)
                self.assertEqual(manifest["suite"], "policy-lab")
                self.assertEqual(manifest["suite_version"], 2)
                self.assertFalse(manifest["holdout_eligible"])
                self.assertEqual(before, digest(load_cases(root, "dev", language)))
                self.assertEqual(len(transport.requests), 8)
                for request in transport.requests:
                    self.assertEqual(set(request), {"question", "case_id", "model_key", "run_id"})
                    self.assertNotIn("expected_", json.dumps(request))
                    self.assertNotIn("ground_truth", request)
                self.assertEqual([row["question"] for row in rows], [case["question"] for case in cases])
                self.assertTrue(all(row["response_id"] for row in rows))
                self.assertEqual(len(native_items(root, "diagnostic", policy=True)[1]), 8)

    def test_frozen_version_one_suite_remains_readable_without_rewriting_any_evidence(self):
        with workspace() as root:
            legacy = [
                {key: value for key, value in case.items() if key != "allowed_citations"}
                for case in load_lab_cases(root, "ko")
            ]
            with (
                patch("foundry_workshop.policy_evaluation.LAB_SUITE_VERSION", 1),
                patch("foundry_workshop.policy_evaluation.load_lab_cases", return_value=legacy),
            ):
                self.collect(root)
            path = directory(root, "diagnostic")
            before = {
                file.relative_to(path): file.read_bytes()
                for file in path.rglob("*") if file.is_file()
            }
            manifest, _, cases = load_matrix(root, "diagnostic")
            self.assertEqual(manifest["suite_version"], 1)
            self.assertEqual(cases, legacy)
            self.assertFalse(any("allowed_citations" in case for case in cases))
            self.assertEqual(before, {
                file.relative_to(path): file.read_bytes()
                for file in path.rglob("*") if file.is_file()
            })

    def test_version_one_cannot_reinterpret_new_allowlists_as_an_old_frozen_contract(self):
        with workspace() as root:
            self.collect(root)
            path = directory(root, "diagnostic") / "manifest.json"
            manifest = read_json(path)
            manifest["suite_version"] = 1
            write_json(path, manifest)
            with self.assertRaisesRegex(ValueError, "version 1 cannot add allowed_citations"):
                load_matrix(root, "diagnostic")

    def test_collection_error_stays_in_denominator_and_has_no_synthetic_native_response(self):
        with workspace() as root:
            result, _ = self.collect(root, fail=("alpha", "PL03"))
            self.assertFalse(result["gate_passed"])
            self.assertEqual(result["policy_lab_counts"], {
                "requested": 8, "returned": 7, "missing": 1, "errors": 1,
                "errors_remain_in_denominator": True,
            })
            _, rows, _ = load_matrix(root, "diagnostic")
            self.assertEqual(len(rows), 8)
            self.assertEqual(next(row for row in rows if row["case_id"] == "PL03")["status"], "error")
            with self.assertRaisesRegex(ValueError, "every actual"):
                native_items(root, "diagnostic")
            _, items = native_items(root, "diagnostic", policy=True)
            self.assertEqual(len(items), 7)
            self.assertNotIn("alpha-PL03", [item["case_id"] for item in items])
            previous = (directory(root, "diagnostic") / "responses.jsonl").read_bytes()
            with self.assertRaises(FileExistsError):
                self.collect(root)
            self.assertEqual(previous, (directory(root, "diagnostic") / "responses.jsonl").read_bytes())

    def test_diagnostic_suite_never_reads_or_opens_holdout_even_when_requested(self):
        with (
            workspace() as root,
            patch("foundry_workshop.benchmark.load_cases") as load,
            patch("foundry_workshop.benchmark.runtime_contract") as contract,
        ):
            for options in (
                {"split": "holdout", "unlock_holdout": True, "candidate": "dev"},
                {"split": "dev", "regressions": "reviewed"},
                {"split": "dev", "candidate": "dev"},
            ):
                with self.assertRaisesRegex(ValueError, "diagnostic dev only"):
                    collect_matrix(
                        root, settings(), RuntimeProfile(protocol="invocations"), binding(),
                        label="no-holdout", confirmed=True, suite="policy-lab", **options,
                    )
            load.assert_not_called()
            contract.assert_not_called()
        with workspace() as root:
            self.collect(root)
            with (
                patch("foundry_workshop.benchmark.load_cases") as load,
                self.assertRaisesRegex(ValueError, "cannot be a frozen holdout"),
            ):
                collect_matrix(
                    root, settings(), RuntimeProfile(protocol="invocations"), binding(),
                    label="not-a-holdout", split="holdout", candidate="diagnostic",
                    model_keys=["alpha"], confirmed=True, unlock_holdout=True,
                )
            load.assert_not_called()
            self.assertFalse(directory(root, "not-a-holdout").exists())

    def test_cli_policy_flags_are_explicit_and_legacy_defaults_stay_off(self):
        for command in (
            ["cloud-evaluate", "--label", "new"],
            ["benchmark", "evaluate", "--label", "new"],
            ["calibrate-judge", "--label", "new"],
            ["prepare-extensions", "--label", "new"],
        ):
            self.assertFalse(parser().parse_args(command).policy)
            self.assertTrue(parser().parse_args([*command, "--policy"]).policy)
        self.assertEqual(parser().parse_args(["benchmark", "collect", "--label", "new"]).suite, "canonical")
        parsed = parser().parse_args([
            "--language", "en", "benchmark", "collect", "--label", "new",
            "--suite", "policy-lab", "--model-key", "chosen-sol",
        ])
        self.assertEqual(parsed.suite, "policy-lab")
        self.assertEqual(parsed.model_key, ["chosen-sol"])
        self.assertEqual(parsed.language, "en")
        report = parser().parse_args([
            "benchmark", "policy-report", "--label", "new", "--calibration", "fresh",
        ])
        self.assertEqual(report.calibration, "fresh")
        self.assertIsNone(report.provider_results)

    def test_policy_release_requires_calibration_and_enforces_each_failed_policy_metric(self):
        # All acceptance inputs below are test doubles; no bundled holdout is loaded.
        with workspace() as root:
            with self.assertRaisesRegex(ValueError, "fresh matching policy controls"):
                verify_release(
                    root, "baseline", "candidate", "unopened",
                    require_native=True, require_traces=False, policy=True,
                )
            models = ["alpha"]
            common = {
                "split": "dev", "model_keys": models, "runtime_contract": {"unit": True},
                "binding": {"unit": True}, "reviewed_regressions": {}, "dataset_hash": "unit-dataset",
            }
            baseline = {**common, "run_id": "unit-baseline"}
            candidate = {**common, "run_id": "unit-candidate"}
            final = {
                **common, "run_id": "unit-final", "split": "holdout",
                "frozen_candidate": {"label": "candidate", "manifest_hash": digest(candidate), "model_keys": models},
            }
            row = {"row_id": "alpha-UNIT", "case_id": "UNIT", "model_key": "alpha"}
            runs = {label: (manifest, [row], []) for label, manifest in (
                ("baseline", baseline), ("candidate", candidate), ("unopened", final)
            )}
            submitted = [{"case_id": row["row_id"], "unit": "not an actual holdout input"}]

            def native(path):
                label = path.parent.name
                state = {
                    "source_run_id": runs[label][0]["run_id"],
                    "input_hash": digest(submitted), "dataset_hash": "unit-dataset",
                    "evaluator_hash": "unit-policy-catalog", "evaluation_id": "unit-eval",
                    "run_id": "unit-" + label, "policy_mode": POLICY_MODE,
                }
                scores = [{
                    "case_id": row["row_id"],
                    "results": [
                        {"name": metric, "score": 1 if label == "candidate" and metric == "policy_helpfulness" else 5,
                         "passed": not (label == "candidate" and metric == "policy_helpfulness")}
                        for metric in POLICY_EVALUATORS
                    ],
                }]
                return state, scores

            with (
                patch("foundry_workshop.benchmark.compare_matrices"),
                patch("foundry_workshop.benchmark.load_matrix", side_effect=lambda _root, label: copy.deepcopy(runs[label])),
                patch("foundry_workshop.benchmark.summarize_matrix", return_value={
                    "errors": 0, "models": {"alpha": {"business_gate_passed": True}},
                }),
                patch("foundry_workshop.benchmark.native_items", return_value=({}, submitted)),
                patch("foundry_workshop.native.verified_native", side_effect=native),
                patch("foundry_workshop.calibration.verify_calibration", return_value={"gate_passed": True}) as calibration,
            ):
                report = verify_release(
                    root, "baseline", "candidate", "unopened", require_native=True,
                    require_traces=False, require_native_pass=True, calibration_label="fresh", policy=True,
                )
            self.assertFalse(report["gate_passed"])
            self.assertFalse(report["native_quality_passed"])
            self.assertEqual(report["native"]["candidate"]["failed_items"][0]["evaluator"], "policy_helpfulness")
            self.assertEqual(calibration.call_args.kwargs, {"policy": True})
            self.assertFalse(report["deployment_approved"])
            self.assertTrue((directory(root, "unopened") / "foundry-policy/release-verification.json").is_file())
            self.assertFalse((directory(root, "unopened") / "release-verification.json").exists())

    def test_learner_acceptance_commands_require_passing_policy_scores(self):
        for relative in ("docs/15-capstone-cleanup.md", "docs/en/15-capstone-cleanup.md"):
            commands = [
                line for line in (ROOT / relative).read_text(encoding="utf-8").splitlines()
                if line.startswith("python scripts/workshop.py ") and " benchmark verify " in line
            ]
            self.assertTrue(commands, f"No Hosted acceptance commands in {relative}")
            for command in commands:
                with self.subTest(guide=relative, command=command):
                    args = parser().parse_args(shlex.split(command)[2:])
                    self.assertTrue(args.policy)
                    self.assertTrue(args.require_native)
                    self.assertTrue(args.require_native_pass)
                    self.assertTrue(args.require_traces)
                    self.assertTrue(args.calibration)


class PolicyCitationRubricTests(unittest.TestCase):
    def row(self, case, language="en"):
        text = {
            "PL05": (
                "Please provide the travel date. Through June 30, 2026 the nightly limit is "
                "120000; from July 1 it is 150000. I cannot choose one limit without the date."
            ),
            "PL06": (
                "A lodging receipt is required. Ask finance about alternative supporting "
                "evidence for a lost receipt. I cannot waive evidence or execute reimbursement."
            ),
            "PL07": (
                "Meals are 30000 per person per day. Lodging is separately 150000 per person "
                "per night; do not combine these into a single nightly limit."
            ),
        }.get(case["case_id"], f"The applicable nightly lodging limit is {case['expected_limit_krw']}.")
        return {
            "case_id": case["case_id"],
            "question": case["question"],
            "status": "ok",
            **evidence(load_documents(ROOT, language), "unit-test"),
            "answer": {
                "answer": text,
                "decision": case["expected_decision"],
                "limit_krw": case["expected_limit_krw"],
                "citations": list(case.get("allowed_citations", case["required_citations"])),
            },
        }

    def test_only_the_three_bilingual_diagnostic_cases_declare_supporting_citations(self):
        expected = {
            "PL05": ["SCOPE-01", "TRAVEL-2025", "TRAVEL-2026"],
            "PL06": ["RECEIPT-01", "TRAVEL-2026"],
            "PL07": ["MEAL-01", "TRAVEL-2026"],
        }
        for language in ("ko", "en"):
            cases = load_lab_cases(ROOT, language)
            self.assertEqual({
                case["case_id"]: case["allowed_citations"]
                for case in cases if "allowed_citations" in case
            }, expected)
            self.assertFalse(any("allowed_citations" in case for case in load_cases(ROOT, "dev", language)))

    def test_relevant_retrieved_support_citations_pass_only_with_an_explicit_allowlist(self):
        for language in ("ko", "en"):
            for case in load_lab_cases(ROOT, language):
                if "allowed_citations" not in case:
                    continue
                with self.subTest(language=language, case_id=case["case_id"]):
                    row = self.row(case, language)
                    result = grade_strict(row, case)
                    self.assertTrue(result["passed"])
                    self.assertTrue(result["checks"]["required_citations"])
                    self.assertTrue(result["checks"]["citations_retrieved"])
                    legacy = {key: value for key, value in case.items() if key != "allowed_citations"}
                    self.assertFalse(grade_strict(row, legacy)["checks"]["citations_relevant"])

    def test_allowlists_do_not_waive_mandatory_references_or_retrieval(self):
        case = next(case for case in load_lab_cases(ROOT, "en") if case["case_id"] == "PL07")
        row = self.row(case)
        row["answer"]["citations"] = ["TRAVEL-2026"]
        result = grade_strict(row, case)
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["required_citations"])
        self.assertTrue(result["checks"]["citations_relevant"])
        row = self.row(case)
        row["source_ids"] = ["MEAL-01"]
        result = grade_strict(row, case)
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["citations_retrieved"])

    def test_unrelated_known_and_unknown_extras_still_fail_exact_allowlists(self):
        case = next(case for case in load_lab_cases(ROOT, "en") if case["case_id"] == "PL05")
        for extra in ("MEAL-01", "APPROVAL-01", "RECEIPT-01", "UNKNOWN-01"):
            with self.subTest(extra=extra):
                row = self.row(case)
                row["answer"]["citations"].append(extra)
                result = grade_strict(row, case)
                self.assertFalse(result["passed"])
                self.assertFalse(result["checks"]["citations_relevant"])
                self.assertTrue(result["checks"]["required_citations"])

    def test_legacy_lodging_exceptions_are_preserved_but_do_not_expand_explicit_sets(self):
        case = load_cases(ROOT, "dev", "en")[0]
        row = self.row(case)
        row["answer"]["citations"] += ["APPROVAL-01", "RECEIPT-01"]
        self.assertTrue(grade_strict(row, case)["passed"])
        explicit = {**case, "allowed_citations": list(case["required_citations"])}
        self.assertFalse(grade_strict(row, explicit)["checks"]["citations_relevant"])
        row["answer"]["citations"].append("MEAL-01")
        self.assertFalse(grade_strict(row, case)["checks"]["citations_relevant"])

    def test_procedure_only_case_still_requires_null_limit(self):
        case = next(case for case in load_lab_cases(ROOT, "en") if case["case_id"] == "PL06")
        self.assertIsNone(case["expected_limit_krw"])
        row = self.row(case)
        row["answer"]["limit_krw"] = 150000
        result = grade_strict(row, case)
        self.assertTrue(result["checks"]["citations_relevant"])
        self.assertFalse(result["checks"]["limit_krw"])
        self.assertFalse(result["passed"])
