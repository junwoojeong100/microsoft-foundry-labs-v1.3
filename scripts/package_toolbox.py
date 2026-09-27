#!/usr/bin/env python3
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from foundry_workshop.contracts import digest, load_cases, load_documents, write_json  # noqa: E402
from foundry_workshop.packaging import copy_runtime, file_hashes, runtime_dependencies  # noqa: E402
from foundry_workshop.search import search_configuration  # noqa: E402
from foundry_workshop.settings import (  # noqa: E402
    Settings,
    load_environment,
    owned_prefix,
    require_env,
)
from foundry_workshop.toolbox import name_for, require_synthetic_index, version_value  # noqa: E402


def build(root: Path, settings: Settings, version: str, *, with_skill: bool = False) -> Path:
    version = version_value(version)
    require_synthetic_index(root, settings)
    search = search_configuration()
    destination = root / ".build" / f"toolbox-{settings.language}-{version}"
    if destination.exists():
        raise FileExistsError("Preserve the existing exact Toolbox package before rebuilding.")
    edition, dependencies = runtime_dependencies(root)
    source = {
        "kind": "packaged-synthetic-index",
        "language": settings.language,
        "search_endpoint": search["endpoint"],
        "index": search["index"],
        "prefix": owned_prefix(),
        "corpus_hash": digest(load_documents(root, settings.language)),
    }
    profile = {
        "schema_version": 1,
        "kind": "synthetic-toolbox-host",
        "language": settings.language,
        "toolbox_version": version,
        "with_skill": with_skill,
        "source": source,
        "questions": [case["question"] for case in load_cases(root, "dev", settings.language)],
        "evidence_storage": "$HOME/workshop-evidence/toolbox-runs (Hosted session filesystem)",
        "runtime": {
            "project_endpoint": settings.project_endpoint,
            "deployment": settings.deployment,
            "toolbox_name": name_for(settings),
            "search_connection": require_env("TOOLBOX_SEARCH_CONNECTION_NAME"),
        },
    }
    destination.mkdir(parents=True)
    copy_runtime(root, destination)
    shutil.copy2(root / "examples/hosted/toolbox_main.py", destination / "main.py")
    shutil.copy2(root / "examples/hosted/.agentignore", destination / ".agentignore")
    (destination / "requirements.txt").write_text("\n".join(dependencies) + "\n")
    write_json(destination / "toolbox-profile.json", profile)
    files = file_hashes(destination)
    write_json(
        destination / "package-manifest.json",
        {
            "kind": "synthetic-toolbox-package",
            "edition": edition,
            "profile": profile,
            "files": files,
            "cloud_deployed": False,
            "excludes": [
                "credentials",
                ".env",
                "evaluation reference answers",
                "holdout",
                "run outputs",
            ],
        },
    )
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Package a pinned synthetic Toolbox host without deploying or copying answer keys."
    )
    parser.add_argument("--language", choices=("en", "ko"), default="en")
    parser.add_argument("--version", required=True)
    parser.add_argument("--with-skill", action="store_true")
    args = parser.parse_args()
    try:
        load_environment(ROOT)
        print(
            build(
                ROOT,
                Settings.from_env(language=args.language),
                args.version,
                with_skill=args.with_skill,
            )
        )
    except (OSError, ValueError, ImportError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
