import asyncio
import importlib.util
import json
import os
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

import httpx
import httpx2
from agent_framework.openai import OpenAIChatClient
from azure.ai.projects import AIProjectClient
from azure.core.pipeline.transport import HttpTransport
from openai import AsyncOpenAI, OpenAI

from .test_sdk_contracts import ROOT, DummyCredential, response_body
from .test_toolbox_transport import Reply

RECIPES = ROOT / "examples/recipes"


def recipe(name):
    spec = importlib.util.spec_from_file_location(f"recipe_{name}", RECIPES / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sync_openai(handler):
    return OpenAI(
        api_key="unit-test-not-a-real-key",
        base_url="https://unit.invalid/v1",
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
        max_retries=0,
    )


class AgentVersionTransport(HttpTransport):
    def __init__(self):
        self.bodies = []

    def open(self):
        return self

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def send(self, request, **_kwargs):
        body = json.loads(request.body)
        self.bodies.append((request.method, urlsplit(request.url).path, body))
        name = urlsplit(request.url).path.split("/")[-2]
        return Reply(request, 200, {"name": name, "version": "7", "id": f"{name}:7", **body})


class ModelRecipeTests(unittest.TestCase):
    def test_responses_recipe_returns_service_ids_without_storing(self):
        requests = []

        def handle(request):
            requests.append(json.loads(request.content))
            return httpx2.Response(
                200, json=response_body("Foundry is a platform."), headers={"x-request-id": "req-1"}
            )

        with sync_openai(handle) as client:
            result = recipe("02_responses").ask(client, "unit-deployment", "What is Foundry?")
        self.assertEqual(result["response_id"], "resp_unit_1")
        self.assertEqual(result["request_id"], "req-1")
        self.assertEqual(result["response_model"], "unit-model")
        self.assertEqual(requests[0]["model"], "unit-deployment")
        self.assertIs(requests[0]["store"], False)

    def test_responses_recipe_stops_on_incomplete_output(self):
        def handle(_request):
            body = response_body("")
            body["status"] = "incomplete"
            return httpx2.Response(200, json=body)

        with sync_openai(handle) as client, self.assertRaises(SystemExit):
            recipe("02_responses").ask(client, "unit-deployment", "What is Foundry?")

    def test_prompt_agent_recipe_creates_a_prompt_version_and_pins_it(self):
        module = recipe("03_prompt_agent")
        transport = AgentVersionTransport()
        with AIProjectClient(
            endpoint="https://unit.services.ai.azure.com/api/projects/unit",
            credential=DummyCredential(),
            transport=transport,
        ) as project:
            agent = module.create_agent(project, "lab-unit-policy-sdk", "unit-deployment")
        method, path, body = transport.bodies[0]
        self.assertEqual(
            (method, path.split("/")[-3:]), ("POST", ["agents", "lab-unit-policy-sdk", "versions"])
        )
        self.assertEqual(body["definition"]["kind"], "prompt")
        self.assertEqual(body["definition"]["model"], "unit-deployment")
        self.assertIn("TRAVEL-2026", body["definition"]["instructions"])
        requests = []

        def handle(request):
            requests.append(json.loads(request.content))
            return httpx2.Response(200, json=response_body("KRW 150000 (TRAVEL-2026)."))

        with sync_openai(handle) as client:
            result = module.invoke(client, agent.name, agent.version, "Lodging limit?")
        self.assertEqual(result["version"], "7")
        self.assertEqual(
            requests[0]["agent_reference"],
            {"type": "agent_reference", "name": "lab-unit-policy-sdk", "version": "7"},
        )
        self.assertIs(requests[0]["store"], False)

    def test_prompt_agent_recipe_refuses_to_create_without_confirmation_or_prefix(self):
        module = recipe("03_prompt_agent")
        environment = {"WORKSHOP_PREFIX": "lab-unit", "AZURE_AI_PROJECT_ENDPOINT": "https://x"}
        for argv in (
            ["03_prompt_agent.py", "--name", "lab-unit-policy"],
            ["03_prompt_agent.py", "--name", "other-policy", "--confirm-create"],
        ):
            with (
                self.subTest(argv=argv),
                patch.dict(os.environ, environment, clear=True),
                patch("sys.argv", argv),
                patch.object(module, "load_dotenv"),
                patch.object(module, "AIProjectClient") as client,
                self.assertRaises(SystemExit),
            ):
                module.main()
            client.assert_not_called()


class FrameworkRecipeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        environment = patch.dict(os.environ, {"OTEL_SDK_DISABLED": "true"}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        self.requests = []

    def chat_client(self, handler):
        client = AsyncOpenAI(
            api_key="unit-test-not-a-real-key",
            base_url="https://unit.invalid/v1",
            http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
            max_retries=0,
        )
        self.addAsyncCleanup(client.close)
        return OpenAIChatClient(model="unit-deployment", async_client=client)

    async def test_tool_recipe_calls_the_read_only_policy_tool_before_answering(self):
        def handle(request):
            body = json.loads(request.content)
            self.requests.append(body)
            result = response_body("KRW 150000; approval first (TRAVEL-2026, APPROVAL-01).", 2)
            if len(self.requests) == 1:
                result["output"] = [
                    {
                        "type": "function_call",
                        "id": "fc_unit",
                        "call_id": "call_unit",
                        "name": body["tools"][0]["name"],
                        "arguments": json.dumps({"query": "hotel approval lodging"}),
                        "status": "completed",
                    }
                ]
            return httpx2.Response(200, json=result)

        module = recipe("04_maf_tool")
        async with module.build_agent(self.chat_client(handle)) as agent:
            result = await agent.run("Can I book a KRW 170000 hotel?")
        self.assertIn("TRAVEL-2026", result.text)
        self.assertEqual(len(self.requests), 2)
        tool_output = json.dumps(self.requests[1]["input"], ensure_ascii=False)
        self.assertIn("APPROVAL-01", tool_output)
        self.assertEqual(json.loads(module.lookup_policy.func("zzzz qqqq")), [])

    async def test_sequential_recipe_runs_both_agents_and_returns_outputs(self):
        def handle(request):
            self.requests.append(json.loads(request.content))
            return httpx2.Response(
                200,
                json=response_body(f"step {len(self.requests)} TRAVEL-2026", len(self.requests)),
            )

        module = recipe("05_maf_sequential")
        task = module.task_for("Hotel?")
        self.assertEqual(json.loads(task)["question"], "Hotel?")
        outputs = await module.run(module.build_workflow(self.chat_client(handle)), task)
        self.assertEqual(len(self.requests), 2)
        self.assertIn("TRAVEL-2026", json.dumps(self.requests[0]["input"], ensure_ascii=False))
        self.assertTrue(outputs)

    async def test_hosted_recipe_serves_the_responses_protocol(self):
        def handle(request):
            self.requests.append(json.loads(request.content))
            return httpx2.Response(200, json=response_body("Synthetic guidance (TRAVEL-2026)."))

        server = recipe("08_hosted_agent").build_server(self.chat_client(handle))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=server), base_url="http://testserver"
        ) as client:
            readiness = await client.get("/readiness")
            self.assertEqual(readiness.json(), {"status": "healthy"})
            response = await client.post(
                "/responses", json={"input": "Lodging limit?", "stream": False, "store": False}
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(self.requests), 1)
        self.assertIn("TRAVEL-2026", self.requests[0]["instructions"])


