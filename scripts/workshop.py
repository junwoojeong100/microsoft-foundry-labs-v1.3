from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

HELPERS = {
    "package-hosted": "scripts/package_hosted.py",
    "prepare-hosted": "scripts/prepare_hosted_azd.py",
    "export-evaluation": "scripts/export_evaluation.py",
    "resilience": "examples/resilient/workshop.py",
    "package-toolbox": "scripts/package_toolbox.py",
    "verify-toolbox-response": "scripts/verify_toolbox_response.py",
}


def command_arguments(arguments: list[str]) -> tuple[str, list[str], dict[str, str]]:
    args = list(arguments)
    entrypoint = "scripts/workshop.py"
    environment = os.environ.copy()
    while args and args[0] in {"--model-deployment", "--script"}:
        if len(args) < 2 or not args[1].strip() or args[1].startswith("--"):
            raise RuntimeError(f"{args[0]} 뒤에 실제 값을 입력하세요.")
        option, value = args[:2]
        args = args[2:]
        if option == "--model-deployment":
            environment["AZURE_AI_MODEL_DEPLOYMENT_NAME"] = value
        elif value in HELPERS:
            entrypoint = HELPERS[value]
        else:
            raise RuntimeError(f"지원하는 보조 명령: {', '.join(HELPERS)}")
    if entrypoint == "scripts/workshop.py" and not args:
        args = ["--help"]
    if entrypoint == HELPERS["resilience"]:
        for key in (
            "FOUNDRY_HOSTING_ENVIRONMENT",
            "FOUNDRY_PROJECT_ENDPOINT",
            "AZURE_AI_PROJECT_ENDPOINT",
            "AZURE_AIPROJECT_ENDPOINT",
            "APPLICATIONINSIGHTS_CONNECTION_STRING",
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
            "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
            "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
        ):
            environment.pop(key, None)
        environment["OTEL_SDK_DISABLED"] = "true"
    return entrypoint, args, environment


def main() -> int:
    from scripts.selfstudy import validate_runtime_environment, verify_runtime

    verify_runtime()
    entrypoint, args, environment = command_arguments(sys.argv[1:])
    explicit_model = "--model-deployment" in sys.argv[1:]
    validate_runtime_environment(environment, explicit_model=explicit_model)
    if entrypoint != "scripts/workshop.py":
        return subprocess.run(
            [sys.executable, str(ROOT / entrypoint), *args],
            cwd=ROOT,
            env=environment,
            check=False,
        ).returncode
    from foundry_workshop.cli import main as run_workshop

    previous = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    try:
        if explicit_model:
            os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"] = environment[
                "AZURE_AI_MODEL_DEPLOYMENT_NAME"
            ]
        return run_workshop(ROOT, args)
    finally:
        if explicit_model:
            if previous is None:
                os.environ.pop("AZURE_AI_MODEL_DEPLOYMENT_NAME", None)
            else:
                os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"] = previous


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        RuntimeError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
