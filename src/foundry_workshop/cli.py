import argparse
import asyncio
import json
import subprocess
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .contracts import load_cases, load_documents, read_json, validate_question, write_json
from .evaluation import acceptance_report, compare_runs, evaluate_run, record_feedback
from .experiments import collect, offline_demo
from .knowledge import evidence, local_retrieve
from .profiles import INFERENCE_APIS, PATTERNS, RETRIEVALS, RuntimeProfile

DEFAULT_QUESTION = "2026년 9월 국내 출장 숙박비는 1박 얼마까지인가요?"
DEFAULT_QUESTION_EN = (
    "What is the domestic business-trip lodging limit per night for September 2026?"
)


def runtime_arguments(command: argparse.ArgumentParser, *, default_kind: str = "policy") -> None:
    command.add_argument("--kind", choices=("policy", "workflow"), default=default_kind)
    command.add_argument("--pattern", choices=PATTERNS, default="sequential")
    command.add_argument("--retrieval", choices=RETRIEVALS, default="local")
    command.add_argument("--prompt", choices=("v1", "v2"), default="v2")
    command.add_argument("--api", choices=INFERENCE_APIS, default="project-responses")
    command.add_argument("--protocol", choices=("responses", "invocations"), default="responses")


def runtime_profile(args: argparse.Namespace) -> RuntimeProfile:
    return RuntimeProfile(
        **{key: getattr(args, key) for key in RuntimeProfile.__dataclass_fields__}
    )


def output_argument(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--output",
        type=Path,
        metavar="FILE",
        help="Also save JSON to a new .json file under outputs/. The parent must exist; no overwrite.",
    )


