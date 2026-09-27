#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from foundry_workshop.contracts import write_json  # noqa: E402
from foundry_workshop.settings import Settings, owned_prefix  # noqa: E402


def binding(values: dict, settings: Settings, service: str) -> dict[str, str]:
    prefix = "AGENT_" + re.sub(r"[^A-Z0-9]", "_", service.upper())
    names = {
        "WORKSHOP_HOSTED_AGENT_NAME": prefix + "_NAME",
        "WORKSHOP_HOSTED_AGENT_VERSION": prefix + "_VERSION",
        "WORKSHOP_HOSTED_AGENT_ENDPOINT": prefix + "_INVOCATIONS_ENDPOINT",
    }
    result = {target: values.get(source) for target, source in names.items()}
    if any(
        not isinstance(value, str) or not value or "\n" in value or "\r" in value
        for value in result.values()
    ):
        raise ValueError("The actual azd name/version/Invocations binding is incomplete or unsafe.")
    if result["WORKSHOP_HOSTED_AGENT_NAME"] != service or not service.startswith(
        owned_prefix() + "-"
    ):
        raise ValueError("The deployment returned another agent name.")
    if not result["WORKSHOP_HOSTED_AGENT_VERSION"].isdigit():
        raise ValueError("The deployed version must be the actual numeric version, never latest.")
    endpoint = urlsplit(result["WORKSHOP_HOSTED_AGENT_ENDPOINT"])
    project = urlsplit(settings.project_endpoint)
    if (
        endpoint.scheme != "https"
        or endpoint.netloc != project.netloc
        or endpoint.path != project.path + f"/agents/{service}/endpoint/protocols/invocations"
        or parse_qs(endpoint.query).get("api-version") != ["v1"]
        or endpoint.fragment
    ):
        raise ValueError(
            "The actual Invocations endpoint does not match the intended project and agent."
        )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export only verified, non-secret hosted binding values from azd."
    )
    parser.add_argument("--service", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--github-env", type=Path)
    args = parser.parse_args()
    try:
        process = subprocess.run(
            ["azd", "env", "get-values", "--output", "json"],
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        value = binding(
            json.loads(process.stdout),
            Settings.from_env(language=os.environ.get("WORKSHOP_LANGUAGE", "en")),
            args.service,
        )
        write_json(args.output, value)
        if args.github_env:
            with args.github_env.open("a", encoding="utf-8") as stream:
                for key, content in value.items():
                    stream.write(f"{key}={content}\n")
        print(json.dumps(value, indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
