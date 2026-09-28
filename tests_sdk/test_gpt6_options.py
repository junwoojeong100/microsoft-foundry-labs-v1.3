import json
import os
import unittest
from dataclasses import replace
from unittest.mock import patch

import httpx
from agent_framework import Agent, Message, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework.openai import OpenAIChatClient, OpenAIChatCompletionClient
from azure.ai.projects.models import PromptAgentDefinition
from openai import AsyncOpenAI, OpenAI

from foundry_workshop.benchmark import compare_matrices
from foundry_workshop.generation import agent_options, maf_options, response_options
from foundry_workshop.model_plan import (
    DEFAULT_MAX_OUTPUT_TOKENS,
    MODEL_ROLES,
    PRIMARY_MODEL,
    PRIMARY_VERSION,
    GenerationConfig,
)
from foundry_workshop.settings import Settings
from tests import workspace
from tests_sdk.test_sdk_contracts import DummyCredential, response_body


class GenerationTests(unittest.IsolatedAsyncioTestCase):
    def settings(self):
        return Settings(
            project_endpoint="https://unit.services.ai.azure.com/api/projects/workshop",
            deployment="workshop-chat",
            tenant_id="00000000-0000-0000-0000-000000000001",
            auth_mode="cli",
            managed_identity_client_id=None,
            max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
            reasoning_effort="low",
        )

    def test_model_roles_and_defaults_are_explicit(self):
        self.assertEqual(PRIMARY_MODEL, "gpt-6-sol")
        self.assertEqual(PRIMARY_VERSION, "2026-09-22")
        self.assertNotEqual(
            MODEL_ROLES["judge"]["deployment"], MODEL_ROLES["comparison"]["deployment"]
        )
        self.assertEqual(MODEL_ROLES["comparison"]["model"], "gpt-6-luna")
        self.assertEqual(MODEL_ROLES["judge"]["model"], "gpt-5.5")
        self.assertNotEqual(MODEL_ROLES["judge"]["model"], PRIMARY_MODEL)
        with patch.dict(os.environ, {}, clear=True):
            generation = GenerationConfig.from_env()
        self.assertEqual(generation.max_output_tokens, 32768)
        self.assertEqual(generation.reasoning_effort, "low")
        for values in (
            {"WORKSHOP_MAX_OUTPUT_TOKENS": "32769"},
            {"WORKSHOP_MAX_OUTPUT_TOKENS": "0"},
            {"WORKSHOP_REASONING_EFFORT": "minimal"},
            {"WORKSHOP_REASONING_EFFORT": ""},
        ):
            with (
                self.subTest(values=values),
                patch.dict(os.environ, values, clear=True),
                self.assertRaises(ValueError),
            ):
                GenerationConfig.from_env()

    def test_real_responses_sdk_receives_cap_and_effort(self):
        captured = []

        def handler(request):
            captured.append(json.loads(request.content))
            return httpx.Response(200, json=response_body("Synthetic answer"))

        with OpenAI(
            api_key="unit-test-not-a-real-key",
            base_url="https://unit.invalid/v1",
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
            max_retries=0,
        ) as client:
            response = client.responses.create(
                model="workshop-chat",
                input="Synthetic question",
                **response_options(self.settings()),
            )
        self.assertTrue(response.output_text)
        self.assertEqual(captured[0]["max_output_tokens"], 32768)
        self.assertEqual(captured[0]["reasoning"], {"effort": "low"})

    async def test_foundry_stateless_tool_options_keep_encrypted_reasoning(self):
        client = FoundryChatClient(
            project_endpoint=self.settings().project_endpoint,
            model=self.settings().deployment,
            credential=DummyCredential(),
        )
        with patch("httpx.AsyncClient.send", side_effect=AssertionError("No network expected")):
            options = await client._prepare_options(
                [Message("user", ["Synthetic question"])], maf_options(self.settings())
            )
        self.assertEqual(options["reasoning"], {"effort": "low"})
        self.assertEqual(options["max_output_tokens"], 32768)
        self.assertIn("reasoning.encrypted_content", options["include"])
        self.assertFalse(options["store"])

    async def test_chat_completion_uses_its_own_parameter_names(self):
        async with AsyncOpenAI(api_key="unit-test-not-a-real-key") as openai:
            client = OpenAIChatCompletionClient(model="workshop-chat", async_client=openai)
            with patch("httpx.AsyncClient.send", side_effect=AssertionError("No network expected")):
                options = client._prepare_options(
                    [Message("user", ["Synthetic question"])],
                    maf_options(self.settings(), api="account-chat"),
                )
        self.assertEqual(options["reasoning_effort"], "low")
        self.assertEqual(options["max_completion_tokens"], 32768)
        self.assertNotIn("reasoning", options)
        self.assertNotIn("include", options)

    async def test_stateless_function_round_trip_replays_reasoning_and_tool_output(self):
        requests = []

        @tool
        def policy_limit() -> str:
            """Return a synthetic policy value without external actions."""
            return "150000"

        def handler(request):
            body = json.loads(request.content)
            requests.append(body)
            payload = response_body("Synthetic final answer", len(requests))
            if len(requests) == 1:
                payload["output"] = [
                    {
                        "type": "reasoning",
                        "id": "rs_unit",
                        "summary": [],
                        "encrypted_content": "opaque-unit-fixture",
                    },
                    {
                        "type": "function_call",
                        "id": "fc_unit",
                        "call_id": "call_unit",
                        "name": "policy_limit",
                        "arguments": "{}",
                        "status": "completed",
                    },
                ]
            return httpx.Response(200, json=payload)

        async with AsyncOpenAI(
            api_key="unit-test-not-a-real-key",
            base_url="https://unit.invalid/v1",
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
            max_retries=0,
        ) as client:
            agent = Agent(
                client=OpenAIChatClient(model="workshop-chat", async_client=client),
                tools=[policy_limit],
                default_options=maf_options(self.settings()),
            )
            result = await agent.run("Synthetic policy question")
        self.assertIn("Synthetic final answer", result.text)
        self.assertEqual(len(requests), 2)
        replayed = requests[1]["input"]
        self.assertTrue(
            any(
                item.get("type") == "reasoning"
                and item.get("encrypted_content") == "opaque-unit-fixture"
                for item in replayed
            )
        )
        self.assertTrue(
            any(
                item.get("type") == "function_call_output" and item.get("call_id") == "call_unit"
                for item in replayed
            )
        )

    def test_prompt_agent_serialization_and_explicit_legacy_compatibility(self):
        definition = PromptAgentDefinition(
            model="workshop-chat",
            instructions="Synthetic",
            **agent_options(self.settings()),
        ).as_dict()
        self.assertEqual(definition["reasoning"], {"effort": "low"})
        legacy = replace(self.settings(), reasoning_effort=None, max_output_tokens=2048)
        self.assertEqual(response_options(legacy), {"max_output_tokens": 2048})
        self.assertEqual(agent_options(legacy), {})
        self.assertEqual(maf_options(legacy), {"store": False, "max_tokens": 2048})

    def test_matrix_comparison_rejects_reasoning_drift(self):
        contract = {
            "profile": {"language": "ko"},
            "models": {},
            "project_endpoint": "unit",
            "inference_endpoint": "unit",
            "max_output_tokens": 32768,
            "reasoning_effort": "low",
            "code_hash": "same",
            "retrieval_configuration": {},
        }
        baseline = {
            "split": "dev",
            "dataset_hash": "same",
            "corpus_hash": "same",
            "model_keys": [],
            "concurrency": 1,
            "rubric_hash": "same",
            "runtime_contract": contract,
        }
        candidate = {**baseline, "runtime_contract": {**contract, "reasoning_effort": "high"}}
        with (
            workspace() as root,
            patch(
                "foundry_workshop.benchmark.load_matrix",
                side_effect=[(baseline, [], []), (candidate, [], [])],
            ),
            patch("foundry_workshop.benchmark.summarize_matrix", return_value={"models": {}}),
            self.assertRaisesRegex(ValueError, "reasoning_effort"),
        ):
            compare_matrices(root, "before", "after")
