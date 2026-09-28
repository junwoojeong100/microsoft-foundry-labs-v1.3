# 데이터와 결과를 구분하기

| 위치 | 내용 | 용도 |
|---|---|---|
| `data/knowledge/` | 한빛기술 합성 정책 | 검색과 답변 근거 |
| `data/policies/` | 같은 정책의 TXT 파일 | File Search 업로드 |
| `data/evaluation/dev.jsonl` | 개발용 6문항 | 반복 개선 |
| `data/evaluation/holdout.jsonl` | 최종 확인용 4문항 | 후보를 고정한 뒤 한 번 확인 |
| `data/evaluation/calibration.jsonl` | 이전 grounding 예시 2개 | legacy 검사 전용, policy calibration 대체 불가 |
| `data/evaluation/policy-calibration.json` | policy control 8개 | 3개 기준의 기대 판정 24개 점검 |
| `data/evaluation/policy-lab.jsonl` | 명시적 합성 진단 8문항 | 별도 `policy-lab` suite, holdout 아님 |
| `data/fixtures/` | 미리 작성한 답변 | 로컬 검사기 연습 |
| `outputs/` | 내가 실제로 실행한 결과 | 검토·비교·정리 |

`demo`의 fixture는 모델이 방금 만든 답변이 아닙니다. 실제 응답·인용·사용량·trace의 증거로 사용하지 않습니다.

영문 데이터는 `en/`에 따로 있으며 ID·금액·날짜와 판단 기준을 유지합니다. 서로 다른 언어의 결과를 한 번의 고정 실험으로 합치지 않습니다.

## 프로젝트·리전별 실행 경계

현재 실습은 **새 North Central US 프로젝트**입니다. Sweden의 `.env`·소유권 ledger·실험 결과·패키지는 비공개 hash 보관본으로 남기며 새 활성 workspace에 인수하지 않습니다. 새 프로젝트 ID/Endpoint/prefix를 확인하고 언어별 독립 소유 이름을 사용합니다.

새 label의 예시는 `nc-baseline-ko`, `nc-candidate-ko`, `nc-policy-calibration-ko`, `nc-policy-lab-ko`이며 영어는 `-en`으로 구분합니다. 각 장의 예시를 바꿀 때 입력 준비·수집·평가·compare·report·verify의 모든 참조를 같은 이름으로 맞춥니다. 이전 결과 파일을 새 label로 복사하거나 hash를 바꾸지 않습니다.

아래 Sweden 기록은 역사적 근거입니다. NC 혼합 관리형 job의 원래 6행은 **5 pass/1 fail**이며, 별도 Task Adherence-only job은 **5/5**입니다. 원래 실패 행을 빼거나 custom 진단으로 바꾸지 않습니다. 각 run의 원시 기록·입력 가림·실제 반환 수·판정 방향을 보존하며, 두 job 모두 holdout과 별개입니다.

정책이나 지침을 바꾸면 사용한 버전과 hash를 보관합니다. 원시 응답·평가 점수·holdout을 고쳐 통과시키지 않습니다.

## 지침 개정의 출처 기록

`data/localization.json`은 **최초 동결 파일·hash·시각을 그대로 보존**합니다. 별도 `active_prompt_revision`에는 2026-09-28의 근거 전용 사실/절차 응답 개정, 이전 commit, 한국어·영어 prompt의 이전/새 SHA-256, 영어 workflow hash를 기록합니다.

원래 corpus·core dev·holdout hash는 바뀌지 않았습니다. 검사는 현재 지침 개정과 과거 동결 출처를 함께 확인하며, 기존 실험의 hash를 새 값으로 바꾸지 않습니다. 새 실행은 현재 개정과 실제 hash를 기록하고 이전 결과는 그대로 보관합니다.

## Policy 평가 입력과 결과

`prepare-extensions --policy --label policy-inputs-ko`는 새 label에 원문 참조 envelope가 있는 `optimizer-dev.jsonl`, `policy-evaluator-definitions.json`, manifest를 준비합니다. 기존 `extensions-ko`나 실제 평가 결과를 수정하지 않습니다.

평가 모드는 `policy-reference-v1`이며 `ground_truth`는 evaluator에 전달하는 신뢰된 원문 참조입니다. Target agent의 입력이나 Skill 업로드 전체에 넣지 않습니다. 각 행의 source hash와 `reference_id`, canonical `result`(정수 1~5)와 `reason`을 감사합니다. 세 기준 `policy_groundedness`, `policy_helpfulness`, `policy_compliance`는 모두 **4 이상 통과·높을수록 좋음**입니다.

