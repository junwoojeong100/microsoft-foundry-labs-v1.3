# 14. GitHub OIDC CI/CD lab

**English** | [한국어](../14-additional-permissions.md) · [Course home](../../README.md)

**Outcome:** Run the included GitHub Actions workflow using an OIDC managed identity and verify the exact Hosted version's six-case dev business checks and artifacts.

**Prerequisites:** Hosted preparation from 08, Actions/Environment permissions in your own GitHub repository, and the lab's Azure resources and roles. Without the required GitHub access, record CI as not run and continue to 15.

**Order:** repository/Environment → CI identity → variables → federation → authentication-only check → manual release. **Do not run a workflow before its variables exist.**

OIDC lets GitHub Actions sign in to Azure using short-lived identity evidence rather than a stored client secret. Your local `az login` or subscription Owner access is not automatically inherited by GitHub's runner.

## 1. Prepare the repository and Environment

1. Use an existing lab repository you administer. If you started from ZIP and have none, open [the source repository](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5), then select **Fork → your Owner → Create fork**. The [browser fork procedure](https://docs.github.com/en/pull-requests/how-tos/work-with-forks/fork-a-repo?tool=webui) requires no local Git work.
2. On **your repository's** `main`, verify `.github/workflows/` and `.gitignore`, then record the chosen commit. Forking copies committed remote source, not changes on your PC. If you changed local code, publish only reviewed source changes, never the whole working folder or ZIP. Exclude `.env`, `.selfstudy/`, `.build/`, `outputs/`, and credentials.
3. If **Actions** asks you to enable workflows in the fork, review your repository and organizational policy before enabling them. Run **Workshop checks → Run workflow → main** and verify the [included checks](../../.github/workflows/check.yml) pass on that commit. These checks do not deploy to Azure or invoke models.
4. Open **Settings → Environments → New environment** and use the exact name **`foundry-workshop`**. Both workflows require this fixed name; it is not an interchangeable example.
5. Apply the `main` deployment-branch restriction and approval rules required by your organization. If forking, menus, permissions, or plan support are unavailable, record this chapter blocked/not run; do not make a repository public or weaken protections to proceed.

All subsequent **Actions, Settings, and OIDC values refer to your repository**. If `Run workflow` is missing, first check that the workflow file is on `main` and that you have execution permission. GitHub Actions runtime/storage charges are separate from Azure costs.

## 2. Prepare the Azure CI identity

In the Azure portal, create a **user-assigned managed identity** in the lab group, or verify an existing lab-owned identity. Record **Client ID** and **Object (principal) ID** separately from Overview.

| Identity | Role | Scope |
|---|---|---|
| This CI managed identity | Foundry Project Manager | The actual Foundry project from 00 |
| The same CI identity | Reader | Its parent Foundry account |

Use each resource's **IAM → Add role assignment** and select your CI identity. Add only missing roles, not subscription Owner or a client secret. The deployed **Hosted runtime's Foundry User** is a separate assignment, applied at project scope by the later explicitly approved workflow step.

**Why CI can make that assignment:** [Foundry Project Manager conditionally permits assigning Foundry User](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles/ai-machine-learning#foundry-project-manager), not arbitrary roles. The CI identity does not need Owner for this lab.

## 3. Register Environment variables before execution

Under GitHub **Settings → Environments → foundry-workshop → Environment variables → Add variable**, register each value as a **Variable**. The workflows read `vars.*`; putting a value only in a Secret will not satisfy them.

| Variable | Source |
|---|---|
| `AZURE_CLIENT_ID` | Section 2's CI identity **Client ID**, not principal ID |
| `AZURE_TENANT_ID` | The subscription's tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Your lab subscription ID from 00 |
| `AZURE_RESOURCE_GROUP` | Lab resource-group name |
| `AZURE_AI_ACCOUNT_NAME` | Parent Foundry resource name, not project name |
| `AZURE_AI_PROJECT_ENDPOINT` | Project endpoint from 00 |
| `AZURE_AI_PROJECT_ID` | Full project ARM ID through `/projects/...` |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | Actual Sol alias; default `workshop-chat` |
| `WORKSHOP_PREFIX` | Your fixed `lab-` prefix from 00 |
| `WORKSHOP_HOSTED_AGENT_NAME` | A new CI-only name under that prefix, such as `<your-prefix>-ci-hosted-en` |

Use a different CI agent from 08's manual agent and 12's frozen matrix. These are identifiers, not API keys or tokens; never paste the entire `.env`. The first three values are also prerequisites for the authentication workflow.

## 4. Configure OIDC federation

First read your repository's OIDC policy and identifiers. Install [GitHub CLI](https://cli.github.com/) and sign in normally. Replace `YOUR-OWNER/YOUR-REPOSITORY` with **your own repository**:

```bash
gh auth login
gh api repos/YOUR-OWNER/YOUR-REPOSITORY/actions/oidc/customization/sub
gh api repos/YOUR-OWNER/YOUR-REPOSITORY --jq '{repository: .full_name, owner_id: .owner.id, repository_id: .id}'
```

`repository` gives the `OWNER/REPOSITORY` names; `owner_id` and `repository_id` are **GitHub numeric IDs**. They are not Azure tenant IDs or managed-identity Object IDs.

Under the CI identity's **Federated credentials → Add credential**, configure trust for that repository and **Environment `foundry-workshop`**. If the GitHub template generates a different subject, use **Other issuer** to enter the exact values. Do not blindly overwrite an existing credential.

| Field | Value |
|---|---|
| Issuer | `https://token.actions.githubusercontent.com` |
| Audience | `api://AzureADTokenExchange` |
| Subject | The Environment subject **actually issued by your repository**, distinguishing the formats below |

**Read the subject format; do not paste these placeholder strings:**

| Repository policy | Format for the `foundry-workshop` Environment |
|---|---|
| Previous name-based default | `repo:OWNER/REPOSITORY:environment:foundry-workshop` |
| Immutable-ID default | `repo:OWNER@OWNER-ID/REPOSITORY@REPOSITORY-ID:environment:foundry-workshop` |
| Organization/repository custom policy | Match `include_claim_keys` and other actual policy settings against the issued subject |

[Current GitHub rules](https://docs.github.com/en/actions/reference/security/oidc#immutable-subject-claims) can use immutable subjects for new repositories and after renames/transfers. `use_default: true` alone does not establish the name-based format. This workflow uses an Environment; do not substitute a `ref:refs/heads/main` subject.

If the policy response is insufficient, **after registering section 3's variables, run only the authentication workflow once** to inspect the **issuer, subject, and audience** reported by `azure/login`. Token exchange is expected to fail if trust is not registered yet; do not record authentication success. Match those values to your repository/Environment, register the exact credential, then repeat section 5's authentication check. **Never print or copy the raw token.**

Correct only the exact trust relationship on mismatch; do not use wildcards or client secrets. Recheck after changing repositories or renaming one. Do not copy a subject from the [validation report](validation-report.md).

## 5. Check authentication without deploying

**After preparing section 3's variables and section 4's federation**, select **Actions → Verify Azure OIDC authentication → Run workflow → main**. Follow normal Environment approval if requested.

The [authentication workflow](../../.github/workflows/verify-azure-oidc.yml) checks three identifiers, authenticates with `azure/login`, and compares the signed-in client/tenant/subscription. Missing or mismatched values fail explicitly.

**Expected result:** a successful run with `authenticated` in the log. `deployment_verified: false` is expected: no deployment, role change, or model call has occurred. On failure, fix configuration/identity/federation before releasing. Do not record raw tokens.

## 6. Release manually and inspect the exact version

1. Read [Approved hosted lab release](../../.github/workflows/hosted-lab-release.yml) and review its actual target, creation, role assignment, and model costs.
2. Select **Actions → Approved hosted lab release → Run workflow**, then branch **`main`**. Verify its current commit matches the checked commit; if it changed, complete checks for the new commit first.
3. Choose **language `en`**, then check **acknowledge_cost** only if you agree to those actions and costs. Do not dispatch duplicates while a run is active.
4. Follow package → new deployment version → runtime role → **six dev rows on that version** → stop that run's session.
5. Download **Artifacts → `foundry-lab-en-<run-id>`** at the bottom of the run page. Inspect `ci-binding.json`, `ci-runtime-role.json`, and `benchmarks/ci-dev/` for actual version, all six rows, errors, and business checks. The default artifact retention is 14 days; privately preserve needed evidence before expiry.

The workflow deploys `workflow / sequential / local / v2 / project-responses / invocations`, not 12's IQ/account-chat matrix. **It does not run a separate smoke command, LLM policy judge, managed red teaming, or holdout.** Passing CI business checks is not final quality acceptance or production approval.

Release is manual, not triggered by every push. On failure, stop further releases and preserve the earlier version/failure artifacts. Check the session-stop step too; if it fails, follow [15's stopping instructions](15-capstone-cleanup.md#4-stop-running-work-first). See [official Hosted CI/CD guidance](https://learn.microsoft.com/azure/foundry/agents/quickstarts/set-up-cicd-hosted-agent).

## Completion check

Compare the actual commit, OIDC identity, deployment version, and dev results in the Actions run and downloaded artifacts. In retention mode, do not delete identities, federation, agents, or volumes.

**Next → [15. Final acceptance and resource lifecycle](15-capstone-cleanup.md)**
