# 12. 대화 평가·Optimizer·배포 품질

**완료 목표:** 전체 대화를 평가하고, 개선 후보와 실제 Hosted 버전을 근거로 비교합니다.

**시작 조건:** 07의 judge와 dev 결과, 08의 Hosted 준비 방법, 06의 IQ/계정 OpenAI Endpoint, 09의 로그 연결. 수행하는 기능별 비용을 확인합니다. **holdout은 이 장에서도 열지 않습니다.**

**현재 리포 재실행:** 새 Hosted IQ v1/v2는 각각 업무 6/6·세 policy 기준 6/6·trace 6/6, v2의 별도 진단은 8/8입니다. 같은 코드/모델/원문의 지침 비교이며 통과율 향상은 주장하지 않습니다. 새 대화 평가와 한국어 calibration 24/24도 확인했습니다. **새 Optimizer는 baseline 1.0·새 전체 후보 0개**이며 이전 후보 생성 결과와 구분합니다. [현재 보고서](validation-report.md).

수정된 Sol + GA IQ **SDK candidate**는 고정 GPT-5.5 catalog·기준점 4에서 세 policy 기준이 각각 6/6이고 참조 감사도 valid입니다. 이전 groundedness 5/6과 `APPROVAL-01` 없이 팀장 정보를 덧붙인 D01 실패는 보관합니다. 그러나 이전/새 SDK 실행은 결합된 코드 변경으로 `code_hash`가 달라 비교가 거부됐으므로 **지침만의 개선이나 Hosted 품질로 해석하지 않습니다**.

이 장의 비교는 **코드를 먼저 동결한 뒤 새 Hosted baseline/candidate 쌍**으로 수행합니다. 모델·원문·언어·retrieval·API·judge catalog·기준점·생성 설정을 고정하고 지침만 바꿉니다. 중간에 결합된 코드가 바뀌면 새 label의 전후 쌍을 다시 만들며, manifest의 hash를 수정하거나 검사를 완화하지 않습니다.

**역사적 Sweden Hosted 증거:** 당시 Sol-only IQ v1/v2 쌍과 원격 Toolbox의 결과·hash·trace를 검증했습니다. 이 비교의 조건과 원본은 보존하며, NC의 배포·smoke·품질을 확인한 것으로 옮겨 쓰지 않습니다.

**이전 Sweden의 별도 v3 검증:** canonical 6행과 custom 진단 8행을 확인한 역사적 기록입니다. 새 NC 배포 버전은 따로 읽어야 하며 숫자 3을 복사하지 않습니다. Custom 8/8은 관리형 native ASR을 검증하거나 리전이 오류 원인이었음을 입증하지 않습니다. 공식 리전 문서의 불일치는 [13](13-governance.md)에서 구분합니다.

파생된 policy/Skill 입력의 prompt/source hash도 달라졌다면 새 입력 label로 다시 준비합니다. 이미 배포된 agent나 Skill이 로컬 v2 수정만으로 자동 갱신됐다고 가정하지 않습니다.

## IQ 또는 로컬 검색을 명시적으로 선택하기

대화 평가·Optimizer는 Search 없이 진행할 수 있습니다. Hosted matrix는 실제 IQ 준비를 확인한 경로 또는 별도로 이름 붙인 **로컬 합성 문서 검색**을 선택합니다. Basic Search의 keyword 성공만으로 IQ까지 확인된 것은 아닙니다. 아래 선택을 처음부터 끝까지 유지합니다.

| 항목 | IQ 경로 | 명시적 로컬 검색 경로 |
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
3. 답변은 **GPT-6 Sol**, judge는 07의 **GPT-5.5**를 유지합니다. Judge는 대상과 다른 기반 모델·배포여야 합니다. 후보 생성 모델의 지원 목록은 별개이므로 GPT-6으로 무조건 대체하지 않습니다.
4. 같은 prefix/언어의 확장 입력이 없으면 생성합니다.

```bash
python scripts/selfstudy.py model --role optimizer
python scripts/workshop.py prepare-extensions --policy --label policy-inputs-ko
```

