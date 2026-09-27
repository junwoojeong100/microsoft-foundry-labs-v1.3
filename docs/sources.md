# 공식 자료와 확인 범위

이 저장소에는 실습 코드, 합성 데이터, 패키징 도구와 테스트가 포함되어 있습니다. 아래 문서는 제품 동작을 더 확인할 때 사용합니다.

| 주제 | 공식 자료 |
|---|---|
| Foundry 개념 | [Overview](https://learn.microsoft.com/azure/foundry/what-is-foundry) |
| 프로젝트 생성 | [Create projects](https://learn.microsoft.com/azure/foundry/how-to/create-projects) |
| 역할과 관리 ID | [Foundry RBAC](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry) |
| 모델과 리전 | [Azure 판매 모델](https://learn.microsoft.com/azure/ai-foundry/foundry-models/concepts/models-sold-directly-by-azure), [리전](https://learn.microsoft.com/azure/foundry/reference/region-support) |
| SDK와 Responses API | [Quickstart](https://learn.microsoft.com/azure/foundry/quickstarts/get-started-code) |
| File Search·함수 | [File Search](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/file-search), [Function calling](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/function-calling) |
| Search 생성·인증 | [Create Search](https://learn.microsoft.com/azure/search/search-create-service-portal), [RBAC](https://learn.microsoft.com/azure/search/search-security-enable-roles) |
| 검색 기능 플랜 | [Semantic ranker](https://learn.microsoft.com/azure/search/semantic-how-to-enable-disable), [Knowledge retrieval](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-enable-disable) |
| 평가·추적 | [Evaluation](https://learn.microsoft.com/azure/foundry/how-to/evaluate-generative-ai-app), [Tracing](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup) |
| Hosted·CI/CD | [Hosted](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent), [CI/CD](https://learn.microsoft.com/azure/foundry/agents/quickstarts/set-up-cicd-hosted-agent) |
| 가격 | [Azure OpenAI](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/), [Search](https://azure.microsoft.com/pricing/details/search/) |

## 무엇이 포함되어 있나요?

실행 버전은 [pyproject.toml](../pyproject.toml)과 [requirements.lock.txt](../requirements.lock.txt)에 고정합니다. Python 3.13을 사용하며, 설치는 `.venv` 한 곳에서 합니다.

라이선스는 [LICENSE](../LICENSE)를 확인하세요. 제품명·API·모델 버전과 이 실습 자료의 버전은 별개입니다.

## 결과를 어떻게 판단하나요?

**로컬 검사와 실제 Azure 실습은 다릅니다.** 로컬 테스트는 코드·요청 형식·입력 검증을 확인합니다. 실제 권한, 모델 품질, 배포, trace는 본인의 Azure 요청 결과로 확인해야 합니다.

```bash
python scripts/check_workshop.py
python -m unittest discover -s tests -v
python -m unittest discover -s tests_sdk -t . -v
```

`selfstudy configure/resource`는 Azure 값을 읽습니다. `roles`는 명령을 보여 줄 뿐 실행하지 않습니다. `capture`는 `--confirm-cost`를 명시할 때 실제 Hosted를 호출합니다.

모델 제공 지역·할당량·Preview 접근·UI·가격은 바뀔 수 있습니다. 문서 확인일은 **2026-09-27**이며 모든 구독의 지원을 보장하지 않습니다.
