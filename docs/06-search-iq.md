# 06. Search·Foundry IQ·Hybrid

**완료 목표:** 본인이 Search를 생성·설정하고 같은 문서를 키워드, IQ, Hybrid로 검색합니다.

**시작 조건:** 00의 Owner·Foundry 설정. 이 장에서 Search와 필요 모델을 직접 만듭니다. **Search Basic은 요청하지 않아도 서비스 비용이 발생**합니다.

**현재 재실행 범위:** 새 그룹에서 한국어 keyword·GA IQ·실제 3072차원 embedding/Hybrid·모델 기반 IQ Chat을 확인했습니다. **이전 NC의 별도 한·영 검증**에서는 영어 첫 dev가 `SCOPE-01` 누락으로 5/6이었고, 검색 문턱 0을 명시한 새 label에서 6/6이었습니다. 그 결과를 새 영어 실행으로 옮기지 않으며 검색 변경을 지침만의 개선으로 부르지 않습니다. [새 실행 범위](validation-report.md).

## 1. Search 서비스 직접 생성

1. Azure 포털 **Create a resource → Azure AI Search**.
2. 실습 구독과 **실습 전용 그룹**, 고유한 서비스 이름을 선택합니다.
3. [리전 표](https://learn.microsoft.com/azure/search/search-region-support)에서 **Semantic ranker와 Agentic retrieval**을 모두 확인합니다.
4. **Basic**, Compute type **Default**, **replica 1개 / partition 1개**로 시작합니다. 상위 SKU나 Confidential compute가 이 실습의 기본은 아닙니다.
5. 가격을 확인한 뒤 생성하고 완료 상태를 기다립니다.
6. Overview의 **URL**, JSON View의 **전체 리소스 ID**, 실제 SKU·replica·partition과 지속 비용을 기록합니다.

**역사적 Sweden Central 결과:** 이전 Basic Search는 replica/partition 1개씩, key 인증 비활성화, system-assigned identity, Free semantic plan을 사용했습니다. 6개 문서의 keyword 조회, GA IQ와 Sol 답변, 실제 3072차원 embedding의 Hybrid 조회가 성공했습니다. 이 자산과 결과는 NC 자산이 아닙니다.

**이전 Sweden IQ Chat**의 실제 `gpt-5.6-luna` planning/synthesis와 OpenAPI·Toolbox 결과도 보관한 역사적 증거입니다. 자세한 주체·버전은 [10](10-toolbox-skills.md)에서 구분하며, 이를 새 NC나 관리형 AI red-team 결과로 복사하지 않습니다.

**이전 Sweden의 영문 실행**도 별도 소유권 workspace에서 검증했습니다. English Search·GA IQ·Hybrid·IQ Chat과 Sol dev 6문항의 과거 통과는 NC 영문 실행의 증거가 아닙니다. 각 프로젝트·언어의 소유 이름·hash·label을 분리합니다.

**과거 오류와 새 재시도:** 앞선 Basic/S1의 `ResourcesForSkuUnavailable`과 S2의 `ServiceQuotaExceeded`(`0 out of 0`)는 당시의 용량·구독 quota 오류입니다. 현재의 영구 차단 상태로 해석하지 않습니다. 새 오류가 나면 현재 quota/가용성과 실패 원문을 확인하고 조건이 바뀐 뒤에만 제한적으로 재시도합니다. Owner/RBAC 추가나 같은 Create 반복으로 해결하지 않으며, 고정 리전과 보존 방침을 유지합니다. 다른 그룹을 임의로 삭제하거나 SKU를 자동으로 올리지 않습니다.

Search가 실제로 준비되지 않은 경우에만 해당 의존 단계를 멈춥니다. File Search와 로컬 검색은 별도 기능이며 Search 성공 증거가 아닙니다.

## 2. 토큰 인증과 관리 ID

Search의 **Settings → Keys → API access control**을 **Role-based access control**로 설정하고 key 인증을 비활성화합니다. 본인 실습 서비스에만 적용하며 API key를 복사하지 않습니다.

**Identity → System assigned → On → Save**를 수행합니다. 이 ID는 뒤에서 Search가 IQ Chat 모델을 호출할 때 사용합니다.

```bash
python scripts/selfstudy.py resource --kind search --id "실제-Search-ARM-ID" --endpoint "실제-Search-URL"
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
python scripts/workshop.py seed-search --confirm-create
python scripts/workshop.py retrieve --provider search --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-search.json
```

`seed-search`는 새 서비스가 아니라 **내 Prefix의 index와 합성 문서**를 생성합니다. 실제 index 이름과 `outputs/azure-objects.json`을 보관합니다.

`provider: azure-ai-search-keyword`, 실제 index/Endpoint, 원문 ID와 내용을 확인합니다. 로컬 검색은 의미 검색이나 Azure 서비스 호출이 아닙니다.

## 5. GA Foundry IQ

합성 문서 6개를 사용하는 이 실습에서는 **reranker 검색 문턱을 0으로 명시**합니다. 기본 필터가 낮은 관련도 문서를 제외하면 범위 밖 질문에 필요한 `SCOPE-01`까지 사라질 수 있습니다. 이는 검색 필터이며 평가 통과 기준 4를 낮추는 설정이 아닙니다. 실제 반환 문서와 인용은 여전히 검사합니다.

```bash
python scripts/selfstudy.py set WORKSHOP_IQ_RERANKER_THRESHOLD 0
python scripts/workshop.py seed-search --iq --confirm-create
python scripts/workshop.py retrieve --provider iq --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-iq.json
python scripts/workshop.py answer --prompt v2 --retrieval iq --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-iq-answer.json
```

`provider: foundry-iq`, knowledge base, `api_version: 2026-04-01`, 실제 documents/references/activity를 봅니다. 마지막 명령은 앞 파일을 읽는 것이 아니라 **새 검색과 모델 호출**입니다.

이 GA 경로를 모델의 질의 계획·답변 합성 실험과 같은 것으로 부르지 않습니다.

## 6. Embedding과 Hybrid 직접 준비

1. 같은 Foundry 카탈로그에서 **text-embedding-3-large**를 찾습니다.
2. 지원 리전/할당량을 확인하고 `workshop-embedding`으로 배포합니다.
3. 모델 상세에서 실제 차원을 확인합니다. 이 모델의 기본 차원은 **3072**이며, 다른 모델/설정을 쓰면 실제 값으로 맞춰야 합니다.
4. 같은 Foundry 계정의 **Azure OpenAI 루트 Endpoint**를 포털에서 확인합니다. 프로젝트 Endpoint와 다릅니다.

```bash
python scripts/selfstudy.py model --role embedding
python scripts/selfstudy.py set WORKSHOP_EMBEDDING_DIMENSIONS 3072
python scripts/selfstudy.py set WORKSHOP_EMBEDDING_API account
python scripts/selfstudy.py set AZURE_OPENAI_ENDPOINT "실제-같은-계정의-OpenAI-루트-URL"
```

원래 index는 그대로 두고 **새 hybrid index 이름**을 명시합니다. 예시 접두사는 내 값으로 바꿉니다.

```bash
python scripts/selfstudy.py set AZURE_SEARCH_INDEX_NAME "lab-yourname-nc-0928-policies-hybrid"
python scripts/workshop.py seed-search --hybrid --confirm-create --confirm-cost
python scripts/workshop.py retrieve --provider hybrid --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-hybrid.json
python scripts/workshop.py answer --prompt v2 --retrieval hybrid --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/06-hybrid-answer.json
```

실제 embedding 호출과 차원, text+vector 검색, 반환 근거를 확인합니다. 0 벡터를 넣거나 키워드 검색의 이름만 바꾸지 않습니다.

**다음 단계 전에 원래 index로 복귀**합니다. 4절에서 실제 출력된 index 이름을 사용합니다.

```bash
python scripts/selfstudy.py set AZURE_SEARCH_INDEX_NAME "4절에서-기록한-원래-index"
```

이 설정 변경은 hybrid index를 삭제하지 않습니다. 둘 다 소유권 ledger에 남으며 최종 정리 때 확인합니다.

## 7. 모델 기반 IQ Chat

이 실험은 **`gpt-5.6-luna` / `2026-07-09`**, Search system-assigned identity를 사용합니다.

기본 답변 모델은 계속 **GPT-6 Sol**입니다. 여기의 **GPT-5.6 Luna**는 Search가 계획/합성에 사용하는 별도 모델이며, 선택적 비교용 GPT-6 Luna와도 다릅니다. [모델 역할](model-selection.md)을 혼동하지 않습니다.

1. 카탈로그에서 해당 모델/버전의 가용성과 할당량을 확인합니다.
2. 같은 Foundry 계정에 배포 이름 **`gpt-5.6-luna`**로 만듭니다. 기본 답변 모델은 바꾸지 않습니다.
3. Foundry 계정 IAM에서 **Search 관리 ID → Cognitive Services User**를 부여합니다. 내 사용자나 프로젝트 ID와 혼동하지 않습니다.
4. 앞에서 기록한 OpenAI 루트 Endpoint와 Search 기능 플랜을 확인합니다.

```bash
python scripts/selfstudy.py model --role iq
python scripts/workshop.py iq-chat check
python scripts/workshop.py iq-chat setup --confirm-create
python scripts/workshop.py iq-chat ask --label iq-chat-first --confirm-cost
```

`model_planning_verified`, `model_synthesis_verified`뿐 아니라 실제 **`modelQueryPlanning` / `modelAnswerSynthesis` activity와 `gpt-5.6-luna` 모델 기록**, 반환 원문을 확인합니다. 배포가 불가능하면 이 preset만 **차단**으로 기록합니다. 다른 모델을 같은 이름으로 위장하거나 GA 조회를 IQ Chat 성공으로 대신하지 않습니다.

## 완료와 유지

원래 index·IQ base와 hybrid index의 결과/소유권을 보관합니다. 이 Search는 10장의 Toolbox/OpenAPI와 이후 Hosted 평가에 사용하므로 아직 삭제하지 않습니다.

**다음 → [07. 업무 평가와 Foundry 평가](07-evaluation.md)**
