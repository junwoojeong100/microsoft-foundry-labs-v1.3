# F03. 순차·병렬·Group Chat과 승인/복구

**목표:** 여러 에이전트를 쓴다는 말보다, 작업 순서와 결과의 의미를 이해합니다.

준비: [기능 환경](README.md), 여러 모델 호출의 비용, 새 출력 파일. 시간: 40~60분. 실제 지급·예약·업무 승인은 없습니다.

## 1. 순차부터 한 번 실행

```bash
python scripts/v12.py workflow --pattern sequential --output outputs/learner-notes-ko/f03-sequential.json
```

질문과 근거가 **규정 분석 → 답변 작성 → 근거 검토**로 전달됩니다. 기본 질문은 원본 코드의 현행 출장 숙박 한도 질문입니다. 실제로 보낸 질문을 결과에서 확인합니다.

최종 출력이 한 개여도 모델을 한 번 호출한 것은 아닙니다. 마지막 검토자의 답변이므로 앞 단계의 오류가 전달될 수 있습니다.

## 2. 같은 질문을 병렬로

```bash
python scripts/v12.py workflow --pattern concurrent --output outputs/learner-notes-ko/f03-concurrent.json
```

여러 역할이 동시에 답합니다. 마지막에 이어 붙인 결과가 있어도 **합의하거나 사실을 검증한 답변 하나가 아닙니다**. 벽시계 시간이 짧아도 전체 토큰 비용이 줄었다고 단정하지 않습니다.

## 3. Group Chat으로 역할 간 대화

```bash
python scripts/v12.py workflow --pattern group-chat --output outputs/learner-notes-ko/f03-group-chat.json
```

참여자의 발화와 종료 이유를 봅니다. 이 예제는 최대 3라운드와 시간 제한이 있습니다. 라운드 상한 문구는 출장 규정의 최종 답변이 아닙니다.

| 관찰 | 순차 | 병렬 | Group Chat |
|---|---|---|---|
| 실제 출력 개수와 의미 | 기록 | 기록 | 기록 |
| 근거 전달/누락 | 기록 | 기록 | 기록 |
| 호출량·지연·실패 | 기록 | 기록 | 기록 |
| 이 업무에 필요한가 | 판단 | 판단 | 판단 |

## 4. 사람 검토 경계

`pending-human-review`는 “검토해야 한다”는 상태입니다. 모델끼리 검토했다는 사실을 실제 사용자의 승인으로 바꾸지 않습니다.

배포용으로 검증된 최종 답변과 호출 계보를 받는 실행도 유지합니다.

```bash
python scripts/v12.py workflow-agent --pattern sequential --retrieval local --prompt v2 --output outputs/learner-notes-ko/f03-workflow-agent.json
```

새 호출이므로 비용과 별도 결과가 생깁니다. 이 결과를 Hosted로 옮기는 것은 [F06](06-hosted.md)의 별도 단계입니다.

## 5. 중단·재개는 별도 SDK 실습

v1.2의 [승인 게이트·복구](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/approval-recovery.md)는 실제 state store와 checkpoint를 쓰되 **미리 작성한 합성 작업과 모의 승인**으로 동작합니다.

첫 실행은 버전 검사 → 로컬 서버 → 일시 정지 → 모의 결정 → 동일 응답/출력 ID 확인입니다. 해당 문서의 전용 SDK 버전과 계측 비활성화 조건을 먼저 확인합니다. 일반 Hosted SDK 설치만으로 이 별도 버전 조합까지 맞는다고 가정하지 않습니다.

실제 업무 인가나 외부 작업의 exactly-once 실행을 검증한 것이 아닙니다. 준비되지 않았다면 “복구 실습 미실행”으로 남깁니다.

**완료:** 패턴별 실제 결과와 선택 이유, 사람 승인과 모의 상태의 구분. **정리:** 실행을 끝낸 본인의 로컬 서버만 종료하고 checkpoint는 결과와 함께 보관합니다.

원본의 고급 패턴·IQ 연결: [워크플로 Lab](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/05-workflows.md).

[기본 Lab 04](../04-tools.md) · [기능 목록](README.md)
