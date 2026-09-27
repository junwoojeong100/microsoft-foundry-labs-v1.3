import asyncio
import json
import os
import unittest
from contextlib import asynccontextmanager
from dataclasses import replace
from unittest.mock import patch

import httpx
from agent_framework.openai import OpenAIChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from openai import AsyncOpenAI

from foundry_workshop.contracts import parse_json
from foundry_workshop.hosted import create_invocations_app
from foundry_workshop.profiles import RuntimeProfile
from foundry_workshop.runtime import build_workflow_agent, run_pipeline

from .test_sdk_contracts import ROOT, response_body, settings


class WorkflowHostingTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.requests = []
        self.patches = patch.dict(os.environ, {"OTEL_SDK_DISABLED": "true"}, clear=True)
        self.patches.start()
        self.client_patch = patch("foundry_workshop.runtime.inference_client", self.client)
        self.client_patch.start()

    async def asyncTearDown(self):
        self.client_patch.stop()
        self.patches.stop()

    @asynccontextmanager
    async def client(self, config, profile):
        def handle(request):
            self.requests.append(json.loads(request.content))
            answer = {
                "answer": "합성 한도는 150000원이며 예약 전 사람의 승인이 필요합니다.",
                "decision": "needs_approval",
                "limit_krw": 150000,
                "citations": ["TRAVEL-2026", "APPROVAL-01"],
            }
            if config.language == "en":
                answer["answer"] = (
                    "The synthetic limit is KRW 150000; human approval is required before booking."
                )
            return httpx.Response(
                200, json=response_body(json.dumps(answer, ensure_ascii=False), len(self.requests))
            )

        async with AsyncOpenAI(
            api_key="unit-test-not-a-real-key",
            base_url="https://unit.invalid/v1",
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)),
            max_retries=0,
        ) as client:
            yield OpenAIChatClient(model=config.deployment, async_client=client)

    async def test_all_three_workflows_return_real_service_lineage_and_bounded_calls(self):
        for pattern, expected in (("sequential", 3), ("concurrent", 4), ("group-chat", 4)):
            self.requests.clear()
            with self.subTest(pattern=pattern):
                profile = RuntimeProfile(kind="workflow", pattern=pattern)
                agent = build_workflow_agent(settings(), ROOT, profile)
                response = await agent.run("2026년 9월 국내 출장 호텔 170000원 사전 승인")
                payload = parse_json(response.text)
                self.assertEqual(len(self.requests), expected)
                self.assertEqual(len(payload["model_calls"]), expected)
                self.assertEqual(payload["response_id"], f"resp_unit_{expected}")
                self.assertEqual(payload["response_model"], "unit-model")
                self.assertEqual(payload["usage"]["input_tokens"], 10 * expected)
                self.assertEqual(payload["answer"]["decision"], "needs_approval")
                self.assertIsNone(payload["trace_id"])
                self.assertFalse(payload["external_actions_performed"])
                self.assertEqual(payload["approval_status"], "pending-human-review")
                for request in self.requests:
                    serialized = json.dumps(request)
                    for forbidden in (
                        "expected_decision",
                        "expected_limit_krw",
                        "required_citations",
                        "ground_truth",
                    ):
                        self.assertNotIn(forbidden, serialized)

    async def test_english_invocations_use_english_prompts_and_corpus(self):
        config = replace(settings(), language="en")
        profile = RuntimeProfile(kind="workflow", protocol="invocations", language="en")
        app = create_invocations_app(config, ROOT, profile)
        request = {
            "question": "A domestic hotel in September 2026 costs KRW 170000. Is advance approval needed?",
            "model_key": "primary",
            "case_id": "D03",
            "run_id": "unit-english",
        }
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.post("/invocations", json=request)
        self.assertEqual(response.status_code, 200, response.text)
        value = response.json()
        self.assertEqual(value["runtime_contract"]["profile"]["language"], "en")
        self.assertEqual(len(self.requests), 3)
        self.assertIn("KRW 150000", value["answer"]["answer"])
        import re

        self.assertIsNone(re.search("[가-힣]", json.dumps(self.requests, ensure_ascii=False)))
        self.assertIsNone(re.search("[가-힣]", json.dumps(value["documents"], ensure_ascii=False)))

    async def test_concurrent_requests_keep_question_and_model_call_state_separate(self):
        profile = RuntimeProfile(kind="workflow")
        questions = [
            "alpha 2026년 9월 국내 출장 숙박비 170000원",
            "beta 2026년 9월 국내 출장 숙박비 170000원",
        ]
        results = await asyncio.gather(
            *[run_pipeline(settings(), ROOT, question, profile) for question in questions]
        )
        self.assertEqual([result["question"] for result in results], questions)
        ids = [{call["response_id"] for call in result["model_calls"]} for result in results]
        self.assertEqual([len(value) for value in ids], [3, 3])
        self.assertFalse(ids[0] & ids[1])

    async def test_real_responses_host_runs_the_workflow_without_azure(self):
        for language, question in (
            (
                "en",
                "A domestic hotel in September 2026 costs KRW 170000. Is advance approval needed?",
            ),
            ("ko", "2026년 9월 국내 출장 호텔 170000원 사전 승인"),
        ):
            with self.subTest(language=language):
                self.requests.clear()
                profile = RuntimeProfile(kind="workflow", language=language)
                server = ResponsesHostServer(
                    build_workflow_agent(
                        replace(settings(), language=language),
                        ROOT,
                        profile,
                    )
                )
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=server), base_url="http://testserver"
                ) as client:
                    readiness = await client.get("/readiness")
                    self.assertEqual(readiness.json(), {"status": "healthy"})
                    response = await client.post(
                        "/responses",
                        json={"input": question, "stream": False, "store": False},
                    )
                self.assertEqual(response.status_code, 200, response.text)
                outputs = response.json()["output"]
                text = "".join(
                    content["text"]
                    for item in outputs
                    for content in item.get("content", [])
                    if content["type"] == "output_text"
                )
                payload = parse_json(text)
                self.assertEqual(payload["mode"], "live")
                self.assertEqual(payload["runtime_profile"]["kind"], "workflow")
                self.assertEqual(payload["runtime_profile"]["pattern"], "sequential")
                self.assertEqual(payload["runtime_profile"], profile.to_dict())
                self.assertEqual(payload["answer"]["decision"], "needs_approval")
                self.assertEqual(payload["approval_status"], "pending-human-review")
                self.assertIs(payload["external_actions_performed"], False)
                self.assertNotIn("pattern", payload)
                self.assertNotIn("outputs", payload)
                self.assertEqual(len(self.requests), 3)

    async def test_real_invocations_host_rejects_gold_labels_and_preserves_contract(self):
        profile = RuntimeProfile(kind="workflow", protocol="invocations")
        app = create_invocations_app(settings(), ROOT, profile)
        request = {
            "question": "2026년 9월 국내 출장 호텔 170000원 사전 승인",
            "model_key": "primary",
            "case_id": "D03",
            "run_id": "unit-run",
        }
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            bad = await client.post("/invocations", json={**request, "expected_limit_krw": 150000})
            self.assertEqual(bad.status_code, 400, bad.text)
            self.assertEqual(self.requests, [])
            response = await client.post("/invocations", json=request)
        self.assertEqual(response.status_code, 200, response.text)
        value = response.json()
        self.assertEqual(value["case_id"], "D03")
        self.assertEqual(value["runtime_contract"]["profile"], profile.to_dict())
        self.assertEqual(value["response_model"], "unit-model")
