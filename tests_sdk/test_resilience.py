"""Real SDK/file-store contracts; no network, paid model, or Hosted execution."""

import asyncio
import copy
import importlib
import json
import os
import tempfile
import unittest
from contextlib import AsyncExitStack, asynccontextmanager, suppress
from pathlib import Path
from unittest.mock import patch

import httpx
from azure.ai.agentserver.core.tasks import (
    TaskDeferred,
    resilient_tasks_enabled,
    set_resilient_tasks_enabled,
)
from azure.ai.agentserver.core.tasks._manager import get_task_manager

from foundry_workshop.resilience import MODEL_LABEL, STAGES, checkpoint_outputs, verify_completion
from tests import ROOT


class ResilienceSDKTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        from azure.ai.agentserver.core.streaming import streams
        from azure.ai.agentserver.core.tasks import _decorator

        cls.original_descriptors = list(_decorator._REGISTERED_DESCRIPTORS)
        cls.original_enabled = resilient_tasks_enabled()
        cls.original_registry = vars(streams).copy()
        cls.server = importlib.import_module("examples.resilient.server")

    @classmethod
    def tearDownClass(cls):
        from azure.ai.agentserver.core.streaming import streams
        from azure.ai.agentserver.core.tasks import _decorator

        _decorator._REGISTERED_DESCRIPTORS[:] = cls.original_descriptors
        vars(streams).clear()
        vars(streams).update(cls.original_registry)
        set_resilient_tasks_enabled(cls.original_enabled)

    async def asyncSetUp(self):
        directory = tempfile.TemporaryDirectory(prefix="workshop-resilience-sdk-")
        self.addCleanup(directory.cleanup)
        self.state_root = Path(directory.name)
        environment = patch.dict(
            os.environ,
            {
                "OTEL_SDK_DISABLED": "true",
                "AGENTSERVER_STATE_ROOT": directory.name,
                "FOUNDRY_AGENT_NAME": "workshop-resilience",
                "FOUNDRY_AGENT_SESSION_ID": "local-contract",
            },
            clear=True,
        )
        environment.start()
        self.addCleanup(environment.stop)
        network = patch("socket.socket.connect", side_effect=AssertionError("Network is forbidden"))
        network.start()
        self.addCleanup(network.stop)
        self.checkpoints = {}
        self.posts = []

    @asynccontextmanager
    async def host(self, **kwargs):
        from azure.ai.agentserver.core.streaming import streams

        # A fresh registry prevents memory from masquerading as restart-surviving storage.
        vars(streams).clear()
        vars(streams).update(vars(type(streams)()))
        callback = kwargs.pop("on_checkpoint", None)

        def record(response, recovered):
            self.checkpoints[response["id"]] = copy.deepcopy(response)
            if callback is not None:
                callback(response, recovered)

        app = self.server.create_app(ROOT, on_checkpoint=record, **kwargs)
        lifespan = AsyncExitStack()
        await lifespan.enter_async_context(app.router.lifespan_context(app))
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client:
                yield app, client
        finally:
            from azure.ai.agentserver.core.streaming._concrete import FileBackedReplayEventStream

            futures = [active.result_future for active in get_task_manager()._active_tasks.values()]
            app.request_shutdown()
            await lifespan.aclose()
            for future in futures:
                with suppress(TaskDeferred):
                    await future
            for post in self.posts:
                if not post.done():
                    post.cancel()
                with suppress(asyncio.CancelledError):
                    await post
            self.posts.clear()
            # SDK close() writes an EOF but retains its OS lock. Emulate process resource release,
            # without deleting or rewriting the persisted events used by the next host.
            for stream in streams._slots.values():
                if isinstance(stream, FileBackedReplayEventStream):
                    stream._cleanup_locks()

    async def poll(self, client, path, predicate, timeout=10):
        async with asyncio.timeout(timeout):
            while True:
                response = await client.get(path)
                if response.status_code == 200 and predicate(response.json()):
                    return response.json()
                if response.status_code == 200 and response.json().get("status") == "failed":
                    self.fail(f"SDK response failed before the required condition: {response.text}")
                self.assertIn(response.status_code, (200, 404), response.text)
                await asyncio.sleep(0.02)

    async def start(self, client):
        existing = set(self.checkpoints)
        post = asyncio.create_task(
            client.post(
                "/responses",
                json={
                    "model": MODEL_LABEL,
                    "input": "D03",
                    "store": True,
                    "background": True,
                    "stream": True,
                },
            )
        )
        self.posts.append(post)
        # ASGITransport buffers SSE; the SDK's backpressured checkpoint gives us its actual ID.
        async with asyncio.timeout(10):
            while not set(self.checkpoints) - existing:
                if post.done():
                    response = post.result()
                    self.fail(f"POST ended before its first checkpoint: {response.text}")
                await asyncio.sleep(0.02)
        rid = (set(self.checkpoints) - existing).pop()
        gate = await self.poll(client, f"/workshop/approvals/{rid}", lambda _: True)
        before = copy.deepcopy(self.checkpoints[rid])
        self.assertEqual(len(before["output"]), 1)
        return rid, gate, before

    def decision(self, gate, choice="approve", input_id="simulated-decision-one"):
        return {
            "gate_id": gate["gate_id"],
            "request_sha256": gate["request_sha256"],
            "if_last_input_id": gate["request_input_id"],
            "input_id": input_id,
            "decision": choice,
            "simulated": True,
        }

    async def finish(self, client, rid):
        return await self.poll(
            client,
            f"/responses/{rid}",
            lambda value: value["status"] in ("completed", "failed", "cancelled"),
        )

    async def test_real_chain_suspends_then_resumes_same_task_without_human_authorization(self):
        from examples.resilient.workshop import checkpoint_recorder
        from foundry_workshop.contracts import read_json

        evidence = self.state_root / "evidence"
        evidence.mkdir()
        async with self.host(
            stage_delay_seconds=0, on_checkpoint=checkpoint_recorder(evidence, None)
        ) as (_, client):
            rid, gate, before = await self.start(client)
            first = await get_task_manager().provider.get(gate["task_id"])
            self.assertEqual(first.status, "suspended")
            await asyncio.sleep(0.1)
            waiting = (await client.get(f"/responses/{rid}")).json()
            self.assertEqual(waiting["status"], "in_progress")
            self.assertEqual(len(waiting["output"]), 1)
            reply = await client.post(f"/workshop/approvals/{rid}", json=self.decision(gate))
            self.assertEqual(reply.status_code, 200, reply.text)
            resumed = reply.json()
            self.assertEqual(resumed["decision"]["entry_mode"], "resumed")
            second = await get_task_manager().provider.get(gate["task_id"])
            self.assertEqual((first.id, second.id), (gate["task_id"], gate["task_id"]))
            self.assertEqual(second.status, "suspended")
            final = await self.finish(client, rid)
            report = verify_completion(before, final, resumed)
            self.assertEqual(report["human_authorization"], "not-granted")
            self.assertEqual(len(report["final_output_ids"]), 3)
            self.assertTrue(list((self.state_root / "tasks").rglob("*.json")))
            self.assertTrue(list((self.state_root / "responses").rglob("*.json")))
            self.assertTrue(list((self.state_root / "state_stores").rglob("*.json")))
            saved = read_json(evidence / "checkpoint.json")["response"]
            self.assertEqual(saved["output"], final["output"])

    async def test_pending_gate_and_original_response_item_survive_host_lifetime_change(self):
        async with self.host(stage_delay_seconds=0.1) as (_, client):
            rid, gate, before = await self.start(client)
        recovered_checkpoints = []
        async with self.host(
            stage_delay_seconds=0,
            on_checkpoint=lambda response, recovered: recovered_checkpoints.append(recovered),
        ) as (_, client):
            persisted = await self.poll(client, f"/workshop/approvals/{rid}", lambda _: True)
            self.assertEqual(persisted, gate)
            waiting = (await client.get(f"/responses/{rid}")).json()
            self.assertEqual(waiting["output"], before["output"])
            self.assertEqual(persisted["status"], "awaiting_simulated_decision")
            reply = await client.post(f"/workshop/approvals/{rid}", json=self.decision(gate))
            self.assertEqual(reply.status_code, 200, reply.text)
            final = await self.finish(client, rid)
            verify_completion(before, final, reply.json())
            self.assertEqual(recovered_checkpoints, [True, True])

    async def test_recovery_skips_committed_stage_and_preserves_all_original_ids_and_payloads(self):
        committed = asyncio.Event()
        snapshots = []

        def checkpoint(response, recovered):
            snapshots.append(copy.deepcopy(response))
            if len(response["output"]) == 2:
                committed.set()

        async with self.host(stage_delay_seconds=0.3, on_checkpoint=checkpoint) as (_, client):
            rid, gate, _ = await self.start(client)
            reply = await client.post(f"/workshop/approvals/{rid}", json=self.decision(gate))
            self.assertEqual(reply.status_code, 200, reply.text)
            approved = reply.json()
            await asyncio.wait_for(committed.wait(), 10)
            before = snapshots[-1]
            self.assertEqual(len(before["output"]), 2)
        continued = []
        async with self.host(
            stage_delay_seconds=0,
            on_checkpoint=lambda response, recovered: continued.append(
                (copy.deepcopy(response), recovered)
            ),
        ) as (_, client):
            final = await self.finish(client, rid)
            report = verify_completion(before, final, approved)
            self.assertEqual(len(report["preserved_output_ids"]), 2)
            self.assertEqual(len(continued), 1)
            self.assertTrue(continued[0][1])
            stages = [json.loads(item["content"][0]["text"])["stage"] for item in final["output"]]
            self.assertEqual(tuple(stages), STAGES)
            async with asyncio.timeout(10):
                replay = await client.get(f"/responses/{rid}?stream=true")
            self.assertEqual(replay.status_code, 200, replay.text)
            events = [
                json.loads(line[6:])
                for line in replay.text.splitlines()
                if line.startswith("data: ") and line[6:] != "[DONE]"
            ]
            original_ids = {item["id"] for item in before["output"]}
            replayed_ids = {
                event["item"]["id"]
                for event in events
                if event["type"] == "response.output_item.done"
            }
            self.assertTrue(original_ids <= replayed_ids)
            # This SDK closes the local SSE log on graceful shutdown. JSON GET is the
            # recovery acceptance contract, not a claimed gapless cross-lifetime SSE tail.

    async def test_uninterrupted_sse_replay_preserves_the_completed_response(self):
        async with self.host(stage_delay_seconds=0) as (_, client):
            rid, gate, before = await self.start(client)
            reply = await client.post(f"/workshop/approvals/{rid}", json=self.decision(gate))
            self.assertEqual(reply.status_code, 200, reply.text)
            await self.finish(client, rid)
            async with asyncio.timeout(10):
                replay = await client.get(f"/responses/{rid}?stream=true")
            self.assertEqual(replay.status_code, 200, replay.text)
            events = [
                json.loads(line[6:])
                for line in replay.text.splitlines()
                if line.startswith("data: ") and line[6:] != "[DONE]"
            ]
            completed = [
                event["response"] for event in events if event["type"] == "response.completed"
            ]
            self.assertTrue(completed)
            verify_completion(before, completed[-1], reply.json())

    async def test_approval_turn_recovers_a_committed_receipt_without_recording_it_twice(self):
        committed = asyncio.Event()
        writes = []
        original_set = self.server.FoundryStateStore.set_item

        async def save_then_defer(store, key, value, **kwargs):
            result = await original_set(store, key, value, **kwargs)
            if value["status"] == "simulation_approved":
                writes.append(copy.deepcopy(value))
                ctx = get_task_manager()._active_tasks[value["task_id"]].context
                committed.set()
                await ctx.shutdown.wait()
            return result

        with patch.object(self.server.FoundryStateStore, "set_item", new=save_then_defer):
            async with self.host(stage_delay_seconds=0.3) as (_, client):
                rid, gate, before = await self.start(client)
                value = self.decision(gate)
                run = await self.server.approval_task.start(
                    task_id=gate["task_id"],
                    input_id=value["input_id"],
                    if_last_input_id=value["if_last_input_id"],
                    input={"action": "decide", "response_id": rid, "decision": value},
                )
                await asyncio.wait_for(committed.wait(), 5)
            with self.assertRaises(TaskDeferred):
                await run.result()
            async with self.host(stage_delay_seconds=0) as (_, client):
                final = await self.finish(client, rid)
                async with asyncio.timeout(5):
                    while True:
                        info = await get_task_manager().provider.get(gate["task_id"])
                        if info.status == "suspended":
                            break
                        await asyncio.sleep(0.02)
                recovered = (await client.get(f"/workshop/approvals/{rid}")).json()
                self.assertEqual(writes, [recovered])
                self.assertEqual(recovered["decision"]["input_id"], value["input_id"])
                verify_completion(before, final, recovered)

    async def test_missing_gate_on_recovery_fails_instead_of_recreating_approval(self):
        async with self.host(stage_delay_seconds=0) as (_, client):
            rid, gate, before = await self.start(client)
        async with self.server.FoundryStateStore(self.server.gate_store_name(rid)) as store:
            await store.delete_item("gate")
        async with self.host(stage_delay_seconds=0) as (_, client):
            final = await self.finish(client, rid)
            self.assertEqual(final["status"], "failed")
            self.assertEqual(final["output"], before["output"])
            reply = await client.get(f"/workshop/approvals/{rid}")
            self.assertEqual(reply.status_code, 404)
            with self.assertRaises(ValueError):
                verify_completion(before, final, gate)

    async def test_invalid_stale_cross_response_and_duplicate_decisions_do_not_execute_work(self):
        async with self.host(stage_delay_seconds=0) as (_, client):
            rid, gate, before = await self.start(client)
            for changed, status in (
                ({"simulated": False}, 400),
                ({"simulated": "true"}, 400),
                ({"decision": "human-approved"}, 400),
                ({"gate_id": "other-response"}, 409),
                ({"request_sha256": "changed"}, 409),
                ({"if_last_input_id": "stale"}, 409),
            ):
                reply = await client.post(
                    f"/workshop/approvals/{rid}", json={**self.decision(gate), **changed}
                )
                self.assertEqual(reply.status_code, status, reply.text)
            unchanged = (await client.get(f"/workshop/approvals/{rid}")).json()
            self.assertEqual(unchanged, gate)
            value = (await client.get(f"/responses/{rid}")).json()
            self.assertEqual(value["output"], before["output"])
            replies = await asyncio.gather(
                client.post(f"/workshop/approvals/{rid}", json=self.decision(gate)),
                client.post(
                    f"/workshop/approvals/{rid}",
                    json=self.decision(gate, input_id="simulated-decision-two"),
                ),
            )
            self.assertEqual(sorted(reply.status_code for reply in replies), [200, 409])
            duplicate = await client.post(f"/workshop/approvals/{rid}", json=self.decision(gate))
            self.assertEqual(duplicate.status_code, 409, duplicate.text)
            final = await self.finish(client, rid)
            approved = (await client.get(f"/workshop/approvals/{rid}")).json()
            verify_completion(before, final, approved)

    async def test_rejection_completes_without_the_approved_workload(self):
        async with self.host(stage_delay_seconds=0) as (_, client):
            rid, gate, before = await self.start(client)
            reply = await client.post(
                f"/workshop/approvals/{rid}", json=self.decision(gate, "reject")
            )
            self.assertEqual(reply.status_code, 200, reply.text)
            final = await self.finish(client, rid)
            report = verify_completion(before, final, reply.json())
            self.assertEqual(len(report["final_output_ids"]), 2)
            self.assertNotIn("synthetic_review_packet", json.dumps(final))

    async def test_timeout_and_cancel_never_complete_or_execute_the_workload(self):
        async with self.host(approval_timeout_seconds=1, stage_delay_seconds=0) as (_, client):
            rid, gate, _ = await self.start(client)
            final = await self.finish(client, rid)
            self.assertEqual(final["status"], "failed", final)
            self.assertEqual(final["error"]["code"], "approval_timeout")
            self.assertEqual(len(final["output"]), 1)
            reply = await client.post(f"/workshop/approvals/{rid}", json=self.decision(gate))
            self.assertEqual(reply.status_code, 409, reply.text)
            rid, _, _ = await self.start(client)
            reply = await client.post(f"/responses/{rid}/cancel")
            self.assertEqual(reply.status_code, 200, reply.text)
            cancelled = await self.finish(client, rid)
            self.assertEqual(cancelled["status"], "cancelled", cancelled)
            self.assertNotIn("synthetic_review_packet", json.dumps(cancelled))

    async def test_contract_rejects_unsafe_modes_before_creating_an_sdk_task(self):
        async with self.host() as (_, client):
            for changes in (
                {"store": False},
                {"background": False},
                {"input": "H01"},
                {"tools": []},
            ):
                result = await client.post(
                    "/responses",
                    json={
                        "model": MODEL_LABEL,
                        "input": "D03",
                        "store": True,
                        "background": True,
                        "stream": True,
                        **changes,
                    },
                )
                self.assertEqual(result.status_code, 400, result.text)
            self.assertFalse(list((self.state_root / "tasks").rglob("*.json")))

    async def test_changed_workload_on_recovery_fails_closed_without_replacing_checkpoint(self):
        async with self.host(stage_delay_seconds=0) as (_, client):
            rid, gate, before = await self.start(client)
        changed = copy.deepcopy(gate["scenario"])
        changed["lineage"]["workload_sha256"] = "changed-version"
        with patch.object(self.server, "scenario", return_value=changed):
            async with self.host(stage_delay_seconds=0) as (_, client):
                final = await self.finish(client, rid)
                self.assertEqual(final["status"], "failed", final)
                self.assertEqual(final["output"], before["output"])
                checkpoint_outputs(final, gate)
                self.assertIsNone(
                    (await client.get(f"/workshop/approvals/{rid}")).json()["decision"]
                )
