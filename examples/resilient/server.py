"""Actual AgentServer tasks + Responses; prewritten workload, local file storage only."""

import asyncio
import json
import time
import uuid
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

from azure.ai.agentserver.core.storage import FoundryStateStore, FoundryStorageNotFoundError
from azure.ai.agentserver.core.tasks import (
    LastInputIdPreconditionFailed,
    RetryPolicy,
    TaskConflictError,
    TaskContext,
    TaskFailed,
    multi_turn_task,
    set_resilient_tasks_enabled,
)
from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponseEventStream,
    ResponsesAgentServerHost,
    ResponsesServerOptions,
)
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from foundry_workshop.contracts import digest, parse_json
from foundry_workshop.resilience import (
    MODE,
    TASK_NAME,
    GateConflict,
    apply_decision,
    checkpoint_outputs,
    new_gate,
    output_payload,
    require_local_environment,
    response_id,
    scenario,
    task_id,
    validate_create,
    validate_decision,
    validate_gate,
)


def gate_store_name(response: str) -> str:
    return f"workshop-resilience-v1/{task_id(response)}"


async def read_gate(response: str) -> dict[str, Any] | None:
    async with FoundryStateStore(gate_store_name(response)) as store:
        try:
            item = await store.get_item("gate")
        except FoundryStorageNotFoundError:
            return None
    if item is None:
        return None
    value = dict(item.value)
    validate_gate(value)
    if value["response_id"] != response:
        raise ValueError("Persisted gate belongs to another response.")
    return value


@multi_turn_task(name=TASK_NAME, timeout=timedelta(seconds=30), retry=RetryPolicy.no_retry())
async def approval_task(ctx: TaskContext[dict]) -> dict:
    """Returning suspends the *SDK chain*; a decision is a new turn on the same task_id."""
    data = ctx.input
    response = response_id(data["response_id"])
    if ctx.task_id != task_id(response):
        raise GateConflict("Approval task and response identities differ.")
    if ctx.shutdown.is_set():
        return await ctx.exit_for_recovery()
    if ctx.cancel.is_set():
        raise asyncio.CancelledError
    store = await FoundryStateStore.get_or_create(gate_store_name(response), item_ttl_seconds=86400)
    async with store:
        item = await store.get_item("gate")
        if data["action"] == "request":
            proposed = new_gate(
                response=response,
                input_id=ctx.input_id,
                gate_id=data["gate_id"],
                source=data["scenario"],
                expires_at=data["expires_at"],
            )
            if item is None:
                await store.create_item("gate", proposed)
                gate = proposed
            else:
                gate = dict(item.value)
                validate_gate(gate)
                if output_payload("approval_request", gate) != output_payload(
                    "approval_request", proposed
                ):
                    raise GateConflict("The persisted request cannot be replaced on recovery.")
        elif data["action"] == "decide":
            if item is None:
                raise GateConflict("There is no persisted approval request.")
            gate = dict(item.value)
            validate_gate(gate)
            # Recovery can re-enter after the decision write but before turn completion.
            if ctx.entry_mode == "recovered" and gate["decision"] is not None:
                expected = gate["decision"]
                if (
                    expected["input_id"] != ctx.input_id
                    or data["decision"].get("simulated") is not True
                    or data["decision"]
                    != {
                        "gate_id": gate["gate_id"],
                        "request_sha256": gate["request_sha256"],
                        "if_last_input_id": gate["request_input_id"],
                        "input_id": expected["input_id"],
                        "decision": expected["decision"],
                        "simulated": True,
                    }
                ):
                    raise GateConflict("Recovered input does not match the committed decision.")
            else:
                gate = apply_decision(gate, data["decision"], entry_mode=ctx.entry_mode)
                await store.set_item("gate", gate, if_match=item.etag)
        else:
            raise ValueError("Unknown approval task action.")
        if ctx.shutdown.is_set():
            return await ctx.exit_for_recovery()
        return gate


class LocalContractMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if (
            scope["type"] == "http"
            and scope["method"] == "POST"
            and (scope["path"] == "/responses" or scope["path"].startswith("/workshop/approvals/"))
        ):
            body = bytearray()
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                body.extend(message.get("body", b""))
                if len(body) > 4096:
                    await JSONResponse({"error": "Local request exceeds 4096 bytes."}, 413)(
                        scope, receive, send
                    )
                    return
                if not message.get("more_body", False):
                    break
            try:
                value = parse_json(body.decode("utf-8"))
                if scope["path"] == "/responses":
                    validate_create(value)
            except (ValueError, UnicodeDecodeError) as exc:
                await JSONResponse({"error": str(exc)}, status_code=400)(scope, receive, send)
                return
            delivered = False

            async def replay() -> Message:
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            await self.app(scope, replay, send)
        else:
            await self.app(scope, receive, send)


