from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation import load_cases  # noqa: E402
from tools import RATES, estimate_trip_cost  # noqa: E402


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
    sessions = curriculum["sessions"]
    if curriculum["version"] != "1.5" or curriculum["total_minutes"] != 420:
        errors.append("Workshop version or duration is not v1.5 / 420.")
    if sum(item["minutes"] for item in sessions) != 420:
        errors.append("Session minutes do not sum to 420.")
    labs = [item for item in sessions if "file" in item]
    if len(labs) != 7 or sum(item["minutes"] for item in labs) != 390:
        errors.append("Expected seven labs and 390 teaching minutes.")
    for item in labs:
        path = ROOT / item["file"]
        if not path.exists():
            errors.append(f"Missing lab: {item['file']}")
            continue
        text = path.read_text(encoding="utf-8")
        if f"**{item['minutes']}분" not in text:
            errors.append(f"Duration badge differs: {item['file']}")
        minutes = [
            int(value) for value in re.findall(r"^\| (\d+)분 \|", text, re.MULTILINE)
        ]
        if sum(minutes) != item["minutes"]:
            errors.append(f"Activity minutes differ: {item['file']} ({sum(minutes)})")

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

    dev = load_cases(ROOT / "data/evaluation/dev.jsonl")
    holdout = load_cases(ROOT / "data/evaluation/holdout.jsonl")
    if len(dev) != 6 or len(holdout) != 4:
        errors.append("Expected 6 dev and 4 holdout cases.")
    if {case["id"] for case in dev} & {case["id"] for case in holdout}:
        errors.append("Dev and holdout IDs overlap.")
    current = (ROOT / "data/knowledge/01-travel-current.txt").read_text(
        encoding="utf-8"
    )
    for value in [*RATES["lodging_per_night"].values(), RATES["meal_per_day"]]:
        if f"{value}원" not in current:
            errors.append(f"Policy and rate mismatch: {value}")
    if RATES["policy_id"] not in current or RATES["effective_from"] not in current:
        errors.append("Rate policy ID or effective date does not match the document.")
    if (
        estimate_trip_cost("서울", 2)["total"] != 390000
        or estimate_trip_cost("부산", 2)["total"] != 330000
    ):
        errors.append("Required expected totals do not match.")
    for path in [
        *ROOT.glob("*.py"),
        *(ROOT / "scripts").glob("*.py"),
        *(ROOT / "tests").glob("*.py"),
    ]:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    ET.parse(ROOT / "docs/assets/architecture.svg")

    reference_verified = False
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
        extensions = source / "docs/ko/labs/extensions"
        mapping = (ROOT / "docs/feature-map.md").read_text(encoding="utf-8")
        for page in extensions.glob("*.md"):
            if f"extensions/{page.name}" not in mapping:
                errors.append(f"v1.2 extension missing from feature map: {page.name}")
    elif require_reference:
        errors.append("Compatibility source is required. Run scripts/prepare_v12.py.")
    if errors:
        raise ValueError("\n".join(errors))
    return {
        "workshop_version": curriculum["version"],
        "total_minutes": 420,
        "teaching_minutes": 390,
        "break_minutes": 30,
        "labs": len(labs),
        "feature_cards": len(list((ROOT / "docs/features").glob("[0-9]*.md"))),
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
        description="Check v1.5 documentation, timing, data and source links offline."
    )
    parser.add_argument("--require-reference", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.require_reference), ensure_ascii=False, indent=2))
    except (OSError, ValueError, SyntaxError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
