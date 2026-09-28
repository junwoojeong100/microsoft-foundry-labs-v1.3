# 12. 대화 평가·Optimizer·배포 품질

[English](en/12-improvement.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 대화 전체를 평가하고, 실제 Hosted 버전을 같은 조건으로 비교합니다.

**시작 조건:** 07장의 judge·dev 결과·policy calibration. Hosted 비교에는 08장의 준비와 09장의 로그가 필요합니다. IQ 경로는 06장의 IQ 조회도 성공해야 합니다.

**실행 위치:** 포털에서 Optimizer, 터미널에서 배포·평가, 브라우저에서 HTML 보고서.

> [!WARNING]
> 배포·모델·평가 비용이 발생합니다. **지침만 바꾸고 holdout은 열지 않습니다.** 실패해도 실행 세션은 9절에서 중지합니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [검색 경로 선택](#iq-또는-로컬-검색을-명시적으로-선택하기) | IQ 또는 local |
| [1. 대화 평가](#1-대화-평가) | 개별 턴과 전체 대화의 차이 |
| [2. Optimizer 준비](#2-optimizer를-위한-모델과-데이터-직접-준비) | 후보 생성 모델과 dev 입력 |
| [3. 지침 최적화](#3-지침만-최적화) | 후보 유무·전체 결과·참조 검사 |
| [4. Hosted 조건 고정](#4-hosted-matrix의-범위-고정) | 같은 모델·검색·API |
| [5. baseline 배포](#5-baseline-프로필-배포) | 정확한 버전과 한 건 호출 |
| [6. baseline 평가](#6-모든-dev-행-수집평가trace) | dev 6행·점수·trace |
| [7. candidate 비교](#7-candidate는-지침만-변경) | 지침만 바꾼 전후 비교 |
| [8. 평가 기준 확인](#8-judge-calibration과-회귀) | calibration과 실제 실패 |
| [9. 세션 중지](#9-유지와-중지) | 결과 보관·실행 중지 |
| [10. 보완 진단](#10-별도의-policy-lab-진단-8문항) | 별도 8문항 결과 |
| [완료 확인](#완료-확인) | 실행 성공과 품질 개선 구분 |

**세 작업은 구분합니다:** 1절은 대화 평가, 2~3절은 지침 후보 생성, 4~9절은 포함된 `v1`/`v2`의 배포 비교입니다. Optimizer 후보가 없어도 준비된 Hosted 비교는 진행할 수 있습니다.

## IQ 또는 로컬 검색을 명시적으로 선택하기

기본은 06장에서 확인한 **IQ**입니다. 아래 조건을 baseline부터 최종 평가까지 유지합니다.

| 고정할 것 | 바꿀 것 |
|---|---|
| 코드·모델·원문·언어·검색·API·judge·점수 기준·생성 설정 | 지침 `v1` → `v2`만 |

코드나 데이터까지 바뀌었다면 새 label로 전후 쌍을 다시 만듭니다. 이전 결과의 hash를 편집하지 않습니다.

<details>
<summary>IQ가 준비되지 않았을 때만: local 검색 경로</summary>

이 경로도 원격 Hosted와 모델 호출을 사용합니다. 검색만 로컬 문서로 바뀌며 **IQ 성공으로 기록하지 않습니다.**

| 항목 | 기본 경로 | 이 대안 |
|---|---|---|
| 패키징·benchmark의 `--retrieval` | `iq` | `local` |
| 준비 명령의 `--name` | `matrix` | `matrix-local` |
| IQ 관련도 문턱 설정 | 수행 | 생략 |

**첫 패키지**

```bash
python scripts/workshop.py --script package-hosted --kind workflow --pattern sequential --retrieval local --prompt v1 --api account-chat --protocol invocations
```

**첫 준비 폴더**

```bash
python scripts/selfstudy.py prepare-hosted --kind matrix --package "실제-local-v1-패키지-경로" --name matrix-local --run v1
```

이후 v2·dev·15장의 holdout에도 `local`을 유지합니다. 서비스·폴더는 **이 준비 명령의 출력**을 사용합니다. `wf-baseline`/`wf-candidate` label은 선택한 한 경로에서만 사용합니다.

</details>

## 1. 대화 평가

**계획 확인**

```bash
python scripts/workshop.py conversations plan
```

**대화 수집**

```bash
python scripts/workshop.py conversations collect --label conversations-first --prompt v2 --confirm-cost
```

**저장된 대화 확인**

```bash
python scripts/workshop.py conversations report --label conversations-first
```

수집한 대화와 오류를 먼저 확인합니다. 요청이 누락됐다면 평가로 넘어가지 않습니다.

**개별 턴 평가 — 질문·답변 한 차례씩**

```bash
python scripts/workshop.py conversations evaluate --label conversations-first --level turn --confirm-cost
```

**전체 대화 평가**

```bash
python scripts/workshop.py conversations evaluate --label conversations-first --level conversation --confirm-cost
```

**확인:** 같은 대화의 두 평가를 읽습니다. 개별 답변이 맞아도 앞뒤 답변이 모순되거나 전체 요청을 해결하지 못할 수 있습니다. 독립 사례 사이에 Memory·대화 상태를 공유하지 않습니다.

## 2. Optimizer를 위한 모델과 데이터 직접 준비

Optimizer는 더 나은 지침 **후보를 만드는 기능**입니다. 후보 생성 자체가 개선을 보장하지 않습니다.

1. Foundry 에이전트의 **Optimize** 화면에서 지원 모델을 확인합니다.
2. 같은 계정에 `gpt-5.5` / `2026-04-24`를 `workshop-optimizer`로 배포합니다.
3. 답변 대상은 Sol, judge는 07장의 별도 GPT-5.5 배포를 유지합니다.
4. 모델을 등록합니다.

```bash
python scripts/selfstudy.py model --role optimizer
```

**입력은 07장의 `outputs/policy-inputs-ko/`를 재사용**합니다.

| 파일 | 확인할 내용 |
|---|---|
| `optimizer-dev.jsonl` | dev 6행과 평가자용 `ground_truth` |
| `policy-evaluator-definitions.json`, manifest | 언어·원문·지침·평가 기준의 일치 |

입력이 없거나 조건이 바뀌었다면 [07장의 준비·calibration](07-evaluation.md#5-원문-참조를-감사하는-policy-평가)부터 수행합니다. holdout은 사용하지 않습니다.

## 3. 지침만 최적화

### 별도 target 준비

최적화할 별도 에이전트를 만듭니다. `YOUR-PREFIX`는 내 접두사입니다. 이미 만들었다면 저장한 이름·버전을 재사용합니다.

```bash
python scripts/workshop.py prompt-agent create --name "YOUR-PREFIX-optimize-ko" --confirm-create --output outputs/learner-notes-ko/12-optimizer-agent.json
```

### 포털: 최적화 한 번 제출

1. **Build → Agents**에서 방금 만든 이름·버전을 엽니다.
2. **Optimize / Create optimization run → Agent**를 선택합니다.
3. 대상 버전·답변 모델을 고정합니다. 최적화 대상은 **Instruction만**, 최대 후보는 **2**로 정합니다.
4. 2절의 `optimizer-dev.jsonl`을 업로드합니다.
5. 07장의 calibration과 같은 세 policy 평가자·버전을 선택합니다. **각 평가자에 `workshop-judge`, 통과점 4**를 지정합니다.
6. `query`·`response`·`ground_truth` 연결을 확인합니다. `ground_truth`의 원문 참조는 평가자용이며 대상 에이전트 입력이 아닙니다. 현재 wizard는 열 이름 재매핑을 지원하지 않습니다.
7. 비용을 확인하고 **한 번만** 제출합니다.
8. baseline과 모든 전체 후보의 지침·평가 결과를 읽습니다.

> [!WARNING]
> 후보 최대 2개는 모델 호출 2회가 아닙니다. 반복 평가와 소규모 묶음 평가(minibatch)가 추가 호출을 만듭니다.

필수 평가 조건을 설정할 수 없거나 비용을 수락하지 않으면 중지합니다. 후보 0개·동점은 **개선 미입증**으로 남깁니다. 후보를 Hosted에 자동 적용하지 않습니다.

### 터미널: 전체 결과 내보내기·감사

Optimizer의 평가 결과에서 **실제 evaluation ID와 run ID**를 확인합니다. 각 전체 결과를 서로 다른 새 label로 내보냅니다.

```bash
python scripts/workshop.py --script export-evaluation --language ko --evaluation-id "실제-eval-ID" --run-id "실제-evalrun-ID" --expected-rows 6 --label optimizer-policy-export-ko
```

**업로드한 원본·같은 calibration으로 참조 검사**

```bash
python scripts/audit_optimizer.py --export-directory outputs/evaluation-exports/optimizer-policy-export-ko --dataset outputs/policy-inputs-ko/optimizer-dev.jsonl --calibration-label policy-calibration-ko --language ko --output outputs/optimizer-policy-audit-ko.json
```

이 검사는 저장 파일만 읽으며 모델을 호출하지 않습니다.

**확인:** `validation_status: valid`, **6/6 원문 일치**, `internal_judge_requests_captured: false`를 확인합니다. 이는 반환된 원문 참조 검사이지 숨겨진 judge 요청의 캡처나 품질 개선 증거가 아닙니다.

생성된 전체 후보마다 별도로 내보내고 검사합니다. 후보가 없으면 후보 파일을 만들지 않습니다. 누락 행이나 `context=response`인 자기 근거를 정상 평가로 인정하지 않습니다.

SDK 초기화·입력 형식·job 조회 오류는 [평가 문제 해결](troubleshooting.md#evaluation), 과거 결과는 [검증 보고서](validation-report.md)를 확인합니다. 서버 job이 이미 있다면 새로 제출하지 않고 **같은 ID를 조회**합니다.

## 4. Hosted matrix의 범위 고정

matrix는 **같은 문항을 배포 버전별로 실행해 비교하는 결과 묶음**입니다. 07장의 SDK 결과와 구분합니다.

이번 프로필은 `workflow / sequential / iq / account-chat / invocations`입니다. 08장의 Responses 프로필과 다르므로 새 패키지·준비 폴더가 필요합니다.

**저장된 설정 확인**

```bash
python scripts/selfstudy.py status
```

`AZURE_OPENAI_ENDPOINT`가 없다면 같은 Foundry 계정의 **OpenAI 서비스 루트**를 등록합니다. `/openai/v1`은 제외합니다.

```bash
python scripts/selfstudy.py set AZURE_OPENAI_ENDPOINT "실제-같은-계정의-OpenAI-루트-URL"
```

**비교 대상은 Sol 하나로 고정**

```bash
python scripts/selfstudy.py models primary=workshop-chat
```

다른 이름의 Sol을 사용했다면 `workshop-chat`만 실제 배포 이름으로 바꿉니다. **judge를 비교 대상에 넣지 않습니다.** Luna 비교는 02·07장의 계정 Responses 경로에서 따로 진행합니다.

## 5. baseline 프로필 배포

### 프로필 패키징·배포

**IQ 검색 조건 고정** — local 경로라면 이 설정은 생략합니다.

```bash
python scripts/selfstudy.py set WORKSHOP_IQ_RERANKER_THRESHOLD 0
```

**`v1` 패키징**

```bash
python scripts/workshop.py --script package-hosted --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations
```

**새 폴더 준비**

```bash
python scripts/selfstudy.py prepare-hosted --kind matrix --package "실제-v1-패키지-경로" --name matrix --run v1
```

**출력된 서비스 배포**

```bash
azd deploy "내-prefix-matrix" --cwd "실제-matrix-v1-절대경로"
```

**새 버전·런타임 ID 조회**

```bash
azd ai agent show "내-prefix-matrix" --cwd "실제-matrix-v1-절대경로" --output json
```

### 이 버전의 런타임 역할 확인

반환된 `instance_identity.principal_id`에 필요한 역할을 확인합니다.

| 접근 대상 | 역할과 범위 |
|---|---|
| 프로젝트 | 프로젝트의 Foundry User |
| 계정 OpenAI API | 부모 Foundry 계정의 **Cognitive Services OpenAI User** |
| IQ 검색 | 실습 Search의 Search Index Data Reader |

`selfstudy.py roles`의 기본 Hosted 계획에는 계정 OpenAI 역할이 없습니다. **프로젝트 역할만 부여하고 넘어가지 않습니다.**

Cognitive Services OpenAI User의 역할 ID는 `5e0bd9bd-7b93-4f28-af87-19fc36ad61bd`입니다. 없는 역할만 해당 자원 범위에 부여합니다.

### 실제 버전 연결·한 건 호출

**배포 버전·주소를 읽어 저장**

```bash
python scripts/selfstudy.py bind-matrix --directory "실제-matrix-v1-폴더" --service "실제-matrix-서비스-이름"
```

**smoke — 전체 평가 전 한 건 호출**

```bash
python scripts/workshop.py benchmark smoke --label matrix-v1-smoke --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations --case D01 --model-key primary --confirm-cost
```

**확인:** 정확한 배포 버전의 응답과 D01 근거를 확인합니다. 실패하면 6절로 가지 않습니다. 실제 런타임 권한·프로필·원래 로그를 확인하고 세션을 중지합니다.

## 6. 모든 dev 행 수집·평가·trace

**계획 확인**

```bash
python scripts/workshop.py benchmark plan --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations
```

**dev 수집**

```bash
python scripts/workshop.py benchmark collect --label wf-baseline --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
```

**확인:** Sol 한 개의 기본 dev는 **6행**입니다. 누락·요청 오류가 있으면 원인을 해결하기 전 평가로 넘어가지 않습니다.

**업무·policy 평가**

```bash
python scripts/workshop.py benchmark evaluate --policy --label wf-baseline --confirm-cost
```

**HTML 보고서 생성**

```bash
python scripts/workshop.py benchmark report --label wf-baseline
```

**로그 조회문(KQL) 확인**

```bash
python scripts/workshop.py benchmark trace-plan --label wf-baseline
```

**실제 로그 조회**

```bash
python scripts/workshop.py benchmark monitor --label wf-baseline
```

| 확인할 위치 | 읽을 내용 |
|---|---|
| `outputs/benchmarks/wf-baseline/report.html` | 브라우저에서 업무 검사·실패 사례 |
| 같은 폴더의 `business-evaluation.json` | `expected_rows: 6`, `actual_rows: 6`, 오류, `models.primary.checks` |
| `foundry-policy/` | 세 평가 기준의 점수·설명·원문 참조 검사 |
| `monitor` 결과 | 실제 trace 조회 결과 |

Trace ID나 KQL 파일만 있다고 로그 조회에 성공한 것은 아닙니다.

## 7. candidate는 지침만 변경

### v2 패키지·새 버전 배포

**`v2` 패키징**

```bash
python scripts/workshop.py --script package-hosted --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations
```

**같은 에이전트 이름, 새 준비 폴더**

```bash
python scripts/selfstudy.py prepare-hosted --kind matrix --package "실제-v2-패키지-경로" --name matrix --run v2
```

**새 버전 배포**

```bash
azd deploy "내-prefix-matrix" --cwd "실제-matrix-v2-절대경로"
```

**버전·런타임 ID 조회**

```bash
azd ai agent show "내-prefix-matrix" --cwd "실제-matrix-v2-절대경로" --output json
```

5절의 역할을 **이번 런타임 ID**에도 확인합니다. 이전 v1 폴더·기록은 유지합니다.

### 새 버전 연결·smoke

```bash
python scripts/selfstudy.py bind-matrix --directory "실제-matrix-v2-폴더" --service "같은-matrix-서비스-이름"
```

**한 건 호출**

```bash
python scripts/workshop.py benchmark smoke --label matrix-v2-smoke --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --case D01 --model-key primary --confirm-cost
```

### 전체 dev 수집·전후 비교

smoke 성공 후 진행합니다. local을 선택했다면 여기서도 모든 `--retrieval`에 `local`을 사용합니다.

```bash
python scripts/workshop.py benchmark collect --label wf-candidate --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
```

6행과 요청 오류를 확인합니다.

**전후 비교**

```bash
python scripts/workshop.py benchmark compare --baseline wf-baseline --candidate wf-candidate
```

**policy 평가**

```bash
python scripts/workshop.py benchmark evaluate --policy --label wf-candidate --reference wf-baseline --confirm-cost
```

**보고서 생성**

```bash
python scripts/workshop.py benchmark report --label wf-candidate
```

**실제 로그 조회**

```bash
python scripts/workshop.py benchmark monitor --label wf-candidate
```

**확인:** `outputs/benchmarks/wf-candidate/report.html`을 baseline과 비교합니다. SDK의 `outputs/candidate/`와 혼동하지 않습니다.

양쪽 모델·코드·데이터·검색·동시성·judge가 같아야 합니다. 실제 반환 근거까지 달라졌다면 지침만으로 개선됐다고 단정하지 않습니다.

## 8. Judge calibration과 회귀

07장의 `outputs/judge-calibration/policy-calibration-ko/calibration.json`을 읽습니다. 언어·judge·기준·catalog hash가 같다면 **다시 호출하지 않습니다**.

<details>
<summary>Calibration이 없거나 조건이 달라졌을 때만</summary>

같은 label의 결과가 없다면 실행합니다. 조건이 달라졌다면 새 label을 사용하고 이후 최종 확인에도 그 이름을 지정합니다.

```bash
python scripts/workshop.py calibrate-judge --policy --label policy-calibration-ko --confirm-cost --timeout 900
```

</details>

**확인:** 8개 사례 × 3개 기준의 기대 판정 24개를 읽습니다. 이는 평가 모델 점검이며 dev 품질 통과와 별개입니다.

<details>
<summary>실제 dev 실패가 있을 때만: 회귀 사례 기록</summary>

회귀 사례는 이후 변경에서 같은 실패가 재발하는지 확인할 사례입니다.

```bash
python scripts/workshop.py benchmark regression --label wf-baseline --row-id "실제-실패-row-ID" --regression-label reviewed-failure --reviewer "내-실습-ID" --reason "실제 응답과 근거에 기반한 이유" --confirm-review
```

후속 수집에 `--regressions reviewed-failure`를 지정해야 사용됩니다. 자동 적용이나 실제 업무 승인이 아닙니다. 실패가 없으면 생략합니다.

</details>

## 9. 유지와 중지

**생성된 실행의 세션만 중지합니다. 실패한 실행도 포함합니다.**

```bash
python scripts/workshop.py benchmark stop-session --label wf-baseline
```

**candidate 세션 중지**

```bash
python scripts/workshop.py benchmark stop-session --label wf-candidate
```

smoke·수동 호출 세션은 [08장의 목록·중지 절차](08-hosted.md#6-정확한-원격-버전-호출)로 확인합니다. 원시 결과·버전·점수·trace를 보관하고 **holdout은 15장까지 열지 않습니다**.

## 10. 별도의 policy-lab 진단 8문항

이 8문항은 **보완 진단**입니다. core dev·holdout이나 13장의 관리형 AI red teaming을 대신하지 않습니다.

이번 v2 배포와 같은 프로필을 사용합니다. **IQ 또는 local 중 선택한 한 경로만** 실행합니다.

**IQ 진단 수집**

```bash
python scripts/workshop.py benchmark collect --suite policy-lab --label policy-lab-iq-ko --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
```

**평가**

```bash
python scripts/workshop.py benchmark evaluate --policy --label policy-lab-iq-ko --confirm-cost
```

**저장된 결과 보고서**

```bash
python scripts/workshop.py benchmark policy-report --label policy-lab-iq-ko --calibration policy-calibration-ko
```

<details>
<summary>local을 선택했을 때만: 위 IQ 명령 대신 실행</summary>

```bash
python scripts/workshop.py benchmark collect --suite policy-lab --label policy-lab-local-ko --kind workflow --pattern sequential --retrieval local --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
```

**평가**

```bash
python scripts/workshop.py benchmark evaluate --policy --label policy-lab-local-ko --confirm-cost
```

**저장된 결과 보고서**

```bash
python scripts/workshop.py benchmark policy-report --label policy-lab-local-ko --calibration policy-calibration-ko
```

</details>

**확인:** 실제 8행·오류·누락, 세 기준 점수·설명, 참조 검사, 같은 calibration을 확인합니다. `policy_compliance`는 **4 이상 통과, 높을수록 좋음**입니다.

추가 인용과 `limit_krw: null` 같은 구조화 규칙은 [데이터 형식](data-format.md#진단-사례의-인용과-구조화-필드)을 따릅니다. 이전 결과나 서비스의 `attack_success` 값을 수정하지 않습니다.

**실제로 사용한 진단 세션 중지** — local 경로는 label을 `policy-lab-local-ko`로 바꿉니다.

```bash
python scripts/workshop.py benchmark stop-session --label policy-lab-iq-ko
```

실패해도 세션을 확인하고 [만료 전에 증거를 보관](advanced/session-files.md)합니다.

## 완료 확인

- [ ] 대화 평가와 Optimizer의 실제 결과를 읽고 후보 생성과 개선을 구분했다.
- [ ] Hosted 전후 쌍의 조건·6행·업무 검사·policy 점수·trace를 대조했다.
- [ ] 같은 calibration·원문 참조를 확인하고 보완 진단과 관리형 검증을 구분했다.
- [ ] 수집·smoke·진단 세션을 중지했고 holdout은 열지 않았다.

---

[← 11. 기억·위임·예약](11-memory-a2a-routines.md) · [전체 과정](../README.ko.md#진행-순서) · [13. 실습 안전 →](13-governance.md) · [진행 지도 ↑](#chapter-map)
