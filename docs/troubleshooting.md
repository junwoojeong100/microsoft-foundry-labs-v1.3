# 문제 해결 — 같은 오류에 재생성부터 하지 않기

[English](en/troubleshooting.md) | **한국어** · [전체 과정](../README.ko.md)

**오류가 나면 의존하는 다음 명령을 멈춥니다.** 현재 장·마지막 성공·대상 버전·오류 원문을 확인합니다. 비밀번호·토큰·API key·회사 데이터는 공유하지 않습니다.

아래에서 **지금 발생한 증상만** 펼칩니다. 처음 시작하거나 이어 하는 방법은 [진행 도움말](checkpoints.md)에 있습니다. 과거 검증 오류를 재현할 필요는 없습니다.

## 증상별 바로 가기

오류가 난 영역을 고른 뒤 **해당 증상만 펼칩니다**. 각 설명은 **먼저 확인 → 다음 행동** 순서입니다. 오류 코드·명령 이름은 브라우저의 페이지 찾기(`Ctrl+F` / `Cmd+F`)로도 찾을 수 있습니다.

- [처음 실행할 때 막힘](#처음-실행할-때-자주-막히는-곳)
- [설치·터미널·저장 파일](#environment)
- [로그인·프로젝트·권한](#identity)
- [모델 응답·배포·할당량](#models)
- [Search·File Search·IQ·Hybrid](#retrieval)
- [MAF·Toolbox·Skill·Hosted](#tools)
- [평가·비교·Optimizer](#evaluation)
- [관리형 AI red teaming·판정 불일치](#managed-safety)
- [로그·Trace·반복 평가](#observability)
- [Memory·Routine·예약 중지](#state-schedules)

[오류와 품질 실패 구분](#오류와-품질-실패를-구분) · [안전하게 재개](#안전하게-재개) · [오류 보고 양식](#오류-보고-양식)

## 처음 실행할 때 자주 막히는 곳

<details>
<summary><code>can&#x27;t open file ... scripts/workshop.py</code></summary>

**먼저 할 일:** VS Code의 **File → Open Folder**로 README와 `scripts/`가 함께 있는 폴더를 엽니다. **Terminal → New Terminal**에서 다시 실행합니다. ZIP 내부나 상위 폴더에서는 실행하지 않습니다.

</details>

<details>
<summary><code>python</code>을 찾을 수 없거나 패키지를 못 찾음</summary>

**먼저 할 일:** [00장의 내 OS 절차](00-setup.md#2-실습-파일과-개발-도구)로 `.venv`를 활성화하고 `python --version`을 확인합니다. PowerShell 활성화가 차단되면 `python` 대신 `.\.venv\Scripts\python.exe`를 사용합니다. 시스템 정책은 낮추지 않습니다.

</details>

<details>
<summary><code>먼저 Lab 00의 configure</code></summary>

**먼저 할 일:** `values`는 저장된 설정을 읽습니다. 처음이라면 [00장 8절의 configure](00-setup.md#8-실제-값으로-설정-자동-수집)를 먼저 마칩니다. 기존 환경이라면 이전 실습 폴더를 열었는지 확인합니다.

</details>

<details>
<summary><code>YOUR-...</code>/<code>실제-...</code>를 거부함</summary>

**먼저 할 일:** 앞 단계가 출력한 내 값으로 바꿉니다. 따옴표는 남기고 꺾쇠는 제거합니다. [값 복사 안내](checkpoints.md#결과-파일을-읽고-다음-명령에-값-옮기기)에서 엔드포인트·ARM ID·폴더를 구분합니다.

</details>

<details>
<summary>서버 명령 뒤 입력 프롬프트가 안 돌아옴</summary>

**먼저 할 일:** `serve`는 실행한 채 두는 명령입니다. A는 그대로 두고, [새 터미널 B](checkpoints.md#두-터미널을-사용하는-장)에서 같은 폴더·가상 환경으로 상태를 확인합니다. 준비 상태가 실패하면 A의 오류를 먼저 읽습니다.

</details>

<details>
<summary><code>azd</code>가 <code>azure.yaml</code>을 못 찾거나 엉뚱한 서비스를 표시함</summary>

**먼저 할 일:** [08장의 준비 명령](08-hosted.md#3-기존-프로젝트에-연결하는-독립-폴더)이 출력한 **`폴더:` 절대 경로**를 `--cwd`에 넣습니다. `.build` 패키지·저장소 루트·`azure.yaml` 파일 경로가 아닙니다.

</details>

<details>
<summary>Windows에서 <code>No module named &#x27;fcntl&#x27;</code></summary>

**먼저 할 일:** 05장 5절은 macOS/Linux 전용입니다. 승인된 WSL/Linux의 별도 소스·Python 환경을 쓰거나 그 절을 미실행으로 남깁니다. 패키지 재설치로 해결되지 않습니다.

</details>

<details>
<summary>CI preflight가 식별자 누락을 보고함</summary>

**먼저 할 일:** [14장의 변수 표](14-additional-permissions.md#3-실행-전에-environment-변수-등록)를 보고 **`foundry-workshop` Environment → Variables**에 등록합니다. 같은 이름의 Secret만 있으면 읽지 못합니다.

</details>

<details>
<summary>Fork 뒤 검사 실행이 없거나 <code>Run workflow</code>가 안 보임</summary>

**먼저 할 일:** 본인 저장소의 Actions 활성화, `main`의 workflow 파일, 실행 권한을 확인합니다. [14장 1절](14-additional-permissions.md#1-저장소와-environment-준비)의 Workshop checks부터 실행합니다.

</details>

<details>
<summary>OIDC에 일치하는 federated credential이 없다고 나옴</summary>

**먼저 할 일:** [14장 4절](14-additional-permissions.md#4-oidc-federation-연결)에서 실제 issuer·subject·audience를 대조합니다. 새 저장소의 숫자 ID와 Environment 형식을 확인합니다. client secret으로 우회하지 않습니다.

</details>

<details>
<summary>준비 도중 중단했는데 <code>status</code>가 configure를 요구함</summary>

**먼저 할 일:** `status`는 생략하고 [15장 5절](15-capstone-cleanup.md#5-소유-자산-목록-대조)에 따라 포털의 실습 구독·그룹을 확인합니다. 설정 파일이 없어도 자원과 비용은 남을 수 있습니다.

</details>

<details>
<summary><code>azure.yaml</code> JSON 문법 오류</summary>

**먼저 할 일:** [13장 3절](13-governance.md#3-내-hosted의-새-버전에-연결)처럼 `policies`를 `services` 아래 실제 에이전트 객체에 넣습니다. 쉼표·괄호를 확인하고 JSON에 YAML 문법을 섞지 않습니다. 문법 검사 전에는 배포하지 않습니다.

</details>

<details>
<summary>native 점수 실패인데 예전 인수 결과는 <code>gate_passed: true</code></summary>

**먼저 할 일:** [15장 2절](15-capstone-cleanup.md#2-hosted-최종-확인)의 `--require-native-pass` 포함 명령으로 **기존 증거만** 검사합니다. holdout을 다시 수집하지 않습니다. 관리형 red-team 감사는 별도로 확인합니다.

</details>

## Azure·모델·도구별 오류

참고 검증의 새 Task Adherence는 6행·5 pass/1 fail이며 severity/flag 불일치로 인수 보류입니다. [현재 보고서](validation-report.md)와 과거 기록을 구분하고 본인의 원래 실패를 보존합니다.

<a id="environment"></a>

### 설치·터미널·저장 파일

<details>
<summary>Python/패키지 오류</summary>

**먼저 확인:** `.venv`의 Python 3.13인가

**다음 행동:** [00장의 설치](00-setup.md#2-실습-파일과-개발-도구)를 따릅니다. 같은 가상 환경에서 `python -m pip check`가 `No broken requirements found.`인지 확인합니다. 다른 Python 환경의 패키지와 섞지 않습니다.

</details>

<details>
<summary><code>az</code>/<code>azd</code>/Foundry 명령 없음</summary>

**먼저 확인:** 도구와 `microsoft.foundry` 확장

**다음 행동:** 00/08의 설치. 기존 동작 환경을 무조건 업그레이드하지 않음

</details>

<details>
<summary><code>.env</code>/셸 설정 충돌</summary>

**먼저 확인:** 과거 export가 우선하는가

**다음 행동:** 이전에 변수를 설정한 터미널을 닫고 실습 폴더에서 새 터미널을 엽니다. 충돌이 계속되면 오류에 표시된 변수만 확인합니다. 다른 프로젝트로 바꾸거나 `.env`를 삭제하지 않습니다.

</details>

<details>
<summary>label/파일/패키지가 이미 존재</summary>

**먼저 확인:** 이전 실제 결과인가

**다음 행동:** 먼저 읽고, 새 요청/패키지에는 새 이름/경로. 실패 삭제 금지

</details>

<a id="identity"></a>

### 로그인·프로젝트·권한

<details>
<summary>configure에 계정 ARM ID 입력</summary>

**먼저 확인:** `/projects/...`까지 있는가

**다음 행동:** 프로젝트 JSON View의 실제 id 복사

</details>

<details>
<summary>Endpoint 불일치</summary>

**먼저 확인:** 모델 URL, 다른 계정/프로젝트 URL인가

**다음 행동:** 같은 프로젝트 홈의 Endpoint와 실제 customSubDomainName 대조

</details>

<details>
<summary>401/로그인 만료</summary>

**먼저 확인:** 사용자·tenant·구독 일치

**다음 행동:** 정상 로그인/MFA. 토큰 복사나 client secret 생성으로 우회 금지

</details>

<details>
<summary>Owner인데 모델/agent 403</summary>

**먼저 확인:** Foundry 데이터 역할

**다음 행동:** 본인/실제 서비스 ID의 Foundry User와 범위 확인

</details>

<details>
<summary>Hosted만 403</summary>

**먼저 확인:** `instance_identity.principal_id` 역할

**다음 행동:** 로컬 로그인 반복 대신 실제 원격 ID에 필요한 역할

</details>

<details>
<summary>Provider 등록/Policy 거부</summary>

**먼저 확인:** Subscription의 provider와 조직 정책

**다음 행동:** Owner로 가능한 등록은 Portal 절차 사용. 상위 정책 우회 금지

</details>

<details>
<summary>접근 차단/timeout</summary>

**먼저 확인:** 조직에서 허용한 실행 환경과 원래 오류

**다음 행동:** 승인된 담당 절차로 해결. 공유 방화벽이나 인증서 보호를 낮추지 않음

</details>

<details>
<summary>첫 azd connection 생성에서 ARM context 발견 실패</summary>

**먼저 확인:** 실제 프로젝트 ARM 환경이 있는가

**다음 행동:** [09](09-operations.md)의 경로처럼 `prepare-hosted --kind runtime`이 준비한 실제 환경을 `--cwd`로 사용. NC에서는 포털 bootstrap 없이 동작했으며 다른 프로젝트 환경은 사용하지 않음

</details>

<a id="models"></a>

### 모델 응답·배포·할당량

<details>
<summary>모델/버전/지역 제공 안 됨</summary>

**먼저 확인:** 실제 가용성·quota

**다음 행동:** 이 실습의 모델·리전을 유지하고 필요한 할당량을 요청합니다. 준비될 때까지 해당 단계를 차단으로 남깁니다. 다른 모델로 바꿔 같은 실습의 성공으로 기록하지 않습니다.

</details>

<details>
<summary>과거 GPT-6 Luna 프로젝트 <code>reasoning.effort</code> 400 / 500</summary>

**먼저 확인:** 계정 API·포털 성공과 프로젝트 API는 별개

**다음 행동:** 현재 첫 경로는 Sol로 시작. 선택적 Luna 비교는 02/07에서 두 모델 모두 `account-responses`로 고정. 이 과거 오류를 재현하려고 설정 제거·재생성을 반복하지 않음

</details>

<details>
<summary><code>Not allowed when agent is specified</code>, <code>param: reasoning</code></summary>

**먼저 확인:** 저장 버전의 definition과 호출 본문

**다음 행동:** reasoning은 definition에만 저장. `agent_reference` 요청에서 중복 전달하지 않음

</details>

<details>
<summary>모델 배포 이름은 맞는데 configure가 거부</summary>

**먼저 확인:** 실제 기반 모델/버전이 다름

**다음 행동:** 기본은 GPT-6 Sol / 2026-09-22. 기존 Sol 별칭이 `workshop-compare`이면 명시적으로 재사용하고 기존 이름의 모델은 변경하지 않음

</details>

<details>
<summary><code>incomplete</code> / 텍스트가 비어 있음</summary>

**먼저 확인:** reasoning이 출력 예산을 소진했는가

**다음 행동:** `WORKSHOP_REASONING_EFFORT=low`, `WORKSHOP_MAX_OUTPUT_TOKENS=32768`와 원래 incomplete_details 확인

</details>

<details>
<summary>도구 후 <code>encrypted reasoning</code> / replay 오류</summary>

**먼저 확인:** stateless 도구 결과와 reasoning 항목의 연결

**다음 행동:** 고정 requirements 환경과 코드의 명시적 encrypted-content include 확인. reasoning을 임의로 제거하지 않음

</details>

<details>
<summary>모델/생성 설정 변경 후 agent 참조 거부</summary>

**먼저 확인:** 저장한 agent 버전과 현재 조건이 다름

**다음 행동:** 기존 결과를 보존하고 새 소유 이름으로 agent 생성. 최신 버전 자동 선택 금지

</details>

<details>
<summary>429</summary>

**먼저 확인:** 공유 한도·동시 요청

**다음 행동:** 중단/대기 후 제한적 재시도. 전후 평가 조건을 유지

</details>

<a id="retrieval"></a>

### Search·File Search·IQ·Hybrid

<details>
<summary>Search 403</summary>

**먼저 확인:** RBAC 인증, 실제 caller, 데이터 역할

**다음 행동:** 내 사용자·프로젝트 MI·계정 MI·Search MI를 구분. key 인증을 켜서 우회하지 않음

</details>

<details>
<summary>Search <code>ResourcesForSkuUnavailable</code></summary>

**먼저 확인:** 새 NC의 실제 리전·SKU 가용성

**다음 행동:** Sweden의 실패 후 성공은 과거 사례. NC는 별도로 확인하고 조건 변경 뒤 제한적으로 재시도. 이전 리전이나 결과로 자동 전환하지 않음

</details>

<details>
<summary>Search <code>ServiceQuotaExceeded</code>, <code>0 out of 0</code></summary>

**먼저 확인:** 해당 SKU의 현재 구독 quota

**다음 행동:** 과거 S2 오류를 현재 Basic의 차단으로 해석하지 않음. 실제 quota가 부족하면 정상 요청 절차를 사용하고 역할 추가·자동 SKU 상승·임의 삭제로 우회하지 않음

</details>

<details>
<summary>File Search 포털 업로드가 보이지 않음</summary>

**먼저 확인:** UI·모델·지역 제공 차이

**다음 행동:** 03의 SDK 생성/조회 경로를 사용하고 실제 File Search call과 인용을 확인

</details>

<details>
<summary>File Search 버튼/인용 없음</summary>

**먼저 확인:** 모델·지역·도구 설정·인덱싱

**다음 행동:** 인라인 답변을 검색 성공으로 바꾸지 않음

</details>

<details>
<summary>과거/현행 혼동</summary>

**먼저 확인:** 질문 날짜와 적용 기간

**다음 행동:** 원문 120,000/150,000원 구분, 실제 실패 기록

</details>

<details>
<summary>Search 기능 과금 오류</summary>

**먼저 확인:** Semantic/Knowledge retrieval 각각의 플랜

**다음 행동:** Free 기능과 Basic 서비스 비용을 구분하고 추가 지출을 결정

</details>

<details>
<summary>Hybrid schema/차원 오류</summary>

**먼저 확인:** 실제 embedding 차원과 새 index

**다음 행동:** 0 벡터/잘라낸 벡터 금지. 기존 index를 덮어쓰지 않음

</details>

<details>
<summary>IQ Chat check 실패</summary>

**먼저 확인:** 고정 모델/버전·Search MI·역할

**다음 행동:** 지원 조건을 해결하거나 해당 preset 차단으로 기록

</details>

<details>
<summary>영어 IQ dev의 D05에서 <code>SCOPE-01</code> 누락</summary>

**먼저 확인:** 원래 반환 문서와 reranker 필터

**다음 행동:** 06의 합성 corpus용 문턱 0을 명시하고 새 label에서 전체 dev를 확인. 기존 5/6과 원문은 보존하며 인용 기준을 낮추지 않음

</details>

<a id="tools"></a>

### MAF·Toolbox·Skill·Hosted

<details>
<summary>01장 JSON에서 배포 버전·API를 찾기 어려움</summary>

**먼저 확인:** `model` 결과의 `text`, `response_id`, `response_model`, `inference_api`를 확인합니다.

**다음 행동:** 배포·모델 버전은 00장의 `doctor --cloud` 출력에서 확인합니다. 응답 JSON의 API 필드 이름은 `api`가 아니라 `inference_api`이며 기대 값은 `project-responses`입니다. [01장](01-foundry.md#2-같은-sol-배포를-코드에서).

</details>

<details>
<summary>05장 결과에 토큰·지연이 없음</summary>

**먼저 확인:** `pattern`, `outputs`, `approval_status`, `external_actions_performed`를 읽습니다.

**다음 행동:** 이 결과는 토큰·지연 집계를 제공하지 않습니다. 역할별 출력과 근거를 비교하고, 없는 측정값을 0으로 채우지 않습니다.

</details>

<details>
<summary>Toolbox 목록은 되는데 query 실패</summary>

**먼저 확인:** downstream Search 접근

**다음 행동:** 프로젝트 MI의 Index Data Reader와 필요한 Service Contributor 확인

</details>

<details>
<summary>Toolbox가 정상 keyless 연결의 인증 enum을 거부</summary>

**먼저 확인:** 현재 SDK의 `ProjectManagedIdentity`와 이전 `AAD` 표현

**다음 행동:** `AAD`만 유효하다고 가정하지 않음. 프로젝트 MI와 실제 대상/역할을 확인하며 API key로 바꾸지 않음. 일반 v1은 수정 후 probe/query/ask 통과

</details>

<details>
<summary>OpenAPI만 실패</summary>

**먼저 확인:** 계정 MI인가, API 버전 인자인가

**다음 행동:** `openapi plan`의 주체와 내부 오류 확인. Toolbox ID와 다름

</details>

<details>
<summary>NC Function 표의 no를 보고 MAF 전체를 단정</summary>

**먼저 확인:** 관리형 Agent Service 도구와 로컬 모델/함수 경로 구분

**다음 행동:** NC의 FoundryChatClient + 로컬 `lookup_policy`와 MCP는 실제 성공. 이 결과는 모든 관리형 Function 도구 지원 보장이 아니며 [04](04-tools.md)의 실제 경로/결과를 구분

</details>

<details>
<summary>Skill readback 차이</summary>

**먼저 확인:** 원래 package·실제 버전·다운로드 bytes

**다음 행동:** 내려받은 파일을 정답에 맞춰 수정하지 않음

</details>

<details>
<summary>Hosted raw capture 실패</summary>

**먼저 확인:** 실제 폴더/Endpoint/활성 버전인가

**다음 행동:** 보관한 stdout/stderr로 진단. 실패 stream을 성공으로 취급하지 않음

</details>

<details>
<summary>다운로드 파일이 예상 폴더에 없음</summary>

**먼저 확인:** `--target-path`가 절대 경로인가

**다음 행동:** 상대 경로는 azd `--cwd` 기준일 수 있음. [세션 증거 보관](advanced/session-files.md)의 절대 경로를 사용하고 만료 전에 원래 세션/버전/hash와 대조

</details>

<a id="evaluation"></a>

### 평가·비교·Optimizer

<details>
<summary>benchmark/SDK 비교의 <code>code_hash</code> 불일치</summary>

**먼저 확인:** 지침 외에 결합된 코드가 바뀌었는가

**다음 행동:** 실제 r2 SDK 전후 쌍도 이 이유로 올바르게 거부됨. 개별 candidate 점수와 지침만의 개선 주장을 구분하고 코드 동결 후 새 전후 쌍을 수집. hash 편집·검사 완화 금지

</details>

<details>
<summary>judge/Optimizer 결과 누락</summary>

**먼저 확인:** evaluator 목록·전체 행·실제 입력

**다음 행동:** 부분 결과로 통과 처리하지 않음

</details>

<details>
<summary>NC Optimizer의 <code>MissingRequiredParameter: pass_threshold</code></summary>

**먼저 확인:** 이름/버전만 보내고 evaluator별 초기화를 생략

**다음 행동:** 선택한 calibration catalog의 `initialization_parameters`에 judge와 필수 문턱 4를 명시합니다. SDK 2.6.1의 공개 mapping 생성자로 값을 보존하고 실제 전송 본문에도 남는지 확인합니다. 평가자 이름·버전·기준을 바꾸거나 기존 실패를 지우지 않습니다. [12장의 결과 검사](12-improvement.md#3-지침만-최적화).

</details>

<details>
<summary>Optimizer inline dataset 입력이 거부됨</summary>

**먼저 확인:** 설치한 SDK와 서비스가 받는 입력 형식을 구분합니다.

**다음 행동:** SDK 2.6.1에서 확인한 형식은 `train_dataset: {"type": "inline", "items": [...]}`입니다. `items`에는 dev의 `query`·`ground_truth`만 넣고 실제 전송 본문을 확인합니다. 서버 job이 생겼다면 같은 ID를 조회하며 새 job을 반복 생성하지 않습니다.

</details>

<details>
<summary>Optimizer의 <code>details.job_id</code> 로컬 오류</summary>

**먼저 확인:** `poller.details`는 mapping인가

**다음 행동:** SDK 2.6.1은 `details["job_id"]`. 서버 job이 이미 존재할 수 있으므로 기존 target/job ID를 조회하고 생성부터 반복하지 않음

</details>

<details>
<summary>이전 legacy Groundedness Optimizer가 baseline 1.0에서 종료</summary>

**먼저 확인:** 그 이전 실행의 judge `context`가 원문인가

**다음 행동:** `context=response`였던 과거 실패를 보존. 현재 policy 기준은 1~5·4 이상 통과이며, 이 legacy 경고를 새 job 결과로 옮기지 않음

</details>

<details>
<summary>judge must be separate from target</summary>

**먼저 확인:** 실제 기반 모델·버전·배포를 모두 확인

**다음 행동:** GPT-6 Sol 대상과 다른 GPT-5.5 / 2026-04-24를 사용. 새 환경은 `workshop-judge`, 기존 GPT-5.5는 `--deployment workshop-optimizer`로 명시. 검사 완화나 기존 모델 교체 금지

</details>

<details>
<summary>Policy 점수나 감사가 거부됨</summary>

**먼저 확인:** 원문 envelope·source hash·reference_id·세 기준·판정 방향

**다음 행동:** `result` 1~5와 `reason`, 4 이상 통과를 유지. IQ projection과 참조 불일치를 고치기 위해 원시 결과를 편집하지 않음. Calibration 24/24는 dev grading 통과가 아님

</details>

<details>
<summary>이전 의미 기준 8/8인데 업무 검사가 실패</summary>

**먼저 확인:** 의미 점수와 구조화 답변 계약은 별개

**다음 행동:** 과거 Sweden 실패와 이후 v3 결과를 모두 보관. 어느 쪽도 새 NC 또는 관리형 AI red-team 결과로 바꾸지 않음

</details>

<details>
<summary>정당한 추가 인용이 거부됨</summary>

**먼저 확인:** 실제 사용한 진단 suite 버전과 required/allowed 목록

**다음 행동:** Version 2는 PL05/PL06/PL07에만 명시적 `allowed_citations`를 사용. 필수·알려진·중복 없는 ID를 유지하고 무관한 참조 거부. 동결 version 1 결과는 그대로 읽으며 수정하지 않음

</details>

<details>
<summary>PL06 절차 질문에 <code>limit_krw: 150000</code></summary>

**먼저 확인:** 실제 지침 hash와 질문의 금액 요청 여부

**다음 행동:** 새 배포의 수정된 v2는 `limit_krw: null`로 검증됨. 과거 응답을 바꾸거나 배포 버전 3을 새로운 prompt 이름으로 혼동하지 않음

</details>

<details>
<summary>Optimizer 완료/export가 있어도 참조 검증이 불명확</summary>

**먼저 확인:** 원본 6행·세 judge 버전/기준점·calibration 일치

**다음 행동:** `scripts/audit_optimizer.py`로 로컬 감사. 잘못된 scope/ref/기준점은 중단하며 원본을 고치지 않음. 숨겨진 judge 요청 캡처나 개선을 주장하지 않음

</details>

<details>
<summary>D01이 맞는 한도를 말했는데 policy grounding 실패</summary>

**먼저 확인:** 답변의 모든 세부 사실이 실제 반환 근거에 있는가

**다음 행동:** `APPROVAL-01` 없는 팀장 정보가 이전 groundedness 5/6의 실제 원인. 수정된 SDK candidate는 각 기준 6/6이지만 이전 결과는 보존하며, 코드가 다른 전후 쌍을 지침만의 개선으로 표시하지 않음

</details>

<a id="managed-safety"></a>

### 관리형 AI red teaming·판정 불일치

<details>
<summary>관리형 AI red teaming의 리전 설명 불일치</summary>

**먼저 확인:** 공식 리전 표와 개념 개요를 둘 다 확인

**다음 행동:** North Central US는 두 목록에 공통으로 포함됩니다. 다른 리전의 지원이나 오류 원인을 추측하지 않습니다. [13장의 두 공식 링크](13-governance.md#5-관리형-ai-red-teaming--기본-검증-대상)와 현재 환경의 실제 응답을 확인합니다.

</details>

<details>
<summary>이전 Sweden Red-team ASR과 설명이 모순</summary>

**먼저 확인:** 원점수·`attack_success`·요청/반환 수와 판정 의미

**다음 행동:** 검증되지 않은 native ASR로 보존. Custom 8/8이나 NC 이전이 지표 방향을 고쳤다고 하지 않고 실제 NC job을 별도 확인

</details>

<details>
<summary>Taxonomy 생성 예제의 <code>body=</code>가 오류</summary>

**먼저 확인:** 설치된 SDK 버전과 해당 메서드 signature

**다음 행동:** SDK 2.6.1은 taxonomy create에 `taxonomy=` 사용. 공식 예제와 버전 차이를 기록하며 원래 오류를 숨기거나 자원을 반복 생성하지 않음

</details>

<details>
<summary><code>num_turns</code>와 반환 행 수가 다름</summary>

**먼저 확인:** Turn depth와 실제 seed/objective 수 구분

**다음 행동:** `num_turns`는 문항 수가 아님. 제출 목록·실제 요청·반환/채점 행을 각각 기록하고 분모를 추측하지 않음

</details>

<details>
<summary>Native Prohibited Actions 지표 방향이 불명확</summary>

**먼저 확인:** 정확한 evaluator 버전·schema·초기화 값

**다음 행동:** Catalog v5 boolean/increase와 pinned v1 ordinal 0~7/decrease는 다름. v1의 `azure_ai_project` 필수. 영어 single-turn/tool-level 범위에서 실제 결과 확인 전 ASR 수정 완료 주장 금지

</details>

<details>
<summary>Native red-team 첫 시도가 0행 실패</summary>

**먼저 확인:** App Insights 연결의 metadata와 SDK credential 지원

**다음 행동:** `ResourceId`·`ApplicationInsightsConnectionString`과 telemetry connection string을 담은 `APIKey` credential 확인. Project MI 연결 생성만으로 SDK getter 지원을 가정하지 않음. 모델 API key로 바꾸는 작업이 아님

</details>

<details>
<summary>Taxonomy update의 ID 오류</summary>

**먼저 확인:** Typed model 직렬화가 read-only `id`를 유지하는가

**다음 행동:** 검토한 `reviewed.as_dict()` payload로 원래 ID를 유지해 버전 2.0 생성에 성공. ID 추측·정책 확대·원래 실패 삭제 금지

</details>

<details>
<summary>Native score 0인데 판정이 다름</summary>

**먼저 확인:** 실제 evaluator별 원점수·flag·reason

**다음 행동:** Prohibited Actions 1행은 0/false/true와 Safe/NoDefect 설명이 모순. Task Adherence 5행은 0/true/false로 일관됨. 원래 5 pass/1 fail을 유지하고 0/6이나 ASR 수정으로 바꾸지 않음

</details>

<details>
<summary>v1 pinning/NC 이전 후에도 Prohibited Actions polarity 문제</summary>

**먼저 확인:** 요청 버전과 실제 native engine 출력 구분

**다음 행동:** 두 조치 모두 관찰된 불일치를 해결하지 못함. 새 Task Adherence-only native job은 별도로 검증하며 원래 실패 행을 제거하거나 custom 결과로 대신하지 않음

</details>

<a id="observability"></a>

### 로그·Trace·반복 평가

<details>
<summary>Continuous Coherence v1의 <code>is_reasoning_model</code> 초기화 오류</summary>

**먼저 확인:** 실제 catalog 버전과 서비스 evaluator ABI

**다음 행동:** NC에서는 같은 judge/문턱을 유지한 별도 v13 실행이 1/1 통과. v1의 0행 실패와 원래 응답은 보존하고 두 rule 모두 pause. 다른 evaluator 버전까지 일괄 변경하지 않음

</details>

<details>
<summary>trace가 없음</summary>

**먼저 확인:** 연결 이후 요청인가, 로그 권한/시간 범위인가

**다음 행동:** 몇 분 대기 후 본인 요청 재조회. 로컬 JSON을 trace로 대신하지 않음

</details>

<a id="state-schedules"></a>

### Memory·Routine·예약 중지

<details>
<summary>Memory 조회 지연</summary>

**먼저 확인:** 같은 store/ID·TTL·scope인가

**다음 행동:** write 반복 대신 같은 항목을 제한적으로 읽기

</details>

<details>
<summary>Memory store 또는 소유 기록이 이미 있음</summary>

**먼저 확인:** `WORKSHOP_MEMORY_STORE_NAME` 선택값

**다음 행동:** 기존 기록을 보존해 조회하거나 같은 prefix 아래의 새 미사용 이름을 선택. prefix 변경·기존 자산 인수·삭제로 우회하지 않음

</details>

<details>
<summary>Routine 전달 후 답변 없음</summary>

**먼저 확인:** dispatch/run과 response 보관 상태

**다음 행동:** 전달·실행·답변을 구분. 직접 agent 호출로 대체 금지

</details>

<details>
<summary><code>azd ai routine run list</code>는 빈 값인데 timer가 실행된 듯함</summary>

**먼저 확인:** 같은 이름의 native history

**다음 행동:** 먼저 disable하고 `scripts/routine_runs.py`로 실제 모든 시도/ID를 보관. NC에서는 SDK history와 원래 telemetry가 실행을 확인했으며 수동 재호출은 하지 않음

</details>

<details>
<summary>예약 Routine의 <code>conversation_not_found</code></summary>

**먼저 확인:** 사용자 생성 conversation을 action에 넣었는가

**다음 행동:** 두 생성 위치 모두 routine actor에서 실패. 사용자 conversation 없이 고정 `action.input`을 넣은 새 disabled timer manifest를 사용. 이전 실패·대화·자산은 보존

</details>

<details>
<summary>Routine 생성 뒤 timer에 입력이 없음</summary>

**먼저 확인:** 저장된 `action.input`

**다음 행동:** Create에는 `--input`이 없음. [11의 manifest](11-memory-a2a-routines.md#3-routines-비활성-상태에서-준비)를 사용. `dispatch --input`은 수동 호출 1회의 override일 뿐 저장 입력이 아님

</details>

<details>
<summary>Disable 후 완료된 timer의 phase가 cancelled</summary>

**먼저 확인:** 원래 `status: Finished`·response ID·timer source·완료 출력

**다음 행동:** `--scheduled --verify-response --response-source telemetry`로 정확한 `invoke_agent` 응답을 확인하고 `run_phase: cancelled`를 그대로 기록. 모든 cancelled 실행을 성공으로 취급하지 않음

</details>

<details>
<summary>수동 Routine의 응답 API 조회가 안 됨</summary>

**먼저 확인:** 원래 response ID와 telemetry의 agent/version/project/trace 일치

**다음 행동:** [11의 명시적 telemetry readback](11-memory-a2a-routines.md#원래-수동-응답을-telemetry에서-읽기)으로 같은 응답을 확인. 새 추론 없이 조회하며 수동·예약 실행을 구분

</details>

## 오류와 품질 실패를 구분

간단한 오류 출력만으로 원인을 알 수 없으면 `python scripts/workshop.py --debug ...`로 **한 번만** 원문과 request ID를 확인합니다. `--model-deployment`를 사용한다면 그 옵션을 `--debug`보다 먼저 둡니다. 디버그 출력에는 로컬 경로와 입력이 포함될 수 있으므로 공개 영상·저장소에 그대로 올리지 않습니다.

`collect`/`evaluate`/`benchmark`가 비정상 종료해도 **오답을 제대로 발견한 결과**일 수 있습니다. 응답 6개가 모두 있는지, 요청 오류가 있는지, 업무 기준이 실패했는지 각각 읽습니다.

“6개 요청 중 5개 성공”은 “5/5 통과”가 아닙니다. 모델/평가자가 제공하지 않은 값을 0이나 성공으로 채우지 않습니다.

## 안전하게 재개

프로젝트·접두사·언어·소스·소유 기록을 유지합니다. 이미 생성한 ID를 조회하고 기존 결과를 읽은 뒤 **필요한 다음 단계만** 진행합니다.

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

---

[증상별 바로 가기 ↑](#증상별-바로-가기) · [진행 도움말](checkpoints.md) · [중지·비용 정리](15-capstone-cleanup.md#4-먼저-실행-중인-것을-멈추기)
