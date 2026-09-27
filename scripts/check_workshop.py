from __future__ import annotations

import ast
import json
import re
import shlex
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from foundry_workshop.cli import parser as runtime_parser  # noqa: E402
from foundry_workshop.contracts import load_cases, load_documents  # noqa: E402
from scripts.selfstudy import argument_parser as setup_parser  # noqa: E402
from scripts.workshop import command_arguments  # noqa: E402

REMOVED_READER_PATTERNS = (
    r"\uac15\uc0ac",
    r"\bv1[.]2\b",
    r"microsoft-foundry-v1[.]2",
    r"[.]reference[/\\]",
    r"prepare_v12",
    r"scripts/v12",
)


def headings(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)', text))
    seen: dict[str, int] = {}
    for title in re.findall(r"^#{1,6}\s+(.+)$", text, re.MULTILINE):
        title = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", title)
        slug = re.sub(r"[^\w\s-]", "", title.lower()).strip().replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        anchors.add(f"{slug}-{count}" if count else slug)
    return anchors


def check() -> dict[str, object]:
    errors: list[str] = []
    curriculum = json.loads((ROOT / "curriculum.json").read_text(encoding="utf-8"))
    steps = curriculum["steps"]
    if curriculum["pacing"] != "self-paced" or curriculum["canonical_runtime"] != "local-package":
        errors.append("The course must be self-paced and use the local runtime.")
    if len(steps) != 16 or [step["id"] for step in steps] != [f"{i:02d}" for i in range(16)]:
        errors.append("The path must contain ordered steps 00-15.")
    if "total_minutes" in curriculum or any("minutes" in step for step in steps):
        errors.append("A mandatory time budget must not be present.")
    introduction = (ROOT / "README.md").read_text(encoding="utf-8")
    seen: set[str] = set()
    for step in steps:
        if not set(step["depends_on"]).issubset(seen):
            errors.append(f"Invalid dependency: {step['id']}")
        seen.add(step["id"])
        path = ROOT / step["file"]
        if not path.is_file():
            errors.append(f"Missing step: {step['file']}")
            continue
        text = path.read_text(encoding="utf-8")
        if "**완료 목표:**" not in text:
            errors.append(f"Missing outcome: {step['file']}")
        if step["file"] not in introduction:
            errors.append(f"Step missing from README: {step['file']}")
    documents = [
        *ROOT.glob("*.md"),
        *(ROOT / "docs").rglob("*.md"),
        *(ROOT / "worksheets").glob("*.md"),
        *(ROOT / "data").rglob("*.md"),
        *(ROOT / "examples").rglob("*.md"),
    ]
    links = 0
    commands = 0
    for path in documents:
        text = path.read_text(encoding="utf-8")
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in REMOVED_READER_PATTERNS):
            errors.append(f"Removed reader-facing wording remains: {path.relative_to(ROOT)}")
        if len(re.findall(r"^```", text, re.MULTILINE)) % 2:
            errors.append(f"Unclosed code fence: {path.relative_to(ROOT)}")
        for target in re.findall(r"!?\[[^\]]*\]\(([^)\n]+)\)", text):
            target = target.split(' "')[0]
            url = urlsplit(target)
            if url.scheme or url.netloc:
                continue
            destination = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not destination.exists():
                errors.append(f"Broken link: {path.relative_to(ROOT)} -> {target}")
            elif (
                url.fragment
                and destination.suffix == ".md"
                and unquote(url.fragment) not in headings(destination)
            ):
                errors.append(f"Broken anchor: {path.relative_to(ROOT)} -> {target}")
            links += 1
        for line in text.splitlines():
            if line.startswith("python scripts/workshop.py "):
                entry, arguments, _ = command_arguments(shlex.split(line)[2:])
                if entry != "scripts/workshop.py":
                    if not (ROOT / entry).is_file():
                        errors.append(f"Missing helper: {entry}")
                    continue
                parser = runtime_parser()
            elif line.startswith("python scripts/selfstudy.py "):
                arguments = shlex.split(line)[2:]
                parser = setup_parser()
            else:
                continue
            if "--help" in arguments:
                continue
            try:
                parser.parse_args(arguments)
                commands += 1
            except SystemExit:
                errors.append(f"Invalid command: {path.relative_to(ROOT)}: {line}")
    policies = load_documents(ROOT)
    dev = load_cases(ROOT, "dev")
    holdout = load_cases(ROOT, "holdout")
    if (len(policies), len(dev), len(holdout)) != (6, 6, 4):
        errors.append("Expected six policies, six dev cases and four holdout cases.")
    if {row["case_id"] for row in dev} & {row["case_id"] for row in holdout}:
        errors.append("Dev and holdout overlap.")
    for policy in policies:
        path = ROOT / "data/policies" / f"{policy['id']}.txt"
        if not path.is_file() or policy["content"] not in path.read_text(encoding="utf-8"):
            errors.append(f"Uploadable policy does not match its canonical content: {policy['id']}")
    for directory in ("src", "scripts", "examples", "tests", "tests_sdk"):
        for path in (ROOT / directory).rglob("*.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    ET.parse(ROOT / "docs/assets/architecture.svg")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    if not (ROOT / "LICENSE").is_file():
        errors.append("The runtime license must be included.")
    if errors:
        raise ValueError("\n".join(errors))
    return {
        "workshop_version": curriculum["version"],
        "package": project["name"],
        "pacing": "self-paced",
        "runtime_included": True,
        "labs": len(steps),
        "documents": len(documents),
        "links_checked": links,
        "command_contracts_checked": commands,
        "reader_wording_check": "PASS",
        "policies": len(policies),
        "dev_cases": len(dev),
        "holdout_cases": len(holdout),
        "azure_tested": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(check(), ensure_ascii=False, indent=2))
    except (OSError, ValueError, SyntaxError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
