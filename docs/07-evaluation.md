# 07. 업무 평가와 Foundry 평가

**완료 목표:** 같은 문항으로 지침을 비교하고, 실제 응답에 Foundry judge를 적용합니다.

**시작 조건:** 설정한 Sol·한빛기술 데이터·실제 SDK 응답. 이 장의 대상은 **직접 SDK + 사전 검색 응답 경로**입니다. 03의 관리형 agent나 나중의 Hosted 버전과 같은 실행이라고 표현하지 않습니다.

아래 label은 새 실습의 예시입니다. 기존 결과가 있다면 새로운 baseline/candidate label을 정하고 모든 후속 참조에 동일하게 사용합니다. 이전 모델·judge·코드 조건의 파일이나 점수를 덮어쓰지 않습니다.

**현재 NC 상태:** 한·영 Sol + IQ SDK dev 6/6, 각 언어의 policy calibration 24/24를 확인했습니다. 영어는 첫 5/6 실패를 보존하고 06의 검색 문턱을 명시한 새 실행에서 6/6을 확인했습니다. Hosted v1/v2와 관리형 red team은 각각 12/13의 별도 대상입니다. 학습자는 새 label을 선택하고 자신의 원문·judge·전체 결과를 확인하며 기록된 점수를 인수하지 않습니다.

**역사적 Sweden Central 기록:** 당시 Sol + GA IQ SDK candidate는 세 policy 기준 각각 6/6과 valid 참조 감사를 확인했고, 한국어/영어 calibration은 각각 24/24였습니다. 이전 groundedness 5/6과 `APPROVAL-01` 없는 D01 팀장 정보 오류도 보관합니다.

**비교의 한계:** 이전/새 r2 SDK 쌍은 결합된 코드 변경으로 `code_hash`가 달라 통제 비교가 올바르게 거부되었습니다. 이 과거 쌍을 지침만의 개선 증거로 바꾸지 않습니다. 이후 **동결한 코드·corpus로 새로 실행한 Hosted IQ v1/v2**는 각 6행의 세 policy 기준 6/6, 참조 감사 valid, 실제 trace 6/6을 확인했고 `benchmark compare`도 허용되었습니다. 이는 별도의 실제 Hosted 증거입니다. 두 실행 모두 통과 수가 같으므로 dev 통과율 향상을 주장하지 않으며, 8문항 진단과 최종 인수는 구분합니다.

이후 **Sweden의 Hosted IQ 배포 버전 3**은 canonical 6행과 진단 8행을 확인했습니다. 이 역사적 custom 진단은 새 NC 실행이나 13의 관리형 AI red teaming 증거가 아니며, 새로운 holdout 검증도 아닙니다.

## 1. dev와 holdout 분리

| 데이터 | 용도 |
|---|---|
| dev 6문항 | 실패 분석·지침 개선·비교 |
| holdout 4문항 | 후보를 고정한 뒤 최종 인수 |
| policy calibration 8개 control | 긍정·부정·근거 부족·counterfactual의 3개 기준 판정 확인 |
| policy-lab 8문항 | 12의 별도 합성 진단 suite. holdout이 아님 |

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

`v2`라는 파일 이름이 같아도 내용과 hash가 바뀌면 같은 지침이 아닙니다. 이전 응답·패키지·agent 버전·label은 그대로 보관하고, 바뀐 지침을 실제 적용한 새 실행으로 비교합니다.

## 4. judge 모델 직접 준비

1. 새 환경에서는 같은 Foundry 계정에 **`gpt-5.5` / `2026-04-24`**를 **`workshop-judge`**로 배포합니다.
2. 실제 기반 모델·버전·비용·생성 완료를 확인합니다. Judge는 Sol 대상과 **다른 기반 모델이며 다른 배포**여야 합니다.
3. 해당 별칭을 judge로 등록합니다. 이 읽기/설정 명령은 배포를 생성하지 않습니다.

```bash
python scripts/selfstudy.py model --role judge --deployment workshop-judge
```

**삭제되지 않은 같은 프로젝트를 재개할 때만:** `workshop-optimizer`가 실제 GPT-5.5 / 2026-04-24인지 다시 확인했다면 아래 별칭을 사용할 수 있습니다. 새 NC에서는 Sweden 보관본의 배포를 인수하지 않고 새 `workshop-judge`를 준비합니다.

```bash
python scripts/selfstudy.py model --role judge --deployment workshop-optimizer
```

Judge를 대상 model map에 넣거나, 분리 검사를 낮추거나, 별칭만으로 실제 모델을 판단하지 않습니다. 비교할 모든 평가에서 같은 judge 조건을 유지합니다.

GPT-5.5는 GPT-6 대상과 다르지만, 이 선택만으로 모든 편향이 제거되지는 않습니다. 실제 원문·행별 설명·업무 검사와 calibration을 함께 검토합니다. 두 dev 실행이 모두 6/6이라면 통과율 개선이 입증된 것은 아닙니다. 완료 상태와 모든 품질 기준 통과도 구분합니다.

## 5. 원문 참조를 감사하는 policy 평가

새 입력 label을 사용해 준비합니다. `--policy`는 기존 Skill 입력이나 legacy 평가 결과를 변경하지 않는 별도 모드입니다.

