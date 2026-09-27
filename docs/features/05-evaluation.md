# F05. 고급 평가와 학습 루프

**목표:** 단일 답변 평가를 대화·도구·Optimizer·운영 회귀로 확장하되, 서로 다른 증거를 구분합니다.

준비: [기능 환경](README.md), 실제 응답용 모델, 지원 judge 배포, 호출 비용. 호환 `.env`의 `AZURE_AI_EVALUATION_MODEL_DEPLOYMENT_NAME`을 채웁니다. 첫 대화 평가 경로 45~75분; 다른 기능은 별도 시간입니다.

## 1. 호환 데이터로 실제 dev 결과 만들기

기본 7시간의 `outputs/improved`는 이 실행기의 입력이 아닙니다. 원본 세트로 별도 실행합니다.

```bash
python scripts/v12.py collect --split dev --label feature-candidate --prompt v2 --retrieval local
python scripts/v12.py evaluate --label feature-candidate
python scripts/v12.py cloud-evaluate --label feature-candidate --confirm-cost
```

로컬 업무 검사와 Foundry judge 원점수, 실행 상태·실패 행을 구분합니다. 이때 원본의 v2는 **프롬프트 이름**이며 향후 워크숍 v2.0을 뜻하지 않습니다.

## 2. 한 답변에서 전체 대화로

```bash
python scripts/v12.py conversations plan
```

수집할 시나리오·턴 수·비용 범위를 확인합니다. 독립 사례끼리 대화 상태나 Memory를 공유하지 않습니다.

```bash
python scripts/v12.py conversations collect --label f05-conversations --prompt v2 --confirm-cost
python scripts/v12.py conversations report --label f05-conversations
python scripts/v12.py conversations evaluate --label f05-conversations --level turn --confirm-cost
python scripts/v12.py conversations evaluate --label f05-conversations --level conversation --confirm-cost
```

같은 수집 결과의 **턴 수준**과 **대화 수준** 결과를 봅니다. 앞 답변과 모순되지 않았는지, 사용자의 의도를 끝까지 해결했는지는 단일 문장 유창성만으로 알 수 없습니다.

**완료:** 실제 대화, 전체 행/오류, 두 수준의 점수와 사람 검토. `Completed`와 모든 품질 기준 통과는 다릅니다.

## 3. 도구 선택까지 평가

MAF 함수 도구의 dev 실행과 Foundry 도구 평가 경로도 유지합니다. 원본에서 실험 기능으로 구분한 API이며, 모델·judge·비용 조건을 먼저 확인합니다.

```bash
python scripts/v12.py maf-evaluate --confirm-cost --output outputs/learner-notes-ko/f05-tool-evaluation.json
```

도구가 존재하는지, 적절한 도구를 골랐는지, 입력이 맞는지, 반환값을 사용했는지는 다른 기준입니다. 실제 결과의 해당 항목을 확인합니다.

## 4. Agent Optimizer: 후보를 만들고 사람이 판단

1. 원본 dev에서만 입력을 준비합니다.

   ```bash
   python scripts/v12.py prepare-extensions --label f05-extension-inputs
   ```

2. 반환 폴더의 `optimizer-dev.jsonl`, 원본·해시·dev 분리를 확인합니다.
3. 별도 소유 Prompt Agent와 지원 optimizer 모델·judge를 준비합니다. 기본 과정 에이전트를 몰래 바꾸지 않습니다.
4. Foundry의 해당 agent **Optimize** 흐름에서 **Instruction만**, 후보 수 최대 **2**를 선택합니다.
5. 비용 확인 후 한 번 제출하고, baseline과 모든 후보의 지침 차이·평가 행·실제 judge 입력을 읽습니다.
6. 근거가 좋아진 후보만 별도 검토합니다. 후보 없음·개선 없음·잘못된 평가 연결도 그대로 기록합니다.

원시 judge 입력을 확보할 수 없거나 지원 모델이 없으면 입력 준비까지만 기록합니다. [Optimizer의 정확한 준비·wizard·내보내기](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/agent-optimizer.md)를 따릅니다. **최적화는 자동 모델 가중치 학습이나 자동 운영 승격이 아닙니다.**

## 5. 이후에도 유지하는 기능

| 기능 | 목적 | 이어갈 절차 |
|---|---|---|
| Judge calibration | 예상되는 좋은/나쁜 답에 evaluator가 일관적인가 | [평가 워크북](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/reference/evaluation-workbook.md) |
| Hosted 모델 matrix | 정확한 버전·프로토콜·모델×문항의 모든 행 비교 | [평가 워크북](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/reference/evaluation-workbook.md) |
| 회귀·인수 | 검토된 dev 실패를 다음 검증 자산으로 보존 | [원본 평가 Lab](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/07-evaluation.md) |
| Agent Insights | trace에서 제안한 반복 패턴을 사람이 확인 | [Insights](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/agent-insights.md) |
| 지속 평가·CI/CD·OIDC·rollback | 승인된 릴리스와 운영 품질 통제 | [릴리스 운영](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/release-operations.md) |

Insights의 심각도나 judge의 점수를 ground truth로 취급하지 않습니다. 배포·예약·OIDC 연결은 별도 권한과 실행 승인이 필요합니다.

**정리:** 본인이 만든 평가/데이터의 보관 정책, 임시 optimizer 대상, 지속 평가 일정과 과금 종료를 확인합니다. 평가 기록을 삭제해 실패를 없애지 않습니다.

[기본 Lab 05](../05-evaluation.md) · [기능 목록](README.md)
