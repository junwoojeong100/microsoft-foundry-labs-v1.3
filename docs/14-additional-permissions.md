# 14. GitHub OIDC CI/CD 실습

**완료 목표:** 포함된 GitHub Actions workflow를 OIDC 관리 ID로 실행하고, 정확한 Hosted 버전의 6문항 dev 업무 검사와 결과 파일을 확인합니다.

**시작 조건:** 08의 Hosted 준비, 본인 GitHub 저장소의 Actions·Environment 설정 권한, 실습 Azure 자원과 역할. GitHub 권한이 없으면 CI를 미실행으로 기록하고 15로 진행합니다.

**순서:** 저장소·Environment → CI 관리 ID → 변수 → federation → 인증만 확인 → 수동 릴리스입니다. **변수를 넣기 전에 workflow부터 실행하지 않습니다.**

OIDC는 GitHub Actions가 짧게 유효한 신원 증명으로 Azure에 로그인하는 방식입니다. 장기 client secret을 저장하지 않습니다. 로컬 `az login`이나 구독 Owner 권한이 GitHub 실행기에 자동 전달되지는 않습니다.

## 1. 저장소와 Environment 준비

1. 이 폴더의 소스를 본인이 관리하는 GitHub 저장소의 `main`에 올립니다. `.github/workflows/`와 `.gitignore`도 포함하며, `.env`, `.selfstudy/`, `.build/`, `outputs/`, 자격 증명은 제외합니다.
2. **Actions → Workshop checks**에서 [포함된 검사](../.github/workflows/check.yml)가 그 commit에서 통과하는지 확인합니다.
3. **Settings → Environments → New environment**에서 이름을 정확히 **`foundry-workshop`**으로 만듭니다. 두 workflow가 이 이름을 고정해서 사용하므로 예시로 보고 다른 이름을 넣지 않습니다.
4. 조직 정책에 맞는 `main` 배포 branch 제한과 승인 규칙을 설정합니다. 메뉴·권한·요금제 제약이 있으면 보호를 낮추지 말고 이 장을 차단/미실행으로 남깁니다.

## 2. Azure CI 관리 ID 준비

Azure 포털에서 실습 그룹에 **User assigned managed identity**를 만들거나 이 실습 소유의 기존 ID를 확인합니다. Overview에서 **Client ID**와 **Object (principal) ID**를 따로 기록합니다.

| 부여 대상 | 역할 | 범위 |
|---|---|---|
| 이 CI 관리 ID | Foundry Project Manager | 00의 실제 Foundry 프로젝트 |
| 같은 CI 관리 ID | Reader | 부모 Foundry 계정 |

해당 리소스의 **IAM → Add role assignment**에서 본인 CI ID를 선택합니다. 없는 역할만 추가하고 구독 Owner나 client secret은 부여하지 않습니다. 릴리스가 생성하는 **Hosted 런타임 ID의 Foundry User**는 다른 역할이며, 뒤의 동의한 workflow 단계에서 프로젝트 범위로 부여합니다.

## 3. 실행 전에 Environment 변수 등록

GitHub **Settings → Environments → foundry-workshop → Environment variables → Add variable**에서 다음을 각각 **변수(Variables)**로 등록합니다. workflow는 `vars.*`를 읽으므로 같은 이름의 Secret에만 넣으면 읽지 못합니다.

| 변수 | 값의 출처 |
|---|---|
| `AZURE_CLIENT_ID` | 2절 CI 관리 ID의 **Client ID**. principal ID가 아님 |
| `AZURE_TENANT_ID` | 해당 구독의 Tenant ID |
| `AZURE_SUBSCRIPTION_ID` | 00의 실습 구독 ID |
| `AZURE_RESOURCE_GROUP` | 실습 그룹 이름 |
| `AZURE_AI_ACCOUNT_NAME` | 부모 Foundry 리소스 이름. 프로젝트 이름이 아님 |
| `AZURE_AI_PROJECT_ENDPOINT` | 00의 Project endpoint |
| `AZURE_AI_PROJECT_ID` | `/projects/...`까지 포함한 프로젝트 ARM ID |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | 실제 Sol 배포 별칭. 기본 `workshop-chat` |
| `WORKSHOP_PREFIX` | 00에서 고정한 내 `lab-` 접두사 |
| `WORKSHOP_HOSTED_AGENT_NAME` | 그 접두사 아래의 새 CI 전용 이름. 예: `<내-prefix>-ci-hosted-ko` |

CI agent는 08/12의 수동 실습·고정 matrix와 다른 이름을 사용합니다. 이 값들은 식별자이며 API key·토큰·`.env` 전체를 붙이지 않습니다. 처음 세 변수가 다음 인증 workflow에도 필요합니다.

