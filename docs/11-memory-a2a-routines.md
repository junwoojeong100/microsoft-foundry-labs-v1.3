# 11. Memory·A2A·Routines

**완료 목표:** 기억 저장, 다른 agent 위임, 예약 실행을 각각 생성·사용·확인·정리합니다.

**시작 조건:** 00의 프로젝트 관리 ID 역할, 06의 embedding 배포, 08의 azd Foundry 확장. 새 agent/Memory/예약과 호출 비용을 본인이 확인합니다.

## 1. Memory: 실제 저장과 새 요청에서의 조회

06에서 만든 `workshop-embedding`이 설정되어 있는지 확인합니다.

```bash
python scripts/selfstudy.py status
python scripts/workshop.py memory plan
python scripts/workshop.py memory create --confirm-create
python scripts/workshop.py memory put --scope alpha --case D02 --confirm-write --confirm-cost
```

반환한 **memory_id**를 기록합니다. 기본 TTL 3600초는 과정의 시간 제한이 아니라 서비스 데이터의 보존 설정입니다. 이 lifecycle 확인은 유효 기간 안에 진행합니다.

```bash
python scripts/workshop.py memory inspect --scope alpha
python scripts/workshop.py memory inspect --scope beta
python scripts/workshop.py memory recall --scope alpha --label memory-alpha --confirm-cost
python scripts/workshop.py memory recall --scope beta --label memory-beta --confirm-cost
```

독립 명령 사이에도 alpha의 항목이 유지되고 beta에는 없는지 확인합니다. **scope는 실제 사용자 두 명의 인가 경계가 아닙니다.** 같은 운영자가 둘 다 조회할 수 있습니다.

먼저 같은 항목의 내용을 변경합니다.

```bash
python scripts/workshop.py memory update --scope alpha --case D01 --memory-id "실제-memory_id" --confirm-write --confirm-cost
python scripts/workshop.py memory inspect --scope alpha
```

**삭제 실습을 선택한 경우에만** 다음을 수행합니다. [보존 모드](15-capstone-cleanup.md#보존-모드로-진행할-때)에서는 생략하고 소유 store와 ID를 유지합니다. 단, Memory 항목의 1시간 TTL은 그대로 적용되므로 영구 보관을 검증한 것은 아닙니다.

```bash
python scripts/workshop.py memory forget --memory-id "실제-memory_id" --confirm-delete
python scripts/workshop.py memory inspect --scope alpha
python scripts/workshop.py memory cleanup --confirm-delete
```

변경/삭제 결과와 ID를 보관합니다. 임시 404나 지연이 있으면 같은 항목을 제한적으로 조회하지, put을 반복해 중복 항목을 만들지 않습니다. 이 과정은 명시적인 Memory API 사용이며 자동 대화 기억 추출을 검증한 것은 아닙니다.

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

내일의 UTC 시각을 계산합니다.

```bash
python -c "from datetime import datetime,timedelta,UTC; print((datetime.now(UTC)+timedelta(days=1)).isoformat())"
```

출력된 시각과 실제 이름/Endpoint를 넣어 **disabled 일회성 timer**를 만듭니다.

```bash
azd ai routine create "내-prefix-timer" --trigger timer --at "방금-계산한-UTC-시각" --agent-name "내-Prompt-Agent-이름" --action agent-response --enabled=false --project-endpoint "실제-프로젝트-Endpoint" --output json
azd ai routine show "내-prefix-timer" --project-endpoint "실제-프로젝트-Endpoint" --output json
```

이름·대상·시각·`enabled: false`를 대조합니다. `--force`로 기존 것을 덮어쓰지 않습니다.

## 4. 한 번 전달하고 반드시 비활성화

enable이 성공한 경우에만 dispatch합니다.

```bash
azd ai routine enable "내-prefix-timer" --project-endpoint "실제-프로젝트-Endpoint"
azd ai routine dispatch "내-prefix-timer" --input "2026년 9월 국내 출장에서 170000원 호텔의 사전 승인 조건은?" --project-endpoint "실제-프로젝트-Endpoint" --output json
```

**dispatch가 실패해도 다음 disable은 실행합니다.** 정리 명령을 성공 조건에만 매달지 않습니다.

```bash
azd ai routine disable "내-prefix-timer" --project-endpoint "실제-프로젝트-Endpoint"
azd ai routine run list "내-prefix-timer" --project-endpoint "실제-프로젝트-Endpoint" --output json
azd ai routine show "내-prefix-timer" --project-endpoint "실제-프로젝트-Endpoint" --output json
python scripts/workshop.py routines inspect --name "내-prefix-timer" --dispatch-id "실제-dispatch-ID" --label routine-first
```

최종 disabled 상태와 실제 전달 결과를 확인합니다. **예약 설정 성공, 전달 성공, agent 답변 확인, 미래 예약 실행은 서로 다릅니다.** 답변을 조회할 수 없으면 직접 호출한 다른 답변으로 대신하지 않습니다.

답변 자체도 조회하려면 새 label로 `routines inspect ... --verify-response`를 실행할 수 있습니다. 404/권한 오류가 나면 전달 결과는 보존하되 `agent_answer_verified: false`로 남깁니다. 반복 dispatch로 다른 응답을 만들지 않습니다.

더 쓰지 않고 삭제를 선택했다면 Foundry의 Routines 목록에서 본인 routine만 삭제합니다. 보존 모드에서는 **disabled 상태로 유지**합니다. 삭제 후에도 모델·Search·기존 로그가 모두 삭제되는 것은 아닙니다.

**완료:** 세 기능의 실제 생성/조회/호출/정리와 미확인 부분을 기록합니다.

**다음 → [12. 대화 평가·Optimizer·배포 품질](12-improvement.md)**
