# 14. 추가 권한 기능의 준비와 경계

**완료 목표:** Azure Owner로 할 수 있는 일과 추가 계정·라이선스·디렉터리 권한이 필요한 일을 구분합니다.

이 장은 조건부입니다. 필요한 추가 조건이 없다면 **설계·미실행**으로 기록하고 15장으로 갑니다. 기본 경로를 끝내기 위해 회사 데이터에 접근하거나 전역 관리자 권한을 요구하지 않습니다.

## 1. 권한 지도

| 기능 | Azure Owner 외에 필요한 것 |
|---|---|
| GitHub Actions CI/CD | 본인 GitHub 계정·저장소 관리/Actions/환경 설정 권한 |
| Entra 앱 등록 방식의 OIDC | 테넌트의 앱 등록 허용 또는 해당 관리자 권한 |
| 사용자 할당 관리 ID 방식의 OIDC | Azure의 관리 ID/federation 생성 권한. 구독 Owner가 일반적으로 가능하지만 정책 확인 |
| Fabric Data Agent / Fabric IQ | 지원 capacity, workspace·데이터 접근, 해당 기능의 제공 조건 |
| Work IQ / Microsoft 365 | 별도 라이선스/사용량 과금·tenant enablement·동의·사용자 데이터 권한 |
| 사설 Skill catalog | API Center 및 catalog 구성·권한·도구 거버넌스 |
| Agent 365·음성·멀티모달 등 | 제품별 라이선스·모델·데이터·테넌트 조건 |

**구독 Owner는 Entra Global Administrator가 아닙니다.** 앱 등록이 기본 허용인 테넌트도 있지만 Owner라는 이유로 보장되지는 않습니다.

## 2. GitHub OIDC를 직접 준비하는 경로

추가 GitHub 조건이 있고 CI를 실제로 실행할 경우입니다. 배포용 identity에 구독 Owner나 client secret을 주지 않습니다.

1. 고정 v1.2 원본 전체를 **별도 개인 작업 폴더**에 준비하고 본인 GitHub 저장소에 올립니다. 원본 CI는 원본 소스 구조를 전제로 하므로 v1.5 루트에 YAML 하나만 복사하지 않습니다. 현재 `.reference`의 원본 remote로 push하지 않습니다.
2. 그 복사본의 offline/SDK/문서 검사가 먼저 통과하는지 확인합니다. 미디어를 생략한 실습 캐시를 전체 원본 CI 입력으로 간주하지 않습니다.
3. Azure 포털에서 실습 그룹에 **User assigned managed identity**를 만들고 client ID·principal ID를 기록합니다. 이 방식은 새 비밀번호를 만들지 않습니다.
4. 해당 identity에 **프로젝트 범위 Foundry Project Manager**, 계정 metadata 조회용 **Reader** 등 실제 workflow에 필요한 권한만 부여합니다. 런타임에는 별도 Foundry User를 부여합니다.
5. GitHub 저장소에 `foundry-workshop` 같은 보호된 **Environment**와 필요한 승인/branch 규칙을 만듭니다.
6. 관리 ID의 **Federated credentials**에서 GitHub issuer, 실제 저장소/환경 subject, audience를 연결합니다.

기본 issuer는 `https://token.actions.githubusercontent.com`, audience는 `api://AzureADTokenExchange`입니다. **subject는 예전 이름 전용 문자열로 추측하지 않습니다.**

```bash
gh api repos/내소유자/내저장소/actions/oidc/customization/sub
```

현재 저장소의 실제 subject 정책과 `azure/login`이 보고하는 issuer/subject/audience를 확인합니다. immutable ID 기반 subject가 사용될 수 있습니다. 오류를 해결하려고 wildcard trust나 client secret으로 우회하지 않습니다.

## 3. 기존 리소스를 쓰는 수동 릴리스

원본의 `.github/workflows/hosted-lab-release.yml`과 helper를 그대로 읽습니다. GitHub Environment에 **비밀 아닌 식별자**를 등록합니다.

