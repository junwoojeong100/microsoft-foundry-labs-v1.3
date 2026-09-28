# 06. Search·Foundry IQ·Hybrid

[English](en/06-search-iq.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 같은 규정을 키워드·IQ·Hybrid로 검색하고 실제 반환 문서를 확인합니다.

**시작 조건:** 00장의 Owner·Foundry 설정과 Sol 호출 성공.

**실행 위치:** 포털에서 서비스·모델 준비 → 터미널에서 설정·검색 → 편집기에서 결과 확인.

> [!WARNING]
> **Search Basic은 요청하지 않아도 서비스 비용이 발생합니다.** Hybrid 실험 후에는 성공 여부와 관계없이 원래 인덱스 설정으로 복귀합니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. Search 생성](#1-search-서비스-직접-생성) | 서비스 이름·리전·요금제 |
| [2. 인증·관리 ID](#2-토큰-인증과-관리-id) | 토큰 인증과 사용자 역할 |
| [3. 기능 요금제](#3-기능별-과금-설정) | 서비스 비용과 기능 비용 구분 |
| [4. 키워드 검색](#4-같은-질문-로컬과-search) | 원래 인덱스 이름과 원문 |
| [5. Foundry IQ](#5-ga-foundry-iq) | 문서·참조·실행 기록 |
| [6. Hybrid](#6-embedding과-hybrid-직접-준비) | 벡터 검색 후 원래 설정 복귀 |
| [7. IQ Chat](#7-모델-기반-iq-chat) | 모델의 질의 계획·답변 합성 |
| [완료 확인](#완료-확인) | 경로별 결과와 남는 비용 |

## 1. Search 서비스 직접 생성

1. Azure 포털에서 **Create a resource → Azure AI Search**를 선택합니다.
2. 실습 구독·전용 그룹·고유 서비스 이름을 지정합니다.
3. **North Central US**, **Basic**, Compute type **Default**, **replica 1개 / partition 1개**를 선택합니다.
4. [리전 표](https://learn.microsoft.com/azure/search/search-region-support)에서 Semantic ranker·Agentic retrieval 지원과 현재 가격을 확인한 뒤 생성합니다.
5. 생성 완료 후 **Overview → URL**, **JSON View → id**를 확인합니다.

**확인:** 실제 서비스의 리전·요금제·복제본(replica)·파티션(partition)이 위 선택과 맞아야 합니다. 리소스 그룹의 위치가 서비스 리전을 자동 결정하지는 않습니다.

**막히면:** `ResourcesForSkuUnavailable`은 용량, `ServiceQuotaExceeded`는 할당량을 확인합니다. 생성 반복·요금제 자동 상향·다른 자원 삭제로 우회하지 않습니다. [Search 문제 해결](troubleshooting.md#retrieval).

## 2. 토큰 인증과 관리 ID

1. Search의 **Settings → Keys → API access control**을 **Role-based access control**로 설정합니다. API key 인증은 사용하지 않습니다.
2. **Identity → System assigned → On → Save**로 Search의 관리 ID를 켭니다.
3. 1절에서 확인한 ID와 URL을 등록합니다.

```bash
python scripts/selfstudy.py resource --kind search --id "실제-Search-ARM-ID" --endpoint "실제-Search-URL"
```

**필요 역할 조회**

```bash
python scripts/selfstudy.py roles --user-object-id "내-사용자-Object-ID"
```

`내-사용자-Object-ID`는 [00장 9절](00-setup.md#9-역할의-실제-명령이-필요할-때)에서 조회합니다. 위 명령은 역할을 부여하지 않습니다.

**확인:** Search의 IAM에서 **내 사용자 → Search Index Data Contributor**가 있는지 봅니다. 없으면 **이 Search 범위에만** 부여합니다. 역할 계획의 모든 줄을 실행하지 않습니다.

프로젝트 관리 ID의 역할은 10장, Search 관리 ID의 모델 접근 역할은 7절에서 준비합니다.

## 3. 기능별 과금 설정

Search의 **Settings → Premium features**에서 다음을 각각 확인합니다.

| 기능 | 용도 |
|---|---|
| Semantic ranker | 검색 결과의 관련도 순서 조정 |
| Knowledge retrieval | IQ 검색 |

제공되는 Free 기능 요금제로 시작할 수 있습니다. **기능이 Free여도 Basic 서비스는 유료**입니다. 제공량을 소진하면 멈추고 추가 비용을 결정합니다.

## 4. 같은 질문, 로컬과 Search

**로컬 검색 — Azure를 호출하지 않음**

```bash
python scripts/workshop.py retrieve --provider local --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-local.json
```

**Search 인덱스와 문서 생성**

인덱스는 문서를 검색할 수 있게 저장한 구조입니다. 다음 명령은 새 서비스가 아니라 **내 접두사의 인덱스와 문서 6개**를 만듭니다.

```bash
python scripts/workshop.py seed-search --confirm-create
```

**Search에서 조회**

```bash
python scripts/workshop.py retrieve --provider search --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-search.json
```

**확인:** `06-search.json`에서 `provider: azure-ai-search-keyword`, 반환 문서 ID·내용을 확인합니다. 현행 숙박 한도와 사전 승인 근거가 있는지 원문과 대조합니다.

**`configuration.index`가 원래 인덱스 이름입니다.** 6절에서 이 값으로 복귀합니다. `outputs/azure-objects.json`의 소유 기록도 보관합니다.

## 5. GA Foundry IQ

이 실습은 정식 출시(GA) IQ 검색을 사용합니다. 작은 문서 모음에서 범위 밖 질문의 근거까지 확인하도록 **검색 관련도 문턱을 0**으로 지정합니다. 평가 통과 점수를 낮추는 설정은 아닙니다.

```bash
python scripts/selfstudy.py set WORKSHOP_IQ_RERANKER_THRESHOLD 0
```

**IQ 검색 자산 생성**

```bash
python scripts/workshop.py seed-search --iq --confirm-create
```

**IQ에서 조회**

```bash
python scripts/workshop.py retrieve --provider iq --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-iq.json
```

**확인:** `provider: foundry-iq`, `api_version: 2026-04-01`, 실제 `documents`, `references`, `activity`를 확인합니다.

**검색 근거로 답변 생성**

```bash
python scripts/workshop.py answer --prompt v2 --retrieval iq --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-iq-answer.json
```

**확인:** 답변의 150,000원 한도·사전 승인·인용이 실제 반환 문서와 맞아야 합니다. 이 명령은 앞 파일을 읽지 않고 **검색과 모델 호출을 새로 수행**합니다.

## 6. Embedding과 Hybrid 직접 준비

Embedding은 문장을 숫자 벡터로 바꿉니다. Hybrid 검색은 키워드와 벡터 검색을 함께 사용합니다.

### 모델·차원 등록

1. 같은 Foundry 계정에 **text-embedding-3-large**를 `workshop-embedding`으로 배포합니다.
2. `Succeeded`와 기본 차원 **3072**를 확인합니다.
3. 같은 계정의 **Azure OpenAI 서비스 루트 주소**를 복사합니다. 프로젝트 주소와 다르며 `/openai/v1`은 제외합니다.

**배포 등록**

```bash
python scripts/selfstudy.py model --role embedding
```

**벡터 차원 설정**

```bash
python scripts/selfstudy.py set WORKSHOP_EMBEDDING_DIMENSIONS 3072
```

**계정 API 선택**

```bash
python scripts/selfstudy.py set WORKSHOP_EMBEDDING_API account
```

**OpenAI 주소 등록**

```bash
python scripts/selfstudy.py set AZURE_OPENAI_ENDPOINT "실제-같은-계정의-OpenAI-루트-URL"
```

### 별도 index에서 검색

원래 인덱스는 유지합니다. `lab-yourname-nc-0928`을 내 접두사로 바꿔 **새 이름**을 지정합니다.

```bash
python scripts/selfstudy.py set AZURE_SEARCH_INDEX_NAME "lab-yourname-nc-0928-policies-hybrid"
```

**벡터 생성과 업로드 — 추가 모델 비용 발생**

```bash
python scripts/workshop.py seed-search --hybrid --confirm-create --confirm-cost
```

**Hybrid 조회**

```bash
python scripts/workshop.py retrieve --provider hybrid --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-hybrid.json
```

**Hybrid 근거로 답변 생성**

```bash
python scripts/workshop.py answer --prompt v2 --retrieval hybrid --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-hybrid-answer.json
```

**확인:** 실제 embedding 호출·차원, 키워드+벡터 검색, 반환 문서·답변을 대조합니다. 차원 오류를 0 벡터나 벡터 잘라내기로 해결하지 않습니다.

### 반드시 원래 index로 복귀

**성공·실패·중단 모두 이 단계를 수행합니다.** 4절의 `06-search.json`에서 `configuration.index` 값을 복사합니다. Hybrid 결과 파일의 값이 아닙니다.

```bash
python scripts/selfstudy.py set AZURE_SEARCH_INDEX_NAME "06-search.json의-configuration.index-값"
```

**복귀 확인**

```bash
python scripts/selfstudy.py status
```

`sdk_settings.AZURE_SEARCH_INDEX_NAME`이 원래 이름이어야 합니다. 설정 복귀는 Hybrid 인덱스 삭제가 아닙니다.

## 7. 모델 기반 IQ Chat

이 절은 Search가 모델로 질의를 계획하고 답변을 합성하는 별도 실험입니다.

1. 같은 Foundry 계정에 `gpt-5.6-luna` / `2026-07-09`를 배포 이름 `gpt-5.6-luna`로 만듭니다.
2. Foundry 계정의 IAM에서 **Search 관리 ID → Cognitive Services User**를 확인·부여합니다.
3. 앞의 OpenAI 루트 주소와 Search 기능 요금제를 확인합니다.

기본 답변 모델은 계속 Sol입니다. 이 모델은 선택 비교용 **GPT-6 Luna와도 다릅니다**.

**IQ 모델 등록**

```bash
python scripts/selfstudy.py model --role iq
```

**선행 조건 검사**

```bash
python scripts/workshop.py iq-chat check
```

검사가 실패하면 생성하지 않습니다. 모델·버전·Search 관리 ID와 역할을 확인합니다.

**자산 생성**

```bash
python scripts/workshop.py iq-chat setup --confirm-create
```

**실제 질문**

```bash
python scripts/workshop.py iq-chat ask --label iq-chat-first --confirm-cost
```

**확인:** `model_planning_verified`, `model_synthesis_verified`와 실제 `modelQueryPlanning`, `modelAnswerSynthesis` 기록을 함께 확인합니다. 모델 기록은 `gpt-5.6-luna`여야 합니다.

미지원이면 IQ Chat만 차단으로 남깁니다. 5절의 IQ 조회를 IQ Chat 성공으로 대신하지 않습니다.

<a id="완료와-유지"></a>

## 완료 확인

- [ ] 키워드·IQ·Hybrid·IQ Chat의 실제 결과 또는 차단 상태를 각각 확인했다.
- [ ] `AZURE_SEARCH_INDEX_NAME`이 4절의 원래 값으로 돌아왔다.
- [ ] 생성 자산의 소유 기록과 Search의 지속 비용을 확인했다.

이 Search는 10장과 이후 평가에 사용합니다. 계속 진행한다면 아직 삭제하지 않습니다.

---

[← 05. 워크플로](05-workflows.md) · [전체 과정](../README.ko.md#진행-순서) · [07. 평가 →](07-evaluation.md) · [진행 지도 ↑](#chapter-map)
