# 출처와 검증 범위

**문서/설치본 확인일: 2026-09-27.** 문서 확인, 로컬 계약 검사, 실제 Azure 실행을 구분합니다.

## 원본

| 원본 | 고정 기준 |
|---|---|
| v1.0 | [23e831f367b37d41ea1ad1df47f22b076bc372ff](https://github.com/junwoojeong100/microsoft-foundry-labs/tree/23e831f367b37d41ea1ad1df47f22b076bc372ff) |
| v1.2 | [c2065477baf8210bbba4b845ab741ecd527b9559](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/tree/c2065477baf8210bbba4b845ab741ecd527b9559) |

설정은 [v12-reference.json](../v12-reference.json), 준비는 `scripts/prepare_v12.py`입니다. 소스·문서·합성 데이터·원본 MIT LICENSE를 유지하고 큰 녹화/캡처 미디어는 기본 다운로드에서 제외합니다.

v1.0의 교육용 제공 문구를 v1.2의 MIT와 같은 허가로 간주하지 않습니다. 새 안내·설정 도구·도표는 이 과정에 맞게 작성했습니다.

## 공식 근거

| 주제 | 문서 |
|---|---|
| Foundry의 역할 | [Overview](https://learn.microsoft.com/azure/foundry/what-is-foundry) |
| 프로젝트 생성 | [Create projects](https://learn.microsoft.com/azure/foundry/how-to/create-projects) |
| 데이터/관리 역할 | [Foundry RBAC](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry) |
| 모델·지역·capability | [Azure 판매 모델](https://learn.microsoft.com/azure/ai-foundry/foundry-models/concepts/models-sold-directly-by-azure), [Foundry 지역](https://learn.microsoft.com/azure/foundry/reference/region-support) |
| 현재 SDK·Responses | [Quickstart](https://learn.microsoft.com/azure/foundry/quickstarts/get-started-code) |
| File Search | [File Search](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/file-search) |
| 함수 도구 | [Function calling](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/function-calling) |
| Search 생성 | [Create Search](https://learn.microsoft.com/azure/search/search-create-service-portal) |
| Search 인증·역할 | [Enable RBAC](https://learn.microsoft.com/azure/search/search-security-enable-roles) |
| 기능 플랜 | [Semantic ranker](https://learn.microsoft.com/azure/search/semantic-how-to-enable-disable), [Knowledge retrieval](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-enable-disable) |
| Search 도구/identity | [AI Search tool](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/ai-search) |
| 평가 | [Portal evaluation](https://learn.microsoft.com/azure/foundry/how-to/evaluate-generative-ai-app) |
| trace | [Tracing setup](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup) |
| Hosted | [Hosted quickstart](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent) |
| CI/CD | [Hosted CI/CD](https://learn.microsoft.com/azure/foundry/agents/quickstarts/set-up-cicd-hosted-agent) |
| 가격 | [Azure OpenAI](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/), [Search](https://azure.microsoft.com/pricing/details/search/) |

고정 Toolbox는 **프로젝트 관리 ID**, 직접 OpenAPI는 **Foundry 계정 관리 ID**, IQ Chat은 **Search 관리 ID**를 사용합니다. 일반 Search 문서와 실제 고정 구현의 연결 방식을 혼동하지 않도록 각각 설명했습니다.

## 버전

본 과정은 원본의 Python **3.13**, Projects **2.6.1**, OpenAI **3.16.1**, MAF·MCP·Hosted 패키지 조합을 별도 `.reference/v1.2/.venv`에 설치합니다. 루트 `requirements.txt`의 이전 축약 예제 조합과 합치지 않습니다.

azd에는 `microsoft.foundry` 확장이 필요합니다. 설치된 CLI에서 연결·routine·Hosted·세션·Skill 명령의 도움말을 대조합니다. 서비스 GA와 SDK/기능 Preview는 서로 다른 속성입니다.

## 검증과 한계

| 확인할 수 있는 것 | 이것만으로 보장하지 않는 것 |
|---|---|
| 문서 연결·단계 의존성·원본 기능 대응 | 모든 구독의 가용성/할당량 |
| 설정 도구의 ID/Endpoint/쓰기 범위·오류 처리 | 실제 tenant의 권한 부여 성공 |
| 설치본 SDK·CLI 인자·모의 전송 | 서비스의 실제 응답 품질 |
| 로컬 테스트·이전 예제 회귀 | 참가자의 전체 Azure 실습 완료 |
| 원본의 날짜별 실행 기록 | 새 참가자 환경에서의 성공 |

**이 개편 작업에서는 사용자 구독의 리소스 생성·권한 변경·모델 호출·배포를 실제로 수행하지 않습니다.** 자기 준비 절차와 실행 도구를 작성하고 로컬에서 검증합니다. `selfstudy configure/resource`는 실행 시 Azure 읽기만 하며, `roles`는 명령 생성만 합니다. `capture`는 **사용자가 `--confirm-cost`를 명시할 때만** 실제 Hosted 호출을 수행합니다.

정확한 서비스 결과는 참가자가 각 장에서 생성한 ID·응답·평가·trace로 확인합니다. Owner가 있어도 추가 테넌트 권한이나 제한 제공 기능이 자동 허용되지는 않습니다.

로컬 확인:

```bash
python scripts/check_workshop.py --require-reference
python -m unittest discover -s tests -p test_selfstudy.py -v
```

현재 과정용 테스트는 위의 단일 실습 환경에서 실행합니다. 보존된 축약 예제까지 전체 회귀를 확인할 때는 별도 루트 requirements 환경에서 `python -m unittest discover -s tests -v`를 사용합니다. 테스트의 임시 데이터/모의 응답을 실제 Azure 결과로 옮기지 않습니다.

문서의 메뉴 이름·모델 수명 주기·가격·API 지원은 바뀔 수 있습니다. 실제 화면/도움말이 다르면 공식 근거와 고정 구현을 대조하고 실패를 보존합니다.
