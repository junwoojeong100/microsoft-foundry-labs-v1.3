from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "scripts"))
selfstudy = importlib.import_module("selfstudy")
bundler = importlib.import_module("package_workshop")
bridge = importlib.import_module("v12")

SUB = "11111111-1111-4111-8111-111111111111"
TENANT = "22222222-2222-4222-8222-222222222222"
USER = "33333333-3333-4333-8333-333333333333"
PROJECT_MI = "44444444-4444-4444-8444-444444444444"
ACCOUNT_MI = "55555555-5555-4555-8555-555555555555"
SEARCH_MI = "66666666-6666-4666-8666-666666666666"
APP_ID = "77777777-7777-4777-8777-777777777777"
HOST_MI = "88888888-8888-4888-8888-888888888888"
ACCOUNT = f"/subscriptions/{SUB}/resourceGroups/rg-lab/providers/Microsoft.CognitiveServices/accounts/lab"
PROJECT = ACCOUNT + "/projects/p"
SEARCH = f"/subscriptions/{SUB}/resourceGroups/rg-search/providers/Microsoft.Search/searchServices/search-lab"
INSIGHTS = f"/subscriptions/{SUB}/resourceGroups/rg-logs/providers/Microsoft.Insights/components/insights"
ENDPOINT = "https://custom-lab.services.ai.azure.com/api/projects/p"


class SelfStudyTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(
            self.stack.enter_context(
                tempfile.TemporaryDirectory(prefix="mf-selfstudy-")
            )
        )
        self.source = self.root / ".reference/v1.2"
        self.stack.enter_context(patch.object(selfstudy, "ROOT", self.root))
        self.stack.enter_context(patch.object(selfstudy, "SOURCE", self.source))
        self.stack.enter_context(
            patch.object(selfstudy, "STATE", self.root / ".selfstudy/azure.json")
        )
        self.stack.enter_context(patch.object(selfstudy, "ENV", self.source / ".env"))
        self.stack.enter_context(patch.object(selfstudy, "verify_source"))
        self.calls = []
        self.reader = self.stack.enter_context(
            patch.object(selfstudy, "az_json", side_effect=self.fake_azure)
        )

    def fake_azure(self, *args):
        self.calls.append(args)
        if args[:2] == ("account", "show"):
            return {"id": SUB, "tenantId": TENANT, "user": {"type": "user"}}
        if args[:3] == ("resource", "show", "--ids"):
            resource_id = args[3]
            if resource_id == PROJECT:
                return {
                    "id": PROJECT,
                    "name": "p",
                    "type": "Microsoft.CognitiveServices/accounts/projects",
                    "location": "swedencentral",
                    "identity": {"principalId": PROJECT_MI},
                }
            if resource_id == ACCOUNT:
                return {
                    "id": ACCOUNT,
                    "name": "lab",
                    "type": "Microsoft.CognitiveServices/accounts",
                    "location": "swedencentral",
                    "identity": {"principalId": ACCOUNT_MI},
                    "properties": {"customSubDomainName": "custom-lab"},
                }
            if resource_id == SEARCH:
                return {
                    "id": SEARCH,
                    "name": "search-lab",
                    "type": "Microsoft.Search/searchServices",
                    "location": "swedencentral",
                    "identity": {"principalId": SEARCH_MI},
                }
            if resource_id == INSIGHTS:
                return {
                    "id": INSIGHTS,
                    "name": "insights",
                    "type": "Microsoft.Insights/components",
                    "properties": {"AppId": APP_ID},
                }
        if args[:4] == ("cognitiveservices", "account", "deployment", "show"):
            return {
                "name": "workshop-chat",
                "properties": {
                    "provisioningState": "Succeeded",
                    "model": {"name": "test-model", "version": "test"},
                },
            }
        self.fail(f"Unexpected Azure request: {args}")

    def configure(self):
        return selfstudy.configure(PROJECT, ENDPOINT, "workshop-chat", "mfv2-user-0927")

    def test_configure_reads_only_explicit_subscription_and_writes_one_environment(
        self,
    ):
        state = self.configure()
        values = selfstudy.env_values()
        self.assertEqual(values["AZURE_SUBSCRIPTION_ID"], SUB)
        self.assertEqual(values["AZURE_AI_PROJECT_ENDPOINT"], ENDPOINT)
        self.assertEqual(values["WORKSHOP_MAX_OUTPUT_TOKENS"], "2048")
        self.assertEqual(
            state["resources"][PROJECT.casefold()]["principal_id"], PROJECT_MI
        )
        self.assertFalse(state["model_invoked"])
        self.assertTrue(state["management_metadata_read"])
        for command in self.calls:
            self.assertIn("show", command)
            self.assertFalse({"create", "delete", "set", "login"}.intersection(command))
        self.assertEqual(len(self.calls), 4)
        self.assertFalse(
            {
                "AZURE_ACCESS_TOKEN",
                "OPENAI_API_KEY",
                "AZURE_CLIENT_SECRET",
            }.intersection(values)
        )
        self.assertEqual(selfstudy.ENV.stat().st_mode & 0o777, 0o600)

    def test_invalid_project_id_and_endpoint_rejected_before_azure(self):
        for resource_id, endpoint in (
            (ACCOUNT, ENDPOINT),
            (PROJECT, "https://custom-lab.openai.azure.com"),
            (PROJECT, ENDPOINT + "?token=test"),
            (PROJECT, ENDPOINT + "/other"),
        ):
            with self.subTest(resource_id=resource_id, endpoint=endpoint):
                with self.assertRaises(selfstudy.SetupError):
                    selfstudy.configure(
                        resource_id, endpoint, "workshop-chat", "mfv2-user"
                    )
        self.assertEqual(self.calls, [])

    def test_account_domain_must_match_server_metadata(self):
        with self.assertRaisesRegex(selfstudy.SetupError, "customSubDomainName"):
            selfstudy.configure(
                PROJECT,
                "https://someone-else.services.ai.azure.com/api/projects/p",
                "workshop-chat",
                "mfv2-user",
            )
        self.assertFalse(selfstudy.ENV.exists())
        self.assertFalse(selfstudy.STATE.exists())

    def test_incomplete_deployment_does_not_write_settings(self):
        original = self.fake_azure

        def pending(*args):
            value = original(*args)
            if args[0] == "cognitiveservices":
                value["properties"]["provisioningState"] = "Creating"
            return value

        self.reader.side_effect = pending
        with self.assertRaisesRegex(selfstudy.SetupError, "Succeeded"):
            self.configure()
        self.assertFalse(selfstudy.ENV.exists())

    def test_another_prefix_or_existing_environment_is_preserved(self):
        self.configure()
        before = selfstudy.ENV.read_bytes()
        with self.assertRaisesRegex(selfstudy.SetupError, "덮어쓰지"):
            selfstudy.configure(PROJECT, ENDPOINT, "workshop-chat", "mfv2-other")
        self.assertEqual(selfstudy.ENV.read_bytes(), before)
        selfstudy.STATE.unlink()
        selfstudy.ENV.write_text(
            "AZURE_AI_PROJECT_ENDPOINT='https://other.services.ai.azure.com/api/projects/p'\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(selfstudy.SetupError, "기존 .env"):
            self.configure()
        self.assertIn("other.services", selfstudy.ENV.read_text())

    def test_resource_registration_is_read_only_and_role_identity_paths_are_distinct(
        self,
    ):
        self.configure()
        selfstudy.register_resource(
            "search", SEARCH, "https://search-lab.search.windows.net"
        )
        selfstudy.register_resource("insights", INSIGHTS, None)
        before = len(self.calls)
        plan = selfstudy.role_plan(USER, HOST_MI)
        self.assertEqual(len(self.calls), before)
        self.assertFalse(plan["role_assignments_executed"])
        rows = plan["assignments"]
        expected = [
            (USER, "Search Index Data Contributor", SEARCH),
            (PROJECT_MI, "Search Index Data Reader", SEARCH),
            (PROJECT_MI, "Search Service Contributor", SEARCH),
            (ACCOUNT_MI, "Search Index Data Reader", SEARCH),
            (SEARCH_MI, "Cognitive Services User", ACCOUNT),
            (HOST_MI, "Foundry User", PROJECT),
        ]
        actual = {(row["principal"], row["role"], row["scope"]) for row in rows}
        self.assertTrue(set(expected).issubset(actual))
        for row in rows:
            self.assertIn(f'--subscription "{SUB}"', row["command"])
            self.assertNotEqual(row["role"], "Owner")
        self.assertEqual(
            selfstudy.env_values()["AZURE_APPLICATION_INSIGHTS_APP_ID"], APP_ID
        )

    def test_search_type_endpoint_and_subscription_cannot_be_substituted(self):
        self.configure()
        for kind, resource_id, endpoint in (
            ("search", INSIGHTS, "https://search-lab.search.windows.net"),
            ("search", SEARCH, "https://another.search.windows.net"),
            (
                "search",
                SEARCH.replace(SUB, TENANT),
                "https://search-lab.search.windows.net",
            ),
        ):
            with self.subTest(kind=kind, resource_id=resource_id):
                with self.assertRaises(selfstudy.SetupError):
                    selfstudy.register_resource(kind, resource_id, endpoint)

    def test_settings_allowlist_protects_scope_and_secrets(self):
        self.configure()
        for key in (
            "AZURE_SUBSCRIPTION_ID",
            "WORKSHOP_PREFIX",
            "OPENAI_API_KEY",
            "AZURE_CLIENT_SECRET",
        ):
            with self.subTest(key=key), self.assertRaises(selfstudy.SetupError):
                selfstudy.set_value(key, "unsafe")
        for key, value in (
            ("WORKSHOP_EMBEDDING_DIMENSIONS", "0"),
            ("WORKSHOP_EMBEDDING_API", "fallback"),
            ("WORKSHOP_IQ_RERANKER_THRESHOLD", "nan"),
            ("WORKSHOP_MAX_OUTPUT_TOKENS", "100000"),
            ("AZURE_AI_MODEL_DEPLOYMENT_NAME", "x\nAZURE_SUBSCRIPTION_ID=other"),
            ("AZURE_OPENAI_ENDPOINT", "https://other.openai.azure.com"),
        ):
            with (
                self.subTest(key=key),
                self.assertRaises((selfstudy.SetupError, ValueError)),
            ):
                selfstudy.set_value(key, value)

    def test_models_command_and_configuration_update_preserve_other_values(self):
        self.configure()
        selfstudy.set_value(
            "AZURE_AI_EVALUATION_MODEL_DEPLOYMENT_NAME", "workshop-judge"
        )
        selfstudy.set_models(["primary=workshop-chat", "comparison=workshop-compare"])
        values = selfstudy.env_values()
        self.assertEqual(
            json.loads(values["WORKSHOP_MODEL_DEPLOYMENTS_JSON"])["comparison"],
            "workshop-compare",
        )
        self.assertEqual(
            values["AZURE_AI_EVALUATION_MODEL_DEPLOYMENT_NAME"], "workshop-judge"
        )
        for models in (
            ["primary=workshop-chat", "same=workshop-chat"],
            ["other=not-primary"],
            ["invalid"],
        ):
            with self.subTest(models=models), self.assertRaises(selfstudy.SetupError):
                selfstudy.set_models(models)

    def test_shell_configuration_conflict_is_not_silent(self):
        self.configure()
        with self.assertRaisesRegex(selfstudy.SetupError, "셸"):
            selfstudy.validate_runtime_environment(
                {"AZURE_AI_PROJECT_ENDPOINT": "https://other.invalid"},
                explicit_model=False,
            )
        selfstudy.validate_runtime_environment(
            {"AZURE_AI_MODEL_DEPLOYMENT_NAME": "other"}, explicit_model=True
        )
        with self.assertRaises(selfstudy.SetupError):
            selfstudy.validate_runtime_environment(
                {"AZURE_AI_MODEL_DEPLOYMENT_NAME": "other"}, explicit_model=False
            )

    def test_compare_files_uses_exact_bytes_and_stays_inside_workspace(self):
        first, second = self.root / "first.txt", self.root / "second.txt"
        first.write_bytes(b"policy")
        second.write_bytes(b"policy")
        self.assertTrue(selfstudy.compare_files(first, second)["files_equal"])
        second.write_bytes(b"changed")
        with self.assertRaisesRegex(selfstudy.SetupError, "bytes"):
            selfstudy.compare_files(first, second)
        with self.assertRaisesRegex(selfstudy.SetupError, "폴더"):
            selfstudy.compare_files(Path("/etc/hosts"), second)

    def test_resilience_wrapper_disables_external_telemetry_only_for_child(self):
        with patch.dict(
            os.environ,
            {
                "AZURE_AI_PROJECT_ENDPOINT": "preserve-parent",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "https://example.invalid",
            },
        ):
            _, _, child = bridge.command_arguments(["--script", "resilience", "check"])
            self.assertNotIn("AZURE_AI_PROJECT_ENDPOINT", child)
            self.assertNotIn("OTEL_EXPORTER_OTLP_ENDPOINT", child)
            self.assertEqual(child["OTEL_SDK_DISABLED"], "true")
            self.assertEqual(os.environ["AZURE_AI_PROJECT_ENDPOINT"], "preserve-parent")

    def prepare_capture(self):
        self.configure()
        folder = self.root / ".selfstudy/hosted"
        folder.mkdir()
        (folder / "azure.yaml").write_text("{}")
        output = self.root / ".selfstudy/capture/response.raw"
        return folder, output

    def capture_process(self, command, **kwargs):
        if command[1:3] == ["env", "get-value"]:
            return subprocess.CompletedProcess(command, 0, ENDPOINT + "\n", "")
        if command[1:4] == ["ai", "agent", "show"]:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps(
                    {
                        "name": "mfv2-user-0927-hosted",
                        "version": "3",
                        "status": "active",
                    }
                ),
                "",
            )
        if command[1:4] == ["ai", "agent", "invoke"]:
            return subprocess.CompletedProcess(
                command, 0, "data: 합성 응답\n".encode(), b""
            )
        self.fail(f"Unexpected process: {command}")

    def test_capture_is_explicit_and_retains_utf8_bytes_without_success_claim(self):
        folder, output = self.prepare_capture()
        with (
            patch.object(selfstudy.shutil, "which", return_value="/fake/azd"),
            patch.object(
                selfstudy.subprocess, "run", side_effect=self.capture_process
            ) as run,
        ):
            with self.assertRaisesRegex(selfstudy.SetupError, "confirm-cost"):
                selfstudy.capture_hosted(
                    folder, "mfv2-user-0927-hosted", "3", output, False
                )
            run.assert_not_called()
            result = selfstudy.capture_hosted(
                folder, "mfv2-user-0927-hosted", "3", output, True
            )
        self.assertEqual(output.read_bytes(), "data: 합성 응답\n".encode())
        self.assertFalse(result["agent_response_verified"])
        self.assertEqual(run.call_count, 3)
        self.assertIn("--new-conversation", run.call_args.args[0])
        with self.assertRaises(selfstudy.SetupError):
            selfstudy.capture_hosted(folder, "mfv2-user-0927-hosted", "3", output, True)

    def test_capture_timeout_and_failure_preserve_original_output(self):
        folder, output = self.prepare_capture()

        def timeout(command, **kwargs):
            if command[1:4] == ["ai", "agent", "invoke"]:
                raise subprocess.TimeoutExpired(
                    command, 300, output=b"partial", stderr=b"timeout"
                )
            return self.capture_process(command, **kwargs)

        with (
            patch.object(selfstudy.shutil, "which", return_value="/fake/azd"),
            patch.object(selfstudy.subprocess, "run", side_effect=timeout),
        ):
            with self.assertRaisesRegex(selfstudy.SetupError, "시간 초과"):
                selfstudy.capture_hosted(
                    folder, "mfv2-user-0927-hosted", "3", output, True
                )
        self.assertEqual(output.read_bytes(), b"partial")
        self.assertEqual(output.with_suffix(".stderr.txt").read_bytes(), b"timeout")

    def test_capture_wrong_version_never_invokes(self):
        folder, output = self.prepare_capture()
        with (
            patch.object(selfstudy.shutil, "which", return_value="/fake/azd"),
            patch.object(
                selfstudy.subprocess, "run", side_effect=self.capture_process
            ) as run,
        ):
            with self.assertRaisesRegex(selfstudy.SetupError, "활성"):
                selfstudy.capture_hosted(
                    folder, "mfv2-user-0927-hosted", "99", output, True
                )
        self.assertEqual(run.call_count, 2)
        self.assertFalse(output.exists())

    def test_packaging_excludes_personal_state_and_records_hashes(self):
        with patch.object(bundler, "ROOT", self.root):
            for name in bundler.ROOT_FILES:
                destination = self.root / name
                destination.write_text("{}" if name == "v12-reference.json" else "test")
            for directory in bundler.DIRECTORIES:
                (self.root / directory).mkdir()
                (self.root / directory / "sample.md").write_text("synthetic")
            for name in (
                ".env",
                ".selfstudy/private.json",
                ".reference/v1.2/.env",
                "outputs/private.json",
            ):
                destination = self.root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text("must not ship")
            output = bundler.build(self.root / "dist/test.zip")
            with ZipFile(output) as archive:
                names = archive.namelist()
                self.assertTrue(any(name.endswith("/README.md") for name in names))
                self.assertFalse(
                    any(
                        "/.reference/" in name
                        or "/outputs/" in name
                        or name.endswith("/.env")
                        for name in names
                    )
                )
                manifest = json.loads(
                    archive.read("microsoft-foundry-v1.5-labs/bundle-manifest.json")
                )
                self.assertTrue(manifest["runtime_download_required"])
                self.assertEqual(manifest["pacing"], "self-paced")
            with self.assertRaises(FileExistsError):
                bundler.build(output)
