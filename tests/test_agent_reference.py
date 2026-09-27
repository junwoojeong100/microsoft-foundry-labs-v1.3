import io
import json
import os
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from foundry_workshop.cli import main
from foundry_workshop.cloud import load_agent_reference, save_agent_reference
from foundry_workshop.settings import Settings
from tests import workspace


class AgentReferenceTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(
            project_endpoint="https://unit.services.ai.azure.com/api/projects/project",
            deployment="model",
            tenant_id="00000000-0000-4000-8000-000000000001",
            auth_mode="cli",
            managed_identity_client_id=None,
            max_output_tokens=2048,
        )
        self.environment = patch.dict(os.environ, {"WORKSHOP_PREFIX": "lab-unit"}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.created = {"agent_name": "lab-unit-policy-ko", "agent_version": "7"}

    def test_saved_version_is_exact_and_scoped(self):
        with workspace() as root:
            save_agent_reference(root, self.settings, self.created)
            result = load_agent_reference(root, self.settings, self.created["agent_name"])
            self.assertEqual(result["agent_version"], "7")
            for settings in (
                replace(
                    self.settings,
                    project_endpoint="https://other.services.ai.azure.com/api/projects/project",
                ),
                replace(self.settings, tenant_id="00000000-0000-4000-8000-000000000002"),
                replace(self.settings, language="en"),
            ):
                with self.subTest(settings=settings), self.assertRaises(ValueError):
                    load_agent_reference(root, settings, self.created["agent_name"])
            with self.assertRaises(FileExistsError):
                save_agent_reference(root, self.settings, self.created)

    def test_missing_corrupt_or_changed_reference_never_selects_latest(self):
        with workspace() as root:
            with self.assertRaisesRegex(ValueError, "No saved agent version"):
                load_agent_reference(root, self.settings, self.created["agent_name"])
            save_agent_reference(root, self.settings, self.created)
            path = root / "outputs/agents/lab-unit-policy-ko.json"
            value = json.loads(path.read_text())
            value["agent_version"] = None
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "latest"):
                load_agent_reference(root, self.settings, self.created["agent_name"])
            value["agent_version"] = "7"
            value["corpus_hash"] = "changed"
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "corpus"):
                load_agent_reference(root, self.settings, self.created["agent_name"])

    def test_name_paths_are_validated(self):
        with workspace() as root:
            for name in ("outside-agent", "lab-unit-../../outside", "lab-unit-X"):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    load_agent_reference(root, self.settings, name)

    def test_cli_creates_once_and_invokes_saved_version_without_retyping(self):
        with workspace() as root:
            project, client = MagicMock(), MagicMock()
            project.agents.create_version.return_value = SimpleNamespace(
                name=self.created["agent_name"], version="7", id="agent-unit"
            )

            @contextmanager
            def clients(_):
                yield project, client

            with (
                patch("foundry_workshop.settings.Settings.from_env", return_value=self.settings),
                patch("foundry_workshop.cloud.project_clients", side_effect=clients),
                patch(
                    "foundry_workshop.cloud.invoke_prompt_agent", return_value={"mode": "test"}
                ) as invoke,
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(main(root, ["prompt-agent", "create", "--confirm-create"]), 0)
                self.assertEqual(
                    main(root, ["prompt-agent", "invoke", "--question", "합성 질문"]), 0
                )
                invoke.assert_called_once_with(
                    client, "lab-unit-policy-ko", "7", "합성 질문", settings=self.settings
                )
                self.assertEqual(main(root, ["prompt-agent", "create", "--confirm-create"]), 2)
            project.agents.create_version.assert_called_once()
