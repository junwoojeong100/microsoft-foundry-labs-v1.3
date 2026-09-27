import os
import unittest
from unittest.mock import MagicMock, patch

from foundry_workshop import memory_lab
from foundry_workshop.cli import parser
from foundry_workshop.contracts import load_cases, write_json

from . import ROOT, workspace
from .test_toolbox import settings

ENVIRONMENT = {
    "WORKSHOP_PREFIX": "lab-unit",
    "AZURE_AI_EMBEDDING_DEPLOYMENT_NAME": "unit-embedding",
}


class MemoryContractTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, ENVIRONMENT, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def test_plan_has_explicit_retention_and_two_synthetic_scopes(self):
        value = memory_lab.plan(settings())
        self.assertFalse(value["azure_requests_sent"])
        self.assertEqual(value["default_ttl_seconds"], 3600)
        self.assertEqual(value["scopes"], ["lab-unit-en-alpha", "lab-unit-en-beta"])
        self.assertNotIn("userId", str(value))
        with self.assertRaises(ValueError):
            memory_lab.scope_name(settings(), "real-customer")

    def test_memory_content_comes_from_the_original_dev_question_not_gold(self):
        for language in ("en", "ko"):
            content = memory_lab.content_for(ROOT, settings(language), "D02", "unit-marker")
            case = next(
                item for item in load_cases(ROOT, "dev", language) if item["case_id"] == "D02"
            )
            self.assertIn(case["question"], content)
            self.assertIn("unit-marker", content)
            self.assertNotIn("expected_limit_krw", content)
            with self.assertRaises(ValueError):
                memory_lab.content_for(ROOT, settings(language), "H01", "unit")

    def test_every_write_delete_and_inference_gate_stops_before_cloud_calls(self):
        project = MagicMock()
        client = MagicMock()
        with workspace() as root:
            with self.assertRaisesRegex(ValueError, "confirm-create"):
                memory_lab.create(project, root, settings(), confirmed=False)
            with self.assertRaisesRegex(ValueError, "confirm-write"):
                memory_lab.put(
                    project,
                    root,
                    settings(),
                    "alpha",
                    "D02",
                    confirmed_write=False,
                    confirmed_cost=True,
                )
            with self.assertRaisesRegex(ValueError, "confirm-cost"):
                memory_lab.recall(
                    project, client, root, settings(), "alpha", "unit", confirmed=False
                )
            with self.assertRaisesRegex(ValueError, "confirm-delete"):
                memory_lab.forget(project, root, settings(), "unit", confirmed=False)
            with self.assertRaisesRegex(ValueError, "confirm-delete"):
                memory_lab.cleanup(project, root, settings(), confirmed=False)
        self.assertEqual(project.mock_calls, [])
        self.assertEqual(client.mock_calls, [])

    def test_configuration_drift_cannot_adopt_another_store(self):
        with workspace() as root:
            path = memory_lab.ownership_path(root, settings())
            write_json(
                path, {"plan": memory_lab.plan(settings()), "owner": "unit-owner", "items": {}}
            )
            memory_lab.load_ownership(root, settings())
            with patch.dict(os.environ, {"AZURE_AI_EMBEDDING_DEPLOYMENT_NAME": "other"}):
                with self.assertRaisesRegex(ValueError, "configuration changed"):
                    memory_lab.load_ownership(root, settings())

    def test_cli_restricts_scope_and_requires_explicit_cost_confirmation(self):
        args = parser().parse_args(
            ["--language", "en", "memory", "recall", "--scope", "alpha", "--label", "unit"]
        )
        self.assertFalse(args.confirm_cost)
        args = parser().parse_args(["memory", "put", "--scope", "alpha", "--case", "D02"])
        self.assertFalse(args.confirm_write)
        self.assertFalse(args.confirm_cost)
