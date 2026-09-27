#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from foundry_workshop.bindings import hosted_binding  # noqa: E402
from foundry_workshop.contracts import write_json  # noqa: E402
from foundry_workshop.settings import Settings, owned_prefix  # noqa: E402


def binding(values: dict, settings: Settings, service: str) -> dict[str, str]:
    return hosted_binding(values, settings.project_endpoint, owned_prefix(), service)


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
