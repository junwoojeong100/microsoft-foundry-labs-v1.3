# 01. Foundry와 첫 모델 응답

[English](en/01-foundry.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 포털과 코드에서 GPT-6 Sol을 호출하고 답변을 확인합니다.

**시작 조건:** [00](00-setup.md)의 설정 완료, `doctor --cloud`에서 Sol 배포의 `Succeeded` 확인.

**실행 위치:** Foundry Playground → 실습 폴더의 터미널 → 편집기.

이 장에서는 새 자원을 만들지 않습니다. 포털과 코드의 모델 호출에는 각각 비용이 발생할 수 있습니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [용어 구분](#무엇을-왜-배우는가) | 모델·배포·에이전트의 차이 |
| [1. 포털에서 질문](#1-포털에서-한-번) | 검색 없는 첫 답변 |
| [2. 코드에서 질문](#2-같은-sol-배포를-코드에서) | 답변 파일과 응답 ID |
| [3. 실행 방식 구분](#3-세-가지-구현을-구분) | 이후 실습의 실행 위치 |
| [완료 확인](#완료-확인) | 실제 모델 호출 성공 |

## 무엇을 왜 배우는가

| 용어 | 뜻 |
|---|---|
| 모델 | 입력을 읽고 답변을 생성하는 엔진 |
| 배포 이름 | 코드가 호출할 모델의 별칭. 기본값은 `workshop-chat` |
| 에이전트 | 모델에 업무 지침과 도구를 연결한 도우미 |
| 프로젝트 | 에이전트·평가·연결을 관리하는 공간 |
| Foundry | 이 기능들을 제공하는 Azure 플랫폼 |

이번에는 **모델 호출만** 확인합니다. 회사 규정 검색과 도구 실행은 뒤에서 추가합니다.

## 1. 포털에서 한 번

1. [Foundry](https://ai.azure.com)에서 00장의 프로젝트를 선택합니다.
2. **Build → Models / Deployments → `workshop-chat` → Playground**를 엽니다. 다른 배포 이름을 설정했다면 그 이름을 선택합니다.
3. **Tools**에 Web search가 있으면 제거합니다. 새 대화를 열고 다음 질문을 보냅니다.

```text
처음 국내 출장을 가는 직원의 준비 체크리스트를 한국어 3줄로 써 주세요.
```

**확인:** 한국어 준비 목록이 나오면 호출 성공입니다. 답변 문장은 예시와 같을 필요가 없습니다. 아직 한빛기술 규정을 조회한 것은 아닙니다.

## 2. 같은 Sol 배포를 코드에서

가상 환경을 활성화한 터미널에서 실행합니다.

```bash
python scripts/workshop.py model --question "처음 국내 출장을 가는 직원의 준비 체크리스트를 한국어 3줄로 써 주세요." --output outputs/learner-notes-ko/01-sol-model.json
```

편집기에서 `outputs/learner-notes-ko/01-sol-model.json`을 엽니다.

| 필드 | 확인할 값 |
|---|---|
| `mode` | `live` |
| `text` | 비어 있지 않은 한국어 답변 |
| `response_id` | 비어 있지 않은 실제 응답 ID |
| `response_model` | 서비스가 반환한 모델 식별값 |
| `inference_api` | `project-responses` |
| `usage` | 반환된 토큰 수. `null`이면 미측정이며 무료라는 뜻이 아님 |

**배포 이름·모델 버전은 00장의 `doctor --cloud` 출력에서 확인합니다.** 이 응답 파일의 `response_model`만으로 배포 설정을 확정하지 않습니다.

| cloud 검사 필드 | 기대 값 |
|---|---|
| `deployment.name` | 내 Sol 배포 이름. 기본 `workshop-chat` |
| `deployment.model.name` / `deployment.model.version` | `gpt-6-sol` / `2026-09-22` |

`trace_id: null`, `trace_export: not-configured`는 이 단계에서 정상입니다. 로그 연결은 09장에서 진행합니다.

**막히면:** 오류나 빈 답변을 성공으로 처리하지 않습니다. 401/403은 로그인·역할, 404는 프로젝트 주소·배포 이름, 429는 할당량을 확인합니다. [문제 해결](troubleshooting.md). 재호출이 필요하면 `01-sol-model-2.json`처럼 새 파일명을 사용합니다.

### 프로젝트 API와 계정 API를 구분하기

이 명령은 프로젝트 Responses API를 사용합니다. 결과 JSON의 **`inference_api` 필드**에서 `project-responses`를 확인합니다.

02장의 선택 비교에서는 두 모델 모두 `account-responses`를 사용합니다. 서로 다른 API의 결과를 같은 조건의 비교로 섞지 않습니다.

## 3. 세 가지 구현을 구분

| 실행 방식 | 실행 위치 | 실습 |
|---|---|---|
| Prompt Agent | Foundry에 지침·도구·버전을 저장 | 03 |
| Microsoft Agent Framework(MAF) | 내 Python 코드가 흐름을 구성하고 Azure 모델을 호출 | 04~05 |
| Hosted Agent | 내 코드를 Foundry에 배포해 실행 | 08 |

로컬 코드가 동작해도 원격 배포가 성공한 것은 아닙니다.

## 완료 확인

- [ ] 포털과 코드에서 실제 답변을 받았다.
- [ ] 결과 파일의 `text`, `response_id`, `response_model`, `inference_api`를 확인했다.
- [ ] 00장의 배포 정보와 대조했고, 이번 호출에 검색·도구가 없음을 구분했다.

---

[← 00. 준비](00-setup.md) · [전체 과정](../README.ko.md#진행-순서) · [02. 모델·지침 →](02-models-prompts.md) · [진행 지도 ↑](#chapter-map)
