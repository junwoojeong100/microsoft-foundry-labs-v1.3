# 실제 실행 검증: North Central US

**한국어** | [English](en/validation-report.md) · [실습 홈](../README.ko.md)

**2026-09-28, 새 North Central US 환경에서 실습을 이어서 검증했습니다.** 현재 그룹은 `rg-mf15-jw-nc-0928`, 계정은 `mf15-jw-nc-0928`, 프로젝트는 `mf15-project`입니다. 기본 답변은 GPT-6 Sol / `workshop-chat`, judge는 다른 기반 모델 GPT-5.5 / `workshop-judge`입니다.

이전 Sweden 그룹은 사용자의 명시적 요청으로 삭제했고 부재를 확인했습니다. 삭제 전에 설정·원본 결과·소유권·배포 정보를 `.selfstudy/archives/sweden-20260928-before-northcentral/`에 hash와 함께 보관했습니다. **새 NC 자원은 삭제하지 않습니다.** 아래의 숫자는 해당 실제 실행 범위에만 적용됩니다.

## 현재 NC 결과

| 범위 | 실제 결과와 한계 |
|---|---|
| 기본 환경·모델 | 새 그룹/Foundry/프로젝트, 7개 모델 배포 확인. Sol·Luna·judge·embedding·IQ·Router·Optimizer 역할을 구분 |
| Agent·파일·로컬 도구 | 한·영 Prompt Agent/File Search, 6행 Code Interpreter CSV, 함수/MCP 및 MAF workflow 실행. Group Chat의 종료 한도는 합의 증명이 아님 |
| Search·IQ·Hybrid·IQ Chat | 한·영 별도 workspace/ledger에서 실제 검색, 3072차원 embedding, IQ Chat의 planning/synthesis 확인 |
| SDK dev·calibration | 한·영 dev 6/6 및 calibration 각각 24/24. 영어 최초 5/6 실패와 검색 필터 교정은 별도 기록 |
| Hosted IQ 지침 비교 | 배포 v1/v2 각각 업무 6/6, 세 policy 기준 각각 6/6, trace 6/6. 코드·모델·원문을 고정했고 통과율 향상은 주장하지 않음 |
| 보완 진단 | 배포 v2의 한국어 `policy-lab` 8/8, 규정 위반 0/8, trace 8/8. 관리형 red team이나 새 holdout이 아님 |
| 최종 알려진 사례 재검증 | 같은 v2에서 4/4·policy·trace gate 확인. 이전에 사용한 문항의 회귀 확인이지 새로운 미공개 holdout이 아님. `deployment_approved: false` |
| 관리형 혼합 red team | 원래 6행·5 pass/1 fail 보존. Prohibited Actions의 severity 0/Safe 설명과 fail/attack-success flag가 모순됨 |
| 별도 관리형 Task Adherence | 새 evaluation/run에서 5/5, severity 0·native 문턱 3·`attack_success: false`. 입력 가림과 원래 response ID 미노출을 그대로 기록 |
| Toolbox·Skills·OpenAPI | 실제 한국어 Toolbox v1/v3, Skill v1 로드, OpenAPI 확인. Hosted Toolbox v1은 canonical capture의 최종 SSE와 패키지/hash를 별도로 검증 |
| Memory·A2A·Routine | 한·영 TTL 0 항목 재조회, 한국어 A2A 위임, 실제 예약의 원래 답변 telemetry 확인. `Finished/cancelled`와 별도 `Killed` 시도 모두 보존 |
| Insights | 1시간 창의 16개 trace 분석, finding 1개. 제안은 정답/자동 수정이 아니며 예약은 disabled |
| Continuous | Coherence v1의 초기화 오류·0행 실패 보존. 같은 judge/문턱 3에서 catalog v13을 고정한 별도 실행은 원래 저장 응답 1개와 연결되고 score 5/pass. 두 rule 모두 paused |
| 실습 RAI 정책 | 현재 DefaultV2의 11개 필터를 보존한 전용 정책, 별도 기본 Hosted v2의 실제 참조 확인. 허위 승인 요청에 `needs_approval` 응답; 플랫폼 차단의 증거로 과장하지 않음 |
| 세션 파일 | 성공한 Hosted Toolbox 세션의 JSON 8개를 로컬 회수하고 크기/SHA256을 기록. 원래 HTTP/SSE와 패키지/세션 ID도 보존 |

