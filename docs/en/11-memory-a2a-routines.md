# 11. Memory, A2A, and Routines

**English** | [한국어](../11-memory-a2a-routines.md) · [Course home](../../README.md)

**Outcome:** Create, use, and verify memory storage, delegation to another agent, and scheduled execution, then explicitly stop, retain, or remove what you own.

**Prerequisites:** Project identity roles from 00, the embedding deployment from 06, and the azd Foundry extension from 08. Review creation and request costs for each feature.

**These are three separate experiments:** storing/recalling an item, delegating to another agent, and running at a scheduled time. **Always disable the Routine at the end.** Record scheduled delivery separately from verification of its actual answer.

## 1. Memory: persist an item and recall it in a new request

Verify `workshop-embedding` from 06 and select a **new retained-store name under the current prefix**. Replace `YOUR-PREFIX` with your actual `WORKSHOP_PREFIX`. If an older store exists, preserve its settings and records:

```bash
python scripts/selfstudy.py status
python scripts/selfstudy.py set WORKSHOP_MEMORY_STORE_NAME "YOUR-PREFIX-memory-retained-en"
python scripts/workshop.py --language en memory plan
```

Inspect the plan's actual name, Sol/embedding deployments, and `default_ttl_seconds: 0`. This is a **local creation proposal**, not a read or update of an existing remote store's TTL.

**The new default TTL is 0: no automatic memory-item expiry.** Pass that choice explicitly when creating the store, then add an item:

```bash
python scripts/workshop.py --language en memory create --ttl-seconds 0 --confirm-create
python scripts/workshop.py --language en memory put --scope alpha --case D02 --confirm-write --confirm-cost
```

Record the **new store name, memory_id, and ownership file**. Verify `default_ttl_seconds: 0` in the creation readback and `automatic_expiration_enabled: false`. This verifies configuration, not a long-duration survival test. Storage charges may continue.

For another **new store** that should expire items, `--ttl-seconds` accepts 1–31,536,000 seconds (365 days). Previously recorded stores keep their original TTL; the new default does not update them. If your selected store already exists with an ownership record, do not create it again: inspect and recall it. For another new run, choose an unused name under the same prefix, without adopting unrecorded remote assets.

`WORKSHOP_MEMORY_STORE_NAME` is a **global selector, not an automatic per-language setting**. Explicitly select `<prefix>-memory-retained-en` for English and `<prefix>-memory-retained-ko` for Korean. Recheck it whenever switching languages; `--language en` alone does not switch an explicitly selected store.

```bash
python scripts/workshop.py --language en memory inspect --scope alpha
python scripts/workshop.py --language en memory inspect --scope beta
python scripts/workshop.py --language en memory recall --scope alpha --label memory-retained-alpha-en --confirm-cost
python scripts/workshop.py --language en memory recall --scope beta --label memory-retained-beta-en --confirm-cost
```

Verify that alpha retains the item across independent commands and beta does not contain it. **These scopes are not an authorization boundary between two real users**; the same operator can read both.

Use the **memory_id returned by this new retained store** to explicitly update that item's content. This does not change its TTL or the older store:

```bash
python scripts/workshop.py --language en memory update --scope alpha --case D01 --memory-id "ACTUAL-MEMORY-ID" --confirm-write --confirm-cost
python scripts/workshop.py --language en memory inspect --scope alpha
```

This chapter **retains the store you created**. Do not run `memory forget`, `memory cleanup`, or `--confirm-delete`. Preserve IDs, TTLs, and ownership records. Any older stores keep their original expiry settings. Decide separately about deletion in 15.

For transient 404s or delays, perform bounded reads of the same item; do not repeatedly `put` duplicate items. This is explicit Memory API usage, not proof of automatic memory extraction from conversations.

## 2. A2A: delegate to a separate endpoint

```bash
python scripts/workshop.py --language en a2a plan
python scripts/workshop.py --language en a2a target --confirm-create
python scripts/workshop.py --language en a2a inspect
```

Create a target under your prefix and inspect its actual card's `supportedInterfaces` for **1.0 / JSONRPC / the exact URL**. Two local participants are not proof of A2A.