def output_path(root: Path, value: Path) -> Path:
    path = value if value.is_absolute() else root / value
    if path.exists() or path.is_symlink():
        raise FileExistsError(
            f"{path} already exists. Read it or choose a new --output file; no request was sent."
        )
    path = path.resolve()
    if not path.is_relative_to(root.resolve() / "outputs") or path.suffix != ".json":
        raise ValueError("--output must be a .json file inside this repository's outputs/.")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Microsoft Foundry v1.5 workshop. Start with doctor, demo and evaluate offline; "
            "advanced command families are optional."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "First offline pass (no external packages or Azure):\n"
            "  python3.13 scripts/workshop.py --language en doctor\n"
            "  python3.13 scripts/workshop.py --language en demo --label first-offline\n"
            "  python3.13 scripts/workshop.py --language en evaluate --label first-offline\n\n"
            "Use a new label for another run. Fixtures are not model-quality evidence.\n"
            "Start at README.md, then follow docs/00-setup.md.\n"
            "For required inputs and side effects: COMMAND --help."
        ),
    )
    result.add_argument(
        "--language",
        choices=("ko", "en"),
        default="ko",
        help="Synthetic data language (default: ko). Place before COMMAND.",
    )
    result.add_argument(
        "--debug", action="store_true", help="Print the error stack for local diagnosis."
    )
    commands = result.add_subparsers(
        dest="command", title="commands", metavar="COMMAND", required=True
    )
    doctor = commands.add_parser(
        "doctor", help="Read-only prerequisite checks; offline by default."
    )
    doctor.add_argument("--cloud", action="store_true")
    demo = commands.add_parser(
        "demo", help="OFFLINE teaching fixtures; never calls an LLM or Azure."
    )
    demo.add_argument("--label", default="demo-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S"))
    demo.add_argument("--prompt", choices=("v1", "v2"), default="v2")
    retrieve = commands.add_parser(
        "retrieve",
        help="Read evidence; local keyword search by default.",
        description="Read synthetic evidence. Local retrieval is offline; Search/IQ can incur costs.",
    )
    retrieve.add_argument("--provider", choices=RETRIEVALS, default="local")
    retrieve.add_argument("--question")
    output_argument(retrieve)
    for name, description in (
        ("model", "LIVE: send one question to the configured Azure model."),
        ("answer", "LIVE: return a validated answer with synthetic source evidence."),
        ("maf", "LIVE: run a local MAF agent with no tool, a function or local MCP."),
        ("workflow", "LIVE: compare sequential, concurrent or group-chat MAF execution."),
    ):
        command = commands.add_parser(name, help=description, description=description)
        command.add_argument("--question")
        output_argument(command)
        if name in {"model", "answer"}:
            command.add_argument(
                "--api",
                choices=("project-responses", "account-responses"),
                default="project-responses",
                help="Choose the inference endpoint explicitly; never changed after an error.",
            )
        if name == "answer":
            command.add_argument("--prompt", choices=("v1", "v2"), default="v2")
            command.add_argument("--retrieval", choices=RETRIEVALS, default="local")
        if name == "maf":
            group = command.add_mutually_exclusive_group()
            group.add_argument("--tools", action="store_true")
            group.add_argument("--mcp", action="store_true")
        if name == "workflow":
            command.add_argument(
                "--pattern",
                choices=("sequential", "concurrent", "group-chat"),
                default="sequential",
            )
    wrapped = commands.add_parser(
        "workflow-agent",
        help="LIVE: run a case-isolated workflow with validated answer and model-call lineage.",
    )
    wrapped.add_argument("--question")
    output_argument(wrapped)
    runtime_arguments(wrapped, default_kind="workflow")
    contract = commands.add_parser(
        "runtime-contract",
        help="Read local code/prompt/configuration hashes; no Azure request or deployment.",
    )
    runtime_arguments(contract)
    benchmark = commands.add_parser(
        "benchmark",
        help="Version-pinned Hosted model matrix, native judges, regressions and release evidence.",
    )
    benchmark_actions = benchmark.add_subparsers(dest="benchmark_action", required=True)
    for action in ("plan", "collect", "smoke"):
        operation = benchmark_actions.add_parser(action)
        runtime_arguments(operation)
        operation.set_defaults(protocol="invocations")
        if action == "collect":
            operation.add_argument("--label", required=True)
            operation.add_argument("--split", choices=("dev", "holdout"), default="dev")
            operation.add_argument("--model-key", action="append")
            operation.add_argument("--concurrency", type=int, default=1)
            operation.add_argument("--candidate")
            operation.add_argument("--unlock-holdout", action="store_true")
            operation.add_argument("--regressions")
            operation.add_argument("--confirm-cost", action="store_true")
        elif action == "smoke":
            operation.add_argument("--label", required=True)
            operation.add_argument("--local", action="store_true")
            operation.add_argument(
                "--azd-directory",
                type=Path,
                help="Required with --local: the existing standalone azd project. Never inferred.",
            )
            operation.add_argument("--case", default="D01")
            operation.add_argument("--model-key")
            operation.add_argument("--confirm-cost", action="store_true")
    matrix_eval = benchmark_actions.add_parser("evaluate")
    matrix_eval.add_argument("--label", required=True)
    matrix_eval.add_argument("--reference")
    matrix_eval.add_argument("--timeout", type=int, default=300)
    matrix_eval.add_argument("--retry-failed", action="store_true")
    matrix_eval.add_argument("--confirm-cost", action="store_true")
    matrix_compare = benchmark_actions.add_parser("compare")
    matrix_compare.add_argument("--baseline", required=True)
    matrix_compare.add_argument("--candidate", required=True)
    for action in ("report", "trace-plan", "monitor", "stop-session"):
        operation = benchmark_actions.add_parser(action)
        operation.add_argument("--label", required=True)
    regression = benchmark_actions.add_parser("regression")
    regression.add_argument("--label", required=True)
    regression.add_argument("--row-id", required=True)
    regression.add_argument("--regression-label", required=True)
    regression.add_argument("--reviewer", required=True)
    regression.add_argument("--reason", required=True)
    regression.add_argument("--confirm-review", action="store_true")
    verify = benchmark_actions.add_parser("verify")
    verify.add_argument("--baseline", required=True)
    verify.add_argument("--candidate", required=True)
    verify.add_argument("--holdout", required=True)
    verify.add_argument("--require-native", action="store_true")
    verify.add_argument("--require-traces", action="store_true")
    verify.add_argument("--require-native-pass", action="store_true")
    verify.add_argument("--require-regressions", action="store_true")
    verify.add_argument("--calibration")
    calibration = commands.add_parser(
        "calibrate-judge",
        help="LIVE judge over bundled calibration fixtures; no target-agent responses.",
    )
    calibration.add_argument("--label", required=True)
    calibration.add_argument("--reference")
    calibration.add_argument("--timeout", type=int, default=300)
    calibration.add_argument("--confirm-cost", action="store_true")
    batch = commands.add_parser(
        "collect", help="LIVE: collect all cases, keeping errors in the denominator."
    )
    batch.add_argument("--label", required=True)
    batch.add_argument("--split", choices=("dev", "holdout"), default="dev")
    batch.add_argument("--prompt", choices=("v1", "v2"), default="v1")
    batch.add_argument(
        "--api", choices=("project-responses", "account-responses"), default="project-responses"
    )
    batch.add_argument(
        "--retrieval",
        choices=(*RETRIEVALS, "none"),
        default="local",
        help="none is a dev-only diagnostic that sends no policy evidence.",
    )
    batch.add_argument("--unlock-holdout", action="store_true")
    batch.add_argument("--candidate", help="Frozen real dev label; required for holdout.")
    grade = commands.add_parser(
        "evaluate", help="Deterministic local business checks; no judge/model call."
    )
    grade.add_argument("--label", required=True)
    compare = commands.add_parser(
        "compare", help="Compare controlled dev experiments without deploying."
    )
    compare.add_argument("--baseline", required=True)
    compare.add_argument("--candidate", required=True)
    compare.add_argument("--variable", choices=("prompt", "model"), default="prompt")
    accept = commands.add_parser(
        "accept", help="Produce a real candidate/holdout handoff, never a deployment approval."
    )
    accept.add_argument("--candidate", required=True)
    accept.add_argument("--holdout", required=True)
    feedback = commands.add_parser(
        "feedback", help="Queue a real dev failure for human review; never auto-approve."
    )
    feedback.add_argument("--label", required=True)
    feedback.add_argument("--case", required=True)
    feedback.add_argument("--reason", required=True)
    judge = commands.add_parser(
        "cloud-evaluate", help="LIVE: billable Foundry judges over already-collected responses."
    )
    judge.add_argument("--label", required=True)
    judge.add_argument("--timeout", type=int, default=300)
    judge.add_argument(
        "--business-evaluator",
        action="store_true",
        help="Preview: also register/reuse your owned code-based business-rubric evaluator.",
    )
    judge.add_argument(
        "--reference",
        help="Add this run to the reference label's Foundry evaluation for Compare runs.",
    )
    judge.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry this label's failed/invalid attempt; the attempt stays in native-attempts/.",
    )
    judge.add_argument("--confirm-cost", action="store_true")
    tool_judge = commands.add_parser(
        "maf-evaluate",
        help="LIVE Preview: run the MAF function-tool agent on dev and score tool calls in Foundry.",
    )
    tool_judge.add_argument("--timeout", type=int, default=300)
    tool_judge.add_argument("--confirm-cost", action="store_true")
    output_argument(tool_judge)
    seed = commands.add_parser(
        "seed-search", help="Create namespaced Search objects in an existing service."
    )
    seed.add_argument("--iq", action="store_true")
    seed.add_argument("--hybrid", action="store_true")
    seed.add_argument("--confirm-cost", action="store_true")
    seed.add_argument("--confirm-create", action="store_true")
    iq_chat = commands.add_parser(
        "iq-chat",
        help="Fixed gpt-5.6-luna + Search managed identity preset; separate from model-free GA retrieval.",
    )
    iq_actions = iq_chat.add_subparsers(dest="iq_chat_action", required=True)
    iq_actions.add_parser(
        "check", help="Read-only model, Search identity, role and source preflight."
    )
    iq_setup = iq_actions.add_parser(
        "setup", help="Create only the owned chat base after a successful preflight."
    )
    iq_setup.add_argument("--confirm-create", action="store_true")
    iq_ask = iq_actions.add_parser(
        "ask", help="Billable IQ planning and answer synthesis with recorded evidence."
    )
    iq_ask.add_argument("--question")
    iq_ask.add_argument("--label", required=True)
    iq_ask.add_argument("--confirm-cost", action="store_true")
    toolbox = commands.add_parser(
        "toolbox", help="Owned synthetic-policy Toolbox lifecycle and version-pinned MAF execution."
    )
    toolbox_actions = toolbox.add_subparsers(dest="toolbox_action", required=True)
    toolbox_plan = toolbox_actions.add_parser(
        "plan", help="Inspect the local preset; no Azure request."
    )
    toolbox_plan.add_argument("--discovery", action="store_true")
    toolbox_plan.add_argument("--skill-version")
    toolbox_plan.add_argument("--pin-policy", action="store_true")
    toolbox_inspect = toolbox_actions.add_parser(
        "inspect", help="Read actual version and connection metadata."
    )
    toolbox_inspect.add_argument("--version")
    for action in ("create", "add-version"):
        operation = toolbox_actions.add_parser(action)
        operation.add_argument("--discovery", action="store_true")
        operation.add_argument("--skill-version")
        operation.add_argument("--pin-policy", action="store_true")
        operation.add_argument("--confirm-create", action="store_true")
    selection = toolbox_actions.add_parser(
        "select", help="Select an owned default version; also used for rollback."
    )
    selection.add_argument("--version", required=True)
    selection.add_argument("--confirm-update", action="store_true")
    for action in ("probe", "query", "ask"):
        operation = toolbox_actions.add_parser(action)
        operation.add_argument("--version", required=True)
        operation.add_argument("--label", required=True)
        if action in {"query", "ask"}:
            operation.add_argument("--confirm-cost", action="store_true")
        if action == "ask":
            operation.add_argument("--with-skill", action="store_true")
    toolbox_cleanup = toolbox_actions.add_parser(
        "cleanup", help="Delete only a fully owned Toolbox after approval."
    )
    toolbox_cleanup.add_argument("--confirm-delete", action="store_true")
    toolbox_serve = toolbox_actions.add_parser(
        "serve", help="Run the version-pinned synthetic Toolbox Responses host locally."
    )
    toolbox_serve.add_argument("--version", required=True)
    toolbox_serve.add_argument("--with-skill", action="store_true")
    agent = commands.add_parser(
        "prompt-agent", help="Create/invoke a real, service-managed prompt agent."
    )
    agent.add_argument("action", choices=("create", "invoke"))
    agent.add_argument("--name", help="Default: your prefix + -policy-<language>.")
    agent.add_argument("--version")
    agent.add_argument("--question")
    agent.add_argument("--confirm-create", action="store_true")
    output_argument(agent)
    file_search = commands.add_parser(
        "file-search", help="Create, query or clean up an owned File Search agent."
    )
    file_search.add_argument("action", choices=("create", "ask", "cleanup"))
    file_search.add_argument("--name")
    file_search.add_argument("--question")
    file_search.add_argument("--label")
    file_search.add_argument("--confirm-create", action="store_true")
    file_search.add_argument("--confirm-delete", action="store_true")
    file_search.add_argument(
        "--retain",
        action="store_true",
        help="Create without automatic vector-store expiry; storage charges can continue.",
    )
    server = commands.add_parser(
        "serve", help="Run the optional local hosted-agent server. Inference remains billable."
    )
    runtime_arguments(server)
    commands.add_parser(
        "cleanup-plan", help="List local ownership records. Does NOT delete Azure resources."
    )
    materials = commands.add_parser(
        "prepare-extensions",
        help="Derive advanced lab inputs from bundled dev/policies only; no Azure calls.",
    )
    materials.add_argument("--label", required=True)
    conversations = commands.add_parser(
        "conversations",
        help="Dev-only multi-turn collection and separate turn/conversation native evaluation.",
    )
    conversation_actions = conversations.add_subparsers(dest="conversation_action", required=True)
    for action in ("plan", "collect"):
        operation = conversation_actions.add_parser(action)
        operation.add_argument("--prompt", choices=("v1", "v2"), default="v2")
        if action == "collect":
            operation.add_argument("--label", required=True)
            operation.add_argument("--confirm-cost", action="store_true")
    report = conversation_actions.add_parser("report")
    report.add_argument("--label", required=True)
    evaluation = conversation_actions.add_parser("evaluate")
    evaluation.add_argument("--label", required=True)
    evaluation.add_argument("--level", choices=("turn", "conversation"), required=True)
    evaluation.add_argument("--timeout", type=int, default=300)
    evaluation.add_argument("--confirm-cost", action="store_true")
    memory = commands.add_parser(
        "memory", help="Owned managed-memory API exercise using two synthetic scopes."
    )
    memory_actions = memory.add_subparsers(dest="memory_action", required=True)
    memory_actions.add_parser("plan")
    memory_create = memory_actions.add_parser("create")
    memory_create.add_argument("--confirm-create", action="store_true")
    for action in ("put", "update"):
        operation = memory_actions.add_parser(action)
        operation.add_argument("--scope", choices=("alpha", "beta"), required=True)
        operation.add_argument("--case", choices=("D01", "D02"), required=True)
        if action == "update":
            operation.add_argument("--memory-id", required=True)
        operation.add_argument("--confirm-write", action="store_true")
        operation.add_argument("--confirm-cost", action="store_true")
    memory_inspect = memory_actions.add_parser("inspect")
    memory_inspect.add_argument("--scope", choices=("alpha", "beta"), required=True)
    memory_recall = memory_actions.add_parser("recall")
    memory_recall.add_argument("--scope", choices=("alpha", "beta"), required=True)
    memory_recall.add_argument("--label", required=True)
    memory_recall.add_argument("--confirm-cost", action="store_true")
    memory_forget = memory_actions.add_parser("forget")
    memory_forget.add_argument("--memory-id", required=True)
    memory_forget.add_argument("--confirm-delete", action="store_true")
    memory_cleanup = memory_actions.add_parser("cleanup")
    memory_cleanup.add_argument("--confirm-delete", action="store_true")
    a2a = commands.add_parser("a2a", help="Explicit A2A 1.0 between owned synthetic Prompt Agents.")
    a2a_actions = a2a.add_subparsers(dest="a2a_action", required=True)
    a2a_actions.add_parser("plan")
    a2a_actions.add_parser("inspect")
    for action in ("target", "caller"):
        operation = a2a_actions.add_parser(action)
        operation.add_argument("--confirm-create", action="store_true")
        if action == "caller":
            operation.add_argument(
                "--new-version",
                action="store_true",
                help="Create another owned caller version without deleting the prior version.",
            )
    a2a_invoke = a2a_actions.add_parser("invoke")
    a2a_invoke.add_argument("--label", required=True)
    a2a_invoke.add_argument("--confirm-cost", action="store_true")
    a2a_verify = a2a_actions.add_parser("verify-recorded")
    a2a_verify.add_argument("--label", required=True)
    routines = commands.add_parser(
        "routines", help="Inspect a recorded routine dispatch; response verification is optional."
    )
    routines_actions = routines.add_subparsers(dest="routines_action", required=True)
    routines_inspect = routines_actions.add_parser("inspect")
    routines_inspect.add_argument("--name", required=True)
    routines_inspect.add_argument("--dispatch-id", required=True)
    routines_inspect.add_argument("--label", required=True)
    routines_inspect.add_argument("--verify-response", action="store_true")
    code_tool = commands.add_parser(
        "code-interpreter",
        help="Generate and verify a CSV using only six synthetic policy records.",
    )
    code_actions = code_tool.add_subparsers(dest="code_interpreter_action", required=True)
    code_run = code_actions.add_parser("run")
    code_run.add_argument("--label", required=True)
    code_run.add_argument("--confirm-create", action="store_true")
    code_run.add_argument("--confirm-cost", action="store_true")
    code_cleanup = code_actions.add_parser("cleanup")
    code_cleanup.add_argument("--label", required=True)
    code_cleanup.add_argument("--confirm-delete", action="store_true")
    openapi = commands.add_parser(
        "openapi",
        help="An explicit managed-identity OpenAPI query over the owned synthetic Search index.",
    )
    openapi_actions = openapi.add_subparsers(dest="openapi_action", required=True)
    openapi_actions.add_parser("plan")
    openapi_invoke = openapi_actions.add_parser("invoke")
    openapi_invoke.add_argument("--label", required=True)
    openapi_invoke.add_argument("--confirm-cost", action="store_true")
    return result


