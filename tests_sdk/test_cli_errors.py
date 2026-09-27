import builtins
import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import AsyncMock, patch

from agent_framework.exceptions import ChatClientException
from azure.identity import CredentialUnavailableError

from foundry_workshop.cli import main
from foundry_workshop.settings import Settings


class FrameworkCliErrorTests(unittest.TestCase):
    def settings(self):
        return Settings(
            project_endpoint="https://unit.services.ai.azure.com/api/projects/workshop",
            deployment="unit-deployment",
            tenant_id="00000000-0000-0000-0000-000000000001",
            auth_mode="cli",
            managed_identity_client_id=None,
            max_output_tokens=2048,
        )

    def wrapped_timeout(self):
        timeout = subprocess.TimeoutExpired(["az", "account", "get-access-token"], 30)
        credential = CredentialUnavailableError("Failed to invoke the Azure CLI")
        credential.__cause__ = timeout
        error = ChatClientException("The model request failed.", credential)
        error.__cause__ = credential
        return error

    def test_framework_commands_report_the_cause_once_without_a_success_file(self):
        commands = {
            "maf": "foundry_workshop.agents.run_agent",
            "workflow": "foundry_workshop.agents.run_workflow",
            "workflow-agent": "foundry_workshop.runtime.run_pipeline",
            "maf-evaluate": "foundry_workshop.tool_evaluation.evaluate_tool_use",
            "serve": "foundry_workshop.agents.serve",
        }
        for language in ("en", "ko"):
            for command, target in commands.items():
                with (
                    self.subTest(language=language, command=command),
                    tempfile.TemporaryDirectory() as directory,
                ):
                    root = Path(directory)
                    (root / "outputs").mkdir()
                    output = root / "outputs/failed.json"
                    arguments = ["--language", language, command]
                    if command != "serve":
                        arguments += ["--output", str(output)]
                    if command == "maf-evaluate":
                        arguments += ["--confirm-cost"]
                    stdout, stderr = io.StringIO(), io.StringIO()
                    options = {} if command == "serve" else {"new_callable": AsyncMock}
                    with (
                        patch("foundry_workshop.settings.load_environment"),
                        patch(
                            "foundry_workshop.settings.Settings.from_env",
                            return_value=self.settings(),
                        ),
                        patch(target, side_effect=self.wrapped_timeout(), **options) as call,
                        redirect_stdout(stdout),
                        redirect_stderr(stderr),
                    ):
                        status = main(root, arguments)
                    self.assertEqual(status, 2)
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertFalse(output.exists())
                    self.assertIn("MAF request failed: ChatClientException", stderr.getvalue())
                    self.assertIn("TimeoutExpired", stderr.getvalue())
                    self.assertIn("timed out after 30 seconds", stderr.getvalue())
                    self.assertIn("No provider/model fallback was used.", stderr.getvalue())
                    self.assertIn("docs/troubleshooting.md", stderr.getvalue())
                    self.assertNotIn("Traceback", stderr.getvalue())
                    call.assert_called_once()
                    if command != "serve":
                        call.assert_awaited_once()

    def test_debug_retains_the_original_sdk_and_credential_exception_chain(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("foundry_workshop.settings.load_environment"),
            patch("foundry_workshop.settings.Settings.from_env", return_value=self.settings()),
            patch(
                "foundry_workshop.agents.run_workflow",
                new_callable=AsyncMock,
                side_effect=self.wrapped_timeout(),
            ),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            status = main(Path(directory), ["--debug", "workflow", "--pattern", "group-chat"])
        self.assertEqual(status, 2)
        self.assertEqual(stdout.getvalue(), "")
        for name in (
            "Traceback",
            "ChatClientException",
            "CredentialUnavailableError",
            "TimeoutExpired",
        ):
            self.assertIn(name, stderr.getvalue())

    def test_unexpected_programming_errors_are_not_masked_as_framework_failures(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("foundry_workshop.settings.load_environment"),
            patch("foundry_workshop.settings.Settings.from_env", return_value=self.settings()),
            patch(
                "foundry_workshop.agents.run_workflow",
                new_callable=AsyncMock,
                side_effect=RuntimeError("Explicit programming error"),
            ),
            self.assertRaisesRegex(RuntimeError, "Explicit programming error"),
        ):
            main(Path(directory), ["workflow"])

    def test_plain_model_calls_do_not_import_optional_agent_framework(self):
        original_import = builtins.__import__

        def import_without_framework(name, *args, **kwargs):
            if name.startswith("agent_framework"):
                self.fail("A plain model call must not require the optional agent SDK.")
            return original_import(name, *args, **kwargs)

        stdout = io.StringIO()
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("foundry_workshop.settings.load_environment"),
            patch("foundry_workshop.settings.Settings.from_env", return_value=self.settings()),
            patch("foundry_workshop.cloud.project_clients") as clients,
            patch("foundry_workshop.cloud.call_model", return_value={"mode": "unit-test"}),
            patch("builtins.__import__", side_effect=import_without_framework),
            redirect_stdout(stdout),
        ):
            clients.return_value.__enter__.return_value = (None, None)
            self.assertEqual(main(Path(directory), ["model"]), 0)