```bash
python scripts/workshop.py prepare-extensions --policy --label policy-inputs-ko
python scripts/workshop.py calibrate-judge --policy --label policy-calibration-ko --confirm-cost --timeout 900
```

준비 폴더의 `optimizer-dev.jsonl`, `policy-evaluator-definitions.json`, manifest를 확인합니다. `ground_truth`에는 **신뢰할 원문 참조 envelope**가 들어갑니다. 이는 evaluator 입력이며 target agent에 전달할 답안이 아닙니다.

| 기준 | 확인할 것 | 통과 방향 |
|---|---|---|
| `policy_groundedness` | 제공된 원문과 일치하는가 | 4 이상, 높을수록 좋음 |
| `policy_helpfulness` | 필요한 안내·확인 질문·적절한 근거 부족 응답인가 | 4 이상, 높을수록 좋음 |
| `policy_compliance` | 규정을 따르고 허위 승인 등을 하지 않는가 | 4 이상, 높을수록 좋음 |

Canonical 출력은 정수 **`result`(1~5)**와 문자열 **`reason`**입니다. 8개 control × 3개 기준은 24개 기대 판정을 점검합니다. 나쁜 답변은 낮은 점수를 받아야 하므로 **24/24 판정 일치는 24개 모두 4점 이상이라는 뜻이 아닙니다**. 올바른 abstention·허위 승인·counterfactual 구분도 읽습니다. 한국어 성공을 영어 calibration의 증거로 사용하지 않습니다.

이 세 기준은 legacy 일반 Relevance와 다른 고정된 의미를 갖습니다. 적절한 근거 부족 응답은 `policy_helpfulness`에서 유용할 수 있습니다. 이전 Relevance 점수를 새 지표로 이름만 바꾸거나 서로 다른 기준의 숫자를 직접 개선량으로 계산하지 않습니다.

앞에서 **새 label로 수집한 완전한 dev 결과**를 평가합니다. 아래 `baseline`/`candidate`는 실제로 선택한 새 이름으로 함께 바꿉니다.

```bash
python scripts/workshop.py cloud-evaluate --policy --label baseline --confirm-cost --timeout 900
python scripts/workshop.py cloud-evaluate --policy --label candidate --reference baseline --confirm-cost --timeout 900
```

이는 저장된 target 응답의 평가이며 **새 target 추론이 아닙니다**. 출력된 `foundry-policy/`의 원점수·`cloud-evaluation-raw.json`·`cloud-evaluation-results.json`·`policy-reference-audit.json`을 보관합니다. 모든 행에 세 기준이 있고 source hash와 `reference_id`가 제출 원문 및 `reason`과 일치하는지 확인합니다.

이 감사는 **제출 원문과 반환된 참조 ID의 일치**를 확인하며, 숨겨진 judge 요청 본문 전체를 캡처했다고 주장하지 않습니다. `Partial`, 누락·오류 행, 잘못된 reference, `context=response`인 자기 근거를 통과로 바꾸지 않습니다. `--policy`와 `--business-evaluator`는 결합하지 않습니다. 이전 Relevance/grounding 점수나 2개 legacy fixture를 새 policy 결과로 이름만 바꾸지 않습니다.

**D01의 교훈:** 저장소 어딘가에 있는 사실이 이번 응답의 근거는 아닙니다. `APPROVAL-01`을 실제로 받지 않았다면 팀장 등 승인 주체를 추측해서 덧붙이지 않습니다. 이미 생성된 답변을 정당화하려고 원래 source 목록이나 `ground_truth`에 문서를 나중에 추가하지 않습니다. 새로운 조회가 필요하면 별도 실행·label로 기록합니다.

## 6. 선택적 Sol/Luna 모델 비교

02에서 Luna 비교를 선택한 경우에만 수행합니다. 실제 별칭과 같은 계정 Endpoint를 확인하고 **같은 v2·local·dev·account-responses 조건**으로 새 쌍을 수집합니다. 앞의 Sol 프로젝트 API candidate를 한쪽 결과로 섞지 않습니다.

```bash
python scripts/workshop.py --model-deployment "ACTUAL-SOL-DEPLOYMENT" collect --api account-responses --split dev --label model-sol --prompt v2 --retrieval local
python scripts/workshop.py --model-deployment "ACTUAL-LUNA-DEPLOYMENT" collect --api account-responses --split dev --label model-luna --prompt v2 --retrieval local
python scripts/workshop.py evaluate --label model-sol
python scripts/workshop.py evaluate --label model-luna
python scripts/workshop.py compare --baseline model-sol --candidate model-luna --variable model
```

계정 API와 프로젝트 API 결과를 섞으면 모델 외 조건도 달라집니다. 수집 manifest의 `inference.api`와 실제 Endpoint까지 고정하세요. 이 선택적 비교가 기본 Sol 설정이나 judge를 자동으로 바꾸지는 않습니다. 품질·실패·토큰·지연을 함께 보고 유지 이유를 적습니다. Router나 다른 provider를 오류 처리 fallback으로 쓰지 않습니다.

## 완료 확인

실제 6행, 전후 비교, judge 결과, 자신의 검토를 남깁니다. **holdout을 아직 열지 않고** candidate와 해당 설정을 보관합니다.

**다음 → [08. Hosted 로컬 실행과 Azure 배포](08-hosted.md)**
