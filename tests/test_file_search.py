import os
import unittest
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
from azure.core.exceptions import ResourceNotFoundError
from openai import NotFoundError
from openai.types.responses import Response

from foundry_workshop import file_search_lab
from foundry_workshop.cloud import load_agent_reference
from foundry_workshop.contracts import read_json
from foundry_workshop.settings import Settings
from tests import workspace
from tests_sdk.test_sdk_contracts import response_body


class FileSearchTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = self.stack.enter_context(workspace())
        self.stack.enter_context(
            patch.dict(os.environ, {"WORKSHOP_PREFIX": "lab-unit"}, clear=True)
        )
        self.settings = Settings(
            "https://unit.services.ai.azure.com/api/projects/workshop",
            "workshop-chat",
            "00000000-0000-0000-0000-000000000001",
            "cli",
            None,
            32768,
            reasoning_effort="low",
        )
        self.name = file_search_lab.agent_name(self.settings, None)
        self.project, self.client = MagicMock(), MagicMock()
        self.project.agents.get.side_effect = ResourceNotFoundError("Unit not found")
        self.project.agents.create_version.return_value = SimpleNamespace(version="3")
        self.client.vector_stores.create.return_value = SimpleNamespace(id="vs_unit")
        self.client.files.create.side_effect = [SimpleNamespace(id=f"file_{i}") for i in range(6)]
        self.not_found = NotFoundError(
            "unit file not linked",
            response=httpx.Response(404, request=httpx.Request("GET", "https://unit.invalid")),
            body={"error": "unit"},
        )
        self.client.vector_stores.files.retrieve.side_effect = self.not_found
        self.client.vector_stores.files.create.return_value = SimpleNamespace(status="completed")

    def create(self):
        return file_search_lab.create(
            self.project, self.client, self.root, self.settings, self.name, confirmed=True
        )

    def raw_response(self, citation="file_0"):
        raw = response_body("Synthetic File Search answer")
        raw["usage"]["input_tokens_details"]["cache_write_tokens"] = 0
        raw["output"][0]["content"][0]["annotations"] = [
            {
                "type": "file_citation",
                "file_id": citation,
                "filename": "TRAVEL-2025.txt",
                "index": 0,
            }
        ]
        raw["output"].insert(
            0,
            {
                "type": "file_search_call",
                "id": "fs_unit",
                "status": "completed",
                "queries": ["synthetic policy"],
                "results": [],
            },
        )
        return raw

    def test_create_requires_consent_and_uploads_only_six_policies(self):
        with self.assertRaisesRegex(ValueError, "confirm-create"):
            file_search_lab.create(
                self.project, self.client, self.root, self.settings, self.name, confirmed=False
            )
        self.project.agents.get.assert_not_called()
        result = self.create()
        self.assertEqual(result["indexed_files"], 6)
        self.assertFalse(result["agent_invoked"])
        self.assertEqual(self.client.files.create.call_count, 6)
        self.client.vector_stores.create.assert_called_once_with(
            name=self.name + "-knowledge",
            expires_after={"anchor": "last_active_at", "days": 7},
        )
        definition = self.project.agents.create_version.call_args.kwargs["definition"].as_dict()
        self.assertEqual(definition["tools"][0]["type"], "file_search")
        self.assertEqual(definition["tools"][0]["vector_store_ids"], ["vs_unit"])
        self.assertEqual(definition["reasoning"], {"effort": "low"})
        self.assertNotIn("150000", definition["instructions"])
        self.assertEqual(
            load_agent_reference(self.root, self.settings, self.name)["agent_version"], "3"
        )
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.create()
        self.project.agents.create_version.assert_called_once()

    def test_partial_upload_is_resumed_without_duplicate_file(self):
        self.client.vector_stores.files.create.return_value = SimpleNamespace(status="failed")
        with self.assertRaisesRegex(ValueError, "Indexing failed"):
            self.create()
        state = file_search_lab.load_owned(self.root, self.settings, self.name)
        self.assertEqual(len(state["files"]), 1)
        self.assertIsNone(state["agent_version"])
        self.client.vector_stores.files.create.return_value = SimpleNamespace(status="completed")
        self.create()
        self.assertEqual(self.client.files.create.call_count, 6)
        self.client.vector_stores.create.assert_called_once()

    def test_retained_store_has_no_automatic_expiry(self):
        result = file_search_lab.create(
            self.project,
            self.client,
            self.root,
            self.settings,
            self.name,
            confirmed=True,
            retain=True,
        )
        self.client.vector_stores.create.assert_called_once_with(name=self.name + "-knowledge")
        self.assertEqual(result["retention"], "retain")
        state = file_search_lab.load_owned(self.root, self.settings, self.name)
        self.assertEqual(state["retention"], "retain")

    def test_partial_run_cannot_silently_change_retention(self):
        self.client.vector_stores.files.create.return_value = SimpleNamespace(status="failed")
        with self.assertRaisesRegex(ValueError, "Indexing failed"):
            self.create()
        with self.assertRaisesRegex(ValueError, "original retention"):
            file_search_lab.create(
                self.project,
                self.client,
                self.root,
                self.settings,
                self.name,
                confirmed=True,
                retain=True,
            )
        self.client.vector_stores.create.assert_called_once()

    def test_ask_pins_version_and_requires_owned_search_citations(self):
        self.create()
        raw = self.raw_response()
        response = Response.model_validate(raw)
        with patch.object(
            file_search_lab, "response_with_payload", return_value=(response, raw)
        ) as request:
            result = file_search_lab.ask(
                self.client, self.root, self.settings, self.name, "합성 질문", "first"
            )
        self.assertTrue(result["file_search_verified"])
        self.assertEqual(request.call_args.kwargs["max_output_tokens"], 32768)
        self.assertNotIn("reasoning", request.call_args.kwargs)
        self.assertEqual(request.call_args.kwargs["extra_body"]["agent_reference"]["version"], "3")
        self.assertEqual(request.call_args.kwargs["include"], ["file_search_call.results"])
        self.assertTrue((Path(result["result_directory"]) / "response.json").is_file())
        with self.assertRaises(FileExistsError):
            file_search_lab.ask(
                self.client, self.root, self.settings, self.name, "합성 질문", "first"
            )

    def test_wrong_file_citation_preserves_raw_failure_not_success(self):
        self.create()
        raw = self.raw_response(citation="file_not_owned")
        with patch.object(
            file_search_lab,
            "response_with_payload",
            return_value=(Response.model_validate(raw), raw),
        ):
            with self.assertRaisesRegex(ValueError, "Original result preserved"):
                file_search_lab.ask(
                    self.client, self.root, self.settings, self.name, "합성 질문", "wrong"
                )
        directory = self.root / "outputs/file-search" / self.name / "runs/wrong"
        self.assertTrue((directory / "response.json").is_file())
        self.assertTrue((directory / "failure.json").is_file())
        self.assertFalse((directory / "summary.json").exists())

    def test_missing_search_is_not_grounded_success(self):
        raw = self.raw_response()
        raw["output"] = raw["output"][1:]
        with self.assertRaisesRegex(ValueError, "File Search call"):
            file_search_lab.verify_search(raw, {"file_0"})

    def test_changed_model_configuration_is_rejected(self):
        self.create()
        with self.assertRaisesRegex(ValueError, "configuration changed"):
            file_search_lab.load_owned(
                self.root, replace(self.settings, reasoning_effort="high"), self.name
            )
        with self.assertRaises(ValueError):
            file_search_lab.agent_name(self.settings, "../outside")

    def test_cleanup_is_scoped_confirmed_and_marks_saved_reference_deleted(self):
        self.create()
        self.client.vector_stores.delete.return_value = SimpleNamespace(deleted=True)
        self.client.files.delete.return_value = SimpleNamespace(deleted=True)
        plan = file_search_lab.cleanup(
            self.project, self.client, self.root, self.settings, self.name, confirmed=False
        )
        self.assertFalse(plan["deletes_resources"])
        self.project.agents.delete_version.assert_not_called()
        file_search_lab.cleanup(
            self.project, self.client, self.root, self.settings, self.name, confirmed=True
        )
        self.project.agents.delete_version.assert_called_once_with(
            agent_name=self.name, agent_version="3"
        )
        self.assertEqual(self.client.files.delete.call_count, 6)
        state = read_json(file_search_lab.ledger_path(self.root, self.name))
        self.assertEqual(state["phase"], "deleted")
        with self.assertRaisesRegex(ValueError, "deleted"):
            load_agent_reference(self.root, self.settings, self.name)

    def test_unconfirmed_delete_keeps_remaining_ownership(self):
        self.create()
        self.client.vector_stores.delete.return_value = SimpleNamespace(deleted=False)
        with self.assertRaisesRegex(ValueError, "not confirmed"):
            file_search_lab.cleanup(
                self.project, self.client, self.root, self.settings, self.name, confirmed=True
            )
        state = read_json(file_search_lab.ledger_path(self.root, self.name))
        self.assertTrue(state["agent_deleted"])
        self.assertFalse(state["vector_store_deleted"])
        self.client.files.delete.assert_not_called()
