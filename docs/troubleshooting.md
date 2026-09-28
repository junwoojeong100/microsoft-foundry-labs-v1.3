# 문제 해결 — 같은 오류에 재생성부터 하지 않기

**현재 장, 마지막 성공, 실제 대상/버전, 오류 원문을 기록합니다.** 비밀번호·토큰·API key·회사 데이터는 기록하거나 공유하지 않습니다.

현재 대상은 **새 North Central US 프로젝트**입니다. 혼합 native job의 6행·5 pass/1 fail과 별도 Task Adherence-only job의 5/5를 구분하며 Prohibited Actions 설명/flag 불일치는 남습니다. [현재 실행 결과](validation-report.md)와 역사적 Sweden 사례를 구분합니다.

| 증상 | 먼저 확인할 것 | 다음 행동 |
|---|---|---|
| Python/패키지 오류 | `.venv`의 Python 3.13인가 | 00의 환경 활성화/설치. 루트 축약 예제 SDK와 혼합 금지 |
| `az`/`azd`/Foundry 명령 없음 | 도구와 `microsoft.foundry` 확장 | 00/08의 설치. 기존 동작 환경을 무조건 업그레이드하지 않음 |
| configure에 계정 ARM ID 입력 | `/projects/...`까지 있는가 | 프로젝트 JSON View의 실제 id 복사 |
| Endpoint 불일치 | 모델 URL, 다른 계정/프로젝트 URL인가 | 같은 프로젝트 홈의 Endpoint와 실제 customSubDomainName 대조 |
| `.env`/셸 설정 충돌 | 과거 export가 우선하는가 | 해당 변수 해제 또는 새 터미널. 다른 프로젝트로 자동 전환하지 않음 |
| 401/로그인 만료 | 사용자·tenant·구독 일치 | 정상 로그인/MFA. 토큰 복사나 client secret 생성으로 우회 금지 |
| Owner인데 모델/agent 403 | Foundry 데이터 역할 | 본인/실제 서비스 ID의 Foundry User와 범위 확인 |
| Search 403 | RBAC 인증, 실제 caller, 데이터 역할 | 내 사용자·프로젝트 MI·계정 MI·Search MI를 구분. key 인증을 켜서 우회하지 않음 |
| Search `ResourcesForSkuUnavailable` | 새 NC의 실제 리전·SKU 가용성 | Sweden의 실패 후 성공은 과거 사례. NC는 별도로 확인하고 조건 변경 뒤 제한적으로 재시도. 이전 리전이나 결과로 자동 전환하지 않음 |
| Search `ServiceQuotaExceeded`, `0 out of 0` | 해당 SKU의 현재 구독 quota | 과거 S2 오류를 현재 Basic의 차단으로 해석하지 않음. 실제 quota가 부족하면 정상 요청 절차를 사용하고 역할 추가·자동 SKU 상승·임의 삭제로 우회하지 않음 |
| Toolbox 목록은 되는데 query 실패 | downstream Search 접근 | 프로젝트 MI의 Index Data Reader와 필요한 Service Contributor 확인 |
| Toolbox가 정상 keyless 연결의 인증 enum을 거부 | 현재 SDK의 `ProjectManagedIdentity`와 이전 `AAD` 표현 | `AAD`만 유효하다고 가정하지 않음. 프로젝트 MI와 실제 대상/역할을 확인하며 API key로 바꾸지 않음. 일반 v1은 수정 후 probe/query/ask 통과 |
| OpenAPI만 실패 | 계정 MI인가, API 버전 인자인가 | `openapi plan`의 주체와 내부 오류 확인. Toolbox ID와 다름 |
| Hosted만 403 | `instance_identity.principal_id` 역할 | 로컬 로그인 반복 대신 실제 원격 ID에 필요한 역할 |
| NC Function 표의 no를 보고 MAF 전체를 단정 | 관리형 Agent Service 도구와 로컬 모델/함수 경로 구분 | NC의 FoundryChatClient + 로컬 `lookup_policy`와 MCP는 실제 성공. 이 결과는 모든 관리형 Function 도구 지원 보장이 아니며 [04](04-tools.md)의 실제 경로/결과를 구분 |
| 모델/버전/지역 제공 안 됨 | 실제 가용성·quota | 정식 quota 요청 또는 명시적 새 계획. 실행 중 몰래 모델 교체 금지 |
| 과거 GPT-6 Luna 프로젝트 `reasoning.effort` 400 / 500 | 계정 API·포털 성공과 프로젝트 API는 별개 | 현재 첫 경로는 Sol로 시작. 선택적 Luna 비교는 02/07에서 두 모델 모두 `account-responses`로 고정. 이 과거 오류를 재현하려고 설정 제거·재생성을 반복하지 않음 |
| `Not allowed when agent is specified`, `param: reasoning` | 저장 버전의 definition과 호출 본문 | reasoning은 definition에만 저장. `agent_reference` 요청에서 중복 전달하지 않음 |
| 모델 배포 이름은 맞는데 configure가 거부 | 실제 기반 모델/버전이 다름 | 기본은 GPT-6 Sol / 2026-09-22. 기존 Sol 별칭이 `workshop-compare`이면 명시적으로 재사용하고 기존 이름의 모델은 변경하지 않음 |
| `incomplete` / 텍스트가 비어 있음 | reasoning이 출력 예산을 소진했는가 | `WORKSHOP_REASONING_EFFORT=low`, `WORKSHOP_MAX_OUTPUT_TOKENS=32768`와 원래 incomplete_details 확인 |
| 도구 후 `encrypted reasoning` / replay 오류 | stateless 도구 결과와 reasoning 항목의 연결 | 고정 requirements 환경과 코드의 명시적 encrypted-content include 확인. reasoning을 임의로 제거하지 않음 |
| 모델/생성 설정 변경 후 agent 참조 거부 | 저장한 agent 버전과 현재 조건이 다름 | 기존 결과를 보존하고 새 소유 이름으로 agent 생성. 최신 버전 자동 선택 금지 |
| File Search 포털 업로드가 보이지 않음 | UI·모델·지역 제공 차이 | 03의 SDK 생성/조회 경로를 사용하고 실제 File Search call과 인용을 확인 |
| 429 | 공유 한도·동시 요청 | 중단/대기 후 제한적 재시도. 전후 평가 조건을 유지 |
| Provider 등록/Policy 거부 | Subscription의 provider와 조직 정책 | Owner로 가능한 등록은 Portal 절차 사용. 상위 정책 우회 금지 |
| 접근 차단/timeout | 조직에서 허용한 실행 환경과 원래 오류 | 승인된 담당 절차로 해결. 공유 방화벽이나 인증서 보호를 낮추지 않음 |
| File Search 버튼/인용 없음 | 모델·지역·도구 설정·인덱싱 | 인라인 답변을 검색 성공으로 바꾸지 않음 |
| 과거/현행 혼동 | 질문 날짜와 적용 기간 | 원문 120,000/150,000원 구분, 실제 실패 기록 |
| Search 기능 과금 오류 | Semantic/Knowledge retrieval 각각의 플랜 | Free 기능과 Basic 서비스 비용을 구분하고 추가 지출을 결정 |
| Hybrid schema/차원 오류 | 실제 embedding 차원과 새 index | 0 벡터/잘라낸 벡터 금지. 기존 index를 덮어쓰지 않음 |
| IQ Chat check 실패 | 고정 모델/버전·Search MI·역할 | 지원 조건을 해결하거나 해당 preset 차단으로 기록 |
| label/파일/패키지가 이미 존재 | 이전 실제 결과인가 | 먼저 읽고, 새 요청/패키지에는 새 이름/경로. 실패 삭제 금지 |
| 영어 IQ dev의 D05에서 `SCOPE-01` 누락 | 원래 반환 문서와 reranker 필터 | 06의 합성 corpus용 문턱 0을 명시하고 새 label에서 전체 dev를 확인. 기존 5/6과 원문은 보존하며 인용 기준을 낮추지 않음 |
| benchmark/SDK 비교의 `code_hash` 불일치 | 지침 외에 결합된 코드가 바뀌었는가 | 실제 r2 SDK 전후 쌍도 이 이유로 올바르게 거부됨. 개별 candidate 점수와 지침만의 개선 주장을 구분하고 코드 동결 후 새 전후 쌍을 수집. hash 편집·검사 완화 금지 |
| judge/Optimizer 결과 누락 | evaluator 목록·전체 행·실제 입력 | 부분 결과로 통과 처리하지 않음 |
| Continuous Coherence v1의 `is_reasoning_model` 초기화 오류 | 실제 catalog 버전과 서비스 evaluator ABI | NC에서는 같은 judge/문턱을 유지한 별도 v13 실행이 1/1 통과. v1의 0행 실패와 원래 응답은 보존하고 두 rule 모두 pause. 다른 evaluator 버전까지 일괄 변경하지 않음 |
| NC Optimizer의 `MissingRequiredParameter: pass_threshold` | SDK job의 evaluator 초기화 계약 | 12의 실제 실패를 보존. Required 필드 삭제·rubric/문턱 완화·다른 evaluator로 교체해 성공을 만들지 않음 |
| Optimizer의 `details.job_id` 로컬 오류 | `poller.details`는 mapping인가 | SDK 2.6.1은 `details["job_id"]`. 서버 job이 이미 존재할 수 있으므로 기존 target/job ID를 조회하고 생성부터 반복하지 않음 |
| 이전 legacy Groundedness Optimizer가 baseline 1.0에서 종료 | 그 이전 실행의 judge `context`가 원문인가 | `context=response`였던 과거 실패를 보존. 현재 policy 기준은 1~5·4 이상 통과이며, 이 legacy 경고를 새 job 결과로 옮기지 않음 |
| 관리형 AI red teaming의 리전 설명 불일치 | 공식 리전 표와 개념 개요를 둘 다 확인 | 표는 East US 2/NC, 개요는 France/Sweden/Switzerland West도 포함. NC는 공통이지만 Sweden 미지원이나 ASR의 리전 원인은 확정하지 않음. [13](13-governance.md) 참조 |
| 이전 Sweden Red-team ASR과 설명이 모순 | 원점수·`attack_success`·요청/반환 수와 판정 의미 | 검증되지 않은 native ASR로 보존. Custom 8/8이나 NC 이전이 지표 방향을 고쳤다고 하지 않고 실제 NC job을 별도 확인 |
| Taxonomy 생성 예제의 `body=`가 오류 | 설치된 SDK 버전과 해당 메서드 signature | SDK 2.6.1은 taxonomy create에 `taxonomy=` 사용. 공식 예제와 버전 차이를 기록하며 원래 오류를 숨기거나 자원을 반복 생성하지 않음 |
| `num_turns`와 반환 행 수가 다름 | Turn depth와 실제 seed/objective 수 구분 | `num_turns`는 문항 수가 아님. 제출 목록·실제 요청·반환/채점 행을 각각 기록하고 분모를 추측하지 않음 |
| Native Prohibited Actions 지표 방향이 불명확 | 정확한 evaluator 버전·schema·초기화 값 | Catalog v5 boolean/increase와 pinned v1 ordinal 0~7/decrease는 다름. v1의 `azure_ai_project` 필수. 영어 single-turn/tool-level 범위에서 실제 결과 확인 전 ASR 수정 완료 주장 금지 |
| judge must be separate from target | 실제 기반 모델·버전·배포를 모두 확인 | GPT-6 Sol 대상과 다른 GPT-5.5 / 2026-04-24를 사용. 새 환경은 `workshop-judge`, 기존 GPT-5.5는 `--deployment workshop-optimizer`로 명시. 검사 완화나 기존 모델 교체 금지 |
| 첫 azd connection 생성에서 ARM context 발견 실패 | 실제 프로젝트 ARM 환경이 있는가 | [09](09-operations.md)의 경로처럼 `prepare-hosted --kind runtime`이 준비한 실제 환경을 `--cwd`로 사용. NC에서는 포털 bootstrap 없이 동작했으며 다른 프로젝트 환경은 사용하지 않음 |
| Native red-team 첫 시도가 0행 실패 | App Insights 연결의 metadata와 SDK credential 지원 | `ResourceId`·`ApplicationInsightsConnectionString`과 telemetry connection string을 담은 `APIKey` credential 확인. Project MI 연결 생성만으로 SDK getter 지원을 가정하지 않음. 모델 API key로 바꾸는 작업이 아님 |
| Taxonomy update의 ID 오류 | Typed model 직렬화가 read-only `id`를 유지하는가 | 검토한 `reviewed.as_dict()` payload로 원래 ID를 유지해 버전 2.0 생성에 성공. ID 추측·정책 확대·원래 실패 삭제 금지 |
| Native score 0인데 판정이 다름 | 실제 evaluator별 원점수·flag·reason | Prohibited Actions 1행은 0/false/true와 Safe/NoDefect 설명이 모순. Task Adherence 5행은 0/true/false로 일관됨. 원래 5 pass/1 fail을 유지하고 0/6이나 ASR 수정으로 바꾸지 않음 |
| v1 pinning/NC 이전 후에도 Prohibited Actions polarity 문제 | 요청 버전과 실제 native engine 출력 구분 | 두 조치 모두 관찰된 불일치를 해결하지 못함. 새 Task Adherence-only native job은 별도로 검증하며 원래 실패 행을 제거하거나 custom 결과로 대신하지 않음 |
| trace가 없음 | 연결 이후 요청인가, 로그 권한/시간 범위인가 | 몇 분 대기 후 본인 요청 재조회. 로컬 JSON을 trace로 대신하지 않음 |
| Memory 조회 지연 | 같은 store/ID·TTL·scope인가 | write 반복 대신 같은 항목을 제한적으로 읽기 |
| Memory store 또는 소유 기록이 이미 있음 | `WORKSHOP_MEMORY_STORE_NAME` 선택값 | 기존 기록을 보존해 조회하거나 같은 prefix 아래의 새 미사용 이름을 선택. prefix 변경·기존 자산 인수·삭제로 우회하지 않음 |
| Routine 전달 후 답변 없음 | dispatch/run과 response 보관 상태 | 전달·실행·답변을 구분. 직접 agent 호출로 대체 금지 |
| `azd ai routine run list`는 빈 값인데 timer가 실행된 듯함 | 같은 이름의 native history | 먼저 disable하고 `scripts/routine_runs.py`로 실제 모든 시도/ID를 보관. NC에서는 SDK history와 원래 telemetry가 실행을 확인했으며 수동 재호출은 하지 않음 |
| 예약 Routine의 `conversation_not_found` | 사용자 생성 conversation을 action에 넣었는가 | 두 생성 위치 모두 routine actor에서 실패. 사용자 conversation 없이 고정 `action.input`을 넣은 새 disabled timer manifest를 사용. 이전 실패·대화·자산은 보존 |
| Routine 생성 뒤 timer에 입력이 없음 | 저장된 `action.input` | Create에는 `--input`이 없음. [11의 manifest](11-memory-a2a-routines.md#3-routines-비활성-상태에서-준비)를 사용. `dispatch --input`은 수동 호출 1회의 override일 뿐 저장 입력이 아님 |
| Disable 후 완료된 timer의 phase가 cancelled | 원래 `status: Finished`·response ID·timer source·완료 출력 | `--scheduled --verify-response --response-source telemetry`로 정확한 `invoke_agent` 응답을 확인하고 `run_phase: cancelled`를 그대로 기록. 모든 cancelled 실행을 성공으로 취급하지 않음 |
| 수동 Routine의 응답 API 조회가 안 됨 | 원래 response ID와 telemetry의 agent/version/project/trace 일치 | [11의 명시적 telemetry readback](11-memory-a2a-routines.md#원래-수동-응답을-telemetry에서-읽기)으로 같은 응답을 확인. 새 추론 없이 조회하며 수동·예약 실행을 구분 |
| Policy 점수나 감사가 거부됨 | 원문 envelope·source hash·reference_id·세 기준·판정 방향 | `result` 1~5와 `reason`, 4 이상 통과를 유지. IQ projection과 참조 불일치를 고치기 위해 원시 결과를 편집하지 않음. Calibration 24/24는 dev grading 통과가 아님 |
| 이전 의미 기준 8/8인데 업무 검사가 실패 | 의미 점수와 구조화 답변 계약은 별개 | 과거 Sweden 실패와 이후 v3 결과를 모두 보관. 어느 쪽도 새 NC 또는 관리형 AI red-team 결과로 바꾸지 않음 |
| 정당한 추가 인용이 거부됨 | 실제 사용한 진단 suite 버전과 required/allowed 목록 | Version 2는 PL05/PL06/PL07에만 명시적 `allowed_citations`를 사용. 필수·알려진·중복 없는 ID를 유지하고 무관한 참조 거부. 동결 version 1 결과는 그대로 읽으며 수정하지 않음 |
| PL06 절차 질문에 `limit_krw: 150000` | 실제 지침 hash와 질문의 금액 요청 여부 | 새 배포의 수정된 v2는 `limit_krw: null`로 검증됨. 과거 응답을 바꾸거나 배포 버전 3을 새로운 prompt 이름으로 혼동하지 않음 |
| Optimizer 완료/export가 있어도 참조 검증이 불명확 | 원본 6행·세 judge 버전/기준점·calibration 일치 | `scripts/audit_optimizer.py`로 로컬 감사. 잘못된 scope/ref/기준점은 중단하며 원본을 고치지 않음. 숨겨진 judge 요청 캡처나 개선을 주장하지 않음 |
| 다운로드 파일이 예상 폴더에 없음 | `--target-path`가 절대 경로인가 | 상대 경로는 azd `--cwd` 기준일 수 있음. [세션 증거 보관](advanced/session-files.md)의 절대 경로를 사용하고 만료 전에 원래 세션/버전/hash와 대조 |
| D01이 맞는 한도를 말했는데 policy grounding 실패 | 답변의 모든 세부 사실이 실제 반환 근거에 있는가 | `APPROVAL-01` 없는 팀장 정보가 이전 groundedness 5/6의 실제 원인. 수정된 SDK candidate는 각 기준 6/6이지만 이전 결과는 보존하며, 코드가 다른 전후 쌍을 지침만의 개선으로 표시하지 않음 |
| Skill readback 차이 | 원래 package·실제 버전·다운로드 bytes | 내려받은 파일을 정답에 맞춰 수정하지 않음 |
| Hosted raw capture 실패 | 실제 폴더/Endpoint/활성 버전인가 | 보관한 stdout/stderr로 진단. 실패 stream을 성공으로 취급하지 않음 |

## 오류와 품질 실패를 구분

간단한 오류 출력만으로 원인을 알 수 없으면 `python scripts/workshop.py --debug ...`로 **한 번만** 원문과 request ID를 확인합니다. `--model-deployment`를 사용한다면 그 옵션을 `--debug`보다 먼저 둡니다. 디버그 출력에는 로컬 경로와 입력이 포함될 수 있으므로 공개 영상·저장소에 그대로 올리지 않습니다.

`collect`/`evaluate`/`benchmark`가 비정상 종료해도 **오답을 제대로 발견한 결과**일 수 있습니다. 응답 6개가 모두 있는지, 요청 오류가 있는지, 업무 기준이 실패했는지 각각 읽습니다.

“6개 요청 중 5개 성공”은 “5/5 통과”가 아닙니다. 모델/평가자가 제공하지 않은 값을 0이나 성공으로 채우지 않습니다.

## 안전하게 재개

프로젝트·prefix·언어·소스·소유권 ledger를 유지합니다. 이미 생성한 ID를 다시 조회하고, 이전 결과를 읽은 뒤 **실제로 필요한 다음 단계만** 진행합니다.

완전히 다른 프로젝트/접두사로 바꾸려면 기존 자산을 정리/기록하고 새 실습 폴더에서 시작합니다. `.selfstudy`, `outputs`, `.env`를 삭제해 보호 조건을 우회하지 않습니다.

## 오류 보고 양식

```text
장/단계:
마지막 성공:
실제 프로젝트/agent/버전:
명령 (비밀 값 제외):
오류/원래 응답 상태:
응답/실행 ID와 로컬 파일:
현재 남아 있는 자산/과금:
다음 확인:
```

중단할 때도 [15의 정리](15-capstone-cleanup.md)를 수행합니다.