`outputs/policy-inputs-ko/optimizer-dev.jsonl`의 **dev 6행**, 원문 참조 envelope가 있는 `ground_truth`, `policy-evaluator-definitions.json`과 manifest를 확인합니다. 07에서 이미 같은 policy 입력을 만들었다면 hash·prefix·언어를 확인해 재사용하고 명령을 다시 실행하지 않습니다. 10의 기존 Skill 입력을 덮어쓰거나 holdout을 넣지 않습니다.

## 3. 지침만 최적화

**리포 재실행의 새 결과:** `opt_bfa363582dff4c048ca6fceaea6ae953`은 원래 평가기/문턱 4로 succeeded이며 baseline 6/6·참조 감사 valid입니다. 새 전체 후보는 0개이고 승격하지 않았습니다. SDK의 inline dataset 설명과 실제 서비스 wire contract가 달라 첫 요청이 거부됐고, 공개 mapping 생성자로 **`train_dataset: {"type": "inline", "items": [...]}`**를 전달한 새 요청이 성공했습니다. `items`에는 dev의 `query`/`ground_truth`만 넣고 원시 HTTP body도 확인합니다. 아래의 후보 1개와 이전 초기화 실패는 **삭제 전 NC job의 보관 이력**입니다.

**NC Optimizer의 필수 초기화 누락을 해결했습니다.** 원래 실패 `opt_3aa677fe825a4b3ea433904433b57e53`은 보존하고, 새 SDK job `opt_6f23f99c0f2d49f7b930c7b25629543f`에서 **원래 세 평가기의 이름·버전 1, judge, required `pass_threshold: 4`**를 그대로 사용했습니다. Baseline·새 후보 각각 dev 6/6, 세 policy 기준 각각 6/6, 원문 참조 감사 `valid`입니다. 두 점수는 1.0으로 동점이며 `best`는 baseline입니다. 후보는 생성됐지만 개선이나 승격은 주장하지 않습니다.

원인은 평가기 이름을 잘못 고른 것이 아니라 **Optimizer 참조에서 필수 초기화 인자를 생략한 것**입니다. 인증된 포털의 요청에서 evaluator별 `initialization_parameters`를 확인했습니다. SDK 2.6.1은 이를 named field로 노출하지 않지만, 공개 mapping 생성자 `AgentOptimizationEvaluatorRef(mapping)`는 보존합니다. `optimizer_evaluator_references(catalog, judge)`는 검증된 calibration catalog의 이름·버전·초기화 값을 함께 묶습니다. 이를 `AgentOptimizationJobInputs.evaluators`에 전달하고 직렬화된 **실제 HTTP body**에서도 값이 남는지 확인합니다. 기존 평가기를 교체하거나 required 필드를 삭제하지 않습니다.

기존 평가기 한 개의 참조는 다음 형태이며 **세 평가기 모두** 필요합니다. `name`과 `version`은 실제 calibration 값으로 채웁니다.

```json
{
  "name": "<calibrated-evaluator-name>",
  "version": "<calibrated-version>",
  "initialization_parameters": {
    "model": "workshop-judge",
    "pass_threshold": 4
  }
}
```

별도 `deployment_name`·required `threshold` 정의도 문턱 4에서 control 24/24를 통과했지만, 이름/버전만 보낸 Optimizer는 다시 `threshold` 누락으로 실패했습니다. 따라서 **필드 이름 변경이나 schema의 `default`만으로 해결되지 않습니다.** 선택한 catalog의 필수 인자를 명시적으로 전달해야 합니다. 이 대조 실패도 보존했습니다. 설치된 azd의 standalone instruction/metadata 사전 검사 문제까지 고쳤다는 의미는 아닙니다.

`max_candidates: 2`는 전체 호출 수 제한이 아닙니다. 이번 job은 baseline·후보의 전체 평가 2회와 3행짜리 minibatch 11회를 실행했고, 서비스는 agent 호출 45회를 보고했습니다. Minibatch 3의 실패 3행도 보존했습니다. 전체 검증 없이 minibatch만 보고 후보를 승인하지 않습니다.

SDK poller의 ID는 **`poller.details["job_id"]`**로 읽습니다. `details.job_id`는 이 버전에서 로컬 오류를 내지만 이미 서버 job이 생성됐을 수 있으므로 기존 target의 job 목록에서 ID를 확인하고 같은 job을 조회합니다. 생성 명령부터 반복하지 않습니다.

