# F08. 안전, 거버넌스와 전문 영역

**목표:** 기능이 보이는 것과 실제 권한으로 올바르게 작동하는 것을 구분합니다.

준비: [기능 환경](README.md), 담당자 동반, 실제 사용한 자원의 조회 권한. 30~45분. 없는 서비스를 만들거나 다른 사용자의 역할을 제거하는 실습이 아닙니다.

## 1. 호출 주체를 따라가기

```bash
python scripts/v12.py doctor --cloud
python scripts/v12.py cleanup-plan
```

두 명령은 자산을 배포하거나 삭제하는 명령이 아닙니다. 실제 설정·소유권을 읽고 다음 표를 채웁니다.

| 연결 | 실제 호출 주체 | 확인할 권한 |
|---|---|---|
| 로컬 코드 → Foundry | CLI 사용자 | 프로젝트 데이터 작업·모델 사용 |
| Hosted → 모델/도구 | 런타임 identity | 해당 모델·도구 대상 접근 |
| Toolbox → Search | keyless 연결의 identity | 검색 인덱스 접근 |
| IQ → 계획/합성 모델 | Search identity | 실제 모델 접근 |
| 사람 → trace | 조회 사용자 | App Insights/Log Analytics 조회 |

포털 성공을 Hosted 권한 성공으로 대신하지 않습니다. `cleanup-plan`은 **조회**이지 삭제 완료가 아닙니다.

## 2. 안전 통제의 층 구분

| 통제 | 막거나 확인하는 것 | 대신하지 못하는 것 |
|---|---|---|
| 지침 | 원하는 업무 행동 | 코드 수준 인가 |
| 입력 검증 | 잘못된 도구 인수 | 원문 정책의 정확성 |
| RBAC/identity | 누가 어떤 자원을 사용하는가 | 답변의 사실성 |
| Content safety/guardrail | 특정 위험 콘텐츠·행동 | 전체 업무 승인 |
| 네트워크 | 허용된 접근 경로 | 모델의 품질 |
| 사람 승인 | 명시적 업무 결정 | 자동 평가·로그 |

v1.2의 [Agent 안전](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/agent-safety.md)에는 소유 정책 연결과 통제된 red-team 경로가 있습니다. **정책이 연결되었다는 것, 실제 요청에 개입했다는 것, 모든 공격을 막는다는 것은 다릅니다.** 전용 합성 대상과 명시적인 비용·권한 승인 없이 실행하지 않습니다.

## 3. 네트워크와 Control Plane

실제로 사용한 프로젝트, Search, App Insights의 IAM·연결·public/private 접근을 **변경하지 않고** 확인합니다.

준비된 사설 환경이 없으면 승인된 client 경로, DNS, endpoint, 데이터 이동, 복구 책임자를 설계로 기록합니다. 이를 VNet 실행 검증이라고 하지 않습니다. 공유 방화벽을 끄거나 인증서 검사를 무시하지 않습니다.

Control Plane의 fleet/자산/정책/할당량 관점도 유지합니다. AI Gateway가 미구성이라면 “설계만”이며, 실습 표를 채우려고 무관한 agent나 새 Gateway를 만들지 않습니다.

실제 확인 순서: [거버넌스·네트워크](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/governance-networking.md).

## 4. Foundry IQ, Fabric IQ, Work IQ를 구분

| 질문 | 알맞은 정보 | 이 자료의 상태 |
|---|---|---|
| 출장 규정은 무엇인가? | 정책 문서 / Foundry IQ | F04의 실제 합성 검색 실습 |
| 부서별 출장비 합계는? | 분석 데이터 / Fabric | 원본과 동일하게 설계 범위 유지 |
| 출장 회의에서 합의한 것은? | Microsoft 365 업무 맥락 / Work IQ | 원본과 동일하게 설계 범위 유지 |

각각 원본 데이터, 호출 identity, 사용자 권한, 과금·동의 조건이 다릅니다. 실제 회사/Microsoft 365 데이터는 사용하지 않습니다.

세 질문마다 **필요 데이터 / 소유자 / identity / 승인 / 실행 또는 미실행**을 적는 것이 첫 과제입니다. [IQ 확장 Lab](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/10-iq-extensions.md)과 [IQ 워크북](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/reference/iq-workbook.md)을 이어서 봅니다.

## 5. 전문 영역도 상태를 유지

음성·멀티모달, 파인튜닝, 브라우저/컴퓨터 동작, Agent 365 등은 v1.2의 [전문 범위 문서](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/specialist-scope.md)에서 **설계·경계**로 다룬 항목입니다. v1.5에서도 그 범위를 보존하며 구현·배포한 기능으로 과장하지 않습니다.

**완료:** 호출 주체·접근 범위·실제 결과·미실행 영역을 구분한 카드. **정리:** 읽기 확인만 했다면 새 자산이 없습니다. 별도 승인된 정책·예약·연결 변경을 했다면 그 변경분만 원복/정리합니다.

[기본 Lab 06](../06-app-operations.md) · [기능 목록](README.md)
