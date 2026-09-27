from __future__ import annotations

import json
import time
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, FunctionTool, PromptAgentDefinition
from azure.core.credentials import AccessToken
from azure.core.exceptions import ResourceNotFoundError

import workshop
from tests.helpers import IsolatedWorkshop, function_call, message, response_payload
from tools import TOOL_SCHEMA


class OfflineCredential:
    def get_token(self, *scopes, **kwargs):
        return AccessToken("offline-test-token", int(time.time()) + 3600)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class RuntimeTests(IsolatedWorkshop):
    def mock_http(self, payloads: list[dict], status_code: int = 200):
        requests = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(
                {"url": str(request.url), "body": json.loads(request.content)}
            )
            self.assertLessEqual(
                len(requests), len(payloads), "Unexpected extra request"
            )
            return httpx.Response(status_code, json=payloads[len(requests) - 1])

        transport = httpx.MockTransport(handler)
        credential = OfflineCredential()
        project = AIProjectClient(
            endpoint=self.settings.endpoint, credential=credential
        )
        original = project.get_openai_client

        def client(**kwargs):
            return original(http_client=httpx.Client(transport=transport), **kwargs)

        self.stack.enter_context(
            patch("azure.identity.AzureCliCredential", return_value=credential)
        )
        self.stack.enter_context(
            patch("azure.ai.projects.AIProjectClient", return_value=project)
        )
        self.stack.enter_context(
            patch.object(project, "get_openai_client", side_effect=client)
        )
        return requests

    def test_real_sdk_serializes_file_and_function_tools(self):
        definition = PromptAgentDefinition(
            model="workshop-chat",
            instructions="Offline contract",
            tools=[
                FileSearchTool(vector_store_ids=["vs_test"], max_num_results=5),
                FunctionTool(**TOOL_SCHEMA),
            ],
        ).as_dict()
        self.assertEqual(
            [tool["type"] for tool in definition["tools"]], ["file_search", "function"]
        )
        self.assertEqual(definition["tools"][1]["name"], "estimate_trip_cost")
        self.assertTrue(definition["tools"][1]["strict"])

    def test_real_sdk_function_round_trip_pins_version(self):
        requests = self.mock_http(
            [
                response_payload("resp_first", [function_call()]),
                response_payload(
                    "resp_last", [message("390000원, 지원 상한 추정입니다.")]
                ),
            ]
        )
        result = workshop.ask(self.settings, "서울 2박 3일 상한은?")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["agent_version"], "7")
        self.assertEqual(result["tool_calls"][0]["result"]["total"], 390000)
        self.assertEqual(result["citations"][0]["file_id"], "file_test")
        self.assertTrue(requests[0]["url"].endswith("/openai/v1/responses"))
        for request in requests:
            self.assertEqual(
                request["body"]["agent_reference"],
                {
                    "name": "trip-coach-test",
                    "version": "7",
                    "type": "agent_reference",
                },
            )
            self.assertEqual(request["body"]["include"], ["file_search_call.results"])
        followup = requests[1]["body"]
        self.assertEqual(followup["previous_response_id"], "resp_first")
        self.assertEqual(followup["input"][0]["type"], "function_call_output")
        self.assertEqual(followup["input"][0]["call_id"], "call_test")
        self.assertEqual(json.loads(followup["input"][0]["output"])["total"], 390000)
        self.assertEqual(
            workshop.read_state(self.settings).response_ids, ["resp_first", "resp_last"]
        )
        self.assertEqual(len(list((self.root / "outputs").glob("*.json"))), 1)

    def test_invalid_tool_output_is_explicit(self):
        requests = self.mock_http(
            [
                response_payload(
                    "resp_first", [function_call('{"city":"서울","nights":0}')]
                ),
                response_payload(
                    "resp_last", [message("숙박 수를 확인해 주세요.", citation=False)]
                ),
            ]
        )
        result = workshop.ask(self.settings, "0박")
        self.assertFalse(result["tool_calls"][0]["result"]["ok"])
        self.assertEqual(
            json.loads(requests[1]["body"]["input"][0]["output"])["error"]["code"],
            "invalid_tool_input",
        )

    def test_refuses_local_tools_in_rag_stage(self):
        self.state.versions[0]["stage"] = "rag"
        self.state.save()
        self.mock_http([response_payload("resp_first", [function_call()])])
        with self.assertRaisesRegex(workshop.WorkshopError, "함수 실행"):
            workshop.ask(self.settings, "서울 2박")
        record = json.loads(next((self.root / "outputs").glob("*.json")).read_text())
        self.assertEqual(record["status"], "error")
        self.assertEqual(record["tool_calls"], [])

    def test_incomplete_response_is_preserved_not_success(self):
        self.mock_http([response_payload("resp_short", [], status="incomplete")])
        with self.assertRaisesRegex(workshop.WorkshopError, "완료되지"):
            workshop.ask(self.settings, "정책 질문")
        record = json.loads(next((self.root / "outputs").glob("*.json")).read_text())
        self.assertEqual(record["status"], "error")
        self.assertEqual(record["responses"][0]["status"], "incomplete")
        self.assertIn("resp_short", workshop.read_state(self.settings).response_ids)

    def test_http_error_has_no_fallback(self):
        requests = self.mock_http(
            [{"error": {"message": "offline test not found", "type": "not_found"}}], 404
        )
        with self.assertRaises(workshop.WorkshopError):
            workshop.ask(self.settings, "정책 질문")
        self.assertEqual(len(requests), 1)
        record = json.loads(next((self.root / "outputs").glob("*.json")).read_text())
        self.assertEqual(record["status"], "error")
        self.assertIn("NotFoundError", record["error"])
        self.assertEqual(record["answer"], "")

    def test_tool_loop_is_bounded(self):
        requests = self.mock_http(
            [
                response_payload(f"resp_{i}", [function_call()])
                for i in range(workshop.MAX_TOOL_ROUNDS + 1)
            ]
        )
        with self.assertRaisesRegex(workshop.WorkshopError, "상한"):
            workshop.ask(self.settings, "계속 계산")
        self.assertEqual(len(requests), 4)
        record = json.loads(next((self.root / "outputs").glob("*.json")).read_text())
        self.assertEqual(record["status"], "error")
        self.assertEqual(len(record["tool_calls"]), 3)

    def test_model_call_is_not_an_agent_or_stored_conversation(self):
        requests = self.mock_http(
            [response_payload("resp_model", [message(citation=False)])]
        )
        result = workshop.ask_model(self.settings, "인사해 주세요.")
        self.assertTrue(result["answer"])
        self.assertFalse(requests[0]["body"]["store"])
        self.assertEqual(requests[0]["body"]["model"], "workshop-chat")
        self.assertNotIn("agent_reference", requests[0]["body"])

    def test_version_change_and_output_overwrite_fail_before_http(self):
        existing = self.root / "outputs/existing.json"
        workshop.write_json(existing, {"keep": True})
        with patch.object(workshop, "cloud_clients") as clients:
            with self.assertRaises(workshop.WorkshopError):
                workshop.ask(self.settings, "질문", expected_version="other")
            with self.assertRaises(workshop.WorkshopError):
                workshop.ask(self.settings, "질문", output_path=existing)
            clients.assert_not_called()
        self.assertEqual(json.loads(existing.read_text()), {"keep": True})

    def test_lock_blocks_overlap_and_releases_on_error(self):
        with workshop.exclusive_session():
            with self.assertRaisesRegex(workshop.WorkshopError, "실행 중"):
                with workshop.exclusive_session():
                    self.fail("Second session must not start")
        self.assertFalse((self.root / ".lab/session.lock").exists())
        with self.assertRaisesRegex(RuntimeError, "test error"):
            with workshop.exclusive_session():
                raise RuntimeError("test error")
        self.assertFalse((self.root / ".lab/session.lock").exists())

    def test_settings_and_state_guard_scope(self):
        self.settings.validate()
        for endpoint in (
            "http://x.ai.azure.com/api/projects/p",
            "https://x.openai.azure.com",
            "https://x.ai.azure.com/api/projects/p?key=x",
            "https://x.ai.azure.com:443/api/projects/p",
        ):
            with (
                self.subTest(endpoint=endpoint),
                self.assertRaises(workshop.WorkshopError),
            ):
                workshop.Settings(endpoint, "model", "trip-coach-test").validate()
        different = workshop.Settings(
            self.settings.endpoint, "another-model", self.settings.agent_name
        )
        with self.assertRaisesRegex(workshop.WorkshopError, ".env"):
            workshop.read_state(different)
        (self.root / "data/knowledge/01-travel-current.txt").write_text(
            "modified", encoding="utf-8"
        )
        with self.assertRaisesRegex(workshop.WorkshopError, "정책/요금"):
            workshop.read_state(self.settings)
        workshop.read_state(self.settings, check_knowledge=False)

    def test_cleanup_requires_exact_confirmation_and_preserves_other_assets(self):
        self.state.response_ids = ["resp_owned"]
        self.state.save()
        client, project = MagicMock(), MagicMock()
        for method in (
            client.responses.delete,
            client.vector_stores.delete,
            client.files.delete,
        ):
            method.return_value = SimpleNamespace(deleted=True)

        @contextmanager
        def clients(_):
            yield project, client

        with patch.object(workshop, "cloud_clients", side_effect=clients) as context:
            workshop.cleanup(self.settings, None)
            with self.assertRaises(workshop.WorkshopError):
                workshop.cleanup(self.settings, "someone-else")
            context.assert_not_called()
            result = workshop.cleanup(self.settings, self.settings.agent_name)
        self.assertEqual(result.files, {})
        self.assertEqual(result.versions, [])
        self.assertEqual(result.response_ids, [])
        project.agents.delete_version.assert_called_once_with(
            agent_name="trip-coach-test", agent_version="7"
        )
        project.agents.delete.assert_not_called()
        client.files.delete.assert_called_once_with("file_test")

    def test_unconfirmed_delete_preserves_ledger(self):
        self.state.response_ids = ["resp_owned"]
        self.state.save()
        client = MagicMock()
        client.responses.delete.return_value = SimpleNamespace(deleted=False)

        @contextmanager
        def clients(_):
            yield MagicMock(), client

        with patch.object(workshop, "cloud_clients", side_effect=clients):
            with self.assertRaisesRegex(workshop.WorkshopError, "삭제가 확인"):
                workshop.cleanup(self.settings, self.settings.agent_name)
        self.assertEqual(
            workshop.read_state(self.settings).response_ids, ["resp_owned"]
        )

    def test_create_reuses_knowledge_and_records_actual_version(self):
        project = MagicMock()
        project.agents.create_version.return_value = SimpleNamespace(version="9")

        @contextmanager
        def clients(_):
            yield project, MagicMock()

        with (
            patch.object(workshop, "cloud_clients", side_effect=clients),
            patch.object(workshop, "prepare_knowledge") as prepare,
        ):
            result = workshop.create_agent(self.settings, "tools", "improved")
        prepare.assert_called_once()
        self.assertEqual(result.selected_version, "9")
        self.assertEqual(result.vector_store_id, "vs_test")
        self.assertEqual(result.selected()["prompt"], "improved")
        definition = project.agents.create_version.call_args.kwargs[
            "definition"
        ].as_dict()
        self.assertEqual(
            [item["type"] for item in definition["tools"]], ["file_search", "function"]
        )

    def test_new_agent_never_overwrites_existing_remote_name(self):
        workshop.STATE_PATH.unlink()
        project = MagicMock()

        @contextmanager
        def clients(_):
            yield project, MagicMock()

        with patch.object(workshop, "cloud_clients", side_effect=clients):
            with self.assertRaisesRegex(workshop.WorkshopError, "이미 있습니다"):
                workshop.create_agent(self.settings, "rag", "baseline")
        project.agents.create_version.assert_not_called()
        self.assertFalse(workshop.STATE_PATH.exists())

    def test_new_agent_persists_partial_setup_before_remote_creation(self):
        workshop.STATE_PATH.unlink()
        project = MagicMock()
        project.agents.get.side_effect = ResourceNotFoundError("Not found")
        project.agents.create_version.return_value = SimpleNamespace(version="1")

        @contextmanager
        def clients(_):
            yield project, MagicMock()

        def fail_upload(*_):
            self.assertTrue(workshop.STATE_PATH.exists())
            raise workshop.WorkshopError("upload failed")

        with (
            patch.object(workshop, "cloud_clients", side_effect=clients),
            patch.object(workshop, "prepare_knowledge", side_effect=fail_upload),
        ):
            with self.assertRaisesRegex(workshop.WorkshopError, "upload failed"):
                workshop.create_agent(self.settings, "rag", "baseline")
        project.agents.create_version.assert_not_called()
        self.assertEqual(workshop.read_state(self.settings).versions, [])
