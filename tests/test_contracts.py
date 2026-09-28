import os
import unittest
from unittest.mock import patch

from foundry_workshop.agents import policy_instructions
from foundry_workshop.cli import doctor_offline, parser
from foundry_workshop.contracts import (
    Answer,
    digest,
    load_cases,
    load_documents,
    parse_json,
    safe_label,
    validate_cases,
)
from foundry_workshop.knowledge import evidence, local_retrieve
from foundry_workshop.settings import Settings, azure_endpoint, require_uuid

from . import ROOT


class ContractTests(unittest.TestCase):
    def valid_answer(self):
        return {
            "answer": "합성 규정의 한도입니다.",
            "decision": "answer",
            "limit_krw": 150000,
            "citations": ["TRAVEL-2026"],
        }

    def test_dataset_counts_and_partitions(self):
        result = doctor_offline(ROOT)
        self.assertEqual(
            (result["documents"], result["dev_cases"], result["holdout_cases"]), (6, 6, 4)
        )
        self.assertFalse(result["azure_tested"])
        self.assertEqual(result["result"], "PASS")

    def test_answer_roundtrip(self):
        value = self.valid_answer()
        self.assertEqual(Answer.from_dict(value).to_dict(), value)

    def test_invalid_answer_shapes(self):
        examples = [
            {**self.valid_answer(), "limit_krw": True},
            {**self.valid_answer(), "limit_krw": -1},
            {**self.valid_answer(), "limit_krw": "150000"},
            {**self.valid_answer(), "decision": "approved"},
            {**self.valid_answer(), "answer": ""},
            {**self.valid_answer(), "citations": ["TRAVEL-2026", "TRAVEL-2026"]},
            {**self.valid_answer(), "citations": "TRAVEL-2026"},
            {**self.valid_answer(), "unexpected": "field"},
        ]
        for value in examples:
            with self.subTest(value=value), self.assertRaises(ValueError):
                Answer.from_dict(value)

    def test_json_is_not_silently_repaired(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '```json\n{"a":1}\n```'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_json(text)

    def test_label_rejects_paths(self):
        for label in ("../outside", "/tmp/results", "UPPER", "a/b", "", "a" * 49):
            with self.subTest(label=label), self.assertRaises(ValueError):
                safe_label(label)
        self.assertEqual(safe_label("candidate-02"), "candidate-02")

    def test_endpoint_validation(self):
        endpoint = "https://unit.services.ai.azure.com/api/projects/workshop/"
        self.assertEqual(azure_endpoint(endpoint, "project"), endpoint.rstrip("/"))
        invalid = [
            "https://ai.azure.com",
            "https://unit.services.ai.azure.com",
            "http://unit.services.ai.azure.com/api/projects/workshop",
            "https://user:password@unit.services.ai.azure.com/api/projects/workshop",
            endpoint + "?token=secret",
            "https://unit.services.ai.azure.com.evil.example/api/projects/workshop",
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                azure_endpoint(value, "project")

    def test_settings_have_no_model_fallback(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            Settings.from_env()

    def test_settings_use_explicit_local_tenant(self):
        environment = {
            "AZURE_TENANT_ID": "00000000-0000-0000-0000-000000000001",
            "AZURE_AI_PROJECT_ENDPOINT": "https://unit.services.ai.azure.com/api/projects/workshop",
            "AZURE_AI_MODEL_DEPLOYMENT_NAME": "actual-deployment-name",
        }
        with patch.dict(os.environ, environment, clear=True):
            settings = Settings.from_env()
        self.assertEqual(settings.deployment, "actual-deployment-name")
        self.assertEqual(settings.auth_mode, "cli")

    def test_uuid_errors_name_the_setting_without_echoing_its_value(self):
        for name in (
            "AZURE_TENANT_ID",
            "AZURE_CLIENT_ID",
            "AZURE_SUBSCRIPTION_ID",
            "AZURE_APPLICATION_INSIGHTS_APP_ID",
        ):
            with (
                self.subTest(name=name),
                patch.dict(os.environ, {name: "unit-invalid"}, clear=True),
            ):
                with self.assertRaisesRegex(ValueError, name) as failure:
                    require_uuid(name)
                self.assertNotIn("unit-invalid", str(failure.exception))
            value = "00000000-0000-0000-0000-000000000001"
            with patch.dict(os.environ, {name: value}, clear=True):
                self.assertEqual(require_uuid(name), value)

    def test_settings_reject_invalid_identity_values_with_actionable_names(self):
        environment = {
            "AZURE_TENANT_ID": "00000000-0000-0000-0000-000000000001",
            "AZURE_AI_PROJECT_ENDPOINT": "https://unit.services.ai.azure.com/api/projects/workshop",
            "AZURE_AI_MODEL_DEPLOYMENT_NAME": "actual-deployment-name",
        }
        for name in ("AZURE_TENANT_ID", "AZURE_CLIENT_ID"):
            with (
                self.subTest(name=name),
                patch.dict(os.environ, {**environment, name: "unit-invalid"}, clear=True),
                self.assertRaisesRegex(ValueError, name),
            ):
                Settings.from_env()

    def test_output_token_errors_name_the_setting_and_keep_exact_bounds(self):
        environment = {
            "WORKSHOP_AUTH_MODE": "managed-identity",
            "AZURE_AI_PROJECT_ENDPOINT": "https://unit.services.ai.azure.com/api/projects/workshop",
            "AZURE_AI_MODEL_DEPLOYMENT_NAME": "actual-deployment-name",
        }
        for value in ("", "not-a-number", "2048.5", "255", "32769"):
            with (
                self.subTest(value=value),
                patch.dict(
                    os.environ, {**environment, "WORKSHOP_MAX_OUTPUT_TOKENS": value}, clear=True
                ),
                self.assertRaisesRegex(ValueError, "WORKSHOP_MAX_OUTPUT_TOKENS.*256.*32768"),
            ):
                Settings.from_env()
        for value in ("256", "2048", "8192", "32768"):
            with patch.dict(
                os.environ, {**environment, "WORKSHOP_MAX_OUTPUT_TOKENS": value}, clear=True
            ):
                self.assertEqual(Settings.from_env().max_output_tokens, int(value))

    def test_context_hash_is_order_independent(self):
        documents = load_documents(ROOT)
        self.assertEqual(
            evidence(documents, "unit")["context_hash"],
            evidence(list(reversed(documents)), "unit")["context_hash"],
        )

    def test_duplicate_or_incomplete_evidence_fails(self):
        document = load_documents(ROOT)[0]
        for documents in ([document, document], [{"id": "missing-fields"}]):
            with self.subTest(documents=documents), self.assertRaises(ValueError):
                evidence(documents, "unit")

    def test_local_retrieval_is_not_labeled_iq(self):
        result = local_retrieve(ROOT, "2026년 9월 국내 출장 숙박비 한도")
        self.assertEqual(result["provider"], "local-keyword")
        self.assertIn("TRAVEL-2026", result["source_ids"])
        self.assertEqual(result["context_hash"], digest(result["documents"]))

    def test_empty_search_does_not_invent_context(self):
        result = local_retrieve(ROOT, "zzzzunmatchedtoken")
        self.assertEqual(result["documents"], [])

    def test_unknown_split_fails(self):
        with self.assertRaises(ValueError):
            load_cases(ROOT, "../other")

    def test_holdout_parser_requires_explicit_flags_at_execution(self):
        args = parser().parse_args(
            [
                "collect",
                "--split",
                "holdout",
                "--label",
                "final",
                "--candidate",
                "candidate",
                "--unlock-holdout",
            ]
        )
        self.assertEqual(args.candidate, "candidate")
        self.assertTrue(args.unlock_holdout)

    def test_workflow_curriculum_uses_existing_maf_examples(self):
        guide = (ROOT / "docs/05-workflows.md").read_text(encoding="utf-8")
        for pattern in ("sequential", "concurrent", "group-chat"):
            self.assertIn(f"workflow --pattern {pattern}", guide)
        self.assertIn("모의", guide)
        self.assertIn("확인", guide)
        self.assertNotIn("포털에 Workflow Designer가 제공되고", guide)

    def test_policy_tool_modes_share_the_answer_schema(self):
        instructions = policy_instructions(ROOT)
        self.assertIn('"needs_approval"', instructions)
        self.assertIn('"insufficient_evidence"', instructions)
        self.assertIn('"limit_krw"', instructions)


class AllowedCitationContractTests(unittest.TestCase):
    def setUp(self):
        self.documents = load_documents(ROOT, "en")
        self.case = {
            "case_id": "UNIT-SCOPE",
            "question": "What travel date is needed to select the domestic lodging policy?",
            "expected_decision": "insufficient_evidence",
            "expected_limit_krw": None,
            "required_citations": ["SCOPE-01"],
        }

    def test_optional_allowlist_accepts_known_unique_supersets_without_mutating_cases(self):
        case = {
            **self.case,
            "allowed_citations": ["SCOPE-01", "TRAVEL-2025", "TRAVEL-2026"],
        }
        cases = [case]
        before = digest(cases)
        self.assertIs(validate_cases(cases, self.documents), cases)
        self.assertEqual(digest(cases), before)
        self.assertEqual(case["required_citations"], ["SCOPE-01"])
        self.assertEqual(case["allowed_citations"], ["SCOPE-01", "TRAVEL-2025", "TRAVEL-2026"])

    def test_malformed_unknown_duplicate_or_incomplete_allowlists_are_rejected(self):
        for allowed in (
            None,
            "SCOPE-01",
            {"SCOPE-01": True},
            ("SCOPE-01",),
            ["SCOPE-01", "SCOPE-01"],
            ["SCOPE-01", "UNKNOWN-01"],
            ["TRAVEL-2025", "TRAVEL-2026"],
            ["SCOPE-01", 1],
            ["SCOPE-01", ""],
            ["SCOPE-01", {}],
            [],
        ):
            with self.subTest(allowed=allowed), self.assertRaises(ValueError):
                validate_cases([{**self.case, "allowed_citations": allowed}], self.documents)

    def test_legacy_five_field_cases_and_rejection_of_other_extensions_are_unchanged(self):
        cases = [self.case]
        before = digest(cases)
        self.assertIs(validate_cases(cases, self.documents), cases)
        self.assertEqual(digest(cases), before)
        self.assertEqual(len(self.case), 5)
        for case in (
            {**self.case, "unapproved_extension": []},
            {key: value for key, value in self.case.items() if key != "question"},
            {**self.case, "required_citations": ["UNKNOWN-01"]},
        ):
            with self.subTest(case=case), self.assertRaises(ValueError):
                validate_cases([case], self.documents)


if __name__ == "__main__":
    unittest.main()
