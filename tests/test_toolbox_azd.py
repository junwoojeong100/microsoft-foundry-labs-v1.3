import json
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import patch

from foundry_workshop.packaging import file_hashes
from foundry_workshop.profiles import RuntimeProfile, packaged_profile

from . import workspace
from .test_ci_helpers import ENV
from .test_packaging import load_script
from .test_toolbox import ENVIRONMENT, seed_ledger, settings

PACKAGE = load_script("package_toolbox")
PREPARE = load_script("prepare_hosted_azd")
HOSTED_PACKAGE = load_script("package_hosted")


class ToolboxAzdTests(unittest.TestCase):
    def test_matrix_preparation_preserves_v1_and_v2_packages_and_explicit_runtime_settings(self):
        models = {"a": "gpt-6-sol", "b": "approved-second-model"}
        environment = {
            **ENV,
            **ENVIRONMENT,
            "WORKSHOP_MODEL_DEPLOYMENTS_JSON": json.dumps(models),
            "WORKSHOP_HOSTED_AGENT_NAME": "lab-unit-matrix",
            "AZURE_SEARCH_INDEX_NAME": "lab-unit-text",
            "AZURE_SEARCH_KNOWLEDGE_SOURCE_NAME": "lab-unit-text-source",
            "AZURE_SEARCH_KNOWLEDGE_BASE_NAME": "lab-unit-text-kb",
        }
        for language in ("en", "ko"):
            for threshold in ("", "0", "2.5"):
                with (
                    self.subTest(language=language, threshold=threshold),
                    workspace() as root,
                    tempfile.TemporaryDirectory() as folder,
                    patch.dict(
                        os.environ,
                        {**environment, "WORKSHOP_IQ_RERANKER_THRESHOLD": threshold},
                        clear=True,
                    ),
                ):
                    configuration = replace(
                        settings(language),
                        openai_endpoint="https://unit.openai.azure.com",
                        max_output_tokens=1024,
                    )
                    (root / "azure.yaml").write_text('{"name":"preserve-source-project"}\n')
                    previous = None
                    for prompt in ("v1", "v2"):
                        profile = RuntimeProfile(
                            kind="workflow",
                            retrieval="iq",
                            prompt=prompt,
                            api="account-chat",
                            protocol="invocations",
                            language=language,
                        )
                        package = HOSTED_PACKAGE.build(root, profile)
                        hashes = file_hashes(package)
                        destination = Path(folder) / prompt
                        with patch.object(PREPARE.subprocess, "run") as execute:
                            path = PREPARE.prepare(
                                package,
                                destination,
                                configuration,
                                "lab-unit-matrix",
                                kind="matrix",
                            )
                        execute.assert_not_called()
                        data = json.loads(path.read_text())
                        self.assertEqual(
                            set(data["services"]), {"workshop-project", "lab-unit-matrix"}
                        )
                        self.assertNotIn("deployments", data["services"]["workshop-project"])
                        agent = data["services"]["lab-unit-matrix"]
                        self.assertEqual(
                            agent["protocols"], [{"protocol": "invocations", "version": "1.0.0"}]
                        )
                        runtime = agent["env"]
                        self.assertEqual(
                            json.loads(runtime["WORKSHOP_MODEL_DEPLOYMENTS_JSON"]), models
                        )
                        self.assertEqual(
                            runtime["AZURE_OPENAI_ENDPOINT"], configuration.openai_endpoint
                        )
                        self.assertEqual(runtime["WORKSHOP_MAX_OUTPUT_TOKENS"], "1024")
                        self.assertEqual(runtime["WORKSHOP_AUTH_MODE"], "managed-identity")
                        for key in (
                            "AZURE_SEARCH_ENDPOINT",
                            "AZURE_SEARCH_INDEX_NAME",
                            "AZURE_SEARCH_KNOWLEDGE_SOURCE_NAME",
                            "AZURE_SEARCH_KNOWLEDGE_BASE_NAME",
                        ):
                            self.assertEqual(runtime[key], environment[key])
                        if threshold:
                            self.assertEqual(
                                float(runtime["WORKSHOP_IQ_RERANKER_THRESHOLD"]), float(threshold)
                            )
                        else:
                            self.assertNotIn("WORKSHOP_IQ_RERANKER_THRESHOLD", runtime)
                        self.assertEqual(file_hashes(destination / agent["project"]), hashes)
                        self.assertEqual(file_hashes(package), hashes)
                        if previous:
                            self.assertEqual(file_hashes(previous[0]), previous[1])
                        previous = (destination, file_hashes(destination))
                    self.assertEqual(
                        (root / "azure.yaml").read_text(), '{"name":"preserve-source-project"}\n'
                    )

    def test_matrix_rejects_other_profiles_and_invalid_configuration_before_writing(self):
        profile = RuntimeProfile(
            kind="workflow",
            retrieval="iq",
            api="account-chat",
            protocol="invocations",
            language="en",
        )
        environment = {
            **ENV,
            **ENVIRONMENT,
            "WORKSHOP_MODEL_DEPLOYMENTS_JSON": '{"a":"gpt-6-sol"}',
            "WORKSHOP_HOSTED_AGENT_NAME": "lab-unit-matrix",
        }
        configuration = replace(settings(), openai_endpoint="https://unit.openai.azure.com")
        with workspace() as root, tempfile.TemporaryDirectory() as folder:
            for field, value in (
                ("language", "ko"),
                ("kind", "policy"),
                ("pattern", "concurrent"),
                ("retrieval", "local"),
                ("api", "project-responses"),
                ("protocol", "responses"),
            ):
                with self.subTest(field=field), patch.dict(os.environ, environment, clear=True):
                    package = HOSTED_PACKAGE.build(root, replace(profile, **{field: value}))
                    with self.assertRaisesRegex(ValueError, "matrix package"):
                        PREPARE.prepare(
                            package,
                            Path(folder) / field,
                            configuration,
                            "lab-unit-matrix",
                            kind="matrix",
                        )
            package = HOSTED_PACKAGE.build(root, profile)
            for index, (changes, overrides) in enumerate(
                [
                    ({}, {"openai_endpoint": None}),
                    ({}, {"openai_endpoint": "https://another.openai.azure.com"}),
                    ({"WORKSHOP_HOSTED_AGENT_NAME": "lab-unit-other"}, {}),
                    ({"WORKSHOP_MODEL_DEPLOYMENTS_JSON": ""}, {}),
                    ({"WORKSHOP_MODEL_DEPLOYMENTS_JSON": '{"a":"unapproved-default"}'}, {}),
                    (
                        {"WORKSHOP_MODEL_DEPLOYMENTS_JSON": '{"a":"gpt-6-sol","b":"gpt-6-sol"}'},
                        {},
                    ),
                    ({"WORKSHOP_IQ_RERANKER_THRESHOLD": "nan"}, {}),
                    ({"AZURE_SEARCH_ENDPOINT": ""}, {}),
                ]
            ):
                with (
                    self.subTest(changes=changes, overrides=overrides),
                    patch.dict(os.environ, {**environment, **changes}, clear=True),
                    self.assertRaises(ValueError),
                ):
                    PREPARE.prepare(
                        package,
                        Path(folder) / f"invalid-{index}",
                        replace(configuration, **overrides),
                        "lab-unit-matrix",
                        kind="matrix",
                    )
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_introductory_runtime_preparation_preserves_packages_and_existing_source_projects(self):
        for language in ("en", "ko"):
            with (
                self.subTest(language=language),
                workspace() as root,
                tempfile.TemporaryDirectory() as folder,
                patch.dict(os.environ, ENV, clear=True),
            ):
                original_project = b'{"name":"keep-the-existing-source-project"}\n'
                (root / "azure.yaml").write_bytes(original_project)
                configuration = replace(settings(language), max_output_tokens=1024)
                profiles = [
                    RuntimeProfile(language=language),
                    *[
                        RuntimeProfile(kind="workflow", pattern=pattern, language=language)
                        for pattern in ("sequential", "concurrent", "group-chat")
                    ],
                ]
                for profile in profiles:
                    with self.subTest(profile=profile.to_dict()):
                        package = HOSTED_PACKAGE.build(root, profile)
                        original_package = file_hashes(package)
                        destination = Path(folder) / profile.package_name
                        path = PREPARE.prepare(
                            package, destination, configuration, "lab-unit-intro", kind="runtime"
                        )
                        data = json.loads(path.read_text())
                        self.assertEqual(
                            set(data["services"]), {"workshop-project", "lab-unit-intro"}
                        )
                        project = data["services"]["workshop-project"]
                        self.assertEqual(project["endpoint"], configuration.project_endpoint)
                        self.assertNotIn("deployments", project)
                        agent = data["services"]["lab-unit-intro"]
                        self.assertEqual(agent["name"], "lab-unit-intro")
                        self.assertEqual(agent["env"]["WORKSHOP_AUTH_MODE"], "managed-identity")
                        self.assertEqual(agent["env"]["WORKSHOP_MAX_OUTPUT_TOKENS"], "1024")
                        self.assertEqual(
                            agent["env"]["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
                            configuration.deployment,
                        )
                        self.assertNotIn("AZURE_SEARCH_ENDPOINT", agent["env"])
                        self.assertNotIn("WORKSHOP_MODEL_DEPLOYMENTS_JSON", agent["env"])
                        self.assertEqual(
                            agent["protocols"], [{"protocol": "responses", "version": "2.0.0"}]
                        )
                        copied = destination / agent["project"]
                        self.assertEqual(packaged_profile(copied), profile)
                        self.assertEqual(file_hashes(copied), original_package)
                        self.assertEqual(file_hashes(package), original_package)
                        self.assertEqual((root / "azure.yaml").read_bytes(), original_project)
                        with self.assertRaises(FileExistsError):
                            PREPARE.prepare(
                                package,
                                destination,
                                configuration,
                                "lab-unit-intro",
                                kind="runtime",
                            )

    def test_introductory_runtime_rejects_different_language_retrieval_prompt_api_and_protocol(
        self,
    ):
        profiles = [
            RuntimeProfile(kind="workflow", language="ko"),
            RuntimeProfile(kind="workflow", retrieval="iq", language="en"),
            RuntimeProfile(kind="workflow", prompt="v1", language="en"),
            RuntimeProfile(kind="workflow", api="account-chat", language="en"),
            RuntimeProfile(kind="workflow", protocol="invocations", language="en"),
        ]
        with (
            workspace() as root,
            tempfile.TemporaryDirectory() as folder,
            patch.dict(os.environ, ENV, clear=True),
        ):
            for index, profile in enumerate(profiles):
                with self.subTest(profile=profile.to_dict()):
                    package = HOSTED_PACKAGE.build(root, profile)
                    destination = Path(folder) / str(index)
                    with self.assertRaisesRegex(ValueError, "language-matched local v2 Responses"):
                        PREPARE.prepare(
                            package, destination, settings("en"), "lab-unit-intro", kind="runtime"
                        )
                    self.assertFalse(destination.exists())

    def test_ci_workflow_uses_an_isolated_exact_profile_without_search_settings(self):
        for language in ("en", "ko"):
            with (
                self.subTest(language=language),
                workspace() as root,
                tempfile.TemporaryDirectory() as folder,
            ):
                environment = {
                    **ENV,
                    "WORKSHOP_MODEL_DEPLOYMENTS_JSON": '{"primary":"gpt-6-sol"}',
                }
                with patch.dict(os.environ, environment, clear=True):
                    profile = RuntimeProfile(
                        kind="workflow", protocol="invocations", language=language
                    )
                    package = HOSTED_PACKAGE.build(root, profile)
                    path = PREPARE.prepare(
                        package,
                        Path(folder) / "run",
                        settings(language),
                        "lab-unit-ci",
                        kind="workflow",
                    )
                    data = json.loads(path.read_text())
                    self.assertEqual(set(data["services"]), {"workshop-project", "lab-unit-ci"})
                    agent = data["services"]["lab-unit-ci"]
                    self.assertEqual(
                        agent["protocols"], [{"protocol": "invocations", "version": "1.0.0"}]
                    )
                    self.assertNotIn("AZURE_SEARCH_ENDPOINT", agent["env"])
                    self.assertEqual(
                        json.loads(agent["env"]["WORKSHOP_MODEL_DEPLOYMENTS_JSON"]),
                        {"primary": "gpt-6-sol"},
                    )

    def test_ci_workflow_rejects_other_profiles_and_model_maps(self):
        with workspace() as root, tempfile.TemporaryDirectory() as folder:
            with patch.dict(
                os.environ,
                {**ENV, "WORKSHOP_MODEL_DEPLOYMENTS_JSON": '{"primary":"other"}'},
                clear=True,
            ):
                package = HOSTED_PACKAGE.build(
                    root, RuntimeProfile(kind="workflow", protocol="invocations", language="en")
                )
                with self.assertRaisesRegex(ValueError, "model map"):
                    PREPARE.prepare(
                        package,
                        Path(folder) / "bad-model",
                        settings(),
                        "lab-unit-ci",
                        kind="workflow",
                    )
                with self.assertRaisesRegex(ValueError, "profile"):
                    PREPARE.prepare(
                        package,
                        Path(folder) / "bad-language",
                        settings("ko"),
                        "lab-unit-ci",
                        kind="workflow",
                    )
                self.assertEqual(list(Path(folder).iterdir()), [])

    def test_manifest_reuses_only_the_existing_project_and_exact_package(self):
        with workspace() as root, tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, ENVIRONMENT, clear=True):
                seed_ledger(root)
                package = PACKAGE.build(root, settings(), "2", with_skill=True)
                destination = Path(folder) / "run"
                path = PREPARE.prepare(package, destination, settings(), "lab-unit-hosted")
                data = json.loads(path.read_text())
                self.assertEqual(set(data["services"]), {"workshop-project", "lab-unit-hosted"})
                project = data["services"]["workshop-project"]
                self.assertEqual(project["endpoint"], settings().project_endpoint)
                self.assertNotIn("deployments", project)
                agent = data["services"]["lab-unit-hosted"]
                self.assertEqual(agent["env"]["WORKSHOP_AUTH_MODE"], "managed-identity")
                self.assertEqual(
                    agent["protocols"], [{"protocol": "responses", "version": "2.0.0"}]
                )
                copied = destination / agent["project"]
                self.assertEqual(
                    (copied / "package-manifest.json").read_bytes(),
                    (package / "package-manifest.json").read_bytes(),
                )
                with self.assertRaises(FileExistsError):
                    PREPARE.prepare(package, destination, settings(), "lab-unit-hosted")

    def test_rejects_changed_package_before_writing(self):
        with workspace() as root, tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, ENVIRONMENT, clear=True):
                seed_ledger(root)
                package = PACKAGE.build(root, settings(), "2")
                (package / "main.py").write_text("changed")
                destination = Path(folder) / "run"
                with self.assertRaisesRegex(ValueError, "package files"):
                    PREPARE.prepare(package, destination, settings(), "lab-unit-hosted")
                self.assertFalse(destination.exists())

    def test_rejects_language_and_model_drift_and_unowned_names(self):
        with workspace() as root, tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, ENVIRONMENT, clear=True):
                seed_ledger(root)
                package = PACKAGE.build(root, settings(), "2")
                destination = Path(folder) / "run"
                with self.assertRaisesRegex(ValueError, "prefix"):
                    PREPARE.prepare(package, destination, settings(), "other-team-hosted")
                with self.assertRaisesRegex(ValueError, "language"):
                    PREPARE.prepare(package, destination, settings("ko"), "lab-unit-hosted")
                with self.assertRaisesRegex(ValueError, "model"):
                    PREPARE.prepare(
                        package,
                        destination,
                        replace(settings(), deployment="other-model"),
                        "lab-unit-hosted",
                    )
                self.assertFalse(destination.exists())

    def test_rejects_nested_projects_and_symlinked_packages(self):
        with workspace() as root, tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, ENVIRONMENT, clear=True):
                seed_ledger(root)
                package = PACKAGE.build(root, settings(), "2")
                parent = Path(folder)
                (parent / "azure.yaml").write_text("{}")
                with self.assertRaisesRegex(ValueError, "existing azd"):
                    PREPARE.prepare(package, parent / "run", settings(), "lab-unit-hosted")
                (package / "linked").symlink_to(package / "main.py")
                with self.assertRaisesRegex(ValueError, "symbolic"):
                    PREPARE.prepare(package, parent / "run", settings(), "lab-unit-hosted")

    def test_environment_bootstrap_has_no_provision_deploy_or_subscription_switch(self):
        with workspace() as root, tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {**ENVIRONMENT, **ENV}, clear=True):
                seed_ledger(root)
                package = PACKAGE.build(root, settings(), "2")
                directory = Path(folder) / "run"
                PREPARE.prepare(package, directory, settings(), "lab-unit-hosted")
                values = PREPARE.environment_values(settings(), ENV["AZURE_AI_PROJECT_ID"])

                def result(command, **kwargs):
                    output = values[command[-1]] if command[1:3] == ["env", "get-value"] else ""
                    self.assertEqual(kwargs["cwd"], directory)
                    self.assertTrue(kwargs["check"])
                    return CompletedProcess(command, 0, output, "")

                with patch.object(PREPARE.subprocess, "run", side_effect=result) as execute:
                    PREPARE.initialize_environment(
                        directory, "lab-unit-hosted", values, "swedencentral"
                    )
                calls = [call.args[0] for call in execute.call_args_list]
                self.assertTrue(all(call[:2] == ["azd", "env"] for call in calls))
                self.assertEqual(calls[0][2:4], ["new", "lab-unit-hosted"])
                self.assertEqual(values["FOUNDRY_PROJECT_ENDPOINT"], settings().project_endpoint)
                self.assertFalse(any("AZURE_DEV_USER_AGENT" in call for call in calls))

    def test_scope_and_environment_errors_are_not_reported_as_success(self):
        with workspace() as root, tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {**ENVIRONMENT, **ENV}, clear=True):
                with self.assertRaisesRegex(ValueError, "ARM ID"):
                    PREPARE.environment_values(settings(), "/subscriptions/other/projects/workshop")
                seed_ledger(root)
                package = PACKAGE.build(root, settings(), "2")
                directory = Path(folder) / "run"
                PREPARE.prepare(package, directory, settings(), "lab-unit-hosted")
                values = PREPARE.environment_values(settings(), ENV["AZURE_AI_PROJECT_ID"])
                with (
                    patch.object(
                        PREPARE.subprocess,
                        "run",
                        side_effect=CalledProcessError(1, ["azd", "env", "new"], stderr="failed"),
                    ),
                    self.assertRaises(CalledProcessError),
                ):
                    PREPARE.initialize_environment(
                        directory, "lab-unit-hosted", values, "swedencentral"
                    )
                with (
                    patch.object(
                        PREPARE.subprocess,
                        "run",
                        return_value=CompletedProcess(["azd"], 0, "wrong-value", ""),
                    ),
                    self.assertRaisesRegex(ValueError, "readback"),
                ):
                    PREPARE.initialize_environment(
                        directory, "lab-unit-hosted", values, "swedencentral"
                    )
                (directory / ".azure").mkdir()
                with self.assertRaises(FileExistsError):
                    PREPARE.initialize_environment(
                        directory, "lab-unit-hosted", values, "swedencentral"
                    )
