# 11. Memory·A2A·Routines

**완료 목표:** 기억 저장, 다른 agent 위임, 예약 실행을 각각 생성·사용·확인·정리합니다.

**시작 조건:** 00의 프로젝트 관리 ID 역할, 06의 embedding 배포, 08의 azd Foundry 확장. 새 agent/Memory/예약과 호출 비용을 본인이 확인합니다.

**현재 NC 상태:** 한·영 TTL 0 Memory의 원래 항목 재조회, 한국어 A2A 위임, 실제 timer 응답의 원본 telemetry 조회를 확인했습니다. Timer는 disabled이며 `Finished/cancelled`와 별도 `Killed/cancelled` 시도를 모두 보존합니다. CLI history가 빈 목록을 반환해도 실제 실행은 존재했으므로 아래 native history 조회를 함께 사용합니다. Sweden의 원격 자산은 그룹 삭제 후 존재한다고 가정하지 않습니다.

## 1. Memory: 실제 저장과 새 요청에서의 조회

06에서 만든 `workshop-embedding`을 확인하고, 현재 prefix 아래의 **새 보존용 store 이름**을 선택합니다. 아래 `YOUR-PREFIX`는 실제 `WORKSHOP_PREFIX`로 바꿉니다. 기존 1시간 store와 기록은 그대로 둡니다.

```bash
python scripts/selfstudy.py status
python scripts/selfstudy.py set WORKSHOP_MEMORY_STORE_NAME "YOUR-PREFIX-memory-retained-ko"
python scripts/workshop.py memory plan
```

`plan`의 실제 이름·Sol 배포·embedding 배포와 `default_ttl_seconds: 0`을 확인합니다. 이 명령은 **로컬 생성 계획**이지 기존 원격 store의 TTL을 읽거나 변경하는 명령이 아닙니다.

**새 기본 TTL은 0이며, 항목의 자동 만료가 없다는 뜻입니다.** 명시적으로 같은 선택을 전달해 생성하고 새 항목을 넣습니다.

```bash
python scripts/workshop.py memory create --ttl-seconds 0 --confirm-create
python scripts/workshop.py memory put --scope alpha --case D02 --confirm-write --confirm-cost
```

반환한 **새 store 이름, `memory_id`, 소유권 파일**을 기록합니다. 생성 readback의 `default_ttl_seconds: 0`과 `automatic_expiration_enabled: false`를 확인합니다. 이는 설정 확인이며 장기간 보관 시험을 수행했다는 뜻은 아닙니다. 저장 비용은 계속 발생할 수 있습니다.

**이전 Sweden의 TTL 0 store**는 두 언어에서 생성/recall, 별도 프로세스 조회, 빈 beta scope와 4063초 항목 조회를 확인했습니다. 이는 보관한 과거 기록이며 NC의 지속성·scope 검증이나 현재 원격 자원의 존재를 뜻하지 않습니다.

다른 **새 store**에 만료가 필요하면 `--ttl-seconds`에 1~31,536,000초(365일)를 명시할 수 있습니다. 이전 store의 TTL은 그 소유 기록을 따르며 새 기본값으로 자동 변경되지 않습니다. 같은 이름이 이미 생성되어 있다면 다시 create하지 말고 기록을 읽어 inspect/recall로 이어갑니다. 다른 새 실행에는 같은 prefix 아래의 사용하지 않은 이름을 선택하며, 원격 자산을 임의로 인수하지 않습니다.

`WORKSHOP_MEMORY_STORE_NAME`은 **언어별 자동 설정이 아닌 전역 선택값**입니다. 한국어 실행은 `<prefix>-memory-retained-ko`, 영어 실행은 `<prefix>-memory-retained-en`을 명시합니다. 언어를 바꿀 때 이 설정부터 다시 확인하며, `--language en`만으로 store가 자동 전환된다고 가정하지 않습니다.

```bash
python scripts/workshop.py memory inspect --scope alpha
python scripts/workshop.py memory inspect --scope beta
python scripts/workshop.py memory recall --scope alpha --label memory-retained-alpha-ko --confirm-cost
python scripts/workshop.py memory recall --scope beta --label memory-retained-beta-ko --confirm-cost
```

