# 15. 최종 인수와 비용 자원 정리

**완료 목표:** 고정한 대상의 새 문항 결과를 확인하고, 본인이 만든 모든 비용 자원을 정리하거나 명시적으로 보관합니다.

중도에 실습을 멈추는 경우에도 **아래 중지·목록 확인·보관 결정을 지금 수행**합니다. 품질 실패 때문에 비용 자원을 방치하지 않습니다. 삭제는 별도로 선택하는 작업입니다.

## 보존 모드로 진행할 때

다음에 재사용하거나 검증 환경을 남기기로 했다면 **삭제 명령을 실행하지 않습니다.**

- `--confirm-delete`, Memory `forget`/`cleanup`, `azd down`, 리소스 그룹 삭제를 모두 생략합니다.
- 03의 File Search는 처음 만들 때 `--retain`을 사용해 vector store 자동 만료도 설정하지 않습니다.
- 11의 Memory는 언어별 새 store를 명시하고 **`memory create --ttl-seconds 0 --confirm-create`**로 항목의 자동 만료 없이 생성합니다. 기존 1시간 store는 삭제하거나 변경하지 않습니다.
- 로컬 서버는 중지하고 Routines·반복 평가는 disabled/paused로 둡니다. 필요 없는 Hosted 실행 세션은 **stop만** 하며 agent·버전·volume은 삭제하지 않습니다.
- `.env`, `.selfstudy/azure.json`, `outputs/`의 실제 ID와 소유권 기록을 개인의 승인된 위치에 보관합니다. 공개 저장소에 올리지 않습니다.
- Search Basic, 파일/volume, 로그 등 남는 비용과 다음 확인 일자를 기록합니다. `lifecycle=retain` 태그는 관리용 표시일 뿐 삭제 방지 잠금이나 비용 상한이 아닙니다.

