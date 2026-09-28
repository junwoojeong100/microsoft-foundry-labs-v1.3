# 사용할 모델과 실제 배포 이름

**처음에는 GPT-6 Sol 하나만 배포합니다.** 나머지는 필요한 장에서 추가합니다. 기본 리전은 North Central US입니다.

모델 이름은 제품, 배포 이름은 **내 코드가 호출하는 별칭**입니다. 같은 별칭이어도 다른 환경에서는 기반 모델이 다를 수 있습니다.

## 필요한 시점에만 배포

| 역할 | 기반 모델 / 버전 | 새 환경의 배포 이름 | 준비 시점 |
|---|---|---|---|
| 기본 답변·에이전트·도구 | **gpt-6-sol / 2026-09-22** | `workshop-chat` | 00 |
| 선택 비교 | gpt-6-luna / 2026-09-22 | `workshop-compare` | 02, 선택한 경우만 |
| 벡터 생성(embedding) | text-embedding-3-large | `workshop-embedding` | 06 |
| IQ의 질의 계획·답변 합성 | **gpt-5.6-luna / 2026-07-09** | `gpt-5.6-luna` | 06 |
| 답변 평가(judge) | **gpt-5.5 / 2026-04-24** | `workshop-judge` | 07 |
| 지침 후보 생성 | gpt-5.5 / 2026-04-24 | `workshop-optimizer` | 12 |

**혼동하기 쉬운 세 가지**

- Luna 비교는 이후 기본 실습의 필수 조건이 아닙니다.
- IQ용 **GPT-5.6 Luna**와 비교용 **GPT-6 Luna**는 다릅니다.
- judge는 답변 대상과 **기반 모델·배포를 모두 분리**합니다. 이름만 다른 같은 모델로 대신하지 않습니다.

포털에서 실제 모델·버전·지원 기능·할당량·`Succeeded`를 확인합니다. 한 API의 성공이 다른 도구·API의 지원을 보장하지는 않습니다.

## 기존 배포를 그대로 재사용하기

이미 사용 중인 배포를 이 가이드의 이름에 맞추려고 변경·삭제하지 않습니다.

1. **같은 프로젝트에 실제 배포가 남아 있는지** 포털에서 확인합니다.
2. 기반 모델·버전을 위 표와 대조합니다.
3. 기존 프로젝트·엔드포인트·접두사를 유지하고 실제 배포 이름을 지정합니다.

**기존 Sol 설정**

```bash
python scripts/selfstudy.py configure --project-id "실제-프로젝트-ARM-ID" --endpoint "실제-프로젝트-Endpoint" --deployment "기존-Sol-배포-이름" --expected-model gpt-6-sol --prefix "기존-lab-접두사"
```

**기존 GPT-5.5를 judge로 등록**

```bash
python scripts/selfstudy.py model --role judge --deployment "기존-GPT-5.5-배포-이름"
```

**Luna 비교를 선택했을 때만**

```bash
python scripts/selfstudy.py model --role comparison --deployment "기존-Luna-배포-이름"
```

등록 명령은 실제 배포를 읽고 설정을 저장합니다. 새 배포를 만들지 않습니다. 삭제된 다른 프로젝트의 이름·주소는 재사용 근거가 아닙니다.

모델·judge·코드가 달라지면 **새 전후 비교 쌍**을 만듭니다. 이전 에이전트·label·결과를 새 조건의 결과로 바꾸지 않습니다.

## 생성 설정

| 항목 | 기본값 |
|---|---|
| Reasoning effort | `low` |
| 출력 토큰 상한 | `32768` |
| 기본 답변 API | `project-responses` |
| 선택적 모델 비교 API | 두 모델 모두 `account-responses` |

출력 상한에는 reasoning과 최종 답변 토큰이 모두 포함됩니다. **상한은 실제 사용량이나 총비용 한도가 아닙니다.** 비교 중에는 같은 설정을 유지합니다.

기존 설정을 확인·변경해야 한다면:

```bash
python scripts/selfstudy.py set WORKSHOP_REASONING_EFFORT low
```

**출력 상한 설정**

```bash
python scripts/selfstudy.py set WORKSHOP_MAX_OUTPUT_TOKENS 32768
```

변경 후에는 새 에이전트·실험 label을 사용합니다. Prompt Agent의 reasoning은 생성 시 지침 정의에 저장하며 `agent_reference` 요청에 중복 전달하지 않습니다.

12장의 `account-chat`은 별도 경로이며 `reasoning_effort`, `max_completion_tokens`로 설정을 전달합니다. 이 값은 judge·IQ·Optimizer의 모든 내부 호출 비용을 제한하지 않습니다.

## IQ와 Optimizer 모델은 별도 역할

Search·Optimizer의 지원 모델은 답변 모델과 별도로 확인합니다. Sol을 기본 답변으로 쓴다고 다른 역할도 Sol로 바꾸지 않습니다.

## 비용을 비교할 때

실제 배포 유형·계약·리전·입력 길이·캐시 여부에 맞는 가격을 확인합니다. 모델 토큰 외에 Search·Hosted·파일·평가·로그 비용도 합산합니다.

저렴한 모델인지와 내 업무에서 충분히 정확한지는 별개입니다. 같은 조건의 실제 답변·오류·사용량으로 비교합니다.

**공식 자료:** [GPT-6 모델·가격](https://azure.microsoft.com/en-us/blog/gpt-6-astra-sol-and-luna-for-production-agents-in-microsoft-foundry/) · [Sol](https://ai.azure.com/catalog/models/gpt-6-sol) · [Luna](https://ai.azure.com/catalog/models/gpt-6-luna) · [Reasoning](https://learn.microsoft.com/azure/foundry/openai/how-to/reasoning) · [Search 계획 모델](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base) · [Optimizer 모델](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview)
