# 05. 워크플로와 모의 승인·중단/재개

[English](en/05-workflows.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 순차·병렬·Group Chat의 결과를 구분하고, 중단·재개와 실제 업무 승인의 차이를 경험합니다.

**시작 조건:** 04의 MAF 실행. 여러 역할만큼 모델 호출이 늘 수 있습니다.

**실행 위치:** 실습 폴더의 터미널. 5절만 터미널 A·B 두 개를 사용합니다.

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. 순차 실행](#1-순차-실행) | 분석 → 작성 → 검토 순서 |
| [2. 병렬 실행](#2-병렬-실행) | 역할별 독립 출력 |
| [3. Group Chat](#3-group-chat) | 제한된 라운드의 역할 대화 |
| [4. 배포용 출력](#4-배포할-수-있는-검증된-출력) | 업무 답변과 호출 계보 |
| [5. 중단·재개 — macOS/Linux](#5-실제-sdk의-중단재개-실험) | 같은 요청·게이트·출력 ID 유지 |
| [완료 확인](#완료-확인) | 모의 승인과 실제 인가 구분, 서버 중지 |

## 1. 순차 실행

```bash
python scripts/workshop.py workflow --pattern sequential --output outputs/learner-notes-ko/05-sequential.json
```

**확인:** 규정 분석 → 답변 작성 → 근거 검토 순서로 실행합니다. 최종 출력이 한 개라도 모델 호출이 한 번인 것은 아닙니다.

## 2. 병렬 실행

```bash
python scripts/workshop.py workflow --pattern concurrent --output outputs/learner-notes-ko/05-concurrent.json
```

**확인:** 여러 역할이 같은 질문과 근거를 동시에 봅니다. 마지막에 이어 붙인 항목은 자동 합의나 검증된 최종 답변 하나가 아닙니다.

## 3. Group Chat

```bash
python scripts/workshop.py workflow --pattern group-chat --output outputs/learner-notes-ko/05-group-chat.json
```

**확인:** 정해진 순서의 역할 대화를 읽습니다. 이 구현은 최대 3라운드와 실행 시간 상한이 있습니다. 이는 **과정의 학습 시간 제한이 아니라 과도한 실행을 막는 코드 제한**입니다. 라운드 상한 문구는 업무 답변이 아닙니다.

세 결과에서 실제 보낸 질문, 출력 개수/의미, 근거 누락, 사용량·지연을 비교합니다. 참여자를 늘린다고 무조건 좋아지는 것은 아닙니다.

## 4. 배포할 수 있는 검증된 출력

```bash
python scripts/workshop.py workflow-agent --pattern sequential --retrieval local --prompt v2 --output outputs/learner-notes-ko/05-workflow-agent.json
```

이 경로는 단순 문자열 결합이 아니라 실제 MAF 구성과 검증된 업무 답변·호출 계보를 사용합니다. `pending-human-review`는 사람이 검토할 상태이지 이미 승인했다는 뜻이 아닙니다.

## 5. 실제 SDK의 중단·재개 실험

**OS 확인:** 이 절은 macOS/Linux 전용입니다. Windows Python의 `fcntl` 오류는 패키지 재설치로 해결되지 않습니다. [00의 승인된 WSL/Linux 준비](00-setup.md#2-실습-파일과-개발-도구)를 사용하거나 이 절을 차단/미실행으로 기록하고 06장으로 갑니다. 1~4절의 모델 워크플로와는 별개입니다.

이 부분은 **모델·Azure 호출 없이 미리 작성한 합성 작업**으로 로컬 SDK의 모의 승인 게이트와 checkpoint를 배웁니다. 이 결과는 실제 사람의 업무 승인이나 외부 업무 실행이 아닙니다.

### SDK 확인

먼저 고정 SDK를 확인합니다.

```bash
python scripts/workshop.py --script resilience check
```

`azure-ai-agentserver-core: 2.1.0`, `azure-ai-agentserver-responses: 2.2.0b1`, `azure_requests_sent: false`를 확인합니다. 실행기는 이 보조 프로세스에서만 외부 계측/Foundry 환경을 제거합니다. 현재 셸이나 `.env`는 바꾸지 않습니다.

### 터미널 A: 서버 시작

터미널 A, v1.5 루트에서 서버를 시작합니다. 이 터미널은 실행한 채 둡니다. [두 터미널 사용법](checkpoints.md#두-터미널을-사용하는-장).

```bash
python scripts/workshop.py --script resilience --language ko --run-id first-pass serve
```

### 터미널 B: 요청 시작·상태 확인

A의 서버 시작 로그를 확인한 뒤 **새 터미널 B**를 엽니다. B도 같은 폴더에서 `.venv`를 활성화한 후 실행합니다.

```bash
python scripts/workshop.py --script resilience --language ko --run-id first-pass start
python scripts/workshop.py --script resilience --language ko --run-id first-pass status
```

승인 대기 상태, 같은 response/task/gate ID, `human_authorization: not-granted`를 기록합니다. 결정하지 않았는데 스스로 진행해서는 안 됩니다.

### 터미널 B: 모의 결정·결과 확인

**모의 결정임을 이해한 뒤** 계속합니다.

```bash
python scripts/workshop.py --script resilience --language ko --run-id first-pass decide --decision approve --confirm-simulated-decision
python scripts/workshop.py --script resilience --language ko --run-id first-pass wait --timeout-seconds 30
python scripts/workshop.py --script resilience --language ko --run-id first-pass status
```

같은 요청/게이트와 출력 ID가 유지되는지 확인합니다. `simulation_approved`는 실제 업무 승인과 다릅니다. 모의 결정의 유효 시간·checkpoint 경계는 실제 SDK 제약이며 임의로 늘리지 않습니다.

### 터미널 A: 서버 종료

결과를 보관하고 A에서 `Ctrl+C`로 **내 서버만** 종료합니다. 포트 충돌이면 다른 사람 프로세스를 죽이지 말고 이 실행의 모든 명령에 동일한 다른 `--port`를 지정합니다.

재시작·취소·steering은 [같은 코드로 이어 하는 추가 실험](advanced/recovery.md)에 있습니다. 외부 예약·송금 같은 효과는 연결하지 않습니다.

## 완료 확인

- [ ] 세 워크플로의 출력·호출·근거·사용량을 비교했다.
- [ ] `pending-human-review`와 모의 결정을 실제 업무 승인으로 해석하지 않았다.
- [ ] 중단·재개의 ID 유지 또는 OS 차단 상태를 확인하고, 실행한 로컬 서버를 중지했다.

---

[← 04. 도구](04-tools.md) · [전체 과정](../README.ko.md#진행-순서) · [06. 검색 →](06-search-iq.md)
