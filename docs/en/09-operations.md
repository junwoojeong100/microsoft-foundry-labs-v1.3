# 09. Traces, Insights, and operations

**English** | [한국어](../09-operations.md) · [Course home](../../README.md)

**Outcome:** Create your logging environment and trace your own actual requests in Foundry.

**Prerequisites:** A Prompt Agent from 03 or Hosted Agent from 08. You prepare Application Insights and Log Analytics here.

## 1. Create and connect logging resources

1. In the Azure portal, open **Create a resource → Log Analytics workspace** and create one in your workshop subscription/group.
2. Under **Create a resource → Application Insights**, choose that group, workspace, and an appropriate region.
3. Record each resource's **JSON View → id**. Check for resources automatically created in a different group.
4. In Foundry, open **Agents → Traces → Connect** and select your new Application Insights resource.
5. If Connect is absent, use **Manage → Project details → Connected resources → Add connection → Application Insights**.

**First connection in an empty project:** If `azd ai connection create` cannot discover the project's ARM context, create the first Application Insights connection through the portal steps above, then retry in the same project. Alternatively, use the [prepared azd environment from 08](08-hosted.md#3-prepare-an-isolated-folder-for-the-existing-project), which contains the verified `AZURE_AI_PROJECT_ID` and matching endpoint. Do not borrow another project's connection, guess an ARM ID, or recreate the project to bypass discovery.

A connection does not itself grant permission to read logs. Verify your access:

```bash
python scripts/selfstudy.py resource --kind insights --id "YOUR-APPLICATION-INSIGHTS-ARM-ID"
python scripts/selfstudy.py resource --kind logs --id "YOUR-LOG-ANALYTICS-ARM-ID"
python scripts/selfstudy.py roles --user-object-id "YOUR-USER-OBJECT-ID"
```

Verify or grant **Log Analytics Reader** at the needed scope. Organizations with protected tables may also require Privileged Monitoring Data Reader. Do not put tokens or connection strings into shared logs or environment examples.

**Insights has an additional caller:** both the interactive user and the **project managed identity** need **Monitoring Reader** on this Application Insights resource. If protected content such as `AppGenAIContent` is read, verify **Privileged Monitoring Data Reader** for both identities at the appropriate scope. In live validation, ordinary trace queries succeeded while Insights returned a dependency 403 until these scoped roles were present. Do not broaden them to the whole subscription.

## 2. Send a new request after connecting

Invoke the exact agent version recorded in 03:

```bash
python scripts/workshop.py --language en prompt-agent invoke --question "What are the domestic business-trip lodging limit and advance-approval conditions for September 2026?" --output outputs/learner-notes-en/09-trace-response.json
```

Do not overwrite an existing file. Choose a new filename if this one is already used.

In **Agents → Traces**, select the agent and a recent time range, then locate the response ID. Collection can take time; wait briefly and refresh.

## 3. Interpret what you see

| Item | Meaning |
|---|---|
| Response ID | Identifier of the actual response |
| Trace ID | Identifier for tracing that execution |
| Span | A step such as model inference or retrieval |
| Tokens/latency/errors | Measured usage, duration, and failures |
| Conversation/session | Conversation history and a Hosted runtime session—not the same concept |

Record your trace ID, linked response ID, and one observed step. A local JSON file is not proof of a server-side trace.

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

If a trace evaluation for your agent has completed, open its recurring settings. First decide the end time and budget, then select a small sample, such as at most five traces per run, and a limited cadence such as hourly.

Verify one actual execution and its sampled data, then **pause at the planned time even if evidence is incomplete**. Enabling the schedule is not evaluation success. Do not leave it running indefinitely while waiting for results. Stopping does not erase charges already incurred.

For a small real-time trial, choose **Continuous**, one evaluator such as Coherence, your judge deployment, 100% sampling, and **at most one run per hour**. Send one synthetic question in the portal Playground, match the actual evaluation run to its response ID, and Pause. Workshop code defaults to `store=False`; a continuous evaluator that retrieves responses may not evaluate an unstored response. A trace alone is not proof of an evaluation run. Store synthetic data only.

CLI, portal, and MCP tools can use different identities. If an error names a different Object ID, check authentication context first. Do not grant new roles to an unknown MCP principal as a workaround.

**Completion:** Record real traces and measurements, whether Insights/recurring evaluation actually ran, and the stop/retention plan.

**Next → [10. Toolbox, Tool Search, Skills, and OpenAPI](10-toolbox-skills.md)**