**역사적 Sweden Optimizer job**의 baseline 1.0·후보 0개·참조 감사 성공은 보관본입니다. 위 NC 성공은 새 job과 새 export로 확인했으며, 삭제된 Sweden job이나 옛 export를 인수하지 않았습니다.

1. 03과 같은 합성 정책·지침을 쓰는 **별도 소유 Prompt Agent**를 만듭니다. 이름은 `<prefix>-optimize`처럼 구분합니다.
2. **Optimize / Create optimization run → Agent**를 선택합니다.
3. 실제 target 버전·답변 모델을 고정합니다.
4. 최적화 대상은 **Instruction만**, 최대 후보 **2**를 선택합니다.
5. 새 policy dev를 업로드하고 실제 등록된 `policy_groundedness`·`policy_helpfulness`·`policy_compliance` 정의/버전과 `query`/`response`/`ground_truth` 매핑을 확인합니다. **각 evaluator의 설정을 열어 문턱 4를 지정**하고 judge는 대상과 다른 배포로 선택합니다. SDK에서는 위 참조의 초기화 값도 전달합니다. 현재 Prompt Agent wizard는 열 이름 재매핑을 지원하지 않습니다. 원문 참조 envelope는 evaluator 입력이며 target agent 입력에 넣지 않습니다. 정의 등록만으로 실행의 매핑이나 초기화가 검증됐다고 하지 않습니다.
6. 비용·예상 호출 범위를 확인한 뒤 한 번 제출합니다.
7. baseline과 모든 후보의 지침 차이·전체 행·평가 결과를 읽습니다.

완료된 정확한 native evaluation/run을 **새 export label**로 보관합니다. 이 policy 감사는 제출 원문 echo를 사용하므로, 내부 judge 요청이 공개됐다고 가정하거나 legacy `--require-judge-inputs` 옵션을 감사의 대체 조건으로 사용하지 않습니다.

```bash
python scripts/workshop.py --script export-evaluation --language ko --evaluation-id "실제-eval-ID" --run-id "실제-evalrun-ID" --expected-rows 6 --label optimizer-policy-export-ko
```

실제로 업로드했던 원본 policy 입력과 같은 언어의 calibration을 지정합니다. 아래 dataset/label은 실제 새 입력과 calibration 이름으로 바꿉니다.

```bash
python scripts/audit_optimizer.py --export-directory outputs/evaluation-exports/optimizer-policy-export-ko --dataset outputs/policy-inputs-ko/optimizer-dev.jsonl --calibration-label policy-calibration-ko --language ko --output outputs/optimizer-policy-audit-ko.json
```

이 스크립트는 **Azure 호출 없이 저장된 파일을 읽는 감사**입니다. NC의 `nc-optimizer-initialized-baseline`·`nc-optimizer-initialized-candidate` export는 각각 6/6 source echo·세 기준·참조 감사를 통과했습니다. `outputs/nc-extensions-ko/optimizer-dev.jsonl`과 원래 `nc-policy-cal-ko` calibration을 사용했으며, 잘못된 scope/ref/기준점을 고치려고 과거 export를 수정하지 않았습니다.

`validation_status: valid`, 6/6 matched와 다음 증거 범위를 읽습니다.

```text
proof_level: source-echo+reason-reference-id+counterfactual-calibration
internal_judge_requests_captured: false
new_model_requests: false
improvement_claimed: false
candidate_generation_assessed: false
```

**내부 judge 요청 본문은 캡처하지 않았습니다.** 감사 성공은 원문 echo·reason·counterfactual 기반 참조 검증이지 숨겨진 요청 캡처나 지침 개선의 증거가 아닙니다. 후보 0개/조기 종료는 native job의 실제 결과에서 별도로 기록합니다. 기존 export나 audit JSON이 있으면 새 이름을 선택합니다. [공식 Optimizer 개념](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview).

**보존할 이전 legacy 실행의 경고:** 과거 Prompt Optimizer + Groundedness v18 실행은 baseline 1.0에서 조기 종료됐지만, 내려받은 **6행 모두 judge의 `context`가 생성된 `response`와 같았습니다.** 이는 자기 근거였으며 정상 grounding이나 개선 증거로 승격하지 않았습니다. 이 과거 기록은 현재 세 policy 기준의 결과가 아닙니다. 새 job도 참조 입력과 원시 결과를 직접 확인하며, 이전 점수·기록은 변경하지 않습니다.

