#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from foundry_workshop.contracts import load_documents  # noqa: E402
from foundry_workshop.materials import policy_document_text  # noqa: E402


def export(root: Path, language: str = "ko") -> Path:
    destination = root / "outputs/policy-documents"
    if language != "ko":
        destination = destination / language
    documents = load_documents(root, language)
    destination.mkdir(parents=True, exist_ok=False)
    for document in documents:
        (destination / f"{document['id']}.txt").write_text(
            policy_document_text(document), encoding="utf-8"
        )
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=("ko", "en"), default="ko")
    args = parser.parse_args()
    try:
        print(export(ROOT, args.language))
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
