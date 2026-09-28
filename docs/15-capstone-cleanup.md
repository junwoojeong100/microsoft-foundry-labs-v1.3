# 15. 최종 인수와 비용 자원 정리

[English](en/15-capstone-cleanup.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 조건을 충족한 후보만 최종 평가하고, 만든 자원을 중지·보관·삭제합니다.

**시작 조건:** 최종 평가는 선행 품질 기준을 충족해야 합니다. **중지·비용 확인은 이전 장을 못 끝냈어도 수행**합니다.

**실행 위치:** 터미널에서 평가·세션·소유 기록 확인, Azure 포털에서 실제 자원·비용 확인.

| 현재 상태 | 진행 순서 |
|---|---|
| 중도 종료·평가 실패·기능 차단 | **holdout을 열지 않고 [4절](#4-먼저-실행-중인-것을-멈추기) → 5~7절** |
| 후보 고정·선행 기준 충족 | 1절 → 2절의 대상 하나 → 3~7절 |
| 다음 실습을 위해 자원 보존 | [보존 모드](#보존-모드로-진행할-때)와 4·5·7절. 삭제 생략 |

최종 인수는 **정한 실습 품질 기준의 통과**입니다. 운영 배포 승인이 아닙니다. 참고 [검증 보고서](validation-report.md)는 관리형 판정 불일치로 인수 보류이며, 본인의 완료 결과를 대신하지 않습니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [보존 모드](#보존-모드로-진행할-때) | 남길 자원·만료·비용 |
| [1. 대상 고정](#1-무엇을-최종-평가할지-고정) | 최종 평가 선행 기준 |
| [2. 최종 평가](#2-hosted-최종-확인) | 선택한 대상의 새 4문항 |
| [3. 결과 해석](#3-결과-해석) | 실제 통과·실패·미완료 |
| [4. 실행 중지](#4-먼저-실행-중인-것을-멈추기) | 서버·예약·세션 중지 |
| [5. 자산 확인](#5-소유-자산-목록-대조) | 실제 자원과 소유 기록 |
| [6. 그룹 삭제 — 선택](#6-실습-전용-그룹-삭제) | 전용 자원의 삭제 확인 |
| [7. 최종 확인](#7-최종-확인) | 남은 비용과 보관 결과 |

## 보존 모드로 진행할 때

> [!CAUTION]
> **보존 모드에서는 삭제하지 않습니다.** `--confirm-delete`, Memory `forget`/`cleanup`, `azd down`, 리소스 그룹 삭제를 실행하지 않습니다.

| 대상 | 할 일 |
|---|---|
| 로컬 서버 | 종료 |
| Routine·반복 평가 | `disabled` / `paused` 확인 |
| Hosted 세션 | 필요 없는 실행만 stop. 에이전트·버전·저장 볼륨 유지 |
| `.env`, `.selfstudy/`, `.build/`, `outputs/` | 승인된 개인 위치에 비공개 보관 |
| Search·파일·볼륨·로그 | 남는 비용과 다음 확인 일자 기록 |

**보존해도 자동 만료 설정은 그대로**입니다.

| 생성 조건 | 만료 |
|---|---|
| 03장의 기본 File Search | 마지막 활동 후 7일 |
| File Search `--retain` | 자동 만료 없음 |
| 11장의 Memory `--ttl-seconds 0` | 항목 자동 만료 없음 |
| 기존 Memory·관리형 세션 | 해당 자원의 원래 TTL·서비스 만료 정책 |

새 생성 명령으로 기존 만료 설정을 바꾸지 않습니다. `lifecycle=retain` 태그도 삭제 방지 잠금이나 비용 상한이 아닙니다.

## 1. 무엇을 최종 평가할지 고정

기본 대상은 12장의 Hosted 후보 `wf-candidate`입니다. 모델·코드·지침·원문·검색·API·동시성·judge·배포 버전을 고정합니다.

**다음 중 하나라도 미충족이면 holdout을 열지 않고 4절로 갑니다.**

- [ ] 후보 dev **6행**, 오류·누락·중복 0개.
- [ ] 업무 검사와 세 policy 기준 통과. policy 점수는 각 4 이상.
- [ ] 원문 참조 검사와 같은 조건의 calibration 확인.
- [ ] 필요한 실제 trace 조회 완료.
- [ ] 13장의 관리형 실행 전체 행·평가 버전·점수 방향을 검토했고, 판정 불일치가 없음.
- [ ] 실패를 보고 기준을 낮추거나 원시 결과를 수정하지 않음.

관리형 Task Adherence의 제한된 범위와 Prohibited Actions의 알려진 한계도 남깁니다. 자체 `policy-lab` 결과로 관리형 검증을 대신하지 않습니다.

Hosted를 수행하지 못했다면 07장의 **SDK candidate**를 별도 최종 대상으로 선택할 수 있습니다. 이때도 해당 대상의 선행 품질 기준과 13장의 검증을 확인하며, Hosted 인수라고 표현하지 않습니다.

**holdout은 선택한 대상 하나에만 사용합니다.** 이미 본 문항을 다른 배포의 새로운 시험으로 다시 사용하지 않습니다. 재실행은 알려진 사례의 회귀 확인입니다.

## 2. Hosted 최종 확인

> [!IMPORTANT]
> `--unlock-holdout`은 잠금 해제 옵션입니다. **1절의 미완료 기준을 면제하지 않습니다.**

12장에서 local을 선택했다면 아래 수집의 `--retrieval iq`를 `local`로 바꾸고 같은 고정 버전을 사용합니다.

**1. 고정한 후보의 4문항 수집**

```bash
python scripts/workshop.py benchmark collect --split holdout --label wf-final --candidate wf-candidate --unlock-holdout --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
```

**확인:** 실제 4행과 오류·누락 여부를 확인합니다. 요청 오류가 있으면 의존 평가를 멈춥니다.

**2. 저장된 응답의 policy 평가**

```bash
python scripts/workshop.py benchmark evaluate --policy --label wf-final --reference wf-baseline --confirm-cost
```

**3. 실제 trace 조회**

```bash
python scripts/workshop.py benchmark monitor --label wf-final
```

**4. 저장된 증거로 최종 기준 확인**

```bash
python scripts/workshop.py benchmark verify --policy --baseline wf-baseline --candidate wf-candidate --holdout wf-final --require-native --require-native-pass --require-traces --calibration policy-calibration-ko
```

| 필드 | 뜻 |
|---|---|
| `gate_passed` | 이 명령의 인수 기준 통과 여부 |
| `native_quality_passed` | Foundry policy 점수 통과 여부 |
| `native_quality_required: true` | 실제 점수 통과가 필수 |
| `deployment_approved: false` | 운영 배포 승인이 아님 |

`--require-native`는 Foundry policy 평가 **증거**, `--require-native-pass`는 **점수 통과**를 요구합니다. 어느 옵션도 13장의 관리형 red-team 감사를 대신하지 않습니다.

<details>
<summary>SDK 대상만 선택했다면: 위 Hosted 명령 대신 실행</summary>

07장의 `candidate`가 dev 6/6·오류 0과 고정 비교 조건을 충족해야 합니다. 아래와 Hosted 최종 평가는 **둘 다 실행하지 않습니다**.

**4문항 수집**

```bash
python scripts/workshop.py collect --split holdout --label final-holdout --prompt v2 --retrieval local --candidate candidate --unlock-holdout
```

**업무 검사**

```bash
python scripts/workshop.py evaluate --label final-holdout
```

**policy 평가**

```bash
python scripts/workshop.py cloud-evaluate --policy --label final-holdout --reference baseline --confirm-cost --timeout 900
```

**업무 인수 검사**

```bash
python scripts/workshop.py accept --candidate candidate --holdout final-holdout
```

`accept`만으로 policy 점수·참조·calibration이 검증되지는 않습니다. 4행의 실제 결과를 각각 확인합니다.

</details>

## 3. 결과 해석

실제 대상·버전·전체 행·오류·업무 검사·policy 점수를 함께 읽습니다. SDK와 Hosted, 서로 다른 조건의 점수를 섞지 않습니다.

실패나 미실행은 그대로 남깁니다. **실습 수행, 품질 통과, 운영 승인은 다른 상태**입니다.

holdout 결과를 보고 후보를 고쳤다면 새로운 최종 평가 데이터가 필요합니다. 기존 4문항 결과를 편집하거나 반복해 새로운 통과처럼 표시하지 않습니다.

## 4. 먼저 실행 중인 것을 멈추기

1. 내 로컬 서버의 터미널에서 `Ctrl+C`를 누릅니다. 프롬프트가 돌아오는지 확인합니다.
2. [11장의 Routine](11-memory-a2a-routines.md#4-실제-timer-전달을-확인한-뒤-비활성화)은 `enabled: false`, [09장의 반복 평가](09-operations.md#6-제한된-반복-평가)는 `paused`인지 확인합니다.
3. Hosted를 실행했다면 **실제로 존재하는 label의 세션만** 중지합니다.

**baseline 세션**

```bash
python scripts/workshop.py benchmark stop-session --label wf-baseline
```

**candidate 세션**

```bash
python scripts/workshop.py benchmark stop-session --label wf-candidate
```

**holdout을 실행했을 때만**

```bash
python scripts/workshop.py benchmark stop-session --label wf-final
```

만들지 않은 label은 생략합니다. smoke·수동 호출·보완 진단 세션도 [08장의 목록·중지](08-hosted.md#6-정확한-원격-버전-호출)로 확인합니다. 다른 사람의 프로세스·세션은 종료하지 않습니다.

**세션 파일은 만료 전에 보관**합니다. [파일 회수 안내](advanced/session-files.md)에서 절대 `--target-path`를 사용하고 요청·버전·hash를 대조합니다.

> [!WARNING]
> **stop은 저장 볼륨 삭제가 아닙니다.** 보존하면 비용이 남을 수 있습니다. 더 필요 없다고 결정했을 때만 해당 세션의 삭제 기능을 별도로 확인합니다.

## 5. 소유 자산 목록 대조

**00장의 `configure` 전에도 Azure 자원은 남을 수 있습니다.** 설정 파일이 없으면 아래 `status`를 생략하고 포털에서 사용한 구독·그룹을 직접 확인합니다.

**저장된 설정 — configure를 마쳤을 때만**

```bash
python scripts/selfstudy.py status
```

**소유 기록 — Python 설치를 마쳤을 때만**

```bash
python scripts/workshop.py cleanup-plan
```

두 명령은 삭제하지 않습니다. `cleanup-plan`은 **로컬 기록만** 읽으며 Azure 전체를 탐색하지 않습니다.

포털의 실제 목록과 대조합니다. 삭제를 선택한 경우에만 아래 순서를 적용합니다.

| 자산 | 확인·정리 순서 |
|---|---|
| Routine·반복 평가 | 비활성화 확인 → 내 일정 삭제 |
| Memory | 항목 확인 → 개별 삭제 → 빈 소유 저장소 삭제 |
| Toolbox·Skill | 참조하는 에이전트·Toolbox → Skill |
| A2A | 요청자 → 연결 → 위임 대상 |
| Prompt·Hosted | 내 이름·버전·세션·볼륨 확인 |
| File Search | 검색 저장소와 업로드 파일 각각 확인 |
| Search | 원래·Hybrid 인덱스, IQ 자산, 서비스 |
| 평가·Optimizer | 결과 보관 → 불필요한 데이터·임시 대상 |
| 로그 | Application Insights·Log Analytics의 그룹·보관 기간 |
| 모델·Foundry | 사용하는 대상이 더 없는지 확인 |
| 역할·관리 ID·federation | 직접 추가한 것만 확인 |

소유 기록을 먼저 지우면 정리할 대상을 찾기 어렵습니다. 결과와 ID를 보관한 뒤 정리합니다.

<details>
<summary>삭제를 선택했고 03장의 File Search 소유 기록이 있을 때만</summary>

**삭제 계획 조회**

```bash
python scripts/workshop.py file-search cleanup
```

이름·파일·저장소와 다른 에이전트의 참조를 확인합니다. 부분 생성 실패로 남은 자산도 포함합니다.

**삭제를 결정한 뒤에만**

```bash
python scripts/workshop.py file-search cleanup --confirm-delete
```

새 이름으로 만든 실험은 같은 `--name`을 지정합니다. 기록된 자산만 정리하며 포털에서 따로 만든 자산은 별도로 확인합니다.

</details>

## 6. 실습 전용 그룹 삭제

**보존 모드라면 생략합니다.** 더 사용할 계획이 없고 모든 자원이 내 실습 전용일 때만 진행합니다.

1. Azure 포털 **Resource groups → 내 실습 그룹 → Resources**를 엽니다.
2. 다른 업무·사용자 자원이 없는지 확인합니다.
3. 필요한 결과·소유 기록을 비공개로 보관합니다.
4. **Delete resource group**에서 정확한 이름을 확인하고 삭제합니다.
5. 삭제 완료 후 그룹과 자원이 실제로 사라졌는지 확인합니다.

공유 자원이 있으면 그룹 전체를 삭제하지 않습니다. **내 개별 자산만** 정리합니다.

다른 그룹의 로그·관리 ID·Search·Hosted 자원도 확인합니다. 한 그룹 삭제가 모든 비용의 종료를 보장하지 않습니다.

Soft delete·보관 정책이 남을 수 있으며 강제 purge는 기본 절차가 아닙니다.

## 7. 최종 확인

- [ ] 내 서버·예약·실행 세션을 중지했다.
- [ ] 포털에서 삭제 또는 보관 상태를 확인했다.
- [ ] 비용 분석에서 남은 과금 자원과 청구 반영 지연을 확인했다.
- [ ] 결과·오류·미실행 범위와 보존할 자원의 다음 확인 일자를 남겼다.
- [ ] `.env`·개인 설정·인증정보를 공개하지 않았다.

---

**과정 종료.** [← 14. CI/CD](14-additional-permissions.md) · [전체 과정](../README.ko.md#진행-순서) · [저장한 결과 찾기](checkpoints.md#설정과-결과를-다시-찾는-곳) · [실습 복습](next-steps.md) · [진행 지도 ↑](#chapter-map)
