import json
import os
import unittest
from contextlib import ExitStack
from dataclasses import replace
from unittest.mock import patch

import httpx
from agent_framework import Agent
from azure.ai.projects import AIProjectClient as SyncProjectClient
from azure.ai.projects.aio import AIProjectClient
from azure.core.credentials import AccessToken

from foundry_workshop.hosted import HostedBinding, HostedTransport
from foundry_workshop.profiles import RuntimeProfile, runtime_contract
from foundry_workshop.runtime import inference_client
from foundry_workshop.search import embed_texts

from .test_sdk_contracts import ROOT, response_body, settings


class AsyncCredential:
    def __init__(self):
        self.scopes = []

    async def get_token(self, *scopes, **_kwargs):
        self.scopes.extend(scopes)
        return AccessToken("unit-test-not-a-real-token", 4102444800)

    async def close(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        await self.close()


class InferenceModeTests(unittest.IsolatedAsyncioTestCase):
    async def test_explicit_account_embeddings_use_correct_sdk_route(self):
        from .test_sdk_contracts import DummyCredential

        captured = []
        config = replace(settings(), openai_endpoint="https://unit.openai.azure.com")
        original = SyncProjectClient.get_openai_client

        def handle(request):
            captured.append(request)
            return httpx.Response(
                200,
                json={
                    "object": "list",
                    "model": "unit-embedding-model",
                    "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2, 0.3]}],
                    "usage": {"prompt_tokens": 3, "total_tokens": 3},
                },
            )

        with ExitStack() as stack:
            http = stack.enter_context(httpx.Client(transport=httpx.MockTransport(handle)))

            def owned_client(project, **kwargs):
                kwargs["http_client"] = http
                kwargs["max_retries"] = 0
                return original(project, **kwargs)

            stack.enter_context(
                patch("foundry_workshop.cloud.credential_for", return_value=DummyCredential())
            )
            stack.enter_context(patch.object(SyncProjectClient, "get_openai_client", owned_client))
            vectors, metadata = embed_texts(
                config,
                ["synthetic unit text"],
                {
                    "api": "account-embeddings",
                    "deployment": "unit-embedding",
                    "dimensions": 3,
                    "endpoint": config.openai_endpoint,
                    "field": "content_vector",
                },
            )
        self.assertEqual(captured[0].url.path, "/openai/v1/embeddings")
        self.assertEqual(captured[0].url.host, "unit.openai.azure.com")
        self.assertEqual(vectors, [[0.1, 0.2, 0.3]])
        self.assertEqual(metadata["observed_model"], "unit-embedding-model")

    async def test_hosted_transport_preserves_api_version_when_adding_session(self):
        captured = []
        binding = HostedBinding(
            "lab-unit",
            "1",
            "https://unit.services.ai.azure.com/api/projects/workshop/agents/lab-unit/endpoint/protocols/invocations?api-version=v1",
        )

        def handle(request):
            captured.append(request)
            return httpx.Response(200, json={"unit_test_only": True})

        with httpx.Client(transport=httpx.MockTransport(handle)) as client:
            transport = HostedTransport(settings(), binding)
            transport.http = client
            transport.session_id = "unit-session"
            transport._token_provider = lambda: "unit-test-not-a-real-token"
            result, raw = transport.invoke({"question": "unit"})
        self.assertEqual(
            dict(captured[0].url.params), {"api-version": "v1", "agent_session_id": "unit-session"}
        )
        self.assertTrue(result["unit_test_only"])
        self.assertEqual(raw["status_code"], 200)

    async def test_both_explicit_apis_use_real_sdk_paths_and_correct_audiences(self):
        for api in ("project-responses", "account-chat"):
            with (
                self.subTest(api=api),
                patch.dict(os.environ, {"OTEL_SDK_DISABLED": "true"}, clear=True),
            ):
                captured = []
                credential = AsyncCredential()
                config = replace(settings(), openai_endpoint="https://unit.openai.azure.com")
                original = AIProjectClient.get_openai_client

                def handle(request, _captured=captured, _api=api):
                    _captured.append((request.url, json.loads(request.content)))
                    if _api == "project-responses":
                        return httpx.Response(200, json=response_body("unit answer"))
                    return httpx.Response(
                        200,
                        json={
                            "id": "chatcmpl-unit",
                            "object": "chat.completion",
                            "created": 1789257600,
                            "model": "unit-model",
                            "choices": [
                                {
                                    "index": 0,
                                    "finish_reason": "stop",
                                    "message": {"role": "assistant", "content": "unit answer"},
                                }
                            ],
                            "usage": {
                                "prompt_tokens": 10,
                                "completion_tokens": 20,
                                "total_tokens": 30,
                            },
                        },
                    )

                def owned_client(project, _original=original, _handle=handle, **kwargs):
                    kwargs["http_client"] = httpx.AsyncClient(
                        transport=httpx.MockTransport(_handle)
                    )
                    kwargs["max_retries"] = 0
                    return _original(project, **kwargs)

                with patch("foundry_workshop.runtime.credential_for", return_value=credential):
                    with patch.object(AIProjectClient, "get_openai_client", owned_client):
                        async with inference_client(config, RuntimeProfile(api=api)) as client:
                            result = await Agent(client=client, instructions="unit only").run(
                                "unit question"
                            )
                self.assertEqual(result.text, "unit answer")
                self.assertEqual(len(captured), 1)
                expected = (
                    "/api/projects/workshop/openai/v1/responses"
                    if api == "project-responses"
                    else "/openai/v1/chat/completions"
                )
                self.assertEqual(captured[0][0].path, expected)
                self.assertEqual(captured[0][1]["model"], config.deployment)
                scope = (
                    "https://ai.azure.com/.default"
                    if api == "project-responses"
                    else "https://cognitiveservices.azure.com/.default"
                )
                self.assertIn(scope, credential.scopes)

    async def test_account_endpoint_mismatch_fails_before_credentials_or_network(self):
        with patch.dict(os.environ, {}, clear=True):
            config = replace(settings(), openai_endpoint="https://other.openai.azure.com")
            profile = RuntimeProfile(api="account-chat", protocol="invocations")
            with self.assertRaises(ValueError):
                runtime_contract(ROOT, config, profile)
            with patch("foundry_workshop.runtime.credential_for") as credential:
                with self.assertRaises(ValueError):
                    async with inference_client(config, profile):
                        self.fail("A mismatched account must not be called.")
                credential.assert_not_called()