주요 private 증거는 `outputs/benchmarks/nc-iq-baseline/`, `nc-iq-candidate/`, `nc-policy-lab-ko/`, `nc-known-final-ko/`, `outputs/nc-managed-task-adherence/`, `outputs/nc-observability/`, `outputs/nc-session-archive/`에 있습니다. 영어 검색/평가는 `.selfstudy/nc-en-workspace/`의 별도 소유권입니다. 원본은 공개 bundle에 넣지 않습니다.

## 실제로 수정한 진행 장애

영어 첫 IQ dev는 `SCOPE-01`이 검색 필터에서 빠져 D05의 필수 인용을 충족하지 못했습니다. 문턱 0을 명시한 **새 label**로 6/6을 확인했고, 원래 5/6과 모든 답변/점수는 유지했습니다. 이는 retrieval 변경이지 지침만의 개선이 아닙니다.

Routine의 CLI history는 `value: null`이었지만 native SDK에는 실제 두 시도가 있었습니다. `scripts/routine_runs.py`로 모든 ID를 보관하고 원래 `Finished` 응답을 telemetry로 검증했습니다. 재호출로 대체하지 않았습니다.

관리형 red team의 `scripts/managed_redteam.py`는 taxonomy 검토, 버전/범위 고정, 재개, 실패 시도 보관과 원시 판정 감사를 제공합니다. **새 5/5와 이전 5 pass/1 fail은 다른 job**이며 Prohibited Actions 지표를 수정한 것이 아닙니다.

## 남은 제한과 게시 상태

**Optimizer는 차단 상태입니다.** 실제 NC SDK job은 custom evaluator의 필수 `pass_threshold` 누락으로 실패했습니다. 이름/버전만 받는 SDK 참조 계약과 설치된 azd의 instruction/metadata 사전 검사 문제를 기록했습니다. 평가기를 교체하거나 required 필드를 제거하지 않았고 개선/승격은 없습니다.

새 CI 관리 ID·프로젝트 범위 역할·계정 Reader·immutable 저장소/Environment federation과 main-only 보호를 확인했습니다. **현재 NC 릴리스 run은 게시 후 별도 확인 대상**입니다.

현재 링크된 R2 영상은 아래 Sweden 기록입니다. NC의 새 CLI 녹화는 편집 중이며 **인증된 포털 재녹화는 새 로그인이 필요**합니다. 이전 포털 영상을 NC 증거로 재표시하지 않습니다.

로컬 core 278개·SDK 146개와 Ruff/compile/dependency 검사를 통과했습니다. 이는 실제 모델 품질이나 서비스 제한 해결의 대체물이 아닙니다. 새 자원은 보존하며 Search Basic·저장 파일/volume·로그 비용은 남습니다. Insights의 약 USD 2.01은 서비스의 해당 분석 **추정치**이지 전체 청구액이 아닙니다.

## 이전 Sweden R2 보관 기록

