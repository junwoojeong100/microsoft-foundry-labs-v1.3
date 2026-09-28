# 14. GitHub OIDC CI/CD lab

**English** | [한국어](../14-additional-permissions.md) · [Course home](../../README.md)

**Outcome:** Run the included GitHub Actions workflow using an OIDC managed identity and verify this lab's exact Hosted version and smoke/dev results.

**Prerequisites:** Hosted preparation from 08, Actions/Environment permissions in your own GitHub repository, and the lab's Azure resources and roles. Without the required GitHub access, record CI as not run and continue to 15.

In this repository rerun, **the previous NC group and its CI identity were deleted together**. New group `rg-mflabs15-jw-0928` has a dedicated identity with project-scoped Foundry Project Manager, account Reader, and the **exact current immutable repository/Environment subject**. Main-only protection is unchanged. On code `7b7ca26`, new OIDC authentication and Korean CI v1/English CI v2 each passed all six dev cases. See the [actual runs/artifacts](validation-report.md).

The `cc816de` rename recovery below is **history from when the previous identity still existed**. Archived client/principal IDs and old authentication success are not evidence for the new release.

## 1. Prepare the repository and lab identity

1. Put the complete workshop in a repository you administer. Exclude `.env`, `.selfstudy/`, `outputs/`, and credentials.
2. Verify the included [local-check workflow](../../.github/workflows/check.yml) passes on the exact commit.
3. Create a **user-assigned managed identity** in the lab group, or use an existing identity whose ownership and lab scope are verified. Record its actual client ID and principal ID.
4. Grant only workflow-required roles, such as **Foundry Project Manager at project scope** and **Reader** for account metadata. The Hosted runtime's **Foundry User** role is separate.
5. Configure a protected GitHub **Environment**, such as `foundry-workshop`, with the lab's branch/approval rules.

Do not give the deployment identity subscription Owner or a client secret. Keep organizational protections in place.

## 2. Configure OIDC federation

In the managed identity's **Federated credentials**, configure the GitHub issuer, actual repository/Environment subject, and audience.

- Issuer: `https://token.actions.githubusercontent.com`
- Audience: `api://AzureADTokenExchange`
- Subject: Must match the repository's current policy; do not guess it from names alone.

The following read-only query requires [GitHub CLI](https://cli.github.com/) and normal sign-in with your repository account:

```bash
gh auth login
```

```bash
gh api repos/YOUR-OWNER/YOUR-REPOSITORY/actions/oidc/customization/sub
```

Match the actual subject policy with issuer/subject/audience reported by `azure/login`. Immutable-ID subjects may apply. Do not bypass errors with wildcard trust or a client secret.

**September 28, 2026 rename recovery:** GitHub's `sub_claim_prefix` changed, so after the user's
approval only the repository name in the existing NC `github-foundry-workshop` federation subject
was corrected. Readback preserved the numeric repository ID, managed identity, credential ID,
Environment, issuer, audience, both existing roles, and main-only protection. The actual subject is:

```text
repo:junwoojeong100@6407492/microsoft-foundry-labs-v1.5@1390444066:environment:foundry-workshop
```

The [authentication-only OIDC run](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5/actions/runs/36404614530) and
[repository checks](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5/actions/runs/36404559521) passed on the same commit, `cc816de`.
The actual issuer, subject, audience, and authenticated client/tenant/subscription were checked;
configuration readback alone was not treated as success. No new deployment, role grant, or model
request was performed. This is not a new release or model-quality result.

### Check authentication without deploying

Manually run [Verify Azure OIDC authentication](../../.github/workflows/verify-azure-oidc.yml) through
**Actions -> Verify Azure OIDC authentication -> Run workflow -> main**.
It reuses the existing `foundry-workshop` Environment and its protection rules.

`scripts/verify_ci_auth.py --preflight` checks only the three required identifiers.
Then `azure/login` performs real OIDC authentication, and `scripts/verify_ci_auth.py` matches the
authenticated service principal's client, tenant, and subscription to the configuration.
Missing values, mismatches, and CLI errors fail explicitly. The workflow creates no resources,
deployments, role assignments, or model requests and prints no raw tokens.
Retain the `authenticated` result, run URL, and commit while preserving its `deployment_verified: false` boundary.

## 3. Configure the included manual release

Read the [manual release workflow](../../.github/workflows/hosted-lab-release.yml) and register its **nonsecret identifiers** in the GitHub Environment:

```text
AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID
AZURE_RESOURCE_GROUP, AZURE_AI_ACCOUNT_NAME
AZURE_AI_PROJECT_ENDPOINT, AZURE_AI_PROJECT_ID
AZURE_AI_MODEL_DEPLOYMENT_NAME, WORKSHOP_PREFIX, WORKSHOP_HOSTED_AGENT_NAME
```

Use the actual project, managed identity, and Sol deployment from 00/08. If your existing Sol alias is `workshop-compare`, specify that name unchanged. Do not paste an entire `.env` or access token into variables/logs.

## 4. Verify the same deployed version

1. Verify prerequisite checks passed for the exact commit.
2. Confirm **language `en`**, target, and deployment/role/inference-cost consent, then **dispatch manually**.
3. Verify package → actual new deployment version → smoke/dev gate on **that same version** → result artifacts.
4. On failure, stop further releases and preserve the previous version and failure artifacts.
5. Record the exact target and a separate decision when returning to a reviewed earlier version.

This workflow manually releases to lab resources; it does not deploy on every push. See [official Hosted CI/CD guidance](https://learn.microsoft.com/azure/foundry/agents/quickstarts/set-up-cicd-hosted-agent).

## Completion check

Record the actual commit, workflow run, OIDC identity, deployment version, smoke/dev results, and artifacts. Stop sessions when no longer needed. In retention mode, do not delete identities, federation, agents, or volumes.

**Next → [15. Final acceptance and resource lifecycle](15-capstone-cleanup.md)**
