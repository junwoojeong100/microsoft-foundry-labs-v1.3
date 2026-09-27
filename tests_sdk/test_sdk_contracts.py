import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from azure.ai.projects import AIProjectClient
from azure.core.credentials import AccessToken
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

from foundry_workshop.agents import build_policy_agent, run_agent, run_workflow
from foundry_workshop.cloud import answer_with_context, invoke_prompt_agent, response_with_payload
from foundry_workshop.contracts import load_documents
from foundry_workshop.knowledge import evidence
from foundry_workshop.settings import Settings, credential_for

ROOT = Path(__file__).resolve().parents[1]


class DummyCredential:
    def get_token(self, *_scopes, **_kwargs):
        return AccessToken("unit-test-not-a-real-token", 4102444800)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def settings():
    return Settings(
        project_endpoint="https://unit.services.ai.azure.com/api/projects/workshop",
        deployment="unit-deployment",
        tenant_id="00000000-0000-0000-0000-000000000001",
        auth_mode="cli",
        managed_identity_client_id=None,
        max_output_tokens=2048,
    )


def response_body(text, number=1):
    return {
        "id": f"resp_unit_{number}",
        "object": "response",
        "created_at": 1789257600,
        "status": "completed",
        "model": "unit-model",
        "parallel_tool_calls": False,
        "tool_choice": "auto",
        "tools": [],
        "output": [
            {
                "type": "message",
                "id": f"msg_unit_{number}",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": text, "annotations": []}],
            }
        ],
        "usage": {
            "input_tokens": 10,
            "output_tokens": 20,
            "total_tokens": 30,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens_details": {"reasoning_tokens": 0},
        },
    }


class ProjectSDKTests(unittest.TestCase):
    def test_raw_response_path_preserves_unknown_foundry_fields_without_reserialization(self):
        raw = response_body("Unit response")
        raw["foundry_extension"] = {"preserve": "exactly"}
        raw["output"].insert(
            0,
            {
                "type": "openapi_call",
                "id": "call-unit",
                "call_id": "call-unit",
                "status": "completed",
                "arguments": "{}",
            },
        )
        with httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(200, json=raw))
        ) as http:
            with AIProjectClient(
                endpoint=settings().project_endpoint, credential=DummyCredential()
            ) as project:
                with project.get_openai_client(http_client=http, max_retries=0) as client:
                    parsed, original = response_with_payload(
                        client, model="unit", input="Synthetic unit question"
                    )
        self.assertEqual(original, raw)
        self.assertEqual(parsed.output_text, "Unit response")

    def test_cli_auth_pins_subscription_without_changing_defaults(self):
        subscription = "00000000-0000-0000-0000-000000000002"
        with patch.dict(os.environ, {"AZURE_SUBSCRIPTION_ID": subscription}):
            with patch("foundry_workshop.settings.subprocess.run") as profile:
                profile.return_value.stdout = settings().tenant_id + "\n"
                with patch("azure.identity.AzureCliCredential") as credential:
                    credential_for(settings())
        credential.assert_called_once_with(subscription=subscription, process_timeout=30)
        self.assertIn("--subscription", profile.call_args.args[0])
        self.assertNotIn("set", profile.call_args.args[0])

    def test_cli_auth_rejects_a_different_tenant_before_getting_a_token(self):
        with patch.dict(
            os.environ, {"AZURE_SUBSCRIPTION_ID": "00000000-0000-0000-0000-000000000002"}
        ):
            with patch("foundry_workshop.settings.subprocess.run") as profile:
                profile.return_value.stdout = "00000000-0000-0000-0000-000000000099\n"
                with patch("azure.identity.AzureCliCredential") as credential:
                    with self.assertRaises(ValueError):
                        credential_for(settings())
        credential.assert_not_called()

    def test_real_sdk_serializes_structured_model_and_pinned_agent_requests(self):
        captured = []
        answer = json.dumps(
            {
                "answer": "Unit-test synthetic answer.",
                "decision": "answer",
                "limit_krw": 150000,
                "citations": ["TRAVEL-2026"],
            }
        )

        def handle(request):
            captured.append((request.url.path, json.loads(request.content)))
            return httpx.Response(
                200, json=response_body(answer), headers={"x-request-id": "unit-request"}
            )

        with httpx.Client(transport=httpx.MockTransport(handle)) as http:
            with AIProjectClient(
                endpoint=settings().project_endpoint, credential=DummyCredential()
            ) as project:
                with project.get_openai_client(http_client=http, max_retries=0) as client:
                    result = answer_with_context(
                        client,
                        settings(),
                        ROOT,
                        "질문",
                        "v2",
                        evidence(load_documents(ROOT), "unit-test"),
                    )
                    invoked = invoke_prompt_agent(client, "lab-unit-agent", "7", "질문")
        self.assertEqual(result["usage"], {"input_tokens": 10, "output_tokens": 20})
        self.assertEqual(result["request_id"], "unit-request")
        self.assertEqual(captured[0][0], "/api/projects/workshop/openai/v1/responses")
        self.assertTrue(captured[0][1]["text"]["format"]["strict"])
        self.assertEqual(captured[1][1]["agent_reference"]["version"], "7")
        self.assertNotIn("agent", captured[1][1])
        self.assertEqual(invoked["agent_version"], "7")


class AgentSDKTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.http_clients = []
        self.captured = []
        self.env_patch = patch.dict(os.environ, {"OTEL_SDK_DISABLED": "true"})
        self.env_patch.start()

    async def asyncTearDown(self):
        for client in self.http_clients:
            await client.close()
        self.env_patch.stop()

    def fake_provider(self, **kwargs):
        from agent_framework.openai import OpenAIChatClient

        def handle(request):
            self.captured.append(json.loads(request.content))
            return httpx.Response(
                200,
                json=response_body(
                    f"Unit-test workflow output {len(self.captured)}", len(self.captured)
                ),
            )

        client = AsyncOpenAI(
            api_key="unit-test-not-a-real-key",
            base_url="https://unit.invalid/v1",
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)),
            max_retries=0,
        )
        self.http_clients.append(client)
        return OpenAIChatClient(model=kwargs["model"], async_client=client)

    async def test_single_agent_uses_installed_framework_without_azure(self):
        with patch("agent_framework.foundry.FoundryChatClient", side_effect=self.fake_provider):
            with patch("foundry_workshop.agents.credential_for", return_value=DummyCredential()):
                result = await run_agent(settings(), ROOT, "개념 설명", tools=False, mcp=False)
        self.assertIn("Unit-test", result["text"])
        self.assertEqual(len(self.captured), 1)

    async def test_three_real_workflow_builders_have_bounded_outputs(self):
        for pattern in ("sequential", "concurrent", "group-chat"):
            self.captured.clear()
            with self.subTest(pattern=pattern):
                with patch(
                    "agent_framework.foundry.FoundryChatClient", side_effect=self.fake_provider
                ):
                    with patch(
                        "foundry_workshop.agents.credential_for", return_value=DummyCredential()
                    ):
                        result = await run_workflow(
                            settings(), ROOT, "2026년 국내 출장 숙박비", pattern
                        )
                self.assertTrue(result["outputs"])
                self.assertTrue(
                    any("Unit-test workflow output" in output for output in result["outputs"])
                )
                self.assertLessEqual(len(self.captured), 3)
                self.assertFalse(result["external_actions_performed"])
                self.assertEqual(result["approval_status"], "pending-human-review")

    async def test_actual_local_mcp_handshake_and_tool(self):
        parameters = StdioServerParameters(
            command=sys.executable, args=[str(ROOT / "examples/mcp_server.py")]
        )
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                self.assertIn("lookup_policy", [tool.name for tool in tools.tools])
                result = await session.call_tool(
                    "lookup_policy", {"query": "2026년 국내 출장 숙박비"}
                )
                self.assertFalse(result.isError)
                payload = json.loads(result.content[0].text)
                self.assertIn("TRAVEL-2026", payload["source_ids"])
                self.assertEqual(payload["provider"], "local-keyword")

    async def test_real_hosting_adapter_exposes_readiness_without_model_call(self):
        from agent_framework_foundry_hosting import ResponsesHostServer

        with patch("agent_framework.foundry.FoundryChatClient", side_effect=self.fake_provider):
            agent = build_policy_agent(settings(), ROOT, DummyCredential())
        server = ResponsesHostServer(agent)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=server), base_url="http://testserver"
        ) as client:
            response = await client.get("/readiness")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})
        self.assertEqual(self.captured, [])


if __name__ == "__main__":
    unittest.main()