def doctor_offline(root: Path, language: str = "ko") -> dict[str, Any]:
    if not (3, 13) <= sys.version_info[:2] < (3, 15):
        raise ValueError("Use Python 3.13 (recommended) or 3.14.")
    documents = load_documents(root, language)
    dev, holdout = load_cases(root, "dev", language), load_cases(root, "holdout", language)
    if {case["case_id"] for case in dev} & {case["case_id"] for case in holdout}:
        raise ValueError("Dev and holdout IDs overlap.")
    if {case["question"] for case in dev} & {case["question"] for case in holdout}:
        raise ValueError("Dev and holdout questions overlap.")
    return {
        "mode": "offline-check",
        "language": language,
        "python": sys.version.split()[0],
        "documents": len(documents),
        "dev_cases": len(dev),
        "holdout_cases": len(holdout),
        "azure_tested": False,
        "result": "PASS",
    }


def cloud_command(root: Path, args: argparse.Namespace) -> dict[str, Any] | None:
    if args.debug:
        print(f"Python executable: {sys.executable}; prefix: {sys.prefix}", file=sys.stderr)
    import httpx
    from azure.core.exceptions import AzureError
    from openai import OpenAIError

    from .cloud import (
        answer_with_context,
        call_model,
        create_prompt_agent,
        doctor_cloud,
        invoke_prompt_agent,
        project_clients,
        retrieve,
    )
    from .settings import Settings, load_environment

    load_environment(root)
    settings = Settings.from_env(language=args.language)
    framework_errors: tuple[type[Exception], ...] = ()
    try:
        if args.command in {"maf", "workflow", "workflow-agent", "maf-evaluate", "serve"}:
            from agent_framework.exceptions import AgentFrameworkException

            framework_errors = (AgentFrameworkException,)
        if args.command == "openapi":
            from . import openapi_lab

            if args.openapi_action == "plan":
                return openapi_lab.plan(settings)
            with project_clients(settings) as (_, client):
                return openapi_lab.invoke(
                    client, root, settings, args.label, confirmed=args.confirm_cost
                )
        if args.command == "code-interpreter":
            from . import code_interpreter_lab

            with project_clients(settings) as (project, client):
                if args.code_interpreter_action == "run":
                    return code_interpreter_lab.run(
                        project,
                        client,
                        root,
                        settings,
                        args.label,
                        confirmed_create=args.confirm_create,
                        confirmed_cost=args.confirm_cost,
                    )
                return code_interpreter_lab.cleanup(
                    project, client, root, settings, args.label, confirmed=args.confirm_delete
                )
        if args.command == "a2a":
            from . import a2a_lab

            if args.a2a_action == "plan":
                return a2a_lab.plan(settings)
            if args.a2a_action == "verify-recorded":
                return a2a_lab.verify_recorded(root, settings, args.label)
            with project_clients(settings) as (project, client):
                if args.a2a_action == "target":
                    return a2a_lab.target(project, root, settings, confirmed=args.confirm_create)
                if args.a2a_action == "caller":
                    return a2a_lab.caller(
                        project,
                        root,
                        settings,
                        confirmed=args.confirm_create,
                        new_version=args.new_version,
                    )
                if args.a2a_action == "inspect":
                    return a2a_lab.inspect(project, root, settings)
                return a2a_lab.invoke(
                    project, client, root, settings, args.label, confirmed=args.confirm_cost
                )
        if args.command == "routines":
            from .routines_lab import inspect_run

            with project_clients(settings, preview=True) as (project, client):
                return inspect_run(
                    project,
                    client,
                    root,
                    settings,
                    args.name,
                    args.dispatch_id,
                    args.label,
                    verify_response=args.verify_response,
                )
        if args.command == "memory":
            from . import memory_lab

            if args.memory_action == "plan":
                return memory_lab.plan(settings)
            with project_clients(settings, preview=True) as (project, client):
                if args.memory_action == "create":
                    return memory_lab.create(project, root, settings, confirmed=args.confirm_create)
                if args.memory_action in {"put", "update"}:
                    return memory_lab.put(
                        project,
                        root,
                        settings,
                        args.scope,
                        args.case,
                        confirmed_write=args.confirm_write,
                        confirmed_cost=args.confirm_cost,
                        memory_id=getattr(args, "memory_id", None),
                    )
                if args.memory_action == "inspect":
                    return memory_lab.inspect_scope(project, root, settings, args.scope)
                if args.memory_action == "recall":
                    return memory_lab.recall(
                        project,
                        client,
                        root,
                        settings,
                        args.scope,
                        args.label,
                        confirmed=args.confirm_cost,
                    )
                if args.memory_action == "forget":
                    return memory_lab.forget(
                        project, root, settings, args.memory_id, confirmed=args.confirm_delete
                    )
                return memory_lab.cleanup(project, root, settings, confirmed=args.confirm_delete)
        if args.command == "conversations":
            from .conversations import collect_live, evaluate_native

            if args.conversation_action == "collect":
                return collect_live(
                    root, settings, args.label, args.prompt, confirmed=args.confirm_cost
                )
            return evaluate_native(
                root,
                settings,
                args.label,
                args.level,
                confirmed=args.confirm_cost,
                timeout=args.timeout,
            )
        if args.command == "toolbox":
            from . import toolbox

            if args.toolbox_action == "plan":
                return toolbox.plan(
                    settings,
                    discovery=args.discovery,
                    skill_version=args.skill_version,
                    pin_policy=args.pin_policy,
                )
            if args.toolbox_action == "serve":
                from .toolbox_host import serve

                serve(root, settings, args.version, with_skill=args.with_skill)
                return None
            with project_clients(settings) as (project, _):
                if args.toolbox_action in {"create", "add-version"}:
                    return toolbox.create_version(
                        project,
                        root,
                        settings,
                        confirmed=args.confirm_create,
                        new_version=args.toolbox_action == "add-version",
                        discovery=args.discovery,
                        skill_version=args.skill_version,
                        pin_policy=args.pin_policy,
                    )
                if args.toolbox_action == "select":
                    return toolbox.select_version(
                        project, root, settings, args.version, confirmed=args.confirm_update
                    )
                if args.toolbox_action == "cleanup":
                    return toolbox.delete_owned(
                        project, root, settings, confirmed=args.confirm_delete
                    )
                binding = toolbox.snapshot(project, settings, args.version)
            if args.toolbox_action == "inspect":
                return binding
            return asyncio.run(
                toolbox.execute(
                    settings,
                    root,
                    binding,
                    args.label,
                    invoke=args.toolbox_action == "ask",
                    confirmed=getattr(args, "confirm_cost", False),
                    with_skill=getattr(args, "with_skill", False),
                    query_only=args.toolbox_action == "query",
                )
            )
        if args.command == "iq-chat":
            from .iq_chat import ask, check, setup

            if args.iq_chat_action == "check":
                return check(root, settings)
            if args.iq_chat_action == "setup":
                return setup(root, settings, confirmed=args.confirm_create)
            return ask(root, settings, args.question, args.label, confirmed=args.confirm_cost)
        if args.command == "runtime-contract":
            from .contracts import digest
            from .profiles import runtime_contract

            contract = runtime_contract(root, settings, runtime_profile(args))
            return {
                "runtime_contract": contract,
                "contract_hash": digest(contract),
                "azure_verified": False,
            }
        if args.command == "calibrate-judge":
            from .benchmark import directory
            from .calibration import calibrate

            return calibrate(
                root,
                settings,
                args.label,
                confirmed=args.confirm_cost,
                timeout=args.timeout,
                reference_catalog=directory(root, args.reference) / "evaluator-catalog.json"
                if args.reference
                else None,
            )
        if args.command == "workflow-agent":
            from .runtime import run_pipeline

            async def execute_workflow():
                return await asyncio.wait_for(
                    run_pipeline(settings, root, args.question, runtime_profile(args)), timeout=240
                )

            return asyncio.run(execute_workflow())
        if args.command == "doctor":
            return doctor_cloud(settings)
        if args.command == "retrieve":
            return retrieve(root, settings, args.question, args.provider)
        if args.command == "seed-search":
            from .search import SearchGateway

            with SearchGateway(settings) as gateway:
                return gateway.seed(
                    root,
                    include_iq=args.iq,
                    confirmed=args.confirm_create,
                    hybrid=args.hybrid,
                    confirm_embedding_cost=args.confirm_cost,
                )
        if args.command == "cloud-evaluate":
            from .cloud_evaluation import evaluate_cloud

            return evaluate_cloud(
                root,
                settings,
                args.label,
                timeout=args.timeout,
                confirmed=args.confirm_cost,
                business_evaluator=args.business_evaluator,
                reference=args.reference,
                retry_failed=args.retry_failed,
            )
        if args.command == "maf-evaluate":
            from .tool_evaluation import evaluate_tool_use

            return asyncio.run(
                evaluate_tool_use(settings, root, timeout=args.timeout, confirmed=args.confirm_cost)
            )
        if args.command in {"maf", "workflow", "serve"}:
            from .agents import run_agent, run_workflow, serve

            if args.command == "maf":
                return asyncio.run(
                    run_agent(settings, root, args.question, tools=args.tools, mcp=args.mcp)
                )
            if args.command == "workflow":
                return asyncio.run(run_workflow(settings, root, args.question, args.pattern))
            serve(settings, root, runtime_profile(args))
            return None
        if args.command == "collect" and args.split == "holdout" and not args.unlock_holdout:
            raise ValueError("Freeze the candidate first, then explicitly pass --unlock-holdout.")
        client_options = (
            {"account_api": True}
            if getattr(args, "api", None) == "account-responses"
            else {}
        )
        with project_clients(settings, **client_options) as (project, client):
            if args.command == "file-search":
                from . import file_search_lab

                name = file_search_lab.agent_name(settings, args.name)
                if args.action == "create":
                    return file_search_lab.create(
                        project,
                        client,
                        root,
                        settings,
                        name,
                        confirmed=args.confirm_create,
                        retain=args.retain,
                    )
                if args.action == "cleanup":
                    return file_search_lab.cleanup(
                        project, client, root, settings, name, confirmed=args.confirm_delete
                    )
                return file_search_lab.ask(client, root, settings, name, args.question, args.label)
            if args.command == "model":
                return {
                    **call_model(client, settings, args.question),
                    "inference_api": args.api,
                }
            if args.command == "prompt-agent":
                from .cloud import agent_reference_path, load_agent_reference, save_agent_reference
                from .settings import owned_prefix

                name = args.name or f"{owned_prefix()}-policy-{settings.language}"
                reference_path = agent_reference_path(root, settings, name)
                if args.action == "create":
                    if reference_path.exists():
                        raise ValueError(
                            "This agent has a saved reference. Invoke it instead, or choose a new owned name."
                        )
                    result = create_prompt_agent(
                        project, settings, root, name, confirmed=args.confirm_create
                    )
                    save_agent_reference(root, settings, result)
                    result["reference_file"] = f"outputs/agents/{name}.json"
                    return result
                version = (
                    args.version or load_agent_reference(root, settings, name)["agent_version"]
                )
                return invoke_prompt_agent(client, name, version, args.question, settings=settings)
            if args.command == "answer":
                context = retrieve(root, settings, args.question, args.retrieval)
                return {
                    **answer_with_context(
                        client, settings, root, args.question, args.prompt, context
                    ),
                    "inference_api": args.api,
                }
            if args.command == "collect":
                from .profiles import retrieval_configuration

                def answer_case(case: dict[str, Any]) -> dict[str, Any]:
                    context = (
                        evidence([], "none")
                        if args.retrieval == "none"
                        else retrieve(root, settings, case["question"], args.retrieval)
                    )
                    return answer_with_context(
                        client, settings, root, case["question"], args.prompt, context
                    )

                return collect(
                    root,
                    label=args.label,
                    split=args.split,
                    prompt_version=args.prompt,
                    retrieval=args.retrieval,
                    mode="live",
                    deployment=settings.deployment,
                    answer_case=answer_case,
                    recoverable_errors=(ValueError, AzureError, OpenAIError, httpx.HTTPError),
                    inference={
                        "project_endpoint": settings.project_endpoint,
                        "api": args.api,
                        "inference_endpoint": settings.openai_endpoint
                        if args.api == "account-responses"
                        else settings.project_endpoint,
                        "max_output_tokens": settings.max_output_tokens,
                        "reasoning_effort": settings.reasoning_effort,
                        "retrieval_configuration": {"provider": "none", "max_documents": 0}
                        if args.retrieval == "none"
                        else retrieval_configuration(
                            RuntimeProfile(retrieval=args.retrieval, language=args.language)
                        ),
                    },
                    candidate=args.candidate,
                    language=args.language,
                )
    except framework_errors as exc:
        cause: BaseException = exc
        for _ in range(4):
            if cause.__cause__ is None:
                break
            cause = cause.__cause__
        raise ValueError(
            f"MAF request failed: {type(exc).__name__}. "
            f"Cause: {type(cause).__name__}: {cause}. "
            "See docs/troubleshooting.md. "
            "No provider/model fallback was used."
        ) from exc
    except (AzureError, OpenAIError, httpx.HTTPError) as exc:
        status = (
            exc.response.status_code
            if isinstance(exc, httpx.HTTPStatusError)
            else getattr(exc, "status_code", None)
        )
        if args.debug and isinstance(exc, httpx.HTTPStatusError):
            print(f"Service error: {exc.response.text[:2000]}", file=sys.stderr)
        raise ValueError(
            f"Azure request failed: {type(exc).__name__}, HTTP {status}. "
            "See docs/troubleshooting.md. "
            "No provider/model fallback was used."
        ) from exc
    raise ValueError("Unsupported cloud command.")


