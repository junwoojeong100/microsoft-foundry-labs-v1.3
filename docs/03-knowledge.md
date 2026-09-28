# 03. Prompt Agent와 File Search

[English](en/03-knowledge.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 지침과 버전을 저장한 에이전트를 만들고, 별도로 실제 파일 검색과 인용을 확인합니다.

**시작 조건:** 00~02의 설정과 응답 모델. 사용할 데이터는 아래 **한빛기술 6문서만**입니다.

**이번 장에서는 에이전트 두 개를 만듭니다.** 먼저 문서를 지침에 넣은 agent, 다음으로 파일을 실제 검색하는 agent입니다. 이름과 버전은 도구가 구분하므로 기본 명령을 그대로 따라가면 됩니다.

**실행 위치:** 편집기에서 원문 읽기 → 터미널에서 생성·호출 → Foundry에서 버전 확인.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. 원문 읽기](#1-원문부터-읽기) | 날짜별 한도와 근거가 없는 범위 |
| [2. 인라인 Prompt Agent](#2-저장되는-prompt-agent) | 저장된 버전과 실제 답변 |
| [3. File Search 생성](#3-실제-file-search-에이전트-만들기) | 파일 6개 인덱싱과 소유 ID |
| [4. 세 질문으로 검색 확인](#4-세-질문으로-구분) | 실제 검색 호출과 내 파일 인용 |
| [5. 결과 보관](#5-저장할-것) | 응답·버전·소유권 기록 |
| [완료 확인](#완료-확인) | 인라인 근거와 실제 파일 검색의 차이 |

## 1. 원문부터 읽기

로컬 `data/policies/`를 엽니다.

| 문서 | 핵심 사실 |
|---|---|
| TRAVEL-2025 | 2026-06-30까지 숙박 1인 1박 **120,000원** |
| TRAVEL-2026 | 2026-07-01부터 숙박 1인 1박 **150,000원** |
| APPROVAL-01 | 한도 초과는 **예약 전 팀장 사전 승인** |
| RECEIPT-01 | 영수증 필요, 분실 시 재무 담당자 확인 |
| MEAL-01 | 현행 식비 1인 1일 **30,000원**, 숙박 한도와 구분 |
| SCOPE-01 | 해외·항공권 정보 없음, 날짜가 없으면 확인 |

파일이 없는 것이 아니라 **무엇을 모르는지도 명시한 데이터**입니다. 실제 회사 규정이 아닙니다.

## 2. 저장되는 Prompt Agent

설정한 접두사로 이름을 만들고 실제 버전을 자동 기록합니다.

```bash
python scripts/workshop.py prompt-agent create --confirm-create --output outputs/learner-notes-ko/03-agent-created.json
```

이 실행기는 시작 지침과 합성 정책을 포함한 **관리형 Prompt Agent**를 만듭니다. 이 단계는 문서를 지침/컨텍스트에 넣는 **인라인 근거 방식**이며 File Search 실습을 완료한 것은 아닙니다.

이어서 호출합니다. 방금 생성해 `outputs/agents/`에 기록한 정확한 버전을 사용하며, 최신 버전을 임의로 선택하지 않습니다.

```bash
python scripts/workshop.py prompt-agent invoke --question "2026년 9월 국내 출장 호텔이 170000원인데 예약해도 되나요?" --output outputs/learner-notes-ko/03-agent-answer.json
```

Foundry **Build → Agents**에서 같은 이름·버전·모델·지침을 확인합니다. 응답의 날짜, 150,000원 한도, 초과 시 예약 전 승인, 원문 ID를 대조하세요.

## 3. 실제 File Search 에이전트 만들기

포털의 업로드 버튼 위치/노출에 의존하지 않고 **포함된 SDK 명령**으로 진행합니다. 01에서 프로젝트 호출을 확인한 실제 Sol 배포를 사용하고, 인라인 agent와 다른 이름을 자동으로 생성합니다.

**생성 명령은 하나만 선택합니다.** 아래 기본값은 마지막 활동 후 7일 만료입니다. 더 오래 보존하려면 아래 접힌 절의 `--retain` 명령을 **대신** 실행합니다. 나중에 두 생성 명령을 연달아 실행해 보존 설정을 바꾸지 않습니다.

```bash
python scripts/workshop.py file-search create --confirm-create
```

이 명령은 합성 문서 6개 업로드 → vector store 인덱싱 확인 → File Search Prompt Agent 생성 → 정확한 버전/소유 ID 기록을 수행합니다. 정책 전체를 지침에 붙여 넣는 방식이 아닙니다.

**확인:** `indexed_files: 6`, 실제 `agent_name`, `agent_version`, `vector_store_id`를 확인합니다. 소유 기록은 `outputs/file-search/<agent-name>/ownership.json`입니다. 중간 오류가 나도 이미 생성한 ID는 보존하므로 임의로 파일을 중복 업로드하지 않습니다.

저장소는 **마지막 활동 후 7일 만료**로 생성합니다. 이는 과정 시간 제한이 아니라 보관/비용 설정입니다. 만료 후 재개하거나 새 모델 설정으로 다시 실행할 때는 기존 자원을 확인하고 새 소유 이름으로 시작합니다.

<details>
<summary>선택: 자동 만료 없이 보존 — 기본 create 대신 실행</summary>

`--retain`은 vector store의 자동 만료를 설정하지 않습니다. 소유 기록의 `retention: retain`을 확인하고, 재개할 때도 같은 옵션을 사용합니다. 파일 저장 비용은 계속 발생할 수 있습니다.

```bash
python scripts/workshop.py file-search create --confirm-create --retain
```

</details>

모델 카탈로그의 File Search 지원과 실제 내 배포의 성공은 별개입니다. SDK에서도 지원/권한 오류가 나면 해당 원인을 해결합니다. **인라인 답변이나 다른 모델로 몰래 대체하지 않습니다.**

<details>
<summary>직접 코드를 수정하거나 자체 Storage를 사용하는 경우</summary>

Reasoning은 생성 시 **agent definition**에 저장합니다. 이후 `agent_reference`로 호출할 때 같은 `reasoning`을 요청 본문에 다시 넣으면 `Not allowed when agent is specified` 오류가 납니다. 포함된 실행기는 저장 버전의 설정을 상속하고 출력 상한만 요청에 전달합니다.

자체 Storage를 연결한 환경은 사용자/서비스 관리 ID의 **Storage Blob Data Contributor** 같은 추가 접근이 필요할 수 있습니다. Basic/Standard setup과 실제 저장소를 [공식 File Search 문서](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/file-search)에서 확인하고 **본인 저장소 범위에만** 부여합니다.

</details>

## 4. 세 질문으로 구분

각 질문은 저장한 정확한 agent 버전에 독립적으로 전달합니다.

```bash
python scripts/workshop.py file-search ask --question "2026년 9월 국내 출장 숙박비 한도와 근거는?" --label current
```

**파일 검색 질문 실행 · `previous`**

```bash
python scripts/workshop.py file-search ask --question "2026년 5월 국내 출장 숙박비 한도와 근거는?" --label previous
```

**파일 검색 질문 실행 · `missing`**

```bash
python scripts/workshop.py file-search ask --question "도쿄 출장 호텔비 한도는?" --label missing
```

**확인:**

| 질문 | 기대 결과 |
|---|---|
| 2026년 9월 | 현행 한도 **150,000원** |
| 2026년 5월 | 과거 한도 **120,000원** |
| 도쿄 출장 | **근거 부족**. 국내 한도를 대신 적용하지 않음 |

실제 `file_search_calls`, 내 업로드 파일을 가리키는 `file_citations`, `file_search_verified: true`를 확인합니다. 프로그램은 검색 호출이나 소유 파일 인용이 없으면 성공으로 처리하지 않습니다.

`result_directory`의 원시 응답과 원문 TXT를 대조합니다. Foundry Agents 목록에서도 같은 이름/버전을 열어 지침과 File Search를 확인할 수 있습니다. **문서 ID를 답변에 써 놓은 것과 실제 파일 인용은 다릅니다.**

## 5. 저장할 것

생성·응답 JSON과 `outputs/agents/`, `outputs/file-search/`의 소유 기록을 보관합니다. 실제 이름·버전·응답 ID·파일/저장소 ID는 이 파일에서 다시 확인할 수 있으므로 따로 옮겨 적지 않습니다. 파일 저장과 검색은 모델 토큰 외 과금이 있을 수 있습니다.

같은 label은 덮어쓰지 않습니다. 필요한 재시도에는 `current-2`처럼 새 label을 사용하고 원래 실패도 보관합니다. 이 단계의 삭제는 15장에서 소유 기록을 확인한 뒤 진행합니다.

**막히면:** 업로드 완료와 인덱싱 완료를 구분하고, API key를 넣어 우회하지 않습니다. 인용이 없거나 잘못된 날짜의 문서를 쓰면 실패 사례로 보존합니다.

인덱싱이 아직 진행 중인 시간 초과라면 같은 생성 명령으로 상태를 다시 확인할 수 있습니다. 영구 실패나 만료라면 원인을 해결하고 15의 소유 자산 목록을 확인한 뒤 **새 이름**을 `--name`에 지정해 생성하세요. 보존 모드에서는 이전 자산도 삭제하지 않습니다. 같은 이름의 원격 agent가 있는데 버전 기록이 없다면 새 버전을 추측해 만들지 말고 포털의 실제 자산부터 확인합니다.

## 완료 확인

- [ ] 인라인 agent와 File Search agent의 이름·정확한 버전을 구분했다.
- [ ] 파일 6개 인덱싱, 실제 검색 호출, 내 파일 인용을 확인했다.
- [ ] 세 답변을 원문과 대조하고 실패·소유권·만료 설정을 보관했다.

---

[← 02. 모델·지침](02-models-prompts.md) · [전체 과정](../README.ko.md#진행-순서) · [04. 도구 →](04-tools.md) · [진행 지도 ↑](#chapter-map)
