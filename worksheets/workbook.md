# 나의 Foundry 자가 실습 기록 — v1.5

[English](en/workbook.md) | **한국어** · [전체 과정](../README.ko.md)

00장에서 이 파일을 **`.selfstudy/workbook-ko.md`로 다른 이름으로 저장**합니다. 실제 ID·관찰만 기록하고 토큰·비밀번호·API key·회사 원문은 넣지 않습니다.

**한꺼번에 다 채우지 않습니다.** 각 장에서 처음 만든 값만 기록하고, 아직 배우지 않은 칸은 비워 둡니다. 이전 환경이 없다면 보관/이전 자산 항목은 `해당 없음`입니다. 검증 보고서의 ID·점수·완료 상태를 복사하지 않습니다.

## 오늘 멈춘 위치

| 항목 | 내 기록 |
|---|---|
| 실습 폴더의 절대 경로 / 언어 | |
| 마지막으로 확인한 장·절 / 결과 파일 | |
| 다음에 실행할 명령 또는 할 일 | |
| 미해결 오류 / 차단된 기능 | |
| 중지한 서버·예약·세션 / 남는 비용·다음 확인일 | |

재개할 때는 [진행 도움말](../docs/checkpoints.md#다음-날-재개하기)을 따릅니다. 기존 이름으로 생성부터 다시 실행하지 않습니다.

## 출발점

| 항목 | 내 값/확인 |
|---|---|
| Entra tenant / 구독 | |
| 활성 구독 Owner 확인 | |
| 고유 WORKSHOP_PREFIX | |
| 프로젝트 Endpoint / ARM ID의 출처 | |
| 전용 리소스 그룹과 실제 리전 | |
| 새 리전 기본값: North Central US / 실제 새 프로젝트 ID | |
| 이전 환경이 있을 때만: 상태·CI ID·outputs/build 보관 위치와 hash | |
| 삭제를 별도로 선택했을 때만: 정확한 그룹 범위 / 유지한 자산 | |
| 새 NC prefix·언어별 소유 이름·사용하지 않은 label | |
| 현재 원본 commit / 실제 수정 여부 | |
| Python·SDK·azd/확장 버전 | |
| 기본 모델/버전 (GPT-6 Sol / 2026-09-22)과 실제 별칭 | |
| 선택적 비교 모델/버전 (GPT-6 Luna / 2026-09-22)과 실제 별칭 | |
| Judge 모델/버전 (GPT-5.5 / 2026-04-24)과 실제 별칭 | |
| 대상과 judge의 기반 모델·배포 분리 확인 | |
| reasoning effort / 출력 토큰 상한 | |
| 예산과 중단/정리 계획 | |

## 진행 상태

`계획 / 실행 / 검증 / 차단 / 미실행 / 보존 / 정리 완료`를 구분합니다.

| 장 | 실제 상태 | 결과 파일/ID | 다음 행동 |
|---|---|---|---|
| 00 환경 직접 준비 | | | |
| 01 첫 모델 응답 | | | |
| 02 Sol 지침/선택적 Luna 비교/Router | | | |
| 03 Prompt Agent/File Search | | | |
| 04 MAF/함수/MCP/Code Interpreter | | | |
| 05 워크플로/로컬 SDK 모의 승인·중단/재개 | | | |
| 06 Search/IQ/Hybrid/IQ Chat | | | |
| 07 업무/native 평가 | | | |
| 08 Hosted 로컬/원격 | | | |
| 09 로그/trace/Insights/반복 평가 | | | |
| 10 Toolbox/Skills/OpenAPI/Hosted | | | |
| 11 Memory/A2A/Routines | | | |
| 12 대화/Optimizer/matrix/calibration | | | |
| 13 관리형 AI red teaming/실습 안전/관리 ID/Control Plane | | | |
| 14 GitHub OIDC CI/CD | | | |
| 15 최종 인수/정리 | | | |

## 실습마다 복사할 결과 카드

```text
장/기능:
사용한 프로젝트·agent·정확한 버전:
모델/배포/버전:
지침·데이터·retrieval·API:
reasoning·출력 한도:
내가 보낸 실제 질문:
받은 실제 응답/파일:
원문·도구 결과와 대조:
응답/실행/trace ID:
원래 실패·미측정·미지원:
생성/변경한 자산과 역할:
정리/보관 상태:
```

## 역할 지도

| 실제 주체 | Object/principal ID 출처 | 대상·역할·범위 | 실제 작업 결과 |
|---|---|---|---|
| 내 CLI 사용자 | | | |
| 프로젝트 관리 ID | | | |
| Foundry 계정 관리 ID | | | |
| Search 관리 ID | | | |
| Hosted 런타임 ID | | | |
| 추가 CI ID (수행 시) | | | |

## 평가 비교

| 항목 | baseline | candidate |
|---|---|---|
| 대상 구현/agent 버전 | | |
| 실제 label/폴더 | | |
| 모델·코드·지침·데이터 hash | | |
| 원문/retrieval/API/동시성 | | |
| reasoning effort / 출력 상한 | | |
| 기대 행 수 / 실제 행 수 / 오류 | | |
| 업무 기준 | | |
| native evaluator·judge·원점수 | | |
| trace/calibration | | |
| 남은 문제와 선택 이유 | | |

**인라인/SDK/MAF/Hosted는 다른 대상입니다.** 각자의 실제 결과를 사용합니다. Judge는 GPT-6 대상과 기반 모델이 다른 GPT-5.5이며, 대상과 배포도 달라야 합니다. 편향이 모두 사라졌다고 가정하지 않습니다. 기존 label과 원시 결과는 변경하지 않습니다.

## 추가 기능 기록

| 항목 | 실제 값/관찰 |
|---|---|
| Skill 원본/readback hash·실제 load | |
| Memory ID·scope·수정/삭제·기록된 store TTL | |
| A2A target/caller/card/실제 위임 | |
| Routine 이름·dispatch·답변 확인·disabled 상태 | |
| Optimizer target·후보 수·raw judge 입력·결정 | |
| Safety policy 실제 ID·연결·개입/비개입 | |
| 관리형 AI red-team 리전·실제 job/run·요청/반환 수·원래 판정/오류 | |
| Native 영어 target·single-turn/tool-level 범위·`num_turns` 깊이 | |
| 제출 seed/objective 수·실제 요청 수·반환/채점 행 수(각각) | |
| Native evaluator 버전·schema·방향·기준점·`azure_ai_project` | |
| 보완 custom policy-lab 결과 — 관리형 red teaming의 대체물 아님 | |
| GitHub OIDC 주체·workflow run·정확한 배포 버전·artifact | |

## 최종 인수

| 항목 | 내 결과 |
|---|---|
| 선택한 최종 대상과 정확한 버전 | |
| holdout 사전 gate | |
| 처음 보는 문항인지 | |
| 기대/실제 행 수·오류·업무/native 품질 | |
| trace/calibration/미검증 영역 | |
| 작은 인수 기준 충족 여부와 이유 | |
| 이번 합성 실습의 미완료 항목 | |
| 내 관리형 red-team job/label·실제 반환/실패 수·판정 일관성 | |
| Task Adherence / 수행한 경우 Prohibited Actions의 점수·flag·입력 가림·한계 | |

## 다음 실습 비교

- 확인할 합성 질문과 실제 실패:
- 유지할 원문·모델·API·judge 조건:
- 한 가지 바꿀 지침 또는 실습 설정:
- 사용할 읽기 전용 도구:
- 새 baseline/candidate label과 보관할 기존 결과:
- 재검토할 dev 항목:
- 중지·보존 상태와 남는 비용:

## 정리 카드

| 자산/실제 그룹 | 내 소유 확인 | 삭제/보관/중지 상태 | 남는 비용·다음 확인 |
|---|---|---|---|
| Foundry·모델·Prompt/Hosted | | | |
| File Search 원본/저장소 | | | |
| Search index/source/base/service | | | |
| Toolbox/Skills/OpenAPI 연결 | | | |
| Memory/A2A/Routines | | | |
| 평가/Optimizer/반복 일정 | | | |
| Hosted 세션/volume | | | |
| Application Insights/Log Analytics | | | |
| 추가 역할/관리 ID/federation | | | |
| 별도 그룹/이전 시도 | | | |

**학습 수행 상태:**

**최종 품질 판단:**

**아직 남은 과금과 다음 확인:**
