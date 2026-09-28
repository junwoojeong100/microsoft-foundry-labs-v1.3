# 11. Memory·A2A·Routines

[English](en/11-memory-a2a-routines.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 기억 저장·다른 에이전트 위임·예약 실행을 각각 확인합니다.

**시작 조건:** 00장의 설정·권한, 08장의 Foundry 확장, 아래 실험별 준비.

**실행 위치:** 터미널에서 생성·호출, 편집기에서 예약 파일 작성, 포털에서 역할 확인.

| 실험 | 필요한 앞 단계 |
|---|---|
| Memory — 기억 저장 | [06장의 embedding 배포·등록](06-search-iq.md#6-embedding과-hybrid-직접-준비). Hybrid 성공은 필요 없음 |
| A2A — 다른 에이전트 위임 | [08장의 준비 폴더](08-hosted.md#3-기존-프로젝트에-연결하는-독립-폴더). 원격 배포는 필요 없음 |
| Routine — 예약 실행 | [03장의 인라인 Prompt Agent](03-knowledge.md#2-저장되는-prompt-agent), [09장의 로그·조회 권한](09-operations.md#1-로그-환경-생성연결) |

세 실험은 독립적입니다. 준비되지 않은 실험만 미실행으로 남깁니다. **예약은 성공·실패와 관계없이 마지막에 비활성화**합니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. Memory](#1-memory-실제-저장과-새-요청에서의-조회) | 저장·범위별 조회·수정 |
| [2. A2A](#2-a2a-별도-endpoint에-위임) | 실제 다른 대상에 위임 |
| [3. Routine 준비](#3-routines-비활성-상태에서-준비) | 미래 시각·입력·비활성 상태 |
| [4. 예약 확인·중지](#4-실제-timer-전달을-확인한-뒤-비활성화) | 원래 예약의 답변과 비활성화 |
| [완료 확인](#완료-확인) | 세 결과와 보존 상태 |

## 1. Memory: 실제 저장과 새 요청에서의 조회

### 새 store 계획·생성

Memory store는 기억 항목을 담는 저장소입니다. 내 접두사를 확인합니다.

```bash
python scripts/selfstudy.py status
```

**새 저장소 이름 선택** — `YOUR-PREFIX`를 내 `WORKSHOP_PREFIX`로 바꿉니다.

```bash
python scripts/selfstudy.py set WORKSHOP_MEMORY_STORE_NAME "YOUR-PREFIX-memory-retained-ko"
```

**생성 계획 확인**

```bash
python scripts/workshop.py memory plan
```

**확인:** 이름·Sol·embedding 배포와 `default_ttl_seconds: 0`을 확인합니다. TTL은 자동 만료까지의 시간이며 **0은 자동 만료 없음**입니다. 저장 비용이 계속 발생할 수 있습니다.

**새 저장소 생성**

```bash
python scripts/workshop.py memory create --ttl-seconds 0 --confirm-create
```

생성 결과의 `default_ttl_seconds: 0`, `automatic_expiration_enabled: false`를 확인합니다. 로컬 `plan`만으로 원격 생성·설정이 검증되지는 않습니다.

**`alpha` 범위에 항목 저장**

```bash
python scripts/workshop.py memory put --scope alpha --case D02 --confirm-write --confirm-cost
```

반환된 `memory_id`와 소유 기록을 보관합니다. 기존 저장소는 재생성하지 말고 저장된 ID로 조회합니다. 만료가 필요하면 **다른 새 저장소** 생성 시 `--ttl-seconds`를 1~31,536,000초로 지정합니다.

### 독립 요청에서 조회

**저장한 범위**

```bash
python scripts/workshop.py memory inspect --scope alpha
```

**저장하지 않은 범위**

```bash
python scripts/workshop.py memory inspect --scope beta
```

**새 요청에서 alpha 기억 사용**

```bash
python scripts/workshop.py memory recall --scope alpha --label memory-retained-alpha-ko --confirm-cost
```

**새 요청에서 beta 기억 사용**

```bash
python scripts/workshop.py memory recall --scope beta --label memory-retained-beta-ko --confirm-cost
```

**확인:** alpha에는 저장한 항목이 있고 beta에는 없어야 합니다. `scope`는 구분용 범위이며 실제 사용자 두 명의 접근 제어를 검증한 것은 아닙니다.

### 같은 항목 수정·보존

위에서 받은 **같은 항목의 ID**인 `memory_id`를 사용합니다.

```bash
python scripts/workshop.py memory update --scope alpha --case D01 --memory-id "실제-memory_id" --confirm-write --confirm-cost
```

**수정 확인**

```bash
python scripts/workshop.py memory inspect --scope alpha
```

같은 항목의 내용이 바뀌었는지 확인합니다. 조회가 늦어도 `put`을 반복하지 않습니다.

이 장에서는 저장소를 **보존**합니다. 삭제는 15장에서 결정합니다. 이전 저장소의 TTL은 자동 변경되지 않습니다.

`WORKSHOP_MEMORY_STORE_NAME`은 전역 설정입니다. 영어로 전환한다면 별도 `-en` 이름을 지정합니다. `--language en`만으로 저장소가 바뀌지 않습니다.

## 2. A2A: 별도 endpoint에 위임

A2A는 한 에이전트가 다른 에이전트에게 작업을 요청하는 방식입니다.

### target 생성·card 확인

**위임 대상(target) 계획**

```bash
python scripts/workshop.py a2a plan
```

**대상 생성**

```bash
python scripts/workshop.py a2a target --confirm-create
```

**대상의 접속 정보(card) 조회**

```bash
python scripts/workshop.py a2a inspect
```

**확인:** `supportedInterfaces`의 **1.0 / JSONRPC / 실제 URL**을 확인합니다.

### 연결 생성·caller 호출

대상 출력의 `target_base`와 `connection_name`을 넣습니다. `target_base`는 card 파일 URL이 아닙니다.

```bash
azd ai connection create "반환된-connection_name" --kind remote-a2a --target "반환된-target_base" --auth-type project-managed-identity --audience https://ai.azure.com --project-endpoint "실제-프로젝트-Endpoint" --cwd "실제-08-Hosted-절대경로"
```

**요청하는 에이전트(caller) 생성**

```bash
python scripts/workshop.py a2a caller --confirm-create
```

**위임 요청**

```bash
python scripts/workshop.py a2a invoke --label a2a-first --confirm-cost
```

**확인:** 실제 성공한 A2A 호출, 대상·요청자 버전, 답변 근거를 확인합니다. 로컬 참여자 두 개를 만든 것만으로 A2A 성공이 아닙니다.

<details>
<summary>이전 caller에서 no valid target URL 오류가 있을 때만</summary>

원래 실패를 보관하고 `base_url`을 포함한 새 버전을 만듭니다.

```bash
python scripts/workshop.py a2a caller --confirm-create --new-version
```

**새 label로 호출**

```bash
python scripts/workshop.py a2a invoke --label a2a-fixed --confirm-cost
```

정상 호출했다면 이 절은 실행하지 않습니다.

</details>

부분 생성 후 실패하면 기존 ID로 연결·역할부터 확인합니다. 대상을 반복 생성하거나 다른 프로토콜로 바꾸지 않습니다.

## 3. Routines: 비활성 상태에서 준비

Routine은 정해진 시각에 에이전트를 실행하는 예약입니다. **03장의 인라인 Prompt Agent 이름**을 사용합니다. 모델 배포 이름이나 File Search 이름이 아닙니다.

**로그 설정 확인·등록**

```bash
python scripts/selfstudy.py resource --kind logs --id "실제-Log-Analytics-ARM-ID"
```

09장에서 준비한 로그 읽기 역할이 있어야 합니다.

**예약 시각 생성 — 지금부터 15분 뒤 UTC**

```bash
python -c "from datetime import datetime,timedelta,UTC; print((datetime.now(UTC)+timedelta(minutes=15)).isoformat(timespec='seconds').replace('+00:00','Z'))"
```

UTC는 표준시입니다. 이 명령의 값을 그대로 사용하면 현지 시각을 직접 변환할 필요가 없습니다. 준비가 오래 걸렸다면 생성 전에 새 미래 시각을 구합니다.

### 편집기: 예약 파일 작성

새 파일 `.selfstudy/routine-static-ko.json`을 만들고 아래 내용을 저장합니다. **시각·에이전트 이름 두 자리만** 실제 값으로 바꿉니다.

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

사용자 생성 `conversation`은 넣지 않습니다. 이 무인 실행 경로에서는 `conversation_not_found`가 발생할 수 있습니다. 예약 입력은 **`action.input`에 저장**하며, 수동 `dispatch --input`으로 대신 설정하지 않습니다.

### 터미널: 비활성 상태로 생성·확인

`YOUR-PREFIX`는 내 접두사로 바꿉니다. 이미 사용한 이름·파일은 덮어쓰지 않습니다.

```bash
azd ai routine create "YOUR-PREFIX-timer-static-ko" --file .selfstudy/routine-static-ko.json --enabled=false --project-endpoint "실제-프로젝트-Endpoint" --output json
```

**저장된 설정 조회**

```bash
azd ai routine show "YOUR-PREFIX-timer-static-ko" --project-endpoint "실제-프로젝트-Endpoint" --output json
```

**확인:** 대상 에이전트, 미래 시각, 고정 입력, `enabled: false`, `conversation` 없음. 하나라도 다르면 활성화하지 않습니다.

<a id="4-한-번-전달하고-반드시-비활성화"></a>

## 4. 실제 timer 전달을 확인한 뒤 비활성화

### 활성화·예약 실행 관찰

비용·시각·입력을 확인한 뒤 활성화합니다.

```bash
azd ai routine enable "YOUR-PREFIX-timer-static-ko" --project-endpoint "실제-프로젝트-Endpoint"
```

**예약 시각 이후 실행 기록 조회**

```bash
azd ai routine run list "YOUR-PREFIX-timer-static-ko" --project-endpoint "실제-프로젝트-Endpoint" --output json
```

**확인:** 실제 `timer_delivery`의 `dispatch_id`, `response_id`, 예약·실행 시각과 `Finished`를 확인합니다. 아직 없다면 같은 목록을 제한적으로 다시 조회합니다. 수동 실행으로 예약 성공을 대신하지 않습니다.

### 반드시 비활성화

**성공·실패·관찰 중단 모두 실행합니다.**

```bash
azd ai routine disable "YOUR-PREFIX-timer-static-ko" --project-endpoint "실제-프로젝트-Endpoint"
```

**비활성화 확인**

```bash
azd ai routine show "YOUR-PREFIX-timer-static-ko" --project-endpoint "실제-프로젝트-Endpoint" --output json
```

`enabled: false`여야 합니다.

**원래 실행 기록 다시 확인**

```bash
azd ai routine run list "YOUR-PREFIX-timer-static-ko" --project-endpoint "실제-프로젝트-Endpoint" --output json
```

<details>
<summary>목록이 비어 있을 때만: SDK 기록 조회</summary>

먼저 비활성화한 뒤, 같은 예약을 조회합니다. 새 예약이나 수동 실행을 만들지 않습니다.

```bash
python scripts/routine_runs.py --name "YOUR-PREFIX-timer-static-ko" --label routine-native-history-ko
```

`outputs/routine-runs/routine-native-history-ko/runs.json`의 모든 시도를 읽습니다. `Finished`인 실제 `dispatch_id`를 아래 검사에 사용하며 실패·취소 행도 보관합니다.

</details>

### 같은 예약 응답을 telemetry로 검증

telemetry는 서버가 남긴 실행 로그입니다. 위에서 확인한 Routine 이름과 **예약 실행의 ID**인 `dispatch_id`를 넣습니다.

```bash
python scripts/workshop.py routines inspect --name "RETURNED-ROUTINE" --dispatch-id "RETURNED-DISPATCH-ID" --label routine-static-timer-readback-ko --verify-response --response-source telemetry --scheduled
```

**확인:** `scheduled_trigger_verified`, `agent_answer_verified`, `routine_enabled`를 확인합니다. 원래 응답·에이전트 버전·프로젝트·trace가 일치하고, 예약은 비활성 상태여야 합니다.

비활성화 후 `run_phase: cancelled`로 보일 수 있습니다. **원래 `Finished` 기록과 같은 응답의 완전한 로그가 있을 때만** 완료 근거로 인정합니다. 값을 고치거나 모든 취소를 성공으로 해석하지 않습니다.

<details>
<summary>별도 수동 실행 기록을 확인할 때만</summary>

### 원래 수동 응답을 telemetry에서 읽기

같은 프로젝트의 기존 수동 실행 ID를 사용합니다. 예약이 아니므로 `--scheduled`를 붙이지 않습니다.

```bash
python scripts/workshop.py routines inspect --name "원래-수동-Routine-이름" --dispatch-id "원래-수동-dispatch-ID" --label routine-manual-telemetry-ko --verify-response --response-source telemetry
```

새 추론 없이 원래 결과만 조회합니다. 수동 실행과 예약 실행의 증거를 섞지 않습니다.

</details>

## 완료 확인

- [ ] Memory의 alpha/beta 차이·항목 수정·TTL·소유 기록을 확인했다.
- [ ] A2A의 실제 위임 결과 또는 차단 상태를 확인했다.
- [ ] 예약 전달과 원래 답변을 각각 확인하고 `enabled: false`를 확인했다.
- [ ] 실행하지 못한 범위와 남겨 둔 자원의 비용을 확인했다.

---

[← 10. 공유 도구](10-toolbox-skills.md) · [전체 과정](../README.ko.md#진행-순서) · [12. 품질 개선 →](12-improvement.md) · [진행 지도 ↑](#chapter-map)
