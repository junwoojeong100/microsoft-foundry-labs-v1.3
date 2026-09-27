# v1.2 기능과 현재 자가 실습의 대응

**기능은 유지하고, 준비와 진행을 참가자 본인이 수행하도록 바꿨습니다.** 코드·데이터·SDK는 고정 v1.2 구현 하나를 사용합니다.

| v1.2 기본 범위 | v1.5 자가 실습 |
|---|---|
| 환경·프로젝트·모델·RBAC | [00](00-setup.md)에서 직접 생성/권한/설정 |
| 모델·프롬프트·비교·Router | [01](01-foundry.md), [02](02-models-prompts.md) |
| Prompt Agent·파일 근거 | [03](03-knowledge.md) |
| MAF·함수·MCP | [04](04-tools.md) |
| 순차·병렬·Group Chat | [05](05-workflows.md) |
| Search·IQ·Hybrid·IQ Chat | [06](06-search-iq.md), 직접 서비스/embedding/모델 준비 |
| dev·candidate·native 평가 | [07](07-evaluation.md) |
| Hosted 패키지·로컬·원격·workflow | [08](08-hosted.md) |
| trace·운영·비용 | [09](09-operations.md), 직접 로그 환경 준비 |
| Toolbox·IQ 확장 | [10](10-toolbox-skills.md), [14](14-additional-permissions.md) |
| 최종 인수·정리 | [15](15-capstone-cleanup.md) |

## 확장 기능도 포함

| 기능 | 현재 안내 | 고정 원본의 상세 계약 |
|---|---|---|
| Toolbox lifecycle | 10 | [toolbox](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/toolbox.md) |
| Hosted Toolbox | 10 | [toolbox-hosted](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/toolbox-hosted.md) |
| Code Interpreter·OpenAPI | 04, 10 | [additional-tools](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/additional-tools.md) |
| Tool Search·Skills | 10 | [tool-search-skills](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/tool-search-skills.md) |
| 대화 평가 | 12 | [conversation-evaluation](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/conversation-evaluation.md) |
| Agent Insights | 09 | [agent-insights](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/agent-insights.md) |
| Agent Optimizer | 12 | [agent-optimizer](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/agent-optimizer.md) |
| 승인·복구·steering | 05 | [approval-recovery](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/approval-recovery.md) |
| A2A 1.0 | 11 | [a2a](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/a2a.md) |
| Memory lifecycle | 11 | [memory](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/memory.md) |
| Routines | 11 | [routines](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/routines.md) |
| 안전 제어·red teaming | 13 | [agent-safety](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/agent-safety.md) |
| 지속 평가·CI/CD·OIDC·rollback | 09, 14 | [release-operations](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/release-operations.md) |
| 모델 교체·Router·폐기 | 02, 07, 15 | [model-operations](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/model-operations.md) |
| 거버넌스·네트워크 | 13 | [governance-networking](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/governance-networking.md) |
| 개발 Toolkit·SDK 연습 | 00, [코드 읽기](code-reading.md) | [developer-toolkit](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/developer-toolkit.md) |
| 전문 영역·추가 권한 | 14 | [specialist-scope](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/specialist-scope.md) |

고정 Hosted matrix·calibration·회귀·trace는 [12](12-improvement.md), 최종 holdout은 [15](15-capstone-cleanup.md)에 있습니다.

**상태를 구분합니다:** 직접 실행 / 검증 / 미지원·차단 / 추가 권한 필요 / 설계만. 원본에서 설계만 다룬 Fabric·Work IQ·전문 기능을 새 구현으로 과장하지 않습니다.

이전의 별도 A/B/C 또는 7시간/상세 분기를 고를 필요 없이 [00](00-setup.md)부터 진행합니다.
