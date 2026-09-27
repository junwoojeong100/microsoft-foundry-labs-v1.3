# 15. 최종 인수와 비용 자원 정리

**완료 목표:** 고정한 대상의 새 문항 결과를 확인하고, 본인이 만든 모든 비용 자원을 정리하거나 명시적으로 보관합니다.

중도에 실습을 멈추는 경우에도 **아래 정리 절차는 지금 수행**합니다. 품질 실패 때문에 비용 자원을 방치하지 않습니다.

## 1. 무엇을 최종 평가할지 고정

기본 권장 대상은 12의 **실제 Hosted `wf-candidate`**입니다. model map, 코드·지침·원문·retrieval·API·동시성·judge·버전을 고정합니다.

holdout 실행 전 다음을 확인합니다.

- dev matrix의 기대 행 수가 모두 있음. 두 모델이면 12행.
- 오류/누락/중복이 없음.
- 미리 정한 업무 기준이 통과했고 native 결과와 한계를 검토함.
- trace 확인과 calibration이 필요한 기준이면 모두 충족.
- 실패를 보고 기준을 낮추거나 원시 결과를 수정하지 않음.

충족하지 못하면 **holdout을 열지 말고 인수 미완료**로 기록합니다. 추가 기능이 미지원이라 Hosted matrix를 수행하지 않았다면 07의 SDK candidate를 별도 최종 대상으로 선택할 수 있지만, 이를 Hosted 인수라고 표현하지 않습니다.

**holdout은 한 실험의 선택한 최종 대상에만 사용합니다.** SDK에서 이미 본 문항을 Hosted의 “처음 보는 시험”으로 다시 주장하지 않습니다.

## 2. Hosted 최종 확인

12의 모든 게이트를 통과한 경우에만:

```bash
python scripts/workshop.py benchmark collect --split holdout --label wf-final --candidate wf-candidate --unlock-holdout --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py benchmark evaluate --label wf-final --reference wf-baseline --confirm-cost
python scripts/workshop.py benchmark monitor --label wf-final
python scripts/workshop.py benchmark verify --baseline wf-baseline --candidate wf-candidate --holdout wf-final --require-native --require-traces --calibration judge-calibration
```

각 단계의 전체 행과 오류를 확인한 다음 계속합니다. 두 모델이면 holdout은 **8행**입니다. 결과의 `gate_passed`, native 품질, 권고와 `deployment_approved: false`를 함께 봅니다.

**SDK 대상만 선택한 경우**에는 Hosted 명령을 실행하지 않고 다음을 사용합니다. 먼저 07의 `candidate`가 6/6·오류 0·고정 비교 조건을 충족해야 합니다.

```bash
python scripts/workshop.py collect --split holdout --label final-holdout --prompt v2 --retrieval local --candidate candidate --unlock-holdout
python scripts/workshop.py evaluate --label final-holdout
python scripts/workshop.py accept --candidate candidate --holdout final-holdout
```

둘 중 **선택한 하나만** 수행합니다. holdout 실패를 보고 수정했다면 새 최종 데이터가 필요합니다.

## 3. 내 말로 설명

워크북의 인수 카드에 다음을 씁니다.

```text
Foundry는 ______를 위한 플랫폼이다.
지침, 지식, 도구는 각각 ______를 담당한다.
Prompt Agent, 로컬 MAF, Hosted는 ______가 다르다.
개선 여부는 ______라는 실제 근거로 판단했다.
운영 전에 추가로 해결할 것은 ______이다.
```

학습 수행, 작은 품질 기준 통과, 생산 운영 승인은 다른 상태입니다. 새로운 실제 업무에 쓰려면 데이터 권한·더 넓은 평가·사용자 인가·장애/비용 대응이 추가로 필요합니다.

## 4. 먼저 실행 중인 것을 멈추기

1. 내가 실행한 로컬 `serve`/복구 서버는 해당 터미널에서 `Ctrl+C`로 종료합니다.
2. Routines와 반복 평가를 **disabled/paused**로 확인합니다.
3. Hosted matrix를 실행했다면 존재하는 label의 세션을 중지합니다.

