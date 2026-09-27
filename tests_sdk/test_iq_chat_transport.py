import json
import os
import unittest
from unittest.mock import patch

import httpx

from foundry_workshop import iq_chat
from foundry_workshop.contracts import load_documents, read_json
from foundry_workshop.search import SearchGateway
from tests import ROOT, workspace
from tests.test_iq_chat import model_preflight, settings

from .test_sdk_contracts import DummyCredential


class IQChatTransportTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "WORKSHOP_PREFIX": "lab-unit",
                "AZURE_SEARCH_ENDPOINT": "https://unit.search.windows.net",
                "AZURE_AI_ACCOUNT_NAME": "unit",
            },
            clear=True,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        doctor_patch = patch("foundry_workshop.cloud.doctor_cloud", return_value=model_preflight())
        self.doctor = doctor_patch.start()
        self.addCleanup(doctor_patch.stop)

    def gateway(self, handler):
        gateway = object.__new__(SearchGateway)
        gateway.settings = settings()
        gateway.endpoint = "https://unit.search.windows.net"
        gateway.credential = DummyCredential()
        gateway.http = httpx.Client(transport=httpx.MockTransport(handler))
        return gateway

    def response_payload(self):
        evidence = read_json(ROOT / "tests/fixtures/iq-activity.json")
        return {
            "activity": evidence["activity"],
            "response": [
                {
                    "content": [
                        {
                            "type": "text",
                            "text": "The synthetic lodging limit is KRW 150000. [ref_id:0]",
                        }
                    ]
                }
            ],
            "references": [
                {"sourceData": {key: item[key] for key in ("id", "title", "content")}}
                for item in load_documents(ROOT, "en")
            ],
        }

    def test_actual_http_shape_uses_only_the_verified_preview_contract(self):
        captured = []
        expected = iq_chat.definition(settings(), "lab-unit-chat-en-kb", "lab-unit-source")
        response = self.response_payload()

        def handle(request):
            captured.append(request)
            return httpx.Response(200, json=expected if request.method == "GET" else response)

        with workspace() as root:
            with patch("foundry_workshop.iq_chat.SearchGateway", return_value=self.gateway(handle)):
                result = iq_chat.ask(
                    root,
                    settings(),
                    "What is the synthetic lodging limit?",
                    "unit-iq",
                    confirmed=True,
                )
            stored = read_json(root / "outputs/iq-chat/unit-iq/summary.json")
            preflight = read_json(root / "outputs/iq-chat/unit-iq/model-preflight.json")
        self.assertEqual(result["model"], "gpt-5.6-luna")
        self.assertEqual(stored["response_hash"], result["response_hash"])
        self.assertEqual(preflight, result["model_deployment"])
        self.assertNotIn("effective_from", result["documents"][0])
        self.assertEqual(self.doctor.call_args.args[0].deployment, iq_chat.CHAT_DEPLOYMENT)
        self.assertEqual([request.method for request in captured], ["GET", "POST"])
        self.assertEqual(captured[-1].url.params["api-version"], "2026-08-01-preview")
        body = json.loads(captured[-1].content)
        self.assertEqual(body["maxOutputSize"], 6000)
        self.assertNotIn("maxOutputSizeInTokens", body)
        self.assertNotIn("intents", body)
        self.assertNotIn("apiKey", str(body))

    def test_failed_request_is_saved_without_retry_or_provider_substitution(self):
        captured = []
        expected = iq_chat.definition(settings(), "lab-unit-chat-en-kb", "lab-unit-source")

        def handle(request):
            captured.append(request)
            return (
                httpx.Response(200, json=expected)
                if request.method == "GET"
                else httpx.Response(503, json={"error": {"message": "unit transport failure"}})
            )

        with workspace() as root:
            with patch("foundry_workshop.iq_chat.SearchGateway", return_value=self.gateway(handle)):
                with self.assertRaises(httpx.HTTPStatusError):
                    iq_chat.ask(
                        root, settings(), "Synthetic question", "unit-failure", confirmed=True
                    )
            path = root / "outputs/iq-chat/unit-failure"
            self.assertEqual(read_json(path / "http-response.json")["status_code"], 503)
            self.assertFalse(read_json(path / "failure.json")["fallback_used"])
            self.assertFalse((path / "summary.json").exists())
        self.assertEqual([request.method for request in captured], ["GET", "POST"])

    def test_wrong_remote_model_stops_before_any_paid_post(self):
        captured = []
        expected = iq_chat.definition(settings(), "lab-unit-chat-en-kb", "lab-unit-source")
        expected["models"][0]["azureOpenAIParameters"]["deploymentId"] = "wrong-model"

        def handle(request):
            captured.append(request)
            return httpx.Response(200, json=expected)

        with workspace() as root:
            with patch("foundry_workshop.iq_chat.SearchGateway", return_value=self.gateway(handle)):
                with self.assertRaises(ValueError):
                    iq_chat.ask(
                        root, settings(), "Synthetic question", "wrong-model", confirmed=True
                    )
            self.assertTrue((root / "outputs/iq-chat/wrong-model/failure.json").is_file())
        self.assertEqual([request.method for request in captured], ["GET"])

    def test_underlying_model_drift_fails_before_any_search_or_paid_request(self):
        self.doctor.return_value["deployment"]["model"]["version"] = "different-version"
        with workspace() as root:
            with (
                patch("foundry_workshop.iq_chat.SearchGateway") as gateway,
                self.assertRaisesRegex(ValueError, "version"),
            ):
                iq_chat.ask(root, settings(), "Synthetic question", "model-drift", confirmed=True)
            gateway.assert_not_called()
            path = root / "outputs/iq-chat/model-drift"
            self.assertEqual(read_json(path / "failure.json")["stage"], "model-preflight")
            self.assertTrue((path / "request.json").is_file())
            self.assertFalse((path / "summary.json").exists())

    def test_gateway_initialization_and_http_preflight_failures_are_recorded(self):
        from azure.core.exceptions import ClientAuthenticationError

        with workspace() as root:
            with (
                patch(
                    "foundry_workshop.iq_chat.SearchGateway",
                    side_effect=ClientAuthenticationError("unit credential failure"),
                ),
                self.assertRaises(ClientAuthenticationError),
            ):
                iq_chat.ask(root, settings(), "Synthetic question", "auth-error", confirmed=True)
            self.assertEqual(
                read_json(root / "outputs/iq-chat/auth-error/failure.json")["stage"],
                "knowledge-base-preflight",
            )
            requests = []

            def handle(request):
                requests.append(request)
                return httpx.Response(403, json={"error": "unit read denied"})

            with (
                patch("foundry_workshop.iq_chat.SearchGateway", return_value=self.gateway(handle)),
                self.assertRaises(httpx.HTTPStatusError),
            ):
                iq_chat.ask(root, settings(), "Synthetic question", "get-error", confirmed=True)
            path = root / "outputs/iq-chat/get-error"
            self.assertEqual(read_json(path / "knowledge-base-response.json")["status_code"], 403)
            self.assertFalse((path / "http-response.json").exists())
            self.assertEqual([request.method for request in requests], ["GET"])

    def test_wrong_language_or_modified_evidence_is_not_a_success(self):
        for mismatch in ("language", "content", "date"):
            response = self.response_payload()
            if mismatch == "language":
                response["references"] = [
                    {"sourceData": item} for item in load_documents(ROOT, "ko")
                ]
            elif mismatch == "content":
                response["references"][0]["sourceData"]["content"] = "Altered synthetic policy."
            else:
                response["references"][0]["sourceData"]["effective_from"] = "1900-01-01"
            expected = iq_chat.definition(settings(), "lab-unit-chat-en-kb", "lab-unit-source")

            def handle(request, expected=expected, response=response):
                return httpx.Response(200, json=expected if request.method == "GET" else response)

            with workspace() as root:
                with (
                    self.subTest(mismatch=mismatch),
                    patch(
                        "foundry_workshop.iq_chat.SearchGateway", return_value=self.gateway(handle)
                    ),
                    self.assertRaisesRegex(ValueError, "canonical synthetic language corpus"),
                ):
                    iq_chat.ask(root, settings(), "Synthetic question", mismatch, confirmed=True)
                path = root / "outputs/iq-chat" / mismatch
                self.assertEqual(read_json(path / "response.json"), response)
                self.assertEqual(read_json(path / "failure.json")["stage"], "response-validation")
                self.assertFalse((path / "summary.json").exists())
