# F07. Memory, A2A, Routines

**목표:** 대화 기록, 기억 저장, 다른 agent 위임, 예약 실행을 다른 기능으로 이해합니다.

준비: [기능 환경](README.md). 각 기능은 독립이며 하나를 고릅니다. 기능당 30~45분. 생성·저장·호출·예약 비용과 정리 책임을 먼저 확인합니다.

## 1. Memory: 저장과 조회를 눈으로 확인

준비된 embedding 배포, 올바른 모델 설정과 고유한 Memory store가 필요합니다.

```bash
python scripts/v12.py memory plan
```

계획과 소유 범위를 확인한 뒤 **생성·합성 데이터 저장·모델 비용을 승인한 경우에만** 실행합니다.

```bash
python scripts/v12.py memory create --confirm-create
python scripts/v12.py memory put --scope alpha --case D02 --confirm-write --confirm-cost
python scripts/v12.py memory inspect --scope alpha
python scripts/v12.py memory inspect --scope beta
python scripts/v12.py memory recall --scope alpha --label f07-alpha --confirm-cost
python scripts/v12.py memory recall --scope beta --label f07-beta --confirm-cost
```

원본의 합성 dev 사례만 사용합니다. alpha와 beta의 저장·조회 결과를 비교합니다. **scope 구분 시연을 실제 다른 사용자의 인가 격리 검증이라고 표현하지 않습니다.**

수정·개별 삭제·store 정리까지 [Memory 절차](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/memory.md)를 따릅니다. 자동으로 모든 대화에서 기억을 추출하거나 모든 agent가 자동 사용한다고 주장하지 않습니다.

## 2. A2A: 별도 주소의 agent에게 위임

준비된 A2A 1.0 지원, 본인 소유 target/caller, 승인된 keyless 연결과 호출 권한이 필요합니다.

첫 단계는 계획입니다.

```bash
python scripts/v12.py a2a plan
```

이후 [A2A 절차](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/a2a.md)의 **target 생성 → 실제 card 확인 → keyless 연결 → caller 생성 → 한 번 위임** 순서를 따릅니다.

연결 ID나 target 주소를 예시에서 복사하지 않습니다. 실제 위임 호출을 확인해야 하며, A2A 1.0이 실패했다고 다른 프로토콜로 자동 전환하지 않습니다. 관련 CLI와 소유권 ledger는 v1.2 구현 그대로 유지됩니다.

## 3. Routines: 예약과 결과는 별도

첫 실험은 **비활성화된 일회성 timer**를 준비하고 수동으로 한 번 전달하는 것입니다. 영구 반복 일정이나 외부 메시징 연결부터 만들지 않습니다.

1. 실제 agent, 소유 routine 이름, 내일의 정확한 UTC 시각, 비용·정리 담당자를 정합니다.
2. [Routines 절차](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/routines.md)의 현재 `azd ai routine` 도움말을 확인합니다.
3. disabled 상태로 생성한 뒤 수동 dispatch를 한 번 수행합니다.
4. 실제 routine 이름과 dispatch ID로 실행을 조회합니다.

```bash
python scripts/v12.py routines inspect --name "실제-routine-이름" --dispatch-id "실제-dispatch-ID" --label f07-routine
```

**전달 성공, agent 답변 확인, 미래 예약 실행 성공은 세 가지 다른 증거**입니다. 답변을 조회할 수 없으면 그 상태를 그대로 남깁니다.

## 종료

Memory의 필요 없는 합성 항목·store, A2A의 소유 target/caller/연결, routine과 잔여 세션을 해당 원본 절차로 정리합니다. 예정된 동작은 수업이 끝난 뒤 계속 실행되지 않도록 담당자가 비활성화/삭제 상태를 확인합니다.

**완료:** 선택한 기능의 실제 ID·입력·결과와 정리 상태. 아직 실행하지 않은 나머지 기능은 미실행입니다.

[기능 목록](README.md) · [운영·권한 경계](08-governance.md)
