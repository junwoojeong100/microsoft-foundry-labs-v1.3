import subprocess
from pathlib import Path
from typing import Any

from .contracts import digest, load_cases, safe_label, write_json
from .hosted import HostedBinding, parse_azd_http, validate_request, validate_response
from .profiles import RuntimeProfile, runtime_contract
from .settings import Settings, load_environment, require_env


def smoke(
    root: Path,
    settings: Settings,
    profile: RuntimeProfile,
    *,
    label: str,
    local: bool,
    model_key: str | None,
    case_id: str,
    confirmed: bool,
    azd_directory: Path | None = None,
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("The smoke request calls a paid model; explicitly pass --confirm-cost.")
    if profile.protocol != "invocations":
        raise ValueError("Use the typed Invocations profile for this smoke check.")
    if local and azd_directory is None:
        raise ValueError(
            "Local smoke requires --azd-directory with the prepared standalone azd project. "
            "The source repository's azd state is never selected automatically."
        )
    execution_root = root
    if azd_directory is not None:
        if not local:
            raise ValueError(
                "--azd-directory is only for local smoke; remote smoke uses its exact endpoint."
            )
        if (
            azd_directory.is_symlink()
            or not azd_directory.is_dir()
            or not (azd_directory / "azure.yaml").is_file()
            or (azd_directory / "azure.yaml").is_symlink()
        ):
            raise ValueError(
                "Use the existing standalone azd directory with its regular azure.yaml."
            )
        execution_root = azd_directory.resolve()
    contract = runtime_contract(root, settings, profile)
    selected = model_key or next(
        key for key, value in contract["models"].items() if value == settings.deployment
    )
    cases = load_cases(root, "dev", profile.language)
    case = next((case for case in cases if case["case_id"] == case_id), None)
    if case is None:
        raise ValueError("Smoke checks use a bundled dev case, never holdout.")
    path = root / "outputs/smoke" / safe_label(label)
    path.mkdir(parents=True, exist_ok=False)
    payload = validate_request(
        {
            "question": case["question"],
            "case_id": case_id,
            "model_key": selected,
            "run_id": safe_label(label),
        },
        contract["models"],
    )
    request_file = path / "request.json"
    write_json(request_file, payload)
    command = [
        "azd",
        "--cwd",
        str(execution_root),
        "ai",
        "agent",
        "invoke",
        "--input-file",
        str(request_file),
        "--output",
        "raw",
        "--timeout",
        "270",
        "--new-session",
        "--no-prompt",
    ]
    if local:
        command.extend(
            [
                require_env("WORKSHOP_HOSTED_AGENT_NAME"),
                "--local",
                "--protocol",
                "invocations",
            ]
        )
        binding = None
    else:
        binding = HostedBinding.from_env(settings)
        command.extend(["--agent-endpoint", binding.endpoint, "--version", binding.version])
    process = subprocess.run(command, capture_output=True, check=False, timeout=300)
    (path / "response.http").write_bytes(process.stdout)
    (path / "azd-stderr.txt").write_bytes(process.stderr)
    if process.returncode:
        raise ValueError(
            f"azd smoke failed with exit {process.returncode}; inspect {path}. No fallback was used."
        )
    result, warning = parse_azd_http(process.stdout)
    validate_response(result, payload, contract)
    write_json(path / "response.json", result)
    write_json(
        path / "receipt.json",
        {
            "local": local,
            "azd_directory": str(execution_root),
            "binding": binding.to_dict() if binding else None,
            "request_hash": digest(payload),
            "response_hash": digest(result),
            "runtime_contract_hash": digest(contract),
            "azd_notice": warning,
            "deployment_approved": False,
        },
    )
    return {
        "local": local,
        "answer": result["answer"],
        "response_id": result["response_id"],
        "response_model": result["response_model"],
        "trace_id": result["trace_id"],
        "evidence_directory": str(path),
        "azd_notice": warning,
        "note": "Stop only this smoke session after reviewing its raw response/session headers.",
    }


def execute(root: Path, args) -> dict[str, Any]:
    from . import benchmark
    from .cli import runtime_profile
    from .observability import monitor_matrix, stop_matrix_session, write_trace_plan

    action = args.benchmark_action
    if action == "compare":
        return benchmark.compare_matrices(root, args.baseline, args.candidate)
    if action == "report":
        return {"report": str(benchmark.report_matrix(root, args.label)), "azure_called": False}
    if action == "regression":
        if not args.confirm_review:
            raise ValueError(
                "Review the original dev evidence and explicitly pass --confirm-review."
            )
        path = benchmark.approve_regression(
            root, args.label, args.row_id, args.regression_label, args.reviewer, args.reason
        )
        return {"regression": str(path), "production_approval": False}
    if action == "trace-plan":
        return write_trace_plan(root, args.label)
    if action == "verify":
        return benchmark.verify_release(
            root,
            args.baseline,
            args.candidate,
            args.holdout,
            require_native=args.require_native,
            require_traces=args.require_traces,
            calibration_label=args.calibration,
            require_native_pass=args.require_native_pass,
            require_regressions=args.require_regressions,
        )
    load_environment(root)
    if action == "monitor":
        return monitor_matrix(root, args.label)
    settings = Settings.from_env(language=args.language)
    if action == "plan":
        profile = runtime_profile(args)
        if profile.protocol != "invocations":
            raise ValueError("The evaluation matrix uses the typed Invocations profile.")
        contract = runtime_contract(root, settings, profile)
        count = len(load_cases(root, "dev", profile.language)) * len(contract["models"])
        multiplier = 1 if profile.kind == "policy" else 3 if profile.pattern == "sequential" else 4
        return {
            "azure_called": False,
            "runtime_contract": contract,
            "contract_hash": digest(contract),
            "dev_rows": count,
            "logical_model_calls_per_dev_matrix": count * multiplier,
            "native_evaluation_items": count * 2,
            "holdout_opened": False,
            "note": "Logical counts exclude retries/retrieval/judge internals. Verify actual deployments and costs before collection.",
        }
    import httpx
    from azure.core.exceptions import AzureError
    from openai import OpenAIError

    try:
        if action == "collect":
            return benchmark.collect_matrix(
                root,
                settings,
                runtime_profile(args),
                HostedBinding.from_env(settings),
                label=args.label,
                split=args.split,
                model_keys=args.model_key,
                concurrency=args.concurrency,
                confirmed=args.confirm_cost,
                candidate=args.candidate,
                unlock_holdout=args.unlock_holdout,
                regressions=args.regressions,
                recoverable_errors=(ValueError, AzureError, httpx.HTTPError, TimeoutError),
            )
        if action == "smoke":
            return smoke(
                root,
                settings,
                runtime_profile(args),
                label=args.label,
                local=args.local,
                model_key=args.model_key,
                case_id=args.case,
                confirmed=args.confirm_cost,
                azd_directory=args.azd_directory,
            )
        if action == "evaluate":
            return benchmark.evaluate_matrix(
                root,
                settings,
                args.label,
                confirmed=args.confirm_cost,
                timeout=args.timeout,
                reference=args.reference,
                retry_failed=args.retry_failed,
            )
        if action == "stop-session":
            return stop_matrix_session(root, settings, args.label)
    except (AzureError, OpenAIError, httpx.HTTPError) as exc:
        raise ValueError(
            f"Selected Azure operation failed: {type(exc).__name__}. No model, endpoint or fixture fallback was used."
        ) from exc
    raise ValueError("Unknown benchmark action.")
