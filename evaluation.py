from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from tools import ROOT
from workshop import (
    WORKSHOP_VERSION,
    Settings,
    WorkshopError,
    ask,
    now,
    read_state,
    sha256,
    write_json,
)

REVIEW_FIELDS = ["id", "query", "response", "expected", "response_id", "pass", "reason"]


def load_cases(path: Path) -> list[dict[str, object]]:
    cases = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise WorkshopError(
                f"{path.name}:{number}: 빈 줄 없이 한 줄에 JSON 한 건씩 작성하세요."
            )
        case = json.loads(line)
        if not isinstance(case, dict) or set(case) != {
            "id",
            "query",
            "expected",
            "critical",
            "requires_tool",
            "requires_citation",
        }:
            raise WorkshopError(
                f"{path.name}:{number}: 평가 데이터 필드가 잘못되었습니다."
            )
        if any(
            not isinstance(case[key], str) or not case[key].strip()
            for key in ("id", "query", "expected")
        ):
            raise WorkshopError(
                f"{path.name}:{number}: id/query/expected가 비어 있습니다."
            )
        if any(
            type(case[key]) is not bool
            for key in ("critical", "requires_tool", "requires_citation")
        ):
            raise WorkshopError(
                f"{path.name}:{number}: 검사 조건은 boolean이어야 합니다."
            )
        cases.append(case)
    if not cases or len({case["id"] for case in cases}) != len(cases):
        raise WorkshopError("평가 데이터가 비어 있거나 ID가 중복되었습니다.")
    return cases


def run_directory(label: str) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}", label):
        raise WorkshopError("label은 1~40자의 영문 소문자/숫자/하이픈이어야 합니다.")
    return ROOT / "outputs" / label


def csv_text(value: str) -> str:
    return "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r")) else value


def review_row(case: dict, result: dict) -> dict[str, str]:
    return {
        "id": csv_text(case["id"]),
        "query": csv_text(case["query"]),
        "response": csv_text(result["answer"]),
        "expected": csv_text(case["expected"]),
        "response_id": result["responses"][-1]["response_id"],
        "pass": "",
        "reason": "",
    }


