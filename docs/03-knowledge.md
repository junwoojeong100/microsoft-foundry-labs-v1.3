# 03. Prompt Agent와 File Search

**완료 목표:** 지침과 버전을 저장한 에이전트를 만들고, 별도로 실제 파일 검색과 인용을 확인합니다.

**시작 조건:** 00~02의 설정과 응답 모델. 사용할 데이터는 아래 **한빛기술 6문서만**입니다.

## 1. 원문부터 읽기

로컬 `.reference/v1.2/data/learner/ko/policies/`를 엽니다.

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

내 `WORKSHOP_PREFIX` 뒤에 `-policy`를 붙여 고유 이름을 만듭니다. 다음 예시 이름을 본인의 것으로 바꿉니다.

```bash
python scripts/workshop.py prompt-agent create --name "mfv2-jw-0927-policy" --confirm-create --output outputs/learner-notes-ko/03-agent-created.json
```

이 실행기는 시작 지침과 합성 정책을 포함한 **관리형 Prompt Agent**를 만듭니다. 이 단계는 문서를 지침/컨텍스트에 넣는 **인라인 근거 방식**이며 File Search 실습을 완료한 것은 아닙니다.

실제로 반환된 버전을 기록하고 호출합니다. `1`이라고 가정하지 않습니다.

```bash
python scripts/workshop.py prompt-agent invoke --name "mfv2-jw-0927-policy" --version "실제-버전" --question "2026년 9월 국내 출장 호텔이 170000원인데 예약해도 되나요?" --output outputs/learner-notes-ko/03-agent-answer.json
```

Foundry **Build → Agents**에서 같은 이름·버전·모델·지침을 확인합니다. 응답의 날짜, 150,000원 한도, 초과 시 예약 전 승인, 원문 ID를 대조하세요.

## 3. 실제 File Search 에이전트 만들기

인라인과 검색을 섞지 않도록 **`<내-prefix>-files`라는 별도 Prompt Agent**를 만듭니다.

1. Foundry **Agents → Create agent**에서 내 이름과 `workshop-chat`을 선택합니다.
2. Instructions에는 아래 지침만 넣습니다. 정책 원문 전체를 붙여 넣지 않습니다.
3. **Tools / Knowledge → Add → File Search**에서 새 저장소를 만들고 앞의 TXT 6개를 업로드합니다.
4. 파일의 인덱싱 상태가 완료될 때까지 기다립니다.
5. 설정을 저장하고 실제 agent 버전을 기록합니다.

```text
당신은 한빛기술의 합성 출장 규정 안내 도우미입니다.
규정 질문은 반드시 File Search로 검색한 뒤 답하세요.
질문의 출장일에 유효한 문서를 선택하고 파일 인용과 문서 ID를 표시하세요.
자료가 없거나 날짜가 부족하면 추측하지 말고 확인을 요청하세요.
예약, 승인, 지급은 실행할 수 없습니다.
```

File Search 버튼이나 업로드가 지원되지 않으면 모델·지역·에이전트 설정을 확인합니다. **인라인 원문으로 대체한 뒤 RAG 성공이라고 표시하지 않습니다.** 본인 구독에서 지원되는 모델을 명시적으로 준비하거나 해당 기능을 차단으로 남깁니다.

자체 Storage를 연결한 환경은 사용자/서비스 관리 ID의 **Storage Blob Data Contributor** 같은 추가 접근이 필요할 수 있습니다. Basic/Standard setup과 실제 저장소를 [공식 File Search 문서](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/file-search)에서 확인하고 **본인 저장소 범위에만** 부여합니다.

## 4. 세 질문으로 구분

Playground에서 독립적인 새 대화로 각각 묻습니다.

```text
2026년 9월 국내 출장 숙박비 한도와 근거는?
2026년 5월 국내 출장 숙박비 한도와 근거는?
도쿄 출장 호텔비 한도는?
```

기대 결과는 **150,000원 / 120,000원 / 근거 부족**입니다. 현재와 과거의 날짜를 뒤집지 않았는지 확인합니다.

인용을 눌러 실제 파일의 해당 문장을 읽습니다. 실행 세부 정보에서 File Search 호출도 확인합니다. **문서 ID를 답변에 써 놓은 것과 실제 파일 인용은 다릅니다.**

## 5. 저장할 것

인라인 agent와 File Search agent 각각의 이름·버전·응답 ID, 파일/저장소 ID, 원문 대조 결과를 워크북에 기록합니다. 파일 저장과 검색은 모델 토큰 외 과금이 있을 수 있습니다.

**막히면:** 업로드 완료와 인덱싱 완료를 구분하고, API key를 넣어 우회하지 않습니다. 인용이 없거나 잘못된 날짜의 문서를 쓰면 실패 사례로 보존합니다.

**다음 → [04. MAF·함수·MCP·Code Interpreter](04-tools.md)**