Policy calibration의 24/24는 기대 판정의 일치 수이지 나쁜 control까지 높은 점수를 받아야 한다는 뜻이 아닙니다. `policy-lab` 8문항은 core dev 6문항·holdout 4문항과 별도입니다. 입력 준비, calibration 성공, 실제 target grading 성공을 각각 구분합니다.

### 진단 사례의 인용과 구조화 필드

**진단 suite version 2**는 두 언어 모두 **PL05·PL06·PL07에만** 명시적 `allowed_citations`를 사용합니다. 허용 목록은 필수 `required_citations`를 모두 포함합니다. 사례 목록과 답변의 인용 ID는 알려진 문서 ID이며 중복이 없어야 합니다. 답변도 필수 참조를 빠뜨릴 수 없고, 추가 인용은 허용 목록 안에 있어야 하며 무관한 참조는 거부합니다. 다른 사례 계약은 유지합니다.

이 계약은 **NC Hosted IQ 배포 v2의 별도 진단 8행**에서도 확인했습니다. 이전 Sweden Hosted v3와 동결 suite version 1 기록은 원래 형태 그대로 보관하며 저장된 버전/hash를 수정하지 않습니다. 배포 버전, prompt 키와 suite 버전은 서로 다른 값입니다.

PL06처럼 **절차만 묻는 질문**은 금액을 요구하지 않으므로 `limit_krw`가 **`null`**이어야 합니다. 원문에 150000원이 있더라도 요청하지 않은 한도를 채워 넣지 않습니다. 이 구조화 검사는 의미 judge와 별개이며, 수정된 지침은 새 동결 runtime/label에서 확인했습니다. 이전 `150000` 응답은 수정하지 않습니다.

### Optimizer export 감사

`scripts/audit_optimizer.py`는 `--export-directory`, 원본 `--dataset`, `--calibration-label`, 자체 `--language`와 새 `--output` 경로를 받는 독립 로컬 감사입니다. [12의 명령](12-improvement.md#3-지침만-최적화)을 사용하며 `workshop.py --script` 별칭으로 추측하지 않습니다.

원래 `definition.json`·`run.json`·`output-items.json`·`summary.json`과 원문/calibration을 읽고 입력 hash를 보존합니다. `proof_level`은 source echo + reason reference ID + counterfactual calibration이며 **`internal_judge_requests_captured: false`**입니다. 감사 valid와 지침 개선·후보 생성은 별개입니다.

## Memory 이름과 보존 설정

`WORKSHOP_MEMORY_STORE_NAME`은 현재 실행에 적용되는 **전역 선택값**입니다. 한 언어에서 정한 이름이 다른 언어에서도 자동 변경 없이 적용되므로 언어를 바꿀 때 반드시 다시 지정합니다.

| 실행 언어 | 현재 prefix 아래의 새 보존용 이름 |
|---|---|
| 한국어 | `<prefix>-memory-retained-ko` |
| 영어 | `<prefix>-memory-retained-en` |

한국어 실행 예시이며 `YOUR-PREFIX`는 본인 prefix로 바꿉니다.

```bash
python scripts/selfstudy.py set WORKSHOP_MEMORY_STORE_NAME "YOUR-PREFIX-memory-retained-ko"
python scripts/workshop.py memory plan
```

새 store는 [11의 생성 절차](11-memory-a2a-routines.md#1-memory-실제-저장과-새-요청에서의-조회)에서 `memory create --ttl-seconds 0 --confirm-create`로 만듭니다. **0은 새 기본값이며 자동 항목 만료 없음**, 양수는 최대 31,536,000초(365일)입니다.

이름 선택이나 로컬 plan만으로 원격 store가 생성·변경된 것은 아닙니다. `outputs/memory/<store-name>/ownership.json`의 실제 이름·언어·TTL·ID를 보관합니다. 기존 1시간 store와 결과는 원래 TTL 그대로 유지하며 삭제·수정·임의 인수하지 않습니다. 새 store의 결과에는 새 label을 사용합니다.

[07 평가](07-evaluation.md) · [15 최종 확인](15-capstone-cleanup.md)