Memory의 새 기본값 **`default_ttl_seconds=0`은 항목 자동 만료 없음**입니다. 양수 TTL은 최대 365일이며, 이전 store는 기록된 원래 TTL을 유지합니다. `WORKSHOP_MEMORY_STORE_NAME`은 전역 선택값이므로 한국어의 `<prefix>-memory-retained-ko`와 영어의 `<prefix>-memory-retained-en`을 구분하고, 각 실행 전에 해당 언어의 선택값을 확인합니다. [11의 보존용 store 절차](11-memory-a2a-routines.md#1-memory-실제-저장과-새-요청에서의-조회)를 따릅니다.

소유 store 전체의 이름·TTL·ID와 기록을 보관합니다. 새 설정으로 이전 자산을 몰래 변경하거나 인수하지 않습니다. 관리형 세션의 자체 만료는 Memory 항목 TTL과 별도입니다. 아래 삭제 절은 검토 자료로만 읽고, 최종 확인에는 “삭제하지 않고 보존”을 기록합니다.

## 1. 무엇을 최종 평가할지 고정

기본 권장 대상은 12의 **실제 Hosted `wf-candidate`**입니다. model map, 코드·지침·원문·retrieval·API·동시성·judge·버전을 고정합니다.

holdout 실행 전 다음을 확인합니다.

- dev matrix의 기대 행 수가 모두 있음. 이 가이드의 Sol 대상 한 개는 기본 6행.
- 오류/누락/중복이 없음.
- 미리 정한 업무 기준과 세 policy 기준이 통과했고 source/reference 감사 및 native 한계를 검토함.
- trace 확인과 calibration이 필요한 기준이면 모두 충족.
- 실패를 보고 기준을 낮추거나 원시 결과를 수정하지 않음.

현재 새 **Hosted IQ v1/v2 쌍**은 Sol 한 개의 map으로 각각 core dev 6행, 세 policy 기준 각각 6/6, valid 참조 감사, 실제 trace 6/6을 확인했고 같은 동결 코드/corpus에서 비교가 허용됐습니다. 한국어/영어 policy calibration도 각각 24/24입니다. 이전 SDK groundedness 5/6과 `code_hash` 차이로 거부된 SDK 비교는 별도 역사로 보존합니다. 새 쌍의 통과 수가 같으므로 통과율 개선을 주장하지 않습니다.

**최신 Hosted IQ 배포 버전 3**은 canonical dev 6행과 진단 suite version 2의 8행 모두 업무 검사·세 policy 기준·source 감사·실제 trace(6+8)를 확인했습니다. 필수 참조를 유지하는 명시적 `allowed_citations`와 PL06의 절차 전용 `limit_krw: null`도 새 runtime/label에서 검증했습니다. 이전 실패는 보존하며 **새 holdout 결과로 주장하지 않습니다**.

수정된 Prompt Optimizer native job은 **baseline 1.0·새 후보 0개로 조기 종료해 완료**됐습니다. [12의 로컬 감사](12-improvement.md#3-지침만-최적화)는 6개 원문 envelope·세 pinned judge/기준점 4·reason 참조 ID와 calibration을 확인했습니다. 증거 수준은 source echo + reason + counterfactual이며 내부 judge 요청 캡처나 지침 개선을 주장하지 않습니다. Legacy 실패도 그대로 보존합니다.

충족하지 못하면 **holdout을 열지 말고 인수 미완료**로 기록합니다. 추가 기능이 미지원이라 Hosted matrix를 수행하지 않았다면 07의 SDK candidate를 별도 최종 대상으로 선택할 수 있지만, 이를 Hosted 인수라고 표현하지 않습니다.

**holdout은 한 실험의 선택한 최종 대상에만 사용합니다.** SDK에서 이미 본 문항을 Hosted의 “처음 보는 시험”으로 다시 주장하지 않습니다.

## 2. Hosted 최종 확인

12의 모든 게이트를 통과한 경우에만:

12에서 로컬 검색 경로를 명시적으로 선택했다면 아래 수집 명령의 **`--retrieval iq`를 `--retrieval local`로 바꾸고**, 같은 고정 matrix-local 버전을 사용합니다. 평가/trace/인수 기준은 낮추지 않습니다. 결과는 로컬 검색을 사용하는 Hosted의 인수이며 IQ 인수가 아닙니다.

```bash
python scripts/workshop.py benchmark collect --split holdout --label wf-final --candidate wf-candidate --unlock-holdout --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py benchmark evaluate --policy --label wf-final --reference wf-baseline --confirm-cost
python scripts/workshop.py benchmark monitor --label wf-final
python scripts/workshop.py benchmark verify --policy --baseline wf-baseline --candidate wf-candidate --holdout wf-final --require-native --require-traces --calibration policy-calibration-ko
```

각 단계의 전체 행과 오류를 확인한 다음 계속합니다. Sol 대상 한 개의 기본 holdout은 **4행**입니다. 결과의 `gate_passed`, native 품질, 권고와 `deployment_approved: false`를 함께 봅니다.

**SDK 대상만 선택한 경우**에는 Hosted 명령을 실행하지 않고 다음을 사용합니다. 먼저 07의 `candidate`가 6/6·오류 0·고정 비교 조건을 충족해야 합니다.

```bash
python scripts/workshop.py collect --split holdout --label final-holdout --prompt v2 --retrieval local --candidate candidate --unlock-holdout
python scripts/workshop.py evaluate --label final-holdout
python scripts/workshop.py cloud-evaluate --policy --label final-holdout --confirm-cost --timeout 900
python scripts/workshop.py accept --candidate candidate --holdout final-holdout
```

`accept`의 업무 검사만으로 policy grading·참조 감사가 확인되는 것은 아닙니다. 해당 실제 결과와 일치하는 policy calibration도 별도로 검토합니다. 기존 legacy calibration이나 점수를 이름만 바꿔 대체하지 않습니다.

둘 중 **선택한 하나만** 수행합니다. holdout 실패를 보고 수정했다면 새 최종 데이터가 필요합니다.

## 3. 내 말로 설명

워크북의 인수 카드에 다음을 씁니다.

```text
Foundry는 ______를 위한 플랫폼이다.
지침, 지식, 도구는 각각 ______를 담당한다.
Prompt Agent, 로컬 MAF, Hosted는 ______가 다르다.
개선 여부는 ______라는 실제 근거로 판단했다.
이번 합성 실습에서 아직 확인하지 못한 것은 ______이다.
```

학습 수행과 작은 실습 품질 기준 통과는 다른 상태입니다. 실제 실행한 대상·버전·결과와 미확인 항목만 기록하고, 미실행 단계를 성공으로 채우지 않습니다.

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

**세션/파일 만료 전에 증거를 보관**합니다. 중지된 세션에서도 파일이 남아 있으면 회수할 수 있습니다. [세션 파일 안내](advanced/session-files.md)의 **절대 `--target-path`**를 사용하고 원래 요청·버전·도구 결과와 hash를 대조합니다. Stop이나 자원 보존을 무기한 파일 보관으로 해석하지 않습니다.

**stop은 volume 삭제와 다릅니다.** 더 보관할 필요가 없는 세션/volume은 현재 세션 삭제 UI/CLI를 확인해 정리합니다. 다른 사람 프로세스를 이름으로 일괄 종료하지 않습니다.

## 5. 소유 자산 목록 대조

```bash
python scripts/selfstudy.py status
python scripts/workshop.py cleanup-plan
```

둘 다 **삭제하지 않습니다**. 워크북, 실제 포털, `outputs/`의 소유권 기록과 대조합니다.

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

주요 소유권 기록은 `outputs/` 아래에 있습니다. 지우면 정리가 쉬워지는 것이 아니라 어떤 자산이 내 것인지 확인하기 어려워집니다.

03의 SDK File Search 자산은 먼저 삭제 계획을 봅니다.

```bash
python scripts/workshop.py file-search cleanup
```

본인 이름·파일·저장소와 다른 agent의 참조 여부를 확인한 뒤 삭제를 결정하면 실행합니다.

```bash
python scripts/workshop.py file-search cleanup --confirm-delete
```

기록된 버전·저장소·업로드 파일만 정리하며, 포털에서 별도로 만든 자산이나 공유 프로젝트는 삭제하지 않습니다. 새 이름으로 만든 실험은 동일한 `--name`을 지정합니다.

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

이 폴더 밖에서도 실습 자원을 만들었다면 그 기록을 함께 확인합니다. 다른 개인 기록이나 공유 자원을 임의로 삭제하지 않습니다.

**과정 종료. [전체 지도](../README.ko.md) · [내 워크북](../worksheets/workbook.md) · [실습 복습](next-steps.md)**
