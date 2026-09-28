# 나의 Foundry 자가 실습 기록 — v1.5

[English](en/workbook.md) | **한국어** · [전체 과정](../README.ko.md)

개인 사본을 `.selfstudy/` 등 비공개 위치에 저장합니다. 실제 ID·관찰만 기록하고 토큰·비밀번호·API key·회사 원문은 넣지 않습니다.

## 출발점

| 항목 | 내 값/확인 |
|---|---|
| Entra tenant / 구독 | |
| 활성 구독 Owner 확인 | |
| 고유 WORKSHOP_PREFIX | |
| 프로젝트 Endpoint / ARM ID의 출처 | |
| 전용 리소스 그룹과 실제 리전 | |
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
| 13 실습 안전/관리 ID/Control Plane 자산 | | | |
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
