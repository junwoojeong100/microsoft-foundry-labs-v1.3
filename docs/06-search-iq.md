# 06. Search·Foundry IQ·Hybrid

[English](en/06-search-iq.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 본인이 Search를 생성·설정하고 같은 문서를 키워드, IQ, Hybrid로 검색합니다.

**시작 조건:** 00의 Owner·Foundry 설정. 이 장에서 Search와 필요 모델을 직접 만듭니다. **Search Basic은 요청하지 않아도 서비스 비용이 발생**합니다.

**실행 위치:** Azure·Foundry 포털에서 서비스·모델 준비, 터미널에서 설정·검색.

> **설정 복귀:** Hybrid 실험이 성공하거나 실패해도 **6절 마지막에 원래 index로 돌아옵니다.** 뒤의 실습은 원래 index를 사용합니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. Search 생성](#1-search-서비스-직접-생성) | 실제 서비스·리전·Basic 비용 |
| [2. 인증·관리 ID](#2-토큰-인증과-관리-id) | 토큰 인증과 사용자 데이터 역할 |
| [3. 기능 과금](#3-기능별-과금-설정) | 서비스 비용과 기능 플랜 구분 |
| [4. 로컬·키워드 검색](#4-같은-질문-로컬과-search) | 원래 index 이름과 반환 원문 |
| [5. GA IQ](#5-ga-foundry-iq) | 실제 documents·references·activity |
| [6. Hybrid](#6-embedding과-hybrid-직접-준비) | 실제 embedding·검색, 원래 index 복귀 |
| [7. IQ Chat](#7-모델-기반-iq-chat) | 별도 모델의 질의 계획·답변 합성 |
| [완료 확인](#완료-확인) | 네 검색 경로의 결과와 소유권 보관 |

## 1. Search 서비스 직접 생성

1. Azure 포털 **Create a resource → Azure AI Search**.
2. 실습 구독과 **실습 전용 그룹**, 고유한 서비스 이름을 선택합니다.
3. 서비스 리전을 **North Central US**로 선택하고, [리전 표](https://learn.microsoft.com/azure/search/search-region-support)에서 **Semantic ranker와 Agentic retrieval**을 모두 확인합니다. 리소스 그룹의 위치만 같다고 서비스 리전도 자동으로 같아지는 것은 아닙니다.
4. **Basic**, Compute type **Default**, **replica 1개 / partition 1개**로 시작합니다. 상위 SKU나 Confidential compute가 이 실습의 기본은 아닙니다.
5. 가격을 확인한 뒤 생성하고 완료 상태를 기다립니다.
6. Overview의 **URL**, JSON View의 **전체 리소스 ID**, 실제 SKU·replica·partition과 지속 비용을 기록합니다.

<details>
<summary>생성이 막힐 때만: 리전 용량과 구독 quota</summary>

`ResourcesForSkuUnavailable`은 용량, `ServiceQuotaExceeded`는 구독 quota를 먼저 확인합니다. 현재 가용성과 실패 원문을 기록하고 조건이 바뀐 뒤에만 제한적으로 재시도합니다. Owner/RBAC 추가·같은 Create 반복으로 해결하지 않으며 다른 그룹 삭제나 자동 SKU 상향으로 우회하지 않습니다.

Search가 준비되지 않았다면 Search 의존 단계를 차단으로 남깁니다. File Search와 로컬 검색은 별도 기능입니다. [독립적으로 진행 가능한 단계](checkpoints.md#막힌-단계가-있을-때)와 [지역별 과거 검증](validation-report.md)을 구분합니다.

</details>

## 2. 토큰 인증과 관리 ID

Search의 **Settings → Keys → API access control**을 **Role-based access control**로 설정하고 key 인증을 비활성화합니다. 본인 실습 서비스에만 적용하며 API key를 복사하지 않습니다.

**Identity → System assigned → On → Save**를 수행합니다. 이 ID는 뒤에서 Search가 IQ Chat 모델을 호출할 때 사용합니다.

```bash
python scripts/selfstudy.py resource --kind search --id "실제-Search-ARM-ID" --endpoint "실제-Search-URL"
```

**필요한 역할의 계획 조회**

```bash
python scripts/selfstudy.py roles --user-object-id "내-사용자-Object-ID"
```

등록은 Azure를 읽고 로컬 설정을 기록할 뿐 역할을 부여하지 않습니다. 출력 계획 중 **내 사용자 → 이 Search의 Search Index Data Contributor**를 IAM과 대조해 없으면 추가합니다. 관리 작업은 기존 Owner가 담당합니다.

프로젝트 관리 ID의 Toolbox 역할은 10에서, Search 관리 ID의 모델 역할은 아래 IQ Chat에서 사용합니다. 역할 계획의 모든 줄을 무조건 실행하지 않습니다.

## 3. 기능별 과금 설정

**Settings → Premium features**에서 Semantic ranker와 Knowledge retrieval을 각각 확인합니다. 제공되는 **Free 기능 플랜**으로 시작할 수 있지만 **Basic 서비스가 무료가 되는 것은 아닙니다**.

기본 제공량을 소진하면 멈추고 비용을 검토한 뒤 Standard 기능 플랜을 선택할지 결정합니다. 오류 때문에 자동 업그레이드하거나 검색 provider를 바꾸지 않습니다.

## 4. 같은 질문, 로컬과 Search

```bash
python scripts/workshop.py retrieve --provider local --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-local.json
```

**검색 index와 문서 준비**

```bash
python scripts/workshop.py seed-search --confirm-create
```

**실제 반환 원문 확인**

```bash
python scripts/workshop.py retrieve --provider search --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-search.json
```

`seed-search`는 새 서비스가 아니라 **내 Prefix의 index와 합성 문서**를 생성합니다. 원래 index 이름은 방금 저장한 `outputs/learner-notes-ko/06-search.json`의 `configuration.index`에서 다시 읽을 수 있습니다. `outputs/azure-objects.json`도 보관하며, 6절 후 이 원래 이름으로 복귀합니다.

**확인:** `provider: azure-ai-search-keyword`, 실제 index/Endpoint, 원문 ID와 내용을 확인합니다. 로컬 검색은 의미 검색이나 Azure 서비스 호출이 아닙니다.

## 5. GA Foundry IQ

합성 문서 6개를 사용하는 이 실습에서는 **reranker 검색 문턱을 0으로 명시**합니다. 기본 필터가 낮은 관련도 문서를 제외하면 범위 밖 질문에 필요한 `SCOPE-01`까지 사라질 수 있습니다. 이는 검색 필터이며 평가 통과 기준 4를 낮추는 설정이 아닙니다. 실제 반환 문서와 인용은 여전히 검사합니다.

```bash
python scripts/selfstudy.py set WORKSHOP_IQ_RERANKER_THRESHOLD 0
```

**검색 index와 문서 준비**

```bash
python scripts/workshop.py seed-search --iq --confirm-create
```

**실제 반환 원문 확인**

```bash
python scripts/workshop.py retrieve --provider iq --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-iq.json
```

**검색 근거로 모델에 질문**

```bash
python scripts/workshop.py answer --prompt v2 --retrieval iq --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-iq-answer.json
```

**확인:** `provider: foundry-iq`, knowledge base, `api_version: 2026-04-01`, 실제 documents/references/activity를 봅니다. 마지막 명령은 앞 파일을 읽는 것이 아니라 **새 검색과 모델 호출**입니다.

이 GA 경로를 모델의 질의 계획·답변 합성 실험과 같은 것으로 부르지 않습니다.

## 6. Embedding과 Hybrid 직접 준비

### 모델·차원 등록

1. 같은 Foundry 카탈로그에서 **text-embedding-3-large**를 찾습니다.
2. 지원 리전/할당량을 확인하고 `workshop-embedding`으로 배포합니다.
3. 모델 상세에서 실제 차원을 확인합니다. 이 모델의 기본 차원은 **3072**이며, 다른 모델/설정을 쓰면 실제 값으로 맞춰야 합니다.
4. 같은 Foundry 계정의 **Azure OpenAI 루트 Endpoint**를 포털에서 확인합니다. 프로젝트 Endpoint와 다릅니다.

```bash
python scripts/selfstudy.py model --role embedding
```

**실제 embedding 차원 설정**

```bash
python scripts/selfstudy.py set WORKSHOP_EMBEDDING_DIMENSIONS 3072
```

**embedding API 경로 설정**

```bash
python scripts/selfstudy.py set WORKSHOP_EMBEDDING_API account
```

**OpenAI 루트 Endpoint 등록**

```bash
python scripts/selfstudy.py set AZURE_OPENAI_ENDPOINT "실제-같은-계정의-OpenAI-루트-URL"
```

### 별도 index에서 검색

원래 index는 그대로 두고 **새 hybrid index 이름**을 명시합니다. 예시 접두사는 내 값으로 바꿉니다.

```bash
python scripts/selfstudy.py set AZURE_SEARCH_INDEX_NAME "lab-yourname-nc-0928-policies-hybrid"
```

**검색 index와 문서 준비**

```bash
python scripts/workshop.py seed-search --hybrid --confirm-create --confirm-cost
```

**실제 반환 원문 확인**

```bash
python scripts/workshop.py retrieve --provider hybrid --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-hybrid.json
```

**검색 근거로 모델에 질문**

```bash
python scripts/workshop.py answer --prompt v2 --retrieval hybrid --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-hybrid-answer.json
```

**확인:** 실제 embedding 호출과 차원, text+vector 검색, 반환 근거를 확인합니다. 0 벡터를 넣거나 키워드 검색의 이름만 바꾸지 않습니다.

### 반드시 원래 index로 복귀

**성공 여부와 관계없이, Hybrid 실험을 끝내거나 중단할 때 원래 index로 복귀**합니다. 4절의 `outputs/learner-notes-ko/06-search.json`을 열고 **`configuration` 안의 `index` 값**을 아래 따옴표 안에 넣습니다. 방금 만든 hybrid 결과 파일의 index가 아닙니다.

```bash
python scripts/selfstudy.py set AZURE_SEARCH_INDEX_NAME "06-search.json의-configuration.index-값"
```

이 설정 변경은 hybrid index를 삭제하지 않습니다. 둘 다 소유권 ledger에 남으며 최종 정리 때 확인합니다.

`python scripts/selfstudy.py status`의 `sdk_settings.AZURE_SEARCH_INDEX_NAME`이 원래 이름인지 확인한 뒤 다음으로 갑니다. Hybrid 실패를 해결하지 못했다면 그 결과는 미완료로 보관합니다.

## 7. 모델 기반 IQ Chat

이 실험은 **`gpt-5.6-luna` / `2026-07-09`**, Search system-assigned identity를 사용합니다.

기본 답변 모델은 계속 **GPT-6 Sol**입니다. 여기의 **GPT-5.6 Luna**는 Search가 계획/합성에 사용하는 별도 모델이며, 선택적 비교용 GPT-6 Luna와도 다릅니다. [모델 역할](model-selection.md)을 혼동하지 않습니다.

1. 카탈로그에서 해당 모델/버전의 가용성과 할당량을 확인합니다.
2. 같은 Foundry 계정에 배포 이름 `gpt-5.6-luna`로 만듭니다. 기본 답변 모델은 바꾸지 않습니다.
3. Foundry 계정 IAM에서 **Search 관리 ID → Cognitive Services User**를 부여합니다. 내 사용자나 프로젝트 ID와 혼동하지 않습니다.
4. 앞에서 기록한 OpenAI 루트 Endpoint와 Search 기능 플랜을 확인합니다.

```bash
python scripts/selfstudy.py model --role iq
```

**IQ Chat 선행 조건 확인**

```bash
python scripts/workshop.py iq-chat check
```

**IQ Chat 자산 생성**

```bash
python scripts/workshop.py iq-chat setup --confirm-create
```

**IQ Chat에 실제 질문 · `iq-chat-first`**

```bash
python scripts/workshop.py iq-chat ask --label iq-chat-first --confirm-cost
```

`model_planning_verified`, `model_synthesis_verified`뿐 아니라 실제 **`modelQueryPlanning` / `modelAnswerSynthesis` activity와 `gpt-5.6-luna` 모델 기록**, 반환 원문을 확인합니다. 배포가 불가능하면 이 preset만 **차단**으로 기록합니다. 다른 모델을 같은 이름으로 위장하거나 GA 조회를 IQ Chat 성공으로 대신하지 않습니다.

<a id="완료와-유지"></a>

## 완료 확인

- [ ] keyword·IQ·Hybrid·IQ Chat의 실제 결과 또는 차단 상태를 각각 확인했다.
- [ ] `sdk_settings.AZURE_SEARCH_INDEX_NAME`이 4절의 원래 index 이름이다.
- [ ] 생성한 index·base·모델의 소유권과 계속 발생하는 비용을 확인했다.

원래 index·IQ base와 hybrid index의 결과/소유권을 보관합니다. 이 Search는 10장의 Toolbox/OpenAPI와 이후 Hosted 평가에 사용하므로 아직 삭제하지 않습니다.

---

[← 05. 워크플로](05-workflows.md) · [전체 과정](../README.ko.md#진행-순서) · [07. 평가 →](07-evaluation.md) · [진행 지도 ↑](#chapter-map)
