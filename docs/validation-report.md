# 실제 실행 검증: Sweden Central

**한국어** | [English](en/validation-report.md) · [실습 홈](../README.ko.md)

**2026-09-27~28에 새 전용 환경에서 가이드를 실행했습니다.** 실행·업무 검사·trace는 검증했지만, Search 용량 차단과 평가 서비스의 불일치를 성공으로 바꾸지 않았습니다.

리소스 그룹은 `rg-mf15-jw-0927-e2e`, 리전은 `swedencentral`, 프로젝트는 `mf15-project`입니다. 사용자 요청에 따라 생성 자원을 삭제하지 않았습니다. 개인 구독/테넌트 ID·Endpoint 설정과 원본 결과는 `.selfstudy/`, `.env`, `outputs/`에 보관하며 저장소에 포함하지 않습니다.

## 검증 범위

| 구간 | 실제 결과 |
|---|---|
| 준비·모델 | 새 그룹·Foundry·프로젝트·배포·RBAC 생성. Luna 계정 API/포털 성공, 프로젝트 API 400/500. Sol 프로젝트 호출을 검증하고 명시적으로 선택 |
| 비교 | 같은 계정 Responses API·질문·지침·근거로 Luna/Sol dev 각각 6/6. 지침 baseline/candidate도 각각 6/6이므로 통과율 개선은 입증되지 않음 |
| 파일·도구 | 한·영 File Search 각 6파일과 현행/과거/근거부족 인용 확인. 함수·MCP 실제 실행, Code Interpreter CSV 6행, Skill upload/readback 검증 |
| 워크플로 | 순차·병렬·Group Chat 및 실제 중단/재개 SDK 실행. 모의 승인과 실제 업무 인가를 분리 |
| Hosted | 한·영 실제 버전 배포와 원격 응답. 각각 6건의 Hosted 평가 및 전체 결과 export. 관리 ID를 실제 배포 결과로 식별 |
| 기억·위임 | 한·영 관리형 Memory 조회와 scope 분리, A2A 1.0/JSONRPC 위임. 별도 사용자 인가 검증으로 과장하지 않음 |
| 예약 | 실제 일회 수동 dispatch 완료 후 disabled로 보관. 응답 조회 실패와 미래 timer 미검증을 별도 기록 |
| 운영 | 실제 App Insights 조회로 요청 추적. Insights는 실제 7 trace 분석, 0 finding; 건강 보장은 아님. Continuous 평가 1건 확인 후 Pause |
| 안전 | 11개 기본 보호 설정을 유지한 별도 RAI policy 생성, 별도 Hosted v2의 실제 참조 확인. 정상/경계 응답 확인; 지침 거절을 플랫폼 차단으로 부르지 않음 |
| CI/CD | client secret 없는 전용 MI, 실제 immutable OIDC subject, `main` 전용 Environment. 같은 검증 커밋으로 영문 agent v1 배포·프로젝트 한정 런타임 역할·dev 6/6·세션 중지 완료 |

[GitHub 검사](https://github.com/junwoojeong100/microsoft-foundry-v1.5-labs/actions/runs/36336934973)와 [승인된 OIDC 릴리스](https://github.com/junwoojeong100/microsoft-foundry-v1.5-labs/actions/runs/36337095039)는 커밋 `24ea3be`에서 성공했습니다. 릴리스 artifact의 실제 버전, 6개 응답, 역할 범위, `persistent_files_deleted: false`도 내려받아 대조했습니다. 영상의 CI 장면은 이 릴리스 이전에 녹화한 설정 확인 장면입니다.

## 최종 Hosted 인수

검색 제공자는 **local**, 워크플로는 **sequential**, 모델 API는 **account-chat**, 원격 프로토콜은 **Invocations**로 고정했습니다.

| 근거 | 결과 |
|---|---|
| baseline v1 dev | 12/12 업무 검사, 요청 오류 0 |
| candidate v2 dev | 12/12 업무 검사, 요청 오류 0 |
| 고정 v2 holdout, 한 번만 실행 | 8/8 업무 검사, 요청 오류 0 |
| 서버 측 trace | 12 + 12 + 8 = 32개 실제 export 확인 |
| Judge calibration | 좋은/나쁜 사전 예시 2/2 구분 |
| Native 품질 | Groundedness 통과. D05/H04의 Relevance 경고 보존 |
| 최종 권고 | `review-native-findings`, `deployment_approved: false` |

이 결과는 작은 합성 실습의 인수입니다. 모든 native 점수 통과, 통계적 모델 순위, SLA 또는 생산 운영 승인을 뜻하지 않습니다. 영문 런타임은 별도 dev/smoke로 확인했으며 공통 한국어 holdout을 영문 시험으로 재사용하지 않았습니다.

## 성공으로 표시하지 않은 항목

**Search/IQ/Hybrid 및 Search 기반 Toolbox/OpenAPI:** Basic과 S1은 해당 리전의 `ResourcesForSkuUnavailable`, S2는 서비스 quota `0/0`으로 생성되지 않았습니다. 다른 리전·공유 서비스로 몰래 바꾸지 않았습니다. 로컬 검색 matrix는 별도 경로이며 IQ 검증이 아닙니다.

**Prompt Optimizer:** 실제 instruction-only 실행은 baseline 1.0에서 조기 종료됐지만, 6행 모두 judge context가 생성된 답변 자체였습니다. 잘못된 자기 근거이므로 완벽한 점수나 개선의 증거로 쓰지 않았고 승격하지 않았습니다.

**Red teaming:** UI의 seed 설정은 5였지만 실제 반환은 3행입니다. ASR 100%/`attack_success: true`와 “금지 행동 없음”이라는 원시 설명이 모순됐습니다. 원래 입력도 가려져 있어 해당 집계를 신뢰할 수 있는 공격 성공률로 쓰지 않습니다. 행 수·점수·설명 모두 그대로 보관했습니다.

**추가 제품:** Fabric·Microsoft 365/Work IQ·Agent 365 등의 별도 라이선스/데이터 연결은 구성했다고 주장하지 않습니다. 기존 회사 메일·회의·업무 데이터에는 접근하지 않았습니다.

## 반영한 개선

에이전트 definition의 reasoning과 호출 옵션을 분리했고, 계정 Responses API 선택을 명시화했습니다. 실제 함수 실행 증거, A2A `base_url`과 명시적 버전 복구, 영어 Hosted 준비/capture, 로컬 matrix, 연속 평가 ID export, File Search 무만료 보존 옵션을 추가했습니다. 한·영 문서와 명령을 함께 검사하고, ZIP은 편집 영상만 허용된 위치에서 포함합니다.

**보관:** 리소스·agent 버전·파일·평가·소유권 기록은 유지합니다. 불필요한 실행 세션은 중지하고 일정/모니터는 비활성화했습니다. Memory 항목의 TTL이나 관리형 세션 자체 만료는 영구 보관과 다르며, 저장·로그 등 남는 비용은 계속 확인해야 합니다.

실습 그룹의 Cost Management `ActualCost` 조회에는 아직 게시된 행이 없었습니다. 청구 반영 지연이 있으므로 이를 총비용 0으로 해석하지 않습니다.
