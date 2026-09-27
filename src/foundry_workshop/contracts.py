import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

DECISIONS = ("answer", "needs_approval", "insufficient_evidence")
ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "decision": {"type": "string", "enum": list(DECISIONS)},
        "limit_krw": {"type": ["integer", "null"]},
        "citations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["answer", "decision", "limit_krw", "citations"],
    "additionalProperties": False,
}


class ModelOutputError(ValueError):
    def __init__(self, message: str, details: dict[str, Any]):
        super().__init__(message)
        self.details = details


def digest(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def code_hash(root: Path) -> str:
    source = root / "src/foundry_workshop"
    if not source.is_dir():
        source = root / "foundry_workshop"
    paths = sorted(source.glob("*.py"))
    if not paths:
        raise ValueError("Cannot fingerprint the workshop source package.")
    return digest({path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON number: {value}")


def parse_json(text: str) -> Any:
    return json.loads(text, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)


def parse_json_prefix(text: str) -> tuple[Any, int]:
    start = len(text) - len(text.lstrip())
    return json.JSONDecoder(
        object_pairs_hook=_unique_object, parse_constant=_invalid_constant
    ).raw_decode(text, start)


def read_json(path: Path) -> Any:
    return parse_json(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any, *, overwrite: bool = True) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w" if overwrite else "x", encoding="utf-8") as output:
        output.write(text)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"{path.name}:{line_number}: empty JSONL row")
        row = parse_json(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path.name}:{line_number}: expected an object")
        rows.append(row)
    if not rows:
        raise ValueError(f"{path.name}: empty dataset")
    return rows


def openai_request_id(response: Any) -> str | None:
    """Return the x-request-id header that the OpenAI SDK attaches to parsed responses.

    The OpenAI Python SDK documents `_request_id` as a public property despite its prefix.
    """
    value = getattr(response, "_request_id", None)
    return value if isinstance(value, str) and value else None


def safe_label(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", value):
        raise ValueError("Label must be 1-48 lowercase letters, digits or hyphens; no paths.")
    return value


def validate_question(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        raise ValueError("Question must contain 1-2000 characters.")
    return value.strip()


@dataclass(frozen=True)
class Answer:
    answer: str
    decision: str
    limit_krw: int | None
    citations: list[str]

    @classmethod
    def from_dict(cls, value: Any) -> "Answer":
        if not isinstance(value, dict) or set(value) != set(ANSWER_SCHEMA["required"]):
            raise ValueError("Answer must have exactly answer, decision, limit_krw and citations.")
        if not isinstance(value["answer"], str) or not value["answer"].strip():
            raise ValueError("Answer text is empty.")
        if value["decision"] not in DECISIONS:
            raise ValueError("Unknown decision.")
        limit = value["limit_krw"]
        if limit is not None and (type(limit) is not int or limit < 0):
            raise ValueError("limit_krw must be a nonnegative integer or null.")
        citations = value["citations"]
        if not isinstance(citations, list) or any(
            not isinstance(item, str) or not item.strip() for item in citations
        ):
            raise ValueError("citations must be a list of nonempty document IDs.")
        if len(citations) != len(set(citations)):
            raise ValueError("Duplicate citations are not allowed.")
        return cls(**value)

    @classmethod
    def from_json(cls, text: str) -> "Answer":
        return cls.from_dict(parse_json(text))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def localized_path(root: Path, relative: str, language: str = "ko") -> Path:
    if language not in {"ko", "en"}:
        raise ValueError("Workshop language must be ko or en.")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Content paths must stay within the workshop.")
    return root / path if language == "ko" else root / path.parent / "en" / path.name


def load_documents(root: Path, language: str = "ko") -> list[dict[str, str]]:
    documents = read_json(localized_path(root, "data/knowledge/policies.json", language))
    if not isinstance(documents, list) or not documents:
        raise ValueError("Knowledge corpus must be a nonempty array.")
    ids = []
    fields = ("id", "title", "content", "effective_from", "effective_to")
    for document in documents:
        if not isinstance(document, dict) or any(
            not isinstance(document.get(key), str) or not document[key].strip() for key in fields
        ):
            raise ValueError("A policy document has missing/invalid fields.")
        if date.fromisoformat(document["effective_from"]) > date.fromisoformat(
            document["effective_to"]
        ):
            raise ValueError("Policy effective dates are reversed.")
        ids.append(document["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("Knowledge corpus has duplicate document IDs.")
    return documents


def load_cases(root: Path, split: str, language: str = "ko") -> list[dict[str, Any]]:
    if split not in {"dev", "holdout"}:
        raise ValueError("Evaluation split must be dev or holdout.")
    cases = read_jsonl(localized_path(root, f"data/evaluation/{split}.jsonl", language))
    return validate_cases(cases, load_documents(root, language))


def validate_cases(
    cases: list[dict[str, Any]], documents: list[dict[str, str]]
) -> list[dict[str, Any]]:
    if not isinstance(cases, list) or not cases:
        raise ValueError("Evaluation cases must be a nonempty list.")
    ids = []
    known_documents = {document["id"] for document in documents}
    for case in cases:
        required = {
            "case_id",
            "question",
            "expected_decision",
            "expected_limit_krw",
            "required_citations",
        }
        if not isinstance(case, dict) or set(case) != required:
            raise ValueError("Evaluation cases must contain exactly the documented case fields.")
        if not isinstance(case.get("case_id"), str):
            raise ValueError("Each case must have a string case_id.")
        safe_label(case["case_id"].lower())
        validate_question(case.get("question"))
        Answer.from_dict(
            {
                "answer": "schema validation",
                "decision": case.get("expected_decision"),
                "limit_krw": case.get("expected_limit_krw"),
                "citations": case.get("required_citations"),
            }
        )
        if not set(case["required_citations"]) <= known_documents:
            raise ValueError(f"Unknown reference document in {case['case_id']}.")
        ids.append(case["case_id"])
    if len(ids) != len(set(ids)):
        raise ValueError("Dataset has duplicate case IDs.")
    return cases


def load_prompt(root: Path, version: str, language: str = "ko") -> tuple[str, str]:
    if version not in {"v1", "v2"}:
        raise ValueError("Prompt version must be v1 or v2.")
    text = localized_path(root, f"prompts/{version}.txt", language).read_text(encoding="utf-8")
    return text, hashlib.sha256(text.encode()).hexdigest()
