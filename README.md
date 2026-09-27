# Microsoft Foundry Hands-on Labs v1.5

**Microsoft Entra ID 계정, Azure 구독, 활성화된 구독 Owner 역할에서 출발해 직접 만들고, 사용하고, 평가하고, 배포하고, 정리합니다.**

시간 제한은 없습니다. 강사가 미리 만든 프로젝트·Search·모델·평가 환경을 받는 것을 전제로 하지 않습니다. **[00. 내 실습 환경 만들기](docs/00-setup.md)**부터 순서대로 진행하세요.

> **한 가지 업무, 한 가지 데이터, 한 가지 실행 환경.**
> 가상 기업 **한빛기술의 출장 규정 도우미**를 만듭니다. v1.2의 합성 문서 6개와 실행 구현을 그대로 사용하면서 안내를 새로 구성했습니다.

## 만들면서 이해할 것

“2026년 9월 국내 출장 호텔이 1박 170,000원인데 예약해도 되나요?”에 다음을 설명하는 도우미입니다.

```text
현행 숙박비 한도는 1인 1박 150,000원입니다.
170,000원은 한도를 초과하므로 예약 전에 팀장의 사전 승인이 필요합니다.
근거는 TRAVEL-2026과 APPROVAL-01입니다.
제가 예약하거나 승인한 것은 아닙니다.
```

문장의 일치가 아니라 **맞는 날짜·금액·원문 근거·실제 도구 실행·승인 경계**로 판단합니다. 과거 규정, 식비, 증빙, 해외 규정이 없는 질문도 확인합니다.

**Foundry는 모델 하나가 아니라 모델·에이전트·지식·도구·평가·운영을 연결하는 Azure 플랫폼**입니다. 처음에는 모델을 호출하고, 이후 같은 업무를 Prompt Agent, MAF, 워크플로, Hosted Agent로 발전시킵니다. 같은 업무라도 실행 경로가 다르면 평가 결과를 서로 대신 쓰지 않습니다.

![Foundry 실습의 전체 구조](docs/assets/architecture.svg)

## 순서대로 진행하기

각 장은 **무엇을 만들지 → 내가 준비할 것 → 실행 → 기대 결과 → 막혔을 때 → 다음 장**으로 구성합니다. 소요 시간보다 완료 조건으로 진도를 판단합니다.

| 순서 | 실습 | 직접 남기는 결과 |
|---|---|---|
| [00](docs/00-setup.md) | 계정·도구·Foundry·모델을 직접 준비 | 내 프로젝트, 역할, 설정 |
| [01](docs/01-foundry.md) | Foundry 이해와 첫 모델 응답 | 포털·SDK의 실제 답변 |
| [02](docs/02-models-prompts.md) | 모델·프롬프트·비교·Router | 고정 조건의 비교와 선택 |
| [03](docs/03-knowledge.md) | Prompt Agent·File Search | 저장 버전, 실제 문서 인용 |
| [04](docs/04-tools.md) | MAF·함수·MCP·Code Interpreter | 실제 도구 호출과 파일 |
| [05](docs/05-workflows.md) | 순차·병렬·Group Chat·승인/복구 | 작업 흐름과 중단·재개 기록 |
| [06](docs/06-search-iq.md) | Search 직접 생성·IQ·Hybrid | 검색 서비스, 인덱스, 지식 기반 |
| [07](docs/07-evaluation.md) | 업무 평가·Foundry 평가 | dev 전후 비교, judge 결과 |
| [08](docs/08-hosted.md) | 패키징·로컬 실행·Azure 배포 | 실제 Hosted 버전과 응답 |
| [09](docs/09-operations.md) | 로그 환경 직접 생성·trace·Insights | 내 요청의 운영 근거 |
| [10](docs/10-toolbox-skills.md) | 연결·Toolbox·Tool Search·Skills | 버전 있는 공유 도구와 절차 |
| [11](docs/11-memory-a2a-routines.md) | Memory·A2A·Routines | 기억·위임·예약의 실제 결과 |
| [12](docs/12-improvement.md) | 대화 평가·Optimizer·배포 품질 | 개선 후보, matrix, 검토 결정 |
| [13](docs/13-governance.md) | 안전·권한·네트워크·Control Plane | 적용된 통제와 한계 |
| [14](docs/14-additional-permissions.md) | 추가 계정/권한이 필요한 기능 | CI/CD·Fabric/Work IQ 준비와 범위 |
| [15](docs/15-capstone-cleanup.md) | 최종 인수·모든 비용 자원 정리 | holdout 결과와 정리 기록 |

