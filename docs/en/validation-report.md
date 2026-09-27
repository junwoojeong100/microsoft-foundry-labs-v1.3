# Live validation: Sweden Central

**English** | [한국어](../validation-report.md) · [Course home](../../README.md)

**The guide was executed in a fresh dedicated environment on September 27–28, 2026.** Execution, business checks, and traces were verified without relabeling Search capacity blockers or inconsistent evaluation results as success.

The group is `rg-mf15-jw-0927-e2e`, region `swedencentral`, and project `mf15-project`. Created resources were retained as requested. Private subscription/tenant IDs, endpoint configuration, and original evidence remain in `.selfstudy/`, `.env`, and `outputs/`, outside the repository bundle.

## Coverage

| Area | Actual outcome |
|---|---|
| Setup and models | New group, Foundry, project, deployments, and RBAC. Luna account API/Playground worked; its project API returned 400/500. Sol project inference was verified and explicitly selected |
| Comparison | Same account Responses API, prompts, questions, and evidence: Luna/Sol dev 6/6 each. Prompt baseline/candidate also 6/6, so no pass-rate improvement was established |
| Files and tools | Six File Search files per language with current/historical/missing-evidence citations. Real function/MCP execution, six-row Code Interpreter CSV, and Skill upload/readback |
| Workflows | Sequential, concurrent, Group Chat, and actual SDK pause/resume. Simulated approval is not business authorization |
| Hosted | Real Korean/English versions deployed and remotely invoked; six Hosted evaluation tasks per language and complete output exports. Actual runtime identities were used |
| State and delegation | Korean/English managed-memory recall, synthetic scope separation, and A2A 1.0/JSONRPC. Not represented as real-user authorization testing |
| Scheduling | One actual manual dispatch completed and the routine was disabled. Response-readback failure and untested future timer firing remain separate |
| Operations | Actual App Insights request queries. Insights analyzed seven real traces and returned zero findings, not a health guarantee. One continuous evaluation completed, then paused |
| Governance | A separate RAI policy preserved 11 default protections and was referenced by a separate Hosted v2. Normal/boundary responses were checked; instruction refusal was not called platform filtering |
| CI/CD | Dedicated secretless MI, actual immutable OIDC subject, `main`-only environment. The verified commit deployed English agent v1, assigned only its project-scoped runtime role, passed 6/6 dev cases, and stopped the session |

[GitHub checks](https://github.com/junwoojeong100/microsoft-foundry-v1.5-labs/actions/runs/36336934973) and the [approved OIDC release](https://github.com/junwoojeong100/microsoft-foundry-v1.5-labs/actions/runs/36337095039) succeeded on commit `24ea3be`. Downloaded artifacts were checked for the actual version, six responses, role scope, and `persistent_files_deleted: false`. The video's CI scene records configuration before this release ran.

## Final Hosted acceptance

The provider was explicitly **local** retrieval, with a **sequential** workflow, **account-chat** model API, and remote **Invocations** protocol.

| Evidence | Result |
|---|---|
| Baseline v1 dev | 12/12 business checks, zero request errors |
| Candidate v2 dev | 12/12 business checks, zero request errors |
| Frozen v2 holdout, executed once | 8/8 business checks, zero request errors |
| Server-side traces | All 12 + 12 + 8 = 32 exports verified |
| Judge calibration | 2/2 known good/bad examples distinguished |
| Native quality | Groundedness passed; D05/H04 Relevance findings retained |
| Final recommendation | `review-native-findings`, `deployment_approved: false` |

This is acceptance for a small synthetic exercise, not every native metric passing, a statistical model ranking, an SLA, or production approval. The English runtime had separate dev/smoke checks; the shared Korean holdout was not relabeled as a new English test.

## Outcomes not labeled successful

**Search/IQ/Hybrid and Search-based Toolbox/OpenAPI:** Basic and S1 returned regional `ResourcesForSkuUnavailable`; S2 had service quota `0/0`. No other region or shared service was silently substituted. The local matrix is a separate path, not IQ validation.

**Prompt Optimizer:** the instruction-only run stopped at a baseline score of 1.0, but all six judge contexts were the generated responses themselves. That self-grounding is invalid quality evidence. No improvement or promotion was claimed.

**Red teaming:** five seeds were selected in the UI, but only three rows returned. The 100% ASR/`attack_success: true` conflicted with raw explanations reporting no prohibited action. Inputs were also redacted. Counts, scores, and explanations were preserved; the aggregate was not treated as a trustworthy attack-success rate.

**Additional products:** Fabric, Microsoft 365/Work IQ, Agent 365, and similar separately licensed/data-bound integrations were not claimed as implemented. Existing corporate mail, meetings, and business data were not accessed.

## Improvements incorporated

Agent-definition reasoning was separated from invocation options. Explicit account Responses selection, actual tool-execution evidence, A2A `base_url` and owned-version repair, English Hosted preparation/capture, local matrix support, continuous-run export IDs, and non-expiring File Search retention were added. Both language guides and command contracts are checked, and packaging allows only curated videos from the designated media folder.

**Retention:** resources, agent versions, files, evaluations, and ownership records remain. Unneeded execution sessions were stopped and schedules/monitors disabled. Memory-item TTLs and managed-session expiration are not indefinite preservation; retained storage and logs may still incur charges.

The resource group's Cost Management `ActualCost` query had no posted rows yet. Billing can lag; this does not establish a total cost of zero.
