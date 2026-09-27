"""Preview: score the local MAF function-tool agent's tool calls with Foundry evaluators."""

from pathlib import Path
from typing import Any

from .contracts import digest, load_cases, load_documents
from .settings import Settings, credential_for, owned_prefix, require_env

EVALUATORS = ("tool_call_accuracy", "relevance")


def tool_calls(response: Any) -> list[dict[str, Any]]:
    calls = []
    for message in getattr(response, "messages", None) or []:
        for content in getattr(message, "contents", None) or []:
            if getattr(content, "type", None) == "function_call":
                arguments = getattr(content, "arguments", None)
                calls.append(
                    {
                        "name": getattr(content, "name", None),
                        "arguments": arguments
                        if isinstance(arguments, (str, dict)) or arguments is None
                        else str(arguments),
                    }
                )
    return calls


def summarize_tool_results(
    *,
    status: str | None,
    output_items: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    responses: list[dict[str, Any]],
    evaluators: tuple[str, ...] = EVALUATORS,
) -> dict[str, Any]:
    """Join Foundry output items to dev cases by their submitted query; never by item order."""
    rows: list[dict[str, Any] | None] = [None] * len(cases)
    problems = []
    if status != "completed":
        problems.append(f"The Foundry run ended with status {status!r}; no scores were accepted.")
    else:
        positions = {case["question"].strip(): index for index, case in enumerate(cases)}
        for item in output_items:
            source = item.get("datasource_item")
            query = source.get("query") if isinstance(source, dict) else None
            position = positions.get(query.strip()) if isinstance(query, str) else None
            if position is None or rows[position] is not None:
                problems.append("An output item did not map to exactly one dev question.")
                continue
            results = {
                result.get("name"): {"score": result.get("score"), "passed": result.get("passed")}
                for result in item.get("results") or []
                if isinstance(result, dict)
            }
            rows[position] = {
                "case_id": cases[position]["case_id"],
                "question": cases[position]["question"],
                "status": item.get("status"),
                "tool_calls": responses[position]["tool_calls"],
                "answer_text": responses[position]["text"],
                "scores": results,
            }
    errors = sum(
        row is None
        or any(
            type(row["scores"].get(name, {}).get("passed")) is not bool
            or type(row["scores"].get(name, {}).get("score")) not in {int, float}
            for name in evaluators
        )
        for row in rows
    )
    complete = not problems and errors == 0
    return {
        "status": status,
        "complete": complete,
        "gate_passed": complete,
        "errors": errors,
        "problems": sorted(set(problems)),
        "native_pass_counts": {
            name: {
                "passed": sum(
                    row is not None and row["scores"].get(name, {}).get("passed") is True
                    for row in rows
                ),
                "total": len(cases),
            }
            for name in evaluators
        },
        "rows": rows,
    }


async def evaluate_tool_use(
    settings: Settings, root: Path, *, timeout: int, confirmed: bool
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("Agent runs and Foundry judges are billable; pass --confirm-cost.")
    if not 30 <= timeout <= 900:
        raise ValueError("Evaluation timeout must be 30-900 seconds.")
    judge = require_env("AZURE_AI_EVALUATION_MODEL_DEPLOYMENT_NAME")
    if judge == settings.deployment:
        raise ValueError("The judge deployment must be separate from the agent's deployment.")
    from agent_framework import evaluate_agent
    from agent_framework.foundry import FoundryChatClient, FoundryEvals

    from .agents import build_policy_agent, lookup_instruction, policy_instructions
    from .cloud import project_clients

    cases = load_cases(root, "dev", settings.language)
    with project_clients(settings, preview=True) as (project, _client):
        catalog_versions = {
            name: project.beta.evaluators.get_version(f"builtin.{name}", "latest")
            .as_dict()
            .get("version")
            for name in EVALUATORS
        }
    responses = []
    with credential_for(settings) as credential:
        agent = build_policy_agent(settings, root, credential, tools=True)
        judge_client = FoundryChatClient(
            project_endpoint=settings.project_endpoint, model=judge, credential=credential
        )
        evaluators = FoundryEvals(
            client=judge_client, model=judge, evaluators=list(EVALUATORS), timeout=float(timeout)
        )
        async with agent:
            runs = []
            for case in cases:
                response = await agent.run(case["question"])
                runs.append(response)
                responses.append({"text": response.text, "tool_calls": tool_calls(response)})
            results = await evaluate_agent(
                agent=agent,
                queries=[case["question"] for case in cases],
                responses=runs,
                evaluators=evaluators,
                eval_name=f"{owned_prefix()}-maf-tools"[:63],
            )
    if len(results) != 1:
        raise ValueError("Expected exactly one Foundry evaluation result.")
    result = results[0]
    output_items: list[dict[str, Any]] = []
    criteria: list[dict[str, Any]] = []
    if result.eval_id:
        with project_clients(settings, preview=True) as (_project, client):
            evaluation = client.evals.retrieve(eval_id=result.eval_id).model_dump(mode="json")
            criteria = [
                {key: criterion.get(key) for key in ("name", "evaluator_name", "evaluator_version")}
                for criterion in evaluation.get("testing_criteria") or []
            ]
            if result.status == "completed" and result.run_id:
                output_items = [
                    item.model_dump(mode="json")
                    for item in client.evals.runs.output_items.list(
                        run_id=result.run_id, eval_id=result.eval_id
                    )
                ]
    summary = summarize_tool_results(
        status=result.status, output_items=output_items, cases=cases, responses=responses
    )
    return {
        "mode": "live",
        "language": settings.language,
        "orchestration": "local-maf",
        "tools": "function",
        "target_deployment": settings.deployment,
        "judge_deployment": judge,
        "evaluators": list(EVALUATORS),
        "catalog_versions_before_run": catalog_versions,
        "testing_criteria": criteria,
        "evaluator_versions_pinned": bool(criteria)
        and all(criterion.get("evaluator_version") for criterion in criteria),
        "dataset": "dev",
        "dataset_hash": digest(cases),
        "corpus_hash": digest(load_documents(root, settings.language)),
        "instructions_hash": digest(
            policy_instructions(root, settings.language) + lookup_instruction(settings.language)
        ),
        "evaluation_id": result.eval_id,
        "run_id": result.run_id,
        "report_url": result.report_url,
        "service_error": result.error,
        **summary,
        "preview": (
            "MAF evaluation APIs are experimental and several Foundry agent evaluators were marked "
            "Preview on Microsoft Learn, checked 2026-09-23."
        ),
        "note": (
            "Tool-use scores are not business correctness. A rerun makes new agent runs and a new "
            "Foundry job; keep a failed output and its report_url instead."
        ),
    }
