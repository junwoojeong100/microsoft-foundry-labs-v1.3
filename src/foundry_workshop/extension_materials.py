import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any

from .contracts import digest, load_cases, load_documents, load_prompt, safe_label, write_json

CONVERSATIONS = (
    ("dates-and-approval", ("D01", "D02", "D03")),
    ("scope-and-boundaries", ("D04", "D05", "D06")),
)


def files_for(root: Path, language: str, prefix: str, *, policy: bool = False) -> dict[str, bytes]:
    if not re.fullmatch(r"lab-[a-z0-9]+(?:-[a-z0-9]+)*", prefix) or len(prefix) > 32:
        raise ValueError("Use the same owned WORKSHOP_PREFIX as the prepared environment.")
    documents = load_documents(root, language)
    cases = load_cases(root, "dev", language)
    prompt, prompt_hash = load_prompt(root, "v2", language)
    by_id = {case["case_id"]: case for case in cases}
    expected_ids = [case_id for _, identifiers in CONVERSATIONS for case_id in identifiers]
    if set(by_id) != set(expected_ids) or len(cases) != len(expected_ids):
        raise ValueError(
            "The conversation plan must account for exactly the six canonical dev cases."
        )
    source = {
        "kind": "derived-extension-materials",
        "language": language,
        "prefix": prefix,
        "dataset_split": "dev",
        "dataset_hash": digest(cases),
        "corpus_hash": digest(documents),
        "prompt_hash": prompt_hash,
        "holdout_loaded": False,
        "target_responses_generated": False,
        "azure_requests_sent": False,
    }
    conversation_plan = {
        **source,
        "conversations": [
            {
                "conversation_id": identifier,
                "turns": [
                    {"case_id": case_id, "question": by_id[case_id]["question"]}
                    for case_id in identifiers
                ],
            }
            for identifier, identifiers in CONVERSATIONS
        ],
    }
    optimizer_rows = []
    for case in cases:
        optimizer_rows.append(
            {
                "case_id": case["case_id"],
                "query": case["question"],
                "context": json.dumps(documents, ensure_ascii=False),
                "ground_truth": json.dumps(
                    {
                        key: case[key]
                        for key in ("expected_decision", "expected_limit_krw", "required_citations")
                    },
                    ensure_ascii=False,
                ),
            }
        )
    if policy:
        from .policy_evaluation import POLICY_MODE, criteria_hash, optimizer_items

        optimizer_rows = optimizer_items(root, language)
        source.update(policy_mode=POLICY_MODE, policy_criteria_hash=criteria_hash())
    table = io.StringIO(newline="")
    writer = csv.DictWriter(
        table,
        fieldnames=("id", "title", "effective_from", "effective_to", "content"),
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(documents)
    skill_name = f"{prefix}-policy-review-{language}"
    description = (
        "Review only bundled synthetic travel-policy evidence before drafting guidance."
        if language == "en"
        else "번들 합성 출장 규정 근거를 검토하고 안내문을 작성합니다."
    )
    boundary = (
        "This skill describes a procedure, not a policy source. Retrieve the original synthetic documents through the approved policy tool. Never run scripts or external business actions."
        if language == "en"
        else "이 skill은 절차이며 정책 원본이 아닙니다. 승인된 정책 도구로 합성 원문을 조회합니다. 스크립트나 외부 업무 변경을 실행하지 않습니다."
    )
    skill = f"---\nname: {skill_name}\ndescription: {description}\n---\n\n{boundary}\n\n{prompt.rstrip()}\n"
    files = {
        "SOURCE.json": (json.dumps(source, indent=2) + "\n").encode(),
        "conversation-plan.json": (
            json.dumps(conversation_plan, ensure_ascii=False, indent=2) + "\n"
        ).encode(),
        "optimizer-dev.jsonl": "".join(
            json.dumps(row, ensure_ascii=False) + "\n" for row in optimizer_rows
        ).encode(),
        "policy-records.csv": table.getvalue().encode("utf-8-sig"),
        "policy-review/SKILL.md": skill.encode(),
    }
    if policy:
        from .policy_evaluation import (
            POLICY_EVALUATORS,
            owned_evaluator_name,
            policy_evaluator_version,
        )

        files["policy-evaluator-definitions.json"] = (
            json.dumps(
                {
                    metric: policy_evaluator_version(owned_evaluator_name(prefix, metric), metric)
                    for metric in POLICY_EVALUATORS
                },
                ensure_ascii=False, indent=2,
            ) + "\n"
        ).encode()
    files["manifest.json"] = (
        json.dumps(
            {
                **source,
                "skill_name": skill_name,
                "files": {
                    name: {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
                    for name, content in sorted(files.items())
                },
                "note": "Optimizer reference fields are evaluator inputs, never target-agent messages. These files are not live results.",
            },
            indent=2,
        )
        + "\n"
    ).encode()
    return files


def prepare(
    root: Path, language: str, prefix: str, label: str, *, policy: bool = False
) -> dict[str, Any]:
    files = files_for(root, language, prefix, policy=policy)
    destination = root / "outputs" / safe_label(label)
    destination.mkdir(parents=True, exist_ok=False)
    for name, content in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    result = {
        "mode": "local-materials",
        "language": language,
        "directory": str(destination),
        "files": sorted(files),
        "azure_requests_sent": False,
        "holdout_loaded": False,
        "policy_evaluators": policy,
        "note": "Prepared inputs only. No agent response, evaluation, deployment or recording has been performed.",
    }
    write_json(destination / "preparation.json", result)
    return result
