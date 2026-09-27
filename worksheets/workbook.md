# 나의 Foundry 자가 실습 기록 — v1.5

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
| 예산과 중단/정리 계획 | |

## 진행 상태

`계획 / 실행 / 검증 / 차단 / 추가 권한 필요 / 설계만 / 정리 완료`를 구분합니다.

| 장 | 실제 상태 | 결과 파일/ID | 다음 행동 |
|---|---|---|---|
| 00 환경 직접 준비 | | | |
| 01 첫 모델 응답 | | | |
| 02 모델/프롬프트/Router | | | |
| 03 Prompt Agent/File Search | | | |
| 04 MAF/함수/MCP/Code Interpreter | | | |
| 05 워크플로/모의 승인·복구 | | | |
| 06 Search/IQ/Hybrid/IQ Chat | | | |
| 07 업무/native 평가 | | | |
| 08 Hosted 로컬/원격 | | | |
| 09 로그/trace/Insights/반복 평가 | | | |
| 10 Toolbox/Skills/OpenAPI/Hosted | | | |
| 11 Memory/A2A/Routines | | | |
| 12 대화/Optimizer/matrix/calibration | | | |
| 13 안전/권한/네트워크 | | | |
| 14 추가 권한 기능 | | | |
| 15 최종 인수/정리 | | | |

## 실습마다 복사할 결과 카드

```text
장/기능:
사용한 프로젝트·agent·정확한 버전:
모델/배포/버전:
지침·데이터·retrieval·API:
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
| 기대 행 수 / 실제 행 수 / 오류 | | |
| 업무 기준 | | |
| native evaluator·judge·원점수 | | |
| trace/calibration | | |
| 남은 문제와 선택 이유 | | |

**인라인/SDK/MAF/Hosted는 다른 대상입니다.** 각자의 실제 결과를 사용합니다.

## 추가 기능 기록

| 항목 | 실제 값/관찰 |
|---|---|
| Skill 원본/readback hash·실제 load | |
| Memory ID·scope·수정/삭제 | |
| A2A target/caller/card/실제 위임 | |
| Routine 이름·dispatch·답변 확인·disabled 상태 | |
| Optimizer target·후보 수·raw judge 입력·결정 | |
| Safety policy 실제 ID·연결·개입/비개입 | |
| 추가 권한이 필요한 기능과 확보/미확보 상태 | |

## 최종 인수

| 항목 | 내 결과 |
|---|---|
| 선택한 최종 대상과 정확한 버전 | |
| holdout 사전 gate | |
| 처음 보는 문항인지 | |
| 기대/실제 행 수·오류·업무/native 품질 | |
| trace/calibration/미검증 영역 | |
| 작은 인수 기준 충족 여부와 이유 | |
| 생산 운영 전 추가 과제 | |

## 내 업무 적용

- 반복되는 문제와 현재 업무 지표:
- 승인된 원문과 갱신 책임자:
- 읽기 전용 도구:
- 사람 승인 없이는 하면 안 되는 동작:
- 반드시 통과해야 할 질문:
- 사용자 인가·네트워크·로그 최소화:
- 비용·오류·rollback·삭제 책임:

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

**생산 운영 승인:** 별도

**아직 남은 과금과 다음 확인:**
