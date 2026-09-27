# 14. Prerequisites and boundaries for additional features

**English** | [한국어](../14-additional-permissions.md) · [Course home](../../README.md)

**Outcome:** Distinguish what Azure Owner permits from work requiring additional accounts, licenses, or directory permissions.

This chapter is conditional. Without the extra prerequisites, record **design only / not run** and continue to 15. Do not access corporate data or demand Global Administrator just to finish the core course.

## 1. Permission map

| Feature | Requirements beyond Azure Owner |
|---|---|
| GitHub Actions CI/CD | Your GitHub account plus repository administration, Actions, and environment permissions |
| OIDC using an Entra app registration | Tenant permission to register apps or the appropriate administrator |
| OIDC using a user-assigned managed identity | Permission to create managed identity/federation in Azure; Owner generally permits this, subject to policy |
| Fabric Data Agent / Fabric IQ | Supported capacity, workspace/data access, and feature availability |
| Work IQ / Microsoft 365 | Separate licensing/usage billing, tenant enablement, consent, and user data permissions |
| Private Skill catalog | API Center, catalog configuration/access, and tool governance |
| Agent 365, voice, multimodal, and similar features | Product-specific licenses, models, data permissions, and tenant prerequisites |

**Subscription Owner is not Entra Global Administrator.** App registration may be allowed by default in some tenants, but Owner does not guarantee it.

## 2. Prepare GitHub OIDC

Use this path only if you have the GitHub prerequisites and choose to run CI. Do not give the deployment identity subscription Owner or a client secret.

1. Put the complete workshop into a repository you administer. Exclude personal `.env`, `outputs/`, and `.selfstudy/`.
2. First verify the bundled [local-check workflow](../../.github/workflows/check.yml) passes.
3. In the Azure portal, create a **user-assigned managed identity** in your lab group and record its client ID/principal ID. No new password is needed.
4. Grant only roles actually required by the workflow, such as **Foundry Project Manager at project scope** and **Reader** for account metadata. The runtime separately needs Foundry User.
5. Create a protected GitHub **Environment**, such as `foundry-workshop`, with the needed approval/branch rules.
6. In the identity's **Federated credentials**, configure the GitHub issuer, actual repository/environment subject, and audience.

The standard issuer is `https://token.actions.githubusercontent.com`; the audience is `api://AzureADTokenExchange`. **Do not guess an older name-only subject format.**

```bash
gh api repos/YOUR-OWNER/YOUR-REPOSITORY/actions/oidc/customization/sub
```

Check the repository's actual subject policy and issuer/subject/audience reported by `azure/login`. Immutable-ID subjects may apply. Do not bypass errors with wildcard trust or a client secret.

## 3. Manually release to existing resources

Read the bundled [manual release workflow](../../.github/workflows/hosted-lab-release.yml) and register its **nonsecret identifiers** in the GitHub Environment:

```text
AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID
AZURE_RESOURCE_GROUP, AZURE_AI_ACCOUNT_NAME
AZURE_AI_PROJECT_ENDPOINT, AZURE_AI_PROJECT_ID
AZURE_AI_MODEL_DEPLOYMENT_NAME, WORKSHOP_PREFIX, WORKSHOP_HOSTED_AGENT_NAME
```

Use the actual resources and managed identity from 00/08. Do not paste an entire `.env` or access token into variables/logs.

1. Verify that the prerequisite check workflow passed for the exact commit.
2. Confirm **language `en`**, target, and deployment/role/inference-cost consent, then **dispatch manually**.
3. Verify package → actual deployed version → smoke/dev gate on that same version → result artifacts.
4. On failure, stop rollout and preserve the previous version and failure artifacts.
5. Record a separate decision when reverting to a reviewed previous version.

Azure deployment requires manual execution and cost consent. This does not configure deployment on every push or grant production approval. See [official Hosted CI/CD guidance](https://learn.microsoft.com/azure/foundry/agents/quickstarts/set-up-cicd-hosted-agent).

## 4. Fabric IQ and Work IQ

These require additional products. Do not claim analytics data or Microsoft 365 connections exist when you have not created them.

| Question | Appropriate source | What you must prepare |
|---|---|---|
| What is the lodging limit? | Policy documents / Foundry IQ | Synthetic knowledge created in 06 |
| What are this quarter's travel totals by department? | Fabric analytical model | Test workspace/capacity, synthetic data, Data Agent, and access |
| What was agreed in the travel-review meeting? | Approved work context / Work IQ | Separate test tenant/account, consent, licensing/billing, and limited synthetic content |

**Fabric sequence:** Verify supported capacity → create a test workspace → add synthetic data → expose a readable Data Agent/semantic model → identify each asset's identity mechanism → create an approved connection → compare synthetic questions with source evidence → review capacity/connection lifecycle.

**Work IQ sequence:** Verify current tenant enablement and billing → obtain admin/user consent → configure required delegated permissions and a test user → review data movement, retention, and action authority → run a separately approved experiment on narrowly scoped synthetic content.

Work IQ may support actions beyond reading. Broadly exploring real company meetings/mail is not a default lab exercise. Without prerequisites, complete only routing, identity, permission, and lifecycle planning.

Official references: [Fabric Data Agent](https://learn.microsoft.com/fabric/data-science/data-agent-end-to-end-tutorial) · [Fabric IQ](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/fabric-iq) · [Work IQ requirements](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-work-iq).

## 5. Other specialist areas

Private Skill catalogs, Agent 365, voice/multimodal, fine-tuning, and browser/computer actions require additional data, models, and product permissions. Treat them as independent follow-on projects.

Do not describe instruction optimization as model retraining without fine-tuning. Registering a Skill is not the same as building a private catalog.

**Next → [15. Final acceptance and resource lifecycle](15-capstone-cleanup.md)**
