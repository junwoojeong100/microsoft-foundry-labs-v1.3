import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from tests import ROOT
from tests.test_ci_helpers import ENV, PREPARE
from tests.test_toolbox import settings


class CIManifestTests(unittest.TestCase):
    def test_offline_ci_uses_the_same_source_bound_verifier_without_azure_login(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/check.yml").read_text())
        steps = workflow["jobs"]["offline"]["steps"]
        commands = "\n".join(step.get("run", "") for step in steps)
        self.assertIn("python scripts/check_workshop.py", commands)
        self.assertIn("python -m unittest discover -s tests -t . -q", commands)
        self.assertIn("python -m unittest discover -s tests_sdk -t . -q", commands)
        self.assertFalse(any("azure/login" in step.get("uses", "") for step in steps))
        self.assertEqual(workflow["permissions"], {"contents": "read"})

    def test_release_deployment_is_isolated_from_the_historical_repository_project(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/hosted-lab-release.yml").read_text())
        job = workflow["jobs"]["release"]
        self.assertTrue(all("${{ runner." not in str(value) for value in job["env"].values()))
        steps = {step.get("name"): step.get("run", "") for step in job["steps"]}
        initialization = steps["Initialize only the existing-project code deployment"]
        self.assertIn('AZD_PROJECT_DIR="$RUNNER_TEMP/foundry-workshop-release"', initialization)
        self.assertIn('>> "$GITHUB_ENV"', initialization)
        self.assertIn("prepare_hosted_azd.py", initialization)
        self.assertIn('--directory "$AZD_PROJECT_DIR"', initialization)
        self.assertNotIn("azd ai agent init", initialization)
        for step in (
            "Deploy only the approved service",
            "Give only the owned runtime project access",
        ):
            self.assertIn('cd "$AZD_PROJECT_DIR"', steps[step])
            self.assertIn("$GITHUB_WORKSPACE/scripts/", steps[step])
        self.assertNotIn("azd provision", "\n".join(steps.values()))

    def test_sdk_checks_install_the_declared_development_dependencies(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/check.yml").read_text())
        commands = "\n".join(step.get("run", "") for step in workflow["jobs"]["offline"]["steps"])
        self.assertIn("pip install --quiet -r requirements.txt", commands)
        self.assertIn("-e .[hosted,dev]", (ROOT / "requirements.txt").read_text())

    def test_only_the_owned_agent_env_is_merged_into_the_existing_project(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, ENV, clear=True):
            path = Path(directory) / "azure.yaml"
            project = {"host": "azure.ai.project", "endpoint": settings().project_endpoint}
            manifest = {
                "name": "unit",
                "services": {
                    "existing-project": project,
                    "lab-unit-ci": {
                        "host": "azure.ai.agent",
                        "name": "lab-unit-ci",
                        "project": ".build/unit",
                        "uses": ["existing-project"],
                        "codeConfiguration": {"runtime": "python_3_13", "entryPoint": "main.py"},
                        "env": {"KEEP": "unchanged"},
                    },
                },
            }
            path.write_text(yaml.safe_dump(manifest))
            PREPARE.prepare(path, settings(), "lab-unit-ci")
            result = yaml.safe_load(path.read_text())
            self.assertEqual(result["services"]["existing-project"], project)
            self.assertEqual(result["services"]["lab-unit-ci"]["env"]["KEEP"], "unchanged")
            self.assertEqual(
                result["services"]["lab-unit-ci"]["env"]["WORKSHOP_AUTH_MODE"], "managed-identity"
            )
            self.assertEqual(result["services"]["lab-unit-ci"]["project"], ".build/unit")
            result["services"]["another-agent"] = {"host": "azure.ai.agent"}
            path.write_text(yaml.safe_dump(result))
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                PREPARE.prepare(path, settings(), "lab-unit-ci")
            self.assertEqual(path.read_bytes(), before)


class OptionalWorkflowTests(unittest.TestCase):
    def test_live_release_is_manual_and_cost_gated(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/hosted-lab-release.yml").read_text())
        triggers = workflow.get("on", workflow.get(True))
        self.assertEqual(set(triggers), {"workflow_dispatch"})
        job = workflow["jobs"]["release"]
        self.assertEqual(job["environment"], "foundry-workshop")
        commands = "\n".join(step.get("run", "") for step in job["steps"])
        self.assertIn('if [ "$ACKNOWLEDGE_COST" != "true" ]', commands)
        self.assertIn("doctor --cloud", commands)
        self.assertIn('azd deploy "$WORKSHOP_HOSTED_AGENT_NAME"', commands)
        self.assertNotIn("azd provision", commands)
        self.assertIn("benchmark stop-session", commands)

    def test_automatic_workflow_is_read_only_and_never_logs_in(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/check.yml").read_text())
        triggers = workflow.get("on", workflow.get(True))
        self.assertEqual(set(triggers), {"push", "pull_request", "workflow_dispatch"})
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        steps = workflow["jobs"]["offline"]["steps"]
        self.assertFalse(any("azure/login" in step.get("uses", "") for step in steps))
        commands = "\n".join(step.get("run", "") for step in steps)
        for forbidden in ("az login", "azd deploy", "azd provision", "--confirm-cost"):
            self.assertNotIn(forbidden, commands)
