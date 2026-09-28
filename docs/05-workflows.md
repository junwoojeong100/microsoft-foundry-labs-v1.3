# 05. 워크플로와 모의 승인·중단/재개

[English](en/05-workflows.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 세 실행 흐름을 비교하고, 모의 승인 대기와 재개를 확인합니다.

**시작 조건:** 04장의 MAF 실행 성공. 여러 역할이 모델을 호출하므로 호출 비용이 늘 수 있습니다.

**실행 위치:** 실습 폴더의 터미널과 편집기. 5절만 터미널 A·B 두 개를 사용합니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. 순차 실행](#1-순차-실행) | 분석 → 작성 → 검토 |
| [2. 병렬 실행](#2-병렬-실행) | 역할별 독립 출력 |
| [3. Group Chat](#3-group-chat) | 제한된 라운드의 역할 대화 |
| [4. 배포용 출력](#4-배포할-수-있는-검증된-출력) | 구조화된 업무 답변 |
| [5. 중단·재개 — macOS/Linux](#5-실제-sdk의-중단재개-실험) | 같은 요청의 대기·결정·완료 |
| [완료 확인](#완료-확인) | 결과 비교와 서버 중지 |

## 1. 순차 실행

```bash
python scripts/workshop.py workflow --pattern sequential --output outputs/learner-notes-ko/05-sequential.json
```

**확인:** 파일의 `pattern: sequential`과 `outputs`를 읽습니다. 규정 분석 → 답변 작성 → 근거 검토 순서입니다. 최종 출력이 하나여도 모델 호출이 한 번인 것은 아닙니다.

## 2. 병렬 실행

```bash
python scripts/workshop.py workflow --pattern concurrent --output outputs/learner-notes-ko/05-concurrent.json
```

**확인:** `pattern: concurrent`와 역할별 `outputs`를 읽습니다. 각 역할이 같은 질문과 근거를 따로 검토합니다. 출력 여러 개가 자동으로 합의한 최종 답변은 아닙니다.

## 3. Group Chat

```bash
python scripts/workshop.py workflow --pattern group-chat --output outputs/learner-notes-ko/05-group-chat.json
```

**확인:** `pattern: group-chat`과 역할 간 대화를 읽습니다. 최대 3라운드와 실행 시간 상한은 과도한 호출을 막는 제한입니다. 상한 도달 문구를 업무 답변으로 해석하지 않습니다.

세 파일에서 **출력의 차이, 금액·날짜·근거 누락**을 비교합니다. 모두 `approval_status: pending-human-review`, `external_actions_performed: false`여야 합니다. 이는 검토 대기이며 실제 승인이 아닙니다.

이 JSON에는 총 토큰·지연 집계가 없습니다. 출력 개수만으로 비용이나 속도의 우열을 판단하지 않습니다.

## 4. 배포할 수 있는 검증된 출력

```bash
python scripts/workshop.py workflow-agent --pattern sequential --retrieval local --prompt v2 --output outputs/learner-notes-ko/05-workflow-agent.json
```

**확인:** 구조화된 업무 답변과 단계별 호출 기록을 읽고 원문과 대조합니다. 이 경로는 1~3절의 문자열 출력과 다릅니다. `pending-human-review`는 여기서도 승인 완료가 아닙니다.

## 5. 실제 SDK의 중단·재개 실험

> [!NOTE]
> **macOS/Linux 전용**입니다. Windows는 [00장의 승인된 WSL/Linux 환경](00-setup.md#2-실습-파일과-개발-도구)을 사용하거나 이 절을 미실행으로 남깁니다. `fcntl` 오류는 패키지 재설치로 해결되지 않습니다.

이 절은 **모델·Azure 호출 없이** 미리 작성한 합성 작업을 실행합니다. 모의 승인 게이트는 결정을 기다리는 지점, checkpoint는 재개를 위해 저장한 상태입니다.

### SDK 확인

```bash
python scripts/workshop.py --script resilience check
```

**확인:** `azure-ai-agentserver-core: 2.1.0`, `azure-ai-agentserver-responses: 2.2.0b1`, `azure_requests_sent: false`를 확인합니다. 오류가 있으면 서버를 시작하지 않습니다.

### 터미널 A: 서버 시작

```bash
python scripts/workshop.py --script resilience --language ko --run-id first-pass serve
```

시작 오류가 없는지 확인하고 **이 터미널은 그대로 둡니다**. 프롬프트가 돌아오지 않는 것은 정상입니다.

### 터미널 B: 요청 시작·상태 확인

새 터미널 B를 열고 같은 폴더에서 `.venv`를 활성화합니다. [두 터미널 사용법](checkpoints.md#두-터미널을-사용하는-장).

```bash
python scripts/workshop.py --script resilience --language ko --run-id first-pass start
```

**상태 조회**

```bash
python scripts/workshop.py --script resilience --language ko --run-id first-pass status
```

**확인:** 승인 대기, response/task/gate ID, `human_authorization: not-granted`를 확인합니다. 결정 전에는 다음 작업으로 진행하지 않아야 합니다.

### 터미널 B: 모의 결정·결과 확인

실제 업무 승인이 아닌 **실험용 결정**을 보냅니다.

```bash
python scripts/workshop.py --script resilience --language ko --run-id first-pass decide --decision approve --confirm-simulated-decision
```

**완료 대기**

```bash
python scripts/workshop.py --script resilience --language ko --run-id first-pass wait --timeout-seconds 30
```

**같은 요청의 최종 상태 조회**

```bash
python scripts/workshop.py --script resilience --language ko --run-id first-pass status
```

**확인:** 같은 요청·게이트에서 완료됐고 출력 ID가 유지되는지 대조합니다. `simulation_approved`는 실험용 상태이며 실제 사람의 업무 승인이 아닙니다.

시간이 초과되면 같은 실행의 상태부터 조회합니다. 새 `start`로 다른 요청을 만들지 않습니다.

### 터미널 A: 서버 종료

A에서 `Ctrl+C`를 누르고 프롬프트가 돌아오는지 확인합니다. 실패하거나 중간에 멈춰도 서버는 종료합니다.

포트 충돌이면 다른 사람의 프로세스를 종료하지 않습니다. 이 실행의 모든 명령에 같은 다른 `--port`를 지정합니다. 재시작·취소 실험은 [추가 안내](advanced/recovery.md)에 있습니다.

## 완료 확인

- [ ] 세 방식의 `outputs`를 읽고 차이와 근거 누락을 비교했다.
- [ ] 검토 대기와 모의 결정을 실제 승인과 구분했다.
- [ ] 같은 요청의 재개 또는 OS 차단을 확인하고, 실행한 서버를 중지했다.

---

[← 04. 도구](04-tools.md) · [전체 과정](../README.ko.md#진행-순서) · [06. 검색 →](06-search-iq.md) · [진행 지도 ↑](#chapter-map)