독립 명령 사이에도 alpha의 항목이 유지되고 beta에는 없는지 확인합니다. **scope는 실제 사용자 두 명의 인가 경계가 아닙니다.** 같은 운영자가 둘 다 조회할 수 있습니다.

방금 **새 보존용 store에서 받은 memory_id**로 같은 항목의 내용만 명시적으로 변경합니다. 이 작업은 TTL이나 이전 store를 변경하지 않습니다.

```bash
python scripts/workshop.py memory update --scope alpha --case D01 --memory-id "실제-memory_id" --confirm-write --confirm-cost
python scripts/workshop.py memory inspect --scope alpha
```

이 실습은 **이전 store와 새 store를 모두 보존**합니다. `memory forget`, `memory cleanup`, `--confirm-delete`를 실행하지 않고 ID·TTL·소유권 기록을 유지합니다. 예전 1시간 항목에는 원래 만료가 그대로 적용됩니다. 이전 label이나 소유 파일을 새 store의 기록으로 바꿔 쓰지 않습니다.

임시 404나 지연이 있으면 같은 항목을 제한적으로 조회하지, put을 반복해 중복 항목을 만들지 않습니다. 이 과정은 명시적인 Memory API 사용이며 자동 대화 기억 추출을 검증한 것은 아닙니다.

## 2. A2A: 별도 endpoint에 위임

```bash
python scripts/workshop.py a2a plan
python scripts/workshop.py a2a target --confirm-create
python scripts/workshop.py a2a inspect
```

본인 prefix의 target을 만들고 실제 card의 `supportedInterfaces`에서 **1.0 / JSONRPC / 정확한 URL**을 확인합니다. 로컬 참여자 두 명을 만든 것을 A2A라고 부르지 않습니다.

target 출력의 **target_base와 connection_name**을 사용합니다. card URL이 아닌 base path입니다.

```bash
azd ai connection create "반환된-connection_name" --kind remote-a2a --target "반환된-target_base" --auth-type project-managed-identity --audience https://ai.azure.com --project-endpoint "실제-프로젝트-Endpoint"
python scripts/workshop.py a2a caller --confirm-create
python scripts/workshop.py a2a invoke --label a2a-first --confirm-cost
```

caller 응답에 실제 성공한 A2A 호출이 있는지 확인합니다. 이름·버전·정확한 1.0 설정·원문 근거를 보존합니다. 지원되지 않는다고 0.3이나 다른 agent로 자동 바꾸지 않습니다.

실습 코드는 연결의 target을 검사한 뒤 **A2A tool에도 같은 `base_url`을 명시**합니다. 연결 생성이 성공했더라도 tool의 URL이 빠지면 호출 시 `no valid target URL` 오류가 날 수 있습니다. 이전 코드로 caller를 이미 만들었다면 원래 실패를 보관하고 다음처럼 **명시적인 새 버전**을 만듭니다. 이전 버전은 삭제하지 않으며, 기록되지 않은 원격 버전이 있으면 갱신을 거부합니다.

```bash
python scripts/workshop.py a2a caller --confirm-create --new-version
python scripts/workshop.py a2a invoke --label a2a-fixed --confirm-cost
```

부분 생성 후 실패했다면 기존 ID로 연결/권한을 확인합니다. target을 반복 생성하거나 ownership 파일을 고치지 않습니다. 최종 정리에서는 **caller → 연결 → target** 순서로 자신이 만든 것만 제거합니다.

## 3. Routines: 비활성 상태에서 준비

03에서 직접 호출한 본인의 **Prompt Agent 이름**을 사용합니다. 모델 배포 이름을 넣지 않습니다. 실제 대상 버전도 기록합니다.

**이 실습의 무인 Routine에는 사용자 생성 conversation을 절대 전달하지 않습니다.** 프로젝트 범위와 agent endpoint에서 만든 conversation 모두 routine actor에서 `conversation_not_found`로 실패했습니다. 기존 실패·대화·Routine은 보존하고, **conversation 없이 고정된 `action.input`을 가진 새 timer**를 사용합니다.