def main(root: Path, argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if hasattr(args, "question") and args.question is None:
        args.question = DEFAULT_QUESTION_EN if args.language == "en" else DEFAULT_QUESTION
    try:
        if hasattr(args, "question"):
            validate_question(args.question)
        if (
            args.command == "collect"
            and args.retrieval == "none"
            and (args.split != "dev" or args.candidate or args.unlock_holdout)
        ):
            raise ValueError(
                "--retrieval none is a dev-only diagnostic, never a candidate or holdout."
            )
        destination = output_path(root, args.output) if getattr(args, "output", None) else None
        if args.command == "doctor" and not args.cloud:
            result = doctor_offline(root, args.language)
        elif args.command == "benchmark":
            from .benchmark_cli import execute

            result = execute(root, args)
        elif args.command == "demo":
            result = offline_demo(root, args.label, args.prompt, language=args.language)
        elif args.command == "retrieve" and args.provider == "local":
            result = local_retrieve(root, args.question, language=args.language)
        elif args.command == "evaluate":
            result = evaluate_run(root, args.label)
        elif args.command == "compare":
            result = compare_runs(root, args.baseline, args.candidate, args.variable)
        elif args.command == "accept":
            result = acceptance_report(root, args.candidate, args.holdout)
        elif args.command == "feedback":
            result = {
                "review_record": str(record_feedback(root, args.label, args.case, args.reason))
            }
        elif args.command == "conversations" and args.conversation_action in {"plan", "report"}:
            from .conversations import business_report, plan

            result = (
                plan(root, args.language, args.prompt)
                if args.conversation_action == "plan"
                else business_report(root, args.label)
            )
        elif args.command == "prepare-extensions":
            from .extension_materials import prepare
            from .settings import load_environment, owned_prefix

            load_environment(root)
            result = prepare(root, args.language, owned_prefix(), args.label)
        elif args.command == "cleanup-plan":
            ledger_path = root / "outputs/azure-objects.json"
            result = {
                "deletes_resources": False,
                "search_ownership": read_json(ledger_path) if ledger_path.exists() else None,
                "required_manual_inventory": [
                    "prompt/hosted agent versions and active sessions",
                    "Foundry model deployments",
                    "Search service and owned index/source/base",
                    "Application Insights / Log Analytics / storage",
                    "separately created Fabric / Work IQ assets, if any",
                ],
                "guide": "docs/15-capstone-cleanup.md",
            }
        else:
            result = cloud_command(root, args)
        if destination is not None and result is None:
            raise ValueError("No JSON result was returned; --output was not written.")
        if result is not None:
            print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
            if destination is not None:
                write_json(destination, result, overwrite=False)
                print(f"Saved JSON: {destination}", file=sys.stderr)
        if args.command in {"evaluate", "accept"} and not result["business_gate_passed"]:
            return 1
        if args.command == "collect" and result["errors"]:
            return 1
        if isinstance(result, dict) and result.get("gate_passed") is False:
            return 1
        return 0
    except (OSError, ValueError, ImportError, TimeoutError, subprocess.SubprocessError) as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            diagnostic = (
                exc.stderr.decode("utf-8", errors="replace")
                if isinstance(exc.stderr, bytes)
                else exc.stderr
            )
            print(f"Command stderr: {diagnostic.strip()}", file=sys.stderr)
        if args.debug:
            traceback.print_exc()
        if isinstance(exc, ImportError):
            print(
                'Install the matching optional dependencies: python -m pip install -e ".[cloud]" or ".[agents,hosted]".',
                file=sys.stderr,
            )
        return 2
