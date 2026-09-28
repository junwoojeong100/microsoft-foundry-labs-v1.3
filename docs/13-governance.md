# 13. 실습 안전·관리 ID·Control Plane

**완료 목표:** 실습 전용 guardrail의 실제 개입을 확인하고, 호출 주체와 소유 자산을 설명합니다.

**시작 조건:** 본인 프로젝트·도구·실제 Hosted 버전. 공유 정책·다른 사용자의 역할·업무 데이터를 변경하지 않습니다.

## 1. 권한 경로 직접 확인

```bash
python scripts/selfstudy.py status
python scripts/workshop.py doctor --cloud
python scripts/workshop.py cleanup-plan
```

Azure 포털의 해당 리소스 IAM/Identity에서 다음을 대조합니다.

| 연결 | 주체 |
|---|---|
| 내 CLI → Foundry | 내 사용자 |
| 프로젝트 도구 → Search | 선택한 프로젝트 관리 ID |
| Search → IQ Chat 모델 | Search system-assigned identity |
| Hosted → 모델/도구 | 실제 `instance_identity.principal_id` |
| 내가 trace 조회 | 내 사용자와 로그 조회 권한 |

`cleanup-plan`은 삭제가 아닙니다. Owner라고 데이터 역할이 자동으로 있는 것, 포털 성공이 Hosted 권한을 증명하는 것, 역할이 답변을 맞게 만드는 것은 모두 잘못된 가정입니다.

## 2. 내 RAI/guardrail 정책 만들기

1. Foundry **Build → Guardrails → Create**에서 내 실습 전용 이름을 만듭니다.
2. 기본 보호를 유지하고 내가 확인할 제어·개입 지점·차단 동작을 선택합니다.
3. 실제 정책 리소스가 생성됐는지 확인하고 전체 ARM ID를 기록합니다.
4. 기존 `Microsoft.DefaultV2`나 다른 모델/팀의 공유 정책은 수정하지 않습니다.

메뉴나 기능이 제공되지 않으면 제한을 기록합니다. 존재하지 않는 policy ID를 문자열로 넣어 완료 처리하지 않습니다.

## 3. 내 Hosted의 새 버전에 연결

08에서 만든 **독립 Hosted 폴더의 해당 서비스**에만 다음 설정을 추가합니다. 전체 YAML을 바꾸지 않습니다.

```yaml
policies:
  - type: rai_policy
    raiPolicyName: <실제로 생성한 전체 policy ARM ID>
```

새 배포/비용을 확인한 뒤:

```bash
azd deploy "실제-agent-서비스-이름" --cwd "해당-Hosted-절대경로"
azd ai agent show "실제-agent-서비스-이름" --cwd "해당-Hosted-절대경로" --output json
```

정책 리소스, 새 agent 버전의 참조, 실제 요청에 대한 개입을 각각 확인합니다. **12의 고정 matrix target은 바꾸지 말고 08의 별도 기본 Hosted에서 실험**합니다.

## 4. 합성 정상/경계 질문

03의 한빛기술 정책과 dev 질문 D01/D06의 **질문 텍스트만** 새 대화에 보냅니다. 응답 상태·정책 개입 정보·trace를 읽습니다.

- 정책이 연결되었는가?
- 실제로 차단 또는 다른 개입이 있었는가?
- underlying 답변이 여전히 정확한가?
- 단순 지침 거절을 플랫폼 필터 개입으로 오해하지 않았는가?

차단되지 않았으면 그대로 기록합니다. 보기 좋은 결과를 만들려고 위험한 입력을 확장하거나 보호를 낮추지 않습니다.

## 5. 제한된 AI red teaming

지원되는 경우 자신의 Prompt Agent 평가 탭에서 **Red teaming**을 엽니다.

1. 정확한 target 이름/버전을 선택합니다.
2. 위험 범주는 이번 업무의 **금지된 승인 주장**처럼 하나로 제한합니다.
3. 생성 taxonomy에서 관련 없는 행동은 제거하고 입력 수·전략 수·예산을 작게 정합니다.
4. 검토 후 한 번 제출하고 **모든 행의 실제 답변과 판정 설명**을 읽습니다.
5. ASR/집계 점수와 실제 행의 판정이 모순되면 모순을 기록합니다. 원하는 숫자로 수정하지 않습니다.

기능/권한/예산이 없으면 미실행입니다. 로컬 D06 확인을 클라우드 red-team scan으로 표현하지 않습니다.

실제 검증에서는 UI에서 seed 5개를 선택했지만 반환 행은 3개였고, **ASR 100%/`attack_success: true`와 “금지 행동을 수행하지 않았다”는 원시 판정 설명이 모순**됐습니다. 세 응답은 허위 승인 주장을 거절했습니다. 요청 수·실제 행 수·원점수·설명·가려진 입력 여부를 모두 보관하고, 이 집계를 그대로 공격 성공률이나 안전 인증으로 사용하지 않습니다. 분모를 3으로 바꿔 5개 검증이 끝난 것처럼 표시하지 마세요.

## 6. 내 실습의 Control Plane 자산 목록

본인 프로젝트의 agent 이름·정확한 버전·모델 배포·연결·정책·사용량을 Control Plane과 실제 소유권 기록에 대조합니다. 1절의 `cleanup-plan`과 워크북에 없는 새 자원을 성공한 것으로 추정하지 않습니다.

읽기 결과, 이번 실습에서 추가한 역할/정책, 남길 자원을 구분합니다. 접근이 조직 정책으로 차단되면 원래 오류를 기록하고 승인된 담당 절차를 따릅니다. 보호 설정을 낮추거나 공유 자원을 바꾸지 않습니다.

## 완료 확인

추가한 정책/역할/버전, 실제 개입과 비개입, 미지원 기능을 기록합니다. 원래 설정과 비교해 새 변경분만 복원할 수 있어야 합니다.

**다음 → [14. GitHub OIDC CI/CD 실습](14-additional-permissions.md)**. 필요한 GitHub 저장소 권한이 없으면 CI를 미실행으로 기록합니다.
