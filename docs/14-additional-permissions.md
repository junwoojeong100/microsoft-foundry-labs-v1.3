# 14. GitHub OIDC CI/CD 실습

[English](en/14-additional-permissions.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 포함된 GitHub Actions workflow를 OIDC 관리 ID로 실행하고, 정확한 Hosted 버전의 6문항 dev 업무 검사와 결과 파일을 확인합니다.

**시작 조건:** 08의 Hosted 준비, 본인 GitHub 저장소의 Actions·Environment 설정 권한, 실습 Azure 자원과 역할. GitHub 권한이 없으면 CI를 미실행으로 기록하고 15로 진행합니다.

**실행 위치:** GitHub 웹의 Actions·Settings, Azure 포털의 관리 ID·IAM, 터미널의 `gh`.

> **진행 조건:** GitHub 권한이 없다면 [15장](15-capstone-cleanup.md)으로 갑니다. 진행한다면 **변수 → federation → 인증 확인 → 릴리스** 순서를 지킵니다.

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. 저장소·Environment](#1-저장소와-environment-준비) | 검사한 commit과 `foundry-workshop` |
| [2. CI 관리 ID](#2-azure-ci-관리-id-준비) | Client ID·principal ID와 제한된 역할 |
| [3. 변수 등록](#3-실행-전에-environment-변수-등록) | workflow가 읽는 `vars.*` 값 |
| [4. federation](#4-oidc-federation-연결) | 내 저장소의 실제 issuer·subject·audience |
| [5. 인증만 확인](#5-배포-없이-인증만-확인) | 실제 로그인 성공, 배포는 아직 안 함 |
| [6. 수동 릴리스](#6-수동-릴리스와-같은-버전의-결과-확인) | 정확한 새 버전·dev 6행·세션 중지 |
| [완료 확인](#완료-확인) | commit·ID·버전·artifact의 일치 |

OIDC는 GitHub Actions가 짧게 유효한 신원 증명으로 Azure에 로그인하는 방식입니다. 장기 client secret을 저장하지 않습니다. 로컬 `az login`이나 구독 Owner 권한이 GitHub 실행기에 자동 전달되지는 않습니다.

## 1. 저장소와 Environment 준비

1. 이미 본인이 관리하는 실습 저장소가 있으면 사용합니다. ZIP으로 시작했고 아직 없다면 [원본 저장소](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5)에서 **Fork → 본인 Owner 선택 → Create fork**로 자신의 사본을 만듭니다. [브라우저 Fork 절차](https://docs.github.com/en/pull-requests/how-tos/work-with-forks/fork-a-repo?tool=webui)에는 로컬 Git 작업이 필요하지 않습니다.
2. **본인 저장소**의 `main`에서 `.github/workflows/`와 `.gitignore`를 확인하고 사용할 commit을 기록합니다. Fork는 원격에 저장된 소스만 복사하며 내 PC의 변경은 포함하지 않습니다. 로컬 코드를 바꿨다면 검토한 소스 변경만 반영하고, 실습 폴더나 ZIP 전체를 업로드하지 않습니다. `.env`, `.selfstudy/`, `.build/`, `outputs/`, 자격 증명은 제외합니다.
3. **Actions**에서 fork의 workflow 활성화 안내가 나오면 본인 저장소와 조직 정책을 확인한 뒤 활성화합니다. **Workshop checks → Run workflow → main**으로 [포함된 검사](../.github/workflows/check.yml)를 수동 실행하고 그 commit의 통과를 확인합니다. 이 검사는 Azure 배포/모델 호출을 하지 않습니다.
4. **Settings → Environments → New environment**에서 이름을 정확히 `foundry-workshop`으로 만듭니다. 두 workflow가 이 이름을 고정해서 사용하므로 예시로 보고 다른 이름을 넣지 않습니다.
5. 조직 정책에 맞는 `main` 배포 branch 제한과 승인 규칙을 설정합니다. Fork·메뉴·권한·요금제 제약이 있으면 저장소를 공개로 바꾸거나 보호를 낮추지 말고 이 장을 차단/미실행으로 남깁니다.

이후 모든 **Actions·Settings 작업과 OIDC 값은 본인 저장소 기준**입니다. `Run workflow`가 없으면 `main`에 해당 workflow 파일이 있는지와 실행 권한을 먼저 확인합니다. GitHub Actions 실행 시간/저장소 과금은 Azure 비용과 별도입니다.

## 2. Azure CI 관리 ID 준비

Azure 포털에서 실습 그룹에 **User assigned managed identity**를 만들거나 이 실습 소유의 기존 ID를 확인합니다. Overview에서 **Client ID**와 **Object (principal) ID**를 따로 기록합니다.

| 부여 대상 | 역할 | 범위 |
|---|---|---|
| 이 CI 관리 ID | Foundry Project Manager | 00의 실제 Foundry 프로젝트 |
| 같은 CI 관리 ID | Reader | 부모 Foundry 계정 |

해당 리소스의 **IAM → Add role assignment**에서 본인 CI ID를 선택합니다. 없는 역할만 추가하고 구독 Owner나 client secret은 부여하지 않습니다. 릴리스가 생성하는 **Hosted 런타임 ID의 Foundry User**는 다른 역할이며, 뒤의 동의한 workflow 단계에서 프로젝트 범위로 부여합니다.

**CI가 그 역할을 부여할 수 있는 이유:** [Foundry Project Manager는 Foundry User 역할에 한해 조건부 역할 부여를 허용](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles/ai-machine-learning#foundry-project-manager)합니다. 모든 역할을 부여할 수 있는 관리자가 되는 것은 아니며, 이 실습을 위해 CI에 Owner를 추가할 필요도 없습니다.

## 3. 실행 전에 Environment 변수 등록

GitHub **Settings → Environments → foundry-workshop → Environment variables → Add variable**에서 다음을 각각 **변수**(Variables)로 등록합니다. workflow는 `vars.*`를 읽으므로 같은 이름의 Secret에만 넣으면 읽지 못합니다.

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

먼저 본인 저장소의 OIDC 정책과 식별자를 읽습니다. [GitHub CLI](https://cli.github.com/) 설치와 정상 로그인이 필요하며 `YOUR-OWNER/YOUR-REPOSITORY`를 실제 **본인 저장소**로 바꿉니다.

```bash
gh auth login
gh api repos/YOUR-OWNER/YOUR-REPOSITORY/actions/oidc/customization/sub
gh api repos/YOUR-OWNER/YOUR-REPOSITORY --jq '{repository: .full_name, owner_id: .owner.id, repository_id: .id}'
```

`repository`는 `OWNER/REPOSITORY` 이름이며 `owner_id`와 `repository_id`는 **GitHub의 숫자 ID**입니다. Azure Tenant ID나 관리 ID의 Object ID를 여기에 넣지 않습니다.

CI 관리 ID의 **Federated credentials → Add credential**에서 그 저장소와 Environment `foundry-workshop`에 대한 신뢰를 설정합니다. GitHub 템플릿이 실제와 다른 subject를 자동 생성한다면 **Other issuer** 방식으로 정확한 값을 입력합니다. 기존 credential을 무조건 덮어쓰지 않습니다.

| 항목 | 값 |
|---|---|
| Issuer | `https://token.actions.githubusercontent.com` |
| Audience | `api://AzureADTokenExchange` |
| Subject | 아래 형식을 구분한 뒤 **본인 저장소가 실제 발급하는** Environment subject |

**Subject 형식 읽기 — 아래 문자열 자체를 복사하지 않습니다.**

| 저장소 정책 | `foundry-workshop` Environment의 형식 |
|---|---|
| 이전 이름 기반 기본값 | `repo:OWNER/REPOSITORY:environment:foundry-workshop` |
| Immutable ID 기반 기본값 | `repo:OWNER@OWNER-ID/REPOSITORY@REPOSITORY-ID:environment:foundry-workshop` |
| 조직/저장소 custom 정책 | `include_claim_keys` 등 실제 정책과 발급된 subject를 그대로 대조 |

[현재 GitHub 규칙](https://docs.github.com/en/actions/reference/security/oidc#immutable-subject-claims)에서는 새 저장소나 이름/소유자 변경 후 immutable 형식을 사용할 수 있습니다. `use_default: true`만 보고 이름 기반이라고 가정하지 않습니다. 이 workflow는 Environment를 사용하므로 `ref:refs/heads/main` 형식을 대신 넣지 않습니다.

정책 조회만으로 확정할 수 없다면 **3절 변수가 준비된 상태에서 인증 전용 workflow만 한 번 실행**해 `azure/login` 단계의 **issuer·subject·audience**를 확인할 수 있습니다. 신뢰를 아직 등록하지 않았다면 토큰 교환 실패가 예상되며 인증 성공으로 기록하지 않습니다. 표시된 값과 본인 저장소·Environment를 대조해 정확한 credential을 등록한 뒤 5절에서 다시 인증을 확인합니다. **raw token은 복사하거나 출력하지 않습니다.**

불일치는 정확한 신뢰 설정만 수정하며 wildcard나 client secret으로 우회하지 않습니다. 저장소를 바꾸거나 이름을 변경했다면 재확인합니다. [검증 보고서의 subject](validation-report.md)를 복사하지 않습니다.

## 5. 배포 없이 인증만 확인

**3절의 변수와 4절의 federation을 준비한 뒤** GitHub에서 **Actions → Verify Azure OIDC authentication → Run workflow → main**을 선택합니다. Environment 승인 요청이 있다면 정상 절차를 따릅니다.

[인증 workflow](../.github/workflows/verify-azure-oidc.yml)는 필수 식별자 세 개 확인 → `azure/login`의 실제 인증 → 로그인한 client·tenant·구독 대조 순서입니다. 누락·불일치가 있으면 멈춥니다.

**확인 결과:** 실행이 성공하고 로그에 `authenticated`가 있어야 합니다. `deployment_verified: false`가 정상이며 아직 배포·역할 변경·모델 호출을 한 것은 아닙니다. 실패하면 릴리스를 실행하지 말고 변수·주체·federation부터 확인합니다. raw token은 기록하지 않습니다.

## 6. 수동 릴리스와 같은 버전의 결과 확인

1. [Approved hosted lab release workflow](../.github/workflows/hosted-lab-release.yml)를 읽고 실제 대상·생성·역할·모델 호출 비용을 확인합니다.
2. **Actions → Approved hosted lab release → Run workflow**에서 branch `main`을 선택합니다. 현재 `main`의 commit이 앞에서 검사한 commit과 같은지 확인합니다. 달라졌다면 새 commit의 검사부터 마칩니다.
3. language `ko`를 선택하고, 내용에 동의할 때만 **acknowledge_cost**를 체크한 뒤 실행합니다. 실행 중이면 중복 dispatch하지 않습니다.
4. 패키지 → 새 배포 버전 → 런타임 역할 → **그 버전의 dev 6행** → 해당 세션 중지 순서로 로그를 확인합니다.
5. 실행 페이지 아래 **Artifacts**에서 `foundry-lab-ko-<run-id>`를 내려받습니다. `ci-binding.json`, `ci-runtime-role.json`, `benchmarks/ci-dev/`의 실제 버전·6행·오류·업무 검사를 확인합니다. 기본 artifact 보관은 14일이므로 필요한 결과는 만료 전에 비공개로 보관합니다.

이 workflow는 `workflow / sequential / local / v2 / project-responses / invocations` 프로필을 배포합니다. 12의 IQ/account-chat matrix와 다릅니다. **별도 smoke 명령, LLM policy judge, 관리형 red teaming, holdout은 실행하지 않습니다.** 따라서 CI 업무 검사 통과가 최종 품질 인수나 운영 승인은 아닙니다.

매 push마다 배포하지 않으며 사용자가 수동 실행합니다. 실패하면 추가 릴리스를 멈추고 이전 버전·실패 artifact를 보존합니다. 세션 중지 단계도 확인하고, 실패했다면 [15의 정리](15-capstone-cleanup.md#4-먼저-실행-중인-것을-멈추기)를 수행합니다. [공식 Hosted CI/CD](https://learn.microsoft.com/azure/foundry/agents/quickstarts/set-up-cicd-hosted-agent).

## 완료 확인

- [ ] 검사한 commit과 실제 릴리스 commit이 같다.
- [ ] OIDC 주체·배포 버전·dev 6행을 Actions와 내려받은 artifact에서 대조했다.
- [ ] 세션 중지와 artifact 보관을 확인했고, CI 업무 검사 통과를 최종 인수와 구분했다.

보존 모드에서는 ID·federation·agent·volume을 삭제하지 않습니다.

---

[← 13. 실습 안전](13-governance.md) · [전체 과정](../README.ko.md#진행-순서) · [15. 마무리·정리 →](15-capstone-cleanup.md)
