# 11. Memory, A2A, and Routines

**English** | [한국어](../11-memory-a2a-routines.md) · [Course home](../../README.md)

**Outcome:** Create, use, and verify memory storage, delegation to another agent, and scheduled execution, then explicitly stop, retain, or remove what you own.

**Prerequisites:** Project identity roles from 00, the embedding deployment from 06, and the azd Foundry extension from 08. Review creation and request costs for each feature.

## 1. Memory: persist an item and recall it in a new request

Verify that `workshop-embedding` from 06 is configured:

```bash
python scripts/selfstudy.py status
python scripts/workshop.py --language en memory plan
python scripts/workshop.py --language en memory create --confirm-create
python scripts/workshop.py --language en memory put --scope alpha --case D02 --confirm-write --confirm-cost
```

Record the returned **memory_id**. The default 3600-second TTL is a service retention setting, not a course deadline. Perform this lifecycle check within that validity period.

```bash
python scripts/workshop.py --language en memory inspect --scope alpha
python scripts/workshop.py --language en memory inspect --scope beta
python scripts/workshop.py --language en memory recall --scope alpha --label memory-alpha-en --confirm-cost
python scripts/workshop.py --language en memory recall --scope beta --label memory-beta-en --confirm-cost
```

Verify that alpha retains the item across independent commands and beta does not contain it. **These scopes are not an authorization boundary between two real users**; the same operator can read both.

Update that same item first:

```bash
python scripts/workshop.py --language en memory update --scope alpha --case D01 --memory-id "ACTUAL-MEMORY-ID" --confirm-write --confirm-cost
python scripts/workshop.py --language en memory inspect --scope alpha
```

Run the following **only if you choose the deletion exercise**. In [retention mode](15-capstone-cleanup.md#retention-mode), skip all three deletion-flow commands and preserve the store and IDs. **Retaining a store does not make its one-hour memory items permanent.**

```bash
python scripts/workshop.py --language en memory forget --memory-id "ACTUAL-MEMORY-ID" --confirm-delete
python scripts/workshop.py --language en memory inspect --scope alpha
python scripts/workshop.py --language en memory cleanup --confirm-delete
```

Keep update/deletion results and IDs. For transient 404s or delays, perform bounded reads of the same item; do not repeatedly `put` duplicate items. This is explicit Memory API usage, not proof of automatic memory extraction from conversations.

## 2. A2A: delegate to a separate endpoint

```bash
python scripts/workshop.py --language en a2a plan
python scripts/workshop.py --language en a2a target --confirm-create
python scripts/workshop.py --language en a2a inspect
```

Create a target under your prefix and inspect its actual card's `supportedInterfaces` for **1.0 / JSONRPC / the exact URL**. Two local participants are not proof of A2A.

Use the returned **target_base and connection_name**. The target is a base path, not the card URL:

```bash
azd ai connection create "RETURNED-CONNECTION-NAME" --kind remote-a2a --target "RETURNED-TARGET-BASE" --auth-type project-managed-identity --audience https://ai.azure.com --project-endpoint "YOUR-PROJECT-ENDPOINT"
python scripts/workshop.py --language en a2a caller --confirm-create
python scripts/workshop.py --language en a2a invoke --label a2a-first-en --confirm-cost
```

Verify a real successful A2A call in the caller response. Preserve names, versions, exact 1.0 configuration, and source evidence. Do not automatically downgrade to 0.3 or substitute another agent when unsupported.

The code checks the connection target and also sets the same explicit **`base_url` on the A2A tool**. A connection can exist while invocation fails with `no valid target URL` when this field is missing. If you created the caller with earlier code, preserve the failure and explicitly create a corrected version:

```bash
python scripts/workshop.py --language en a2a caller --confirm-create --new-version
python scripts/workshop.py --language en a2a invoke --label a2a-fixed-en --confirm-cost
```

This keeps the previous version. The helper refuses an update when unrecorded remote versions exist; do not edit the ownership ledger to bypass that check.

After partial creation, inspect existing IDs, connections, and roles. Do not repeatedly recreate targets or edit ownership files. If choosing final deletion, remove only your assets in **caller → connection → target** order. Retention mode keeps all three.

## 3. Routines: prepare a disabled schedule

Use the actual **Prompt Agent name** you invoked in 03—not a model deployment name. Record its actual target version too.

Calculate tomorrow's UTC timestamp:

```bash
python -c "from datetime import datetime,timedelta,UTC; print((datetime.now(UTC)+timedelta(days=1)).isoformat())"
```

With that timestamp and the actual agent/endpoint, create a **disabled one-time timer**:

```bash
azd ai routine create "YOUR-PREFIX-timer-en" --trigger timer --at "CALCULATED-UTC-TIMESTAMP" --agent-name "YOUR-ENGLISH-PROMPT-AGENT-NAME" --action agent-response --enabled=false --project-endpoint "YOUR-PROJECT-ENDPOINT" --output json
azd ai routine show "YOUR-PREFIX-timer-en" --project-endpoint "YOUR-PROJECT-ENDPOINT" --output json
```

Check name, target, timestamp, and `enabled: false`. Do not use `--force` to overwrite an existing routine.

## 4. Dispatch once and always disable

Dispatch only after enable succeeds:

```bash
azd ai routine enable "YOUR-PREFIX-timer-en" --project-endpoint "YOUR-PROJECT-ENDPOINT"
azd ai routine dispatch "YOUR-PREFIX-timer-en" --input "What advance approval is required for a KRW 170000 hotel on a domestic business trip in September 2026?" --project-endpoint "YOUR-PROJECT-ENDPOINT" --output json
```

**Run disable even if dispatch fails.** Do not make this stopping step conditional on success:

```bash
azd ai routine disable "YOUR-PREFIX-timer-en" --project-endpoint "YOUR-PROJECT-ENDPOINT"
azd ai routine run list "YOUR-PREFIX-timer-en" --project-endpoint "YOUR-PROJECT-ENDPOINT" --output json
azd ai routine show "YOUR-PREFIX-timer-en" --project-endpoint "YOUR-PROJECT-ENDPOINT" --output json
python scripts/workshop.py --language en routines inspect --name "YOUR-PREFIX-timer-en" --dispatch-id "ACTUAL-DISPATCH-ID" --label routine-first-en
```

Verify the final disabled state and real delivery result. **Schedule creation, dispatch, agent response verification, and future scheduled execution are different outcomes.** If you cannot retrieve the response, do not substitute a separate direct agent answer.

If no longer needed and you choose deletion, remove only your routine from Foundry's Routines list. In retention mode, **leave it disabled**. Routine deletion does not also delete models, Search, or previous logs.

**Completion:** Record actual creation, reads, calls, stop/retention/deletion status, and unverified areas for all three features.

**Next → [12. Conversation evaluation, Optimizer, and deployment quality](12-improvement.md)**
