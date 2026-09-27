import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
import httpx2
from agent_framework.exceptions import AgentFrameworkException
from agent_framework.openai import OpenAIChatClient
from openai import AsyncOpenAI

from foundry_workshop import toolbox
from foundry_workshop.contracts import digest, load_documents, read_json
from tests import workspace
from tests.test_toolbox import ENVIRONMENT, seed_ledger, settings

from .test_sdk_contracts import DummyCredential, response_body


class ToolboxAgentTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        environment = patch.dict(
            os.environ, {**ENVIRONMENT, "OTEL_SDK_DISABLED": "true"}, clear=True
        )
        environment.start()
        self.addCleanup(environment.stop)
        self.mcp_requests = []
        self.model_requests = []
        self.tool_error = False
        self.clients = []
        test = self
        self.real_async_client = httpx.AsyncClient

        class RecordingMCPClient(self.real_async_client):
            # A real subclass keeps isinstance checks valid while the MCP transport is stubbed.
            def __init__(self, *args, **kwargs):
                kwargs["transport"] = httpx.MockTransport(test.mcp_response)
                super().__init__(*args, **kwargs)
                test.clients.append(self)

        self.recording_mcp_client = RecordingMCPClient
        # openai 3.x uses httpx2; the MCP client in the pinned MAF/mcp stack still uses httpx.
        self.model_client = AsyncOpenAI(
            api_key="unit-test-not-a-real-key",
            base_url="https://unit.invalid/v1",
            http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(self.model_response)),
            max_retries=0,
        )

    async def asyncTearDown(self):
        await self.model_client.close()
        for client in self.clients:
            await client.aclose()

    def model_response(self, request):
        body = json.loads(request.content)
        self.model_requests.append(body)
        result = response_body(
            "Synthetic policy requires prior approval. TRAVEL-2026, APPROVAL-01.",
            len(self.model_requests),
        )
        if len(self.model_requests) == 1:
            result["output"] = [
                {
                    "type": "function_call",
                    "id": "fc_unit",
                    "call_id": "call_unit",
                    "name": body["tools"][0]["name"],
                    "arguments": json.dumps(
                        {"query": "Synthetic lodging policy for September 2026"}
                    ),
                    "status": "completed",
                }
            ]
        return httpx2.Response(200, json=result)

    def mcp_response(self, request):
        if request.method in {"GET", "DELETE"}:
            return httpx.Response(405)
        body = json.loads(request.content)
        self.mcp_requests.append(body)
        method = body["method"]
        if method.startswith("notifications/"):
            return httpx.Response(202)
        response = {"jsonrpc": "2.0", "id": body["id"]}
        if method == "initialize":
            response["result"] = {
                "protocolVersion": body["params"]["protocolVersion"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "unit-toolbox", "version": "1"},
            }
        elif method == "tools/list":
            response["result"] = {
                "tools": [
                    {
                        "name": "policy_search",
                        "description": "Search the unit-test synthetic policy corpus.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
                            "required": ["query"],
                        },
                    }
                ]
            }
        elif method == "tools/call":
            content = (
                {"error": "Explicit unit-tool failure"}
                if self.tool_error
                else {"documents": load_documents(self.root, "en")}
            )
            response["result"] = {
                "content": [{"type": "text", "text": json.dumps(content)}],
                "structuredContent": content,
                "isError": self.tool_error,
            }
        else:
            response["error"] = {"code": -32601, "message": "Method not found"}
        return httpx.Response(200, json=response)

    def binding(self):
        definition = {"name": toolbox.name_for(settings()), "version": "1", **toolbox.definition()}
        return {
            "definition": definition,
            "definition_hash": digest(definition),
            "selected_version": "1",
            "connection": {"id": "unit-connection-id"},
            "endpoint": toolbox.endpoint(settings(), toolbox.name_for(settings()), "1"),
            "skill_ref": None,
        }

    async def execute(self, root, *, invoke, query_only=False, evidence_root=None, packaged=False):
        self.root = root
        seed_ledger(root)
        with (
            patch("httpx.AsyncClient", self.recording_mcp_client),
            patch("foundry_workshop.toolbox.credential_for", return_value=DummyCredential()),
            patch(
                "agent_framework.foundry.FoundryChatClient",
                return_value=OpenAIChatClient(model="unit-target", async_client=self.model_client),
            ),
        ):
            return await toolbox.execute(
                settings(),
                root,
                self.binding(),
                "unit",
                invoke=invoke,
                confirmed=invoke or query_only,
                query_only=query_only,
                evidence_root=evidence_root,
                packaged_source={
                    "kind": "packaged-synthetic-index",
                    "language": "en",
                    "search_endpoint": "https://unit.search.windows.net",
                    "index": "lab-unit-policies",
                    "prefix": "lab-unit",
                    "corpus_hash": digest(load_documents(root, "en")),
                }
                if packaged
                else None,
            )

    async def test_real_mcp_discovery_does_not_call_a_model(self):
        with workspace() as root:
            result = await self.execute(root, invoke=False)
            self.assertEqual(result["tools"], ["policy_search"])
            self.assertFalse(result["model_invoked"])
            self.assertFalse(result["tool_invoked"])
            self.assertTrue((root / "outputs/toolbox-runs/unit/tool-list.json").exists())
        self.assertEqual(self.model_requests, [])
        self.assertIn("initialize", [item["method"] for item in self.mcp_requests])
        self.assertNotIn("tools/call", [item["method"] for item in self.mcp_requests])

    async def test_real_framework_calls_mcp_and_preserves_actual_sdk_metadata(self):
        with workspace() as root:
            result = await self.execute(root, invoke=True)
            self.assertTrue(result["model_invoked"])
            self.assertTrue(result["tool_invoked"])
            self.assertEqual(len(result["model_calls"]), 2)
            self.assertEqual(result["function_calls"][0]["name"], "policy_search")
            path = root / "outputs/toolbox-runs/unit"
            self.assertFalse(read_json(path / "tool-results.json")[0]["isError"])
            self.assertTrue((path / "response.json").exists())
        self.assertEqual(sum(item["method"] == "tools/call" for item in self.mcp_requests), 1)

    async def test_direct_tool_query_proves_downstream_access_without_a_model(self):
        with workspace() as root:
            result = await self.execute(root, invoke=False, query_only=True)
            self.assertTrue(result["tool_invoked"])
            self.assertFalse(result["model_invoked"])
            self.assertEqual(result["mode"], "live-toolbox-query")
        self.assertEqual(self.model_requests, [])
        self.assertEqual(sum(item["method"] == "tools/call" for item in self.mcp_requests), 1)

    async def test_packaged_source_writes_only_to_explicit_session_evidence_root(self):
        with workspace() as root, tempfile.TemporaryDirectory() as folder:
            evidence = Path(folder) / "session-evidence"
            result = await self.execute(
                root, invoke=False, query_only=True, evidence_root=evidence, packaged=True
            )
            self.assertEqual(result["output_directory"], str(evidence / "unit"))
            self.assertTrue((evidence / "unit/tool-results.json").is_file())
            self.assertFalse((root / "outputs/toolbox-runs").exists())

    async def test_a_tool_error_cannot_be_hidden_by_a_fluent_model_answer(self):
        self.tool_error = True
        with workspace() as root:
            with self.assertRaises((ValueError, AgentFrameworkException, ExceptionGroup)):
                await self.execute(root, invoke=True)
            path = root / "outputs/toolbox-runs/unit"
            self.assertTrue(read_json(path / "tool-results.json")[0]["isError"])
            self.assertFalse((path / "summary.json").exists())