def evaluate(settings: Settings, dataset: Path, label: str) -> Path:
    cases = load_cases(dataset)
    state = read_state(settings)
    selected = state.selected()
    if selected["stage"] != "tools":
        raise WorkshopError("이 평가 세트는 Lab 04의 tools 버전이 필요합니다.")
    folder = run_directory(label)
    if folder.exists():
        raise WorkshopError(
            f"기존 평가를 덮어쓰지 않습니다. 새로운 label을 사용하세요: {label}"
        )
    folder.mkdir(parents=True)
    manifest = {
        "workshop_version": WORKSHOP_VERSION,
        "status": "error",
        "started_at": now(),
        "dataset_sha256": sha256(dataset),
        "dataset": dataset.name,
        "agent_name": state.agent_name,
        "agent_version": state.selected_version,
        "model": state.model,
        "prompt_sha256": selected["prompt_sha256"],
        "knowledge_sha256": state.knowledge_sha256,
        "count": len(cases),
        "mode": "live",
    }
    write_json(folder / "cases.json", cases)
    manifest["cases_sha256"] = sha256(folder / "cases.json")
    results = []
    try:
        for index, case in enumerate(cases, 1):
            print(f"[{index}/{len(cases)}] {case['id']}")
            result = ask(
                settings,
                case["query"],
                folder / f"response-{index:02d}.json",
                expected_version=state.selected_version,
            )
            results.append(result)
        with (folder / "review.csv").open(
            "w", encoding="utf-8-sig", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
            writer.writeheader()
            writer.writerows(
                review_row(case, result)
                for case, result in zip(cases, results, strict=True)
            )
        with (folder / "foundry-evaluation.jsonl").open(
            "w", encoding="utf-8"
        ) as handle:
            for case, result in zip(cases, results, strict=True):
                handle.write(
                    json.dumps(
                        {
                            "query": case["query"],
                            "response": result["answer"],
                            "ground_truth": case["expected"],
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        manifest["status"] = "completed"
    except WorkshopError as exc:
        manifest["error"] = str(exc)
        raise
    finally:
        manifest["completed_responses"] = len(results)
        write_json(folder / "manifest.json", manifest)
    return folder


def score(label: str) -> dict[str, object]:
    folder = run_directory(label)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    cases = json.loads((folder / "cases.json").read_text(encoding="utf-8"))
    if manifest["cases_sha256"] != sha256(folder / "cases.json"):
        raise WorkshopError("평가 문항 스냅샷이 실행 후 변경되었습니다.")
    if manifest["status"] != "completed" or manifest["completed_responses"] != len(
        cases
    ):
        raise WorkshopError("오류 또는 응답 누락이 있는 평가는 채점할 수 없습니다.")
    with (folder / "review.csv").open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != REVIEW_FIELDS:
            raise WorkshopError("review.csv의 열 이름/순서를 변경하지 마세요.")
        rows = list(reader)
    if len(rows) != len(cases) or len({row["id"] for row in rows}) != len(rows):
        raise WorkshopError("검토 행이 누락·중복되었거나 개수가 다릅니다.")
    by_id = {row["id"]: row for row in rows}
    verdicts = []
    for index, case in enumerate(cases, 1):
        result = json.loads(
            (folder / f"response-{index:02d}.json").read_text(encoding="utf-8")
        )
        if result["status"] != "completed" or result["query"] != case["query"]:
            raise WorkshopError("완료되지 않았거나 질문이 다른 응답이 섞였습니다.")
        for key in (
            "workshop_version",
            "agent_name",
            "agent_version",
            "model",
            "prompt_sha256",
            "knowledge_sha256",
        ):
            if result[key] != manifest[key]:
                raise WorkshopError(f"실행 설정이 다른 응답이 섞였습니다: {key}")
        expected = review_row(case, result)
        row = by_id.get(expected["id"])
        if row is None:
            raise WorkshopError(f"검토 행이 없습니다: {case['id']}")
        for key in REVIEW_FIELDS[:-2]:
            if row[key] != expected[key]:
                raise WorkshopError(
                    f"{case['id']}: pass와 reason 외의 열이 변경되었습니다: {key}"
                )
        if (
            row["pass"] not in {"pass", "fail"}
            or not isinstance(row["reason"], str)
            or not row["reason"].strip()
        ):
            raise WorkshopError(
                f"{case['id']}: pass/fail과 검토 이유를 모두 입력하세요."
            )
        if row["pass"] == "pass":
            if case["requires_tool"] and not any(
                call["name"] == "estimate_trip_cost"
                and call["result"].get("ok") is True
                for call in result["tool_calls"]
            ):
                raise WorkshopError(
                    f"{case['id']}: 실제 계산 도구 성공 기록이 없어 pass로 채점할 수 없습니다."
                )
            if case["requires_citation"] and not result["citations"]:
                raise WorkshopError(
                    f"{case['id']}: 실제 파일 인용이 없어 pass로 채점할 수 없습니다."
                )
        verdicts.append(
            {
                "id": case["id"],
                "pass": row["pass"] == "pass",
                "critical": case["critical"],
                "reason": row["reason"],
            }
        )
    passed = sum(item["pass"] for item in verdicts)
    critical_failures = sum(item["critical"] and not item["pass"] for item in verdicts)
    summary = {
        "scoring": "human_review_with_evidence_checks",
        "agent_version": manifest["agent_version"],
        "total": len(cases),
        "passed": passed,
        "critical_failures": critical_failures,
        "quality_gate": "PASS" if passed == len(cases) else "NOT_READY",
        "production_approved": False,
        "verdicts": verdicts,
    }
    write_json(folder / "score.json", summary)
    return summary
