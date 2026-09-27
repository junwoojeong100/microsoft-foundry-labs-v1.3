# 중단·재시작·거절을 직접 확인하기

05의 기본 실행을 마친 뒤에만 진행합니다. **합성 작업과 모의 결정**이며 Azure 호출이나 실제 업무 승인은 없습니다.

## 중단 후 같은 작업 재개

새 `run-id`를 사용합니다. 터미널 A:

```bash
python scripts/workshop.py --script resilience --language ko --run-id restart-check serve
```

터미널 B:

```bash
python scripts/workshop.py --script resilience --language ko --run-id restart-check start
python scripts/workshop.py --script resilience --language ko --run-id restart-check status
```

응답·게이트·출력 ID를 기록합니다. 승인 대기 상태가 된 뒤 A에서 `Ctrl+C`로 **이 서버만** 종료합니다.

A에서 같은 serve 명령을 다시 실행하고, B에서는 **start가 아닌 status**를 실행합니다.

```bash
python scripts/workshop.py --script resilience --language ko --run-id restart-check status
python scripts/workshop.py --script resilience --language ko --run-id restart-check decide --decision approve --confirm-simulated-decision
python scripts/workshop.py --script resilience --language ko --run-id restart-check wait --timeout-seconds 30
```

같은 response/gate와 원래 출력 ID가 유지되는지 확인합니다. 오래 기다려 유효 시간이 지났다면 그 실패를 기록합니다. 임의로 새 작업을 만들어 같은 재개 결과로 처리하지 않습니다.

## 승인하지 않는 흐름

별도 `run-id`로 serve → start → status를 진행하고 다음 모의 결정을 보냅니다.

```bash
python scripts/workshop.py --script resilience --language ko --run-id reject-check decide --decision reject --confirm-simulated-decision
python scripts/workshop.py --script resilience --language ko --run-id reject-check status
```

거절 이후 승인된 작업처럼 계속 진행하지 않는지 확인합니다. 이처럼 대기 중인 작업에 명시적인 결정을 주는 것이 이 예제의 steering입니다. 임의의 새 업무나 외부 결제를 지시하는 기능은 아닙니다.

## 무엇을 검증했나

checkpoint, 저장 상태, 원래 요청과 결정의 연결을 확인했습니다. 외부 시스템의 exactly-once 실행, 실제 사람의 인가, 모든 장애 상황을 검증한 것은 아닙니다.

결과를 보관하고 사용한 서버를 종료합니다. 로컬 상태를 제거하려면 먼저 해당 실행의 `cleanup --help`와 소유 run ID를 확인하세요.

[05로 돌아가기](../05-workflows.md)
