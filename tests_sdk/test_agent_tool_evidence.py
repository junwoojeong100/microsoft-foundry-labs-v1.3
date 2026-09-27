import json
import unittest
from contextlib import nullcontext
from unittest.mock import patch

import httpx
from agent_framework.openai import OpenAIChatClient
from openai import AsyncOpenAI

from foundry_workshop.agents import run_agent
from foundry_workshop.settings import Settings
from tests import workspace
from tests_sdk.test_sdk_contracts import response_body


class AgentToolEvidenceTests(unittest.IsolatedAsyncioTestCase):
    async def run_with_transport(self, *, invoke_tool):
        requests = []
        answer = json.dumps(
            {
                "answer": "The synthetic lodging limit is KRW 150000.",
                "decision": "answer",
                "limit_krw": 150000,
                "citations": ["TRAVEL-2026"],
            }
        )

        def handler(request):
            requests.append(json.loads(request.content))
            payload = response_body(answer, len(requests))
            if invoke_tool and len(requests) == 1:
                payload["output"] = [
                    {
                        "type": "function_call",
                        "id": "fc_policy",
                        "call_id": "call_policy",
                        "name": "lookup_policy",
                        "arguments": json.dumps({"query": "2026년 9월 국내 출장 숙박비"}),
                        "status": "completed",
                    }
                ]
            return httpx.Response(200, json=payload)

        settings = Settings(
            project_endpoint="https://unit.services.ai.azure.com/api/projects/workshop",
            deployment="unit-model",
            tenant_id=None,
            auth_mode="managed-identity",
            managed_identity_client_id=None,
            max_output_tokens=32768,
        )
        with workspace() as root:
            async with AsyncOpenAI(
                api_key="unit-test-not-a-real-key",
                base_url="https://unit.invalid/v1",
                http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
                max_retries=0,
            ) as client:
                with (
                    patch(
                        "foundry_workshop.agents.credential_for",
                        return_value=nullcontext(object()),
                    ),
                    patch(
                        "agent_framework.foundry.FoundryChatClient",
                        return_value=OpenAIChatClient(model=settings.deployment, async_client=client),
                    ),
                ):
                    result = await run_agent(
                        settings,
                        root,
                        "2026년 9월 국내 출장 숙박비",
                        tools=True,
                        mcp=False,
                    )
        return result, requests

    async def test_actual_function_execution_and_result_are_preserved(self):
        result, requests = await self.run_with_transport(invoke_tool=True)
        self.assertEqual(len(requests), 2)
        self.assertTrue(result["tool_execution_verified"])
        self.assertEqual(result["tool_calls"][0]["name"], "lookup_policy")
        self.assertTrue(result["tool_calls"][0]["completed"])
        self.assertIn("TRAVEL-2026", result["tool_calls"][0]["result_text"])

    async def test_fluent_answer_without_a_tool_call_is_not_execution_evidence(self):
        with self.assertRaisesRegex(ValueError, "not actually invoked"):
            await self.run_with_transport(invoke_tool=False)
