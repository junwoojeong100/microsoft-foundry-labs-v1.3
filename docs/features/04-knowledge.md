# F04. Search, Foundry IQ와 Toolbox

**목표:** 검색, 지식 기반 응답, 도구 공유를 같은 이름으로 뭉뚱그리지 않고 직접 구분합니다.

준비: [기능 환경](README.md), 담당자가 준비한 Azure AI Search 서비스·Endpoint·필요한 관리/데이터 권한, 고유 Prefix, 생성·검색 비용 승인. 시간: 45~75분. 서비스 자체 생성은 수업 전 준비입니다.

## 1. 먼저 로컬 검색을 기준으로

```bash
python scripts/v12.py retrieve --provider local --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/f04-local.json
```

동봉한 6개 정책의 학습용 키워드 검색입니다. Foundry File Search나 의미 검색이라고 부르지 않습니다.

## 2. 내 Search 객체 생성·조회

호환 `.env`에 `AZURE_SEARCH_ENDPOINT`를 추가합니다. 본인 이름의 객체 생성이 승인된 다음 실행합니다.

```bash
python scripts/v12.py seed-search --confirm-create
python scripts/v12.py retrieve --provider search --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/f04-search.json
```

`provider: azure-ai-search-keyword`, 실제 Endpoint·index·문서 ID를 확인합니다. 소유권 기록 `outputs/azure-objects.json`은 지우거나 수정하지 않습니다.

## 3. 같은 지식을 Foundry IQ로

```bash
python scripts/v12.py seed-search --iq --confirm-create
python scripts/v12.py retrieve --provider iq --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/f04-iq.json
python scripts/v12.py answer --prompt v2 --retrieval iq --question "2026년 9월 국내 출장 숙박 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/f04-answer.json
```

GA 경로의 `provider: foundry-iq`, API 버전, `references`, `activity`, 실제 원문을 확인합니다. `answer`는 저장한 retrieve 파일을 읽는 것이 아니라 **새로 검색하고 모델을 호출**합니다.

**GA 검색과 모델 기반 계획·합성은 같은 실험이 아닙니다.** 원본의 IQ Chat preset은 별도 지원 모델·Search managed identity·knowledge base 설정을 요구합니다. `iq-chat check`로 선행 조건을 확인한 뒤 [별도 IQ Chat 절차](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/06-knowledge.md)를 따릅니다. 준비되지 않았을 때 다른 provider로 자동 대체하지 않습니다.

Hybrid도 유지합니다. 실제 embedding 배포와 차원, 별도 소유 index를 준비하고 [하이브리드 절차](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/06-knowledge.md)를 따릅니다. 문자열 검색의 이름을 hybrid로 바꾸거나 0 벡터를 넣지 않습니다.

## 4. Toolbox로 도구 공유

담당자가 **같은 Search에 대한 keyless 프로젝트 연결**을 준비한 뒤 `.env`의 `TOOLBOX_SEARCH_CONNECTION_NAME`을 설정합니다.

```bash
python scripts/v12.py toolbox plan
python scripts/v12.py toolbox create --confirm-create
```

반환된 **실제 버전**으로 다음을 실행합니다. 아래 `실제-버전`을 바꿉니다.

```bash
python scripts/v12.py toolbox probe --version "실제-버전" --label f04-tool-list
python scripts/v12.py toolbox query --version "실제-버전" --label f04-tool-query --confirm-cost
python scripts/v12.py toolbox ask --version "실제-버전" --label f04-tool-answer --confirm-cost
```

목록 탐색, 직접 검색, 모델을 통한 답변은 세 가지 별도 성공 기준입니다. MCP 연결 성공만으로 Search의 데이터 권한까지 검증되지는 않습니다.

## 5. 유지하는 다음 기능

| 기능 | 이어갈 실제 절차 |
|---|---|
| Toolbox 버전 변경·선택·되돌리기·정리 | [Toolbox lifecycle](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/toolbox.md) |
| 같은 Toolbox의 Hosted 실행 | [Hosted Toolbox](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/toolbox-hosted.md) |
| Tool Search, Skills, 사설 catalog 경계 | [도구 탐색과 Skills](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/tool-search-skills.md) |
| GA IQ / 모델 기반 IQ / Hybrid / workflow 연결 | [지식 Lab](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/06-knowledge.md) |

**완료:** provider별 실제 검색·참조·답변과 Toolbox의 목록/실행 차이를 설명합니다. **정리:** 원본 소유권 ledger에 기록된 본인 객체만 정리합니다. 기본 과정의 `lab.py cleanup`은 이 Search·Toolbox 자산을 삭제하지 않습니다.

[기본 Lab 03](../03-knowledge.md) · [기능 목록](README.md)