```bash
python scripts/workshop.py benchmark stop-session --label wf-baseline
python scripts/workshop.py benchmark stop-session --label wf-candidate
python scripts/workshop.py benchmark stop-session --label wf-final
```

존재하지 않는 실험 label을 억지로 만들지 않습니다. 별도 smoke/수동 호출 세션은 해당 Hosted 폴더의 `azd ai agent sessions list`로 식별한 뒤 본인 세션만 중지합니다.

**stop은 volume 삭제와 다릅니다.** 더 보관할 필요가 없는 세션/volume은 현재 세션 삭제 UI/CLI를 확인해 정리합니다. 다른 사람 프로세스를 이름으로 일괄 종료하지 않습니다.

## 5. 소유 자산 목록 대조

```bash
python scripts/selfstudy.py status
python scripts/workshop.py cleanup-plan
```

둘 다 **삭제하지 않습니다**. 워크북, 실제 포털, 원본의 ownership ledger와 대조합니다.

| 자산 | 확인/정리 |
|---|---|
| Routines·반복 평가 | 비활성화 후 본인 일정 제거 |
| Memory | inspect → 개별 forget → 비어 있는 본인 store cleanup |
| Toolbox·Skills | 참조하는 agent/Toolbox를 먼저 정리하고 본인 Skill 제거 |
| A2A | caller → 연결 → target |
| Prompt/Hosted agent | 정확한 본인 이름·버전·세션 확인 후 제거 |
| File Search | vector store와 업로드 파일을 각각 확인 |
| Search | 원래 index·hybrid index·source/base·서비스 |
| 평가·Optimizer | 보관할 결과/데이터/임시 target을 구분 |
| 로그 | Application Insights·Log Analytics의 실제 그룹·보관 정책 |
| 모델/Foundry | 더 필요한 호출자가 없는지 확인 |
| 역할·관리 ID·federation | 직접 추가한 scope/assignment만 확인 |

주요 소유권 기록은 `.reference/v1.2/outputs/` 아래에 있습니다. 지우면 정리가 쉬워지는 것이 아니라 어떤 자산이 내 것인지 확인하기 어려워집니다.

## 6. 실습 전용 그룹 삭제

모든 자원이 이 과정 전용이고 더 사용할 계획이 없다면 Azure 포털에서:

1. **Resource groups → 내 실습 그룹 → Resources**를 엽니다.
2. 다른 업무/사용자 자원이 없는지 실제 목록을 확인합니다.
3. 보관할 실행/평가 근거를 개인의 승인된 위치에 저장합니다.
4. **Delete resource group**에서 정확한 그룹 이름을 확인해 삭제합니다.
5. 작업 완료와 해당 자원의 부재를 다시 확인합니다.

다른 그룹에 있는 Application Insights, Log Analytics, 관리 ID, 별도 Search/Hosted 자원도 확인합니다. 한 그룹 삭제로 모두 삭제됐다고 가정하지 않습니다.

공유 리소스가 있으면 그룹 전체를 삭제하지 않고 **내가 만든 개별 자산만** 정리합니다. 유지한다면 이유·비용·소유자·다음 확인 일자를 기록합니다.

Azure의 soft delete/보관 정책은 API 삭제와 즉시 물리 삭제를 다르게 만들 수 있습니다. 강제 purge를 기본 실습으로 수행하지 않습니다.

## 7. 최종 확인

- [ ] 실행 중인 예약/세션이 의도치 않게 남지 않았다.
- [ ] 실제 포털에서 삭제 또는 보관 상태를 확인했다.
- [ ] 비용 분석에서 남은 과금 자원을 확인했다. 청구 반영 지연도 고려했다.
- [ ] 합성 결과와 오류·미실행 범위를 사실대로 기록했다.
- [ ] 개인정보·토큰·`.env`를 공개 저장소에 올리지 않았다.

이전 축약 예제를 이미 실행한 사용자는 루트 `.lab/`의 별도 자산도 [축약 예제 안내](compact-example.md)에 따라 확인합니다. 현재 원본 런타임의 정리 명령과 섞지 않습니다.

**과정 종료. [전체 지도](../README.md) · [내 워크북](../worksheets/workbook.md)**
