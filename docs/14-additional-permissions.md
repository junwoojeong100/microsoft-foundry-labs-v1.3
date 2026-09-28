# 14. GitHub OIDC CI/CD 실습

[English](en/14-additional-permissions.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** GitHub Actions로 배포하고, 그 버전의 dev 6문항 결과를 확인합니다.

**시작 조건:** 08장의 준비, 실습 Azure 권한, **본인 GitHub 저장소의 Actions·Environment 설정 권한**.

**실행 위치:** GitHub 웹, Azure 포털, 터미널의 `gh`.

> [!IMPORTANT]
> GitHub 권한이 없으면 이 장을 미실행으로 남기고 [15장](15-capstone-cleanup.md)으로 갑니다. 진행한다면 **변수 → 신뢰 연결 → 인증 확인 → 배포** 순서를 지킵니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. 저장소 준비](#1-저장소와-environment-준비) | 검사한 commit과 Environment |
| [2. CI 관리 ID](#2-azure-ci-관리-id-준비) | ID와 제한된 역할 |
| [3. 변수 등록](#3-실행-전에-environment-변수-등록) | workflow가 읽는 설정 |
| [4. OIDC 연결](#4-oidc-federation-연결) | 저장소와 Azure의 정확한 신뢰 |
| [5. 인증 확인](#5-배포-없이-인증만-확인) | 배포 없이 로그인 성공 |
| [6. 수동 릴리스](#6-수동-릴리스와-같은-버전의-결과-확인) | 새 버전·6행·세션 중지 |
| [완료 확인](#완료-확인) | 코드·버전·결과의 일치 |

CI/CD는 검사·배포를 자동 실행하는 흐름입니다. OIDC는 GitHub가 **짧게 유효한 신원 증명**으로 Azure에 로그인하는 방식입니다. 장기 client secret은 저장하지 않습니다.

## 1. 저장소와 Environment 준비

1. 본인이 관리하는 실습 저장소를 엽니다. 없다면 [원본 저장소](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5)의 **Fork → 본인 계정 → Create fork**로 사본을 만듭니다.
2. 내 저장소의 `main`에서 `.github/workflows/`를 확인하고 사용할 commit을 확인합니다.
3. **Actions**에 활성화 안내가 보이면 조직 정책에 따라 활성화합니다.
4. **Workshop checks → Run workflow → main**을 실행하고 그 commit의 통과를 확인합니다. 이 검사는 Azure를 호출하지 않습니다.
5. **Settings → Environments → New environment**에서 이름을 정확히 `foundry-workshop`으로 만듭니다.
6. 조직 정책에 맞는 `main` 배포 제한과 승인 규칙을 설정합니다.

Fork에는 내 PC의 변경이 포함되지 않습니다. 변경이 있다면 검토한 소스만 반영하고, **`.env`, `.selfstudy/`, `.build/`, `outputs/`, ZIP 전체는 업로드하지 않습니다.**

메뉴·권한·요금제에 막히면 저장소 공개 전환이나 보호 완화로 우회하지 않습니다. `Run workflow`가 없으면 `main`의 파일과 실행 권한부터 확인합니다.

## 2. Azure CI 관리 ID 준비

Azure 포털에서 실습 그룹에 **User assigned managed identity**를 만들거나, 이 실습 소유의 기존 ID를 사용합니다.

Overview의 **Client ID**와 **Object (principal) ID**를 구분합니다. IAM에서 같은 CI 관리 ID에 다음 역할을 부여합니다.

| 역할 | 범위 |
|---|---|
| Foundry Project Manager | 실제 Foundry 프로젝트 |
| Reader | 부모 Foundry 계정 |

기존 역할은 중복 부여하지 않습니다. CI에 구독 Owner나 client secret을 추가하지 않습니다.

**Hosted 런타임 ID와 CI 관리 ID는 별개**입니다. 릴리스는 해당 런타임에 프로젝트 범위 Foundry User를 부여합니다.

이는 [Foundry Project Manager의 조건부 역할 부여](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles/ai-machine-learning#foundry-project-manager) 범위에 포함됩니다.

## 3. 실행 전에 Environment 변수 등록

내 저장소의 **Settings → Environments → foundry-workshop → Environment variables → Add variable**에서 등록합니다.

**Variables에 넣습니다.** 같은 이름의 Secret에만 넣으면 workflow의 `vars.*`가 읽지 못합니다.

| 변수 | 넣을 값 |
|---|---|
| `AZURE_CLIENT_ID` | 2절의 **Client ID**. principal ID 아님 |
| `AZURE_TENANT_ID` | 구독의 Tenant ID |
| `AZURE_SUBSCRIPTION_ID` | 실습 구독 ID |
| `AZURE_RESOURCE_GROUP` | 실습 그룹 이름 |
| `AZURE_AI_ACCOUNT_NAME` | 부모 Foundry 리소스 이름 |
| `AZURE_AI_PROJECT_ENDPOINT` | 00장의 Project endpoint |
| `AZURE_AI_PROJECT_ID` | `/projects/...`까지 포함한 ARM ID |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | Sol 배포 이름. 기본 `workshop-chat` |
| `WORKSHOP_PREFIX` | 00장의 내 접두사 |
| `WORKSHOP_HOSTED_AGENT_NAME` | 새 CI 전용 이름. 예: `<내-prefix>-ci-hosted-ko` |

CI 에이전트는 08·12장의 이름과 구분합니다. API key·토큰·`.env` 전체를 넣지 않습니다. 첫 세 변수는 인증 검사에도 필요합니다.

## 4. OIDC federation 연결

federation은 **어느 GitHub 실행을 Azure가 신뢰할지** 정하는 연결입니다.

[GitHub CLI](https://cli.github.com/)를 설치하고 로그인합니다.

```bash
gh auth login
```

아래 `YOUR-OWNER/YOUR-REPOSITORY`는 **내 저장소**로 바꿉니다.

**OIDC 정책 조회**

```bash
gh api repos/YOUR-OWNER/YOUR-REPOSITORY/actions/oidc/customization/sub
```

**GitHub 숫자 ID 조회**

```bash
gh api repos/YOUR-OWNER/YOUR-REPOSITORY --jq '{repository: .full_name, owner_id: .owner.id, repository_id: .id}'
```

Azure의 CI 관리 ID에서 **Federated credentials → Add credential**을 엽니다.

| 항목 | 값 |
|---|---|
| Issuer | `https://token.actions.githubusercontent.com` |
| Audience | `api://AzureADTokenExchange` |
| Subject | 내 저장소의 `foundry-workshop` Environment가 실제 발급하는 값 |

Subject는 아래 중 **실제 정책과 맞는 형식**을 사용합니다.

| 정책 | 형식 |
|---|---|
| 이름 기반 기본값 | `repo:OWNER/REPOSITORY:environment:foundry-workshop` |
| Immutable ID 기반 기본값 | `repo:OWNER@OWNER-ID/REPOSITORY@REPOSITORY-ID:environment:foundry-workshop` |
| 사용자 지정 정책 | 실제 `include_claim_keys`와 발급된 subject 대조 |

`OWNER-ID`, `REPOSITORY-ID`는 위에서 조회한 **GitHub 숫자 ID**입니다. Azure ID가 아닙니다.

새 저장소·이름 변경 시 형식이 달라질 수 있습니다. [현재 GitHub 규칙](https://docs.github.com/en/actions/reference/security/oidc#immutable-subject-claims)을 확인합니다.

`use_default: true`만으로 형식을 단정하지 않습니다. 템플릿이 다른 값을 만들면 **Other issuer**로 정확한 값을 입력합니다. Environment를 사용하는 실행이므로 `ref:refs/heads/main`을 대신 넣지 않습니다.

**형식을 확정할 수 없다면:** 3절 변수 등록 후 5절의 **인증 전용 workflow만** 한 번 실행합니다. `azure/login` 로그의 issuer·subject·audience를 대조해 신뢰를 등록한 뒤 다시 확인합니다. 등록 전 인증 실패는 예상되며 성공으로 기록하지 않습니다.

raw token은 출력·복사하지 않습니다. wildcard나 client secret으로 우회하지 않습니다.

## 5. 배포 없이 인증만 확인

1. **Actions → Verify Azure OIDC authentication → Run workflow → main**을 선택합니다.
2. Environment 승인 요청이 있으면 정상 절차를 따릅니다.
3. 로그의 로그인 주체·테넌트·구독을 2~3절 값과 대조합니다.

**기대 결과:** workflow 성공, `authenticated`, `deployment_verified: false`. 아직 배포·역할 변경·모델 호출은 하지 않았습니다.

실패하면 릴리스를 실행하지 않습니다. 변수와 federation부터 확인합니다. [인증 workflow](../.github/workflows/verify-azure-oidc.yml).

## 6. 수동 릴리스와 같은 버전의 결과 확인

1. [릴리스 workflow](../.github/workflows/hosted-lab-release.yml)의 배포·역할 부여·호출 비용을 확인합니다.
2. **Actions → Approved hosted lab release → Run workflow → main**을 선택합니다.
3. `main`의 commit이 1절에서 검사한 commit과 같은지 확인합니다. 다르면 새 commit을 먼저 검사합니다.
4. language `ko`를 선택하고, 비용·작업에 동의하면 **acknowledge_cost**를 체크해 한 번 실행합니다.
5. **패키지 → 새 배포 → 런타임 역할 → 그 버전의 dev 6행 → 세션 중지**를 확인합니다.
6. **Artifacts**에서 `foundry-lab-ko-<run-id>`를 내려받습니다.

| 내려받은 파일 | 확인할 내용 |
|---|---|
| `ci-binding.json` | 실제 배포 이름·버전 |
| `ci-runtime-role.json` | 그 런타임 ID의 역할 |
| `benchmarks/ci-dev/` | 실제 6행, 오류, 업무 검사 |

Artifact 기본 보관은 **14일**입니다. 필요한 결과는 만료 전에 비공개로 보관합니다.

이 프로필은 `workflow / sequential / local / v2 / project-responses / invocations`입니다. 12장의 IQ 비교와 다르며, **별도 smoke·LLM judge·관리형 red teaming·holdout은 실행하지 않습니다.**

CI 업무 검사 통과는 최종 품질 인수나 운영 승인이 아닙니다. 실패하면 중복 실행하지 말고 원래 결과와 세션 중지 상태를 확인합니다.

## 완료 확인

- [ ] 검사한 commit과 릴리스 commit이 같다.
- [ ] OIDC 주체·배포 버전·dev 6행을 로그와 artifact에서 대조했다.
- [ ] 세션 중지와 결과 보관을 확인하고, 검사 범위 밖의 평가와 구분했다.

---

[← 13. 실습 안전](13-governance.md) · [전체 과정](../README.ko.md#진행-순서) · [15. 마무리·정리 →](15-capstone-cleanup.md) · [진행 지도 ↑](#chapter-map)
