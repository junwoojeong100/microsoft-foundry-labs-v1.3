#!/usr/bin/env python3
"""Export an owned routine's native history without dispatching or changing it."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from foundry_workshop.cloud import project_clients  # noqa: E402
from foundry_workshop.contracts import digest, safe_label, write_json  # noqa: E402
from foundry_workshop.settings import Settings, load_environment, owned_prefix  # noqa: E402


def export_runs(project: Any, directory: Path, name: str, prefix: str) -> dict[str, Any]:
    if (
        not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
        or not name.startswith(prefix + "-")
    ):
        raise ValueError("Use the exact routine name under your verified WORKSHOP_PREFIX.")
    directory.mkdir(parents=True, exist_ok=False)
    routine = project.beta.routines.get(name).as_dict()
    write_json(directory / "routine.json", routine, overwrite=False)
    if routine.get("name") != name or type(routine.get("enabled")) is not bool:
        raise ValueError("The returned routine does not match the requested name or enabled state.")
    runs = [item.as_dict() for item in project.beta.routines.list_runs(name, limit=100)]
    write_json(directory / "runs.json", runs, overwrite=False)
    identifiers = []
    for run in runs:
        if not isinstance(run, dict) or any(
            not isinstance(run.get(field), str) or not run[field]
            for field in ("id", "dispatch_id", "status", "phase", "attempt_source")
        ):
            raise ValueError("Malformed native routine history; preserve the original export.")
        identifiers.append(run["id"])
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate native run IDs; do not infer a delivery from this history.")
    summary = {
        "mode": "read-only-native-routine-history",
        "routine_name": name,
        "routine_enabled": routine["enabled"],
        "returned_runs": len(runs),
        "runs_hash": digest(runs),
        "runs": runs,
        "new_model_request": False,
        "routine_changed": False,
        "agent_answer_verified": False,
        "note": (
            "Keep every native attempt, including Killed/cancelled entries. History is not "
            "answer verification. Use the actual dispatch_id with routines inspect; an "
            "empty CLI history is not proof that the timer never fired."
        ),
    }
    write_json(directory / "summary.json", summary, overwrite=False)
    return summary


def main(argv: list[str] | None = None, *, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--label", required=True, help="New export label; never overwrite evidence.")
    args = parser.parse_args(argv)
    cloud_errors: tuple[type[Exception], ...] = ()
    try:
        from azure.core.exceptions import AzureError
        from httpx import HTTPError
        from openai import OpenAIError

        cloud_errors = (AzureError, HTTPError, OpenAIError)
        directory = root / "outputs/routine-runs" / safe_label(args.label)
        if directory.resolve().parent != root.resolve() / "outputs/routine-runs":
            raise ValueError("Export only to a new directory under outputs/routine-runs.")
        load_environment(root)
        settings = Settings.from_env()
        with project_clients(settings, preview=True) as (project, _):
            result = export_runs(project, directory, args.name, owned_prefix())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, ImportError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 2
    except cloud_errors as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
