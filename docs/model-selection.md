# 사용할 모델은 이렇게 정합니다

**기본 답변 모델은 `gpt-6-luna` / `2026-09-22`입니다.** 짧은 규정 질의, 반복 평가, 도구 호출이 많은 이 과정에서는 응답성과 비용 효율을 우선합니다.

Microsoft의 공식 설명에서 Luna는 Sol보다 작고 빠른 고빈도 작업용 모델입니다. Sol은 복잡한 지식 작업·코딩·에이전트 워크플로에 적합하므로 **비교와 평가**에 사용합니다. 이 선택은 제품 특성에 근거한 시작점이며, 본인 환경의 실제 품질은 dev 결과로 판단합니다.

## 필요한 시점에만 배포

| 역할 | 실제 모델 / 버전 | 배포 이름 | 준비 시점 |
|---|---|---|---|
| 기본 답변·에이전트·도구 | **gpt-6-luna / 2026-09-22** | `workshop-chat` | 00 |
| 비교·judge | **gpt-6-sol / 2026-09-22** | `workshop-compare` | 02에서 생성, 07에서 재사용 |
| Embedding | text-embedding-3-large | `workshop-embedding` | 06 |
| IQ의 모델 기반 계획/합성 | gpt-5.6-luna / 2026-07-09 | `gpt-5.6-luna` | 06의 해당 실험 |
| 개선 후보 생성 | gpt-5.5 / 2026-04-24 | `workshop-optimizer` | 12 |

**한꺼번에 다 만들지 않습니다.** 비교용 Sol 배포를 judge로 재사용하므로 동일 모델을 불필요하게 중복 배포하지 않습니다.

모델명과 배포 이름은 다릅니다. 코드에는 `workshop-chat`을 넣지만, 포털의 실제 기반 모델은 `gpt-6-luna`여야 합니다. 설정 도구가 이름뿐 아니라 실제 모델·버전·생성 상태를 확인합니다.

## 생성 설정

```text
Reasoning effort: low
출력 토큰 상한: 32768
주 실행 API: Responses
```

출력 상한에는 **reasoning 토큰과 최종 답변 토큰이 모두 포함**됩니다. 짧게 답하라는 지침만으로 reasoning 비용이 제한되지는 않습니다. 상한은 선결제나 예약량이 아니라 요청이 생성할 수 있는 최대치입니다.

32768은 초기 reasoning 여유를 두기 위한 실습 설정입니다. 무조건 이만큼 사용한다는 뜻은 아닙니다. 실제 사용량을 확인한 후 조정하되, 비교 중에는 같은 값과 reasoning을 유지합니다.

Responses·Prompt Agent·MAF·Hosted에서 같은 설정을 사용합니다. Chat Completions를 쓰는 matrix 경로는 같은 의미를 해당 API의 `reasoning_effort`와 `max_completion_tokens`로 전달합니다.

이 상한은 **실습 코드가 보내는 답변 생성 요청**에 적용합니다. 관리형 judge·IQ 계획/합성·Optimizer·중첩 agent의 내부 호출까지 같은 총예산으로 묶는 것은 아닙니다. 각 서비스의 설정·사용량·추가 비용을 별도로 확인합니다.

## 모든 역할을 GPT-6으로 바꾸지 않는 이유

Foundry 모델 카탈로그는 두 GPT-6 모델의 Agent v2·도구 호출과 File Search·Code Interpreter 등을 명시합니다. **모델의 지원 목록과 개별 지역·배포·포털 UI가 실제로 동작하는지는 별도**이므로 각 장의 첫 요청으로 확인합니다.

Azure AI Search의 knowledge base 계획 모델과 Agent Optimizer의 후보 생성 모델에는 **별도 지원 목록**이 있습니다. 확인일 기준 GPT-6이 해당 목록에 있다고 가정하지 않습니다. GPT-6 에이전트가 Search 도구를 사용하는 것과 Search가 자체 계획 모델로 GPT-6을 호출하는 것은 다릅니다.

## 비용 비교의 기준

공식 출시 자료의 **Global Standard·short-context·100만 토큰 기준** 가격은 다음과 같습니다.

| 모델 | 입력 | 출력 |
|---|---:|---:|
| GPT-6 Luna | USD 0.10 | USD 0.50 |
| GPT-6 Sol | USD 2.00 | USD 10.00 |

이 표는 **2026-09-27에 확인한 출시 자료**이며 현재 계약·지역·배포 유형·캐시·long-context 가격을 대신하지 않습니다. 전체 실습 비용이 정확히 같은 비율로 줄어든다는 뜻도 아닙니다. Search·평가·Hosted·로그는 별도 과금입니다.

**공식 근거:** [모델 출시·용도·가격](https://azure.microsoft.com/en-us/blog/gpt-6-astra-sol-and-luna-for-production-agents-in-microsoft-foundry/) · [Luna 모델 카드](https://ai.azure.com/catalog/models/gpt-6-luna) · [Sol 모델 카드](https://ai.azure.com/catalog/models/gpt-6-sol) · [Reasoning 설정](https://learn.microsoft.com/azure/foundry/openai/how-to/reasoning) · [Search 계획 모델](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base) · [Optimizer 모델](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview)
