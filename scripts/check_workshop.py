from __future__ import annotations

import argparse
import ast
import json
import re
import shlex
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def headings(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)', text))
    seen = {}
    for title in re.findall(r"^#{1,6}\s+(.+)$", text, re.MULTILINE):
        title = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", title)
        slug = re.sub(r"[^\w\s-]", "", title.lower()).strip().replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        anchors.add(f"{slug}-{count}" if count else slug)
    return anchors


def check(require_reference: bool) -> dict[str, object]:
    errors = []
    curriculum = json.loads((ROOT / "curriculum.json").read_text(encoding="utf-8"))
    labs = curriculum["steps"]
    if curriculum["version"] != "1.5" or curriculum["pacing"] != "self-paced":
        errors.append("Workshop must be v1.5 and self-paced.")
    if "total_minutes" in curriculum or any("minutes" in item for item in labs):
        errors.append("Self-study must not have a mandatory time budget.")
    if len(labs) != 16 or [item["id"] for item in labs] != [
        f"{number:02d}" for number in range(16)
    ]:
        errors.append("Expected the ordered 00-15 path.")
    if (
        curriculum["canonical_runtime"] != "pinned-v1.2"
        or curriculum["canonical_dataset"] != "hanbit-ko"
    ):
        errors.append(
            "The primary path must use one pinned runtime and Hanbit dataset."
        )
    seen = set()
    introduction = (ROOT / "README.md").read_text(encoding="utf-8")
    for item in labs:
        if not set(item["depends_on"]).issubset(seen):
            errors.append(f"Dependency points forward or does not exist: {item['id']}")
        seen.add(item["id"])
        path = ROOT / item["file"]
        if not path.exists():
            errors.append(f"Missing lab: {item['file']}")
            continue
        text = path.read_text(encoding="utf-8")
        if "**완료 목표:**" not in text or (
            "**시작 조건:**" not in text and item["id"] not in {"00", "14", "15"}
        ):
            errors.append(f"Missing explicit outcome or prerequisites: {item['file']}")
        if item["file"] not in introduction:
            errors.append(f"Lab is not reachable from README: {item['file']}")
        if (
            "7시간" in text
            or "다온테크" in text
            or re.search(r"담당자에게.{0,30}(?:받|요청)", text)
        ):
            errors.append(
                f"Old timed/instructor-provided/alternate-data dependency: {item['file']}"
            )

    documents = (
        list(ROOT.glob("*.md"))
        + list((ROOT / "docs").rglob("*.md"))
        + list((ROOT / "worksheets").glob("*.md"))
    )
    reference = json.loads((ROOT / "v12-reference.json").read_text(encoding="utf-8"))
    source = ROOT / reference["directory"]
    source_url = (
        reference["repository"].removesuffix(".git")
        + "/blob/"
        + reference["commit"]
        + "/"
    )
    checked_links = 0
    source_links = 0
    deferred_links = 0
    for path in documents:
        text = path.read_text(encoding="utf-8")
        fences = re.findall(r"^```", text, re.MULTILINE)
        if len(fences) % 2:
            errors.append(f"Unclosed code fence: {path.relative_to(ROOT)}")
        for target in re.findall(r"!?\[[^\]]*\]\(([^)\n]+)\)", text):
            target = target.split(' "')[0]
            url = urlsplit(target)
            if target.startswith(source_url):
                relative_url = urlsplit(target[len(source_url) :])
                file = (source / unquote(relative_url.path)).resolve()
                is_reference = True
                source_links += 1
            elif url.scheme or url.netloc:
                continue
            else:
                file = (path.parent / unquote(url.path)).resolve() if url.path else path
                is_reference = file.is_relative_to(ROOT / ".reference")
            if not file.exists():
                if is_reference and not require_reference:
                    deferred_links += 1
                    continue
                errors.append(f"Broken link: {path.relative_to(ROOT)} -> {target}")
                continue
            if (
                url.fragment
                and file.suffix == ".md"
                and unquote(url.fragment) not in headings(file)
            ):
                errors.append(f"Broken anchor: {path.relative_to(ROOT)} -> {target}")
            checked_links += 1

    for path in [
        *ROOT.glob("*.py"),
        *(ROOT / "scripts").glob("*.py"),
        *(ROOT / "tests").glob("*.py"),
    ]:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    ET.parse(ROOT / "docs/assets/architecture.svg")

    reference_verified = False
    command_count = 0
    dev, holdout = [], []
    if source.exists():
        result = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout.strip() != reference["commit"]:
            errors.append("Compatibility source commit differs.")
        else:
            reference_verified = True
        dev = [
            json.loads(line)
            for line in (source / "data/evaluation/dev.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        holdout = [
            json.loads(line)
            for line in (source / "data/evaluation/holdout.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        policies = json.loads(
            (source / "data/knowledge/policies.json").read_text(encoding="utf-8")
        )
        if len(dev) != 6 or len(holdout) != 4 or len(policies) != 6:
            errors.append(
                "Expected six Hanbit policies, six dev and four holdout cases."
            )
        if {case["case_id"] for case in dev} & {case["case_id"] for case in holdout}:
            errors.append("Dev and holdout overlap.")
        extensions = source / "docs/ko/labs/extensions"
        mapping = (ROOT / "docs/feature-map.md").read_text(encoding="utf-8")
        for page in extensions.glob("*.md"):
            if f"extensions/{page.name}" not in mapping:
                errors.append(f"v1.2 extension missing from feature map: {page.name}")
        sys.path.insert(0, str(source / "src"))
        from foundry_workshop.cli import parser as original_parser
        from v12 import command_arguments

        for path in documents:
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.startswith("python scripts/workshop.py "):
                    continue
                entry, args, _ = command_arguments(shlex.split(line)[2:])
                if entry == "scripts/workshop.py" and "--help" not in args:
                    try:
                        original_parser().parse_args(args)
                        command_count += 1
                    except SystemExit:
                        errors.append(
                            f"Invalid executable arguments: {path.relative_to(ROOT)}: {line}"
                        )
    elif require_reference:
        errors.append("Compatibility source is required. Run scripts/prepare_v12.py.")
    if errors:
        raise ValueError("\n".join(errors))
    return {
        "workshop_version": curriculum["version"],
        "pacing": "self-paced",
        "canonical_dataset": "hanbit-ko",
        "labs": len(labs),
        "command_contracts_checked": command_count,
        "documents": len(documents),
        "document_links_checked": checked_links,
        "source_links_checked": source_links,
        "deferred_reference_links": deferred_links,
        "reference_commit_verified": reference_verified,
        "dev_cases": len(dev),
        "holdout_cases": len(holdout),
        "azure_tested": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check the self-paced path, prerequisites, command contracts and source links offline."
    )
    parser.add_argument("--require-reference", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.require_reference), ensure_ascii=False, indent=2))
    except (OSError, ValueError, SyntaxError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