**새 NC의 stateless timer도 실제 예약 시각에 전달됐습니다.** 원래 response ID·agent 버전·project·trace·답변을 telemetry로 확인했습니다. 이전 Sweden의 수동/예약 응답은 별도 보관 기록이며 새 응답으로 바꾸지 않습니다.

먼저 09에서 만든 실제 로그 workspace를 등록합니다. 실제 `customerId`는 `AZURE_LOG_ANALYTICS_WORKSPACE_ID`, 현재 프로젝트 ARM ID는 `AZURE_AI_PROJECT_ID`에 연결됩니다. 이 명령은 새 workspace나 모델 응답을 만들지 않습니다.

```bash
python scripts/selfstudy.py resource --kind logs --id "실제-Log-Analytics-ARM-ID"
```

필요한 로그 읽기 역할을 확인한 뒤 직접 관찰할 수 있는 미래 UTC 시각을 선택합니다. 다음 5분은 예시이며 준비 시간이 더 필요하면 충분한 여유를 둡니다.

```bash
python -c "from datetime import datetime,timedelta,UTC; print((datetime.now(UTC)+timedelta(minutes=5)).isoformat(timespec='seconds').replace('+00:00','Z'))"
```

편집기로 **아직 없는 새 파일** `.selfstudy/routine-static-ko.json`을 만듭니다. 시각과 실제 agent 이름을 바꾸고 UTF-8 JSON으로 저장합니다. `conversation` 필드는 넣지 않습니다.

```json
{
  "enabled": false,
  "triggers": {
    "default": {
      "type": "timer",
      "at": "FUTURE-UTC-TIMESTAMP"
    }
  },
  "action": {
    "type": "invoke_agent_responses_api",
    "agent_name": "ACTUAL-KOREAN-PROMPT-AGENT-NAME",
    "input": "2026년 9월 국내 출장에서 170000원 호텔의 사전 승인 조건은?"
  }
}
```

Manifest의 action type은 CLI 별칭 `agent-response`가 아니라 **`invoke_agent_responses_api`**입니다. Create에는 `--input`이 없으므로 저장될 입력은 manifest의 `action.input`에 넣습니다. 수동 `dispatch --input`은 그 한 번의 override일 뿐 timer의 저장 입력을 설정하지 않습니다.

```bash
azd ai routine create "YOUR-PREFIX-timer-static-ko" --file .selfstudy/routine-static-ko.json --enabled=false --project-endpoint "실제-프로젝트-Endpoint" --output json
azd ai routine show "YOUR-PREFIX-timer-static-ko" --project-endpoint "실제-프로젝트-Endpoint" --output json
```

현재 prefix 아래의 새 이름, agent, 미래 시각, **`enabled: false`·고정 input·conversation 없음**을 readback에서 확인합니다. 기존 이름에 `--force`로 덮어쓰거나 이전 파일을 수정하지 않습니다.

<a id="4-한-번-전달하고-반드시-비활성화"></a>

## 4. 실제 timer 전달을 확인한 뒤 비활성화

비용·시각·입력을 검토하고 준비가 끝났을 때만 enable합니다.

```bash
azd ai routine enable "YOUR-PREFIX-timer-static-ko" --project-endpoint "실제-프로젝트-Endpoint"
azd ai routine run list "YOUR-PREFIX-timer-static-ko" --project-endpoint "실제-프로젝트-Endpoint" --output json
```

예약 시각 이후 같은 목록을 제한적으로 다시 읽고 실제 **`timer_delivery`** 실행의 `dispatch_id`, `response_id`, 예약/실행 시각과 `Finished` 상태를 기록합니다. 이 timer에 수동 dispatch를 보내 예약 성공처럼 만들지 않습니다.

**CLI 목록이 비어 있을 때:** NC에서 `azd ai routine run list`가 `value: null`을 반환했지만 SDK의 실제 history에는 실행이 있었습니다. 먼저 계획대로 disable한 뒤, 다음 읽기 전용 명령으로 실제 ID를 보관합니다. 새 timer나 수동 dispatch를 만들지 않습니다.

