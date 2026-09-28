# 데이터와 결과를 구분하기

**원문·평가 입력·실제 응답은 서로 다른 자료입니다.** 답변 모델에 평가 정답을 넣거나 미리 만든 답변을 실제 호출 결과로 사용하지 않습니다.

| 위치 | 내용 | 용도 |
|---|---|---|
| `data/knowledge/` | 한빛기술 가상 규정 | 검색·답변 근거 |
| `data/policies/` | 같은 규정의 TXT 파일 | File Search 업로드 |
| `data/evaluation/dev.jsonl` | 개발용 6문항 | 반복 개선 |
| `data/evaluation/holdout.jsonl` | 최종 4문항 | **15장까지 열지 않음** |
| `data/evaluation/policy-calibration.json` | 평가 모델 점검용 8개 사례 | 3개 기준의 기대 판정 24개 |
| `data/evaluation/policy-lab.jsonl` | 보완 진단 8문항 | core dev·holdout·관리형 평가와 별개 |
| `data/evaluation/calibration.jsonl` | 이전 grounding 예시 2개 | 이전 검사 전용. policy calibration 대체 불가 |
| `data/fixtures/` | 미리 작성한 답변 | 오프라인 검사기 연습 |
| `outputs/` | 내가 실행한 결과 | 확인·비교·정리 |

영문 자료는 각 `en/` 폴더에 있습니다. 서로 다른 언어의 결과를 같은 조건의 실험으로 합치지 않습니다.

## 프로젝트·리전별 실행 경계

프로젝트·엔드포인트·접두사가 다른 결과는 구분합니다. 새 프로젝트는 **새 소스 폴더**에서 시작하고 이전 `.env`, 소유 기록, 결과를 활성 설정으로 복사하지 않습니다.

label을 바꾸면 입력 준비·수집·평가·비교·최종 확인의 참조도 모두 바꿉니다. 이전 결과를 새 이름으로 복사해 재실행처럼 표시하지 않습니다.

실행 이력은 [검증 보고서](validation-report.md)에 있습니다. 그 결과는 본인의 실행을 대신하지 않습니다.

## 지침 개정의 출처 기록

`data/localization.json`은 최초 파일 정보와 현재 지침 개정(`active_prompt_revision`)을 구분해 보관합니다. hash는 **내용의 식별값**입니다.

지침을 바꾸면 새 실행에 새 hash가 남아야 합니다. 과거 응답·패키지·평가 결과의 hash를 현재 값으로 고치지 않습니다.

## Policy 평가 입력과 결과

[07장의 준비 명령](07-evaluation.md#5-원문-참조를-감사하는-policy-평가)은 다음을 만듭니다.

| 파일·필드 | 의미 |
|---|---|
| `optimizer-dev.jsonl` | 평가·최적화 입력 |
| `ground_truth` | 평가자에게 전달할 **신뢰할 원문 참조 묶음** |
| `policy-evaluator-definitions.json` | 평가 기준 정의 |
| manifest | 입력의 언어·원문·지침·설정 기록 |
| source hash / `reference_id` | 제출 원문과 반환 설명을 대조할 값 |
| `result` / `reason` | 정수 점수 1~5 / 채점 이유 |

세 기준 `policy_groundedness`, `policy_helpfulness`, `policy_compliance`는 모두 **4 이상 통과**입니다. 원문 참조 검사가 `valid`여도 점수까지 통과한 것은 아닙니다.

Calibration의 **24/24는 기대 판정의 일치 수**입니다. 나쁜 답변까지 높은 점수를 받는 것이 목표가 아닙니다. 준비·calibration·실제 답변 채점을 각각 확인합니다.

### 진단 사례의 인용과 구조화 필드

진단 suite version 2는 **PL05·PL06·PL07**에 `allowed_citations`를 지정합니다.

- 필수 `required_citations`는 빠질 수 없습니다.
- 추가 인용은 허용 목록 안의 알려진 문서 ID여야 합니다.
- 중복·무관한 인용은 허용하지 않습니다.

PL06처럼 **절차만 묻는 질문**은 `limit_krw: null`이어야 합니다. 원문에 한도가 있어도 묻지 않은 금액을 채워 넣지 않습니다.

이 구조화 검사는 평가 모델의 의미 점수와 별개입니다. 이전 suite version 1 결과는 그대로 보관합니다. 배포 버전·지침 `v2`·suite 버전은 서로 다른 값입니다.

### Optimizer export 감사

[12장의 `scripts/audit_optimizer.py`](12-improvement.md#3-지침만-최적화)는 저장된 평가와 업로드 원본·calibration을 대조합니다. 새 모델 호출은 하지 않습니다.

`proof_level`은 반환 원문·설명의 참조 ID·대조 사례 기반 검사입니다. `internal_judge_requests_captured: false`이므로 숨겨진 judge 요청을 캡처한 것은 아닙니다. 감사 통과·후보 생성·품질 개선도 각각 다른 결과입니다.

## Memory 이름과 보존 설정

`WORKSHOP_MEMORY_STORE_NAME`은 **전역 선택값**입니다. 언어를 바꿔도 자동으로 바뀌지 않습니다.

| 언어 | 내 접두사 아래의 새 이름 |
|---|---|
| 한국어 | `<prefix>-memory-retained-ko` |
| 영어 | `<prefix>-memory-retained-en` |

**한국어 저장소 이름 선택**

```bash
python scripts/selfstudy.py set WORKSHOP_MEMORY_STORE_NAME "YOUR-PREFIX-memory-retained-ko"
```

**계획 확인**

```bash
python scripts/workshop.py memory plan
```

이름 선택과 계획만으로 원격 저장소가 생기지는 않습니다. [11장의 생성 절차](11-memory-a2a-routines.md#1-memory-실제-저장과-새-요청에서의-조회)를 따릅니다.

TTL `0`은 **항목 자동 만료 없음**, 양수는 최대 31,536,000초(365일)입니다. 기존 저장소의 TTL은 자동 변경되지 않습니다.

`outputs/memory/<store-name>/ownership.json`의 실제 이름·언어·TTL·ID를 보관합니다. 새 실행에는 새 label을 사용합니다.

[07 평가](07-evaluation.md) · [15 최종 확인](15-capstone-cleanup.md)