def create_app(
    root: Path,
    *,
    language: str = "en",
    approval_timeout_seconds: int = 600,
    stage_delay_seconds: float = 1.0,
    on_checkpoint: Callable[[dict[str, Any], bool], None] | None = None,
) -> ResponsesAgentServerHost:
    require_local_environment()
    if type(approval_timeout_seconds) is not int or not 1 <= approval_timeout_seconds <= 900:
        raise ValueError("approval_timeout_seconds must be between 1 and 900.")
    if not 0 <= stage_delay_seconds <= 5:
        raise ValueError("stage_delay_seconds must be between 0 and 5.")
    source = scenario(root, language)
    app = ResponsesAgentServerHost(
        options=ResponsesServerOptions(resilient_background=True, shutdown_grace_period_seconds=2),
        configure_observability=None,
        graceful_shutdown_timeout=3,
    )
    set_resilient_tasks_enabled(True)
    app.add_middleware(LocalContractMiddleware)

    async def identity(request: Request):
        return JSONResponse(
            {
                "mode": MODE,
                "agent_name": app.config.agent_name,
                "run_id": app.config.session_id,
            }
        )

    async def get_approval(request: Request):
        try:
            gate = await read_gate(request.path_params["response"])
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        if gate is None:
            return JSONResponse({"error": "Approval request not found."}, status_code=404)
        return JSONResponse(gate)

    async def decide(request: Request):
        try:
            response = response_id(request.path_params["response"])
            gate = await read_gate(response)
            if gate is None:
                return JSONResponse({"error": "Approval request not found."}, status_code=404)
            value = parse_json((await request.body()).decode("utf-8"))
            validate_decision(gate, value)
            result = await approval_task.run(
                task_id=gate["task_id"],
                input_id=value["input_id"],
                if_last_input_id=value["if_last_input_id"],
                input={"action": "decide", "response_id": response, "decision": value},
            )
        except (GateConflict, LastInputIdPreconditionFailed, TaskConflictError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        except (ValueError, UnicodeDecodeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except TaskFailed as exc:
            return JSONResponse({"error": f"SDK approval task failed: {exc}"}, status_code=500)
        return JSONResponse(result)

    app.add_route("/workshop/identity", identity, methods=["GET"])
    app.add_route("/workshop/approvals/{response}", get_approval, methods=["GET"])
    app.add_route("/workshop/approvals/{response}", decide, methods=["POST"])

    @app.response_handler
    async def handler(
        request: CreateResponse, context: ResponseContext, cancellation_signal: asyncio.Event
    ):
        if context.is_recovery and context.persisted_response is None:
            raise ValueError("Recovery snapshot is missing; refusing to regenerate committed work.")
        stream = (
            ResponseEventStream(
                response_id=context.response_id, response=context.persisted_response
            )
            if context.is_recovery and context.persisted_response is not None
            else ResponseEventStream(response_id=context.response_id, request=request)
        )
        yield stream.emit_created()
        if context.shutdown.is_set():
            await context.exit_for_recovery()
        if cancellation_signal.is_set():
            return
        yield stream.emit_in_progress()

        gate = await read_gate(context.response_id)
        if gate is None:
            if stream.response.get("output"):
                raise ValueError("Checkpointed response lost its approval gate; refusing recovery.")
            gate = await approval_task.run(
                task_id=task_id(context.response_id),
                input_id=f"request-{context.response_id}",
                input={
                    "action": "request",
                    "response_id": context.response_id,
                    "gate_id": uuid.uuid4().hex,
                    "scenario": source,
                    "expires_at": context.created_at.timestamp() + approval_timeout_seconds,
                },
            )
        if gate["request_sha256"] != digest(source):
            raise ValueError("Scenario or workload changed since the request; recovery is refused.")
        committed = checkpoint_outputs(stream.response, gate)
        start = len(committed)

        async def pause(seconds: float) -> bool:
            deadline = asyncio.get_running_loop().time() + seconds
            while asyncio.get_running_loop().time() < deadline:
                if context.shutdown.is_set():
                    await context.exit_for_recovery()
                if cancellation_signal.is_set():
                    return False
                await asyncio.sleep(min(0.05, max(0, deadline - asyncio.get_running_loop().time())))
            if context.shutdown.is_set():
                await context.exit_for_recovery()
            return not cancellation_signal.is_set()

        if start == 0:
            for event in stream.output_item_message(
                json.dumps(output_payload("approval_request", gate))
            ):
                yield event
            if not await pause(0):
                return
            yield stream.checkpoint()
            if on_checkpoint is not None:
                on_checkpoint(stream.response, context.is_recovery)
            start = 1

        while gate["status"] == "awaiting_simulated_decision":
            if not await pause(0.05):
                return
            if time.time() >= gate["expires_at"]:
                yield stream.emit_failed(
                    code="approval_timeout",
                    message="Simulated decision window expired; no workload steps were executed.",
                )
                return
            current = await read_gate(context.response_id)
            if current is None:
                raise ValueError("Persisted gate disappeared; no fallback or implicit approval.")
            if output_payload("approval_request", current) != output_payload(
                "approval_request", gate
            ):
                raise ValueError("Persisted approval request changed while waiting.")
            gate = current

        stages = (
            ("approval_request", "simulation_rejected")
            if gate["status"] == "simulation_rejected"
            else ("approval_request", "synthetic_review_packet", "human_handoff_required")
        )
        for stage in stages[start:]:
            if not await pause(stage_delay_seconds):
                return
            for event in stream.output_item_message(json.dumps(output_payload(stage, gate))):
                yield event
            if not await pause(0):
                return
            yield stream.checkpoint()
            if on_checkpoint is not None:
                on_checkpoint(stream.response, context.is_recovery)
        if not await pause(0):
            return
        yield stream.emit_completed()

    return app
