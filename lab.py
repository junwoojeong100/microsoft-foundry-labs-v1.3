from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys

from tools import ROOT, estimate_trip_cost
from workshop import (
    WORKSHOP_VERSION,
    WorkshopError,
    ask,
    ask_model,
    cleanup,
    create_agent,
    exclusive_session,
    load_settings,
    new_output_path,
    read_state,
    select_version,
    write_json,
)


def print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def doctor(live: bool) -> None:
    from evaluation import load_cases

    if not (3, 11) <= sys.version_info[:2] < (3, 15):
        raise WorkshopError("이 실습은 Python 3.11~3.14를 사용합니다. 권장: 3.13.")
    settings = load_settings()
    versions = {}
    for requirement in (ROOT / "requirements.txt").read_text().splitlines():
        name, expected = requirement.split("==")
        installed = importlib.metadata.version(name)
        versions[name] = installed
        if installed != expected:
            raise WorkshopError(
                f"{name}: 설치 {installed}, 실습 기준 {expected}. requirements.txt로 설치하세요."
            )
    load_cases(ROOT / "data/evaluation/dev.jsonl")
    load_cases(ROOT / "data/evaluation/holdout.jsonl")
    if estimate_trip_cost("서울", 2)["total"] != 390000:
        raise WorkshopError("합성 요금 데이터 검사 실패.")
    result = {
        "workshop_version": WORKSHOP_VERSION,
        "local_setup": "PASS",
        "azure_tested": False,
        "agent_tested": False,
        "packages": versions,
    }
    if live:
        response = ask_model(settings, "연결 확인입니다. 한국어로 한 문장만 답하세요.")
        result["azure_tested"] = True
        result["response_id"] = response["response_id"]
        result["answer"] = response["answer"]
    print_json(result)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="보존된 축약 예제. 현재 전체 과정은 scripts/workshop.py를 사용합니다."
    )
    parser.add_argument(
        "--version", action="version", version=f"Foundry workshop v{WORKSHOP_VERSION}"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser(
        "doctor", help="로컬 준비 확인. --live는 실제 모델 1회 호출"
    )
    check.add_argument("--live", action="store_true")
    model = commands.add_parser("model", help="문서와 도구 없는 모델 호출")
    model.add_argument("query")
    create = commands.add_parser(
        "create", help="문서 업로드 및 새 Prompt Agent 버전 생성"
    )
    create.add_argument("--stage", choices=["rag", "tools"], required=True)
    create.add_argument(
        "--prompt", choices=["baseline", "improved"], default="baseline"
    )
    chat = commands.add_parser(
        "ask", help="선택된 정확한 버전으로 질문. 매 질문은 새 대화"
    )
    chat.add_argument("query")
    evaluation = commands.add_parser(
        "evaluate", help="실제 응답 수집 및 빈 사람 검토표 생성"
    )
    evaluation.add_argument("--label", required=True)
    evaluation.add_argument("--dataset", choices=["dev", "holdout"], default="dev")
    review = commands.add_parser(
        "score", help="사람이 작성한 review.csv의 완전성과 근거 확인"
    )
    review.add_argument("--label", required=True)
    commands.add_parser("status", help="선택 버전과 이 실습의 소유 자산 표시")
    use = commands.add_parser("use", help="이 실습에서 만든 버전으로 로컬 선택 변경")
    use.add_argument("--version", required=True)
    remove = commands.add_parser(
        "cleanup", help="기본: 삭제 대상 조회. --confirm agent이름: 기록된 자산만 삭제"
    )
    remove.add_argument("--confirm")
    args = parser.parse_args()

    if args.command == "doctor":
        doctor(args.live)
        return 0
    if args.command == "score":
        from evaluation import score

        print_json(score(args.label))
        return 0
    with exclusive_session():
        return execute(args)


def execute(args: argparse.Namespace) -> int:
    settings = load_settings()
    if args.command == "model":
        result = ask_model(settings, args.query)
        path = new_output_path("model")
        write_json(path, result)
        print(result["answer"])
        print(f"\n기록: {path.relative_to(ROOT)}")
    elif args.command == "create":
        state = create_agent(settings, args.stage, args.prompt)
        print_json(
            {
                "agent_name": state.agent_name,
                **state.selected(),
                "indexed_files": state.indexed_files,
            }
        )
    elif args.command == "ask":
        result = ask(settings, args.query)
        print(result["answer"])
        print_json(
            {
                "agent_version": result["agent_version"],
                "response_id": result["responses"][-1]["response_id"],
                "citations": result["citations"],
                "tool_calls": result["tool_calls"],
                "latency_ms": result["latency_ms"],
                "output_file": result["output_file"],
            }
        )
    elif args.command == "evaluate":
        from evaluation import evaluate

        folder = evaluate(
            settings, ROOT / "data/evaluation" / f"{args.dataset}.jsonl", args.label
        )
        print(f"실제 응답 수집 완료: {folder.relative_to(ROOT)}")
        print(
            "아직 품질 점수가 아닙니다. review.csv의 pass와 reason을 작성한 뒤 score를 실행하세요."
        )
    elif args.command == "status":
        from dataclasses import asdict

        print_json(asdict(read_state(settings, check_knowledge=False)))
    elif args.command == "use":
        print_json(select_version(settings, args.version).selected())
    elif args.command == "cleanup":
        from dataclasses import asdict

        print_json(asdict(cleanup(settings, args.confirm)))
        if args.confirm is None:
            print(
                "조회만 했습니다. 삭제하려면 --confirm에 위 agent_name을 정확히 입력하세요."
            )
        else:
            print(
                "기록된 자산 정리 완료. 포털 생성 자산, 모델 배포, 프로젝트, 로그 저장소는 별도 확인하세요."
            )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        WorkshopError,
        OSError,
        ValueError,
        importlib.metadata.PackageNotFoundError,
        ModuleNotFoundError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
