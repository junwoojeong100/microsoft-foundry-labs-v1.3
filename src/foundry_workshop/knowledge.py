import re
from pathlib import Path
from typing import Any

from .contracts import digest, load_documents, validate_question


def evidence(
    documents: list[dict[str, Any]],
    provider: str,
    *,
    references: list[dict[str, Any]] | None = None,
    activity: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    ids = []
    normalized = []
    for document in documents:
        if not isinstance(document, dict) or any(
            not isinstance(document.get(key), str) or not document[key].strip()
            for key in ("id", "title", "content")
        ):
            raise ValueError("Retrieved evidence must contain id, title and content strings.")
        ids.append(document["id"])
        normalized.append(
            {key: value for key, value in document.items() if not key.startswith("@")}
        )
    if len(ids) != len(set(ids)):
        raise ValueError("Retrieved evidence contains duplicate source IDs.")
    normalized.sort(key=lambda document: document["id"])
    return {
        "provider": provider,
        "documents": normalized,
        "source_ids": sorted(ids),
        "context_hash": digest(normalized),
        "references": references or [],
        "activity": activity or [],
    }


def local_retrieve(
    root: Path, question: str, top: int = 6, *, language: str = "ko"
) -> dict[str, Any]:
    validate_question(question)
    if not 1 <= top <= 20:
        raise ValueError("top must be between 1 and 20.")
    tokens = set(re.findall(r"[a-z0-9]+|[가-힣]{2,}", question.casefold()))
    scored = []
    for document in load_documents(root, language):
        haystack = (document["title"] + " " + document["content"]).casefold()
        score = sum(token in haystack for token in tokens)
        if score:
            scored.append((score, document["id"], document))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return evidence([item[2] for item in scored[:top]], "local-keyword")
