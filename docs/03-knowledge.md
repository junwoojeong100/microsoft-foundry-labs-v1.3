# 03. Prompt Agent와 File Search

[English](en/03-knowledge.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 지침에 문서를 넣는 방식과 파일을 검색하는 방식을 비교합니다.

**시작 조건:** 00장의 설정, 01장의 Sol 호출 성공, 02장의 지침 비교.

**실행 위치:** 편집기에서 원문 읽기 → 터미널에서 생성·호출 → Foundry에서 버전 확인.

에이전트를 **두 개** 만듭니다. 첫 번째는 문서를 지침에 넣고, 두 번째는 File Search로 검색합니다. 이름과 버전은 실행기가 따로 저장합니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. 원문 읽기](#1-원문부터-읽기) | 날짜별 한도와 자료가 없는 범위 |
| [2. Prompt Agent](#2-저장되는-prompt-agent) | 저장된 버전과 실제 답변 |
| [3. File Search 생성](#3-실제-file-search-에이전트-만들기) | 파일 6개 인덱싱 |
| [4. 검색 확인](#4-세-질문으로-구분) | 실제 검색 호출과 파일 인용 |
| [5. 결과 보관](#5-저장할-것) | 응답·버전·소유 기록 |
| [완료 확인](#완료-확인) | 두 방식의 차이 |

## 1. 원문부터 읽기

편집기에서 `data/policies/`의 TXT 파일 6개를 읽습니다. 모두 실습용 가상 규정입니다.

| 문서 | 답변에 적용할 사실 |
|---|---|
| TRAVEL-2025 | 2026-06-30까지 숙박 1인 1박 **120,000원** |
| TRAVEL-2026 | 2026-07-01부터 숙박 1인 1박 **150,000원** |
| APPROVAL-01 | 한도 초과는 **예약 전 팀장 사전 승인** |
| RECEIPT-01 | 영수증 필요. 분실 시 재무 담당자 확인 |
| MEAL-01 | 현행 식비 1인 1일 **30,000원** |
| SCOPE-01 | 해외·항공권 정보 없음. 출장 날짜가 없으면 확인 |

## 2. 저장되는 Prompt Agent

**문서를 지침에 포함한 에이전트 생성**

```bash
python scripts/workshop.py prompt-agent create --confirm-create --output outputs/learner-notes-ko/03-agent-created.json
```

생성 결과의 이름·버전을 확인한 뒤 호출합니다. 다음 명령은 `outputs/agents/`에 저장한 **정확한 버전**을 사용합니다.

```bash
python scripts/workshop.py prompt-agent invoke --question "2026년 9월 국내 출장 호텔이 170000원인데 예약해도 되나요?" --output outputs/learner-notes-ko/03-agent-answer.json
```

**확인:** 답변에 150,000원 한도, 한도 초과, 예약 전 팀장 승인, 근거 문서가 있어야 합니다. Foundry **Build → Agents**에서 같은 이름·버전·모델·지침을 확인합니다.

이 방식은 문서를 지침에 넣은 **인라인 근거 방식**입니다. 아직 File Search를 실행한 것은 아닙니다.

## 3. 실제 File Search 에이전트 만들기

인덱싱은 업로드한 파일을 검색할 수 있게 준비하는 작업입니다. 아래 명령은 **업로드 → 인덱싱 → 에이전트 생성**을 수행합니다.

**기본 생성 — 마지막 활동 후 7일 만료**

```bash
python scripts/workshop.py file-search create --confirm-create
```

| 출력 | 확인할 값 |
|---|---|
| `indexed_files` | `6` |
| `agent_name`, `agent_version` | 새 File Search 에이전트의 실제 이름·버전 |
| `vector_store_id` | 검색용 파일 저장소의 ID |

소유 기록은 `outputs/file-search/<agent-name>/ownership.json`에 저장됩니다. **6개 인덱싱이 끝나야** 다음 질문을 실행합니다. 파일 저장·검색에도 비용이 발생할 수 있습니다.

<details>
<summary>자동 만료 없이 보존할 때만: 기본 create 대신 실행</summary>

```bash
python scripts/workshop.py file-search create --confirm-create --retain
```

`retention: retain`을 확인합니다. 저장 비용이 계속 발생할 수 있습니다. 기본 명령과 이 명령을 연달아 실행해 만료 설정을 바꾸지 않습니다.

</details>

**막히면:** 인덱싱 중 시간 초과라면 같은 생성 명령으로 상태를 다시 확인합니다. 영구 실패·만료라면 소유 기록을 먼저 읽고, 원인을 해결한 뒤 새 `--name`을 사용합니다. 파일을 반복 업로드하거나 인라인 답변으로 대체하지 않습니다.

자체 Storage를 연결했다면 추가 데이터 역할이 필요할 수 있습니다. [공식 File Search 안내](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/file-search)에서 실제 저장소와 호출 주체를 확인합니다.

## 4. 세 질문으로 구분

**현행 규정**

```bash
python scripts/workshop.py file-search ask --question "2026년 9월 국내 출장 숙박비 한도와 근거는?" --label current
```

**과거 규정**

```bash
python scripts/workshop.py file-search ask --question "2026년 5월 국내 출장 숙박비 한도와 근거는?" --label previous
```

**자료가 없는 규정**

```bash
python scripts/workshop.py file-search ask --question "도쿄 출장 호텔비 한도는?" --label missing
```

각 명령의 `result_directory`를 열어 다음을 대조합니다.

| 결과 이름(label) | 기대 답변 |
|---|---|
| `current` | **150,000원**, TRAVEL-2026 근거 |
| `previous` | **120,000원**, TRAVEL-2025 근거 |
| `missing` | **근거 부족**. 국내 한도를 해외에 적용하지 않음 |

세 결과 모두 실제 `file_search_calls`, 내 파일을 가리키는 `file_citations`, `file_search_verified: true`를 확인합니다. 답변에 문서 ID를 적은 것만으로 검색 성공이 아닙니다.

**기대와 다르면:** 질문 날짜·반환 원문·인용을 비교합니다. 실패 결과는 보관하고, 재시도에는 `current-2`처럼 새 label을 사용합니다.

## 5. 저장할 것

`outputs/learner-notes-ko/`, `outputs/agents/`, `outputs/file-search/`를 보관합니다. 이름·버전·응답 ID·파일 ID를 따로 옮겨 적을 필요는 없습니다.

기본 파일 저장소는 마지막 활동 후 7일에 만료됩니다. 다음 날 재개할 때 실제 상태를 확인하세요. 삭제는 [15장](15-capstone-cleanup.md)에서 소유 기록과 다른 에이전트의 참조를 확인한 뒤 결정합니다.

## 완료 확인

- [ ] 두 에이전트의 이름과 버전을 구분했다.
- [ ] 파일 6개 인덱싱과 실제 검색·파일 인용을 확인했다.
- [ ] 세 답변을 원문과 대조하고, 소유 기록과 만료 설정을 보관했다.

---

[← 02. 모델·지침](02-models-prompts.md) · [전체 과정](../README.ko.md#진행-순서) · [04. 도구 →](04-tools.md) · [진행 지도 ↑](#chapter-map)
