#!/usr/bin/env python3
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from foundry_workshop.packaging import copy_runtime, file_hashes, runtime_dependencies  # noqa: E402
from foundry_workshop.profiles import PROFILE_FILENAME, RuntimeProfile  # noqa: E402


def build(root: Path, profile: RuntimeProfile | None = None) -> Path:
    profile = RuntimeProfile() if profile is None else profile
    destination = root / ".build" / profile.package_name
    if destination.exists():
        raise ValueError(
            "The hosted package already exists. Preserve or remove that exact generated directory before rebuilding."
        )
    edition, dependencies = runtime_dependencies(root)
    destination.mkdir(parents=True)
    copy_runtime(root, destination)
    for name in ("main.py", ".agentignore"):
        shutil.copy2(root / "examples/hosted" / name, destination / name)
    (destination / PROFILE_FILENAME).write_text(
        json.dumps({"schema_version": 1, "profile": profile.to_dict()}, indent=2) + "\n",
        encoding="utf-8",
    )
    (destination / "requirements.txt").write_text("\n".join(dependencies) + "\n", encoding="utf-8")
    files = file_hashes(destination)
    (destination / "package-manifest.json").write_text(
        json.dumps(
            {
                "edition": edition,
                "files": files,
                "excludes": [
                    ".env",
                    ".foundry",
                    "eval YAML configs",
                    "outputs",
                    "evaluation datasets",
                    "holdout",
                    "virtualenv",
                    "credentials",
                ],
                "dependency_policy": "Direct versions pinned; record resolved dependencies from the actual remote build.",
                "cloud_deployed": False,
                "runtime_profile": profile.to_dict(),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build a secret-free, profile-pinned Hosted package."
    )
    parser.add_argument("--kind", choices=("policy", "workflow"), default="policy")
    parser.add_argument(
        "--pattern", choices=("sequential", "concurrent", "group-chat"), default="sequential"
    )
    parser.add_argument("--retrieval", choices=("local", "search", "iq", "hybrid"), default="local")
    parser.add_argument("--prompt", choices=("v1", "v2"), default="v2")
    parser.add_argument(
        "--api", choices=("project-responses", "account-chat"), default="project-responses"
    )
    parser.add_argument("--protocol", choices=("responses", "invocations"), default="responses")
    parser.add_argument("--language", choices=("ko", "en"), default="ko")
    args = parser.parse_args()
    try:
        print(build(ROOT, RuntimeProfile(**vars(args))))
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
