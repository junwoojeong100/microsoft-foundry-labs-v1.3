# 09. Traces, Insights, and operations

**English** | [한국어](../09-operations.md) · [Course home](../../README.md#curriculum) · [Help](checkpoints.md)

**Outcome:** Create your logging environment and trace your own actual requests in Foundry.

**Prerequisites:** The default path needs **03's inline Prompt Agent name, version, and successful invocation**: the target created with `prompt-agent create`, not the File Search agent. If you have only a Hosted Agent, use section 2's alternative. You prepare Application Insights and Log Analytics here.

**Where you work:** Azure/Foundry portals for connections and observations; terminal for registration and a new request.

> **Important:** responses from before the logging connection are not collected retroactively. **Pause** any recurring evaluation at the planned time, even without a result.

<a id="chapter-map"></a>

**Chapter map**

| Step | Result to check |
|---|---|
| [1. Connect logs](#1-create-and-connect-logging-resources) | Actual logging resources, connection, and read access |
| [2. New request](#2-send-a-new-request-after-connecting) | A new post-connection response ID |
| [3. Trace](#3-interpret-what-you-see) | That request's trace and detailed spans |
| [4. Insights](#4-agent-insights) | Actual findings or not-run status |
| [5. Costs](#5-connect-measurements-to-costs) | Service/storage costs beyond tokens |
| [6. Recurring evaluation](#6-bound-recurring-evaluation) | Actual evaluation results and paused status |
| [Completion check](#completion-check) | Observed evidence and stop/retention state |

If logging was prepared early, verify that connection and its roles instead of creating duplicates.

## 1. Create and connect logging resources

1. In the Azure portal, open **Create a resource → Log Analytics workspace** and create one in your workshop subscription/group in **North Central US**.
2. Under **Create a resource → Application Insights**, choose that group, workspace, and **North Central US**.
3. Record each resource's **JSON View → id**. Check for resources automatically created in a different group.
4. In Foundry, open **Agents → Traces → Connect** and select your new Application Insights resource.
5. If Connect is absent, use **Manage → Project details → Connected resources → Add connection → Application Insights**.

<details>
<summary>If connection setup fails or chapter 13 reports ResourceId/credential errors</summary>

### First CLI connection and actual native-SDK requirements

**The verified NC first-connection path used real azd ARM context, not portal bootstrap.** Use the folder prepared by [08's `prepare-hosted --kind runtime`](08-hosted.md#3-prepare-an-isolated-folder-for-the-existing-project) as `--cwd` for `azd ai connection create`; it contains the actual project ARM ID and endpoint. Preparing this context does not require a Hosted deployment or model invocation. Do not borrow another project's environment.

The first native red-team attempt failed with **zero rows because the App Insights connection lacked `ResourceId`**. A created connection is not necessarily usable by the SDK telemetry getter. This SDK path required:

| Connection item | Required actual value |
|---|---|
| Metadata `ResourceId` | The Application Insights resource's full ARM ID |
| Metadata `ApplicationInsightsConnectionString` | That resource's telemetry connection string |
| `APIKey` credential | The **same telemetry connection string** |

Here `APIKey` is **the telemetry credential class required by the installed SDK 2.6.1 getter**, not a model API key. Do not obtain a model key or change Entra model authentication for this fix. A project-managed-identity App Insights connection could be created but was unsupported by that getter. Keep this version-specific telemetry exception separate from model/Search authentication.

The current CLI supports repeated `--metadata KEY=VALUE` plus `--auth-type api-key`/`--key` for this credential. **Treat the actual connection string as private configuration; never expose it in recordings, source control, or shared logs.** After correcting metadata/credentials, a new native run returned six rows. Preserve the failed zero-row attempt.

</details>

A connection does not itself grant permission to read logs. Verify your access:

```bash
python scripts/selfstudy.py resource --kind insights --id "YOUR-APPLICATION-INSIGHTS-ARM-ID"
```

**Register the actual resource ID in local settings**

```bash
python scripts/selfstudy.py resource --kind logs --id "YOUR-LOG-ANALYTICS-ARM-ID"
```

**Read the required-role plan**

```bash
python scripts/selfstudy.py roles --user-object-id "YOUR-USER-OBJECT-ID"
```

`resource --kind logs` reads the actual Azure **`customerId`** and automatically sets **`AZURE_LOG_ANALYTICS_WORKSPACE_ID`**, also recording the current project ARM ID. The workspace GUID is not its resource ARM ID. Do not guess it from a name or put an ARM ID in that variable. Registration does not grant log access or generate a model response.

Verify or grant **Log Analytics Reader** at the needed scope. Organizations with protected tables may also require Privileged Monitoring Data Reader. Do not put tokens or connection strings into shared logs or environment examples.

**Insights has an additional caller:** verify Monitoring Reader for the user/project identity and scoped Privileged Monitoring Data Reader when protected content is needed. Check only the roles needed on this lab's logging resources.

## 2. Send a new request after connecting

**If you have only a Hosted Agent:** instead of the Prompt Agent command below, send **one new request** to its existing version using [08's exact remote-version invocation](08-hosted.md#6-invoke-the-exact-remote-version). Do not redeploy. Find that response's trace, then stop its session.

Invoke the exact agent version recorded in 03:

```bash
python scripts/workshop.py --language en prompt-agent invoke --question "What are the domestic business-trip lodging limit and advance-approval conditions for September 2026?" --output outputs/learner-notes-en/09-trace-response.json
```

Do not overwrite an existing file. Choose a new filename if this one is already used.

**Check:** in **Agents → Traces**, select the agent and a recent time range, then locate the response ID. Collection can take time; wait briefly and refresh.

## 3. Interpret what you see

| Item | Meaning |
|---|---|
| Response ID | Identifier of the actual response |
| Trace ID | Identifier for tracing that execution |
| Span | A step such as model inference or retrieval |
| Tokens/latency/errors | Measured usage, duration, and failures |
| Conversation/session | Conversation history and a Hosted runtime session—not the same concept |

Match the portal's trace and linked response IDs to section 2's response, then expand one execution step. A local JSON file is not proof of a server-side trace.

For Hosted, also create **a new request after connecting logs**. Server-side traces do not necessarily show every internal Python function; add client-side OpenTelemetry instrumentation separately when needed.

## 4. Agent Insights

If available, run one **Insights** scan against a limited time range of your agent's existing synthetic traces.

Before execution, check the model, budget, target agent, and time range. Compare findings with the original trace. **AI-suggested failure patterns and severity are not ground truth.**

If traces, models, or the feature are unavailable, record “Insights not run.” Do not generate unnecessary requests just to populate the screen. See [official Agent Insights guidance](https://learn.microsoft.com/azure/foundry/observability/how-to/agent-insights).

## 5. Connect measurements to costs

| Cost area | What to verify |
|---|---|
| Models | Input/output tokens across all calls, deployment type, and unit prices |
| Search | Always-on Basic charges plus retrieval/feature plans |
| File Search | Storage and tool charges |
| Hosted | Running compute and session/volume retention |
| Evaluation/Optimizer/Insights | Additional evaluation and model calls |
| Logs | Ingestion volume and retention |

`null` usage means unmeasured, not zero. Tokens from only some calls do not establish the actual bill. In Azure **Cost Management → Cost analysis**, filter by the workshop group and review budgets and retention policies.

GPT-6 **reasoning tokens count toward output cost and the output cap**. Do not calculate cost from visible answer length alone. Defaults are `low` / `32768`; the cap is not actual usage.

## 6. Bound recurring evaluation

This section verifies actual recurring evaluation. **If you have no completed trace evaluation, skip the next paragraph's recurring settings and check availability of the Continuous path below.** If neither path is available or you decline the cost, record not run; do not leave a schedule enabled.

If a trace evaluation for your agent has completed, open its recurring settings. First decide the end time and budget, then select a small sample, such as at most five traces per run, and a limited cadence such as hourly.

Verify one actual execution and its sampled data, then **pause at the planned time even if evidence is incomplete**. Enabling the schedule is not evaluation success. Do not leave it running indefinitely while waiting for results. Stopping does not erase charges already incurred.

For a small real-time trial:

1. Choose **Continuous**, one evaluator such as Coherence, and your judge deployment.
2. Set 100% sampling and **at most one run per hour**.
3. Send one synthetic question in the portal Playground.
4. Match the actual evaluation run to its response ID, then **Pause**.

Workshop code defaults to `store=False`; a continuous evaluator that retrieves responses may not evaluate an unstored response. **A trace alone is not proof of an evaluation run.** Store synthetic data only.

<details>
<summary>Only for a Coherence initialization error: historical version findings</summary>

Coherence v1 failed in the earlier NC environment with zero rows and `CoherenceEvaluator.__init__() got an unexpected keyword argument 'is_reasoning_model'`. A separate pinned-v13 rule succeeded. **The new rerun verified catalog v13 before creating its own rule**, retained GPT-5.5/threshold 3/one-run-hourly, graded one original stored response score 5/pass, then paused. Earlier failures remain archived. Do not reproduce the error or change unrelated evaluator versions to v13.

</details>

CLI, portal, and MCP tools can use different identities. If an error names a different Object ID, check authentication context first. Do not grant new roles to an unknown MCP principal as a workaround.

## Completion check

- [ ] I matched a new post-connection response to its actual trace and spans.
- [ ] I distinguished measured usage, unmeasured `null`, and actual billing.
- [ ] I recorded whether Insights/recurring evaluation ran and left enabled schedules paused.

Preserve the evidence and review logging/retention costs.

---

[← 08. Deployment](08-hosted.md) · [Course home](../../README.md#curriculum) · [10. Shared tools →](10-toolbox-skills.md) · [Chapter map ↑](#chapter-map)
