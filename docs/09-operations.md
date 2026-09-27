# 09. Trace·Insights·운영

**완료 목표:** 로그 환경을 직접 만들고, 본인의 실제 요청을 Foundry에서 추적합니다.

**시작 조건:** 03의 Prompt Agent 또는 08의 Hosted. 이 장에서 Application Insights와 Log Analytics를 직접 준비합니다.

## 1. 로그 환경 생성·연결

1. Azure 포털 **Create a resource → Log Analytics workspace**에서 내 실습 구독·그룹에 새 workspace를 만듭니다.
2. **Create a resource → Application Insights**에서 같은 실습 그룹, 해당 workspace, 적절한 리전을 선택해 생성합니다.
3. 두 리소스 각각의 **JSON View → id**를 기록합니다. 다른 그룹에 자동 생성된 자원이 없는지 확인합니다.
4. Foundry **Agents → Traces → Connect**에서 방금 만든 Application Insights를 선택합니다.
5. Connect가 없으면 **Manage → Project details → Connected resources → Add connection → Application Insights**를 사용합니다.

연결만으로 조회 권한까지 부여된 것은 아닙니다. 본인의 로그 조회 권한을 확인합니다.

```bash
python scripts/selfstudy.py resource --kind insights --id "실제-Application-Insights-ARM-ID"
python scripts/selfstudy.py resource --kind logs --id "실제-Log-Analytics-ARM-ID"
python scripts/selfstudy.py roles --user-object-id "내-사용자-Object-ID"
```

필요한 범위의 **Log Analytics Reader**를 IAM에서 확인/부여합니다. 보호된 테이블을 사용하는 조직은 별도 Privileged Monitoring Data Reader가 필요할 수 있습니다. 토큰이나 connection string을 로그/환경 예제에 넣지 않습니다.

## 2. 연결 이후 새 요청 한 번

03에서 만든 **실제 이름과 버전**으로 호출합니다.

```bash
python scripts/workshop.py prompt-agent invoke --name "내-prefix-policy" --version "저장한-실제-버전" --question "2026년 9월 국내 출장 숙박비 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/09-trace-response.json
```

기존 파일 이름을 덮어쓰지 않습니다. 이미 사용했으면 새 파일명을 정합니다.

Foundry **Agents → Traces**에서 최근 시간 범위와 agent를 선택하고 응답 ID로 찾습니다. 수집에 시간이 걸릴 수 있으므로 잠시 기다린 후 새로 고칩니다.

## 3. 무엇이 보이는가

| 항목 | 해석 |
|---|---|
| Response ID | 실제 응답 식별자 |
| Trace ID | 해당 실행의 추적 식별자 |
| Span | 모델 호출·검색 등 실행의 세부 단계 |
| Token/지연/오류 | 측정된 사용량·경과 시간·실패 |
| Conversation/Session | 대화 이력과 Hosted 실행 세션. 같은 개념이 아님 |

본인 Trace ID, 연결된 Response ID, 관찰한 단계 하나를 워크북에 적습니다. 로컬 JSON 파일이 있다는 이유로 서버 측 trace를 확인했다고 하지 않습니다.

Hosted도 같은 방식으로 **연결 후의 새 요청**을 만들어 봅니다. 서버 측 trace가 내 Python 함수 내부 전체를 보여 주는 것은 아니며, 필요하면 별도 client-side OpenTelemetry 계측을 추가합니다.

## 4. Agent Insights

지원되는 경우 본인 agent의 **Insights**에서 제한된 시간 범위·기존 합성 trace를 대상으로 한 번 scan합니다.

실행 전에 사용 모델·예산·대상 agent·시간 범위를 확인하고, 반환한 finding을 원래 trace와 대조합니다. **AI가 제안한 실패 패턴이나 severity는 ground truth가 아닙니다.**

사용 가능한 trace/모델/기능이 없으면 “Insights 미실행”으로 기록합니다. 화면을 채우려고 불필요한 요청을 반복하지 않습니다. [공식 Insights 안내](https://learn.microsoft.com/azure/foundry/observability/how-to/agent-insights).

## 5. 비용을 연결해서 읽기

| 비용 | 직접 확인할 것 |
|---|---|
| 모델 | 모든 호출의 입력·출력 토큰, 배포 유형/단가 |
| Search | Basic 서비스의 상시 비용, 검색/기능 플랜 |
| File Search | 저장과 도구 과금 |
| Hosted | 실행 compute, session/volume 보관 |
| 평가·Optimizer·Insights | 추가 모델/평가 호출 |
| 로그 | 수집량과 보관 기간 |

`null` 사용량은 0이 아니라 미측정입니다. 일부 호출의 토큰만으로 실제 청구액을 확정하지 않습니다. Azure **Cost Management → Cost analysis**에서 실습 그룹을 필터링하고, 예산 알림과 보관 정책을 확인합니다.

## 6. 제한된 반복 평가

본인 agent의 **완료된 trace 평가**가 있으면 그 평가의 반복 설정을 엽니다. 먼저 종료 시각과 비용을 정하고, 작은 샘플(예: 실행당 최대 5개), 시간별 예약 등 제한된 구성을 선택합니다.

한 번의 실제 실행·표본을 확인하고 **계획한 시각에는 결과가 부족해도 일시 중지**합니다. 활성화 자체는 평가 성공이 아니며, 결과를 기다리느라 무기한 켜 두지 않습니다. 이미 발생한 비용은 중지로 없어지지 않습니다.

**완료:** 실제 trace와 측정값, Insights/반복 평가의 수행 상태, 중지/보관 계획을 기록합니다.

**다음 → [10. Toolbox·Tool Search·Skills](10-toolbox-skills.md)**
