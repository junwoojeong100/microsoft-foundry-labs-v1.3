# 14. GitHub OIDC CI/CD lab

**English** | [한국어](../14-additional-permissions.md) · [Course home](../../README.md)

**Outcome:** Run the included GitHub Actions workflow using an OIDC managed identity and verify this lab's exact Hosted version and smoke/dev results.

**Prerequisites:** Hosted preparation from 08, Actions/Environment permissions in your own GitHub repository, and the lab's Azure resources and roles. Without the required GitHub access, record CI as not run and continue to 15.

The old CI managed identity **was inside the deleted Sweden group and was deleted with it**. Archived client/principal IDs do not establish a usable identity. The NC group now has a dedicated identity with project-scoped Foundry Project Manager, account-scoped Reader, and the exact immutable repository/Environment subject. Existing main-only protection remains. Verify actual release success against the commit/run in the [validation report](validation-report.md); configured identity and variables are not deployment success.

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
