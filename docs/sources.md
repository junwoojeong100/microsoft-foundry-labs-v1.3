# v1.5 출처, 버전, 검증 범위

**확인일: 2026-09-27.** 공식 문서 확인, 설치본의 SDK 계약 확인, 실제 Azure 실행은 서로 다른 근거입니다.

## 1. 사용자가 지정한 원본

| 버전 | 고정해서 확인한 커밋 | 참고 범위 |
|---|---|---|
| v1.0 | [23e831f367b37d41ea1ad1df47f22b076bc372ff](https://github.com/junwoojeong100/microsoft-foundry-labs/tree/23e831f367b37d41ea1ad1df47f22b076bc372ff) | README의 포털·코드 경로, 7개 핵심 주제, 학습 목적 |
| v1.2 | [c2065477baf8210bbba4b845ab741ecd527b9559](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/tree/c2065477baf8210bbba4b845ab741ecd527b9559) | 한국어 README, 입문 경로, 에이전트·평가 설명, 패키지·출처 |

기본 동선의 문서·코드·도표·가상 정책·평가 문항과 기능 카드는 새로 작성했습니다. **v1.2 기능 구현은 원본 커밋으로 고정한 소스 복사본을 재사용**합니다. `scripts/prepare_v12.py`가 원본 LICENSE를 유지하고 `.reference/v1.2/`를 준비합니다. 큰 녹화·캡처 미디어는 다운로드하지 않으며 원본의 과거 결과를 새 실행으로 표시하지 않습니다.

v1.2는 [MIT 라이선스](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/LICENSE)가 명시되어 있습니다. v1.0 README의 “교육 목적 제공” 문구를 같은 MIT 허가로 간주하지 않습니다. 외부 자료를 추가 복사할 때는 각각의 라이선스를 다시 확인해야 합니다.

## 2. 공식 기술 근거

| 주제 | 확인한 문서 | v1.5에 반영한 계약 |
|---|---|---|
| Foundry의 의미 | [What is Microsoft Foundry?](https://learn.microsoft.com/azure/foundry/what-is-foundry) | 모델·에이전트·도구·평가·운영을 묶는 플랫폼 |
| 프로젝트 준비 | [Create a project](https://learn.microsoft.com/azure/foundry/how-to/create-projects) | 현재 포털, Foundry 리소스·프로젝트, 역할 구분 |
| 역할 | [Foundry RBAC](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry) | Foundry User 등 역할 이름과 관리/데이터 작업 구분 |
| 모델 선택 | [Azure 판매 모델](https://learn.microsoft.com/azure/ai-foundry/foundry-models/concepts/models-sold-directly-by-azure) · [모델 선택 기준](https://learn.microsoft.com/azure/ai-foundry/foundry-models/how-to/model-choice-guide) | 모델 지원 기능, 속도·비용·업무 적합성. 가용성은 별도 확인 |
| 현재 SDK | [Get started with code](https://learn.microsoft.com/azure/foundry/quickstarts/get-started-code) | `AIProjectClient`, Projects 2.x, `get_openai_client`, Responses |
| Agent 버전 | [SDK 빠른 시작](https://learn.microsoft.com/azure/foundry/quickstarts/get-started-code#create-an-agent) | `PromptAgentDefinition`, `agents.create_version` |
| 파일 검색 | [File Search](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/file-search) | 파일 업로드·벡터 저장소·인덱싱·`FileSearchTool`·인용·별도 과금 |
| 함수 도구 | [Function calling](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/function-calling) | `FunctionTool`, 앱이 실행하고 `function_call_output` 반환 |
| 포털 평가 | [Run evaluations](https://learn.microsoft.com/azure/foundry/how-to/evaluate-generative-ai-app) | Dataset / Individual turns, query·response 매핑, judge 모델, Relevance |
| trace | [Set up tracing](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup) | Application Insights 연결, 서버 측 trace, 응답 ID·권한·보관 비용 |
| 운영 확장 | [Monitoring dashboard](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard) | 관측과 지속 평가의 별도 설정. 일부 기능 Preview |
| 모델 비용 | [Azure OpenAI 가격표](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/) | 단가를 고정 금액으로 보장하지 않음 |

문서의 UI 이름이나 일부 예제는 서로 다른 시점의 내용을 포함할 수 있습니다. 본 과정은 **현재 Foundry + Agent Versions + Responses**로 통일합니다. 포털 버튼 위치가 같다는 보장 대신 작업 목적, 입력, 결과를 제시합니다.

직접 연결형 Prompt Agent의 작은 예제를 사용합니다. 여러 도구를 재사용하거나 복잡한 워크플로를 만들 때 권장되는 Toolbox/Agent Framework 계층을 필수 설치로 추가하지 않았습니다. 이것은 입문 범위를 줄이기 위한 선택입니다.

그 기능 자체를 없앤 것은 아닙니다. [기능 카드](features/README.md)에서는 원본 구현과 별도 SDK를 사용합니다. v1.0의 Ignite 2025 직후 제작, v1.2의 현재 기능 반영, v1.5의 안내 개선, Ignite 2026 이후 v2.0 제작 계획은 사용자의 버전 의도를 반영합니다.

## 3. 이 판의 고정 패키지

실제 설치 파일은 [requirements.txt](../requirements.txt)입니다.

| 패키지 | 버전 |
|---|---|
| azure-ai-projects | 2.7.0 |
| azure-identity | 1.25.3 |
| openai | 3.16.2 |
| httpx | 0.28.1 |
| python-dotenv | 1.2.3 |
| streamlit | 1.64.0 |

PyPI 메타데이터와 실제 설치 가능한 배포를 대조했습니다. 메타데이터의 최신 버전 문자열만으로 설치 가능하다고 가정하지 않았습니다. **직접 의존성 고정**이며 모든 운영체제의 전이 의존성 전체를 동일하게 고정한 lockfile은 아닙니다.

권장 Python은 3.13이고, 코드가 허용하는 범위는 3.11~3.14입니다. 작성 환경의 로컬 검사는 Python 3.14에서 수행합니다. 다른 OS·Python 조합은 수업 전에 별도 점검해야 합니다.

호환 기능은 원본 `pyproject.toml`의 **Projects 2.6.1·OpenAI 3.16.1·MAF 등**을 별도 Python 3.13 환경에 설치합니다. 기본 경로와 버전이 다른 것은 의도한 격리이며, 하나의 가상 환경에 두 세트를 합치지 않습니다.

## 4. 검증 범위를 구분하기

| 구분 | 이 자료가 제공하는 것 | 이것만으로 보장하지 않는 것 |
|---|---|---|
| 문서·데이터 | 420분 시간표, 연결된 단계, 일관된 합성 정책·평가 입력 | 초보자의 실측 완료 시간 |
| 로컬 로직 | 계산, 입력 거부, 평가표 검증, 오류·버전·정리 경계 테스트 | 모델의 실제 정답률 |
| 설치본 계약 | 고정 SDK의 도구 직렬화, 실제 클라이언트의 모의 HTTP 요청/응답 | 서비스의 리전별 실제 수락 |
| 앱 로컬 실행 | 화면·입력·결과 표시와 서버 응답 확인 | 공용 사용자 서비스나 Azure 앱 배포 |
| v1.2 기능 보존 | 고정 커밋 준비, 격리 의존성, 호환 진입점·원본 명령/SDK 계약 | 모든 상세 기능의 새 Azure 실행 |
| 실제 Azure | [강사 사전 점검](instructor.md)의 모델→검색→함수→평가→trace 전체 절차 | 이 문서를 작성하면서 사용자 구독에서 실행했다는 주장 |

**자료 작성 과정에서는 사용자 구독에 리소스를 만들거나 실제 모델·유료 평가를 실행하지 않습니다.** 문서 속 예시 금액은 합성 규정으로 계산한 기대값입니다. 실제 응답 ID, 포털 점수, 배포 성공 기록을 미리 채워 놓지 않습니다.

로컬 확인 명령:

```bash
python -m unittest discover -s tests -v
python scripts/check_workshop.py
```

호환 소스까지 준비했다면 `python scripts/check_workshop.py --require-reference`로 상세 기능 링크의 실제 대상도 확인합니다.

테스트는 Azure 자격 증명 없이, 임시 폴더와 모의 응답을 사용합니다. 테스트 결과 파일을 참가자의 `outputs/` 실적에 섞지 않습니다.

## 5. 사용 중 바뀔 수 있는 것

모델 수명 주기, 리전·할당량, File Search 지원 조합, 포털 평가 선택기, 역할 이름, Preview 기능, 가격은 바뀔 수 있습니다. 수업 당일 이전에 공식 문서와 실제 프로젝트를 확인하세요.

“최신 모델이면 모든 도구가 지원된다”, “포털이 열리면 데이터 작업 권한도 있다”, “이전 버전에서 성공했으니 v1.5도 성공했다”는 가정은 하지 않습니다.

[v1.5 변경 지도](../v1.5-changes.md) · [시작점](../README.md)
