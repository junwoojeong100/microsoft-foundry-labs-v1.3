# 14. GitHub OIDC CI/CD 실습

**완료 목표:** 포함된 GitHub Actions workflow를 OIDC 관리 ID로 실행하고, 이 실습의 정확한 Hosted 버전과 smoke/dev 결과를 확인합니다.

**시작 조건:** 08의 Hosted 준비, 본인 GitHub 저장소의 Actions·Environment 설정 권한, 실습 Azure 자원과 역할. GitHub 권한이 없으면 CI를 미실행으로 기록하고 15로 진행합니다.

NC 재구축에서는 **이전 CI 관리 ID도 삭제된 Sweden 그룹 안에 있었으므로 함께 없어졌습니다.** 보관된 client/principal ID가 유효하다고 가정하지 않습니다. 새 NC 그룹에 전용 관리 ID를 만들고 프로젝트 범위 Foundry Project Manager, 계정 범위 Reader, 실제 immutable 저장소/Environment subject를 연결했습니다. 기존 main-only 보호는 유지합니다. 실제 릴리스 성공은 [검증 보고서](validation-report.md)의 해당 commit/run으로 확인하며 설정 완료만으로 배포 성공을 주장하지 않습니다.

## 1. 저장소와 실습 ID 준비

1. 이 폴더 전체를 본인이 관리하는 GitHub 저장소에 올립니다. `.env`, `.selfstudy/`, `outputs/`, 자격 증명은 제외합니다.
2. 포함된 [로컬 검사 workflow](../.github/workflows/check.yml)가 정확한 commit에서 통과하는지 확인합니다.
3. Azure 포털에서 실습 그룹에 **User assigned managed identity**를 만들거나, 이 실습에 소유권이 확인된 기존 ID를 사용합니다. 실제 client ID와 principal ID를 기록합니다.
4. workflow가 요구하는 **프로젝트 범위 Foundry Project Manager**, 계정 metadata 조회용 **Reader** 등 필요한 역할만 부여합니다. Hosted 런타임의 **Foundry User**는 별도입니다.
5. GitHub 저장소에 `foundry-workshop` 같은 보호된 **Environment**와 실습용 branch/승인 규칙을 지정합니다.

배포 ID에 구독 Owner나 client secret을 주지 않습니다. 조직의 기존 보호 설정을 낮추지 않습니다.

## 2. OIDC federation 연결

관리 ID의 **Federated credentials**에서 GitHub issuer, 실제 저장소/Environment subject, audience를 연결합니다.

- Issuer: `https://token.actions.githubusercontent.com`
- Audience: `api://AzureADTokenExchange`
- Subject: 현재 저장소의 실제 정책과 일치해야 하며, 이름만으로 추측하지 않습니다.

다음 읽기 명령은 [GitHub CLI](https://cli.github.com/) 설치와 본인 저장소 계정의 정상 로그인이 필요합니다.

```bash
gh auth login
```

```bash
gh api repos/YOUR-OWNER/YOUR-REPOSITORY/actions/oidc/customization/sub
```

실제 subject 정책과 `azure/login`이 보고하는 issuer/subject/audience를 대조합니다. immutable ID 기반 subject가 사용될 수 있습니다. 오류를 wildcard trust나 client secret으로 우회하지 않습니다.

## 3. 포함된 수동 릴리스 설정

[수동 릴리스 workflow](../.github/workflows/hosted-lab-release.yml)를 읽고 GitHub Environment에 **비밀 아닌 식별자**를 등록합니다.

```text
AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID
AZURE_RESOURCE_GROUP, AZURE_AI_ACCOUNT_NAME
AZURE_AI_PROJECT_ENDPOINT, AZURE_AI_PROJECT_ID
AZURE_AI_MODEL_DEPLOYMENT_NAME, WORKSHOP_PREFIX, WORKSHOP_HOSTED_AGENT_NAME
```

00/08에서 확인한 실제 프로젝트·관리 ID·Sol 배포를 사용합니다. 기존 Sol 별칭이 `workshop-compare`이면 그대로 명시합니다. `.env` 전체나 액세스 토큰을 변수/로그에 붙이지 않습니다.

## 4. 같은 버전의 결과 확인

1. 정확한 commit의 선행 검사가 성공했는지 확인합니다.
2. 언어, 대상, 배포/역할/추론 비용 동의를 확인한 뒤 **수동 dispatch**합니다.
3. 패키지 → 실제 새 배포 버전 → **같은 버전**의 smoke/dev gate → 결과 artifact를 순서대로 확인합니다.
4. 실패하면 추가 릴리스를 멈추고 이전 버전과 실패 artifact를 보존합니다.
5. 검토한 이전 버전으로 되돌릴 때에도 정확한 대상과 별도 결정을 기록합니다.

이 workflow는 실습 자원에 대한 수동 릴리스입니다. 매 push마다 자동 배포하지 않습니다. [공식 Hosted CI/CD](https://learn.microsoft.com/azure/foundry/agents/quickstarts/set-up-cicd-hosted-agent).

## 완료 확인

실제 commit, workflow run, OIDC 주체, 배포 버전, smoke/dev 결과와 artifact를 워크북에 기록합니다. 생성한 세션은 필요에 따라 중지하고, 보존 모드에서는 ID·federation·agent·volume을 삭제하지 않습니다.

**다음 → [15. 최종 인수와 비용 자원 정리](15-capstone-cleanup.md)**
