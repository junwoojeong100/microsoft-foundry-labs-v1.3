# 15. Final acceptance and resource lifecycle

**English** | [한국어](../15-capstone-cleanup.md) · [Course home](../../README.md#curriculum) · [Help](checkpoints.md)

**Outcome:** Test a frozen target on unseen cases, then explicitly stop, retain, or remove every chargeable resource you created.

**Prerequisites:** final evaluation requires every prior quality gate. **Stop work and review costs now even if earlier chapters are incomplete.**

**Where you work:** terminal for evaluation, sessions, and ownership records; Azure portal for actual resources and costs.

> [!WARNING]
> **Stopping is not deletion.** Quality failures are not a reason to leave chargeable resources unattended. Stop execution, then separately decide what to retain or delete.

| Your current state | Where to go |
|---|---|
| Stopping early, or a prerequisite gate failed/is blocked | **Keep holdout closed; go to [4: stop](#4-stop-running-work-first), then 5–7 for inventory/costs** |
| Frozen candidate and all prerequisite gates satisfied | Section 1 → **one chosen target** in 2 → sections 3–7 |
| Retaining resources for reuse | Retention mode below plus 4, 5, and 7; skip deletion commands and section 6 |

**You can stop and clean up even before completing 00's `configure`.** Inspect the subscription and lab group you used in 00 directly in Azure.

- Skip commands for agents or labels you never created.
- Skip `selfstudy.py status` if `.selfstudy/azure.json` does not exist.
- Azure resources can remain even without local configuration.

**Reference validation still holds final acceptance.** The new managed Task Adherence result has six rows/five pass/one fail with inconsistent severity/flags, so no new holdout was opened.

The [report's results and lifecycle history](validation-report.md) are not your completion record or deletion instructions. **Execution and final quality acceptance are separate.**

<a id="chapter-map"></a>

**Chapter map**

| Step | Result to check |
|---|---|
| [Keeping resources: retention mode](#retention-mode) | Retained assets, expiry, and costs |
| [1. Freeze the final target](#1-freeze-the-final-evaluation-target) | Prerequisites for opening holdout |
| [2. Evaluate one chosen target](#2-run-final-acceptance) | Four new cases for one frozen target |
| [3. Interpret results](#3-interpret-the-results) | Actual quality and incomplete scope |
| [4. Stop first](#4-stop-running-work-first) | Local servers, schedules, and sessions stopped |
| [5. Reconcile assets](#5-reconcile-your-owned-assets) | Actual portal resources and owned records |
| [6. Delete group — optional](#6-optional-deletion-of-the-dedicated-lab-group) | Absence of dedicated resources chosen for deletion |
| [7. Final checklist](#7-final-checklist) | Retention, deletion, remaining costs, and evidence |

## Retention mode

> [!CAUTION]
> In retention mode, **do not execute deletion commands**. Skip `--confirm-delete`, Memory `forget`/`cleanup`, other cleanup operations, `azd down`, and resource-group deletion.

### What to stop and what to keep

| Target | Retention-mode action |
|---|---|
| Local servers | Stop |
| Routines and recurring evaluation | Verify `disabled` / `paused` |
| Unneeded Hosted compute sessions | **Stop only**; retain agents, versions, and volumes |

### Files and ownership records to retain

Retain `.env`, all of `.selfstudy/`, `.build/`, and `outputs/` in an approved private location. Include actual IDs, deployment preparation, and ownership records. **Do not publish them.**

Keep every owned store's name, TTL, IDs, and records too. Do not silently update or adopt older assets under the new setting.

### Automatic expiry and remaining costs

| Asset and creation condition | Expiry behavior |
|---|---|
| File Search in 03, created with `--retain` | No automatic expiry |
| File Search in 03, created with the default command | Still expires **seven days after last activity** |
| New Memory in 11, created with `--ttl-seconds 0` | No automatic item expiry |
| An older Memory store | Keeps its originally recorded TTL |

Do not rerun File Search creation to change retention or silently change an older Memory store's TTL.

In 11, **explicitly select a new language-specific store** and create it with `memory create --ttl-seconds 0 --confirm-create`. The new default `default_ttl_seconds=0` means no automatic item expiry; positive TTLs can be at most 365 days.

Managed-session expiry and Memory-item TTL are separate.

**Language selector:** `WORKSHOP_MEMORY_STORE_NAME` is global. Before each run, distinguish English `<prefix>-memory-retained-en` from Korean `<prefix>-memory-retained-ko`. Follow [11's retained-store procedure](11-memory-a2a-routines.md#1-memory-persist-an-item-and-recall-it-in-a-new-request).

Record **remaining costs and the next review date** for Search Basic, files/volumes, and logging. `lifecycle=retain` is an administrative tag, not a deletion lock or budget cap.

Read-only `status` and `cleanup-plan` remain available for inventory; they do not authorize deletion. Read deletion sections as reference only and record **“retained, not deleted.”**

## 1. Freeze the final evaluation target

The recommended target is 12's **actual Hosted candidate**. Choose one:

| Your selected retrieval path | Final candidate |
|---|---|
| IQ | `wf-candidate-en` |
| Explicit local retrieval | `wf-local-candidate-en` |

Freeze model map, code, instructions, source documents, retrieval, API, concurrency, judge, generation settings, and version.

Before unlocking holdout, verify the following. **If any item is unmet, go to section 4 to stop work and review costs first.**

- [ ] Every expected dev matrix row exists: six core rows for this guide's single Sol target.
- [ ] No errors, omissions, or duplicates remain.
- [ ] The predetermined business gate and all three policy criteria pass, with valid source/reference audits and reviewed native limitations.
- [ ] Required trace and calibration conditions are met.
- [ ] Chapter 13's **managed run and full row/version/direction audit** are recorded, retaining the Prohibited Actions limitation. A new Task Adherence-only result is judged only within its native scope; filtered old rows or custom `policy-lab` are not substitutes.
- [ ] I did not lower thresholds after seeing failures or edit raw results.

If not satisfied, **do not open holdout; record incomplete acceptance**.

If unavailable features prevented the Hosted matrix, you may instead select 07's SDK candidate as a separate final target. Do not call that Hosted acceptance.

**Use holdout for only one chosen final target in an experiment.** Cases already seen in an SDK run cannot later be called unseen Hosted test data.

## 2. Run final acceptance

If you already saw these four cases, another run is **known-case regression**, not a new unseen test or production approval, even if its recorded split is `holdout`.

> [!IMPORTANT]
> Run the block for your **chosen final target only after all section 1 prerequisites pass**. `--unlock-holdout` is not permission to ignore unfinished evaluation.

Never run the IQ block against a local matrix or count local results as IQ validation.

### IQ Hosted target

**1. Collect four new cases from the chosen Hosted version**

```bash
python scripts/workshop.py --language en benchmark collect --split holdout --label wf-final-en --candidate wf-candidate-en --unlock-holdout --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
```

**2. Evaluate saved responses with the policy judge · `wf-final-en`**

```bash
python scripts/workshop.py --language en benchmark evaluate --policy --label wf-final-en --reference wf-baseline-en --confirm-cost
```

**3. Query actual traces · `wf-final-en`**

```bash
python scripts/workshop.py --language en benchmark monitor --label wf-final-en
```

**4. Check final gates against saved evidence**

```bash
python scripts/workshop.py --language en benchmark verify --policy --baseline wf-baseline-en --candidate wf-candidate-en --holdout wf-final-en --require-native --require-native-pass --require-traces --calibration policy-calibration-en
```

<details>
<summary>Local Hosted target only: use this instead of the IQ block</summary>

### Local-retrieval Hosted target

For 12's separately named `matrix-local-en`, keep the frozen local profile throughout collection and use only its own baseline, candidate, and calibration:

```bash
python scripts/workshop.py --language en benchmark collect --split holdout --label wf-local-final-en --candidate wf-local-candidate-en --unlock-holdout --kind workflow --pattern sequential --retrieval local --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
```

**Evaluate saved responses with the policy judge · `wf-local-final-en`**

```bash
python scripts/workshop.py --language en benchmark evaluate --policy --label wf-local-final-en --reference wf-local-baseline-en --confirm-cost
```

**Query actual traces · `wf-local-final-en`**

```bash
python scripts/workshop.py --language en benchmark monitor --label wf-local-final-en
```

**Check final gates against saved evidence**

```bash
python scripts/workshop.py --language en benchmark verify --policy --baseline wf-local-baseline-en --candidate wf-local-candidate-en --holdout wf-local-final-en --require-native --require-native-pass --require-traces --calibration policy-calibration-en
```

`benchmark verify` checks the stored run contracts and exact versions; it does **not** accept `--retrieval`. Verify the selected manifests contain `retrieval: local` and retain their original hashes.

The local collection and local-only labels determine which profile is verified. Do not override, edit, or substitute IQ results.

</details>

For either Hosted path, inspect every row and error after each step. This guide's single Sol target requires **four core holdout rows**.

| Result field | What to read |
|---|---|
| `gate_passed` | Whether the acceptance criteria checked by this command passed |
| `native_quality_passed` | Whether actual Foundry policy scores passed |
| `native_quality_required: true` | Whether passing scores were required |
| `deployment_approved: false` | Do not interpret this as production approval |

A local Hosted pass does not complete Search/IQ/Hybrid or Toolbox/OpenAPI work.

**Distinguish the two options**

- `--require-native`: requires Foundry policy-evaluation **evidence**.
- `--require-native-pass`: also requires candidate/holdout **scores to pass**.

This command does not verify chapter 13's separate managed red-team audit. Check that explicitly in section 1.

<details>
<summary>SDK target only: use this instead of either Hosted block</summary>

### SDK-only target

**If you selected only the SDK target**, do not execute the Hosted commands. First ensure 07's `candidate-en` passed 6/6 with zero errors under matched, frozen conditions:

```bash
python scripts/workshop.py --language en collect --split holdout --label final-holdout-en --prompt v2 --retrieval local --candidate candidate-en --unlock-holdout
```

**Run business checks on saved responses · `final-holdout-en`**

```bash
python scripts/workshop.py --language en evaluate --label final-holdout-en
```

**Evaluate saved responses with the policy judge · `final-holdout-en`**

```bash
python scripts/workshop.py --language en cloud-evaluate --policy --label final-holdout-en --reference baseline-en --confirm-cost --timeout 900
```

**Check final business acceptance**

```bash
python scripts/workshop.py --language en accept --candidate candidate-en --holdout final-holdout-en
```

The business-only `accept` result does not itself verify policy grading or reference audits. Review those actual artifacts and matching policy calibration separately. Do not substitute renamed legacy calibration or scores.

</details>

Choose **one path only**. If you modify the system after observing holdout failures, you need a new final test set; do not tune against this holdout or edit it.

## 3. Interpret the results

Review section 2's actual target, version, complete rows, business/policy verdicts, and remaining errors together. The SDK target from 07 and Hosted target from 12 are different. Scores from mismatched conditions do not demonstrate improvement.

Learning completion and passing the small lab quality gate are different states. No separate report is required, but preserve raw results and failures and never treat unperformed work as successful.

## 4. Stop running work first

1. Stop your local `serve`/recovery servers with `Ctrl+C` in their terminals.
2. Verify only Routines and recurring evaluations you created are **disabled/paused**. If you created none, mark this not applicable.
3. If you ran a Hosted matrix, stop **only labels that actually exist**. Skip the final-label line if holdout was not run.

### If you chose the IQ matrix

```bash
python scripts/workshop.py --language en benchmark stop-session --label wf-baseline-en
```

**Stop this run's session · `wf-candidate-en`**

```bash
python scripts/workshop.py --language en benchmark stop-session --label wf-candidate-en
```

**Only if holdout actually ran: stop `wf-final-en`**

```bash
python scripts/workshop.py --language en benchmark stop-session --label wf-final-en
```

### If you chose the local-retrieval matrix instead

```bash
python scripts/workshop.py --language en benchmark stop-session --label wf-local-baseline-en
```

**Stop this run's session · `wf-local-candidate-en`**

```bash
python scripts/workshop.py --language en benchmark stop-session --label wf-local-candidate-en
```

**Only if holdout actually ran: stop `wf-local-final-en`**

```bash
python scripts/workshop.py --language en benchmark stop-session --label wf-local-final-en
```

Do not invent missing experiment labels. Identify separate smoke/manual sessions using `azd ai agent sessions list` in the appropriate Hosted folder and stop only your sessions.

**Archive evidence before session/file expiry.** Files may still be retrieved from a stopped session while available.

Follow [session-file retrieval](advanced/session-files.md) with an **absolute `--target-path`**. Match the original request/version and recorded tool-result hashes. Stopping or retaining resources does not guarantee indefinite file retention.

> [!WARNING]
> **Stopping does not delete volumes.** Keep them in retention mode. Only after separately deciding they are no longer needed, inspect the current session-deletion UI/CLI before removing them.

Never terminate other people's processes in bulk by name.

## 5. Reconcile your owned assets

**Read saved settings — only after completing 00's `configure`**

If configuration is incomplete, skip the block below and inspect the actual lab group and created resources in the Azure portal.

```bash
python scripts/selfstudy.py status
```

**Read the owned-resource cleanup plan**

If Python setup is complete, use the command below to read local records. **It does not automatically discover all Azure assets.** If Python setup is incomplete, skip this command too and inspect the portal.

```bash
python scripts/workshop.py --language en cleanup-plan
```

Neither command deletes anything. Compare the listed assets with the real portal and ownership records under `outputs/`.

The removal column below applies **only if you separately choose deletion**, not in retention mode:

| Asset | Verify / optional removal order |
|---|---|
| Routines and recurring evaluations | Disable first; remove only your schedules |
| Memory | Inspect → forget owned items → clean up your empty store |
| Toolbox and Skills | Remove referring agents/Toolboxes before your Skill |
| A2A | Caller → connection → target |
| Prompt/Hosted agents | Verify exact owned names, versions, and sessions before removal |
| File Search | Review vector stores and uploaded files separately |
| Search | Original/hybrid indexes, sources/bases, and service |
| Evaluation/Optimizer | Separate retained evidence/data from temporary targets |
| Logs | Actual Application Insights/Log Analytics groups and retention |
| Models/Foundry | Check whether any callers still need them |
| Roles, identities, federation | Review only assignments/scopes you added |

Deleting ownership ledgers makes it harder—not easier—to determine which assets are yours.

Expand the following **only if you chose to delete File Search**. If you never created it or are in retention mode, skip both cleanup commands.

<details>
<summary>Only after choosing deletion, with SDK File Search ownership records from 03</summary>

If partial failure left only files/stores, reconcile the ownership record and portal first.

**1. Inspect the plan without deleting**

```bash
python scripts/workshop.py --language en file-search cleanup
```

**2. Delete only after checking ownership and references**

Check owned names, files, stores, and references from other agents. Only after choosing deletion:

```bash
python scripts/workshop.py --language en file-search cleanup --confirm-delete
```

This removes only recorded versions, stores, and uploads—not portal-created assets or a shared project. For experiments created with another name, provide the same `--name`.

</details>

## 6. Optional deletion of the dedicated lab group

> [!CAUTION]
> **Skip this section in retention mode and go to section 7.** These steps apply only after you separately choose deletion.

If every resource is dedicated to this course and no longer needed:

1. In the Azure portal, open **Resource groups → your lab group → Resources**.
2. Inspect the actual list for business resources or another user's assets.
3. Save any execution/evaluation evidence you need in an approved private location.
4. Under **Delete resource group**, verify the exact name before deletion.
5. Verify completion and the resources' absence afterward.

Also inspect Application Insights, Log Analytics, managed identities, and separate Search/Hosted resources in other groups. Deleting one group does not imply everything was removed.

If resources are shared, do not delete the group; remove **only your own individual assets** when appropriate. If retaining them, record reason, cost, owner, and next review date.

Azure soft-delete and retention policies can make API deletion different from immediate physical erasure. Forced purge is not a default exercise.

## 7. Final checklist

- [ ] No routine or running session remains active unintentionally.
- [ ] I verified actual deletion or retention status in the portal.
- [ ] I reviewed remaining billable resources in Cost analysis, allowing for billing delays.
- [ ] I recorded synthetic results, errors, and unperformed work honestly.
- [ ] I did not publish personal information, tokens, or `.env`.

If you created resources outside this folder's workflow, include their inventory too. Do not remove unrelated personal records or shared resources.

---

**End of course.** [← 14. CI/CD](14-additional-permissions.md) · [Course home](../../README.md#curriculum) · [Find saved results](checkpoints.md#find-saved-configuration-and-results) · [Review the lab](next-steps.md) · [Chapter map ↑](#chapter-map)
