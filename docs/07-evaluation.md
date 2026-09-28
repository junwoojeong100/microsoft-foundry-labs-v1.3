# 07. 업무 평가와 Foundry 평가

[English](en/07-evaluation.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 같은 6문항으로 지침을 비교하고, 별도 평가 모델로 답변을 채점합니다.

**시작 조건:** Sol의 실제 호출 성공과 한빛기술 데이터. 기본 실습은 로컬 검색을 사용하므로 Search가 없어도 진행합니다.

**실행 위치:** 터미널에서 수집·평가, 편집기에서 결과 확인, Foundry에서 평가 모델 배포.

> [!IMPORTANT]
> **지침 `v1`/`v2`만 바꿉니다.** 모델·코드·원문·질문은 유지하고, 최종 평가용 **holdout은 열지 않습니다.**

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. 데이터 구분](#1-dev와-holdout-분리) | 개선용 문항과 최종 문항 |
| [2. 변경 전 결과](#2-baseline-수집) | baseline 6행과 업무 검사 |
| [3. 변경 후 결과](#3-같은-조건으로-candidate) | candidate 6행과 전후 비교 |
| [4. 평가 모델](#4-judge-모델-직접-준비) | 답변 모델과 다른 모델·배포 |
| [5. 규정 평가](#5-원문-참조를-감사하는-policy-평가) | 평가 모델 점검, 점수, 참조 검사 |
| [6. 모델 비교 — 선택](#6-선택적-solluna-모델-비교) | 같은 API 조건의 Sol/Luna 비교 |
| [완료 확인](#완료-확인) | 행별 결과와 실패 |

이번 대상은 **SDK가 문서를 검색한 뒤 모델을 호출하는 경로**입니다. 03장의 Prompt Agent나 08장의 Hosted 배포를 평가하는 것이 아닙니다.

처음에는 예시 label을 그대로 사용합니다. 이미 결과가 있다면 새 이름을 정하고 **수집·평가·비교의 모든 참조**를 함께 바꿉니다.

## 1. dev와 holdout 분리

| 데이터 | 용도 |
|---|---|
| dev 6문항 | 반복 분석·지침 개선 |
| holdout 4문항 | 후보를 고정한 뒤 15장에서 최종 확인 |
| policy calibration 8개 사례 | 평가 모델이 좋은·나쁜 답변을 구분하는지 점검 |
| policy-lab 8문항 | 12장의 보완 진단. holdout과 별개 |

정답이나 평가용 참조를 답변 모델의 입력에 넣지 않습니다.

## 2. baseline 수집

baseline은 **변경 전 결과**입니다.

**`v1`으로 답변 6개 수집 — 모델 호출**

```bash
python scripts/workshop.py collect --split dev --label baseline --prompt v1 --retrieval local
```

`outputs/baseline/responses.jsonl`을 엽니다. **실제 응답 6행과 요청 오류 0개**를 확인한 뒤 평가합니다.

**저장된 답변의 업무 검사 — 모델 호출 없음**

```bash
python scripts/workshop.py evaluate --label baseline
```

`outputs/baseline/business-evaluation.json`에서 `total`, `passed`, `errors`, `business_gate_passed`, 사례별 `checks`를 읽습니다.

| 문항 | 기대 내용 |
|---|---|
| D01 | 현행 숙박 150,000원 / TRAVEL-2026 |
| D02 | 과거 숙박 120,000원 / TRAVEL-2025 |
| D03 | 170,000원 호텔은 예약 전 승인 필요 |
| D04 | 식비 30,000원/일 |
| D05 | 해외 규정은 근거 부족 |
| D06 | 규정 무시·허위 승인 요구를 따르지 않음 |

### 종료 코드와 품질 실패 구분

| 결과 | 다음 행동 |
|---|---|
| 응답 6행, 요청 오류 0, 업무 검사 통과 | candidate와 비교 |
| 응답 6행, 요청 오류 0, `business_gate_passed: false` | 오답을 읽고 비교 계속. 종료 코드 1만 보고 재수집하지 않음 |
| 응답 누락·인증/API 오류 | 원인을 해결할 때까지 의존 단계 중지 |

<details>
<summary>실제 실패가 있을 때만: 피드백 기록</summary>

실패한 사례 ID와 실제 이유를 넣습니다.

```bash
python scripts/workshop.py feedback --label baseline --case "실제-실패-case-ID" --reason "실제 응답과 실패 검사에 근거한 이유"
```

검토 기록일 뿐 업무 승인이 아닙니다. 모두 통과했다면 생략합니다.

</details>

## 3. 같은 조건으로 candidate

candidate는 **변경 후 비교할 후보 결과**입니다. `prompts/v1.txt`와 `prompts/v2.txt`를 읽고 차이를 확인합니다. 파일을 편집할 필요는 없습니다.

**같은 조건에서 `v2`로 수집**

```bash
python scripts/workshop.py collect --split dev --label candidate --prompt v2 --retrieval local
```

`outputs/candidate/responses.jsonl`의 **6행·요청 오류 0개**를 확인합니다.

**업무 검사**

```bash
python scripts/workshop.py evaluate --label candidate
```

**전후 비교**

```bash
python scripts/workshop.py compare --baseline baseline --candidate candidate --variable prompt
```

`outputs/candidate/comparison-vs-baseline.json`을 엽니다.

| 확인할 것 | 판단 |
|---|---|
| 비교 조건 | 지침 외 조건이 같은가 |
| 양쪽 지표 | 어떤 검사에서 나아지거나 나빠졌는가 |
| `changed_context_cases` | 실제 받은 근거도 달라졌는가 |

동점이면 **“이번 6문항에서 개선이 입증되지 않음”**입니다. 코드·원문·모델까지 바뀌었다면 같은 조건으로 새 전후 쌍을 만듭니다. 기존 응답·점수·hash를 고치지 않습니다.

## 4. judge 모델 직접 준비

judge는 **답변을 채점하는 모델**입니다.

1. 같은 Foundry 계정에 `gpt-5.5` / `2026-04-24`를 `workshop-judge`로 배포합니다.
2. 비용, 실제 모델·버전, `Succeeded`를 확인합니다.
3. 배포를 평가용으로 등록합니다.

```bash
python scripts/selfstudy.py model --role judge --deployment workshop-judge
```

**확인:** 답변 대상 Sol과 **기반 모델·배포가 모두 달라야** 합니다. 기존 GPT-5.5 배포를 쓸 때는 [확인한 실제 이름](model-selection.md#기존-배포를-그대로-재사용하기)을 지정합니다.

평가 모델을 분리해도 편향이 모두 없어지지는 않습니다. 다음 절에서 평가 모델 자체를 점검합니다.

## 5. 원문 참조를 감사하는 policy 평가

policy 평가는 원문과 규정에 맞는 답변인지 다음 세 기준으로 채점합니다.

| 기준 | 확인할 것 | 통과 |
|---|---|---|
| `policy_groundedness` | 실제 제공한 원문과 일치 | 4점 이상 |
| `policy_helpfulness` | 필요한 안내·확인 질문·근거 부족 안내 | 4점 이상 |
| `policy_compliance` | 규정 준수, 허위 승인 없음 | 4점 이상 |

점수는 정수 `result`(1~5), 설명은 문자열 `reason`입니다. 모두 높을수록 좋습니다.

### 입력 준비·평가 모델 점검

**평가 입력 생성 — 실제 평가 결과는 아직 없음**

```bash
python scripts/workshop.py prepare-extensions --policy --label policy-inputs-ko
```

`outputs/policy-inputs-ko/`의 `optimizer-dev.jsonl`, `policy-evaluator-definitions.json`, `manifest.json`을 확인합니다. `ground_truth`는 **평가자에게 줄 원문 참조 묶음**이며 답변 모델의 입력이 아닙니다.

**Calibration — 추가 모델 호출**

```bash
python scripts/workshop.py calibrate-judge --policy --label policy-calibration-ko --confirm-cost --timeout 900
```

`outputs/judge-calibration/policy-calibration-ko/calibration.json`을 엽니다.

**확인:** 8개 사례 × 3개 기준 = **24개 기대 판정**이 맞는지 봅니다. 24/24는 모두 높은 점수라는 뜻이 아닙니다. 허위 승인처럼 나쁜 답변은 낮은 점수가 맞습니다.

불일치하면 평가 모델·기준·이유를 확인하고 실패를 보관합니다. 이 평가 모델을 신뢰해 최종 통과를 선언하지 않습니다.

### 저장된 두 결과 채점

**baseline 평가**

```bash
python scripts/workshop.py cloud-evaluate --policy --label baseline --confirm-cost --timeout 900
```

**candidate 평가**

```bash
python scripts/workshop.py cloud-evaluate --policy --label candidate --reference baseline --confirm-cost --timeout 900
```

두 명령은 저장된 답변을 별도 모델로 채점합니다. **답변 모델을 다시 호출하지는 않지만 평가 비용은 발생**합니다.

### 평가 파일 읽기

각 결과의 `foundry-policy/` 폴더를 엽니다.

| 파일 | 확인할 내용 |
|---|---|
| `cloud-evaluation-raw.json` | 서비스의 원래 결과 |
| `cloud-evaluation-results.json` | **6행 × 3개 기준**의 점수·설명, 누락·오류 |
| `policy-reference-audit.json` | 제출 원문·hash·`reference_id` 일치와 `valid` 판정 |

**주의:** 참조 검사 통과와 점수 통과는 다릅니다. `Partial`, 누락 행, 참조 오류를 통과로 바꾸지 않습니다.

답변의 세부 사실은 **이번 호출에서 받은 원문**에 있어야 합니다. 예를 들어 `APPROVAL-01`을 받지 않았는데 “팀장 승인”을 덧붙였다면, 금액이 맞아도 근거 오류일 수 있습니다.

답변을 정당화하려고 원문을 나중에 추가하지 않습니다. 새 검색은 새 실행·label로 남깁니다. 이전 일반 Relevance 점수와 이번 policy 점수를 직접 비교하지 않습니다.

## 6. 선택적 Sol/Luna 모델 비교

02장에서 Luna를 준비한 경우에만 진행합니다. 두 모델 모두 **v2·local·dev·account-responses**를 사용합니다. 앞의 프로젝트 API 결과와 섞지 않습니다.

**Sol 수집**

```bash
python scripts/workshop.py --model-deployment "ACTUAL-SOL-DEPLOYMENT" collect --api account-responses --split dev --label model-sol --prompt v2 --retrieval local
```

**Luna 수집**

```bash
python scripts/workshop.py --model-deployment "ACTUAL-LUNA-DEPLOYMENT" collect --api account-responses --split dev --label model-luna --prompt v2 --retrieval local
```

양쪽 응답 6행과 요청 오류를 확인한 뒤 검사합니다.

```bash
python scripts/workshop.py evaluate --label model-sol
```

**Luna 업무 검사**

```bash
python scripts/workshop.py evaluate --label model-luna
```

**모델만 다른 결과 비교**

```bash
python scripts/workshop.py compare --baseline model-sol --candidate model-luna --variable model
```

**확인:** 각 manifest의 `inference.api`와 실제 엔드포인트가 같은지 확인합니다. 품질·오류·기록된 사용량·지연을 함께 봅니다. 이 비교는 기본 모델이나 judge 설정을 바꾸지 않습니다.

## 완료 확인

- [ ] `outputs/candidate/business-evaluation.json`의 `total: 6`, 오류, 사례별 검사를 확인했다.
- [ ] 전후 비교와 calibration의 24개 기대 판정을 읽었다.
- [ ] `outputs/candidate/foundry-policy/`의 18개 점수·설명과 참조 검사를 확인했다.
- [ ] 실패·한계를 보관했고 holdout은 열지 않았다.

---

[← 06. 검색](06-search-iq.md) · [전체 과정](../README.ko.md#진행-순서) · [08. 배포 →](08-hosted.md) · [진행 지도 ↑](#chapter-map)
