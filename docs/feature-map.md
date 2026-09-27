# v1.2 → v1.5 전체 기능 대응표

**기능 범위는 유지하고, 학습자가 처음 보는 동선만 단순하게 바꿉니다.** “7시간 기본 실습”과 “자료가 보존하는 전체 기능”을 혼동하지 않습니다.

**기본**은 420분 경로에서 직접 수행하는 것, **호환 실습**은 고정 v1.2 구현을 v1.5 카드로 실행하는 것, **설계 유지**는 원본부터 실제 서비스 연결 범위가 아니었던 것입니다. 표는 기능 제공 방식이며, 작성자가 모든 기능을 Azure에서 새로 실행했다는 상태표가 아닙니다.

## 원본의 기본 모듈

| v1.2 주제 | v1.5 기본 동선 | 추가 기능을 유지한 곳 |
|---|---|---|
| 00 시작·환경 | [준비](00-setup.md) | [분리된 호환 환경](features/README.md) |
| 01 Foundry·프로젝트·RBAC | [Lab 01](01-foundry.md) | [F08 거버넌스](features/08-governance.md) |
| 02 모델·비교·Router | [Lab 02](02-models-prompts.md) | [F01 모델 운영](features/01-models.md) |
| 03 Prompt Agent·지침·근거 | [Lab 03](03-knowledge.md) | 관리형 `prompt-agent` 명령도 호환 코드에 유지 |
| 04 MAF·함수·MCP | [Lab 04](04-tools.md)의 도구 원리 | [F02 MAF·MCP·추가 도구](features/02-agents-tools.md) |
| 05 MAF 워크플로 | Lab 04의 실행과 승인 경계 | [F03 순차·병렬·Group Chat·복구](features/03-workflows.md) |
| 06 RAG·Search·IQ·Hybrid | [Lab 03](03-knowledge.md)의 실제 File Search | [F04 Search·IQ·Toolbox](features/04-knowledge.md) |
| 07 평가·학습 루프·holdout | [Lab 05](05-evaluation.md), [Lab 07](07-capstone.md) | [F05 native·대화·회귀·calibration](features/05-evaluation.md) |
| 08 Hosted | [Lab 06](06-app-operations.md)의 앱과 서비스 구분 | [F06 패키지·로컬·원격·matrix](features/06-hosted.md) |
| 09 trace·운영·비용·정리 | [Lab 06](06-app-operations.md), [Lab 07](07-capstone.md) | [F05 릴리스](features/05-evaluation.md), [F08 권한](features/08-governance.md) |
| 10 Fabric/Work IQ 확장 | Foundry의 전체 역할 설명 | [F08 원본과 동일한 설계 범위](features/08-governance.md) |
| 11 캡스톤 | [Lab 07](07-capstone.md) | 원본 고급 인수 워크북도 호환 소스에 유지 |

## 원본의 확장 모듈

| 유지하는 기능 | v1.5 카드 | 실제 원본 절차 / 상태 경계 |
|---|---|---|
| 관리형 Toolbox lifecycle | F04 | [Toolbox](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/toolbox.md) — 버전·목록·실행 별도 |
| Hosted Toolbox | F06 | [Hosted Toolbox](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/toolbox-hosted.md) — 배포 승인 필요 |
| Code Interpreter / OpenAPI | F02 | [추가 도구](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/additional-tools.md) — 실제 파일/API 결과 |
| Tool Search / Skills / catalog | F04 | [Tool Search·Skills](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/tool-search-skills.md) — 지원·접근 조건 |
| 전체 대화 평가 | F05 | [대화 평가](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/conversation-evaluation.md) — 턴/대화 점수 분리 |
| Agent Insights | F05 | [Insights](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/agent-insights.md) — AI finding은 사람 검토 필요 |
| Agent Optimizer | F05 | [Optimizer](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/agent-optimizer.md) — 후보 생성과 승격 분리 |
| 승인 게이트 / 복구 / steering | F03 | [승인·복구](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/approval-recovery.md) — 실제 SDK, 모의 업무 |
| A2A 1.0 | F07 | [A2A](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/a2a.md) — 실제 위임과 프로토콜 확인 |
| Memory lifecycle | F07 | [Memory](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/memory.md) — 합성 scope, 자동 인가 아님 |
| Routines | F07 | [Routines](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/routines.md) — 전달과 답변 분리 |
| 안전 정책 / red teaming | F08 | [Agent 안전](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/agent-safety.md) — 전용 대상·별도 승인 |
| 지속 평가 / CI/CD / OIDC / rollback | F05 | [릴리스 운영](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/release-operations.md) — 운영 승인 필요 |
| 모델 교체 / Router / 폐기 | F01 | [모델 운영](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/model-operations.md) — 고정 조건 비교 |
| 거버넌스 / 네트워크 / Control Plane | F08 | [거버넌스](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/governance-networking.md) — 조회와 설계 구분 |
| 개발 Toolkit / 독립 SDK 연습 | F02 | [개발 도구](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/developer-toolkit.md), [코드 연습](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/code-along.md) |
| 전문 기능 범위 | F08 | [전문 영역](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/specialist-scope.md) — 설계 유지, 구현 주장 안 함 |

원본의 [Hosted 평가 워크북](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/reference/evaluation-workbook.md)과 [IQ 확장 워크북](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/reference/iq-workbook.md)도 유지합니다. 원본에서 설계만 하거나 제한된 접근으로 미실행인 기능을 v1.5에서 “전부 검증됨”으로 바꾸지 않습니다.

## 사용 방법

기본 7시간을 진행하는 동안에는 각 Lab의 다음 링크만 따릅니다. 특정 기능을 더 다룰 때 [기능 환경](features/README.md)을 한 번 준비하고 해당 F 카드의 **첫 실행**부터 진행합니다. 여러 시간의 확장 실습을 7시간 시간표에 몰래 더하지 않습니다.

[버전 의도](../v1.5-changes.md) · [기본 경로](../README.md)
