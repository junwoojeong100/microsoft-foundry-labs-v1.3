# Microsoft Foundry 실습 가이드 · v1.5

[English](README.md) | **한국어**

**내 Azure 환경에서 AI 도우미를 만들고, 근거를 연결하고, 평가한 뒤 배포합니다. 필요한 코드와 데이터는 모두 이 폴더에 있습니다.**

준비물은 **Microsoft Entra ID 계정, Azure 구독, 활성 구독 Owner 역할**입니다. 시간 제한 없이 자신의 속도로 진행합니다. ZIP을 사용하면 GitHub 계정과 Git 설치 없이 시작할 수 있습니다.

**처음이라면 → [00. 실습 준비](docs/00-setup.md)**

이미 진행 중이라면 → [내 진행표](worksheets/workbook.md)

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
| [13 실습 안전](docs/13-governance.md) | 실습 정책·관리 ID·소유 자산 확인 | 통제와 한계 |
| [14 GitHub OIDC CI/CD](docs/14-additional-permissions.md) | 포함된 ID 기반 실습 릴리스 workflow 실행 | 정확한 버전과 smoke/dev 근거 |
| [15 마무리](docs/15-capstone-cleanup.md) | 최종 확인·자원 정리 | 결과물과 정리 기록 |

각 장의 **실행 → 확인 → 다음**만 따라가세요. 별도 학습 경로를 고르거나 다른 저장소를 받을 필요가 없습니다.

## 세 곳만 기억하세요

| 위치 | 용도 |
|---|---|
| `.venv/` | 이 프로젝트의 Python 환경 |
| `.env` | 실제 Azure 연결 설정. 도구가 생성하며 공유하지 않음 |
| `outputs/` | 실제 답변·평가·소유 자산 기록 |

모든 명령은 **이 README가 있는 폴더**에서 실행합니다.

```bash
python scripts/workshop.py doctor
python scripts/selfstudy.py values
```

첫 명령은 로컬 준비 확인, 둘째는 설정한 값을 다시 보는 명령입니다. 설치와 Azure 준비는 00장에서 안내합니다.

## 진행 규칙

- `data/policies/`의 합성 문서 6개만 사용합니다.
- 새 서비스는 해당 장에서 필요할 때 만듭니다.
- 오류나 빈 응답을 예시 답변으로 대체하지 않습니다.
- 좋은 답변 한 건, 높은 점수 한 번으로 실습 전체가 통과했다고 보지 않습니다.
- **중간에 멈출 때도 [15의 정리](docs/15-capstone-cleanup.md)를 확인**합니다.

Owner 역할이 있어도 모델 할당량·지역·제한 제공 기능을 자동으로 사용할 수 있는 것은 아닙니다. 조직의 보호 설정을 유지합니다. 14장은 포함된 GitHub OIDC CI/CD 실습에 필요한 저장소·환경 권한만 다룹니다.

## 포털·CLI 요약 영상

**각 3분 38초, 음성 없이 자막으로 설명합니다.** 실제 포털 조작과 실시간 CLI 출력을 녹화·편집했으며 모델 응답을 시뮬레이션하지 않았습니다.

| 한국어 | English |
|---|---|
| [![한국어 요약](docs/assets/videos/foundry-v1.5-summary-ko-poster.png)](docs/assets/videos/foundry-v1.5-summary-ko.mp4) | [![English summary](docs/assets/videos/foundry-v1.5-summary-en-poster.png)](docs/assets/videos/foundry-v1.5-summary-en.mp4) |
| [MP4 보기](docs/assets/videos/foundry-v1.5-summary-ko.mp4) · [자막](docs/assets/videos/foundry-v1.5-summary-ko.srt) | [Watch MP4](docs/assets/videos/foundry-v1.5-summary-en.mp4) · [Captions](docs/assets/videos/foundry-v1.5-summary-en.srt) |

[녹화 범위와 출처](docs/videos.md) · [실제 검증 결과와 제한](docs/validation-report.md). 영상은 이전 실습 시점의 기록입니다. 현재 모델 기본값과 Search 준비 조건은 최신 본문을 따르며, 과거 녹화만으로 현재 단계의 성공을 판단하지 않습니다.

**도움말:** [문제 해결](docs/troubleshooting.md) · [기능 찾기](docs/feature-map.md) · [코드 읽기](docs/code-reading.md) · [공식 자료](docs/sources.md)
