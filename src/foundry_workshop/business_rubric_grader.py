"""Self-contained business-rubric grader for a Foundry code-based custom evaluator (no imports beyond json)."""

import json

DECISIONS = ("answer", "needs_approval", "insufficient_evidence")
FIELDS = ("answer", "decision", "limit_krw", "citations")
CHECKS = ("schema", "decision", "limit_krw", "required_citations", "citations_retrieved")


def _load(value):
    return json.loads(value) if isinstance(value, str) else value


def _valid_answer(answer):
    if not isinstance(answer, dict) or set(answer) != set(FIELDS):
        return False
    if not isinstance(answer["answer"], str) or not answer["answer"].strip():
        return False
    if answer["decision"] not in DECISIONS:
        return False
    limit = answer["limit_krw"]
    if limit is not None and (type(limit) is not int or limit < 0):
        return False
    citations = answer["citations"]
    if not isinstance(citations, list) or any(
        not isinstance(value, str) or not value.strip() for value in citations
    ):
        return False
    return len(citations) == len(set(citations))


def business_checks(item):
    result = dict.fromkeys(CHECKS, False)
    try:
        answer = _load(item.get("answer_json"))
        expected = _load(item.get("ground_truth"))
        source_ids = _load(item.get("source_ids"))
    except (TypeError, ValueError):
        return result
    if (
        not _valid_answer(answer)
        or not isinstance(expected, dict)
        or not isinstance(source_ids, list)
    ):
        return result
    citations = set(answer["citations"])
    result.update(
        schema=True,
        decision=answer["decision"] == expected.get("expected_decision"),
        limit_krw=answer["limit_krw"] == expected.get("expected_limit_krw"),
        required_citations=set(expected.get("required_citations", [])) <= citations,
        citations_retrieved=bool(citations) and citations <= set(source_ids),
    )
    return result


def grade(sample: dict, item: dict) -> float:
    try:
        results = business_checks(item)
    except Exception:
        return 0.0
    return sum(results.values()) / len(results)
