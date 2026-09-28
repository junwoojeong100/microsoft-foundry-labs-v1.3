# 사용할 모델과 실제 배포 이름

**기본 답변 모델은 `gpt-6-sol` / `2026-09-22`입니다.** 첫 응답부터 Prompt Agent·도구·Hosted 실습까지 Sol로 직접 시작합니다. GPT-6 Luna는 같은 조건의 모델 비교를 원할 때만 추가합니다.

## 필요한 시점에만 배포

아래 이름은 **새 환경의 기본 별칭**입니다. 이름만 보고 기반 모델을 판단하지 않습니다.

| 역할 | 실제 모델 / 버전 | 새 환경의 배포 이름 | 준비 시점 |
|---|---|---|---|
| 기본 답변·에이전트·도구 | **gpt-6-sol / 2026-09-22** | `workshop-chat` | 00 |
| 선택적 비교 | **gpt-6-luna / 2026-09-22** | `workshop-compare` | 02, 비교를 선택한 경우만 |
| judge | **gpt-5.5 / 2026-04-24** | `workshop-judge` | 07 |
| Embedding | text-embedding-3-large | `workshop-embedding` | 06 |
| IQ의 모델 기반 계획/합성 | **gpt-5.6-luna / 2026-07-09** | `gpt-5.6-luna` | 06의 해당 실험 |
| 개선 후보 생성 | gpt-5.5 / 2026-04-24 | `workshop-optimizer` | 12 |

**Luna 비교는 기본 경로의 선행 조건이 아닙니다.** 모델 비교를 할 때는 Sol과 GPT-6 Luna 모두 같은 명시적 `account-responses` API를 사용합니다. 하나만 프로젝트 API로 실행한 결과와 섞지 않습니다.

Judge는 GPT-6 대상과 **기반 모델이 다른 GPT-5.5**이며, 모든 대상과 **배포도 달라야** 합니다. 다른 배포 이름만 붙인 같은 대상 모델로 대신하지 않고, 분리 검사를 낮추지 않습니다. 기반 모델을 분리해도 평가 편향이 모두 사라지는 것은 아니므로 실제 근거·행별 설명·업무 검사와 calibration을 함께 검토합니다.

## 기존 배포를 그대로 재사용하기

**별칭은 모델의 정체성이 아닙니다.** 이 실습의 기존 환경에는 Sol이 `workshop-compare`, GPT-5.5가 `workshop-optimizer`라는 이름으로 이미 있습니다. 새 기본 이름에 맞추려고 기존 모델을 바꾸거나 자원을 삭제하지 않습니다.

같은 프로젝트·Endpoint·prefix를 유지하고 실제 Sol 별칭을 명시합니다.

```bash
python scripts/selfstudy.py configure --project-id "실제-프로젝트-ARM-ID" --endpoint "실제-프로젝트-Endpoint" --deployment workshop-compare --expected-model gpt-6-sol --prefix "기존-lab-접두사"
python scripts/selfstudy.py model --role judge --deployment workshop-optimizer
```

두 번째 명령은 기존 GPT-5.5의 모델/버전을 읽어 judge로 설정합니다. 새 배포를 만드는 명령이 아닙니다. Judge를 대상 model map에 넣지 않습니다.

기존 `workshop-chat`이 실제로 **GPT-6 Luna / 2026-09-22**이고 비교를 선택한 경우에만:

```bash
python scripts/selfstudy.py model --role comparison --deployment workshop-chat
```

새 환경은 표의 별칭을 사용하고, 기존 환경은 확인한 실제 별칭을 사용합니다. 원시 결과·평가·소유권 기록과 기존 label은 수정하거나 재사용하지 않습니다. 모델·judge·코드 조건이 달라지면 새 비교 쌍을 수집합니다.

## 생성 설정

```text
Reasoning effort: low
출력 토큰 상한: 32768
기본 답변 API: project-responses
선택적 모델 비교 API: account-responses
```

출력 상한에는 reasoning 토큰과 최종 답변 토큰이 모두 포함됩니다. 상한은 실제 사용량이나 선결제가 아닙니다. 비교 중에는 같은 reasoning·출력 한도를 유지합니다.

Prompt Agent의 reasoning은 저장된 **definition**에만 넣습니다. `agent_reference` 요청에서 다시 덮어쓰지 않습니다. Hosted matrix의 `account-chat`은 별도 API이며 같은 의미를 `reasoning_effort`와 `max_completion_tokens`로 전달합니다.

이 한도는 실습 코드의 답변 생성 요청에 적용합니다. 관리형 judge·IQ 계획/합성·Optimizer의 내부 호출 비용까지 하나로 묶는 총예산은 아닙니다.

## IQ와 Optimizer 모델은 별도 역할

IQ의 **`gpt-5.6-luna`**는 선택적 비교 모델 **`gpt-6-luna`**와 다릅니다. Search가 계획/합성에 사용하는 모델을 답변 모델 기본값 변경에 맞춰 바꾸지 않습니다. Search와 Optimizer는 각각의 지원 목록과 실제 배포를 확인합니다.

## 비용을 비교할 때

2026-09-27에 확인한 출시 자료의 **Global Standard·short-context·100만 토큰 기준** 참고 가격입니다. 현재 계약·리전·캐시·배포 유형·long-context 가격을 대신하지 않습니다.

| 모델 | 입력 | 출력 |
|---|---:|---:|
| GPT-6 Sol | USD 2.00 | USD 10.00 |
| 선택적 GPT-6 Luna | USD 0.10 | USD 0.50 |

GPT-5.5 judge/Optimizer, Search, Hosted, 평가와 로그는 별도 비용입니다. 더 저렴한 모델이라는 제품 특성과 이 실습에서 필요한 품질은 따로 판단합니다.

**공식 근거:** [GPT-6 모델·가격](https://azure.microsoft.com/en-us/blog/gpt-6-astra-sol-and-luna-for-production-agents-in-microsoft-foundry/) · [Sol 모델 카드](https://ai.azure.com/catalog/models/gpt-6-sol) · [Luna 모델 카드](https://ai.azure.com/catalog/models/gpt-6-luna) · [Reasoning](https://learn.microsoft.com/azure/foundry/openai/how-to/reasoning) · [Search 계획 모델](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base) · [Optimizer 모델](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview)