Use the returned **target_base and connection_name**. The target is a base path, not the card URL. `--cwd` is the actual Hosted folder prepared in 08:

```bash
azd ai connection create "RETURNED-CONNECTION-NAME" --kind remote-a2a --target "RETURNED-TARGET-BASE" --auth-type project-managed-identity --audience https://ai.azure.com --project-endpoint "YOUR-PROJECT-ENDPOINT" --cwd "YOUR-08-HOSTED-ABSOLUTE-PATH"
python scripts/workshop.py --language en a2a caller --confirm-create
python scripts/workshop.py --language en a2a invoke --label a2a-first-en --confirm-cost
```

Verify a real successful A2A call in the caller response. Preserve names, versions, exact 1.0 configuration, and source evidence. Do not automatically downgrade to 0.3 or substitute another agent when unsupported.

<details>
<summary>Only for an older caller reporting no valid target URL</summary>

Current code checks both the connection target and A2A tool's `base_url`. If an older caller lacks the URL, preserve the failure and create an explicit new version. Do not run this after an already successful call:

```bash
python scripts/workshop.py --language en a2a caller --confirm-create --new-version
python scripts/workshop.py --language en a2a invoke --label a2a-fixed-en --confirm-cost
```

This keeps the previous version. The helper refuses an update when unrecorded remote versions exist; do not edit the ownership ledger to bypass that check.

</details>

After partial creation, inspect existing IDs, connections, and roles. Do not repeatedly recreate targets or edit ownership files. If choosing final deletion, remove only your assets in **caller → connection → target** order. Retention mode keeps all three.

## 3. Routines: prepare a disabled schedule

Use the actual **Prompt Agent name** you invoked in 03—not a model deployment name. Record its actual target version too.

**Never pass a user-created conversation to an unattended routine in this lab.** Both project-scoped and agent-endpoint conversations failed with `conversation_not_found` under the routine actor. Preserve those failures and resources. Use a **fresh timer with static `action.input` and no conversation**.

First register the actual log workspace from 09. Its real `customerId` binds `AZURE_LOG_ANALYTICS_WORKSPACE_ID`, and the actual project ARM ID binds `AZURE_AI_PROJECT_ID`. This does not create a workspace or generate a model response:

```bash
python scripts/selfstudy.py resource --kind logs --id "YOUR-LOG-ANALYTICS-ARM-ID"
```

Verify log-read permissions and choose a future UTC time you can observe. Five minutes below is only an example; allow enough time for preparation and review:

```bash
python -c "from datetime import datetime,timedelta,UTC; print((datetime.now(UTC)+timedelta(minutes=5)).isoformat(timespec='seconds').replace('+00:00','Z'))"
```

In your editor, create a **new, nonexistent file** such as `.selfstudy/routine-static-en.json`. Replace the timestamp and actual agent name and save UTF-8 JSON. Omit `conversation` entirely:

```json
{
  "enabled": false,
  "triggers": {
    "default": {
      "type": "timer",
      "at": "FUTURE-UTC-TIMESTAMP"
    }
  },
  "action": {
    "type": "invoke_agent_responses_api",
    "agent_name": "ACTUAL-ENGLISH-PROMPT-AGENT-NAME",
    "input": "What advance approval is required for a KRW 170000 hotel on a domestic business trip in September 2026?"
  }
}
```

The manifest uses wire type **`invoke_agent_responses_api`**, not CLI alias `agent-response`. Create has no `--input` flag, so persistent input belongs in `action.input`. A manual `dispatch --input` override affects only that one dispatch; it does not configure the timer's stored input.

```bash
azd ai routine create "YOUR-PREFIX-timer-static-en" --file .selfstudy/routine-static-en.json --enabled=false --project-endpoint "YOUR-PROJECT-ENDPOINT" --output json
azd ai routine show "YOUR-PREFIX-timer-static-en" --project-endpoint "YOUR-PROJECT-ENDPOINT" --output json
```

Read back the fresh owned name, agent, future timestamp, **`enabled: false`, static input, and absence of a conversation**. Do not use `--force` or overwrite an existing manifest.

<a id="4-dispatch-once-and-always-disable"></a>

