# Troubleshooting: do not start by recreating resources

**English** | [한국어](../troubleshooting.md) · [Course home](../../README.md)

**Record the current chapter, last success, actual target/version, and original error.** Do not record or share passwords, tokens, API keys, or company data.

For first-time setup or returning to the lab, start with [command/resume guidance](checkpoints.md). Then find **the symptom you actually encountered** below. You do not need to reproduce or fix every historical failure in the validation report.

## Find your symptom

Choose the affected area, then **expand only your symptom**. Each answer follows **check first → next action**. You can also find error codes or command names with browser search (`Ctrl+F` / `Cmd+F`).

- [First-run blockers](#common-first-run-blockers)
- [Installation, terminal, and saved files](#environment)
- [Sign-in, project, and permissions](#identity)
- [Model responses, deployments, and quota](#models)
- [Search, File Search, IQ, and Hybrid](#retrieval)
- [MAF, Toolbox, Skills, and Hosted](#tools)
- [Evaluation, comparison, and Optimizer](#evaluation)
- [Managed AI red teaming and inconsistent verdicts](#managed-safety)
- [Logs, traces, and continuous evaluation](#observability)
- [Memory, Routines, and stopping schedules](#state-schedules)
- [English-language settings](#language)

[Execution versus quality](#distinguish-execution-errors-from-quality-failures) · [Resume safely](#resume-safely) · [Error-report template](#error-report-template)

## Common first-run blockers

<details>
<summary><code>can&#x27;t open file ... scripts/workshop.py</code></summary>

**First action:** Open the folder containing both README and scripts, then use a terminal there

</details>

<details>
<summary>Missing <code>python</code> or packages</summary>

**First action:** Follow 00's OS-specific installation and `.venv` activation; do not weaken PowerShell policy

</details>

<details>
<summary>Asked to run Lab 00&#x27;s configure</summary>

**First action:** `values` is not an installation command; complete project/deployment/configure in 00

</details>

<details>
<summary>Rejected <code>YOUR-...</code> / <code>ACTUAL-...</code></summary>

**First action:** Replace placeholders with preceding steps' actual values; distinguish endpoint and ARM ID

</details>

<details>
<summary>No prompt after a server command</summary>

**First action:** This can be normal; leave A running and use B in the same environment for checks

</details>

<details>
<summary><code>azd</code> cannot find <code>azure.yaml</code> or shows the wrong service</summary>

**First action:** Use the absolute **preparation folder** printed in 08 as `--cwd`, not the `.build` package or repository root

</details>

<details>
<summary>Windows: <code>No module named &#x27;fcntl&#x27;</code></summary>

**First action:** 05's local SDK experiment needs macOS/Linux; use approved WSL/Linux or record that section not run

</details>

<details>
<summary>CI preflight reports missing identifiers</summary>

**First action:** First populate **the exact `foundry-workshop` Environment → Variables** in 14, not only Secrets

</details>

<details>
<summary>No checks after forking or no <code>Run workflow</code> button</summary>

**First action:** Check Actions enablement, workflow files on your repository's `main`, and execution permission; start with 14's manual Workshop checks

</details>

<details>
<summary>OIDC reports no matching federated credential</summary>

**First action:** Match 14's actual issuer/subject/audience, including immutable IDs and the Environment subject; do not bypass with a client secret

</details>

<details>
<summary>Stopping during setup but <code>status</code> requires configure</summary>

**First action:** Azure resources may exist without local settings; use 15's pre-configuration stopping path and inspect the actual portal

</details>

<details>
<summary>JSON syntax error in <code>azure.yaml</code></summary>

**First action:** Put 13's `policies` inside the actual agent service; check commas/braces and do not mix YAML into JSON

</details>

<details>
<summary>Failed native score but an old acceptance report says <code>gate_passed: true</code></summary>

**First action:** Recheck saved evidence using 15's command with `--require-native-pass`; managed red-team audit remains separate

</details>

## Azure, model, and tool errors

The reference validation's new Task Adherence run returned six rows/five pass/one fail; inconsistent severity/flags hold acceptance. Distinguish the [current report](validation-report.md) from history and preserve your own failures.

<a id="environment"></a>

### Installation, terminal, and saved files

<details>
<summary>Python/package error</summary>

**Check first:** Is `.venv` using Python 3.13?

**Next action:** Activate/install as in 00; do not mix unrelated example SDK environments.

</details>

<details>
<summary>Missing <code>az</code>, <code>azd</code>, or Foundry commands</summary>

**Check first:** Tools and `microsoft.foundry` extension

**Next action:** Follow 00/08; do not blindly upgrade an existing working environment.

</details>

<details>
<summary><code>.env</code>/shell conflict</summary>

**Check first:** Is an older exported variable taking precedence?

**Next action:** Unset only the conflicting variable or use a fresh terminal; do not silently switch projects.

</details>

<details>
<summary>Existing label/file/package</summary>

**Check first:** Is it a previous real result?

**Next action:** Read it first; use new names for new requests/packages, preserving failures.

</details>

<a id="identity"></a>

### Sign-in, project, and permissions

<details>
<summary><code>configure</code> receives an account ARM ID</summary>

**Check first:** Does it include `/projects/...`?

**Next action:** Copy the actual project ID from JSON View.

</details>

<details>
<summary>Endpoint mismatch</summary>

**Check first:** A model URL or another account/project?

**Next action:** Match the project-home endpoint with its actual custom subdomain.

</details>

<details>
<summary>401 / expired sign-in</summary>

**Check first:** Matching user, tenant, and subscription

**Next action:** Use normal sign-in/MFA; do not bypass with copied tokens or a new client secret.

</details>

<details>
<summary>Model/agent 403 despite Owner</summary>

**Check first:** Foundry data roles

**Next action:** Check Foundry User and scope for the actual user/service identity.

</details>

<details>
<summary>Only Hosted returns 403</summary>

**Check first:** Roles for `instance_identity.principal_id`

**Next action:** Grant the actual remote identity's required roles instead of repeating local login.

</details>

<details>
<summary>Provider registration or Policy denial</summary>

**Check first:** Subscription providers and organizational policy

**Next action:** Use the normal portal registration process where permitted; do not bypass higher-level policies.

</details>

<details>
<summary>Access denied / timeout</summary>

**Check first:** Approved execution environment and original error

**Next action:** Use the organization's approved support process. Do not weaken shared firewall or certificate protections.

</details>

<details>
<summary>First <code>azd ai connection create</code> cannot discover ARM context</summary>

**Check first:** Is actual project ARM context prepared?

**Next action:** Use `--cwd` with the real environment from `prepare-hosted --kind runtime`, as in [09](09-operations.md). This worked in NC without portal bootstrap; do not borrow another project's environment.

</details>

<a id="models"></a>

### Model responses, deployments, and quota

<details>
<summary>Model/version/region unavailable</summary>

**Check first:** Actual availability and quota

**Next action:** Request quota or make an explicit new plan; do not silently replace models mid-run.

</details>

<details>
<summary>Historical GPT-6 Luna project <code>reasoning.effort</code> 400 / 500</summary>

**Check first:** Account/Playground success did not establish project-API support

**Next action:** The first-pass guide now starts with Sol. Optional Luna comparisons in 02/07 use `account-responses` for both models. Do not recreate this old failure by repeatedly stripping settings or recreating deployments.

</details>

<details>
<summary><code>Not allowed when agent is specified</code>, <code>param: reasoning</code></summary>

**Check first:** Stored definition versus request body

**Next action:** Store reasoning only in the definition; do not resend it with `agent_reference`.

</details>

<details>
<summary>Correct alias but <code>configure</code> rejects model</summary>

**Check first:** Actual base model/version

**Next action:** The default is GPT-6 Sol / 2026-09-22. Explicitly reuse an existing Sol alias such as `workshop-compare`; do not replace the model behind another alias.

</details>

<details>
<summary><code>incomplete</code> / empty text</summary>

**Check first:** Did reasoning exhaust the output budget?

**Next action:** Check `WORKSHOP_REASONING_EFFORT=low`, `WORKSHOP_MAX_OUTPUT_TOKENS=32768`, and original `incomplete_details`.

</details>

<details>
<summary><code>encrypted reasoning</code> / replay failure after tools</summary>

**Check first:** Link between stateless tool results and reasoning items

**Next action:** Use pinned requirements and the code's explicit encrypted-content inclusion; do not arbitrarily remove reasoning.

</details>

<details>
<summary>Agent-reference rejected after generation/model change</summary>

**Check first:** Saved version versus current settings

**Next action:** Preserve results and create a new owned name; never silently select latest.

</details>

<details>
<summary>429</summary>

**Check first:** Shared quota and concurrent requests

**Next action:** Stop/wait, then retry in a bounded way while preserving comparison conditions.

</details>

<a id="retrieval"></a>

### Search, File Search, IQ, and Hybrid

<details>
<summary>Search 403</summary>

**Check first:** RBAC authentication, actual caller, data roles

**Next action:** Distinguish user, project MI, account MI, and Search MI. Do not enable key authentication as a bypass.

</details>

<details>
<summary>Search creation: <code>ResourcesForSkuUnavailable</code></summary>

**Check first:** Actual availability for the new NC region/SKU

**Next action:** Sweden failure/recovery is historical. Check NC independently and retry only after relevant conditions change; do not silently switch regions or adopt earlier results.

</details>

<details>
<summary>Search creation: <code>ServiceQuotaExceeded</code>, <code>0 out of 0</code></summary>

**Check first:** Current subscription quota for that SKU

**Next action:** The historical S2 error is not a current Basic blocker. Use the normal quota request process when needed; no automatic tier escalation, additional RBAC roles, or arbitrary deletions to bypass it.

</details>

<details>
<summary>No File Search upload control in portal</summary>

**Check first:** UI, model, region differences

**Next action:** Use 03's SDK path and verify real File Search calls/citations.

</details>

<details>
<summary>Missing File Search citations</summary>

**Check first:** Tools and indexing status

**Next action:** Do not count an inline answer as successful retrieval.

</details>

<details>
<summary>Historical/current policy confusion</summary>

**Check first:** Question date and effective periods

**Next action:** Distinguish KRW 120,000/150,000 and record the real failure.

</details>

<details>
<summary>Search feature billing error</summary>

**Check first:** Separate Semantic/Knowledge retrieval plans

**Next action:** Distinguish Free feature allowances from Basic service costs; decide explicitly on more spending.

</details>

<details>
<summary>Hybrid schema/dimension mismatch</summary>

**Check first:** Real embedding dimensions and a new index

**Next action:** No zero/truncated vectors; do not overwrite the original index.

</details>

<details>
<summary>IQ Chat check fails</summary>

**Check first:** Pinned model/version, Search MI, roles

**Next action:** Resolve the support requirements or mark that preset blocked.

</details>

<details>
<summary>English IQ dev D05 omits <code>SCOPE-01</code></summary>

**Check first:** Actual returned sources and reranker filtering

**Next action:** Explicitly use chapter 06's threshold 0 for the small synthetic corpus and collect all dev cases under a new label. Preserve the original 5/6 and sources; do not weaken citation requirements.

</details>

<a id="tools"></a>

### MAF, Toolbox, Skills, and Hosted

<details>
<summary>Toolbox lists tools but query fails</summary>

**Check first:** Downstream Search access

**Next action:** Check the project MI's Index Data Reader and required Service Contributor roles.

</details>

<details>
<summary>Toolbox rejects a valid keyless authentication enum</summary>

**Check first:** Current SDK `ProjectManagedIdentity` versus legacy `AAD`

**Next action:** Do not assume only `AAD` is valid. Verify the project MI, target, and roles; do not switch to an API key. Standard v1 probe/query/ask passed after this handling was corrected.

</details>

<details>
<summary>Only OpenAPI fails</summary>

**Check first:** Account MI and API-version arguments

**Next action:** Read the caller and nested error in `openapi plan`; it is not the Toolbox identity.

</details>

<details>
<summary>Inferring all MAF support from NC Function=no</summary>

**Check first:** Managed Agent Service tools versus local model/function execution

**Next action:** NC FoundryChatClient + local `lookup_policy` and MCP actually succeeded. This does not guarantee all managed Function tools; distinguish [04's](04-tools.md) actual paths and results.

</details>

<details>
<summary>Skill readback differs</summary>

**Check first:** Original package, exact version, downloaded bytes

**Next action:** Do not edit the download to force equality.

</details>

<details>
<summary>Hosted raw capture fails</summary>

**Check first:** Actual folder, endpoint, active version

**Next action:** Diagnose preserved stdout/stderr; a failed stream is not successful completion.

</details>

<details>
<summary>Downloaded file is not in the expected local folder</summary>

**Check first:** Is `--target-path` absolute?

**Next action:** Relative paths can resolve against azd `--cwd`. Use [absolute session-archive targets](advanced/session-files.md) before expiry and verify original session/version/hash bindings.

</details>

<details>
<summary>MAF shows a tool configuration but execution is unverified</summary>

**Check first:** Actual `tool_calls`, not the static `tools: function` label

**Next action:** Inspect `name`, `arguments`, `completed`, and `result_text`, plus `tool_execution_verified`. A configured or listed tool is not evidence that it ran.

</details>

<a id="evaluation"></a>

### Evaluation, comparison, and Optimizer

<details>
<summary>Benchmark/SDK comparison rejects <code>code_hash</code> mismatch</summary>

**Check first:** Did coupled code change beyond instructions?

**Next action:** The old/new r2 SDK pair was correctly rejected for this reason. Separate candidate quality from prompt-only improvement; freeze code and collect a fresh matched pair. Never edit hashes or weaken checks.

</details>

<details>
<summary>Missing judge/Optimizer results</summary>

**Check first:** Evaluator list, all rows, actual inputs

**Next action:** Partial results cannot pass.

</details>

<details>
<summary>NC Optimizer: <code>MissingRequiredParameter: pass_threshold</code></summary>

**Check first:** Sending name/version without per-evaluator initialization

**Next action:** Bind the calibration catalog's `initialization_parameters` and preserve them with the SDK mapping constructor. Chapter 12 verifies a new job and both six-row audits using original versions/threshold 4; the original failure remains.

</details>

<details>
<summary>Optimizer local <code>details.job_id</code> error</summary>

**Check first:** Is `poller.details` a mapping?

**Next action:** SDK 2.6.1 uses `details["job_id"]`. A server job may already exist: retrieve the exact target/job rather than creating again.

</details>

<details>
<summary>Earlier legacy Groundedness Optimizer stopped at baseline 1.0</summary>

**Check first:** Was that old run's judge context the original evidence?

**Next action:** Preserve the historical `context=response` failure. Current policy criteria use 1–5 with pass at 4; do not transfer the legacy warning into the new job's results.

</details>

<details>
<summary>Native evaluation refuses an identical target/judge deployment</summary>

**Check first:** Actual judge base model, version, and deployment

**Next action:** Use GPT-5.5 / 2026-04-24, different from the GPT-6 Sol target. Fresh labs use `workshop-judge`; explicitly reuse existing GPT-5.5 with `--deployment workshop-optimizer`. Do not weaken checks or replace existing models.

</details>

<details>
<summary>Policy score or audit is rejected</summary>

**Check first:** Original envelope, source hashes, reference_id, all three criteria, and score direction

**Next action:** Keep canonical `result` 1–5 and `reason`, with pass at 4 or above. Do not edit raw evidence to hide IQ projection/reference mismatches. Calibration's 24/24 agreement is not a dev-grading pass.

</details>

<details>
<summary>Older semantic criteria passed 8/8 but business checks failed</summary>

**Check first:** Semantic scores and structured contracts are different

**Next action:** Preserve the old Sweden failure and later v3 results. Neither becomes an NC or managed AI red-team result through relabeling.

</details>

<details>
<summary>Legitimate extra supporting citations are rejected</summary>

**Check first:** Actual diagnostic suite version and required/allowed sets

**Next action:** Version 2 uses explicit `allowed_citations` only for PL05/PL06/PL07. Keep mandatory, known, unique IDs and reject unrelated references. Frozen version-1 results remain readable without edits.

</details>

<details>
<summary>PL06 procedure query returns <code>limit_krw: 150000</code></summary>

**Check first:** Actual instruction hash and whether an amount was requested

**Next action:** Corrected v2 on the new deployment was verified with `limit_krw: null`. Preserve the old response; deployment version 3 is not a new prompt-preset name.

</details>

<details>
<summary>Optimizer completed/exported but reference use is unclear</summary>

**Check first:** Original six rows, three pinned judge versions/thresholds, matching calibration

**Next action:** Run local `scripts/audit_optimizer.py`. It rejects wrong scope/references/thresholds without changing originals; do not claim hidden-request capture or improvement.

</details>

<details>
<summary>D01 gives the right limit but fails policy grounding</summary>

**Check first:** Is every detail supported by the actual returned evidence?

**Next action:** A team-lead detail without `APPROVAL-01` caused the original groundedness 5/6. The corrected SDK candidate scored 6/6 per criterion, but preserve the old evidence and do not call a code-mismatched pair prompt-only improvement.

</details>

<a id="managed-safety"></a>

### Managed AI red teaming and inconsistent verdicts

<details>
<summary>Managed AI red-team regional descriptions conflict</summary>

**Check first:** Read both official matrix and concept overview

**Next action:** The matrix lists East US 2/NC; the overview also lists France, Sweden, and Switzerland West. NC is common, but Sweden non-support or a regional ASR cause is not established. See [13](13-governance.md).

</details>

<details>
<summary>Historical Sweden red-team ASR contradicted explanations</summary>

**Check first:** Original flags, counts, reasons, and metric meaning

**Next action:** Preserve it as unvalidated native ASR. Neither custom 8/8 nor moving to NC proves metric direction fixed; verify the actual NC job separately.

</details>

<details>
<summary>Taxonomy sample fails with <code>body=</code></summary>

**Check first:** Installed SDK version and that method's signature

**Next action:** SDK 2.6.1 taxonomy creation uses `taxonomy=`. Record the sample/version mismatch; do not hide the error or repeatedly recreate resources.

</details>

<details>
<summary><code>num_turns</code> differs from returned rows</summary>

**Check first:** Turn depth versus actual seed/objective count

**Next action:** `num_turns` is not a case count. Record submitted seeds, actual requests, and returned/scored rows separately; do not guess a denominator.

</details>

<details>
<summary>Native Prohibited Actions direction is unclear</summary>

**Check first:** Exact evaluator version, schema, and initialization

**Next action:** Catalog v5 boolean/increase differs from pinned v1 ordinal 0–7/decrease. V1 requires `azure_ai_project`. Use English single-turn/tool-level scope and do not claim ASR fixed before actual results.

</details>

<details>
<summary>Initial native red-team attempt failed with zero rows</summary>

**Check first:** App Insights metadata and SDK credential support

**Next action:** Verify `ResourceId`, `ApplicationInsightsConnectionString`, and an `APIKey` credential carrying the telemetry connection string. A created project-MI connection did not mean this SDK getter supported it. This is not a model API-key change.

</details>

<details>
<summary>Taxonomy update loses its ID</summary>

**Check first:** Does typed serialization retain read-only `id`?

**Next action:** Reviewed `reviewed.as_dict()` payload retained the original ID and created version 2.0. Do not invent IDs, broaden policy, or erase the original failure.

</details>

<details>
<summary>Native score 0 has different flags</summary>

**Check first:** Per-evaluator raw score, flags, and reason

**Next action:** One Prohibited Actions item is 0/false/true despite Safe/NoDefect; five Task Adherence items are consistently 0/true/false. Preserve five pass/one fail, not 0/6 or an ASR-fix claim.

</details>

<details>
<summary>Prohibited Actions polarity persists after v1 pinning/NC relocation</summary>

**Check first:** Requested version versus actual native-engine output

**Next action:** Neither action resolved the observed inconsistency. Verify a fresh Task Adherence-only native job separately; do not delete the original failed row or substitute custom results.

</details>

<a id="observability"></a>

### Logs, traces, and continuous evaluation

<details>
<summary>Continuous Coherence v1: <code>is_reasoning_model</code> initialization error</summary>

**Check first:** Actual catalog version and service evaluator ABI

**Next action:** In NC, a separate v13 run passed 1/1 with the same judge/threshold. Keep the v1 zero-row failure and original response, and pause both rules. Do not change unrelated evaluator versions.

</details>

<details>
<summary>No trace</summary>

**Check first:** Request after connection, permissions, time range

**Next action:** Wait briefly and query your own request again; local JSON is not a trace.

</details>

<a id="state-schedules"></a>

### Memory, Routines, and stopping schedules

<details>
<summary>Delayed Memory read</summary>

**Check first:** Same store/ID, recorded TTL, and scope

**Next action:** Use bounded reads rather than repeated writes. Retaining a store does not rewrite its configured TTL.

</details>

<details>
<summary>Memory store or ownership record already exists</summary>

**Check first:** Selected `WORKSHOP_MEMORY_STORE_NAME`

**Next action:** Inspect the preserved owned store or select an unused name under the same prefix. Do not change prefixes, adopt existing assets, or delete records as a bypass.

</details>

<details>
<summary>No answer after Routine dispatch</summary>

**Check first:** Dispatch/run state and response retention

**Next action:** Distinguish delivery, execution, and response; do not substitute a separate agent call. Always disable the routine.

</details>

<details>
<summary><code>azd ai routine run list</code> is empty despite apparent timer delivery</summary>

**Check first:** Native history for the exact routine name

**Next action:** Disable first, then export all attempts/IDs with `scripts/routine_runs.py`. In NC, SDK history and original telemetry verified the delivery without another dispatch.

</details>

<details>
<summary>Scheduled Routine returns <code>conversation_not_found</code></summary>

**Check first:** Was a user-created conversation supplied in the action?

**Next action:** Both creation scopes failed under the routine actor. Use a fresh disabled timer manifest with static `action.input` and no conversation; preserve failed runs, conversations, and resources.

</details>

<details>
<summary>Created timer has no stored input</summary>

**Check first:** Persistent `action.input`

**Next action:** Create has no `--input` flag. Use [11's manifest](11-memory-a2a-routines.md#3-routines-prepare-a-disabled-schedule). `dispatch --input` overrides one manual call only.

</details>

<details>
<summary>Completed timer phase becomes cancelled after disable</summary>

**Check first:** Original `Finished` status, response ID, timer source, completed output

**Next action:** Use `--scheduled --verify-response --response-source telemetry` for the exact `invoke_agent` response and retain `run_phase: cancelled`. Do not treat every cancelled run as successful.

</details>

<details>
<summary>Manual Routine response is unavailable through the response API</summary>

**Check first:** Exact original response ID and matching telemetry agent/version/project/trace

**Next action:** Use [11's explicit telemetry readback](11-memory-a2a-routines.md#read-the-original-manual-response-from-telemetry) without another inference, keeping manual and scheduled evidence distinct.

</details>

<a id="language"></a>

### English-language settings

<details>
<summary>English command runs Korean data</summary>

**Check first:** Placement of `--language en`

**Next action:** Put it before the subcommand, after wrapper options. An English prompt alone does not select the English bundle.

</details>

<details>
<summary>English Hosted package rejected as language mismatch</summary>

**Check first:** `prepare-hosted` defaults to `ko`

**Next action:** Use `selfstudy.py prepare-hosted --language en` from 08 and verify the package's frozen English profile. This is a subcommand option, not a global `selfstudy.py` flag.

</details>

<details>
<summary>English capture sends a Korean question</summary>

**Check first:** `capture` defaults to `ko`

**Next action:** Use `selfstudy.py capture --language en` with the exact English service/version and `--confirm-cost`, then the package-aware verifier from 10.

</details>

<details>
<summary>Existing Search ledger rejects English corpus</summary>

**Check first:** Workspace language/corpus ownership

**Next action:** Keep the existing ledger; start a separate fresh language experiment with distinct owned assets.

</details>

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

---

[Find your symptom ↑](#find-your-symptom) · [Progress help](checkpoints.md) · [Stop work and review costs](15-capstone-cleanup.md#4-stop-running-work-first)
