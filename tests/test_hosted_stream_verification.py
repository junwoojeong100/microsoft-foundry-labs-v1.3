import json
import os
import unittest
from unittest.mock import patch

from foundry_workshop.contracts import code_hash, read_json
from foundry_workshop.toolbox import QUESTIONS

from . import workspace
from .test_packaging import load_script
from .test_toolbox import ENVIRONMENT, seed_ledger, settings

VERIFY = load_script("verify_toolbox_response")


class HostedStreamTests(unittest.TestCase):
    def test_status_text_is_not_an_actual_successful_response(self):
        for value in (
            "Server responded successfully",
            'event: response.completed\ndata: {"type":"response.completed","response":{"status":"failed"}}\n\n',
            'event: response.failed\ndata: {"type":"response.failed","response":{"status":"failed"}}\n\n',
        ):
            with self.assertRaises(ValueError):
                VERIFY.completed_response(value)

    def test_only_one_completed_service_event_is_accepted(self):
        response = {"id": "resp-unit", "status": "completed", "error": None, "output": []}
        text = (
            "event: response.completed\ndata: "
            + json.dumps({"type": "response.completed", "response": response})
            + "\n\n"
        )
        self.assertEqual(VERIFY.completed_response(text), response)
        with_header = (
            "HTTP/2.0 200 OK\r\nContent-Type: text/event-stream; charset=utf-8\r\n\r\n" + text
        )
        self.assertEqual(VERIFY.completed_response(with_header), response)
        with self.assertRaises(ValueError):
            VERIFY.completed_response(with_header.replace("200 OK", "500 Error"))
        with self.assertRaises(ValueError):
            VERIFY.completed_response(text + text)

    def test_runtime_package_and_actual_agent_version_are_verified(self):
        package_script = load_script("package_toolbox")
        with workspace() as root, patch.dict(os.environ, ENVIRONMENT, clear=True):
            seed_ledger(root)
            package = package_script.build(root, settings(), "4", with_skill=True)
            profile = read_json(package / "toolbox-profile.json")
            result = {
                "mode": "live-toolbox-agent",
                "language": "en",
                "toolbox_name": profile["runtime"]["toolbox_name"],
                "toolbox_version": "4",
                "deployment": settings().deployment,
                "corpus_hash": profile["source"]["corpus_hash"],
                "code_hash": code_hash(package),
                "model_invoked": True,
                "tool_invoked": True,
                "question": QUESTIONS["en"],
                "model_calls": [{"response_id": "resp-model-unit", "response_model": "unit-model"}],
                "function_calls": [
                    {"name": "load_skill", "completed": True},
                    {"name": "policy_search", "completed": True},
                ],
                "skill_load_verified": True,
                "structured_answer": {
                    "answer": "Synthetic guidance",
                    "decision": "needs_approval",
                    "limit_krw": 150000,
                    "citations": ["TRAVEL-2026"],
                },
                "output_directory": "/home/session/workshop-evidence/unit",
            }
            response = {
                "id": "resp-unit",
                "status": "completed",
                "agent_session_id": "session-unit",
                "agent_reference": {"name": "lab-unit-hosted", "version": "2"},
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": json.dumps(result)}],
                    }
                ],
            }
            text = (
                "data: " + json.dumps({"type": "response.completed", "response": response}) + "\n\n"
            )
            self.assertTrue(VERIFY.verify(text, package, "lab-unit-hosted", "2")["verified"])
            with self.assertRaises(ValueError):
                VERIFY.verify(text, package, "lab-unit-hosted", "1")