아래는 **그룹 삭제 전 시점**의 기록입니다. “보존”이나 “최종” 표현도 당시 범위이며 현재 NC 상태가 아닙니다. [원래 R2 보고서](https://github.com/junwoojeong100/microsoft-foundry-v1.5-labs/blob/0a8ab50/docs/validation-report.md)와 원본 보관본을 유지합니다.

**2026-09-28 재검증에서 Search 생성과 IQ·Hybrid·연결 도구 실습을 완료했습니다. 기본 모델은 GPT-6 Sol이며, 원문 참조와 업무 목적을 명시한 별도 평가 경로를 검증했습니다.**

리소스 그룹은 `rg-mf15-jw-0927-e2e`, 리전은 `swedencentral`, 프로젝트는 `mf15-project`입니다. 이전 자원과 실패 기록은 삭제하지 않았습니다. 개인 설정·원본 증거는 `.selfstudy/`, `.env`, `outputs/`에 보관하며 저장소에 포함하지 않습니다.

### 1. 이전 제한에 대한 처리 결과

| 항목 | 실제 조치와 검증 |
|---|---|
| Search 생성 | 기존 자원 정리 이후 Basic, replica 1/partition 1, 관리 ID, key 인증 비활성 구성으로 생성 성공 |
| Search·IQ·Hybrid | 한·영 별도 index/소유권 기록에서 키워드, GA IQ, 실제 3072차원 embedding + Hybrid, IQ Chat 계획/합성 모두 실행 |
| Luna 프로젝트 API | 기존 Luna 배포를 변경하지 않고 Sol을 기본으로 명시. 프로젝트 Responses와 실제 에이전트 호출 검증 |
| Judge 분리 | 대상 Sol과 다른 기반 모델 GPT-5.5 사용. 배포 이름만 다른 동일 모델을 독립 judge라고 부르지 않음 |
| Optimizer 자기 근거 | 원본 문서·기대 행동·reference ID를 `ground_truth`에 담고 세 custom 평가기에 연결. 실제 결과 6행 전체와 버전·문턱·참조 일치 검증 |
| Relevance의 보류 응답 감점 | `policy_helpfulness`에서 정당한 보류와 불필요한 거절을 구분. 잘못된 사실은 별도 grounding/compliance에서 실패 |
| Red-team 집계 불일치 | 원래 집계는 수정하지 않음. 입력 원문과 응답 ID가 남는 8개 명시적 진단을 실행하고, 교정된 기준으로 준수 위반율 계산 |
| Memory 보존 | 기존 1시간 저장소는 유지하고 한·영 보존용 저장소를 새로 생성. TTL `0` 조회 확인, 한국어 항목은 4,063초 후에도 조회 성공 |
| Routines 응답 | 원래 수동 실행과 실제 예약 실행 모두 동일 response ID의 agent/version/project/trace 및 원래 답변을 조회. 별도 재호출로 대체하지 않음 |
| 세션 파일 보존 | 중지된 실제 Hosted 세션의 증거 파일을 로컬에 다운로드하고 hash 대조. 세션·volume은 삭제하지 않음 |

실습 환경에서는 기존 Sol 배포 이름 `workshop-compare`와 기존 GPT-5.5 배포 `workshop-optimizer`를 명시적으로 재사용했습니다. 새 학습자가 만드는 기본 별칭과 이름이 달라도 **실제 모델·버전**으로 확인합니다.

### 2. 최종 IQ Hosted 검증

검색은 **실제 Foundry IQ**, 워크플로는 **sequential**, 모델 API는 **account-chat**, 원격 프로토콜은 **Invocations**, 모델은 **Sol**입니다. 로컬 검색으로 성공을 대신하지 않았습니다.

| 실행 | 실제 응답/업무 검사 | 세 policy 평가기 | 실제 trace |
|---|---|---|---|
| IQ Hosted v1 dev | 6/6 | 각각 6/6 | 6/6 |
| IQ Hosted v2 dev | 6/6 | 각각 6/6 | 6/6 |
| 최종 v3 dev | 6/6 | 각각 6/6 | 6/6 |
| 최종 v3 진단 suite v2 | 8/8 | 각각 8/8 | 8/8 |

v1/v2 비교는 같은 코드·모델·원문 조건을 확인했습니다. 둘 다 통과했으므로 통과율 향상이라고 주장하지 않습니다. v3는 후속 진단에서 발견한 응답 계약을 수정한 새 버전입니다.

최종 8개 진단은 요청 8, 반환 8, 누락 0, 요청 오류 0이며 **교정된 policy compliance 기준의 위반은 0/8**입니다. 이것은 이 실습 진단의 결과이며 Microsoft 관리형 Red-team UI의 ASR를 고친 숫자가 아닙니다.

새 진단 suite의 `allowed_citations`는 PL05/PL06/PL07에 한해 근거 있는 보조 인용을 명시합니다. 필수 인용은 여전히 필요하며, 모르는 문서·검색되지 않은 문서·관련 없는 추가 인용은 거부합니다. 절차만 묻는 질문의 `limit_krw`는 `null`입니다. 이전 버전의 실패 행과 frozen dataset은 그대로 남습니다.

**사용 기록:** `outputs/benchmarks/r2-iq-final-dev/`, `outputs/benchmarks/r2-iq-final-lab/`. 이번 진단을 새로운 holdout으로 부르지 않습니다. 이전 holdout은 최초 실행 기록으로만 보존했습니다.

### 3. 평가 입력과 판정의 검증

세 평가기는 `policy_groundedness`, `policy_helpfulness`, `policy_compliance`입니다. 문턱은 **4/5**, 높은 점수가 더 적절한 답변을 뜻합니다.

한·영 각각 정상 답변, 잘못된 금액, 참조 반전, 정당한 보류, 불필요한 거절, 허위 승인, 정상 승인 경계 안내, 가짜 인용의 **8개 control × 3개 기준 = 24/24** 판정이 기대와 일치했습니다. 좋은 예시만 통과시킨 검사가 아닙니다.

원문 참조 envelope의 hash, 결과에 반환된 원문, 판정 설명의 reference ID, 점수/통과 방향을 검사합니다. **서비스 내부 judge 요청 본문을 직접 캡처했다고 주장하지 않습니다.** 참조만 바꿨을 때 같은 답변이 실패하는 counterfactual control도 확인했습니다.

새 Sol Optimizer 실행은 세 기준으로 baseline 1.0을 얻어 조기 종료했고 개선 후보는 생성하지 않았습니다. 원래 입력 6개와 실제 반환 6개, 평가기 버전·문턱·judge·참조는 `scripts/audit_optimizer.py`로 모두 대조했습니다. 따라서 **참조 연결은 검증됐지만 프롬프트 개선 효과나 새 후보 생성은 주장하지 않으며 승격하지 않았습니다.**

### 4. 연결 도구·영문 경로·예약

Toolbox v1에서 실제 Search query와 Sol 답변을 확인했습니다. Tool Search와 Skill 경로에서는 `load_skill`, `tool_search`, `call_tool` 실행을 확인했습니다. 교정한 Skill은 새 버전으로 올리고 원본 다운로드 hash를 검증했으며 기존 버전을 보존했습니다. OpenAPI와 원격 Hosted Toolbox도 실제 Search 결과를 사용했습니다.

영문 경로는 `.selfstudy/r2-en-workspace/`의 별도 prefix/index/ledger를 사용합니다. 한글 index를 영문으로 덮어쓰지 않았습니다. 영문 Sol + IQ dev 6개는 세 policy 평가기 모두 6/6이며, 실제 영어 Search/IQ/Hybrid/IQ Chat/OpenAPI도 수행했습니다.

Routines는 명시적 `action.input`을 사용한 stateless timer로 실행했습니다. 사용자 대화를 넘긴 시도는 `conversation_not_found`였고 실패로 보존했습니다. 예약 완료 후 disable하면 service phase가 `cancelled`로 바뀌는 현상도 기록했습니다. 검증기는 `Finished`와 실제 원래 응답의 완료 trace가 함께 있는 경우에만 완료를 인정하고, 원시 phase를 바꾸지 않습니다.

### 5. 보존과 읽을 때 주의할 점

기존 자원·에이전트 버전·평가·파일·소유권 기록은 삭제하지 않았습니다. 완료된 연산 세션은 중지하고 일정/모니터는 비활성화합니다. Memory/벡터 저장소의 만료 설정과 관리형 세션 수명은 서로 다릅니다. 회수한 파일은 `outputs/r2-session-archive/`에 hash와 함께 보관합니다.

Search Basic, 저장소, 로그 등의 보관 비용은 계속 발생할 수 있습니다. 청구 조회에 게시된 행이 없더라도 총비용 0으로 해석하지 않습니다.

이 보고서의 이전 실패는 새 성공으로 덮어쓴 것이 아닙니다. 최초 리전 용량 오류, Luna 프로젝트 API 오류, 원래 자기 근거 평가, 모순된 ASR, 잘못된 대화 전달, 절차 응답과 인용 계약의 실패를 별도로 보존했습니다. 본 보고서는 **검증한 실습 범위의 최신 결과**를 설명합니다.

### 6. 코드와 CI 재현 확인

로컬 검사 278개와 SDK 검사 124개, Ruff, 양언어 문서·명령·링크 검사를 통과했습니다. [GitHub 검사](https://github.com/junwoojeong100/microsoft-foundry-v1.5-labs/actions/runs/36362144665)와 [승인된 OIDC 릴리스](https://github.com/junwoojeong100/microsoft-foundry-v1.5-labs/actions/runs/36362528860)는 같은 코드 커밋 `5267633`에서 성공했습니다.

릴리스 artifact를 내려받아 **CI agent v2의 영문 실제 응답 6개, 업무 검사 6/6, 현재 runtime code hash 일치, 세션 idle, persistent 파일 비삭제**를 확인했습니다. 이 CI의 로컬 검색 smoke 경로와 위의 별도 IQ Hosted 검증을 혼동하지 않습니다.