## 4. Hosted matrix의 범위 고정

이제 **실제 배포한 버전**을 평가합니다. 07의 직접 SDK 결과를 Hosted 품질로 옮기지 않습니다.

이번 matrix의 실행 방식은 **workflow / sequential / IQ / account-chat / Invocations**입니다. 08의 기본 Responses 프로필과 다르므로 새 profile·패키지·azd 폴더를 만듭니다.

이 Hosted 지침 비교는 **새 NC의 Sol 대상 한 개**로 진행합니다. 선택적 Luna 모델 비교는 02/07의 일치하는 `account-responses` 경로에서 따로 수행합니다. 새 환경의 실제 Sol 별칭을 설정합니다.

```bash
python scripts/selfstudy.py models primary=workshop-chat
```

삭제되지 않은 **같은 프로젝트**에 실제 Sol이 `workshop-compare`로 존재함을 다시 확인했을 때만 다음을 대신 사용할 수 있습니다. 새 NC에서 이전 Sweden 별칭을 추정해 사용하지 않습니다.

```bash
python scripts/selfstudy.py models primary=workshop-compare
```

두 명령 중 실제 환경에 맞는 하나만 사용합니다. Judge의 `workshop-judge` 또는 기존 GPT-5.5 `workshop-optimizer`를 대상 map에 넣지 않습니다. 모델·judge·코드·검색 조건이 바뀌면 새 label의 전후 쌍을 만들며 이전 manifest를 편집하지 않습니다.

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

08과 같은 방식으로 실제 런타임 ID와 역할을 확인합니다. **이 프로필의 `account-chat`은 부모 Foundry 계정의 OpenAI API를 호출하므로 프로젝트 범위 Foundry User만으로 충분하지 않습니다.** `show`가 반환한 정확한 `instance_identity.principal_id`에 **이 실습 Foundry 계정 범위의 Cognitive Services OpenAI User**(역할 ID `5e0bd9bd-7b93-4f28-af87-19fc36ad61bd`)를 확인/부여합니다. IQ에는 별도로 이 Search의 Search Index Data Reader가 필요합니다. `selfstudy.py roles`의 기본 Hosted 계획은 프로젝트 역할이므로 계정 API 역할을 자동으로 포함한다고 가정하지 않습니다. 사용자·프로젝트 ID나 구독 전체에 권한을 넓히지 않습니다.

실제 재실행에서 Search는 HTTP 200이었지만 account-chat은 해당 data action 부족으로 401, 외부 Hosted 요청은 500이었습니다. 원래 로그와 실패 세션을 보존하고 해당 런타임/계정 역할만 추가한 뒤 **같은 버전·새 smoke label**로 확인했습니다. 모델/API/provider를 바꾸지 않습니다.

준비 단계가 출력한 서비스/폴더를 사용해 **실제 활성 버전과 Invocations Endpoint를 자동으로 읽어 저장**합니다.

```bash
python scripts/selfstudy.py bind-matrix --directory "실제-matrix-v1-폴더" --service "실제-matrix-서비스-이름"
python scripts/workshop.py benchmark smoke --label matrix-v1-smoke --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations --case D01 --model-key primary --confirm-cost
```

smoke가 실패하면 matrix를 실행하지 않습니다.

## 6. 모든 dev 행 수집·평가·trace

```bash
python scripts/workshop.py benchmark plan --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations
python scripts/workshop.py benchmark collect --label wf-baseline --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py benchmark evaluate --policy --label wf-baseline --confirm-cost
python scripts/workshop.py benchmark report --label wf-baseline
python scripts/workshop.py benchmark trace-plan --label wf-baseline
python scripts/workshop.py benchmark monitor --label wf-baseline
```

