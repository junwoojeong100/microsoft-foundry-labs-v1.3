# 02. Sol 지침과 선택적 모델·Router 비교

[English](en/02-models-prompts.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 지침이 바꾸는 것과 문서가 필요한 것을 구분합니다.

**시작 조건:** 01장의 Sol 호출 성공. **1~2절은 기본, 3~4절은 선택**입니다.

**실행 위치:** Foundry Playground. 선택 비교는 포털과 터미널.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. 지침 비교](#1-프롬프트만-바꿔-보기) | 같은 모델의 답변 차이 |
| [2. 근거 없는 질문](#2-지침으로-만들-수-없는-지식) | 회사 규정은 지침만으로 알 수 없음 |
| [3. Luna 비교 — 선택](#3-선택적으로-luna와-비교) | 같은 조건의 두 모델 답변 |
| [4. Router — 선택](#4-선택적으로-router-살펴보기) | 지원 API와 모델 선택 결과 |
| [완료 확인](#완료-확인) | 기본 실습과 선택 비교의 수행 여부 |

## 1. 프롬프트만 바꿔 보기

Playground에서 01장의 Sol 배포를 선택하고 검색 도구를 끕니다.

**첫 번째 새 대화**에 입력합니다.

```text
부산 출장 준비를 도와줘.
```

답변을 읽은 뒤 **두 번째 새 대화**에 입력합니다. 이전 대화를 이어 쓰지 않습니다.

```text
당신은 신입 직원의 출장 준비 도우미입니다.
부산 출장 전에 확인할 것 3개를 정리하세요.
회사 규정, 날짜, 기간은 아직 제공하지 않았습니다.
비용이나 승인 여부를 추측하지 말고 필요한 정보를 되물으세요.
```

**확인:** 두 답변의 길이, 추측한 정보, 확인 질문을 비교합니다. 두 번째 답변이 비용을 단정하거나 정보를 되묻지 않으면 지침을 따르지 못한 사례입니다.

## 2. 지침으로 만들 수 없는 지식

새 대화에서 질문합니다.

```text
한빛기술의 2026년 9월 국내 출장 숙박비 한도는 얼마인가요?
공식 근거도 알려 주세요.
```

**기대 결과:** 규정을 받지 않았으므로 모른다고 답하거나 문서를 요청해야 합니다. 금액이나 인용을 제시해도 원문이 없으면 정답으로 인정하지 않습니다.

**지침은 행동을 정하고, 검색은 근거를 가져옵니다.** 모델 가중치를 바꾸는 파인튜닝과는 다릅니다.

모델 비교를 하지 않는다면 [완료 확인](#완료-확인) 후 03장으로 갑니다.

<a id="3-비교-모델을-직접-준비"></a>

## 3. 선택적으로 Luna와 비교

**추가 배포와 호출 비용이 발생합니다.** 비용을 수락한 경우에만 진행합니다.

1. 같은 Foundry 리소스에서 `gpt-6-luna` / `2026-09-22`를 찾습니다.
2. 리전·할당량·Responses·Structured Outputs 지원을 확인합니다.
3. 배포 이름을 `workshop-compare`로 지정합니다. 같은 이름이 이미 있으면 [기존 이름 사용법](model-selection.md#기존-배포를-그대로-재사용하기)을 따릅니다.
4. 실제 모델·버전과 `Succeeded`를 확인한 뒤 등록합니다.

```bash
python scripts/selfstudy.py model --role comparison --deployment "ACTUAL-LUNA-DEPLOYMENT"
```

`ACTUAL-LUNA-DEPLOYMENT`에는 방금 확인한 배포 이름을 넣습니다. 기본은 `workshop-compare`입니다. 이 명령은 배포를 새로 만들지 않습니다.

같은 Foundry 계정의 **Azure OpenAI endpoint**를 등록합니다. `/openai/v1`이 붙어 있으면 그 경로를 제외한 서비스 루트만 넣습니다.

```bash
python scripts/selfstudy.py set AZURE_OPENAI_ENDPOINT "https://YOUR-FOUNDRY-DOMAIN.openai.azure.com"
```

두 모델에 **같은 지침·질문·로컬 문서·계정 API**를 사용합니다. Sol의 기본 배포 이름은 `workshop-chat`입니다.

**Sol 호출**

```bash
python scripts/workshop.py --model-deployment "ACTUAL-SOL-DEPLOYMENT" answer --api account-responses --prompt v2 --retrieval local --question "2026년 9월 국내 출장 숙박비 한도와 예약 전 절차는?" --output outputs/learner-notes-ko/02-sol-account.json
```

**Luna 호출**

```bash
python scripts/workshop.py --model-deployment "ACTUAL-LUNA-DEPLOYMENT" answer --api account-responses --prompt v2 --retrieval local --question "2026년 9월 국내 출장 숙박비 한도와 예약 전 절차는?" --output outputs/learner-notes-ko/02-luna-account.json
```

**확인:** 두 파일의 답변·인용·오류·사용량을 비교합니다. 150,000원 한도와 한도 초과 시 예약 전 승인 절차가 근거와 맞는지 봅니다.

`--model-deployment`는 이 요청에만 적용됩니다. 기본 모델 설정은 바꾸지 않습니다. 한 질문으로 우열을 확정하지 말고, 전체 dev 비교는 07장에서 진행합니다.

지원되지 않으면 **모델 비교 미실행**으로 남깁니다. 같은 모델에 이름만 달리 붙여 비교하지 않습니다.

<a id="4-router를-직접-살펴보기"></a>

## 4. 선택적으로 Router 살펴보기

Model Router는 요청에 따라 모델을 선택합니다.

1. 카탈로그에서 **Model Router**의 지원 리전·API·모드·가격을 확인합니다.
2. 실행하기로 했다면 실습 전용 배포를 만듭니다.
3. **그 배포가 지원하는 Playground**에서 3절과 같은 질문을 보냅니다.
4. Router 버전과 선택된 모델을 확인합니다. 모델이 표시되지 않으면 **선택 모델 미확인**으로 남깁니다.

Router가 프로젝트 Responses API를 지원한다고 가정하지 않습니다. 모델 오류를 Router로 바꿔 성공 처리하지도 않습니다. [공식 Router 평가](https://learn.microsoft.com/azure/foundry/openai/how-to/evaluate-model-router).

## 완료 확인

- [ ] 같은 모델에서 지침만 바꾼 두 답변을 비교했다.
- [ ] 문서를 주지 않은 회사 규정 답변을 정답으로 인정하지 않았다.
- [ ] Luna·Router는 실제 결과 또는 선택적 미실행으로 구분했다.

기본 Sol 배포는 다음 장에서 사용하므로 삭제하지 않습니다.

---

[← 01. 첫 응답](01-foundry.md) · [전체 과정](../README.ko.md#진행-순서) · [03. 에이전트·파일 →](03-knowledge.md) · [진행 지도 ↑](#chapter-map)
