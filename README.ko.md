# Microsoft Foundry 실습 가이드 · v1.5

[English](README.md) | **한국어**

**내 Azure 환경에서 AI 도우미를 만들고, 근거를 연결하고, 평가한 뒤 배포합니다. 필요한 코드와 데이터는 모두 이 폴더에 있습니다.**

준비물은 **Microsoft Entra ID 계정, Azure 구독, 활성 구독 Owner 역할**입니다. 시간 제한 없이 자신의 속도로 진행합니다. ZIP을 사용하면 GitHub 계정과 Git 설치 없이 시작할 수 있습니다.

**처음이라면 → [00. 실습 준비](docs/00-setup.md)**

이미 진행 중이라면 → [저장한 결과에서 재개하기](docs/checkpoints.md#다음-날-재개하기)

## 처음 시작하는 순서

1. **00장에서 파일 다운로드·도구 설치·Azure 설정을 마칩니다.** 아직 터미널 사용이 익숙하지 않아도 이 순서로 시작하면 됩니다.
2. **한국어 가이드 하나로 01~15장을 순서대로 진행합니다.** 번호가 붙은 기본 절차를 한 단계씩 실행하고, 결과를 확인한 뒤 다음으로 갑니다. `선택`, `문제가 있을 때`, `이전 환경`으로 표시한 절은 해당할 때만 읽습니다.
3. **별도 작성 파일 없이, 명령 출력과 저장된 결과를 확인합니다.** 다음 날에는 [재개 방법과 완료 기준](docs/checkpoints.md)을 확인합니다. 중간에 끝내도 [15장의 중지·정리](docs/15-capstone-cleanup.md#4-먼저-실행-중인-것을-멈추기)는 수행합니다.

02장의 Luna·Router 비교는 선택 사항입니다. 14장은 GitHub 저장소 권한이 있을 때 수행합니다. 그 밖의 기능이 지원되지 않으면 **해당 기능을 차단/미실행으로 기록**하고, 필요한 선행 기능이 준비된 단계만 이어갑니다. 전체 실습이 무료이거나 모든 구독에서 끝까지 실행된다는 보장은 없습니다.

## 무엇을 만드나요?

가상 기업 **한빛기술의 출장 규정 도우미**입니다.

> “2026년 9월 국내 출장 호텔이 1박 170,000원인데 예약해도 되나요?”

완성한 도우미는 **한도 150,000원, 예약 전 팀장 승인 필요, 근거 문서**를 함께 설명합니다. 자료가 없으면 추측하지 않고, 승인하거나 결제한 것처럼 말하지 않습니다.

Foundry는 모델 하나가 아니라 **모델·에이전트·지식·도구·평가·운영을 연결하는 Azure 플랫폼**입니다. 이 흐름을 같은 업무 사례로 직접 경험합니다.

처음부터 **GPT-6 Sol**로 시작합니다. **GPT-6 Luna 비교는 선택 사항**, judge는 대상과 기반 모델이 다른 **GPT-5.5**를 사용합니다. 새 환경의 배포 이름은 각각 `workshop-chat`, `workshop-compare`, `workshop-judge`입니다. 기존 이름이 다르더라도 모델을 몰래 바꾸거나 삭제하지 않습니다. [모델 역할과 기존 별칭 사용법](docs/model-selection.md)을 확인하세요.

![실습 구조](docs/assets/architecture.svg)

## 진행 순서

| 단계 | 할 일 | 끝나면 남는 것 |
|---|---|---|
| [00 준비](docs/00-setup.md) | 개발 환경·프로젝트·모델·권한 만들기 | 내 실습 환경 |
| [01 첫 응답](docs/01-foundry.md) | 포털과 코드에서 모델 호출 | 실제 응답 |
| [02 모델·지침](docs/02-models-prompts.md) | 지침 비교, 선택적으로 Luna·Router 비교 | 선택 이유 |
| [03 에이전트·파일](docs/03-knowledge.md) | Prompt Agent와 File Search | 저장 버전·문서 인용 |
| [04 도구](docs/04-tools.md) | 함수·MCP·Code Interpreter 실행 | 실제 도구 결과 |
| [05 워크플로](docs/05-workflows.md) | 순차·병렬·대화·중단/재개 | 작업 흐름 |
| [06 검색](docs/06-search-iq.md) | Search·IQ·Hybrid 구성 | 검색되는 내 문서 |
| [07 평가](docs/07-evaluation.md) | 같은 질문으로 전후 비교 | 품질 근거 |
| [08 배포](docs/08-hosted.md) | 로컬 확인 후 Hosted 배포 | 원격 agent |
| [09 운영](docs/09-operations.md) | Trace·Insights·비용 확인 | 요청 추적 |
| [10 공유 도구](docs/10-toolbox-skills.md) | Toolbox·Skills·OpenAPI 연결 | 재사용 가능한 도구 |
| [11 기억·위임·예약](docs/11-memory-a2a-routines.md) | Memory·A2A·Routines 실행 | 상태와 실행 기록 |
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

모든 명령은 **이 README가 있는 폴더**에서 실행합니다. **아래는 00장의 `configure`까지 마친 뒤 재개할 때 쓰는 명령**입니다. 처음이라면 먼저 00장으로 갑니다.

```bash
python scripts/workshop.py doctor
python scripts/selfstudy.py values
```

첫 명령은 로컬 준비 확인, 둘째는 저장한 설정을 다시 보는 명령입니다. 둘 다 모델에 질문하지 않습니다. `.selfstudy/`에는 개인 설정·배포 준비 정보도 있으므로 `outputs/`와 함께 보관합니다.

## 진행 규칙

- `data/policies/`의 합성 문서 6개만 사용합니다.
- 새 서비스는 해당 장에서 필요할 때 만듭니다.
- 오류나 빈 응답을 예시 답변으로 대체하지 않습니다.
- 좋은 답변 한 건, 높은 점수 한 번으로 실습 전체가 통과했다고 보지 않습니다.
- **중간에 멈출 때도 [15의 정리](docs/15-capstone-cleanup.md)를 확인**합니다.

Owner 역할이 있어도 모델 할당량·지역·제한 제공 기능을 자동으로 사용할 수 있는 것은 아닙니다. 조직의 보호 설정을 유지합니다. 14장은 포함된 GitHub OIDC CI/CD 실습에 필요한 저장소·환경 권한만 다룹니다.

## 검증 상태와 한계

**2026-09-28 검증에서 실습 실행과 최종 품질 인수는 구분했습니다.** 새 SDK·Hosted dev 결과는 각각 6/6이지만, 관리형 Task Adherence는 6행 중 5 pass/1 fail이며 severity/판정 flag가 불일치해 **최종 인수는 보류, 새 holdout은 미실행**입니다. Optimizer도 새 전체 후보가 없어 개선·승격을 주장하지 않습니다.

[실제 검증 보고서](docs/validation-report.md)는 참고 기록이지 본인의 완료 기록이 아닙니다. 13장의 관리형 AI red teaming은 사용자 지정 8문항 진단으로 대체하지 않습니다. 리전 문서 차이와 과거 실행의 상세 이력도 보고서와 해당 장에서 확인할 수 있습니다.

<a id="포털cli-요약-영상"></a>

## North Central US 포털·CLI 요약 영상

**리포 재실행판: 각 4분 32초·31개 장면, 음성 없이 자막으로 설명합니다.** 이번 실행의 **인증된 포털 5개 장면**, 실제 CLI 녹화와 표시된 저장 증거 조회만 사용했습니다. 새 그룹 생성부터 평가·배포·중지까지 보여 주며, 관리형 판정 불일치와 최종 인수 보류도 그대로 담았습니다. 로그인·인증 정보는 편집본에서 제외했습니다.

| 한국어 | English |
|---|---|
| [![한국어 요약](docs/assets/videos/foundry-v1.5-summary-ko-poster.png)](docs/assets/videos/foundry-v1.5-summary-ko.mp4) | [![English summary](docs/assets/videos/foundry-v1.5-summary-en-poster.png)](docs/assets/videos/foundry-v1.5-summary-en.mp4) |
| [MP4 보기](docs/assets/videos/foundry-v1.5-summary-ko.mp4) · [자막](docs/assets/videos/foundry-v1.5-summary-ko.srt) | [Watch MP4](docs/assets/videos/foundry-v1.5-summary-en.mp4) · [Captions](docs/assets/videos/foundry-v1.5-summary-en.srt) |

[녹화 범위와 출처](docs/videos.md) · [실제 검증 결과와 제한](docs/validation-report.md). 현재 파일은 **새 그룹의 포털·CLI 재실행판**입니다. 이전 NC 포털판은 revision `7b7ca26`, NC CLI판은 `1d53a68`, Sweden판은 `0a8ab50`에 보존합니다. 한·영 자막이 전체 실습을 두 언어로 각각 수행했다는 뜻은 아닙니다.

**도움말:** [진행·재개·완료 기준](docs/checkpoints.md) · [문제 해결](docs/troubleshooting.md) · [기능 찾기](docs/feature-map.md) · [코드 읽기](docs/code-reading.md) · [공식 자료](docs/sources.md)