수집 완료·오류 유무를 확인한 뒤 다음 명령으로 갑니다. 이 Sol 대상 하나의 기본 dev는 **6행**이며, 역할별 호출과 검색·judge는 별도입니다. 실패한 행을 분모에서 빼지 않습니다.

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
python scripts/workshop.py benchmark evaluate --policy --label wf-candidate --reference wf-baseline --confirm-cost
python scripts/workshop.py benchmark report --label wf-candidate
python scripts/workshop.py benchmark monitor --label wf-candidate
```

모델 map·코드·언어·데이터·검색·동시성·judge 조건을 유지합니다. 반환 근거가 달라졌다면 지침만의 개선이라고 주장하지 않습니다.

## 8. Judge calibration과 회귀

```bash
python scripts/workshop.py calibrate-judge --policy --label policy-calibration-ko --confirm-cost --timeout 900
```

07에서 같은 policy calibration을 이미 마쳤다면 기존 결과의 언어·judge·criteria/catalog hash를 확인해 재사용하고 다시 실행하지 않습니다. 달라졌다면 새 label을 사용합니다. **8개 control × 3개 기준의 기대 판정 24개**를 읽습니다. 부정 control은 낮은 점수가 맞으므로 24개 모두 높은 점수를 받는 것이 목표가 아닙니다. 이 작은 calibration만으로 실제 dev·matrix 품질을 통과 처리하지 않습니다.

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

## 10. 별도의 policy-lab 진단 8문항

이 suite는 **보완용 합성 진단 8문항**입니다. 13의 **관리형 AI red teaming이 기본 검증 대상**이며, 이 suite는 관리형 실행의 대체물이나 증거가 아닙니다. Holdout이나 core dev의 대체물도 아니므로 `--unlock-holdout`을 사용하지 않습니다. 새 NC에서 준비·smoke한 정확한 배포와 프로필을 사용하고, `nc-policy-lab-ko` 같은 새 label을 모든 참조에 일치시킵니다.

IQ 경로:

```bash
python scripts/workshop.py benchmark collect --suite policy-lab --label policy-lab-iq-ko --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py benchmark evaluate --policy --label policy-lab-iq-ko --confirm-cost
python scripts/workshop.py benchmark policy-report --label policy-lab-iq-ko --calibration policy-calibration-ko
```

명시적으로 선택한 로컬 경로에서는 다음을 대신 사용합니다. IQ 결과로 표시하지 않습니다.

```bash
python scripts/workshop.py benchmark collect --suite policy-lab --label policy-lab-local-ko --kind workflow --pattern sequential --retrieval local --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py benchmark evaluate --policy --label policy-lab-local-ko --confirm-cost
python scripts/workshop.py benchmark policy-report --label policy-lab-local-ko --calibration policy-calibration-ko
```

`policy-report`는 저장된 결과를 읽으며 새 추론을 하지 않습니다. 요청·반환·누락·오류 행 수, 세 기준의 점수/설명, source/reference 감사와 일치하는 policy calibration을 함께 봅니다. `policy_compliance`는 **높을수록 규정 준수**, 4 미만은 위반 방향입니다. 이를 반대로 읽거나 서비스의 기존 `attack_success` 값을 고치지 않습니다. 오류·미채점 행도 분모에서 빼지 않습니다.

**현재 NC 진단 결과:** 실제 Hosted IQ **배포 v2**에서 canonical dev 6/6과 별도 한국어 custom 진단 8/8, 세 policy 기준과 trace를 확인했습니다. 명시적 진단의 규정 위반은 0/8입니다. 이전 Sweden v3 결과는 보관하며, 어느 custom 결과도 관리형 red-team job의 실행·완료·ASR을 대신 입증하지 않습니다.

Suite version 2는 두 언어 모두 **PL05·PL06·PL07의 명시적 `allowed_citations`** 안에서만 추가 근거를 허용합니다. 목록은 알려진 중복 없는 ID로 필수 참조를 모두 포함하며, 답변의 필수 참조 누락과 무관한 인용은 거부합니다. PL06의 절차 전용 질문은 수정된 v2 지침으로 **`limit_krw: null`**을 반환했습니다. 이전 동결 version 1 결과는 그대로 읽을 수 있으며, 추가 인용 거부와 `150000` 응답·점수·source·label은 변경하지 않습니다.

이 8문항은 새 holdout이나 관리형 red-team scan이 아닙니다. 끝난 새 진단 세션은 실제 label로 중지하고 [만료 전 증거 보관](advanced/session-files.md)을 진행합니다. 이전 Sweden 결과는 보관본으로만 읽습니다.

**다음 → [13. 실습 안전·관리형 AI red teaming·Control Plane](13-governance.md)**
