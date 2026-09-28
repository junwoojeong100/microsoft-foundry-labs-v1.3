# Microsoft Foundry 실습 가이드 · v1.5

[English](README.md) | **한국어**

내 Azure 환경에서 **출장 규정 도우미**를 만듭니다. 근거와 도구를 연결하고, 답변을 평가한 뒤 배포하는 과정입니다. 필요한 코드와 합성 데이터는 모두 이 폴더에 있습니다.

2025년 11월 Microsoft Ignite 2025 직후에 만든 [microsoft-foundry-labs](https://github.com/junwoojeong100/microsoft-foundry-labs)의 후속 버전입니다. 이전 버전을 먼저 설치하거나 실습할 필요는 없습니다.

| 지금 필요한 것 | 바로 가기 |
|---|---|
| 처음 시작 | **[00. 실습 준비](docs/00-setup.md)** |
| 하던 실습 이어하기 | [저장한 결과에서 재개](docs/checkpoints.md#다음-날-재개하기) |
| 원하는 장 찾기 | [전체 진행 순서](#진행-순서) |
| 오류 해결 | [문제 해결](docs/troubleshooting.md) |
| 오늘 실습 끝내기 | **[실행 중지·비용 정리](docs/15-capstone-cleanup.md#4-먼저-실행-중인-것을-멈추기)** |

**준비물:** Microsoft Entra ID 계정, Azure 구독, 활성 구독 Owner 역할.

ZIP을 받았다면 GitHub 계정과 Git 설치 없이 시작할 수 있습니다. 시간 제한 없이 자신의 속도로 진행합니다.

> [!WARNING]
> **무료 실습이 아닙니다.** 모델 호출과 생성한 서비스에 비용이 발생할 수 있습니다. 중간에 멈출 때도 실행·예약·보관 비용을 확인하세요.

## 처음 시작하는 순서

1. **[00. 실습 준비](docs/00-setup.md)** — 파일 다운로드, 도구 설치, Azure 설정을 마칩니다. 터미널이 처음이어도 이 장부터 시작합니다.
2. **[01. 첫 응답](docs/01-foundry.md)부터 순서대로** — 한국어 가이드 하나를 따라 한 단계씩 실행하고 결과를 확인합니다.
3. **끝낼 때는 [15. 중지·정리](docs/15-capstone-cleanup.md#4-먼저-실행-중인-것을-멈추기)** — 마지막 장까지 못 갔어도 수행합니다. 다음 날에는 [재개 순서](docs/checkpoints.md#다음-날-재개하기)부터 확인합니다.

별도 작성·제출 파일은 없습니다. 명령 출력과 저장된 결과가 실습 기록입니다.

| 조건이 있는 단계 | 진행 방법 |
|---|---|
| 02의 Luna·Router 비교 | 비교하려는 경우에만 실행합니다. |
| 14의 GitHub CI/CD | 필요한 저장소 권한이 있을 때 실행합니다. |
| 구독에서 지원하지 않는 기능 | 차단/미실행으로 남기고, 선행 조건을 갖춘 단계만 이어갑니다. |

모든 구독에서 모든 기능을 끝까지 실행할 수 있다는 보장은 없습니다. [막힌 단계의 다음 행동](docs/checkpoints.md#막힌-단계가-있을-때)을 확인하세요.

### 한 단계 읽는 순서

**시작 조건 확인 → 진행 지도에서 이동 → 명령 하나 실행 → 결과 확인**

| 표시 | 읽는 방법 |
|---|---|
| **실행 위치** | 포털, 터미널, 편집기 중 어디에서 작업하는지 먼저 확인합니다. |
| **진행 지도** | 단계 이름을 누르면 해당 절로 이동합니다. 오른쪽에는 확인할 결과가 있습니다. |
| **명령 상자** | 상자 하나의 명령만 복사·실행합니다. 결과를 읽은 뒤 다음 상자로 이동합니다. |
| **확인** / **완료 확인** | 실제 출력·파일과 대조합니다. 명령 종료와 품질 통과는 다릅니다. |
| **선택** / 접힌 설명 | 해당 조건일 때만 펼칩니다. 기본 명령에 추가로 모두 실행하지 않습니다. |

긴 장에서 순서를 놓쳤다면 맨 아래의 **진행 지도 ↑** 링크로 돌아갑니다.

명령이 화면에서 잘려 보여도 **상자 전체를 복사**합니다. 직접 줄을 나누지 않습니다. [명령·자리표시자 읽기](docs/checkpoints.md#명령과-자리표시자-읽기).

## 무엇을 만드나요?

가상 기업 **한빛기술의 출장 규정 도우미**입니다.

> “2026년 9월 국내 출장 호텔이 1박 170,000원인데 예약해도 되나요?”

완성한 도우미는 **한도 150,000원, 예약 전 팀장 승인 필요, 근거 문서**를 함께 설명합니다. 자료가 없으면 추측하지 않고, 승인하거나 결제한 것처럼 말하지 않습니다.

Foundry는 모델 하나가 아니라 **모델·에이전트·지식·도구·평가·운영을 연결하는 Azure 플랫폼**입니다. 이 흐름을 같은 업무 사례로 직접 경험합니다.

모델은 **역할별로 구분**합니다. 처음에는 답변 모델 하나만 준비합니다.

| 역할 | 기반 모델 → 새 환경의 배포 이름 |
|---|---|
| 기본 답변 · 00장부터 | **GPT-6 Sol** → `workshop-chat` |
| 선택 비교 · 02장에서 선택한 경우만 | GPT-6 Luna → `workshop-compare` |
| 답변 채점 · 07장 | GPT-5.5 → `workshop-judge` |

judge는 답변 대상과 **다른 기반 모델·별도 배포**를 사용합니다.

기존 이름이 다르더라도 그 안의 모델을 바꾸거나 삭제하지 않습니다. [모델 역할과 기존 별칭 사용법](docs/model-selection.md)을 확인하세요.

![실습 구조](docs/assets/architecture.svg)

## 진행 순서

### 준비와 첫 응답 · 00~02

| 단계 | 할 일 | 끝나면 남는 것 |
|---|---|---|
| [00 준비](docs/00-setup.md) | 개발 환경·프로젝트·모델·권한 만들기 | 내 실습 환경 |
| [01 첫 응답](docs/01-foundry.md) | 포털과 코드에서 모델 호출 | 실제 응답 |
| [02 모델·지침](docs/02-models-prompts.md) | 지침 비교, 선택적으로 Luna·Router 비교 | 선택 이유 |

### 지식·도구와 평가 · 03~07

| 단계 | 할 일 | 끝나면 남는 것 |
|---|---|---|
| [03 에이전트·파일](docs/03-knowledge.md) | Prompt Agent와 File Search | 저장 버전·문서 인용 |
| [04 도구](docs/04-tools.md) | 함수·MCP·Code Interpreter 실행 | 실제 도구 결과 |
| [05 워크플로](docs/05-workflows.md) | 순차·병렬·대화·중단/재개 | 작업 흐름 |
| [06 검색](docs/06-search-iq.md) | Search·IQ·Hybrid 구성 | 검색되는 내 문서 |
| [07 평가](docs/07-evaluation.md) | 같은 질문으로 전후 비교 | 품질 근거 |

### 배포·운영과 확장 · 08~11

| 단계 | 할 일 | 끝나면 남는 것 |
|---|---|---|
| [08 배포](docs/08-hosted.md) | 로컬 확인 후 Hosted 배포 | 원격 agent |
| [09 운영](docs/09-operations.md) | Trace·Insights·비용 확인 | 요청 추적 |
| [10 공유 도구](docs/10-toolbox-skills.md) | Toolbox·Skills·OpenAPI 연결 | 재사용 가능한 도구 |
| [11 기억·위임·예약](docs/11-memory-a2a-routines.md) | Memory·A2A·Routines 실행 | 상태와 실행 기록 |

### 개선·검증과 마무리 · 12~15

| 단계 | 할 일 | 끝나면 남는 것 |
|---|---|---|
| [12 품질 개선](docs/12-improvement.md) | 대화 평가·Optimizer·배포 평가 | 검토한 개선 후보 |
| [13 실습 안전](docs/13-governance.md) | 관리형 AI red teaming·실습 정책·관리 ID·자산 확인 | 실제 관리형 실행 근거와 한계 |
| [14 GitHub OIDC CI/CD](docs/14-additional-permissions.md) | 포함된 ID 기반 실습 릴리스 workflow 실행 | 정확한 버전과 dev 업무 검사 |
| [15 마무리](docs/15-capstone-cleanup.md) | 최종 확인·자원 정리 | 결과물과 정리 기록 |

각 장의 **실행 → 확인 → 다음**을 따라가세요. 낯선 용어, 명령의 자리표시자, 이미 있는 결과 파일의 처리 방법은 [진행 도움말](docs/checkpoints.md)에 모았습니다.

## 세 곳만 기억하세요

| 위치 | 용도 |
|---|---|
| `.venv/` | 이 프로젝트의 Python 환경 |
| `.env` | 실제 Azure 연결 설정. 도구가 생성하며 공유하지 않음 |
| `outputs/` | 실제 답변·평가·소유 자산 기록 |

> [!IMPORTANT]
> 아래는 **00장의 `configure`를 마친 뒤 재개할 때** 쓰는 명령입니다. 처음이라면 [00. 실습 준비](docs/00-setup.md)부터 시작하세요.

모든 명령은 **이 README가 있는 폴더**에서 실행합니다.

**1. 로컬 준비 확인**

```bash
python scripts/workshop.py doctor
```

**2. 저장한 연결 설정 확인**

```bash
python scripts/selfstudy.py values
```

두 명령 모두 모델에 질문하지 않습니다. `.selfstudy/`의 개인 설정·배포 준비 정보도 `outputs/`와 함께 보관합니다.

## 진행 규칙

- `data/policies/`의 합성 문서 6개만 사용합니다.
- 새 서비스는 해당 장에서 필요할 때 만듭니다.
- 오류나 빈 응답을 예시 답변으로 대체하지 않습니다.
- 좋은 답변 한 건, 높은 점수 한 번으로 실습 전체가 통과했다고 보지 않습니다.
- **중간에 멈출 때도 [15의 정리](docs/15-capstone-cleanup.md)를 확인**합니다.

Owner 역할이 있어도 모델 할당량·지역·제한 제공 기능을 자동으로 사용할 수 있는 것은 아닙니다. 조직의 보호 설정을 유지합니다.

14장은 포함된 GitHub OIDC CI/CD 실습에 필요한 저장소·환경 권한만 다룹니다.

## 검증 상태와 한계

> [!IMPORTANT]
> **2026-09-28 검증의 최종 인수는 보류이며, 새 holdout은 미실행입니다.** 실습 실행과 최종 품질 인수를 구분합니다.

| 검증 대상 | 실제 결과 | 해석 |
|---|---|---|
| SDK·Hosted dev | 각각 6/6 | dev 결과이며 최종 인수가 아닙니다. |
| 관리형 Task Adherence | 6행 중 5 pass/1 fail | severity와 판정 flag가 불일치합니다. |
| Optimizer | 새 전체 후보 없음 | 개선·승격을 주장하지 않습니다. |

[실제 검증 보고서](docs/validation-report.md)는 참고 기록이지 본인의 완료 기록이 아닙니다. 리전 문서 차이와 과거 실행 이력도 보고서와 해당 장에 있습니다.

13장의 관리형 AI red teaming은 사용자 지정 8문항 진단으로 대체하지 않습니다.

<a id="포털cli-요약-영상"></a>

## North Central US 포털·CLI 요약 영상

**각 4분 32초 · 31개 장면 · 음성 없이 자막 제공**

새 그룹 생성부터 평가·배포·중지까지 보여 주는 리포 재실행판입니다. 관리형 판정 불일치와 최종 인수 보류도 그대로 담았습니다.

이번 실행의 **인증된 포털 5개 장면**, 실제 CLI 녹화, 표시된 저장 증거 조회만 사용했습니다. 로그인·인증 정보는 편집본에서 제외했습니다.

| 한국어 | English |
|---|---|
| [![한국어 요약](docs/assets/videos/foundry-v1.5-summary-ko-poster.png)](docs/assets/videos/foundry-v1.5-summary-ko.mp4) | [![English summary](docs/assets/videos/foundry-v1.5-summary-en-poster.png)](docs/assets/videos/foundry-v1.5-summary-en.mp4) |
| [MP4 보기](docs/assets/videos/foundry-v1.5-summary-ko.mp4) · [자막](docs/assets/videos/foundry-v1.5-summary-ko.srt) | [Watch MP4](docs/assets/videos/foundry-v1.5-summary-en.mp4) · [Captions](docs/assets/videos/foundry-v1.5-summary-en.srt) |

[녹화 범위와 출처](docs/videos.md) · [실제 검증 결과와 제한](docs/validation-report.md)

한·영 자막이 전체 실습을 두 언어로 각각 수행했다는 뜻은 아닙니다.

<details>
<summary>이전 영상의 보관 위치</summary>

현재 파일은 **새 그룹의 포털·CLI 재실행판**입니다. 이전 영상은 다음 revision에 보존합니다.

| 이전 영상 | Revision |
|---|---|
| NC 포털판 | `7b7ca26` |
| NC CLI판 | `1d53a68` |
| Sweden판 | `0a8ab50` |

</details>

**도움말:** [진행·재개·완료 기준](docs/checkpoints.md) · [문제 해결](docs/troubleshooting.md) · [기능 찾기](docs/feature-map.md) · [코드 읽기](docs/code-reading.md) · [공식 자료](docs/sources.md)