```text
AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID
AZURE_RESOURCE_GROUP, AZURE_AI_ACCOUNT_NAME
AZURE_AI_PROJECT_ENDPOINT, AZURE_AI_PROJECT_ID
AZURE_AI_MODEL_DEPLOYMENT_NAME, WORKSHOP_PREFIX, WORKSHOP_HOSTED_AGENT_NAME
```

값은 00/08에서 직접 만든 리소스와 실제 MI에서 가져옵니다. `.env` 파일 전체나 액세스 토큰을 변수/로그에 붙이지 않습니다.

1. 정확한 commit의 선행 검사 workflow가 성공했는지 확인합니다.
2. 언어·대상·배포/역할/추론 비용 동의를 확인해 **수동 dispatch**합니다.
3. 패키지 → 실제 배포 버전 → 같은 버전의 smoke/dev gate → 결과 artifact를 확인합니다.
4. 실패하면 rollout을 멈추고 기존 버전과 실패 artifact를 보존합니다.
5. 검토된 이전 버전으로 되돌릴 때도 별도 결정을 기록합니다.

이 경로는 매 push 자동 배포나 운영 승인 자동화를 요구하지 않습니다. [공식 Hosted CI/CD](https://learn.microsoft.com/azure/foundry/agents/quickstarts/set-up-cicd-hosted-agent)와 [원본 릴리스 절차](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/release-operations.md)를 대조합니다.

## 4. Fabric IQ와 Work IQ

v1.2는 이 영역을 **설계 범위**로 다룹니다. v1.5에서도 제공하지 않은 분석 데이터나 실제 Microsoft 365 연결을 구현했다고 주장하지 않습니다.

| 질문 | 적절한 원본 | 내가 준비해야 할 것 |
|---|---|---|
| 출장 숙박 한도는? | 정책 문서 / Foundry IQ | 06에서 만든 합성 지식 |
| 이번 분기 부서별 출장비 합계는? | Fabric의 분석 모델 | 테스트 workspace/capacity·합성 데이터·Data Agent·접근 권한 |
| 출장 검토 회의의 합의 내용은? | 승인된 업무 맥락 / Work IQ | 별도 테스트 tenant·계정·동의·라이선스/과금·제한된 합성 자료 |

**Fabric의 준비 순서:** 기능 지원 capacity 확인 → 테스트 workspace → 합성 데이터 → 읽기 가능한 Data Agent/의미 모델 → 자산별 identity 방식 확인 → 승인된 연결 → 합성 질문과 근거 대조 → capacity/연결 정리.

**Work IQ의 준비 순서:** 현재 tenant enablement/과금 조건 확인 → 관리자·사용자 동의 → 필요한 delegated 권한과 테스트 사용자 → 데이터 이동/보존/동작 권한 검토 → 제한된 합성 대상의 별도 승인 실험.

Work IQ는 읽기 외 동작이 가능할 수 있습니다. 회사 계정으로 전체 회의/메일을 탐색하는 것을 기본 실습으로 하지 않습니다. 준비되지 않았다면 라우팅·identity·권한·정리 계획까지만 완료합니다.

공식 근거: [Fabric Data Agent](https://learn.microsoft.com/fabric/data-science/data-agent-end-to-end-tutorial) · [Fabric IQ](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/fabric-iq) · [Work IQ 요구사항](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-work-iq).

## 5. 그 밖의 전문 영역

사설 Skill catalog, Agent 365, 음성/멀티모달, fine-tuning, 브라우저/컴퓨터 동작은 원본의 별도 전문 범위를 유지합니다. 추가 데이터·모델·제품 권한을 확인하고 독립 과제로 진행합니다.

파인튜닝을 하지 않았는데 지침 개선을 “모델 재학습”이라고 하지 않고, catalog를 만들지 않았는데 Skill 등록을 사설 catalog 구축이라고 하지 않습니다.

**다음 → [15. 최종 인수와 비용 자원 정리](15-capstone-cleanup.md)**
