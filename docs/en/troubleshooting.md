# Troubleshooting: do not start by recreating resources

**English** | [한국어](../troubleshooting.md) · [Course home](../../README.md)

**Record the current chapter, last success, actual target/version, and original error.** Do not record or share passwords, tokens, API keys, or company data.

| Symptom | Check first | Next action |
|---|---|---|
| Python/package error | Is `.venv` using Python 3.13? | Activate/install as in 00; do not mix unrelated example SDK environments. |
| Missing `az`, `azd`, or Foundry commands | Tools and `microsoft.foundry` extension | Follow 00/08; do not blindly upgrade an existing working environment. |
| `configure` receives an account ARM ID | Does it include `/projects/...`? | Copy the actual project ID from JSON View. |
| Endpoint mismatch | A model URL or another account/project? | Match the project-home endpoint with its actual custom subdomain. |
| `.env`/shell conflict | Is an older exported variable taking precedence? | Unset only the conflicting variable or use a fresh terminal; do not silently switch projects. |
| 401 / expired sign-in | Matching user, tenant, and subscription | Use normal sign-in/MFA; do not bypass with copied tokens or a new client secret. |
| Model/agent 403 despite Owner | Foundry data roles | Check Foundry User and scope for the actual user/service identity. |
| Search 403 | RBAC/Both authentication, actual caller, data roles | Distinguish user, project MI, account MI, and Search MI. |
| Search creation: `ResourcesForSkuUnavailable` | Regional service capacity; observed for both Basic and Standard S1 in Sweden Central | Not solved by Owner/RBAC or repeated Create. Keep the required region fixed; [record Search-dependent exercises as blocked](06-search-iq.md#if-regional-capacity-or-quota-blocks-creation) until capacity is available. |
| Search creation: `ServiceQuotaExceeded`, `0 out of 0` | Subscription service quota for the selected SKU; observed on the single S2 attempt | No Search service was created. Request the required Search quota through the official process; no further tier escalation, region switch, or extra RBAC roles. Record the attempted SKU/configuration and higher ongoing price before any later approved deployment. Keep Search/IQ/Hybrid and Search-based Toolbox/OpenAPI blocked, not completed through File Search. |
| Toolbox lists tools but query fails | Downstream Search access | Check the project MI's Index Data Reader and required Service Contributor roles. |
| Only OpenAPI fails | Account MI and API-version arguments | Read the caller and nested error in `openapi plan`; it is not the Toolbox identity. |
| Only Hosted returns 403 | Roles for `instance_identity.principal_id` | Grant the actual remote identity's required roles instead of repeating local login. |
| MAF shows a tool configuration but execution is unverified | Actual `tool_calls`, not the static `tools: function` label | Inspect `name`, `arguments`, `completed`, and `result_text`, plus `tool_execution_verified`. A configured or listed tool is not evidence that it ran. |
| Model/version/region unavailable | Actual availability and quota | Request quota or make an explicit new plan; do not silently replace models mid-run. |
| Luna project `reasoning.effort` 400 / 500 | Separate account/Playground and project results | Follow 01's account API test and explicit Sol choice. Do not repeatedly strip reasoning, rename, or recreate. |
| `Not allowed when agent is specified`, `param: reasoning` | Stored definition versus request body | Store reasoning only in the definition; do not resend it with `agent_reference`. |
| Correct alias but `configure` rejects model | Actual base model/version | Starting candidate: GPT-6 Luna / 2026-09-22. Sol requires explicit `--expected-model gpt-6-sol`; an older deployment is not the new model. |
| `incomplete` / empty text | Did reasoning exhaust the output budget? | Check `WORKSHOP_REASONING_EFFORT=low`, `WORKSHOP_MAX_OUTPUT_TOKENS=32768`, and original `incomplete_details`. |
| `encrypted reasoning` / replay failure after tools | Link between stateless tool results and reasoning items | Use pinned requirements and the code's explicit encrypted-content inclusion; do not arbitrarily remove reasoning. |
| Agent-reference rejected after generation/model change | Saved version versus current settings | Preserve results and create a new owned name; never silently select latest. |
| No File Search upload control in portal | UI, model, region differences | Use 03's SDK path and verify real File Search calls/citations. |
| 429 | Shared quota and concurrent requests | Stop/wait, then retry in a bounded way while preserving comparison conditions. |
| Provider registration or Policy denial | Subscription providers and organizational policy | Use the normal portal registration process where permitted; do not bypass higher-level policies. |
| Public access disabled / timeout | Private Link, DNS, caller location | Use an approved network route; do not weaken shared firewall or certificate protections. |
| Missing File Search citations | Tools and indexing status | Do not count an inline answer as successful retrieval. |
| Historical/current policy confusion | Question date and effective periods | Distinguish KRW 120,000/150,000 and record the real failure. |
| Search feature billing error | Separate Semantic/Knowledge retrieval plans | Distinguish Free feature allowances from Basic service costs; decide explicitly on more spending. |
| Hybrid schema/dimension mismatch | Real embedding dimensions and a new index | No zero/truncated vectors; do not overwrite the original index. |
| IQ Chat check fails | Pinned model/version, Search MI, roles | Resolve the support requirements or mark that preset blocked. |
| Existing label/file/package | Is it a previous real result? | Read it first; use new names for new requests/packages, preserving failures. |
| Benchmark frozen-condition error | Model map, code, corpus, API, version, concurrency | Create a new comparable experiment; do not edit raw hashes. |
| Missing judge/Optimizer results | Evaluator list, all rows, actual inputs | Partial results cannot pass. |
| Optimizer stops at a baseline score of 1.0 | Is the actual judge context the original evidence? | If context equals the generated response, preserve the self-grounding finding; do not promote the score as quality evidence. |
| Red-team ASR contradicts its explanations | Raw scores, `attack_success`, actual rows, and requested count | Keep the original evidence and discrepancy. Do not overwrite row judgments with an aggregate or silently reduce the denominator. |
| Native evaluation refuses an identical target/judge deployment | Judge alias versus every actual target deployment | This guard is intentional. If `workshop-compare` is a target, deploy a separate GPT-6 Sol `workshop-judge` and register it with `selfstudy.py model --role judge --deployment workshop-judge`. Do not weaken the guard; model-family bias still remains. |
| First `azd ai connection create` cannot discover ARM context | Empty project or missing prepared azd context | Create the first Application Insights connection through [09's portal steps](09-operations.md#1-create-and-connect-logging-resources), then retry, or use an existing prepared azd environment with the verified project ARM ID and matching endpoint. Do not borrow a different project's connection or recreate resources. |
| No trace | Request after connection, permissions, time range | Wait briefly and query your own request again; local JSON is not a trace. |
| Delayed Memory read | Same store/ID, TTL, and scope | Use bounded reads rather than repeated writes. Retaining the store does not extend the one-hour item TTL. |
| No answer after Routine dispatch | Dispatch/run state and response retention | Distinguish delivery, execution, and response; do not substitute a separate agent call. Always disable the routine. |
| Skill readback differs | Original package, exact version, downloaded bytes | Do not edit the download to force equality. |
| Hosted raw capture fails | Actual folder, endpoint, active version | Diagnose preserved stdout/stderr; a failed stream is not successful completion. |
| English command runs Korean data | Placement of `--language en` | Put it before the subcommand, after wrapper options. An English prompt alone does not select the English bundle. |
| English Hosted package rejected as language mismatch | `prepare-hosted` defaults to `ko` | Use `selfstudy.py prepare-hosted --language en` from 08 and verify the package's frozen English profile. This is a subcommand option, not a global `selfstudy.py` flag. |
| English capture sends a Korean question | `capture` defaults to `ko` | Use `selfstudy.py capture --language en` with the exact English service/version and `--confirm-cost`, then the package-aware verifier from 10. |
| Existing Search ledger rejects English corpus | Workspace language/corpus ownership | Keep the existing ledger; start a separate fresh language experiment with distinct owned assets. |
| Entra app/Fabric/M365 access denied | Additional product/directory permissions | Review 14; Azure Owner cannot force tenant/product enablement. |

## Distinguish execution errors from quality failures

If the concise error is insufficient, add `--debug` once to inspect the original error and request ID. Keep `--language en` and `--debug` **before the workshop subcommand**. A wrapper `--model-deployment` option must precede both. Debug output may include local paths and inputs; do not publish it unreviewed in a video or repository.

A nonzero exit from `collect`, `evaluate`, or `benchmark` can mean the checker **correctly found an incorrect answer**. Separately inspect whether all six responses exist, any requests failed, and any business checks failed.

“Five successful requests out of six” is not “five out of five passed.” Do not fill missing model/judge values with zeros or success.

## Resume safely

Keep project, prefix, language, source, and ownership ledger consistent. Read existing IDs/results before performing **only the next necessary step**.

To move to a different project/prefix or start a separate language experiment, first record or deliberately retain the old resources and use a fresh workshop copy. Do not delete `.selfstudy`, `outputs`, or `.env` to bypass protections.

## Error-report template

```text
Chapter/step:
Last successful step:
Actual project/agent/version:
Command, with secrets excluded:
Error/original response state:
Response/run ID and local file:
Remaining assets and charges:
Next check:
```

Even when blocked, follow [15's stopping and lifecycle review](15-capstone-cleanup.md).
