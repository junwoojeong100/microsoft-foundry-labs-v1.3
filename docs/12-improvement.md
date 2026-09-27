# 12. 대화 평가·Optimizer·배포 품질

**완료 목표:** 전체 대화를 평가하고, 개선 후보와 실제 Hosted 버전을 근거로 비교합니다.

**시작 조건:** 07의 judge와 dev 결과, 08의 Hosted 준비 방법, 06의 IQ/계정 OpenAI Endpoint, 09의 로그 연결. 수행하는 기능별 비용을 확인합니다. **holdout은 이 장에서도 열지 않습니다.**

## Search를 만들 수 없을 때의 명시적 경로

대화 평가·Optimizer는 Search 없이 진행할 수 있습니다. 4~9절의 Hosted matrix도 **로컬 합성 문서 검색**을 명시적으로 선택해 검증할 수 있습니다. 이때 아래 세 변경을 처음부터 끝까지 유지합니다.

| 항목 | IQ 경로 | Search 미제공 경로 |
|---|---|---|
| 모든 패키징·benchmark 명령의 `--retrieval` | `iq` | `local` |
| 준비 명령의 `--name` | `matrix` | `matrix-local` |
| IQ reranker threshold 설정 | 5절에서 설정 | 생략 |

예를 들어 첫 패키지와 폴더는 다음과 같습니다.

```bash
python scripts/workshop.py --script package-hosted --kind workflow --pattern sequential --retrieval local --prompt v1 --api account-chat --protocol invocations
python scripts/selfstudy.py prepare-hosted --kind matrix --package "실제-local-v1-패키지-경로" --name matrix-local --run v1
```

이후에도 v2 패키징·dev 수집·15의 holdout에서 `--retrieval local`을 유지하고, 준비 도구가 반환한 **실제 matrix-local 서비스·폴더·버전**을 사용합니다. `wf-baseline`/`wf-candidate` label은 선택한 한 경로에서만 사용합니다. 준비 도구는 승인한 서비스 이름을 자식 프로세스에 전달하고, `bind-matrix`는 배포 후 실제 Endpoint를 읽어 저장합니다.

로컬 검색은 Search·IQ·벡터 검색의 구현/검증이 아닙니다. 원격 Hosted 실행, 모델 호출, 평가, trace와 검색 provider를 각각 구분해 기록합니다. IQ 경로로 나중에 바꾸면 기존 결과를 재사용하지 않고 새 label과 전후 쌍을 만듭니다.

## 1. 대화 평가

```bash
python scripts/workshop.py conversations plan
python scripts/workshop.py conversations collect --label conversations-first --prompt v2 --confirm-cost
python scripts/workshop.py conversations report --label conversations-first
python scripts/workshop.py conversations evaluate --label conversations-first --level turn --confirm-cost
python scripts/workshop.py conversations evaluate --label conversations-first --level conversation --confirm-cost
```

같은 실제 대화를 턴 수준과 전체 대화 수준으로 봅니다. 독립 평가 사례 사이에 Memory나 대화 상태를 공유하지 않습니다. 앞 답변과의 모순, 의도 해결, 전체 행/오류를 읽고 차이를 기록합니다.

## 2. Optimizer를 위한 모델과 데이터 직접 준비

1. Foundry agent의 **Optimize** 화면에서 지원 모델을 확인합니다.
2. 이 실습은 후보 생성용으로 **`gpt-5.5` / `2026-04-24` → `workshop-optimizer`**를 사용합니다. 지역/할당량/비용을 확인하고 02와 같은 방법으로 만듭니다.
3. 답변은 GPT-6 Luna, judge는 07의 GPT-6 Sol 배포를 유지합니다. 후보 생성 모델의 지원 목록은 별개이므로 GPT-6으로 무조건 대체하지 않습니다.
4. 같은 prefix/언어의 확장 입력이 없으면 생성합니다.

```bash
python scripts/selfstudy.py model --role optimizer
python scripts/workshop.py prepare-extensions --label extensions-ko
```

`optimizer-dev.jsonl`의 **dev 6행**과 참조 필드를 확인합니다. 이미 10에서 생성했다면 원본 hash와 prefix를 확인해 재사용합니다. holdout은 넣지 않습니다.

## 3. 지침만 최적화

