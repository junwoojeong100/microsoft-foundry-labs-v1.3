# 09. Trace·Insights·운영

[English](en/09-operations.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 로그를 연결하고 내가 보낸 요청의 실행 기록을 찾습니다.

**시작 조건:** 03장의 인라인 Prompt Agent 생성·호출 성공. File Search 에이전트와 구분합니다. Hosted만 있다면 2절의 대안을 사용합니다.

**실행 위치:** Azure·Foundry 포털에서 연결·조회, 터미널에서 설정 등록·새 요청.

> [!IMPORTANT]
> **로그 연결 전의 요청은 소급 수집되지 않습니다.** 로그 수집·보관과 추가 평가에 비용이 발생합니다. 반복 평가를 켰다면 결과가 없어도 계획한 시각에 중지합니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. 로그 연결](#1-로그-환경-생성연결) | 자원·연결·조회 권한 |
| [2. 새 요청](#2-연결-이후-새-요청-한-번) | 연결 후의 응답 ID |
| [3. Trace 확인](#3-무엇이-보이는가) | 같은 요청의 실행 단계 |
| [4. Insights](#4-agent-insights) | 분석 결과 또는 미실행 |
| [5. 비용 확인](#5-비용을-연결해서-읽기) | 토큰·실행·보관 비용 |
| [6. 반복 평가](#6-제한된-반복-평가) | 실제 평가와 `paused` |
| [완료 확인](#완료-확인) | 관찰 결과와 예약 중지 |

## 1. 로그 환경 생성·연결

이미 만들었다면 새로 생성하지 않고 같은 자원을 확인합니다.

1. Azure 포털 **Create a resource → Log Analytics workspace**에서 실습 구독·그룹, **North Central US**를 선택해 생성합니다.
2. **Create a resource → Application Insights**에서 같은 그룹·리전과 방금 만든 workspace를 선택합니다.
3. 각 리소스의 **JSON View → id**를 확인합니다.
4. Foundry **Agents → Traces → Connect**에서 해당 Application Insights를 연결합니다.
5. Connect가 없으면 **Manage → Project details → Connected resources → Add connection → Application Insights**를 사용합니다.

**Application Insights 등록**

```bash
python scripts/selfstudy.py resource --kind insights --id "실제-Application-Insights-ARM-ID"
```

**Log Analytics 등록**

```bash
python scripts/selfstudy.py resource --kind logs --id "실제-Log-Analytics-ARM-ID"
```

두 번째 명령은 실제 `customerId`를 읽어 `AZURE_LOG_ANALYTICS_WORKSPACE_ID`에 저장합니다. **workspace GUID와 ARM ID는 다른 값**입니다.

**역할 계획 조회**

```bash
python scripts/selfstudy.py roles --user-object-id "내-사용자-Object-ID"
```

| 주체 | 확인할 역할 |
|---|---|
| 내 사용자 | 해당 로그 자원의 Log Analytics Reader |
| 프로젝트 관리 ID | Insights 분석용 Monitoring Reader |
| 보호 콘텐츠를 읽는 주체 | 조직 정책에 따라 Privileged Monitoring Data Reader |

IAM에서 없는 역할만 해당 로그 자원 범위에 부여합니다. 자원 등록·연결 명령이 조회 권한까지 부여하지는 않습니다.

<details>
<summary>연결 실패 또는 13장의 ResourceId/credential 오류가 있을 때만</summary>

### 첫 CLI 연결과 native SDK의 실제 요구 조건

CLI 연결에는 [08장의 `prepare-hosted` 폴더](08-hosted.md#3-기존-프로젝트에-연결하는-독립-폴더)를 `--cwd`로 사용합니다. 해당 폴더에 실제 프로젝트 ARM 설정이 있어야 합니다. 원격 배포는 필요하지 않습니다.

이 실습의 SDK 2.6.1 telemetry 조회는 다음을 요구합니다.

| 연결 항목 | 값 |
|---|---|
| Metadata `ResourceId` | 해당 Application Insights의 전체 ARM ID |
| Metadata `ApplicationInsightsConnectionString` | 해당 리소스의 연결 문자열 |
| `APIKey` credential | 같은 telemetry 연결 문자열 |

여기의 `APIKey`는 SDK의 **telemetry 인증 형식**입니다. 모델 API key를 만들거나 모델·Search의 Entra 인증을 바꾸라는 뜻이 아닙니다.

CLI는 반복 `--metadata KEY=VALUE`, `--auth-type api-key`, `--key`를 지원합니다. 연결 문자열은 비공개로 다루고 저장소·화면 녹화·공유 로그에 남기지 않습니다. [오류별 확인](troubleshooting.md#managed-safety).

</details>

## 2. 연결 이후 새 요청 한 번

03장에서 저장한 인라인 에이전트 버전을 호출합니다.

```bash
python scripts/workshop.py prompt-agent invoke --question "2026년 9월 국내 출장 숙박비 한도와 사전 승인 조건은?" --output outputs/learner-notes-ko/09-trace-response.json
```

**확인:** 결과 파일의 새 응답 ID를 확인합니다. 파일이 이미 있으면 새 출력 이름을 사용합니다.

**Hosted만 있다면:** 위 명령 대신 [08장의 정확한 버전 호출](08-hosted.md#6-정확한-원격-버전-호출)을 한 번 실행합니다. 다시 배포하지 않습니다. Trace 확인 후 그 세션을 중지합니다.

## 3. 무엇이 보이는가

1. Foundry **Agents → Traces**에서 해당 에이전트와 최근 시간 범위를 선택합니다.
2. 2절의 **응답 ID**로 요청을 찾습니다.
3. 해당 trace를 열고 실행 단계(span) 하나를 펼칩니다.

| 항목 | 뜻 |
|---|---|
| Response ID | 응답 식별자 |
| Trace ID | 실행 추적 식별자 |
| Span | 모델 호출·검색 같은 세부 단계 |
| Token / 지연 / 오류 | 측정된 사용량·소요 시간·실패 |
| Conversation / Session | 대화 이력 / Hosted 실행 단위 |

**확인:** 포털의 응답 ID가 2절 결과와 같아야 합니다. 수집 지연이면 몇 분 뒤 같은 요청을 다시 조회합니다. 불필요하게 모델을 재호출하지 않습니다.

Trace는 함수 내부 전체를 자동으로 기록하지 않습니다. 로컬 JSON만 있거나 Trace ID만 표시된 상태도 실제 로그 조회와 다릅니다.

## 4. Agent Insights

1. 지원되는 에이전트의 **Insights**를 엽니다.
2. 대상·시간 범위·사용 모델·비용을 확인합니다.
3. 기존 합성 trace로 한 번 분석합니다.
4. 제안된 문제(finding)를 **원래 trace와 대조**합니다.

AI의 제안은 정답이 아닙니다. 기능·모델·trace가 없으면 미실행으로 남깁니다. [공식 Insights 안내](https://learn.microsoft.com/azure/foundry/observability/how-to/agent-insights).

## 5. 비용을 연결해서 읽기

Azure **Cost Management → Cost analysis**에서 실습 그룹으로 필터링합니다.

| 비용 | 확인할 대상 |
|---|---|
| 모델 | 입력·출력·reasoning 토큰과 배포 단가 |
| 검색·파일 | Search Basic, 기능 요금제, File Search 저장·호출 |
| Hosted | 실행 세션과 저장 볼륨 |
| 추가 분석 | 평가·Optimizer·Insights |
| 로그 | 수집량과 보관 기간 |

`null`은 미측정이며 0원이 아닙니다. 출력 상한 `32768`도 실제 사용량이나 총예산이 아닙니다. 청구 반영 지연을 고려하고 예산 알림·보관 기간을 확인합니다.

## 6. 제한된 반복 평가

**제공 기능과 비용을 확인한 경우에만** 진행합니다. 먼저 종료 시각을 정합니다.

완료된 trace 평가가 있다면 그 평가의 반복 설정에서 작은 표본(예: 최대 5개)과 시간별 예약을 선택합니다. 없다면 다음 Continuous 방식의 제공 여부를 확인합니다.

1. **Continuous**에서 평가자 하나(예: Coherence)와 07장의 judge를 선택합니다.
2. 샘플링 100%, **최대 1회/시간**으로 설정합니다.
3. Playground에서 합성 질문 하나를 보냅니다.
4. 실제 평가 run의 응답 ID를 질문 결과와 대조합니다.
5. **Pause**하고 `paused` 상태를 확인합니다.

**결과가 없어도 종료 시각에 Pause합니다.** 활성화만으로 평가 성공이 아닙니다.

실습 코드의 기본 호출은 `store=False`입니다. 저장되지 않은 응답은 연속 평가에서 조회하지 못할 수 있으므로 포털의 저장된 합성 응답을 사용합니다. Trace 존재와 평가 완료를 구분합니다.

초기화 오류나 조회 실패는 [로그 문제 해결](troubleshooting.md#observability)을 확인합니다. 다른 로그인 주체에 무작정 권한을 추가하지 않습니다.

## 완료 확인

- [ ] 연결 후의 응답 ID를 실제 trace·span과 대조했다.
- [ ] 실습 그룹의 토큰 외 비용과 보관 기간을 확인했다.
- [ ] Insights·반복 평가의 결과 또는 미실행 상태를 확인했다.
- [ ] 켠 반복 평가는 `paused`, 사용한 Hosted 세션은 중지 상태다.

---

[← 08. 배포](08-hosted.md) · [전체 과정](../README.ko.md#진행-순서) · [10. 공유 도구 →](10-toolbox-skills.md) · [진행 지도 ↑](#chapter-map)
