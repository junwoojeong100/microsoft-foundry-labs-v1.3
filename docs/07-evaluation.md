# 07. 업무 평가와 Foundry 평가

**완료 목표:** 같은 문항으로 지침을 비교하고, 실제 응답에 Foundry judge를 적용합니다.

**시작 조건:** 기본 모델·한빛기술 데이터·실제 SDK 응답. 이 장의 대상은 **직접 SDK + 사전 검색 응답 경로**입니다. 03의 관리형 agent나 나중의 Hosted 버전과 같은 실행이라고 표현하지 않습니다.

## 1. dev와 holdout 분리

| 데이터 | 용도 |
|---|---|
| dev 6문항 | 실패 분석·지침 개선·비교 |
| holdout 4문항 | 후보를 고정한 뒤 최종 인수 |
| calibration | 좋은/나쁜 예시에 judge가 어떻게 반응하는지 확인 |

holdout은 15장까지 열지 않습니다. 정답 필드를 모델 입력에 넣지 않습니다.

## 2. baseline 수집

```bash
python scripts/workshop.py collect --split dev --label baseline --prompt v1 --retrieval local
python scripts/workshop.py evaluate --label baseline
```

`outputs/baseline/`의 `manifest.json`, `responses.jsonl`, `business-evaluation.json`을 엽니다.

`total`, `passed`, `errors`, `business_gate_passed`와 **6개 사례의 checks 전체**를 읽습니다. 이 평가는 결정적 업무 검사이며 LLM judge가 아닙니다.

| 문항 | 확인 |
|---|---|
| D01 | 현행 숙박 150,000원 / TRAVEL-2026 |
| D02 | 과거 숙박 120,000원 / TRAVEL-2025 |
| D03 | 170,000원 호텔의 사전 승인 필요 |
| D04 | 식비 30,000원/일 |
| D05 | 해외 규정의 근거 부족 |
| D06 | 규정 무시·승인 완료 요구를 따르지 않음 |

실패가 있으면 실제 실패 ID와 이유를 기록합니다. 예시 ID를 무조건 복사하지 않습니다.

```bash
python scripts/workshop.py feedback --label baseline --case "실제-실패-case-ID" --reason "실제 응답과 실패 검사에 근거한 이유"
```

이 명령은 검토 대기 기록을 만들 뿐 업무 승인을 하지 않습니다. 모두 통과했다면 가짜 실패를 만들지 말고 전체 통과 검토를 워크북에 남깁니다.

## 3. 같은 조건으로 candidate

`prompts/v1.txt`와 `prompts/v2.txt`를 비교합니다. 두 파일은 비교할 지침입니다. 모델·코드·원문·질문·retrieval은 그대로 둡니다.

```bash
python scripts/workshop.py collect --split dev --label candidate --prompt v2 --retrieval local
python scripts/workshop.py evaluate --label candidate
python scripts/workshop.py compare --baseline baseline --candidate candidate --variable prompt
```

`comparison-vs-baseline.json`의 조건, 양쪽 지표, `changed_context_cases`를 확인합니다. 원시 응답·점수·hash를 편집하지 않습니다. 같은 점수면 “이번 6문항에서 개선이 입증되지 않음”도 정상입니다.

코드를 변경했다면 같은 코드로 새 baseline/candidate 쌍을 만들어야 합니다. 평가 기준을 낮추거나 오류 행을 빼서 개선을 만들지 않습니다.

## 4. judge 모델 직접 준비

1. Foundry 카탈로그에서 평가에 지원되는 GPT 모델을 확인합니다. 시작 후보는 `gpt-4.1-mini`입니다.
2. 같은 리소스에 `workshop-judge`라는 별도 배포를 만들고 Succeeded를 확인합니다.
3. judge와 답변 모델을 구분해 기록합니다.

```bash
python scripts/selfstudy.py set AZURE_AI_EVALUATION_MODEL_DEPLOYMENT_NAME workshop-judge
python scripts/workshop.py cloud-evaluate --label candidate --timeout 300 --confirm-cost
```

이미 수집된 응답을 평가합니다. **새 target 응답을 수집하는 작업이 아닙니다.** native 평가 ID·실행 ID·모든 행의 원점수·오류·사용한 judge를 보관합니다.

Foundry **Evaluation**에서 같은 실행을 찾아 행 수와 완료 상태를 확인합니다. `Partial`, 누락된 evaluator, 빈 결과를 완료로 처리하지 않습니다. 올바른 “근거 부족” 답변도 일반 Relevance judge가 낮게 평가할 수 있으므로 설명을 읽습니다.

## 5. 사용자 지정 업무 기준과 실행 비교

해당 Preview 기능을 지원하고 추가 과금을 수락한 경우:

```bash
python scripts/workshop.py cloud-evaluate --label baseline --business-evaluator --timeout 300 --confirm-cost
python scripts/workshop.py cloud-evaluate --label candidate --business-evaluator --reference baseline --timeout 300 --confirm-cost
```

실제로 포함된 evaluator 목록, 전체 6행, 로컬 업무 기준과의 일치 여부를 확인합니다. 서비스가 사용자 지정 결과를 누락했다면 실패 기록을 보존합니다. 낮은 점수만 골라 재실행하지 않습니다.

## 6. 모델 비교까지 확장

02에서 만든 다른 배포가 있으면 **같은 v2·local·dev 조건**으로 수집합니다.

```bash
python scripts/workshop.py --model-deployment workshop-compare collect --split dev --label model-compare --prompt v2 --retrieval local
python scripts/workshop.py evaluate --label model-compare
python scripts/workshop.py compare --baseline candidate --candidate model-compare --variable model
```

품질·실패·토큰·지연을 함께 보고 선택/유지 이유를 적습니다. Router나 다른 provider를 오류 처리 fallback으로 쓰지 않습니다.

## 완료 확인

실제 6행, 전후 비교, judge 결과, 자신의 검토를 남깁니다. **holdout을 아직 열지 않고** candidate와 해당 설정을 보관합니다.

**다음 → [08. Hosted 로컬 실행과 Azure 배포](08-hosted.md)**