```bash
python scripts/routine_runs.py --name "YOUR-PREFIX-timer-static-ko" --label routine-native-history-ko
```

`outputs/routine-runs/routine-native-history-ko/runs.json`의 **모든 시도**를 읽고 `Finished`인 실제 `dispatch_id`를 다음 검사에 사용합니다. 목록 조회는 답변 검증이 아니며 `Killed`·`cancelled` 행을 지우지 않습니다. 같은 label은 덮어쓰지 않습니다.

**성공·실패·관찰 중단 어느 경우에도 disable을 따로 실행**합니다. 성공한 경우에만 정리를 실행하는 조건으로 묶지 않습니다.

```bash
azd ai routine disable "YOUR-PREFIX-timer-static-ko" --project-endpoint "실제-프로젝트-Endpoint"
azd ai routine run list "YOUR-PREFIX-timer-static-ko" --project-endpoint "실제-프로젝트-Endpoint" --output json
azd ai routine show "YOUR-PREFIX-timer-static-ko" --project-endpoint "실제-프로젝트-Endpoint" --output json
```

**이전 Sweden에서** disable 후 `phase`가 `completed`에서 `cancelled`로 바뀌고 `Finished`/원래 response ID가 남는 현상을 관찰했습니다. 새 NC에서도 원시 phase를 바꾸지 않고 실제 기록과 완전한 응답을 확인합니다.

### 같은 예약 응답을 telemetry로 검증

실제 실행에서 반환한 **Routine 이름과 `dispatch_id`**, 사용하지 않은 소문자 label을 넣습니다. 아래 `RETURNED-...` 자리와 예시 label을 본인 값으로 바꾸며, 별도 run ID나 수동 dispatch ID를 대신 넣지 않습니다.

```bash
python scripts/workshop.py routines inspect --name "RETURNED-ROUTINE" --dispatch-id "RETURNED-DISPATCH-ID" --label routine-static-timer-readback-ko --verify-response --response-source telemetry --scheduled
```

검사기는 실제 timer source·예약/실행 시각, 원래 response ID·agent/version/project/trace와 완료된 `invoke_agent` 출력을 확인합니다. 이전 Sweden의 두 verified 값과 disabled 상태는 역사적 기록입니다. **새 NC 결과**에서 `scheduled_trigger_verified`, `agent_answer_verified`, `routine_enabled`, readback 방식과 새 추론 여부를 확인합니다.

Disable 뒤의 증거는 **`run_phase: cancelled`를 그대로 보존**합니다. 이 예외는 `Finished` 상태와 같은 원래 응답의 완전한 telemetry가 확인될 때만 유효합니다. 모든 cancelled 실행이 성공인 것은 아닙니다. 수집 지연이면 같은 ID를 읽기 재시도하며, 다른 모델 호출이나 새 dispatch로 대체하지 않습니다.

### 원래 수동 응답을 telemetry에서 읽기

현재 설정한 **같은 프로젝트의 로그가 아직 있는 수동 실행만** 원래 ID로 조회합니다. 삭제된 Sweden 자원의 증거는 보관본에서 읽으며 아래 NC 명령에 과거 ID를 넣지 않습니다. 다시 조회할 때는 새 label을 사용합니다.

```bash
python scripts/workshop.py routines inspect --name "원래-수동-Routine-이름" --dispatch-id "원래-수동-dispatch-ID" --label routine-manual-telemetry-ko --verify-response --response-source telemetry
```

수동 readback에는 `--scheduled`를 붙이지 않습니다. 기존 수동 응답과 예약 응답은 서로 다른 증거이며, 모두 새 추론 없이 확인합니다. Routine은 **disabled 상태로 보존**하고 기존 실패·대화·원시 기록을 삭제하지 않습니다.

**완료 확인:** 생성·실행·readback·보존 상태를 각각 기록합니다. Timer 전달이 확인되어도 새로운 policy judge의 품질 기준까지 모두 통과한 것은 아닙니다.

**다음 → [12. 대화 평가·Optimizer·배포 품질](12-improvement.md)**
