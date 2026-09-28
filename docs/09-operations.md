# 09. Trace·Insights·운영

[English](en/09-operations.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 로그 환경을 직접 만들고, 본인의 실제 요청을 Foundry에서 추적합니다.

**시작 조건:** 기본 경로는 **03의 인라인 Prompt Agent 이름·버전과 호출 성공**입니다. File Search agent가 아니라 `prompt-agent create`로 만든 대상입니다. Hosted만 있다면 아래 2절의 대안을 사용합니다. 이 장에서 Application Insights와 Log Analytics를 직접 준비합니다.

**실행 위치:** Azure·Foundry 포털에서 연결·관찰, 터미널에서 자원 등록·새 요청.

> **중요:** 로그 연결 전의 응답은 소급 수집되지 않습니다. 반복 평가를 켰다면 결과 유무와 관계없이 계획한 시각에 **Pause**합니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. 로그 연결](#1-로그-환경-생성연결) | 실제 로그 자원·연결·조회 역할 |
| [2. 새 요청](#2-연결-이후-새-요청-한-번) | 연결 이후의 새 응답 ID |
| [3. Trace](#3-무엇이-보이는가) | 같은 요청의 trace와 세부 span |
| [4. Insights](#4-agent-insights) | 실제 finding 또는 미실행 상태 |
| [5. 비용](#5-비용을-연결해서-읽기) | 토큰 외 서비스·보관 비용 |
| [6. 반복 평가](#6-제한된-반복-평가) | 실제 평가 결과와 paused 상태 |
| [완료 확인](#완료-확인) | 관찰한 증거와 중지·보관 상태 |

로그를 미리 준비했다면 새 자원을 만들지 말고 같은 연결과 권한을 확인합니다.

## 1. 로그 환경 생성·연결

1. Azure 포털 **Create a resource → Log Analytics workspace**에서 내 실습 구독·그룹, **North Central US**에 새 workspace를 만듭니다.
2. **Create a resource → Application Insights**에서 같은 실습 그룹, 해당 workspace, **North Central US**를 선택해 생성합니다.
3. 두 리소스 각각의 **JSON View → id**를 기록합니다. 다른 그룹에 자동 생성된 자원이 없는지 확인합니다.
4. Foundry **Agents → Traces → Connect**에서 방금 만든 Application Insights를 선택합니다.
5. Connect가 없으면 **Manage → Project details → Connected resources → Add connection → Application Insights**를 사용합니다.

<details>
<summary>연결이 막히거나 13장 SDK에서 ResourceId/credential 오류가 날 때</summary>

### 첫 CLI 연결과 native SDK의 실제 요구 조건

**NC에서 확인한 첫 연결 경로는 포털 bootstrap이 아니라 실제 azd ARM 환경**이었습니다. [08의 `prepare-hosted --kind runtime`](08-hosted.md#3-기존-프로젝트에-연결하는-독립-폴더)이 만든 폴더를 `azd ai connection create`의 `--cwd`로 사용하면 실제 프로젝트 ARM ID와 Endpoint가 있습니다. 이 준비만으로 Hosted를 배포하거나 모델을 호출할 필요는 없습니다. 다른 프로젝트의 환경을 빌리지 않습니다.

첫 native red-team 시도는 App Insights 연결의 **`ResourceId` 누락으로 0행 실패**했습니다. 연결이 생성됐다는 사실만으로 SDK telemetry getter가 사용할 수 있는 것은 아닙니다. 이번 SDK 경로에는 다음 값이 필요했습니다.

| 연결 항목 | 실제로 필요한 값 |
|---|---|
| Metadata `ResourceId` | 해당 Application Insights의 전체 ARM resource ID |
| Metadata `ApplicationInsightsConnectionString` | 해당 리소스의 telemetry connection string |
| `APIKey` credential | **같은 telemetry connection string**을 담는 credential |

여기의 `APIKey`는 **설치된 SDK 2.6.1 getter가 요구하는 telemetry credential class**입니다. 모델 API key를 받거나 모델의 Entra 인증을 바꾸라는 뜻이 아닙니다. Project Managed Identity App Insights 연결은 생성 가능했지만 이 getter에서는 지원되지 않았습니다. 모델/Search 인증과 이 버전별 telemetry 예외를 구분합니다.

현재 CLI는 `--metadata KEY=VALUE`를 반복 지정하고 `--auth-type api-key`/`--key`로 이 credential을 전달할 수 있습니다. **실제 connection string은 비공개 설정으로 다루고 녹화·저장소·공유 로그에 노출하지 않습니다.** 연결 metadata/credential을 확인한 뒤 새 native 실행에서 6행을 받았으며, 실패한 0행 시도는 보존합니다.

</details>

연결만으로 조회 권한까지 부여된 것은 아닙니다. 본인의 로그 조회 권한을 확인합니다.

```bash
python scripts/selfstudy.py resource --kind insights --id "실제-Application-Insights-ARM-ID"
```

**실제 자원 ID를 로컬 설정에 등록**

```bash
python scripts/selfstudy.py resource --kind logs --id "실제-Log-Analytics-ARM-ID"
```

**필요한 역할의 계획 조회**

```bash
python scripts/selfstudy.py roles --user-object-id "내-사용자-Object-ID"
```

`resource --kind logs`는 실제 Azure 응답의 `customerId`를 읽어 **`AZURE_LOG_ANALYTICS_WORKSPACE_ID`를 자동 설정**하고 현재 프로젝트 ARM ID도 기록합니다. Workspace GUID와 리소스 ARM ID는 다릅니다. 이름으로 GUID를 추측하거나 ARM ID를 이 변수에 넣지 않습니다. 이 등록은 조회 역할을 부여하거나 새 모델 응답을 만들지 않습니다.

필요한 범위의 **Log Analytics Reader**를 IAM에서 확인/부여합니다. 보호된 테이블을 사용하는 조직은 별도 Privileged Monitoring Data Reader가 필요할 수 있습니다. 토큰이나 connection string을 로그/환경 예제에 넣지 않습니다.

**Insights 분석에는 호출 주체가 하나 더 있습니다.** 사용자뿐 아니라 프로젝트 관리 ID의 Monitoring Reader와, 보호 콘텐츠를 읽을 때 필요한 Privileged Monitoring Data Reader 범위를 확인합니다. 해당 실습 로그 자원 범위에서 필요한 역할만 확인합니다.

## 2. 연결 이후 새 요청 한 번

**Hosted만 있는 경우:** 아래 Prompt Agent 명령 대신 [08의 정확한 원격 버전 호출](08-hosted.md#6-정확한-원격-버전-호출)로 기존 Hosted 버전에 새 요청 **한 번만** 보냅니다. 다시 배포하지 않으며, 같은 응답의 trace를 확인한 뒤 그 세션을 중지합니다.

03에서 기록한 에이전트 버전으로 다시 호출합니다.

```bash
python scripts/workshop.py prompt-agent invoke --question "2026년 9월 국내 출장 숙박비 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/09-trace-response.json
```

기존 파일 이름을 덮어쓰지 않습니다. 이미 사용했으면 새 파일명을 정합니다.

**확인:** Foundry **Agents → Traces**에서 최근 시간 범위와 agent를 선택하고 응답 ID로 찾습니다. 수집에 시간이 걸릴 수 있으므로 잠시 기다린 후 새로 고칩니다.

## 3. 무엇이 보이는가

| 항목 | 해석 |
|---|---|
| Response ID | 실제 응답 식별자 |
| Trace ID | 해당 실행의 추적 식별자 |
| Span | 모델 호출·검색 등 실행의 세부 단계 |
| Token/지연/오류 | 측정된 사용량·경과 시간·실패 |
| Conversation/Session | 대화 이력과 Hosted 실행 세션. 같은 개념이 아님 |

포털의 Trace ID와 연결된 Response ID를 2절 응답과 대조하고, 실행 단계 하나를 펼쳐 확인합니다. 로컬 JSON 파일이 있다는 이유로 서버 측 trace를 확인했다고 하지 않습니다.

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

GPT-6의 **reasoning 토큰도 출력 비용과 출력 상한에 포함**됩니다. 화면의 짧은 답변 길이만으로 비용을 계산하지 않습니다. 기본 설정은 `low` / `32768`이며 실제 사용량과 별개인 상한입니다.

## 6. 제한된 반복 평가

이 절은 실제 반복 평가를 확인하는 단계입니다. **완료된 trace 평가가 없으면 다음 문단의 반복 설정은 생략하고, 아래 Continuous 방식의 제공 여부를 확인**합니다. 어느 경로든 지원되지 않거나 비용을 수락하지 않으면 미실행으로 남기며 예약을 켜 두지 않습니다.

본인 agent의 **완료된 trace 평가**가 있으면 그 평가의 반복 설정을 엽니다. 먼저 종료 시각과 비용을 정하고, 작은 샘플(예: 실행당 최대 5개), 시간별 예약 등 제한된 구성을 선택합니다.

한 번의 실제 실행·표본을 확인하고 **계획한 시각에는 결과가 부족해도 일시 중지**합니다. 활성화 자체는 평가 성공이 아니며, 결과를 기다리느라 무기한 켜 두지 않습니다. 이미 발생한 비용은 중지로 없어지지 않습니다.

실시간 방식을 시험한다면 다음 순서로 진행합니다.

1. **Continuous**, 평가자 하나(예: Coherence), 본인의 judge를 선택합니다.
2. 샘플링 100%, **최대 1회/시간**으로 작게 설정합니다.
3. 포털 Playground에서 합성 질문 하나를 보냅니다.
4. 실제 평가 run과 그 응답 ID를 대조한 뒤 **Pause**합니다.

실습 코드의 기본 호출은 `store=False`입니다. 연속 평가가 응답을 다시 조회하는 경로에서는 저장되지 않은 응답이 평가되지 않을 수 있습니다. **trace 존재만으로 평가 완료를 판단하지 않습니다.** 저장할 때도 합성 데이터만 사용합니다.

<details>
<summary>Coherence 초기화 오류가 있을 때만: 과거 버전별 결과</summary>

NC의 v1 실행은 `CoherenceEvaluator.__init__() got an unexpected keyword argument 'is_reasoning_model'`로 0행 실패했습니다. 실제 catalog의 **v13**을 확인해 새 rule/evaluation에서 같은 GPT-5.5 judge·문턱 3·1회/시간을 유지하자 원래 저장 응답 1개가 score 5/pass로 평가됐습니다. 두 rule은 모두 paused이며 v1 실패를 지우지 않았습니다. 이 오류를 재현하거나 다른 evaluator까지 일괄 v13으로 바꾸지 않습니다.

</details>

CLI·포털·MCP가 서로 다른 로그인 주체를 사용할 수 있습니다. 오류의 Object ID가 지정한 사용자와 다르면 먼저 인증 컨텍스트를 확인합니다. 모르는 MCP 주체에 새 역할을 부여해 우회하지 않습니다.

## 완료 확인

- [ ] 연결 이후의 새 응답을 실제 trace·span과 대조했다.
- [ ] 측정된 사용량과 미측정 `null`, 실제 청구액을 구분했다.
- [ ] Insights·반복 평가의 실제 수행 여부를 확인하고, 켠 예약은 paused로 두었다.

로그·보관 비용과 필요한 증거를 함께 보관합니다.

---

[← 08. 배포](08-hosted.md) · [전체 과정](../README.ko.md#진행-순서) · [10. 공유 도구 →](10-toolbox-skills.md) · [진행 지도 ↑](#chapter-map)
