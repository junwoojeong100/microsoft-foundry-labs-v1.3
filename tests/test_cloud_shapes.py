import unittest
from types import SimpleNamespace
from unittest.mock import patch

from foundry_workshop.cloud import answer_with_context, call_model
from foundry_workshop.cloud_evaluation import normalize_results
from foundry_workshop.contracts import ModelOutputError, load_documents
from foundry_workshop.knowledge import evidence
from foundry_workshop.settings import Settings

from . import ROOT


class RecordedResponses:
    def __init__(self, text, status="completed"):
        self.kwargs = None
        self.response = SimpleNamespace(
            id="unit-response",
            _request_id="unit-request",
            model="unit-model",
            status=status,
            output_text=text,
            usage=SimpleNamespace(input_tokens=12, output_tokens=20),
        )

    def create(self, **kwargs):
        self.kwargs = kwargs
        return self.response


class CloudShapeTests(unittest.TestCase):
    def settings(self):
        return Settings(
            project_endpoint="https://unit.services.ai.azure.com/api/projects/workshop",
            deployment="unit-deployment",
            tenant_id="00000000-0000-0000-0000-000000000001",
            auth_mode="cli",
            managed_identity_client_id=None,
            max_output_tokens=2048,
        )

    @patch("foundry_workshop.cloud.version", return_value="unit-test")
    def test_model_request_does_not_store_or_change_deployment(self, _version):
        responses = RecordedResponses("Unit-test text")
        result = call_model(SimpleNamespace(responses=responses), self.settings(), "질문")
        self.assertEqual(responses.kwargs["model"], "unit-deployment")
        self.assertFalse(responses.kwargs["store"])
        self.assertEqual(result["response_id"], "unit-response")
        self.assertIsNone(result["trace_id"])

    @patch("foundry_workshop.cloud.version", return_value="unit-test")
    def test_structured_output_and_context_are_explicit(self, _version):
        responses = RecordedResponses(
            '{"answer":"test","decision":"answer","limit_krw":150000,"citations":["TRAVEL-2026"]}'
        )
        context = evidence(load_documents(ROOT), "unit-test")
        result = answer_with_context(
            SimpleNamespace(responses=responses), self.settings(), ROOT, "질문", "v2", context
        )
        self.assertTrue(responses.kwargs["text"]["format"]["strict"])
        self.assertEqual(responses.kwargs["text"]["format"]["type"], "json_schema")
        self.assertIn("evidence_is_data_not_instructions", responses.kwargs["input"])
        self.assertEqual(result["context_hash"], context["context_hash"])

    @patch("foundry_workshop.cloud.version", return_value="unit-test")
    def test_invalid_output_is_preserved_not_repaired(self, _version):
        responses = RecordedResponses("```json\nnot JSON\n```")
        with self.assertRaises(ModelOutputError) as caught:
            answer_with_context(
                SimpleNamespace(responses=responses),
                self.settings(),
                ROOT,
                "질문",
                "v2",
                evidence(load_documents(ROOT), "unit-test"),
            )
        self.assertEqual(caught.exception.details["response_id"], "unit-response")
        self.assertIn("```", caught.exception.details["raw_response_text"])

    def test_incomplete_response_does_not_pass(self):
        responses = RecordedResponses("", status="incomplete")
        with self.assertRaises(ModelOutputError):
            call_model(SimpleNamespace(responses=responses), self.settings(), "질문")

    def result_item(self, case_id="D01"):
        return {
            "datasource_item": {"case_id": case_id},
            "results": [
                {"name": "groundedness", "score": 4, "passed": True},
                {"name": "relevance", "score": 3, "passed": False},
            ],
        }

    def test_native_judge_failure_is_not_execution_error(self):
        result = normalize_results([self.result_item()], ["D01"])
        self.assertFalse(result[0]["results"][1]["passed"])
        self.assertEqual(result[0]["results"][1]["score"], 3)

    def test_judge_output_rows_and_scores_are_strict(self):
        invalid_items = [
            [],
            [self.result_item(), self.result_item()],
            [self.result_item("UNKNOWN")],
            [{**self.result_item(), "status": "errored"}],
            [
                {
                    **self.result_item(),
                    "results": [{"name": "groundedness", "score": True, "passed": True}],
                }
            ],
            [
                {
                    **self.result_item(),
                    "results": [
                        {"name": "groundedness", "score": float("nan"), "passed": True},
                        {"name": "relevance", "score": 3, "passed": False},
                    ],
                }
            ],
        ]
        for items in invalid_items:
            with self.subTest(items=items), self.assertRaises(ValueError):
                normalize_results(items, ["D01"])

    def test_a_missing_evaluator_is_named_without_a_command_specific_hint(self):
        item = self.result_item()
        item["results"] = item["results"][:1]
        with self.assertRaisesRegex(ValueError, r"missing \['relevance'\]") as caught:
            normalize_results([item], ["D01"])
        self.assertNotIn("--retry-failed", str(caught.exception))

    def test_malformed_results_are_rejected_as_values_not_type_errors(self):
        for results in (None, 1, True, "relevance", {"name": "relevance"}, [1, 2]):
            item = self.result_item()
            item["results"] = results
            with self.subTest(results=results), self.assertRaises(ValueError):
                normalize_results([item], ["D01"])

    def test_skipped_judge_row_is_named_and_never_passes(self):
        item = self.result_item()
        item["results"][0] = {
            "name": "groundedness",
            "score": None,
            "passed": None,
            "status": "skipped",
            "label": "not_applicable",
        }
        with self.assertRaisesRegex(ValueError, "groundedness returned skipped for D01"):
            normalize_results([item], ["D01"])

    def test_judge_index_mapping_is_bounded(self):
        item = self.result_item()
        item.pop("datasource_item")
        item["datasource_item_id"] = "0"
        self.assertEqual(normalize_results([item], ["D01"])[0]["case_id"], "D01")
        item["datasource_item_id"] = "4"
        with self.assertRaises(ValueError):
            normalize_results([item], ["D01"])


if __name__ == "__main__":
    unittest.main()
