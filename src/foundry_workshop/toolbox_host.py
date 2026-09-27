import asyncio
import json
from pathlib import Path
from typing import Any, Never
from uuid import uuid4

from .contracts import load_cases, validate_question
from .settings import Settings
from .toolbox import QUESTIONS, execute, snapshot, version_value


def build_agent(
    root: Path,
    settings: Settings,
    version: str,
    *,
    with_skill: bool = False,
    packaged_source: dict[str, Any] | None = None,
    questions: list[str] | None = None,
    evidence_root: Path | None = None,
):
    from agent_framework import AgentResponse, Message, WorkflowBuilder, WorkflowContext, executor

    version = version_value(version)
    if packaged_source is not None:
        if (
            evidence_root is None
            or not evidence_root.is_absolute()
            or evidence_root.resolve().is_relative_to(root.resolve())
        ):
            raise ValueError(
                "The packaged host must use an explicit writable session evidence directory."
            )
        evidence_root.mkdir(parents=True, exist_ok=True)
    allowed = (
        [case["question"] for case in load_cases(root, "dev", settings.language)]
        if questions is None
        else questions
    )
    if (
        not isinstance(allowed, list)
        or not allowed
        or any(not isinstance(value, str) for value in allowed)
    ):
        raise ValueError("The Toolbox host needs its explicit synthetic questions-only allowlist.")
    allowed = [*allowed, QUESTIONS[settings.language]]

    @executor(id="synthetic_toolbox_request")
    async def invoke(messages: list[Message], context: WorkflowContext[Never, AgentResponse]):
        from .cloud import project_clients

        users = [message for message in messages if message.role == "user"]
        if not users:
            raise ValueError("The Toolbox host requires a synthetic user question.")
        question = validate_question(users[-1].text)
        if question not in allowed:
            raise ValueError(
                "This training host accepts only the bundled dev questions or its documented Toolbox question."
            )
        with project_clients(settings) as (project, _):
            binding = snapshot(project, settings, version)
        result = await execute(
            settings,
            root,
            binding,
            f"request-{uuid4().hex}",
            invoke=True,
            confirmed=True,
            with_skill=with_skill,
            question=question,
            packaged_source=packaged_source,
            evidence_root=evidence_root,
        )
        await context.yield_output(
            AgentResponse(
                messages=[Message("assistant", [json.dumps(result, ensure_ascii=False)])],
                response_id=result["model_calls"][-1]["response_id"],
            )
        )

    return (
        WorkflowBuilder(start_executor=invoke, name="SyntheticToolboxHost")
        .build()
        .as_agent(name="SyntheticToolboxHost")
    )


def serve(
    root: Path,
    settings: Settings,
    version: str,
    *,
    with_skill: bool = False,
    packaged_source: dict[str, Any] | None = None,
    questions: list[str] | None = None,
    evidence_root: Path | None = None,
) -> None:
    from agent_framework_foundry_hosting import ResponsesHostServer

    agent = build_agent(
        root,
        settings,
        version,
        with_skill=with_skill,
        packaged_source=packaged_source,
        questions=questions,
        evidence_root=evidence_root,
    )
    asyncio.run(ResponsesHostServer(agent).run_async())
