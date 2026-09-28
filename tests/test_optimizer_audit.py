import copy
import importlib.util
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from foundry_workshop.calibration import (
    POLICY_CALIBRATION_MODE,
    policy_calibration_inputs,
)
from foundry_workshop.cloud_evaluation import normalize_results
from foundry_workshop.contracts import digest, load_documents, read_json, write_json
from foundry_workshop.policy_evaluation import (
    POLICY_EVALUATORS,
    POLICY_MODE,
    audit_policy_results,
    criteria_hash,
    optimizer_items,
)

from . import ROOT, workspace
from .test_policy_evaluation import policy_catalog, policy_outputs

spec = importlib.util.spec_from_file_location("optimizer_audit", ROOT / "scripts/audit_optimizer.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OptimizerAuditTests(unittest.TestCase):
    """Synthetic exported receipts and calibration scores; never live inference."""

    def setUp(self):
        self.root = self.enterContext(workspace())
        self.export = self.root / "outputs/export"
        self.dataset = self.root / "outputs/prepared/optimizer-dev.jsonl"
        self.dataset.parent.mkdir(parents=True)
        self.prepared = optimizer_items(self.root, "ko")
        self.dataset.write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in self.prepared),
            encoding="utf-8",
        )
        self.catalog = policy_catalog()
        self.seed_calibration()
        self.definition = {
            "id": "eval_unit_optimizer",
            "testing_criteria": [
                {
                    "type": "azure_ai_evaluator",
                    "name": item["evaluator_name"],
                    "evaluator_name": item["evaluator_name"],
                    "evaluator_version": item["definition"]["version"],
                    "initialization_parameters": {
                        **item["parameters"], "deployment_name": item["parameters"]["model"]
                    },
                    "data_mapping": {**module.OPTIMIZER_MAPPING, **module.OPTIONAL_MAPPING},
                }
                for item in self.catalog
            ],
        }
        self.run = {
            "id": "evalrun_unit_optimizer",
            "eval_id": self.definition["id"],
            "name": "baseline",
            "status": "completed",
            "data_source": {
                "type": "azure_ai_target_completions",
                "source": {
                    "type": "file_content",
                    "content": [
                        {"item": {
                            "item_id": index, "query": item["query"], "ground_truth": item["ground_truth"],
                        }, "sample": None}
                        for index, item in enumerate(self.prepared)
                    ],
                },
                "input_messages": {"type": "template", "template": [
                    {"role": "user", "content": "{{item.query}}", "type": "message"}
                ]},
                "target": {"type": "azure_ai_agent", "name": "unit-agent", "version": "draft-unit"},
            },
        }
        self.outputs = []
        for index, item in enumerate(self.prepared):
            reference_id = json.loads(item["ground_truth"])["reference_id"]
            self.outputs.append({
                "id": str(index + 1),
                "eval_id": self.definition["id"],
                "run_id": self.run["id"],
                "status": "completed",
                "datasource_item_id": index,
                "datasource_item": {
                    "item_id": index, "query": item["query"], "ground_truth": item["ground_truth"],
                    "sample.output_text": f"Explicit test output for {item['case_id']}; not an LLM response.",
                    "response_id": f"resp_unit_{index}",
                    "agent_name": "unit-agent", "agent_version": "draft-unit",
                    "trace_id": f"unit-trace-{index}",
                },
                "sample": {
                    "model": "unit-target",
                    "input": [{"role": "user", "content": item["query"]}],
                    "error": None,
                },
                "results": [{
                    "name": entry["evaluator_name"], "score": 5.0, "passed": True,
                    "threshold": 4, "status": "completed",
                    "reason": f"Explicit test reference: {reference_id}.",
                    "sample": {"model": "unit-judge-model-v1", "usage": {"total_tokens": 10}},
                    "preserve_provider_field": {"original": True},
                } for entry in self.catalog],
            })
        self.write_export()

    def seed_calibration(self, *, miscalibrated=False):
        path = self.root / "outputs/judge-calibration/unit-controls"
        corpus = load_documents(self.root, "ko")
        fixture = read_json(self.root / "data/evaluation/policy-calibration.json")
        inputs, corpora = policy_calibration_inputs(fixture, corpus, "ko")
        labels = {
            control["case"]["case_id"]: copy.deepcopy(control["expected_pass"])
            for control in fixture["controls"]
        }
        if miscalibrated:
            labels["PC02"]["policy_groundedness"] = True
        raw = policy_outputs(inputs, labels)
        for row in raw:
            for result in row["results"]:
                result["sample"]["model"] = "unit-judge-model-v1"
        results = normalize_results(raw, list(labels), POLICY_EVALUATORS)
        audit = audit_policy_results(inputs, raw, results, corpora, self.catalog)
        manifest = {
            "mode": POLICY_CALIBRATION_MODE, "policy_mode": POLICY_MODE,
            "criteria_hash": criteria_hash(), "fixture_version": 1, "language": "ko",
            "dataset_hash": digest(fixture), "input_hash": digest(inputs),
            "source_corpora_hash": digest(corpora), "expected_rows": len(inputs),
            "target_responses_generated": False,
        }
        state = {
            "status": "completed", "validation_status": "valid",
            "source_run_id": "unit-calibration-source", "evaluation_id": "eval_unit_calibration",
            "run_id": "evalrun_unit_calibration", "judge_deployment": "unit-judge",
            "project_endpoint": "https://unit.services.ai.azure.com/api/projects/workshop",
            "input_hash": digest(inputs), "dataset_hash": digest(fixture),
            "results_hash": digest(results), "evaluator_hash": digest(self.catalog),
            "evaluator_names": list(POLICY_EVALUATORS),
            "policy_mode": POLICY_MODE, "policy_criteria_hash": criteria_hash(),
            "policy_source_corpora_hash": digest(corpora), "policy_reference_audit_hash": digest(audit),
        }
        for name, value in {
            "manifest.json": manifest, "dataset.json": fixture, "corpus.json": corpus,
            "evaluator-catalog.json": self.catalog, "cloud-evaluation.json": state,
            "cloud-evaluation-raw.json": raw, "cloud-evaluation-results.json": results,
            "policy-evaluation-inputs.json": inputs, "policy-source-corpora.json": corpora,
            "policy-reference-audit.json": audit,
        }.items():
            write_json(path / name, value)

    def write_export(self):
        summary = {
            "evaluation_id": self.definition["id"], "run_id": self.run["id"],
            "expected_rows": 6, "actual_rows": len(self.outputs),
            "definition_hash": digest(self.definition), "run_hash": digest(self.run),
            "output_items_hash": digest(self.outputs), "judge_inputs_available": False,
        }
        for name, value in (
            ("definition", self.definition), ("run", self.run),
            ("output-items", self.outputs), ("summary", summary),
        ):
            write_json(self.export / f"{name}.json", value)

    def audit(self):
        return module.audit_optimizer(self.root, self.export, self.dataset, "unit-controls")

    def arguments(self):
        return [
            "--export-directory", str(self.export), "--dataset", str(self.dataset),
            "--calibration-label", "unit-controls",
        ]

    def test_source_echo_audit_accepts_no_case_id_and_no_internal_judge_inputs_without_mutation(self):
        before = {
            file.relative_to(self.root): file.read_bytes()
            for file in (self.root / "outputs").rglob("*") if file.is_file()
        }
        with patch("foundry_workshop.native.project_clients") as clients:
            report = self.audit()
            clients.assert_not_called()
        self.assertEqual(report["validation_status"], "valid")
        self.assertEqual(report["counts"], {"requested": 6, "returned": 6, "matched": 6, "missing": 0, "extra": 0})
        self.assertFalse(report["internal_judge_requests_captured"])
        self.assertFalse(report["improvement_claimed"])
        self.assertFalse(report["candidate_generation_assessed"])
        self.assertFalse(report["holdout_loaded"])
        self.assertEqual(report["calibration"]["summary"]["correct"], 24)
        self.assertTrue(all(item["passed"] == 6 for item in report["evaluators"]))
        self.assertEqual(report["rows"][0]["original_results"], self.outputs[0]["results"])
        self.assertIn("sha256", report["artifacts"]["prepared_dataset"])
        self.assertEqual(before, {
            file.relative_to(self.root): file.read_bytes()
            for file in (self.root / "outputs").rglob("*") if file.is_file()
        })

    def test_canonical_json_equality_and_reordered_results_do_not_depend_on_serialization(self):
        self.outputs.reverse()
        self.run["data_source"]["source"]["content"].reverse()
        for output in self.outputs:
            source = output["datasource_item"]
            source["ground_truth"] = json.dumps(json.loads(source["ground_truth"]), sort_keys=True, indent=2)
        self.write_export()
        self.assertEqual(self.audit()["counts"]["matched"], 6)

    def test_missing_query_can_only_use_item_id_verified_against_submitted_original_inputs(self):
        del self.outputs[0]["datasource_item"]["query"]
        self.write_export()
        self.assertEqual(self.audit()["rows"][0]["match_method"], "verified-item-id")
        self.outputs[0]["datasource_item"]["item_id"] = "unregistered"
        self.write_export()
        with self.assertRaises(ValueError):
            self.audit()

    def test_exact_query_matching_does_not_require_an_echoed_item_id(self):
        del self.outputs[0]["datasource_item"]["item_id"]
        self.write_export()
        self.assertEqual(self.audit()["rows"][0]["match_method"], "exact-query")

    def test_reference_mismatch_self_reference_and_missing_echo_never_pass(self):
        original = copy.deepcopy(self.outputs)
        for change in ("different-reference", "self-reference", "missing-reference", "no-echo", "query-conflict", "id-conflict"):
            with self.subTest(change=change):
                self.outputs = copy.deepcopy(original)
                source = self.outputs[0]["datasource_item"]
                if change == "different-reference":
                    source["ground_truth"] = self.outputs[1]["datasource_item"]["ground_truth"]
                elif change == "self-reference":
                    source["ground_truth"] = source["sample.output_text"]
                elif change == "missing-reference":
                    source.pop("ground_truth")
                elif change == "no-echo":
                    self.outputs[0].pop("datasource_item")
                elif change == "query-conflict":
                    source["query"] = "An unrelated query must not fall back to a matching item ID."
                else:
                    source["item_id"] = 1
                self.write_export()
                with self.assertRaises(ValueError):
                    self.audit()

    def test_missing_extra_duplicate_cases_or_response_ids_never_pass(self):
        original = copy.deepcopy(self.outputs)
        for change in ("missing", "extra", "duplicate", "response-id", "duplicate-response", "empty-output"):
            with self.subTest(change=change):
                self.outputs = copy.deepcopy(original)
                if change == "missing":
                    self.outputs.pop()
                elif change == "extra":
                    self.outputs.append(copy.deepcopy(original[0]))
                elif change == "duplicate":
                    self.outputs[1] = copy.deepcopy(self.outputs[0])
                elif change == "response-id":
                    self.outputs[0]["datasource_item"].pop("response_id")
                elif change == "duplicate-response":
                    self.outputs[1]["datasource_item"]["response_id"] = self.outputs[0]["datasource_item"]["response_id"]
                else:
                    self.outputs[0]["datasource_item"]["sample.output_text"] = ""
                self.write_export()
                with self.assertRaises(ValueError):
                    self.audit()

    def test_evaluator_version_mapping_judge_and_threshold_must_match_calibration(self):
        original = copy.deepcopy(self.definition)
        for change in ("version", "judge", "alias", "threshold", "mapping", "missing-evaluator"):
            with self.subTest(change=change):
                self.definition = copy.deepcopy(original)
                criterion = self.definition["testing_criteria"][0]
                if change == "version":
                    criterion["evaluator_version"] = "99"
                elif change == "judge":
                    criterion["initialization_parameters"]["model"] = "other"
                elif change == "alias":
                    criterion["initialization_parameters"]["deployment_name"] = "other"
                elif change == "threshold":
                    criterion["initialization_parameters"]["pass_threshold"] = 1
                elif change == "mapping":
                    criterion["data_mapping"]["ground_truth"] = "{{sample.output_text}}"
                else:
                    self.definition["testing_criteria"].pop()
                self.write_export()
                with self.assertRaises(ValueError):
                    self.audit()

    def test_prompt_protocol_optimizer_requires_the_calibrated_threshold_and_judge(self):
        catalog = policy_catalog(prompt_protocol=True)
        definition = copy.deepcopy(self.definition)
        for criterion, evaluator in zip(definition["testing_criteria"], catalog, strict=True):
            criterion["initialization_parameters"] = dict(evaluator["parameters"])
        expected = {item["evaluator_name"]: item for item in catalog}
        self.assertEqual(module.check_criteria(definition, catalog, "unit-judge"), expected)
        for change in ("threshold", "missing-threshold", "conflicting-model", "legacy-alias"):
            with self.subTest(change=change):
                changed = copy.deepcopy(definition)
                parameters = changed["testing_criteria"][0]["initialization_parameters"]
                if change == "threshold":
                    parameters["threshold"] = 3
                elif change == "missing-threshold":
                    parameters.pop("threshold")
                elif change == "conflicting-model":
                    parameters["model"] = "other"
                else:
                    parameters["pass_threshold"] = parameters.pop("threshold")
                with self.assertRaises(ValueError):
                    module.check_criteria(changed, catalog, "unit-judge")

    def test_malformed_scores_thresholds_pass_direction_or_reason_ids_never_pass(self):
        original = copy.deepcopy(self.outputs)
        changes = [
            {"score": score} for score in (None, True, "5", 0, 6, 1.5)
        ] + [
            {"score": 1, "passed": True}, {"score": 5, "passed": False},
            {"threshold": 1}, {"reason": "Safe, but no reference ID."},
            {"reason": self.outputs[1]["results"][0]["reason"]}, {"status": "skipped"},
            {"sample": {"model": "different-judge"}},
        ]
        for change in changes:
            with self.subTest(change=change):
                self.outputs = copy.deepcopy(original)
                self.outputs[0]["results"][0].update(change)
                self.write_export()
                with self.assertRaises(ValueError):
                    self.audit()

    def test_valid_low_score_is_preserved_and_does_not_become_an_improvement_claim(self):
        self.outputs[0]["results"][0].update(score=1, passed=False)
        self.write_export()
        report = self.audit()
        self.assertEqual(report["validation_status"], "valid")
        self.assertEqual(report["rows"][0]["original_results"][0]["score"], 1)
        self.assertFalse(report["rows"][0]["original_results"][0]["passed"])
        self.assertEqual(report["evaluators"][0]["passed"], 5)
        self.assertFalse(report["improvement_claimed"])

    def test_calibration_failure_or_changed_prepared_inputs_cannot_be_used_as_proof(self):
        self.seed_calibration(miscalibrated=True)
        with self.assertRaisesRegex(ValueError, "calibration must pass"):
            self.audit()
        self.seed_calibration()
        self.prepared[0]["ground_truth"] = self.outputs[0]["datasource_item"]["sample.output_text"]
        self.dataset.write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in self.prepared),
            encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            self.audit()

    def test_export_hash_and_target_input_mapping_are_checked_not_merely_reported(self):
        self.outputs[0]["results"][0]["score"] = 1
        write_json(self.export / "output-items.json", self.outputs)
        with self.assertRaisesRegex(ValueError, "hashes/counts"):
            self.audit()
        self.outputs[0]["results"][0]["score"] = 5
        self.run["data_source"]["input_messages"]["template"][0]["content"] = "{{item.ground_truth}}"
        self.write_export()
        with self.assertRaisesRegex(ValueError, "query-only"):
            self.audit()

    def test_cli_print_only_and_new_reports_never_overwrite_or_write_invalid_success(self):
        destination = self.root / "outputs/audit/report.json"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(module.main(self.arguments(), root=self.root), 0)
        self.assertFalse(destination.exists())
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(module.main([*self.arguments(), "--output", str(destination)], root=self.root), 0)
        before = destination.read_bytes()
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(module.main([*self.arguments(), "--output", str(destination)], root=self.root), 1)
        self.assertEqual(destination.read_bytes(), before)
        self.outputs.pop()
        self.write_export()
        invalid = self.root / "outputs/audit/invalid.json"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(module.main([*self.arguments(), "--output", str(invalid)], root=self.root), 1)
        self.assertFalse(invalid.exists())