**진도 기록:** [개인 워크북](worksheets/workbook.md). **기능 전체 대응:** [v1.2 기능 지도](docs/feature-map.md).

## Owner 권한의 범위를 정확히 이해하기

구독 Owner는 Azure 리소스를 만들고 그 범위에서 역할을 부여할 수 있습니다. 하지만 **모든 데이터 접근 권한, 모델 할당량, Preview 접근, Entra 디렉터리 관리자 권한까지 자동으로 갖는 것은 아닙니다.**

| 조건 | 이 과정의 처리 |
|---|---|
| Foundry·Search·로그·모델·관리 ID 역할 | 본인이 생성·설정하는 절차 제공 |
| 지역/할당량/조직 Azure Policy | 생성 전에 확인하고, 제한은 정식 절차로 해결 |
| Preview/제한 제공 기능 | 지원 여부를 먼저 확인. 지원되지 않으면 차단 상태 기록 |
| GitHub CI/CD | GitHub 계정·저장소 권한이 추가로 필요 |
| Fabric/Work IQ/Microsoft 365 | 별도 라이선스·테넌트 설정·데이터 권한/동의가 필요 |

추가 권한이 없는 기능을 성공한 것으로 처리하거나, 강제로 활성화하지 않습니다. **Azure Owner 경로의 완료와 추가 통합의 완료를 구분**합니다.

## 실행 방식은 하나

```bash
python scripts/workshop.py doctor
python scripts/workshop.py model --question "한국어로 한 문장 인사해 주세요."
```

00장에서 설치·로그인·설정을 마친 뒤 실행합니다. 모든 명령은 **v1.5 폴더 루트**에서 시작합니다. 실행기가 고정 v1.2 코드의 올바른 Python·작업 폴더를 선택합니다.

| 항목 | 이 과정의 단일 기준 |
|---|---|
| Python / SDK | `.reference/v1.2/.venv`의 Python 3.13과 고정 패키지 |
| 설정 | `.reference/v1.2/.env` — 설정 도구로 생성/수정 |
| 업무 데이터 | `.reference/v1.2/data/knowledge/policies.json`의 한빛기술 6문서 |
| 평가 | 같은 원본의 dev 6문항, holdout 4문항, calibration |
| 실제 실행 결과 | `.reference/v1.2/outputs/` |
| 내가 만든 Azure 자원 기록 | `.selfstudy/azure.json`와 개인 워크북 |

루트의 `app.py`, `lab.py`, `data/`, `requirements.txt`는 이전 축약 예제를 보존한 것입니다. **현재 본 과정에서는 사용하지 않습니다.** 코드 비교가 필요할 때만 [축약 예제 안내](docs/compact-example.md)를 읽습니다. 두 데이터 세트나 SDK를 섞지 않습니다.

## 비용·데이터·실행 원칙

- 실제 회사 문서, 개인정보, Microsoft 365 데이터 대신 동봉한 합성 자료만 사용합니다.
- 필요한 서비스는 해당 장에서 만듭니다. Search와 로그를 첫날 모두 만들 필요가 없습니다.
- 유료 모델·검색·저장·로그·Hosted·평가 비용은 별개입니다. 예산 알림은 자동 결제 차단이 아닙니다.
- 생성/호출/예약/삭제 전에 대상과 비용을 직접 확인합니다. 실습 전용 리소스 그룹만 사용합니다.
- 오류, 빈 응답, 미지원 기능을 다른 모델·provider·fixture로 몰래 바꾸지 않습니다.
- **마지막 장까지 기다리지 말고 중단할 때도 [정리 절차](docs/15-capstone-cleanup.md)를 확인**합니다.

## v1.5의 방향

v1.0은 Ignite 2025 직후, v1.2는 이후 추가된 기능을 반영한 판입니다. v1.5는 **기능을 줄이지 않고 학습 동선과 독립 실행 가능성을 개선**합니다. 초기 7시간 제약은 제거했습니다. v2.0은 Ignite 2026 이후 계획이며 미래 기능을 미리 가정하지 않습니다.

이 가이드는 실제 Azure 결과를 미리 채워 놓지 않습니다. [출처·검증 범위](docs/sources.md), [버전별 변경](v1.5-changes.md), [문제 해결](docs/troubleshooting.md)을 확인할 수 있습니다.

**지금 시작 → [00. 내 실습 환경 만들기](docs/00-setup.md)**
