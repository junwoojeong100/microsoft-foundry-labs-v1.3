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
| Search 403 | RBAC authentication, actual caller, data roles | Distinguish user, project MI, account MI, and Search MI. Do not enable key authentication as a bypass. |
| Search creation: `ResourcesForSkuUnavailable` | Current regional/SKU capacity versus the earlier failure | Basic creation and keyword retrieval later succeeded in Sweden Central. For a new error, preserve evidence and retry only after a relevant condition changes; see [current setup and history](06-search-iq.md#current-setup-and-historical-capacity-errors). |
| Search creation: `ServiceQuotaExceeded`, `0 out of 0` | Current subscription quota for that SKU | The historical S2 error is not a current Basic blocker. Use the normal quota request process when needed; no automatic tier escalation, additional RBAC roles, or arbitrary deletions to bypass it. |
| Toolbox lists tools but query fails | Downstream Search access | Check the project MI's Index Data Reader and required Service Contributor roles. |
| Toolbox rejects a valid keyless authentication enum | Current SDK `ProjectManagedIdentity` versus legacy `AAD` | Do not assume only `AAD` is valid. Verify the project MI, target, and roles; do not switch to an API key. Standard v1 probe/query/ask passed after this handling was corrected. |
| Only OpenAPI fails | Account MI and API-version arguments | Read the caller and nested error in `openapi plan`; it is not the Toolbox identity. |
| Only Hosted returns 403 | Roles for `instance_identity.principal_id` | Grant the actual remote identity's required roles instead of repeating local login. |
| MAF shows a tool configuration but execution is unverified | Actual `tool_calls`, not the static `tools: function` label | Inspect `name`, `arguments`, `completed`, and `result_text`, plus `tool_execution_verified`. A configured or listed tool is not evidence that it ran. |
| Model/version/region unavailable | Actual availability and quota | Request quota or make an explicit new plan; do not silently replace models mid-run. |
| Historical GPT-6 Luna project `reasoning.effort` 400 / 500 | Account/Playground success did not establish project-API support | The first-pass guide now starts with Sol. Optional Luna comparisons in 02/07 use `account-responses` for both models. Do not recreate this old failure by repeatedly stripping settings or recreating deployments. |
| `Not allowed when agent is specified`, `param: reasoning` | Stored definition versus request body | Store reasoning only in the definition; do not resend it with `agent_reference`. |
| Correct alias but `configure` rejects model | Actual base model/version | The default is GPT-6 Sol / 2026-09-22. Explicitly reuse an existing Sol alias such as `workshop-compare`; do not replace the model behind another alias. |
| `incomplete` / empty text | Did reasoning exhaust the output budget? | Check `WORKSHOP_REASONING_EFFORT=low`, `WORKSHOP_MAX_OUTPUT_TOKENS=32768`, and original `incomplete_details`. |
| `encrypted reasoning` / replay failure after tools | Link between stateless tool results and reasoning items | Use pinned requirements and the code's explicit encrypted-content inclusion; do not arbitrarily remove reasoning. |
| Agent-reference rejected after generation/model change | Saved version versus current settings | Preserve results and create a new owned name; never silently select latest. |
| No File Search upload control in portal | UI, model, region differences | Use 03's SDK path and verify real File Search calls/citations. |
| 429 | Shared quota and concurrent requests | Stop/wait, then retry in a bounded way while preserving comparison conditions. |
| Provider registration or Policy denial | Subscription providers and organizational policy | Use the normal portal registration process where permitted; do not bypass higher-level policies. |
| Access denied / timeout | Approved execution environment and original error | Use the organization's approved support process. Do not weaken shared firewall or certificate protections. |
| Missing File Search citations | Tools and indexing status | Do not count an inline answer as successful retrieval. |
| Historical/current policy confusion | Question date and effective periods | Distinguish KRW 120,000/150,000 and record the real failure. |
| Search feature billing error | Separate Semantic/Knowledge retrieval plans | Distinguish Free feature allowances from Basic service costs; decide explicitly on more spending. |
| Hybrid schema/dimension mismatch | Real embedding dimensions and a new index | No zero/truncated vectors; do not overwrite the original index. |
| IQ Chat check fails | Pinned model/version, Search MI, roles | Resolve the support requirements or mark that preset blocked. |
| Existing label/file/package | Is it a previous real result? | Read it first; use new names for new requests/packages, preserving failures. |
| Benchmark/SDK comparison rejects `code_hash` mismatch | Did coupled code change beyond instructions? | The old/new r2 SDK pair was correctly rejected for this reason. Separate candidate quality from prompt-only improvement; freeze code and collect a fresh matched pair. Never edit hashes or weaken checks. |
| Missing judge/Optimizer results | Evaluator list, all rows, actual inputs | Partial results cannot pass. |
| Earlier legacy Groundedness Optimizer stopped at baseline 1.0 | Was that old run's judge context the original evidence? | Preserve the historical `context=response` failure. Current policy criteria use 1–5 with pass at 4; do not transfer the legacy warning into the new job's results. |
| Red-team ASR contradicts its explanations | Raw scores, `attack_success`, actual rows, and requested count | Keep the original evidence and discrepancy. Do not overwrite row judgments with an aggregate or silently reduce the denominator. |
| Native evaluation refuses an identical target/judge deployment | Actual judge base model, version, and deployment | Use GPT-5.5 / 2026-04-24, different from the GPT-6 Sol target. Fresh labs use `workshop-judge`; explicitly reuse existing GPT-5.5 with `--deployment workshop-optimizer`. Do not weaken checks or replace existing models. |
| First `azd ai connection create` cannot discover ARM context | Empty project or missing prepared azd context | Create the first Application Insights connection through [09's portal steps](09-operations.md#1-create-and-connect-logging-resources), then retry, or use an existing prepared azd environment with the verified project ARM ID and matching endpoint. Do not borrow a different project's connection or recreate resources. |
| No trace | Request after connection, permissions, time range | Wait briefly and query your own request again; local JSON is not a trace. |
| Delayed Memory read | Same store/ID, recorded TTL, and scope | Use bounded reads rather than repeated writes. Retaining a store does not rewrite its configured TTL. |
| Memory store or ownership record already exists | Selected `WORKSHOP_MEMORY_STORE_NAME` | Inspect the preserved owned store or select an unused name under the same prefix. Do not change prefixes, adopt existing assets, or delete records as a bypass. |
| No answer after Routine dispatch | Dispatch/run state and response retention | Distinguish delivery, execution, and response; do not substitute a separate agent call. Always disable the routine. |
| Scheduled Routine returns `conversation_not_found` | Was a user-created conversation supplied in the action? | Both creation scopes failed under the routine actor. Use a fresh disabled timer manifest with static `action.input` and no conversation; preserve failed runs, conversations, and resources. |
| Created timer has no stored input | Persistent `action.input` | Create has no `--input` flag. Use [11's manifest](11-memory-a2a-routines.md#3-routines-prepare-a-disabled-schedule). `dispatch --input` overrides one manual call only. |
| Completed timer phase becomes cancelled after disable | Original `Finished` status, response ID, timer source, completed output | Use `--scheduled --verify-response --response-source telemetry` for the exact `invoke_agent` response and retain `run_phase: cancelled`. Do not treat every cancelled run as successful. |
| Manual Routine response is unavailable through the response API | Exact original response ID and matching telemetry agent/version/project/trace | Use [11's explicit telemetry readback](11-memory-a2a-routines.md#read-the-original-manual-response-from-telemetry) without another inference, keeping manual and scheduled evidence distinct. |
| Policy score or audit is rejected | Original envelope, source hashes, reference_id, all three criteria, and score direction | Keep canonical `result` 1–5 and `reason`, with pass at 4 or above. Do not edit raw evidence to hide IQ projection/reference mismatches. Calibration's 24/24 agreement is not a dev-grading pass. |
| Older semantic criteria passed 8/8 but business checks failed | Semantic scores and structured contracts are different | Preserve that failure. New Hosted IQ deployment version 3 verified business/policy/audit/trace checks; do not retroactively edit old scores. |
| Legitimate extra supporting citations are rejected | Actual diagnostic suite version and required/allowed sets | Version 2 uses explicit `allowed_citations` only for PL05/PL06/PL07. Keep mandatory, known, unique IDs and reject unrelated references. Frozen version-1 results remain readable without edits. |
| PL06 procedure query returns `limit_krw: 150000` | Actual instruction hash and whether an amount was requested | Corrected v2 on the new deployment was verified with `limit_krw: null`. Preserve the old response; deployment version 3 is not a new prompt-preset name. |
| Optimizer completed/exported but reference use is unclear | Original six rows, three pinned judge versions/thresholds, matching calibration | Run local `scripts/audit_optimizer.py`. It rejects wrong scope/references/thresholds without changing originals; do not claim hidden-request capture or improvement. |
| Downloaded file is not in the expected local folder | Is `--target-path` absolute? | Relative paths can resolve against azd `--cwd`. Use [absolute session-archive targets](advanced/session-files.md) before expiry and verify original session/version/hash bindings. |
| D01 gives the right limit but fails policy grounding | Is every detail supported by the actual returned evidence? | A team-lead detail without `APPROVAL-01` caused the original groundedness 5/6. The corrected SDK candidate scored 6/6 per criterion, but preserve the old evidence and do not call a code-mismatched pair prompt-only improvement. |
| Skill readback differs | Original package, exact version, downloaded bytes | Do not edit the download to force equality. |
| Hosted raw capture fails | Actual folder, endpoint, active version | Diagnose preserved stdout/stderr; a failed stream is not successful completion. |
| English command runs Korean data | Placement of `--language en` | Put it before the subcommand, after wrapper options. An English prompt alone does not select the English bundle. |
| English Hosted package rejected as language mismatch | `prepare-hosted` defaults to `ko` | Use `selfstudy.py prepare-hosted --language en` from 08 and verify the package's frozen English profile. This is a subcommand option, not a global `selfstudy.py` flag. |
| English capture sends a Korean question | `capture` defaults to `ko` | Use `selfstudy.py capture --language en` with the exact English service/version and `--confirm-cost`, then the package-aware verifier from 10. |
| Existing Search ledger rejects English corpus | Workspace language/corpus ownership | Keep the existing ledger; start a separate fresh language experiment with distinct owned assets. |

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
