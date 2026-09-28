# 12. 대화 평가·Optimizer·배포 품질

[English](en/12-improvement.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 전체 대화를 평가하고, 개선 후보와 실제 Hosted 버전을 근거로 비교합니다.

**시작 조건:**

- **평가:** 07의 judge·dev 결과·policy calibration.
- **Hosted 비교:** 08의 Hosted 준비, 같은 계정의 OpenAI Endpoint, 09의 로그 연결.
- **IQ 경로만:** 06의 IQ 조회 성공. 명시적 로컬 검색 경로에는 필요하지 않습니다.

**실행 위치:** Foundry 포털에서 Optimizer, 터미널에서 배포·평가, 브라우저에서 HTML 보고서.

> [!IMPORTANT]
> 기능별 비용을 먼저 확인합니다. 코드를 동결하고 **지침만 바꾸며, holdout은 열지 않습니다.** Hosted 비교에는 포함된 `v1`/`v2`를 사용합니다. Optimizer 후보를 기다리거나 자동 적용하지 않습니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [먼저 검색 경로 선택](#iq-또는-로컬-검색을-명시적으로-선택하기) | IQ 또는 명시적 local 중 한 경로 |
| [1. 대화 평가](#1-대화-평가) | 턴 평가와 전체 대화 평가의 차이 |
| [2. Optimizer 준비](#2-optimizer를-위한-모델과-데이터-직접-준비) | 지원 모델과 기존 dev·calibration |
| [3. 지침 최적화](#3-지침만-최적화) | 실제 후보 유무·전체 점수·원문 감사 |
| [4. Hosted 조건 고정](#4-hosted-matrix의-범위-고정) | 모델·프로필·Endpoint |
| [5. baseline 배포](#5-baseline-프로필-배포) | 정확한 버전·역할·smoke |
| [6. baseline 평가](#6-모든-dev-행-수집평가trace) | dev 6행·업무·judge·trace |
| [7. candidate 비교](#7-candidate는-지침만-변경) | 지침만 다른 새 배포와 전후 비교 |
| [8. calibration·회귀](#8-judge-calibration과-회귀) | 일치하는 기준과 실제 실패 검토 |
| [9. 세션 중지](#9-유지와-중지) | 결과 보관과 compute 중지 |
| [10. 보완 진단](#10-별도의-policy-lab-진단-8문항) | 별도 8문항 결과와 세션 중지 |
| [완료 확인](#완료-확인) | 실행 완료와 개선·인수를 구분 |

이 장의 비교는 **코드를 먼저 동결한 뒤 새 Hosted baseline/candidate 쌍**으로 수행합니다.

- **고정:** 모델·원문·언어·retrieval·API·judge catalog·기준점·생성 설정.
- **변경:** 지침만 `v1`에서 `v2`로 바꿉니다.
- **코드가 달라졌다면:** 새 label의 전후 쌍을 다시 만듭니다. manifest의 hash를 수정하거나 검사를 완화하지 않습니다.

파생된 policy/Skill 입력의 prompt/source hash도 달라졌다면 새 입력 label로 다시 준비합니다. 이미 배포된 agent나 Skill이 로컬 v2 수정만으로 자동 갱신됐다고 가정하지 않습니다.

## IQ 또는 로컬 검색을 명시적으로 선택하기

**기본은 06에서 확인한 IQ 경로입니다.** IQ가 준비되지 않았다면 아래의 명시적 로컬 경로를 검토합니다. 이를 IQ 성공으로 기록하지 않습니다.

대화 평가·Optimizer는 Search 없이도 각자의 선행 조건을 갖춰 진행할 수 있습니다.

<details>
<summary>IQ가 준비되지 않았을 때만: 로컬 검색을 사용하는 별도 Hosted 비교</summary>

| 항목 | IQ 경로 | 명시적 로컬 검색 경로 |
|---|---|---|
| 모든 패키징·benchmark 명령의 `--retrieval` | `iq` | `local` |
| 준비 명령의 `--name` | `matrix` | `matrix-local` |
| IQ reranker threshold 설정 | 5절에서 설정 | 생략 |

예를 들어 첫 패키지와 폴더는 다음과 같습니다.

```bash
python scripts/workshop.py --script package-hosted --kind workflow --pattern sequential --retrieval local --prompt v1 --api account-chat --protocol invocations
```

**반환된 패키지로 배포 폴더 준비**

```bash
python scripts/selfstudy.py prepare-hosted --kind matrix --package "실제-local-v1-패키지-경로" --name matrix-local --run v1
```

**이후에도 바꾸지 않을 값**

- v2 패키징·dev 수집·15의 holdout에서도 `--retrieval local`을 유지합니다.
- 준비 도구가 반환한 **실제 matrix-local 서비스·폴더·버전**을 사용합니다.
- `wf-baseline`/`wf-candidate` label은 선택한 한 경로에서만 사용합니다.

준비 도구는 승인한 서비스 이름을 자식 프로세스에 전달합니다. `bind-matrix`는 배포 후 실제 Endpoint를 읽어 저장합니다.

로컬 검색은 Search·IQ·벡터 검색의 구현/검증이 아닙니다. 원격 Hosted 실행, 모델 호출, 평가, trace와 검색 provider를 각각 구분해 기록합니다.

나중에 IQ 경로로 바꾸면 **새 label과 전후 쌍**을 만듭니다. 기존 결과를 재사용하지 않습니다.

</details>

## 1. 대화 평가

```bash
python scripts/workshop.py conversations plan
```

**실제 대화 수집 · `conversations-first`**

```bash
python scripts/workshop.py conversations collect --label conversations-first --prompt v2 --confirm-cost
```

**저장된 대화 보고서 확인 · `conversations-first`**

```bash
python scripts/workshop.py conversations report --label conversations-first
```

**같은 대화의 평가 실행 · `conversations-first` · `turn`**

```bash
python scripts/workshop.py conversations evaluate --label conversations-first --level turn --confirm-cost
```

**같은 대화의 평가 실행 · `conversations-first` · `conversation`**

```bash
python scripts/workshop.py conversations evaluate --label conversations-first --level conversation --confirm-cost
```

**확인:** 같은 실제 대화를 두 수준으로 읽습니다.

| 평가 수준 | 읽을 내용 |
|---|---|
| `turn` | 개별 턴의 응답과 판정 |
| `conversation` | 앞 답변과의 모순, 전체 대화의 의도 해결 |

전체 행과 오류를 확인하고 두 수준의 차이를 기록합니다. 독립 평가 사례 사이에 Memory나 대화 상태를 공유하지 않습니다.

## 2. Optimizer를 위한 모델과 데이터 직접 준비

1. Foundry agent의 **Optimize** 화면에서 지원 모델을 확인합니다.
2. 이 실습은 후보 생성용으로 `gpt-5.5` / `2026-04-24` → `workshop-optimizer`를 사용합니다. 지역/할당량/비용을 확인하고 02와 같은 방법으로 만듭니다.
3. 답변은 **GPT-6 Sol**, judge는 07의 **GPT-5.5**를 유지합니다. Judge는 대상과 다른 기반 모델·배포여야 합니다. 후보 생성 모델의 지원 목록은 별개이므로 GPT-6으로 무조건 대체하지 않습니다.
4. **07에서 만든 `outputs/policy-inputs-ko/`와 calibration을 재사용**합니다. hash·prefix·언어가 같은지 확인하며 holdout은 넣지 않습니다.

```bash
python scripts/selfstudy.py model --role optimizer
```

**확인할 폴더:** `outputs/policy-inputs-ko/`

| 파일 | 확인할 내용 |
|---|---|
| `optimizer-dev.jsonl` | dev 6행과 원문 참조 envelope를 담은 `ground_truth` |
| `policy-evaluator-definitions.json`·manifest | 실제 평가 기준과 입력의 조건 |

입력이 없다면 [07의 준비·calibration](07-evaluation.md#5-원문-참조를-감사하는-policy-평가)을 먼저 마칩니다. 기존 폴더에 같은 준비 명령을 다시 실행하지 않습니다.

## 3. 지침만 최적화

### 별도 target 준비

03의 agent와 구분되는 **새 소유 이름**을 정합니다. `YOUR-PREFIX`를 내 접두사로 바꿉니다. 이미 이 이름으로 준비했다면 생성하지 말고 저장한 이름·버전을 사용합니다.

```bash
python scripts/workshop.py prompt-agent create --name "YOUR-PREFIX-optimize-ko" --confirm-create --output outputs/learner-notes-ko/12-optimizer-agent.json
```

기본은 아래 번호 순서의 포털 절차입니다. 직접 SDK를 작성하지 않는다면 다음 복구 설명은 건너뜁니다.

<details>
<summary>SDK로 직접 실행하거나 초기화 오류가 있을 때: 계약 차이와 검증 이력</summary>

#### 이번 리포 재실행

Job: `opt_bfa363582dff4c048ca6fceaea6ae953`

- **실행 결과:** 원래 평가기·문턱 4로 succeeded. Baseline 6/6, 참조 감사 valid.
- **후보 결과:** 새 전체 후보 0개. 승격하지 않았습니다.
- **첫 요청의 실패:** SDK의 inline dataset 설명과 실제 서비스 wire contract가 달랐습니다.

공개 mapping 생성자로 `train_dataset: {"type": "inline", "items": [...]}`를 전달한 새 요청은 성공했습니다. `items`에는 dev의 `query`/`ground_truth`만 넣고 원시 HTTP body도 확인합니다.

아래의 후보 1개와 초기화 실패는 **삭제 전 NC job의 보관 이력**입니다.

#### 이전 NC 실행의 초기화 수정

원래 실패 `opt_3aa677fe825a4b3ea433904433b57e53`은 보존했습니다. 새 SDK job `opt_6f23f99c0f2d49f7b930c7b25629543f`은 다음 조건으로 확인했습니다.

- **유지한 조건:** 원래 세 평가기의 이름·버전 1, judge, 필수 `pass_threshold: 4`.
- **실행 결과:** baseline·새 후보 각각 dev 6/6, 세 policy 기준 각각 6/6, 원문 참조 감사 `valid`.
- **비교 결과:** 두 점수는 1.0으로 동점이며 `best`는 baseline. 후보 생성은 확인했지만 개선·승격은 주장하지 않습니다.

원인은 잘못된 평가기 이름이 아니라 **Optimizer 참조의 필수 초기화 인자 누락**이었습니다. 인증된 포털 요청에서 evaluator별 `initialization_parameters`를 확인했습니다.

#### SDK에 전달할 값

SDK 2.6.1은 `initialization_parameters`를 named field로 노출하지 않습니다. 공개 mapping 생성자 `AgentOptimizationEvaluatorRef(mapping)`는 이 값을 보존합니다.

1. `optimizer_evaluator_references(catalog, judge)`로 검증된 catalog의 이름·버전·초기화 값을 함께 묶습니다.
2. 이를 `AgentOptimizationJobInputs.evaluators`에 전달합니다.
3. 직렬화된 **실제 HTTP body**에서도 값이 남는지 확인합니다.

기존 평가기를 교체하거나 required 필드를 삭제하지 않습니다.

기존 평가기 한 개의 참조는 다음 형태이며 **세 평가기 모두** 필요합니다. `name`과 `version`은 실제 calibration 값으로 채웁니다.

```json
{
  "name": "<calibrated-evaluator-name>",
  "version": "<calibrated-version>",
  "initialization_parameters": {
    "model": "workshop-judge",
    "pass_threshold": 4
  }
}
```

별도 `deployment_name`·required `threshold` 정의도 문턱 4에서 control 24/24를 통과했습니다. 그러나 이름/버전만 보낸 Optimizer는 다시 `threshold` 누락으로 실패했습니다. 이 대조 실패도 보존했습니다.

**필드 이름 변경이나 schema의 `default`만으로 해결되지 않습니다.** 선택한 catalog의 필수 인자를 명시적으로 전달해야 합니다. 설치된 azd의 standalone instruction/metadata 사전 검사 문제까지 고쳤다는 뜻은 아닙니다.

#### 비용과 같은 job 재조회

`max_candidates: 2`는 전체 호출 수 제한이 아닙니다. 이 이전 NC job의 실제 실행량은 다음과 같습니다.

- Baseline·후보의 전체 평가 2회.
- 3행짜리 minibatch 11회.
- 서비스가 보고한 agent 호출 45회.

Minibatch 3의 실패 3행도 보존했습니다. 전체 검증 없이 minibatch만 보고 후보를 승인하지 않습니다.

SDK poller의 ID는 `poller.details["job_id"]`로 읽습니다. `details.job_id`는 이 버전에서 로컬 오류를 냅니다.

이미 서버 job이 생성됐을 수 있으므로 기존 target의 job 목록에서 ID를 확인하고 **같은 job을 조회**합니다. 생성 명령부터 반복하지 않습니다.

#### Sweden 보관 기록

역사적 Sweden Optimizer의 baseline 1.0·후보 0개·참조 감사 성공은 보관본입니다. 위 NC 성공은 새 job과 새 export로 확인했습니다. 삭제된 Sweden job이나 옛 export를 인수하지 않았습니다.

</details>

### 포털: 최적화 한 번 제출

> [!WARNING]
> 최대 후보 **2개**는 전체 모델 호출 **2회**가 아닙니다. 여러 평가·minibatch가 추가 호출을 발생시킵니다.

1. Foundry **Build → Agents**에서 방금 만든 별도 Prompt Agent의 이름·버전을 엽니다.
2. **Optimize / Create optimization run → Agent**를 선택합니다.
3. 실제 target 버전·답변 모델을 고정합니다.
4. 최적화 대상은 **Instruction만**, 최대 후보 **2**를 선택합니다.
5. 2절의 `optimizer-dev.jsonl`을 업로드합니다.
6. 07의 calibration catalog와 `policy_groundedness`·`policy_helpfulness`·`policy_compliance`의 정의·버전을 대조합니다. **각 evaluator에 문턱 4와 `workshop-judge`를 지정**합니다.
7. `query`/`response`/`ground_truth` 매핑을 확인합니다. 현재 Prompt Agent wizard는 열 이름 재매핑을 지원하지 않습니다. 원문 참조 envelope는 **evaluator 입력**이며 target agent 입력에 넣지 않습니다.
8. 비용·예상 호출 범위를 확인한 뒤 한 번 제출합니다.
9. baseline과 모든 후보의 지침 차이·전체 행·평가 결과를 읽습니다.

**중단 조건:** 비용을 수락할 수 없거나 필요한 평가 조건을 설정할 수 없다면 Optimizer를 미실행/차단으로 남깁니다. 선행 조건을 갖춘 Hosted 비교로는 이어갈 수 있습니다.

**결과 해석:** 후보 0개나 동점은 개선 성공이 아닙니다.

### 터미널: 전체 결과 내보내기·감사

완료된 정확한 native evaluation/run을 **새 export label**로 보관합니다. 이 policy 감사는 제출 원문 echo를 사용하므로, 내부 judge 요청이 공개됐다고 가정하거나 legacy `--require-judge-inputs` 옵션을 감사의 대체 조건으로 사용하지 않습니다.

```bash
python scripts/workshop.py --script export-evaluation --language ko --evaluation-id "실제-eval-ID" --run-id "실제-evalrun-ID" --expected-rows 6 --label optimizer-policy-export-ko
```

실제로 업로드했던 원본 policy 입력과 같은 언어의 calibration을 지정합니다. 아래 dataset/label은 실제 새 입력과 calibration 이름으로 바꿉니다.

```bash
python scripts/audit_optimizer.py --export-directory outputs/evaluation-exports/optimizer-policy-export-ko --dataset outputs/policy-inputs-ko/optimizer-dev.jsonl --calibration-label policy-calibration-ko --language ko --output outputs/optimizer-policy-audit-ko.json
```

이 스크립트는 **Azure 호출 없이 저장된 파일을 읽는 감사**입니다.

Baseline과 실제 생성된 각 전체 후보를 별도 export/감사 파일로 보관합니다. 후보가 없으면 후보 export를 만들지 않습니다. [과거 결과](validation-report.md)의 파일·점수를 복사하지 않습니다.

**확인:** `validation_status: valid`, 6/6 matched와 다음 증거 범위를 읽습니다.

```text
proof_level: source-echo+reason-reference-id+counterfactual-calibration
internal_judge_requests_captured: false
new_model_requests: false
improvement_claimed: false
candidate_generation_assessed: false
```

**내부 judge 요청 본문은 캡처하지 않았습니다.** 감사 성공은 원문 echo·reason·counterfactual 기반 참조 검증이지 숨겨진 요청 캡처나 지침 개선의 증거가 아닙니다.

후보 0개/조기 종료는 native job의 실제 결과에서 별도로 기록합니다. 기존 export나 audit JSON이 있으면 새 이름을 선택합니다. [공식 Optimizer 개념](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview).

> [!WARNING]
> judge의 `context`가 생성된 `response`와 같다면 **자기 근거**입니다. 정상 grounding이나 개선의 증거로 인정하지 않습니다.

<details>
<summary>참고: 이전 legacy 실행에서 자기 근거를 발견한 사례</summary>

과거 Prompt Optimizer + Groundedness v18 실행은 baseline 1.0에서 조기 종료됐지만, 내려받은 **6행 모두 judge의 `context`가 생성된 `response`와 같았습니다.** 정상 grounding이나 개선 증거로 승격하지 않았습니다. 이 과거 기록은 현재 세 policy 기준의 결과가 아닙니다. 새 job도 참조 입력과 원시 결과를 직접 확인하며, 이전 점수·기록은 변경하지 않습니다.

</details>

## 4. Hosted matrix의 범위 고정

이제 **실제 배포한 버전**을 평가합니다. 07의 직접 SDK 결과를 Hosted 품질로 옮기지 않습니다.

이번 matrix의 실행 방식은 **workflow / sequential / IQ / account-chat / Invocations**입니다. 08의 기본 Responses 프로필과 다르므로 새 profile·패키지·azd 폴더를 만듭니다.

`matrix`는 **같은 dev 문항을 배포 버전별로 실행해 비교하는 결과 묶음**입니다.

먼저 `AZURE_OPENAI_ENDPOINT`가 저장되어 있는지 확인합니다. 명시적 로컬 검색 경로에도 필요합니다.

```bash
python scripts/selfstudy.py status
```

**값이 없을 때만: OpenAI 루트 Endpoint 등록**

Foundry의 같은 계정에서 Azure OpenAI **서비스 루트**를 복사합니다. 프로젝트 Endpoint가 아니며, 표시된 URL의 `/openai/v1` 경로는 제외합니다.

```bash
python scripts/selfstudy.py set AZURE_OPENAI_ENDPOINT "실제-같은-계정의-OpenAI-루트-URL"
```

이 Hosted 지침 비교는 **새 NC의 Sol 대상 한 개**로 진행합니다. 선택적 Luna 모델 비교는 02/07의 일치하는 `account-responses` 경로에서 따로 수행합니다. 새 환경의 실제 Sol 별칭을 설정합니다.

```bash
python scripts/selfstudy.py models primary=workshop-chat
```

<details>
<summary>이전 환경이 있을 때만: 다른 기존 Sol 별칭</summary>

같은 프로젝트에 실제 Sol이 `workshop-compare`로 존재함을 확인했을 때만 다음을 **대신** 사용합니다.

```bash
python scripts/selfstudy.py models primary=workshop-compare
```

</details>

두 명령 중 실제 환경에 맞는 하나만 사용합니다. Judge의 `workshop-judge` 또는 기존 GPT-5.5 `workshop-optimizer`를 대상 map에 넣지 않습니다. 모델·judge·코드·검색 조건이 바뀌면 새 label의 전후 쌍을 만들며 이전 manifest를 편집하지 않습니다.

## 5. baseline 프로필 배포

### 프로필 패키징·배포

작은 합성 corpus의 검색 필터도 시작 전에 명시합니다. `0`은 IQ 검색 필터이지 평가 통과 점수가 아닙니다. baseline 이후에는 같은 조건을 유지합니다.

```bash
python scripts/selfstudy.py set WORKSHOP_IQ_RERANKER_THRESHOLD 0
```

```bash
python scripts/workshop.py --script package-hosted --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations
```

반환된 패키지 경로로 **새 빈 폴더**를 준비합니다. 00에서 수집한 project_id/location을 사용합니다.

```bash
python scripts/selfstudy.py prepare-hosted --kind matrix --package "실제-v1-패키지-경로" --name matrix --run v1
```

**준비한 서비스만 원격 배포**

```bash
azd deploy "내-prefix-matrix" --cwd "실제-matrix-v1-절대경로"
```

**배포된 실제 버전과 런타임 ID 조회**

```bash
azd ai agent show "내-prefix-matrix" --cwd "실제-matrix-v1-절대경로" --output json
```

### 이 버전의 런타임 역할 확인

08과 같은 방식으로 `show`가 반환한 정확한 `instance_identity.principal_id`를 확인합니다. 사용자나 프로젝트 ID가 아닙니다.

| 호출 경로 | 필요한 역할과 범위 |
|---|---|
| 프로젝트 접근 | 08에서 확인한 프로젝트 역할 |
| `account-chat` → 부모 계정 OpenAI API | 이 실습 Foundry 계정의 **Cognitive Services OpenAI User** |
| IQ → Search | 이 Search의 **Search Index Data Reader** |

> [!IMPORTANT]
> **프로젝트 범위 Foundry User만으로 계정 API 권한까지 충족되지 않습니다.** `selfstudy.py roles`의 기본 Hosted 계획은 프로젝트 역할만 다룹니다.

Cognitive Services OpenAI User의 역할 ID는 `5e0bd9bd-7b93-4f28-af87-19fc36ad61bd`입니다. 누락된 역할만 확인/부여하며 구독 전체로 범위를 넓히지 않습니다.

<details>
<summary>참고: Search 성공과 account-chat 권한 실패가 함께 나온 재실행</summary>

Search는 HTTP 200이었지만 account-chat은 data action 부족으로 401, 외부 Hosted 요청은 500이었습니다.

원래 로그와 실패 세션을 보존했습니다. 해당 런타임/계정 역할만 추가한 뒤 **같은 버전·새 smoke label**로 확인했습니다. 모델/API/provider는 바꾸지 않았습니다.

</details>

### 실제 버전 연결·한 건 호출

준비 단계가 출력한 서비스/폴더를 사용해 **실제 활성 버전과 Invocations Endpoint를 자동으로 읽어 저장**합니다.

```bash
python scripts/selfstudy.py bind-matrix --directory "실제-matrix-v1-폴더" --service "실제-matrix-서비스-이름"
```

**연결한 버전에 한 건 요청 · `matrix-v1-smoke`**

```bash
python scripts/workshop.py benchmark smoke --label matrix-v1-smoke --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations --case D01 --model-key primary --confirm-cost
```

smoke가 실패하면 matrix를 실행하지 않습니다.

## 6. 모든 dev 행 수집·평가·trace

### 계획 확인·6행 수집

```bash
python scripts/workshop.py benchmark plan --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations
```

**전체 문항 수집 · `wf-baseline`**

```bash
python scripts/workshop.py benchmark collect --label wf-baseline --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
```

**확인:** 수집 완료·오류 유무를 확인한 뒤 다음 명령으로 갑니다. 이 Sol 대상 하나의 기본 dev는 **6행**이며, 역할별 호출과 검색·judge는 별도입니다. 실패한 행을 분모에서 빼지 않습니다.

### 저장된 결과 평가·보고서·trace

```bash
python scripts/workshop.py benchmark evaluate --policy --label wf-baseline --confirm-cost
```

**저장된 결과로 HTML 보고서 생성 · `wf-baseline`**

```bash
python scripts/workshop.py benchmark report --label wf-baseline
```

**trace 조회용 KQL 확인 · `wf-baseline`**

```bash
python scripts/workshop.py benchmark trace-plan --label wf-baseline
```

**실제 trace 조회 · `wf-baseline`**

```bash
python scripts/workshop.py benchmark monitor --label wf-baseline
```

`trace-plan`은 KQL 작성, `monitor`는 연결된 App Insights 실제 조회입니다. 응답의 Trace ID만 있는 것을 export 검증으로 대신하지 않습니다.

**먼저 브라우저로 열 파일**

`outputs/benchmarks/wf-baseline/report.html`

전체 업무 검사와 실패 사례를 표로 읽습니다. 같은 폴더의 `business-evaluation.json`에서 `expected_rows: 6`, `actual_rows: 6`, `errors`, `models.primary.checks`도 확인합니다.

**서로 다른 증거:** HTML의 업무 검사, `foundry-policy/`의 judge 결과, 실제 조회한 trace. 어느 하나로 나머지를 대신하지 않습니다.

## 7. candidate는 지침만 변경

### v2 패키지·새 버전 배포

```bash
python scripts/workshop.py --script package-hosted --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations
```

**같은 agent 이름**으로, v2 패키지를 사용하는 **새 matrix-v2 폴더**를 5절과 같이 준비·배포합니다. 기존 v1 폴더를 덮어쓰지 않습니다. 새 실제 버전/Invocations Endpoint로 두 설정값을 갱신합니다.

```bash
python scripts/selfstudy.py prepare-hosted --kind matrix --package "실제-v2-패키지-경로" --name matrix --run v2
```

**준비한 서비스만 원격 배포**

```bash
azd deploy "내-prefix-matrix" --cwd "실제-matrix-v2-절대경로"
```

**배포된 실제 버전과 런타임 ID 조회**

```bash
azd ai agent show "내-prefix-matrix" --cwd "실제-matrix-v2-절대경로" --output json
```

### 새 버전 연결·smoke

새 버전과 그 런타임 ID의 5절 역할을 확인한 뒤 binding을 갱신하고 **한 건의 smoke부터** 실행합니다.

```bash
python scripts/selfstudy.py bind-matrix --directory "실제-matrix-v2-폴더" --service "같은-matrix-서비스-이름"
```

**연결한 버전에 한 건 요청 · `matrix-v2-smoke`**

```bash
python scripts/workshop.py benchmark smoke --label matrix-v2-smoke --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --case D01 --model-key primary --confirm-cost
```

### 전체 dev 수집·전후 비교

smoke 성공을 확인한 뒤 전체 dev를 수집합니다. 명시적 로컬 경로를 선택했다면 여기서도 `local`을 유지합니다.

```bash
python scripts/workshop.py benchmark collect --label wf-candidate --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
```

**저장된 전후 결과 비교**

```bash
python scripts/workshop.py benchmark compare --baseline wf-baseline --candidate wf-candidate
```

**저장된 응답을 policy judge로 평가 · `wf-candidate`**

```bash
python scripts/workshop.py benchmark evaluate --policy --label wf-candidate --reference wf-baseline --confirm-cost
```

**저장된 결과로 HTML 보고서 생성 · `wf-candidate`**

```bash
python scripts/workshop.py benchmark report --label wf-candidate
```

**실제 trace 조회 · `wf-candidate`**

```bash
python scripts/workshop.py benchmark monitor --label wf-candidate
```

모델 map·코드·언어·데이터·검색·동시성·judge 조건을 유지합니다. 반환 근거가 달라졌다면 지침만의 개선이라고 주장하지 않습니다.

후보 보고서는 `outputs/benchmarks/wf-candidate/report.html`입니다. SDK 결과인 `outputs/candidate/`나 baseline 보고서와 혼동하지 않습니다.

## 8. Judge calibration과 회귀

**07에서 같은 policy calibration을 마쳤다면 다시 실행하지 않습니다.**

`outputs/judge-calibration/policy-calibration-ko/calibration.json`

이 파일과 같은 폴더의 manifest/catalog에서 언어·judge·criteria/catalog hash가 일치하는지 확인한 뒤 재사용합니다.

<details>
<summary>Calibration이 없거나 조건이 달라졌을 때만</summary>

아래는 그 label이 아직 없을 때만 실행합니다. 조건이 달라졌다면 새 label과 맞는 평가 조건을 사용하고 이후 인수 명령에도 그 label을 지정합니다.

```bash
python scripts/workshop.py calibrate-judge --policy --label policy-calibration-ko --confirm-cost --timeout 900
```

</details>

**8개 control × 3개 기준의 기대 판정 24개**를 읽습니다. 부정 control은 낮은 점수가 맞으므로 24개 모두 높은 점수를 받는 것이 목표가 아닙니다. 이 작은 calibration만으로 실제 dev·matrix 품질을 통과 처리하지 않습니다.

모든 dev 업무 검사가 통과했다면 `regression`은 생략합니다. **실제 dev 실패가 있을 때만** 해당 row를 검토 기록으로 남깁니다.

<details>
<summary>실제 dev 실패가 있을 때만: 회귀 사례 등록</summary>

```bash
python scripts/workshop.py benchmark regression --label wf-baseline --row-id "실제-실패-row-ID" --regression-label reviewed-failure --reviewer "내-실습-ID" --reason "실제 응답과 근거에 기반한 이유" --confirm-review
```

reviewer 문자열은 Entra로 검증된 업무 승인자가 아닙니다. 회귀 파일 생성만으로 다음 수집에 자동 적용되지 않습니다.

후속 dev 수집에서 `--regressions reviewed-failure`를 명시할 때만 사용됩니다. 예시를 실행하려고 실패나 row ID를 만들지 않습니다.

</details>

## 9. 유지와 중지

```bash
python scripts/workshop.py benchmark stop-session --label wf-baseline
```

**해당 실행의 세션 중지 · `wf-candidate`**

```bash
python scripts/workshop.py benchmark stop-session --label wf-candidate
```

원시 결과·실제 버전·업무/native/trace/calibration 상태를 보관합니다. **holdout은 15장에 남겨 둡니다.** 실패한 candidate를 통과한 것으로 바꾸지 않고 미완료 인수로 남길 수 있습니다.

별도 smoke 요청의 세션은 [08의 세션 목록/중지](08-hosted.md#6-정확한-원격-버전-호출)로 확인합니다. 수집·평가가 실패해도 세션 중지는 생략하지 않습니다.

## 10. 별도의 policy-lab 진단 8문항

이 suite는 **보완용 합성 진단 8문항**입니다.

> [!IMPORTANT]
> 13의 **관리형 AI red teaming이 기본 검증 대상**입니다. 이 8문항은 관리형 실행의 대체물이나 증거가 아닙니다. Core dev·holdout도 대신하지 않으므로 `--unlock-holdout`을 사용하지 않습니다.

새 NC에서 준비·smoke한 정확한 배포와 프로필을 사용합니다. `nc-policy-lab-ko` 같은 새 label을 정했다면 모든 참조에 동일하게 적용합니다.

**IQ 경로 — 로컬 검색을 선택했다면 아래의 접힌 대안만 실행**

```bash
python scripts/workshop.py benchmark collect --suite policy-lab --label policy-lab-iq-ko --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
```

**저장된 응답을 policy judge로 평가 · `policy-lab-iq-ko`**

```bash
python scripts/workshop.py benchmark evaluate --policy --label policy-lab-iq-ko --confirm-cost
```

**저장된 진단 결과 확인 · `policy-lab-iq-ko`**

```bash
python scripts/workshop.py benchmark policy-report --label policy-lab-iq-ko --calibration policy-calibration-ko
```

<details>
<summary>로컬 검색을 선택했을 때만: 위 IQ 진단 대신 실행</summary>

명시적으로 선택한 로컬 경로에서는 다음을 대신 사용합니다. 두 진단을 연달아 실행하거나 IQ 결과로 표시하지 않습니다.

```bash
python scripts/workshop.py benchmark collect --suite policy-lab --label policy-lab-local-ko --kind workflow --pattern sequential --retrieval local --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
```

**저장된 응답을 policy judge로 평가 · `policy-lab-local-ko`**

```bash
python scripts/workshop.py benchmark evaluate --policy --label policy-lab-local-ko --confirm-cost
```

**저장된 진단 결과 확인 · `policy-lab-local-ko`**

```bash
python scripts/workshop.py benchmark policy-report --label policy-lab-local-ko --calibration policy-calibration-ko
```

</details>

**보고서 읽기:** `policy-report`는 저장된 결과를 읽으며 새 추론을 하지 않습니다.

- **행 수:** 요청·반환·누락·오류를 모두 확인합니다. 오류·미채점 행도 분모에서 빼지 않습니다.
- **점수:** 세 기준의 점수와 설명을 읽습니다.
- **근거:** source/reference 감사와 일치하는 policy calibration을 함께 확인합니다.

> [!IMPORTANT]
> `policy_compliance`는 **높을수록 규정 준수**이며, 4 미만은 위반 방향입니다. 반대로 읽거나 서비스의 기존 `attack_success` 값을 고치지 않습니다.

Suite version 2는 두 언어 모두 **PL05·PL06·PL07의 명시적 `allowed_citations`** 안에서만 추가 근거를 허용합니다. 목록은 알려진 중복 없는 ID로 필수 참조를 모두 포함하며, 답변의 필수 참조 누락과 무관한 인용은 거부합니다.

<details>
<summary>참고: PL06의 이전 결과와 수정된 v2 결과</summary>

PL06의 절차 전용 질문은 수정된 v2 지침으로 `limit_krw: null`을 반환했습니다.

이전 동결 version 1 결과는 그대로 읽을 수 있습니다. 추가 인용 거부와 `150000` 응답·점수·source·label은 변경하지 않습니다.

</details>

이 8문항은 새 holdout이나 관리형 red-team scan이 아닙니다. 결과 확인 뒤에는 **실제로 사용한 label 하나**로 세션을 중지하고 [만료 전 증거 보관](advanced/session-files.md)을 진행합니다. 로컬 경로라면 아래 label을 `policy-lab-local-ko`로 바꿉니다.

```bash
python scripts/workshop.py benchmark stop-session --label policy-lab-iq-ko
```

## 완료 확인

- [ ] 대화 평가와 Optimizer의 실제 결과를 읽고, 후보 생성과 개선 입증을 구분했다.
- [ ] Hosted 전후 쌍의 지침 외 조건·전체 6행·업무 검사·policy 점수·trace를 대조했다.
- [ ] 일치하는 calibration과 원문 참조 감사를 확인하고, 8문항 진단을 관리형 검증과 구분했다.
- [ ] 수집·smoke·진단 세션을 중지하고 **holdout은 열지 않았다**.

---

[← 11. 기억·위임·예약](11-memory-a2a-routines.md) · [전체 과정](../README.ko.md#진행-순서) · [13. 실습 안전 →](13-governance.md) · [진행 지도 ↑](#chapter-map)
