import asyncio
import copy
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from foundry_workshop import toolbox
from foundry_workshop.cli import parser
from foundry_workshop.contracts import digest, load_documents, write_json
from foundry_workshop.settings import Settings

from . import workspace


def settings(language="en"):
    return Settings(
        "https://unit.services.ai.azure.com/api/projects/workshop",
        "gpt-6-sol",
        "00000000-0000-0000-0000-000000000001",
        "cli",
        None,
        2048,
        language=language,
    )


ENVIRONMENT = {
    "WORKSHOP_PREFIX": "lab-unit",
    "AZURE_SEARCH_ENDPOINT": "https://unit.search.windows.net",
    "TOOLBOX_SEARCH_CONNECTION_NAME": "lab-unit-search",
}


def seed_ledger(root, language="en"):
    write_json(
        root / "outputs/azure-objects.json",
        {
            "scope": {
                "search_endpoint": ENVIRONMENT["AZURE_SEARCH_ENDPOINT"],
                "prefix": "lab-unit",
            },
            "corpus_hash": digest(load_documents(root, language)),
            "objects": [{"path": "indexes/lab-unit-policies", "api_version": "2024-07-01"}],
        },
    )


class ToolboxTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, ENVIRONMENT, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def test_local_plan_uses_only_the_synthetic_index_and_no_credentials(self):
        with patch("foundry_workshop.toolbox.credential_for") as credential:
            plan = toolbox.plan(settings())
        credential.assert_not_called()
        self.assertFalse(plan["azure_requests_sent"])
        self.assertEqual(plan["toolbox_name"], "lab-unit-tools-en")
        self.assertEqual(toolbox.name_for(settings("ko")), "lab-unit-tools-ko")
        self.assertEqual(plan["definition"]["tools"][0]["name"], "policy_search")
        self.assertNotIn("microsoft.com/api/mcp", str(plan))
        self.assertEqual(
            plan["definition"]["tools"][0]["azure_ai_search"]["indexes"][0]["top_k"], 6
        )

    def test_names_and_versions_cannot_redirect_outside_the_owned_project(self):
        for name in ("other-team-tools", "../tools", "lab-unit/name", "https://example.test"):
            with patch.dict(os.environ, {"TOOLBOX_NAME": name}), self.assertRaises(ValueError):
                toolbox.name_for(settings())
        for version in (None, "", "latest", "default", "../1", "1?redirect=x"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                toolbox.version_value(version)
        self.assertEqual(
            toolbox.endpoint(settings(), "lab-unit-tools-en", "2"),
            "https://unit.services.ai.azure.com/api/projects/workshop/toolboxes/lab-unit-tools-en/versions/2/mcp?api-version=v1",
        )

    def test_definition_rejects_unknown_tools_connections_indexes_and_skills(self):
        original = toolbox.definition()
        toolbox.validate_definition(original)
        toolbox.validate_definition(toolbox.definition(discovery=True))
        for field, value in (
            ("index_name", "company-documents"),
            ("project_connection_id", "another-connection"),
            ("project_connection_id", None),
            ("query_type", "semantic"),
            ("top_k", 100),
            ("filter", "id eq 'other'"),
        ):
            changed = copy.deepcopy(original)
            changed["tools"][0]["azure_ai_search"]["indexes"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                toolbox.validate_definition(changed)
        for changed in (
            {"tools": []},
            {"tools": [*original["tools"], {"type": "web_search"}]},
            {**original, "skills": [{"name": "unreviewed-skill"}]},
        ):
            with self.assertRaises(ValueError):
                toolbox.validate_definition(changed)

    def test_skill_references_are_owned_language_specific_and_version_pinned(self):
        value = toolbox.definition(discovery=True, skill_version="3", language="en")
        toolbox.validate_definition(value, allowed_skill_name=toolbox.skill_name(settings()))
        with self.assertRaisesRegex(ValueError, "unapproved skill"):
            toolbox.validate_definition(
                value, allowed_skill_name=toolbox.skill_name(settings("ko"))
            )
        value["skills"][0]["version"] = "latest"
        with self.assertRaisesRegex(ValueError, "immutable"):
            toolbox.validate_definition(value, allowed_skill_name=toolbox.skill_name(settings()))
        with self.assertRaises(ValueError):
            toolbox.validate_definition({**toolbox.definition(), "skills": False})
        pinned = toolbox.definition(discovery=True, pin_policy=True)
        toolbox.validate_definition(pinned)
        self.assertTrue(pinned["tools"][0]["tool_configs"]["policy_search"]["pin"])
        with self.assertRaisesRegex(ValueError, "discovery"):
            toolbox.definition(pin_policy=True)

    def test_seed_ownership_requires_the_exact_language_corpus_and_index(self):
        with workspace() as root:
            with self.assertRaises(ValueError):
                toolbox.require_synthetic_index(root, settings())
            seed_ledger(root)
            toolbox.require_synthetic_index(root, settings())
            with self.assertRaises(ValueError):
                toolbox.require_synthetic_index(root, settings("ko"))
            with patch.dict(os.environ, {"AZURE_SEARCH_INDEX_NAME": "lab-unit-other"}):
                with self.assertRaises(ValueError):
                    toolbox.require_synthetic_index(root, settings())

    def test_connection_checks_metadata_only_and_requires_keyless_authentication(self):
        project = MagicMock()
        connection = SimpleNamespace(
            name="lab-unit-search",
            id="unit-connection-id",
            type="CognitiveSearch",
            target="https://unit.search.windows.net/",
            credentials=SimpleNamespace(type="AAD"),
        )
        project.connections.get.return_value = connection
        result = toolbox.connection_scope(project)
        self.assertEqual(result["authentication"], "AAD")
        project.connections.get.assert_called_once_with(
            name="lab-unit-search", include_credentials=False
        )
        connection.credentials.type = "ProjectManagedIdentity"
        self.assertEqual(
            toolbox.connection_scope(project)["authentication"], "ProjectManagedIdentity"
        )
        connection.credentials.type = "ApiKey"
        with self.assertRaisesRegex(ValueError, "keyless"):
            toolbox.connection_scope(project)

    def test_every_side_effect_requires_its_own_explicit_gate(self):
        project = MagicMock()
        with workspace() as root:
            with self.assertRaisesRegex(ValueError, "confirm-create"):
                toolbox.create_version(project, root, settings(), confirmed=False)
            with self.assertRaisesRegex(ValueError, "confirm-update"):
                toolbox.select_version(project, root, settings(), "2", confirmed=False)
            with self.assertRaisesRegex(ValueError, "confirm-delete"):
                toolbox.delete_owned(project, root, settings(), confirmed=False)
            with self.assertRaisesRegex(ValueError, "confirm-cost"):
                asyncio.run(
                    toolbox.execute(settings(), root, {}, "unit", invoke=True, confirmed=False)
                )
        self.assertEqual(project.mock_calls, [])

    def test_default_selection_refuses_unowned_versions_and_detects_drift(self):
        project = MagicMock()
        with workspace() as root:
            write_json(
                toolbox.ledger_file(root, settings()),
                {
                    "project_endpoint": settings().project_endpoint,
                    "toolbox_name": toolbox.name_for(settings()),
                    "versions": {"1": {}, "2": {}},
                },
            )
            with self.assertRaisesRegex(ValueError, "Only a version"):
                toolbox.select_version(project, root, settings(), "3", confirmed=True)
            with patch(
                "foundry_workshop.toolbox.snapshot", return_value={"selected_version": "other"}
            ):
                with self.assertRaisesRegex(ValueError, "Another owner"):
                    toolbox.select_version(project, root, settings(), "2", confirmed=True)
            project.toolboxes.update.assert_not_called()
            project.toolboxes.list_versions.return_value = [SimpleNamespace(version="3")]
            with self.assertRaisesRegex(ValueError, "remote versions differ"):
                toolbox.delete_owned(project, root, settings(), confirmed=True)
            project.toolboxes.delete.assert_not_called()

    def test_cli_keeps_version_pinning_and_opt_in_flags(self):
        args = parser().parse_args(
            ["--language", "en", "toolbox", "ask", "--version", "2", "--label", "unit"]
        )
        self.assertFalse(args.confirm_cost)
        self.assertEqual(args.version, "2")
        self.assertFalse(parser().parse_args(["toolbox", "create"]).confirm_create)
        self.assertFalse(
            parser().parse_args(["toolbox", "select", "--version", "2"]).confirm_update
        )