## 4. Observe one timer delivery, then disable

Enable only after reviewing cost, timing, and input:

```bash
azd ai routine enable "YOUR-PREFIX-timer-static-en" --project-endpoint "YOUR-PROJECT-ENDPOINT"
azd ai routine run list "YOUR-PREFIX-timer-static-en" --project-endpoint "YOUR-PROJECT-ENDPOINT" --output json
```

After the scheduled time, perform bounded reads of the same run list. Record the actual **`timer_delivery`** run's `dispatch_id`, `response_id`, scheduled/triggered times, and `Finished` status. Do not manually dispatch this timer to manufacture scheduled-execution evidence.

**Run disable separately on success, failure, or when ending observation.** Do not make stopping conditional on success:

```bash
azd ai routine disable "YOUR-PREFIX-timer-static-en" --project-endpoint "YOUR-PROJECT-ENDPOINT"
azd ai routine run list "YOUR-PREFIX-timer-static-en" --project-endpoint "YOUR-PROJECT-ENDPOINT" --output json
azd ai routine show "YOUR-PREFIX-timer-static-en" --project-endpoint "YOUR-PROJECT-ENDPOINT" --output json
```

**In the historical Sweden run**, disabling changed `phase` from `completed` to `cancelled` while `Finished` and the original response ID remained. In NC, preserve the actual raw phase and verify the original completed response rather than rewriting status.

<details>
<summary>Only if the CLI list is empty after disabling: read SDK history</summary>

### Recover native history when the CLI list is empty

In NC, `azd ai routine run list` returned `value: null` although SDK history contained the real delivery. Disable the timer as planned, then export its actual IDs without creating another timer or manual dispatch:

```bash
python scripts/routine_runs.py --name "YOUR-PREFIX-timer-static-en" --label routine-native-history-en
```

Read **every attempt** in `outputs/routine-runs/routine-native-history-en/runs.json`. Use the actual `Finished` attempt's `dispatch_id` below; retain `Killed`/`cancelled` entries. Listing history does not verify the answer, and export labels are never overwritten.

</details>

### Verify the same scheduled response through telemetry

Use the returned **routine name and `dispatch_id`**, with an unused lowercase label. Replace the `RETURNED-...` placeholders and example label with your actual values. Do not substitute the separate run ID or a manual dispatch ID:

```bash
python scripts/workshop.py --language en routines inspect --name "RETURNED-ROUTINE" --dispatch-id "RETURNED-DISPATCH-ID" --label routine-static-timer-readback-en --verify-response --response-source telemetry --scheduled
```

The verifier checks the timer source/timestamps, original response ID, agent/version/project/trace, and completed `invoke_agent` output. The two verified flags and disabled state from Sweden are historical. Check `scheduled_trigger_verified`, `agent_answer_verified`, `routine_enabled`, retrieval source, and new-inference status in the **new NC result**.

Post-disable evidence must retain **`run_phase: cancelled`**. This exception applies only with `Finished` status and complete telemetry for the same original response; not every cancelled run is successful. If ingestion is delayed, retry reading the same ID—not a new dispatch or replacement model call.

<details>
<summary>Only if you have a separate manual Routine run — skip on a first pass</summary>

### Read the original manual response from telemetry

Read back only an original manual run whose logs still exist in the **same currently configured project**. Read deleted Sweden-resource evidence from its archive; do not pass those old IDs to the NC command below. Use an unused label for another readback:

```bash
python scripts/workshop.py --language en routines inspect --name "ORIGINAL-MANUAL-ROUTINE-NAME" --dispatch-id "ORIGINAL-MANUAL-DISPATCH-ID" --label routine-manual-telemetry-en --verify-response --response-source telemetry
```

Do not add `--scheduled` to a manual readback. Manual and timer runs are different evidence, both verified without new inference. **Retain routines disabled** and preserve earlier failures, conversations, and raw records.

</details>

**Completion check:** Record creation, execution, readback, and retention separately. Verified timer delivery does not mean every new policy-quality criterion has passed.

**Next → [12. Conversation evaluation, Optimizer, and deployment quality](12-improvement.md)**
