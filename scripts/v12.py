from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from prepare_v12 import SOURCE, verify_source

ROOT = Path(__file__).resolve().parents[1]
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
            raise RuntimeError(
                f"허용된 보조 스크립트만 실행합니다: {', '.join(HELPERS)}"
            )
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


def main(*, managed: bool = False) -> int:
    if not SOURCE.exists():
        print(
            "먼저 python scripts/prepare_v12.py --install을 실행하세요.",
            file=sys.stderr,
        )
        return 1
    verify_source()
    python = (
        SOURCE
        / ".venv"
        / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    )
    if not python.exists():
        print(
            "호환 가상 환경이 없습니다. python scripts/prepare_v12.py --install을 실행하세요.",
            file=sys.stderr,
        )
        return 1
    entrypoint, args, environment = command_arguments(sys.argv[1:])
    if managed:
        from selfstudy import validate_runtime_environment

        validate_runtime_environment(
            environment,
            explicit_model="--model-deployment" in sys.argv[1:],
        )
    print(f"v1.5 실습 · 고정 v1.2 런타임 · 작업/결과 폴더: {SOURCE}", file=sys.stderr)
    completed = subprocess.run(
        [str(python), entrypoint, *args], cwd=SOURCE, env=environment, check=False
    )
    return completed.returncode


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