1. 03과 같은 합성 정책·지침을 쓰는 **별도 소유 Prompt Agent**를 만듭니다. 이름은 `<prefix>-optimize`처럼 구분합니다.
2. **Optimize / Create optimization run → Agent**를 선택합니다.
3. 실제 target 버전·답변 모델을 고정합니다.
4. 최적화 대상은 **Instruction만**, 최대 후보 **2**를 선택합니다.
5. 준비한 dev를 업로드하고 evaluator가 요구하는 `query`/`context`/`ground_truth` 열을 확인합니다. 현재 Prompt Agent wizard는 열 이름 재매핑을 지원하지 않으므로 업로드 전에 스키마를 맞춥니다. 생성될 응답은 evaluator의 response 입력이며 참조 정답을 agent 입력에 넣지 않습니다.
6. 비용·예상 호출 범위를 확인한 뒤 한 번 제출합니다.
7. baseline과 모든 후보의 지침 차이·전체 행·평가 결과를 읽습니다.

후보가 없거나 개선이 없을 수 있습니다. 참조 문맥이 답변 자신으로 잘못 매핑된 결과는 승격 근거가 아닙니다. 가능한 경우 raw judge 입력을 내보내 직접 대조합니다.

```bash
python scripts/workshop.py --script export-evaluation --language ko --evaluation-id "실제-eval-ID" --run-id "실제-evalrun-ID" --expected-rows 6 --label optimizer-raw --require-judge-inputs
```

raw 입력을 확인할 권한/기능이 없으면 그 제한을 기록하고 자동 승격하지 않습니다. [공식 Optimizer 개념](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview).

**실제 검증에서 발견한 주의점:** 이 환경의 Prompt Optimizer + Groundedness v18 실행은 baseline 1.0에서 조기 종료됐지만, 내려받은 **6행 모두 judge의 `context`가 생성된 `response`와 같았습니다.** 이는 답변이 자기 자신을 근거로 평가된 것이므로 정상적인 grounding 검증이나 개선 증거가 아닙니다. `judge_inputs_available: true`만 확인하지 말고 내용도 원래 `context` 열과 대조하세요. 점수·원시 결과를 바꾸지 않고 이 실행은 승격하지 않았습니다.

## 4. Hosted matrix의 범위 고정

이제 **실제 배포한 버전**을 평가합니다. 07의 직접 SDK 결과를 Hosted 품질로 옮기지 않습니다.

이번 matrix의 실행 방식은 **workflow / sequential / IQ / account-chat / Invocations**입니다. 08의 기본 Responses 프로필과 다르므로 새 profile·패키지·azd 폴더를 만듭니다.

처음에는 실제 기본 모델 한 개로 시작할 수 있습니다. 두 모델을 준비했다면 다음처럼 기록합니다. JSON의 값은 실제 배포 이름입니다.

```bash
python scripts/selfstudy.py models primary=workshop-chat comparison=workshop-compare
```

이 명령은 모든 OS에서 같은 방식으로 JSON 설정을 기록합니다. 한 모델만 쓸 경우 `comparison=...`을 빼세요. 현재 기본 배포는 반드시 포함합니다.

## 5. baseline 프로필 배포

작은 합성 corpus의 검색 필터도 시작 전에 명시합니다. `0`은 IQ 검색 필터이지 평가 통과 점수가 아닙니다. baseline 이후에는 같은 조건을 유지합니다.

```bash
python scripts/selfstudy.py set WORKSHOP_IQ_RERANKER_THRESHOLD 0
```

```bash
python scripts/workshop.py --script package-hosted --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations
```

반환된 패키지 경로로 **새 빈 폴더**를 준비합니다. 00에서 수집한 project_id/location을 사용합니다.

```bash
python scripts/selfstudy.py prepare-hosted --kind matrix --package "실제-v1-패키지-경로" --name matrix --run v1
azd deploy "내-prefix-matrix" --cwd "실제-matrix-v1-절대경로"
azd ai agent show "내-prefix-matrix" --cwd "실제-matrix-v1-절대경로" --output json
```

08과 같은 방식으로 실제 런타임 ID와 역할을 확인합니다. 준비 단계가 출력한 서비스/폴더를 사용해 **실제 활성 버전과 Invocations Endpoint를 자동으로 읽어 저장**합니다.