## 4. OIDC federation 연결

CI 관리 ID의 **Federated credentials → Add credential**에서 GitHub Actions 연결을 준비합니다. 본인의 저장소와 **Environment `foundry-workshop`**을 대상으로 합니다.

| 항목 | 값 |
|---|---|
| Issuer | `https://token.actions.githubusercontent.com` |
| Audience | `api://AzureADTokenExchange` |
| Subject | **본인 저장소의 현재 OIDC 정책과 정확히 일치하는** Environment subject |

정책 확인에는 [GitHub CLI](https://cli.github.com/)와 본인 저장소 계정의 정상 로그인이 필요합니다. `YOUR-OWNER/YOUR-REPOSITORY`를 실제 저장소로 바꿉니다.

```bash
gh auth login
gh api repos/YOUR-OWNER/YOUR-REPOSITORY/actions/oidc/customization/sub
```

기본 이름 기반 subject와 immutable ID 기반/custom subject는 다를 수 있습니다. 이 조회의 정책과 다음 단계 `azure/login`이 보고하는 **issuer·subject·audience**를 대조합니다. 불일치하면 그 정확한 신뢰 설정만 검토하며 wildcard나 client secret으로 우회하지 않습니다. 저장소를 바꾸거나 이름을 변경했다면 재확인합니다. [검증 보고서의 subject](validation-report.md)를 복사하지 않습니다.

## 5. 배포 없이 인증만 확인

**3절의 변수와 4절의 federation을 준비한 뒤** GitHub에서 **Actions → Verify Azure OIDC authentication → Run workflow → main**을 선택합니다. Environment 승인 요청이 있다면 정상 절차를 따릅니다.

[인증 workflow](../.github/workflows/verify-azure-oidc.yml)는 필수 식별자 세 개 확인 → `azure/login`의 실제 인증 → 로그인한 client·tenant·구독 대조 순서입니다. 누락·불일치가 있으면 멈춥니다.

**확인 결과:** 실행이 성공하고 로그에 `authenticated`가 있어야 합니다. `deployment_verified: false`가 정상이며 아직 배포·역할 변경·모델 호출을 한 것은 아닙니다. 실패하면 릴리스를 실행하지 말고 변수·주체·federation부터 확인합니다. raw token은 기록하지 않습니다.

## 6. 수동 릴리스와 같은 버전의 결과 확인

1. [Approved hosted lab release workflow](../.github/workflows/hosted-lab-release.yml)를 읽고 실제 대상·생성·역할·모델 호출 비용을 확인합니다.
2. **Actions → Approved hosted lab release → Run workflow**에서 branch **`main`**을 선택합니다. 현재 `main`의 commit이 앞에서 검사한 commit과 같은지 확인합니다. 달라졌다면 새 commit의 검사부터 마칩니다.
3. **language `ko`**를 선택하고, 내용에 동의할 때만 **acknowledge_cost**를 체크한 뒤 실행합니다. 실행 중이면 중복 dispatch하지 않습니다.
4. 패키지 → 새 배포 버전 → 런타임 역할 → **그 버전의 dev 6행** → 해당 세션 중지 순서로 로그를 확인합니다.
5. 실행 페이지 아래 **Artifacts → `foundry-lab-ko-<run-id>`**를 내려받습니다. `ci-binding.json`, `ci-runtime-role.json`, `benchmarks/ci-dev/`의 실제 버전·6행·오류·업무 검사를 확인합니다. 기본 artifact 보관은 14일이므로 필요한 결과는 만료 전에 비공개로 보관합니다.

이 workflow는 `workflow / sequential / local / v2 / project-responses / invocations` 프로필을 배포합니다. 12의 IQ/account-chat matrix와 다릅니다. **별도 smoke 명령, LLM policy judge, 관리형 red teaming, holdout은 실행하지 않습니다.** 따라서 CI 업무 검사 통과가 최종 품질 인수나 운영 승인은 아닙니다.

매 push마다 배포하지 않으며 사용자가 수동 실행합니다. 실패하면 추가 릴리스를 멈추고 이전 버전·실패 artifact를 보존합니다. 세션 중지 단계도 확인하고, 실패했다면 [15의 정리](15-capstone-cleanup.md#4-먼저-실행-중인-것을-멈추기)를 수행합니다. [공식 Hosted CI/CD](https://learn.microsoft.com/azure/foundry/agents/quickstarts/set-up-cicd-hosted-agent).

## 완료 확인

실제 commit, workflow run, OIDC 주체, 배포 버전, dev 결과와 artifact를 워크북에 기록합니다. 보존 모드에서는 ID·federation·agent·volume을 삭제하지 않습니다.

**다음 → [15. 최종 인수와 비용 자원 정리](15-capstone-cleanup.md)**