class RetrievalRecipeTests(unittest.TestCase):
    def test_iq_recipe_uses_the_ga_contract_and_raises_on_errors(self):
        seen = []

        def handle(request):
            seen.append(request)
            if "missing" in str(request.url):
                return httpx.Response(404, json={"error": {"message": "not found"}})
            return httpx.Response(
                200,
                json={
                    "references": [{"docKey": "TRAVEL-2026"}],
                    "activity": [{"type": "searchIndex"}],
                },
            )

        module = recipe("06_iq_retrieve")
        with httpx.Client(transport=httpx.MockTransport(handle)) as http:
            result = module.retrieve(
                http,
                "https://unit.search.windows.net",
                "lab-unit-kb",
                "lab-unit-source",
                "t",
                "Q",
            )
            with self.assertRaises(httpx.HTTPStatusError):
                module.retrieve(http, "https://unit.search.windows.net", "missing", "s", "t", "Q")
        self.assertEqual(result, {"references": ["TRAVEL-2026"], "activity": ["searchIndex"]})
        first = seen[0]
        self.assertEqual(first.url.params["api-version"], "2026-04-01")
        self.assertEqual(first.url.path, "/knowledgebases('lab-unit-kb')/retrieve")
        body = json.loads(first.content)
        self.assertEqual(body["knowledgeSourceParams"][0]["knowledgeSourceName"], "lab-unit-source")
        self.assertEqual(first.headers["authorization"], "Bearer t")


if __name__ == "__main__":
    asyncio.run(unittest.main())