```bash
python scripts/selfstudy.py bind-matrix --directory "실제-matrix-v1-폴더" --service "실제-matrix-서비스-이름"
python scripts/workshop.py benchmark smoke --label matrix-v1-smoke --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations --case D01 --model-key primary --confirm-cost
```

smoke가 실패하면 matrix를 실행하지 않습니다.

## 6. 모든 dev 행 수집·평가·trace

```bash
python scripts/workshop.py benchmark plan --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations
python scripts/workshop.py benchmark collect --label wf-baseline --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py benchmark evaluate --label wf-baseline --confirm-cost
python scripts/workshop.py benchmark report --label wf-baseline
python scripts/workshop.py benchmark trace-plan --label wf-baseline
python scripts/workshop.py benchmark monitor --label wf-baseline
```

수집 완료·오류 유무를 확인한 뒤 다음 명령으로 갑니다. 두 모델이면 dev **12행**이며, 역할별 호출과 검색·judge는 별도입니다. 실패한 행을 분모에서 빼지 않습니다.

`trace-plan`은 KQL 작성, `monitor`는 연결된 App Insights 실제 조회입니다. 응답의 Trace ID만 있는 것을 export 검증으로 대신하지 않습니다.

## 7. candidate는 지침만 변경

```bash
python scripts/workshop.py --script package-hosted --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations
```

**같은 agent 이름**으로, v2 패키지를 사용하는 **새 matrix-v2 폴더**를 5절과 같이 준비·배포합니다. 기존 v1 폴더를 덮어쓰지 않습니다. 새 실제 버전/Invocations Endpoint로 두 설정값을 갱신합니다.

```bash
python scripts/selfstudy.py prepare-hosted --kind matrix --package "실제-v2-패키지-경로" --name matrix --run v2
```

출력된 배포·조회 명령을 실행해 새 버전을 확인합니다.

```bash
python scripts/selfstudy.py bind-matrix --directory "실제-matrix-v2-폴더" --service "같은-matrix-서비스-이름"
python scripts/workshop.py benchmark collect --label wf-candidate --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py benchmark compare --baseline wf-baseline --candidate wf-candidate
python scripts/workshop.py benchmark evaluate --label wf-candidate --reference wf-baseline --confirm-cost
python scripts/workshop.py benchmark report --label wf-candidate
python scripts/workshop.py benchmark monitor --label wf-candidate
```

모델 map·코드·언어·데이터·검색·동시성·judge 조건을 유지합니다. 반환 근거가 달라졌다면 지침만의 개선이라고 주장하지 않습니다.

## 8. Judge calibration과 회귀

```bash
python scripts/workshop.py calibrate-judge --label judge-calibration --reference wf-candidate --confirm-cost
```

알려진 좋은/나쁜 예시 2건으로 groundedness 판단을 확인합니다. **나쁜 예시는 실패해야 하므로 native 점수 2/2 통과가 목표가 아닙니다.** 예상 판별 `correct: 2`, `gate_passed: true`를 확인합니다. 작은 calibration이 judge 전체의 정확성을 보장하지는 않습니다.

실제 dev 실패가 있으면 해당 row만 검토 기록으로 남깁니다.

```bash
python scripts/workshop.py benchmark regression --label wf-baseline --row-id "실제-실패-row-ID" --regression-label reviewed-failure --reviewer "내-실습-ID" --reason "실제 응답과 근거에 기반한 이유" --confirm-review
```

reviewer 문자열은 Entra로 검증된 업무 승인자가 아닙니다. 회귀 파일을 만들었다는 것만으로 다음 수집에 적용됐다고 하지 않습니다. 후속 dev 수집에서 `--regressions reviewed-failure`를 명시할 때만 사용됩니다.

## 9. 유지와 중지

```bash
python scripts/workshop.py benchmark stop-session --label wf-baseline
python scripts/workshop.py benchmark stop-session --label wf-candidate
```

원시 결과·실제 버전·업무/native/trace/calibration 상태를 보관합니다. **holdout은 15장에 남겨 둡니다.** 실패한 candidate를 통과한 것으로 바꾸지 않고 미완료 인수로 남길 수 있습니다.

**다음 → [13. 안전·권한·네트워크·Control Plane](13-governance.md)**
