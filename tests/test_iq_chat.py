import copy
import json
import os
import unittest
from dataclasses import replace
from unittest.mock import MagicMock, patch

from foundry_workshop import iq_chat
from foundry_workshop.cli import parser
from foundry_workshop.contracts import digest, load_documents, read_json, write_json
from foundry_workshop.settings import Settings

from . import ROOT, workspace


def settings(language="en"):
    return Settings(
        "https://unit.services.ai.azure.com/api/projects/workshop",
        "another-answer-model",
        "00000000-0000-0000-0000-000000000001",
        "cli",
        None,
        2048,
        openai_endpoint="https://unit.openai.azure.com",
        language=language,
    )


def model_preflight():
    return {
        "deployment": {
            "name": iq_chat.CHAT_DEPLOYMENT,
            "state": "Succeeded",
            "model": {"name": iq_chat.CHAT_MODEL, "version": iq_chat.CHAT_MODEL_VERSION},
        }
    }


class Reply:
    def __init__(self, body, status=200):
        self.body, self.status_code = body, status
        self.text = json.dumps(body)

    def json(self):
        return self.body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise ValueError(f"Unit-test HTTP {self.status_code}")


class IQChatTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "WORKSHOP_PREFIX": "lab-unit",
                "AZURE_SEARCH_ENDPOINT": "https://unit.search.windows.net",
                "AZURE_SUBSCRIPTION_ID": "00000000-0000-0000-0000-000000000002",
                "AZURE_RESOURCE_GROUP": "unit-group",
                "AZURE_AI_ACCOUNT_NAME": "unit",
            },
            clear=True,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def expected(self):
        return iq_chat.definition(settings(), "lab-unit-chat-en-kb", "lab-unit-source")

    def readiness_replies(self):
        return [
            {
                "id": "unit-search",
                "identity": {
                    "type": "SystemAssigned",
                    "principalId": "00000000-0000-0000-0000-000000000003",
                },
                "sku": "basic",
            },
            "/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/unit-group/providers/Microsoft.CognitiveServices/accounts/unit",
            ["/roleDefinitions/" + iq_chat.COGNITIVE_SERVICES_USER],
        ]

    def write_ledger(self, root):
        path = root / "outputs/azure-objects.json"
        write_json(
            path,
            {
                "scope": {
                    "search_endpoint": "https://unit.search.windows.net",
                    "prefix": "lab-unit",
                },
                "corpus_hash": digest(load_documents(root, "en")),
                "objects": [
                    {
                        "path": "knowledgesources('lab-unit-source')",
                        "api_version": "2026-04-01",
                    }
                ],
            },
        )
        return path

    def test_preset_is_concrete_keyless_and_separate_from_ga(self):
        value = self.expected()
        parameters = value["models"][0]["azureOpenAIParameters"]
        self.assertEqual(parameters["deploymentId"], "gpt-5.6-luna")
        self.assertEqual(parameters["modelName"], "gpt-5.6-luna")
        self.assertIsNone(parameters["authIdentity"])
        self.assertNotIn("apiKey", parameters)
        self.assertEqual(value["retrievalReasoningEffort"], {"kind": "low"})
        self.assertEqual(value["outputMode"], "answerSynthesis")
        self.assertEqual(iq_chat.chat_name(settings()), "lab-unit-chat-en-kb")
        self.assertEqual(iq_chat.chat_name(settings("ko")), "lab-unit-chat-ko-kb")
        with self.assertRaises(ValueError):
            iq_chat.definition(
                replace(settings(), openai_endpoint="https://other.openai.azure.com"),
                "base",
                "source",
            )

    def test_model_auth_source_and_mode_drift_are_rejected(self):
        expected = self.expected()
        iq_chat.validate_definition(expected, expected)
        variants = []
        for key, value in (
            ("modelName", "model-router"),
            ("deploymentId", "wrong"),
            ("apiKey", "unexpected-key"),
            ("apiKey", ""),
            ("authIdentity", {"userAssignedIdentity": "different"}),
        ):
            changed = copy.deepcopy(expected)
            changed["models"][0]["azureOpenAIParameters"][key] = value
            variants.append(changed)
        for key, value in (
            ("models", []),
            ("knowledgeSources", [None]),
            ("outputMode", "extractiveData"),
            ("answerInstructions", "Different answer prompt"),
            ("retrievalInstructions", "Different retrieval prompt"),
            ("retrieveDefaults", {"outputMode": "extractiveData"}),
        ):
            variants.append({**expected, key: value})
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError):
                iq_chat.validate_definition(value, expected)
        service_shape = copy.deepcopy(expected)
        service_shape["models"][0]["azureOpenAIParameters"]["apiKey"] = None
        service_shape["answerInstructions"] = None
        service_shape["retrieveDefaults"] = None
        iq_chat.validate_definition(service_shape, expected)

    def test_readiness_uses_fixed_model_and_only_read_operations(self):
        gateway = MagicMock()
        gateway.source, gateway.index = "lab-unit-source", "lab-unit-policies"
        gateway.request.side_effect = [
            Reply(
                {"kind": "searchIndex", "searchIndexParameters": {"searchIndexName": gateway.index}}
            ),
            Reply({}, 404),
        ]
        gateway.__enter__.return_value = gateway
        with (
            patch(
                "foundry_workshop.cloud.doctor_cloud",
                return_value=model_preflight(),
            ) as doctor,
            patch("foundry_workshop.iq_chat.az_json", side_effect=self.readiness_replies()) as az,
            patch("foundry_workshop.iq_chat.SearchGateway", return_value=gateway),
        ):
            result = iq_chat.check(ROOT, settings())
        self.assertEqual(doctor.call_args.args[0].deployment, iq_chat.CHAT_DEPLOYMENT)
        self.assertTrue(result["ready_for_setup"])
        self.assertFalse(result["configured"])
        self.assertFalse(result["model_inference_verified"])
        self.assertEqual(result["model_deployment"], model_preflight()["deployment"])
        self.assertTrue(all(call.args[0] == "GET" for call in gateway.request.call_args_list))
        self.assertFalse(
            any("create" in call.args[0] or "set" in call.args[0] for call in az.call_args_list)
        )

    def test_unprepared_version_or_role_fails_before_setup(self):
        wrong = model_preflight()
        wrong["deployment"]["model"]["version"] = "different"
        with patch(
            "foundry_workshop.cloud.doctor_cloud",
            return_value=wrong,
        ):
            with self.assertRaisesRegex(ValueError, "version"):
                iq_chat.check(ROOT, settings())
        with self.assertRaisesRegex(ValueError, "confirm-create"):
            iq_chat.setup(ROOT, settings(), confirmed=False)
        with self.assertRaisesRegex(ValueError, "confirm-cost"):
            iq_chat.ask(ROOT, settings(), "question", "unit", confirmed=False)

    def test_malformed_or_different_model_preflight_fails_explicitly(self):
        for value in (
            None,
            {},
            {"deployment": []},
            {"deployment": {"model": None}},
            {"deployment": {**model_preflight()["deployment"], "state": "Failed"}},
            {"deployment": {**model_preflight()["deployment"], "name": "another-deployment"}},
        ):
            with (
                self.subTest(value=value),
                patch("foundry_workshop.cloud.doctor_cloud", return_value=value),
                self.assertRaisesRegex(ValueError, "Succeeded deployment"),
            ):
                iq_chat.check_model(settings())
        with (
            patch.dict(os.environ, {"AZURE_AI_ACCOUNT_NAME": "another-account"}),
            patch("foundry_workshop.cloud.doctor_cloud") as doctor,
            self.assertRaisesRegex(ValueError, "same account"),
        ):
            iq_chat.check_model(settings())
        doctor.assert_not_called()
        with self.assertRaisesRegex(ValueError, "local CLI"):
            iq_chat.check_model(replace(settings(), auth_mode="managed-identity"))

    def test_unprepared_identity_scope_roles_or_source_never_pass_readiness(self):
        valid_source = {
            "kind": "searchIndex",
            "searchIndexParameters": {"searchIndexName": "lab-unit-policies"},
        }
        cases = []
        for service in (
            None,
            {},
            {"identity": "malformed", "sku": "basic"},
            {**self.readiness_replies()[0], "sku": "free"},
            {**self.readiness_replies()[0], "sku": "unknown"},
            {"identity": {"type": "SystemAssigned", "principalId": "not-a-uuid"}, "sku": "basic"},
        ):
            replies = self.readiness_replies()
            replies[0] = service
            cases.append((replies, valid_source))
        for index, value in (
            (1, "/subscriptions/wrong/accounts/unit"),
            (2, []),
            (2, {"unexpected": "role shape"}),
            (2, ["/roleDefinitions/a-different-role"]),
        ):
            replies = self.readiness_replies()
            replies[index] = value
            cases.append((replies, valid_source))
        for source in (None, {}, {"kind": "searchIndex", "searchIndexParameters": []}):
            cases.append((self.readiness_replies(), source))
        for replies, source in cases:
            gateway = MagicMock()
            gateway.source, gateway.index = "lab-unit-source", "lab-unit-policies"
            gateway.__enter__.return_value = gateway
            gateway.request.side_effect = [Reply(source), Reply({}, 404)]
            with (
                self.subTest(replies=replies, source=source),
                patch("foundry_workshop.cloud.doctor_cloud", return_value=model_preflight()),
                patch("foundry_workshop.iq_chat.az_json", side_effect=replies),
                patch("foundry_workshop.iq_chat.SearchGateway", return_value=gateway),
                self.assertRaises(ValueError),
            ):
                iq_chat.check(ROOT, settings())
            self.assertTrue(all(call.args[0] == "GET" for call in gateway.request.call_args_list))

    def test_setup_is_create_only_and_never_changes_the_ga_base(self):
        gateway = MagicMock()
        gateway.__enter__.return_value = gateway
        expected = self.expected()
        gateway.request.side_effect = [Reply(expected, 201), Reply(expected)]
        readiness = {"knowledge_base": expected["name"], "preset": expected, "configured": False}
        with workspace() as root:
            ledger_path = self.write_ledger(root)
            with (
                patch("foundry_workshop.iq_chat.check", return_value=readiness),
                patch("foundry_workshop.iq_chat.SearchGateway", return_value=gateway),
            ):
                result = iq_chat.setup(root, settings(), confirmed=True)
            objects = read_json(ledger_path)["objects"]
        self.assertTrue(result["created"])
        self.assertFalse(result["existing_ga_base_modified"])
        self.assertTrue(gateway.request.call_args_list[0].kwargs["create_only"])
        self.assertEqual(objects[-1]["path"], "knowledgebases('lab-unit-chat-en-kb')")
        self.assertEqual(objects[-1]["api_version"], iq_chat.CHAT_API)

    def test_setup_rejects_unowned_and_malformed_ledgers_without_writes(self):
        expected = self.expected()
        readiness = {"knowledge_base": expected["name"], "preset": expected, "configured": True}
        with workspace() as root:
            ledger_path = self.write_ledger(root)
            ledger = read_json(ledger_path)
            variants = (
                ledger,
                {**ledger, "corpus_hash": "different"},
                {**ledger, "objects": [{"path": [], "api_version": iq_chat.CHAT_API}]},
                {
                    **ledger,
                    "objects": [
                        *ledger["objects"],
                        {"path": "knowledgebases('lab-unit-chat-en-kb')", "api_version": "wrong"},
                    ],
                },
            )
            for value in variants:
                write_json(ledger_path, value)
                before = ledger_path.read_bytes()
                with (
                    self.subTest(ledger=value),
                    patch("foundry_workshop.iq_chat.check", return_value=readiness),
                    patch("foundry_workshop.iq_chat.SearchGateway") as gateway,
                    self.assertRaises(ValueError),
                ):
                    iq_chat.setup(root, settings(), confirmed=True)
                gateway.assert_not_called()
                self.assertEqual(ledger_path.read_bytes(), before)

    def test_owned_setup_is_idempotent_and_a_create_collision_is_not_overwritten(self):
        expected = self.expected()
        readiness = {"knowledge_base": expected["name"], "preset": expected, "configured": True}
        with workspace() as root:
            ledger_path = self.write_ledger(root)
            ledger = read_json(ledger_path)
            ledger["objects"].append(
                {"path": "knowledgebases('lab-unit-chat-en-kb')", "api_version": iq_chat.CHAT_API}
            )
            write_json(ledger_path, ledger)
            before = ledger_path.read_bytes()
            with (
                patch("foundry_workshop.iq_chat.check", return_value=readiness),
                patch("foundry_workshop.iq_chat.SearchGateway") as gateway,
            ):
                result = iq_chat.setup(root, settings(), confirmed=True)
            self.assertFalse(result["created"])
            gateway.assert_not_called()
            self.assertEqual(ledger_path.read_bytes(), before)
            readiness["configured"] = False
            transport = MagicMock()
            transport.__enter__.return_value = transport
            transport.request.return_value = Reply({"error": "name collision"}, 412)
            with (
                patch("foundry_workshop.iq_chat.check", return_value=readiness),
                patch("foundry_workshop.iq_chat.SearchGateway", return_value=transport),
                self.assertRaisesRegex(ValueError, "412"),
            ):
                iq_chat.setup(root, settings(), confirmed=True)
            self.assertEqual(transport.request.call_count, 1)
            self.assertTrue(transport.request.call_args.kwargs["create_only"])
            self.assertEqual(ledger_path.read_bytes(), before)

    def test_response_requires_real_fixed_model_activities_and_original_evidence(self):
        prior = read_json(ROOT / "tests/fixtures/iq-activity.json")
        payload = {
            "activity": prior["activity"],
            "response": prior["response"],
            "references": [{"sourceData": item} for item in load_documents(ROOT)],
        }
        value = iq_chat.parse_response(payload)
        self.assertEqual(value["provider"], "foundry-iq-chat")
        self.assertTrue(value["answer"])
        self.assertIn("TRAVEL-2026", value["source_ids"])
        for broken in (
            {**payload, "error": {"message": "service failure"}},
            {**payload, "activity": []},
            {**payload, "references": []},
            {**payload, "response": [{"content": [{"type": "text", "text": 1}]}]},
            {
                **payload,
                "activity": [{"type": "modelQueryPlanning", "error": {"message": "failed"}}],
            },
        ):
            with self.subTest(broken=broken), self.assertRaises(ValueError):
                iq_chat.parse_response(broken)

    def test_corpus_projection_is_preserved_without_inventing_missing_dates(self):
        for language in ("en", "ko"):
            documents = load_documents(ROOT, language)
            projection = [
                {key: item[key] for key in ("id", "title", "content")} for item in documents
            ]
            before = copy.deepcopy(projection)
            iq_chat.validate_corpus_evidence(ROOT, projection, language)
            iq_chat.validate_corpus_evidence(ROOT, documents, language)
            self.assertEqual(projection, before)
            self.assertNotIn("effective_from", projection[0])
            for key, value in (
                ("id", "OTHER-SOURCE"),
                ("content", "Altered synthetic source."),
                ("effective_from", "1900-01-01"),
                ("unexpected_field", None),
            ):
                changed = copy.deepcopy(projection)
                changed[0][key] = value
                with self.subTest(language=language, key=key), self.assertRaises(ValueError):
                    iq_chat.validate_corpus_evidence(ROOT, changed, language)
        with self.assertRaises(ValueError):
            iq_chat.validate_corpus_evidence(ROOT, [], "en")

    def test_cli_exposes_no_implicit_model_override_or_write(self):
        self.assertEqual(
            parser().parse_args(["--language", "en", "iq-chat", "check"]).iq_chat_action, "check"
        )
        self.assertFalse(parser().parse_args(["iq-chat", "setup"]).confirm_create)
        self.assertFalse(parser().parse_args(["iq-chat", "ask", "--label", "unit"]).confirm_cost)
