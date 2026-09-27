import json
import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from foundry_workshop.contracts import read_json, write_json
from foundry_workshop.native import evaluate_items, verified_native

from .test_sdk_contracts import settings


class NativeEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "WORKSHOP_PREFIX": "lab-unit",
                "AZURE_AI_EVALUATION_MODEL_DEPLOYMENT_NAME": "unit-judge",
            },
            clear=True,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.catalog_calls = []
        self.create_calls = []
        self.run_calls = []
        self.status = "completed"
        self.result_passed = False
        self.omit_rows = False
        self.evaluator_names = ("groundedness", "relevance")
        self.supported_levels = ["turn", "conversation"]
        self.items = [
            {
                "case_id": "D01",
                "query": "합성 질문",
                "response": "합성 답",
                "context": "합성 근거",
                "ground_truth": "원본 정답",
            }
        ]

    @contextmanager
    def clients(self, *_args, **_kwargs):
        def catalog(name, version):
            self.catalog_calls.append((name, version))
            return SimpleNamespace(
                as_dict=lambda: {
                    "name": name,
                    "version": "7",
                    "supported_evaluation_levels": self.supported_levels,
                    "definition": {
                        "init_parameters": {
                            "properties": {"model": {}, "threshold": {}, "evaluation_level": {}}
                        }
                    },
                }
            )

        def create(**kwargs):
            self.create_calls.append(kwargs)
            return SimpleNamespace(id=f"eval-unit-{len(self.create_calls)}")

        def create_run(**kwargs):
            self.run_calls.append(kwargs)
            return SimpleNamespace(id=f"run-unit-{len(self.run_calls)}")

        def retrieve(**_kwargs):
            return SimpleNamespace(
                status=self.status,
                report_url="https://ai.azure.com/unit",
                model_dump=lambda **_: {"status": self.status},
            )

        def output_items(**_kwargs):
            if self.omit_rows:
                return []
            return [
                SimpleNamespace(
                    model_dump=lambda **_: {
                        "datasource_item": {"case_id": "D01"},
                        "results": [
                            {"name": name, "score": 3, "passed": self.result_passed}
                            for name in self.evaluator_names
                        ],
                    }
                )
            ]

        project = SimpleNamespace(
            beta=SimpleNamespace(evaluators=SimpleNamespace(get_version=catalog))
        )
        client = SimpleNamespace(
            evals=SimpleNamespace(
                create=create,
                runs=SimpleNamespace(
                    create=create_run,
                    retrieve=retrieve,
                    output_items=SimpleNamespace(list=output_items),
                ),
            )
        )
        yield project, client

    def evaluate(self, path, **kwargs):
        options = {
            "label": "unit-eval",
            "source_run_id": "unit-source",
            "dataset_hash": "unit-dataset",
            "forbidden_deployments": {"unit-deployment"},
            "evaluator_names": self.evaluator_names,
            "confirmed": True,
            "timeout": 5,
            **kwargs,
        }
        with patch("foundry_workshop.native.project_clients", self.clients):
            return evaluate_items(settings(), path, self.items, **options)

    def test_custom_business_evaluator_uses_its_pinned_version_without_builtin_mapping(self):
        self.evaluator_names = ("groundedness", "relevance", "business_rubric")
        self.items[0].update(answer_json="{}", source_ids="[]")
        custom = {
            "business_rubric": {
                "evaluator_name": "lab_unit_business_rubric",
                "definition": {"name": "lab_unit_business_rubric", "version": "3"},
            }
        }
        with tempfile.TemporaryDirectory() as folder:
            result = self.evaluate(Path(folder), custom_catalog=custom)
        business = self.create_calls[0]["testing_criteria"][2]
        self.assertEqual(business["evaluator_name"], "lab_unit_business_rubric")
        self.assertEqual(business["evaluator_version"], "3")
        self.assertEqual(
            business["initialization_parameters"],
            {"deployment_name": "unit-judge", "pass_threshold": 1.0},
        )
        self.assertIsNone(business.get("data_mapping"))
        self.assertEqual(len(self.catalog_calls), 2)
        self.assertEqual(result["native_pass_counts"]["business_rubric"]["total"], 1)

    def test_retrying_a_failed_run_with_a_reference_catalog_still_works(self):
        with tempfile.TemporaryDirectory() as folder:
            base, target = Path(folder, "base"), Path(folder, "target")
            self.evaluate(base)
            options = {
                "source_run_id": "unit-target",
                "reference_catalog": base / "evaluator-catalog.json",
            }
            self.status = "failed"
            with self.assertRaisesRegex(ValueError, "failed"):
                self.evaluate(target, **options)
            self.status = "completed"
            result = self.evaluate(target, retry_failed=True, **options)
            self.assertEqual(result["run_id"], "run-unit-3")
            self.assertTrue(read_json(target / "cloud-evaluation.json")["retry_of"])

    def test_a_retried_run_can_be_the_reference_for_compare_runs(self):
        with tempfile.TemporaryDirectory() as folder:
            base, candidate = Path(folder, "base"), Path(folder, "candidate")
            self.omit_rows = True
            with self.assertRaisesRegex(ValueError, "exactly one result"):
                self.evaluate(base)
            self.omit_rows = False
            self.evaluate(base, retry_failed=True)
            state = read_json(base / "cloud-evaluation.json")
            self.assertEqual(state["item_fields"], sorted(self.items[0]))
            self.assertEqual(state["validation_status"], "valid")
            self.items[0]["response"] = "Candidate synthetic answer"
            result = self.evaluate(
                candidate,
                source_run_id="unit-candidate",
                reference_state=base / "cloud-evaluation.json",
                reference_catalog=base / "evaluator-catalog.json",
            )
            self.assertEqual(result["reference_run_id"], state["run_id"])
            self.assertEqual(self.run_calls[-1]["eval_id"], state["evaluation_id"])

    def test_an_invalid_reference_run_retries_inside_the_same_evaluation(self):
        with tempfile.TemporaryDirectory() as folder:
            base, candidate = Path(folder, "base"), Path(folder, "candidate")
            self.evaluate(base)
            base_state = read_json(base / "cloud-evaluation.json")
            self.items[0]["response"] = "Candidate synthetic answer"
            reference = {
                "source_run_id": "unit-candidate",
                "reference_state": base / "cloud-evaluation.json",
                "reference_catalog": base / "evaluator-catalog.json",
            }
            self.omit_rows = True
            with self.assertRaisesRegex(ValueError, "exactly one result"):
                self.evaluate(candidate, **reference)
            self.omit_rows = False
            with self.assertRaisesRegex(ValueError, "same reference"):
                self.evaluate(candidate, source_run_id="unit-candidate", retry_failed=True)
            self.assertFalse((candidate / "native-attempts").exists())
            result = self.evaluate(candidate, retry_failed=True, **reference)
            self.assertEqual(len(self.create_calls), 1)
            self.assertEqual(
                [call["eval_id"] for call in self.run_calls], [base_state["evaluation_id"]] * 3
            )
            self.assertEqual(
                [call["name"] for call in self.run_calls],
                ["unit-eval", "unit-eval", "unit-eval-retry-1"],
            )
            self.assertEqual(result["reference_run_id"], base_state["run_id"])
            self.assertEqual(result["run_name"], "unit-eval-retry-1")
            state = read_json(candidate / "cloud-evaluation.json")
            self.assertEqual(state["retry_of"]["attempt"], 1)
            self.assertTrue(
                (candidate / "native-attempts/attempt-1/cloud-evaluation.json").is_file()
            )

    def test_only_cloud_evaluate_advice_names_the_retry_flag(self):
        with tempfile.TemporaryDirectory() as folder:
            self.omit_rows = True
            with self.assertRaises(ValueError) as plain:
                self.evaluate(Path(folder, "plain"))
            self.assertNotIn("--retry-failed", str(plain.exception))
            path = Path(folder, "advised")
            with self.assertRaisesRegex(ValueError, "once with --retry-failed"):
                self.evaluate(path, retry_advice=True)
            with self.assertRaisesRegex(ValueError, "not valid either"):
                self.evaluate(path, retry_failed=True, retry_advice=True)
            self.assertTrue((path / "native-attempts/attempt-1/cloud-evaluation.json").is_file())

    def test_reference_run_joins_the_same_evaluation_with_the_same_catalog(self):
        with tempfile.TemporaryDirectory() as folder:
            base, candidate = Path(folder, "base"), Path(folder, "candidate")
            self.evaluate(base)
            self.items[0]["response"] = "Candidate synthetic answer"
            reference = {
                "reference_state": base / "cloud-evaluation.json",
                "reference_catalog": base / "evaluator-catalog.json",
            }
            with self.assertRaisesRegex(ValueError, "different run"):
                self.evaluate(candidate, **reference)
            result = self.evaluate(candidate, source_run_id="unit-candidate", **reference)
            self.assertEqual(len(self.create_calls), 1)
            self.assertEqual([call["eval_id"] for call in self.run_calls], ["eval-unit-1"] * 2)
            self.assertEqual(result["reference_run_id"], "run-unit-1")
            self.assertEqual(len(self.catalog_calls), 2)
            self.assertEqual(
                read_json(candidate / "evaluator-catalog.json"),
                read_json(base / "evaluator-catalog.json"),
            )
            state = read_json(base / "cloud-evaluation.json")
            state["status"] = "failed"
            write_json(base / "cloud-evaluation.json", state)
            with self.assertRaisesRegex(ValueError, "completed, validated"):
                self.evaluate(Path(folder, "third"), source_run_id="unit-third", **reference)

    def test_catalog_is_pinned_and_resuming_does_not_submit_again_or_hide_low_scores(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            first = self.evaluate(path)
            second = self.evaluate(path)
            self.assertEqual(first["run_id"], second["run_id"])
            self.assertEqual(len(self.create_calls), 1)
            self.assertEqual(len(self.run_calls), 1)
            self.assertEqual(len(self.catalog_calls), 2)
            criteria = self.create_calls[0]["testing_criteria"]
            self.assertTrue(all(item["evaluator_version"] == "7" for item in criteria))
            state, rows = verified_native(path)
            self.assertEqual(state["validation_status"], "valid")
            self.assertFalse(rows[0]["results"][0]["passed"])
            with self.assertRaises(ValueError):
                self.evaluate(path, retry_failed=True)

    def test_only_failed_attempts_can_retry_with_the_same_catalog_and_preserved_history(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            self.status = "failed"
            with self.assertRaises(ValueError):
                self.evaluate(path)
            self.status = "completed"
            self.evaluate(path, retry_failed=True)
            self.assertTrue((path / "native-attempts/attempt-1/cloud-evaluation.json").is_file())
            self.assertEqual(len(self.catalog_calls), 2)
            self.assertEqual(len(self.create_calls), 2)
            self.assertTrue(read_json(path / "cloud-evaluation.json")["retry_of"])

    def test_missing_rows_and_changed_input_or_catalog_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            self.omit_rows = True
            with self.assertRaises(ValueError):
                self.evaluate(path)
            self.assertEqual(
                read_json(path / "cloud-evaluation.json")["validation_status"], "invalid"
            )
            self.assertEqual(read_json(path / "cloud-evaluation-raw.json"), [])
            catalog = read_json(path / "evaluator-catalog.json")
            catalog[0]["parameters"]["threshold"] = 1
            write_json(path / "evaluator-catalog.json", catalog)
            with self.assertRaises(ValueError):
                self.evaluate(path, retry_failed=True)
            self.items[0]["response"] = "changed"
            with self.assertRaises(ValueError):
                self.evaluate(path)

    def test_only_query_response_context_enter_native_mapping(self):
        with tempfile.TemporaryDirectory() as folder:
            self.evaluate(Path(folder))
            source = self.run_calls[0]["data_source"]["source"]
            self.assertEqual(source["type"], "file_content")
            self.assertEqual(source["content"][0]["item"], self.items[0])
            criteria = self.create_calls[0]["testing_criteria"]
            self.assertIn("context", criteria[0]["data_mapping"])
            self.assertNotIn("context", criteria[1]["data_mapping"])
            self.assertNotIn("sample.output", json.dumps(criteria))

    def test_message_inputs_pin_level_and_use_array_schema_without_query_mapping(self):
        self.evaluator_names = ("groundedness", "coherence")
        self.items = [
            {
                "case_id": "D01",
                "messages": [
                    {"role": "user", "content": "Synthetic question"},
                    {"role": "assistant", "content": "Synthetic answer"},
                ],
            }
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            result = self.evaluate(path, messages_input=True, evaluation_level="conversation")
            self.assertEqual(result["evaluation_level"], "conversation")
            self.assertEqual(self.run_calls[0]["extra_body"], {"evaluation_level": "conversation"})
            self.assertEqual(
                self.create_calls[0]["data_source_config"]["item_schema"]["properties"]["messages"],
                {"type": "array"},
            )
            for criterion in self.create_calls[0]["testing_criteria"]:
                self.assertEqual(criterion["data_mapping"], {"messages": "{{item.messages}}"})
                self.assertEqual(
                    criterion["initialization_parameters"]["evaluation_level"], "conversation"
                )
            with self.assertRaisesRegex(ValueError, "evaluation level"):
                self.evaluate(path, messages_input=True, evaluation_level="turn")
            self.assertEqual(len(self.run_calls), 1)

    def test_unsupported_conversation_evaluator_or_missing_answer_never_submits(self):
        self.items = [
            {
                "case_id": "D01",
                "messages": [
                    {"role": "user", "content": "Synthetic question"},
                    {"role": "assistant", "content": "Synthetic answer"},
                ],
            }
        ]
        self.supported_levels = ["turn"]
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "advertise support"):
                self.evaluate(Path(folder), messages_input=True, evaluation_level="conversation")
            self.items[0]["messages"].pop()
            with self.assertRaisesRegex(ValueError, "complete text conversations"):
                self.evaluate(Path(folder), messages_input=True, evaluation_level="conversation")
        self.assertEqual(self.create_calls, [])
        self.assertEqual(self.run_calls, [])


class BusinessEvaluatorTests(unittest.TestCase):
    def project(self, versions):
        from azure.core.exceptions import ResourceNotFoundError

        created = []

        def list_versions(name):
            if versions is None:
                raise ResourceNotFoundError("missing")
            return [SimpleNamespace(as_dict=lambda value=value: value) for value in versions]

        def create_version(name, evaluator_version):
            created.append((name, evaluator_version))
            return SimpleNamespace(as_dict=lambda: {**evaluator_version, "version": "9"})

        evaluators = SimpleNamespace(list_versions=list_versions, create_version=create_version)
        return SimpleNamespace(beta=SimpleNamespace(evaluators=evaluators)), created

    def test_identical_code_is_reused_and_changed_or_missing_code_creates_a_version(self):
        from foundry_workshop.cloud_evaluation import GRADER_PATH, ensure_business_evaluator

        code = GRADER_PATH.read_text()
        project, created = self.project([{"version": "4", "definition": {"code_text": code}}])
        result = ensure_business_evaluator(project, "lab-unit")
        self.assertEqual(
            (result["evaluator_name"], result["definition"]["version"]),
            ("lab_unit_business_rubric", "4"),
        )
        self.assertEqual(created, [])
        for versions in ([{"version": "4", "definition": {"code_text": "old"}}], None):
            project, created = self.project(versions)
            result = ensure_business_evaluator(project, "lab-unit")
            self.assertEqual(len(created), 1)
            self.assertEqual(created[0][1]["definition"]["code_text"], code)
            self.assertEqual(result["definition"]["version"], "9")

    def test_cloud_business_results_are_compared_with_local_checks(self):
        from foundry_workshop.cloud_evaluation import evaluate_cloud
        from foundry_workshop.contracts import load_documents
        from foundry_workshop.experiments import collect
        from foundry_workshop.knowledge import evidence
        from tests import workspace

        def answer(case):
            return {
                **evidence(load_documents(root, "en"), "unit-test"),
                "answer": {
                    "answer": "Unit-test response, not an LLM result.",
                    "decision": case["expected_decision"],
                    "limit_krw": case["expected_limit_krw"],
                    "citations": case["required_citations"],
                },
                "response_id": "unit-" + case["case_id"],
                "response_model": "unit-model",
                "usage": None,
            }

        seen = {}

        def fake_evaluate(_settings, directory, items, **kwargs):
            seen.update(kwargs, items=items)
            rows = [
                {
                    "case_id": item["case_id"],
                    "results": [
                        {
                            "name": "business_rubric",
                            "passed": item["case_id"] != "D02",
                            "score": 1.0,
                        }
                    ],
                }
                for item in items
            ]
            directory.mkdir(parents=True, exist_ok=True)
            write_json(directory / "cloud-evaluation-results.json", rows)
            return {"mode": "live", "label": kwargs["label"]}

        @contextmanager
        def clients(*_args, **_kwargs):
            yield BusinessEvaluatorTests.project(self, None)[0], None

        with workspace() as root, patch.dict(os.environ, {"WORKSHOP_PREFIX": "lab-unit"}):
            collect(
                root,
                label="candidate",
                split="dev",
                prompt_version="v2",
                retrieval="local",
                mode="live",
                deployment="unit-deployment",
                inference={"project_endpoint": "https://unit.invalid"},
                answer_case=answer,
                language="en",
            )
            with (
                patch("foundry_workshop.native.evaluate_items", fake_evaluate),
                patch("foundry_workshop.cloud.project_clients", clients),
            ):
                result = evaluate_cloud(
                    root,
                    settings(),
                    "candidate",
                    timeout=5,
                    confirmed=True,
                    business_evaluator=True,
                )
            self.assertEqual(result["business_rubric_agreement"]["mismatched_cases"], ["D02"])
            self.assertEqual(result["business_rubric_agreement"]["matched"], 5)
            self.assertEqual(
                seen["evaluator_names"], ("groundedness", "relevance", "business_rubric")
            )
            self.assertIn("answer_json", seen["items"][0])
            self.assertEqual(
                seen["custom_catalog"]["business_rubric"]["evaluator_name"],
                "lab_unit_business_rubric",
            )
            self.assertTrue(
                (
                    root
                    / "outputs/candidate/foundry-business-rubric/business-rubric-agreement.json"
                ).is_file()
            )
            with self.assertRaisesRegex(ValueError, "different"):
                evaluate_cloud(
                    root, settings(), "candidate", timeout=5, confirmed=True, reference="candidate"
                )
            collect(
                root,
                label="final",
                split="holdout",
                prompt_version="v2",
                retrieval="local",
                mode="live",
                deployment="unit-deployment",
                inference={"project_endpoint": "https://unit.invalid"},
                answer_case=answer,
                candidate="candidate",
                language="en",
            )
            with self.assertRaisesRegex(ValueError, "dev runs only"):
                evaluate_cloud(
                    root, settings(), "final", timeout=5, confirmed=True, reference="candidate"
                )

    def test_retry_failed_is_forwarded_only_as_an_explicit_request(self):
        from foundry_workshop.cloud_evaluation import evaluate_cloud
        from foundry_workshop.contracts import load_documents
        from foundry_workshop.experiments import collect
        from foundry_workshop.knowledge import evidence
        from tests import workspace

        def answer(case):
            return {
                **evidence(load_documents(root, "en"), "unit-test"),
                "answer": {
                    "answer": "Unit-test response, not an LLM result.",
                    "decision": case["expected_decision"],
                    "limit_krw": case["expected_limit_krw"],
                    "citations": case["required_citations"],
                },
                "response_id": "unit-" + case["case_id"],
                "response_model": "unit-model",
                "usage": None,
            }

        seen = []

        def fake_evaluate(_settings, directory, items, **kwargs):
            seen.append((kwargs["retry_failed"], kwargs["retry_advice"]))
            return {"mode": "live", "label": kwargs["label"]}

        with workspace() as root:
            collect(
                root,
                label="baseline",
                split="dev",
                prompt_version="v1",
                retrieval="local",
                mode="live",
                deployment="unit-deployment",
                inference={"project_endpoint": "https://unit.invalid"},
                answer_case=answer,
                language="en",
            )
            with patch("foundry_workshop.native.evaluate_items", fake_evaluate):
                for retry in (False, True):
                    evaluate_cloud(
                        root, settings(), "baseline", timeout=5, confirmed=True, retry_failed=retry
                    )
        self.assertEqual(seen, [(False, True), (True, True)])

    def test_no_evidence_diagnostic_is_refused_before_any_cloud_call(self):
        from foundry_workshop.cloud_evaluation import evaluate_cloud
        from foundry_workshop.experiments import collect
        from foundry_workshop.knowledge import evidence
        from tests import workspace

        def withheld(case):
            return {
                **evidence([], "none"),
                "answer": {
                    "answer": "Unit-test response without evidence, not an LLM result.",
                    "decision": "insufficient_evidence",
                    "limit_krw": None,
                    "citations": [],
                },
                "response_id": "unit-" + case["case_id"],
                "response_model": "unit-model",
                "usage": None,
            }

        def must_not_run(*_args, **_kwargs):
            raise AssertionError("A cloud call was attempted.")

        with workspace() as root:
            collect(
                root,
                label="diagnostic",
                split="dev",
                prompt_version="v1",
                retrieval="none",
                mode="live",
                deployment="unit-deployment",
                inference={"provider": "none", "max_documents": 0},
                answer_case=withheld,
                language="en",
            )
            with (
                patch("foundry_workshop.native.evaluate_items", must_not_run),
                patch("foundry_workshop.cloud.project_clients", must_not_run),
            ):
                for business in (False, True):
                    with self.subTest(business_evaluator=business):
                        with self.assertRaisesRegex(ValueError, "stays local"):
                            evaluate_cloud(
                                root,
                                settings(),
                                "diagnostic",
                                timeout=5,
                                confirmed=True,
                                business_evaluator=business,
                            )
            self.assertFalse((root / "outputs/diagnostic/foundry-business-rubric").exists())
            self.assertFalse((root / "outputs/diagnostic/cloud-evaluation.json").exists())
