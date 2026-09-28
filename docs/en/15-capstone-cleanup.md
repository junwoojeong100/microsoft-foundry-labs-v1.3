# 15. Final acceptance and resource lifecycle

**English** | [한국어](../15-capstone-cleanup.md) · [Course home](../../README.md)

**Outcome:** Test a frozen target on unseen cases, then explicitly stop, retain, or remove every chargeable resource you created.

Even when stopping early, **perform the stopping, inventory, and retention decisions below now**. Quality failures are not a reason to leave chargeable resources unattended. Deletion is a separate choice.

**Current repository-rerun boundary:** only old NC group `rg-mf15-jw-nc-0928` was deleted; new `rg-mflabs15-jw-0928` is retained. **New Task Adherence returned six rows/five pass/one fail with inconsistent severity/flags, so final acceptance is held and no new holdout was unlocked.** All 13 observed Hosted sessions are idle; timer/continuous/Insights schedules are disabled/paused. Eight remote evidence files were archived. See the [new results and retention costs](validation-report.md).

Sweden and earlier NC 5/5, four-known-case, and Optimizer-candidate statements below describe historical runs. They do not grant new acceptance or make previously used holdout cases unseen. **Finishing the lab execution and passing final quality acceptance are different states.**

## Retention mode

If you want to reuse the lab or preserve a validation environment, **do not execute deletion commands**.

- Skip `--confirm-delete`, all Memory `forget`/`cleanup`, other cleanup operations, `azd down`, and resource-group deletion.
- Create File Search in 03 with `--retain` so the vector store has no automatically configured expiry.
- In 11, explicitly select a new language-specific Memory store and use **`memory create --ttl-seconds 0 --confirm-create`** for no automatic item expiry. Do not delete or modify the existing one-hour store.
- Stop local servers and leave Routines/recurring evaluation **disabled/paused**. **Stop only** unnecessary Hosted compute sessions; do not delete agents, versions, or persistent volumes.
- Privately retain `.env`, `.selfstudy/azure.json`, actual IDs, and `outputs/` ownership records in an approved location. Do not upload them to a public repository.
- Record remaining Search Basic, file/volume, and logging costs and the next review date. `lifecycle=retain` is an administrative tag, not a deletion lock or a budget cap.

Memory's new default **`default_ttl_seconds=0` means no automatic item expiry**. Positive TTLs can be at most 365 days, and previously recorded stores retain their original settings. `WORKSHOP_MEMORY_STORE_NAME` is global: use `<prefix>-memory-retained-en` for English and `<prefix>-memory-retained-ko` for Korean, checking the selector before each language's run. Follow [11's retained-store procedure](11-memory-a2a-routines.md#1-memory-persist-an-item-and-recall-it-in-a-new-request).

Keep every owned store's name, TTL, IDs, and records. Do not silently update or adopt older assets under the new setting. Managed-session expiry is separate from Memory-item TTL. Treat deletion sections as reference only and record “retained, not deleted.”

Read-only `status` and `cleanup-plan` may still be used for inventory; they do not authorize deletion.

## 1. Freeze the final evaluation target

The recommended target is 12's **actual Hosted candidate**: `wf-candidate-en` for the IQ path, or `wf-local-candidate-en` for the explicitly selected local-retrieval path. Choose one. Freeze model map, code, instructions, source documents, retrieval, API, concurrency, judge, generation settings, and version.

Before unlocking holdout, verify:

- Every expected dev matrix row exists: six core rows for this guide's single Sol target.
- No errors, omissions, or duplicates remain.
- The predetermined business gate and all three policy criteria pass, with valid source/reference audits and reviewed native limitations.
- Required trace and calibration conditions are met.
- Record chapter 13's **managed run and full row/version/direction audit**, explicitly retaining the Prohibited Actions limitation. Judge a new Task Adherence-only result only within that native scope; filtered old rows or custom `policy-lab` are not substitutes.
- You did not lower thresholds after seeing failures or edit raw results.

**Historical Sweden evidence:** preserve its Hosted IQ v1/v2 pair, language calibrations, earlier groundedness 5/6, and rejected comparison under their original conditions. They do not complete NC execution, evaluation, or managed AI red teaming.

**The old Sweden v3 canonical-six/custom-eight passes** are historical complementary evidence. Its native ASR remained unvalidated, and official regional descriptions conflict; unsupported region is not a proven cause. Custom results or a region change cannot replace actual NC managed verification, metric-direction checks, or holdout.

Preserve **the old Sweden Optimizer/audit and NC initialization failure**. Chapter 12's follow-up NC job succeeded by explicitly binding the original evaluator versions and required `pass_threshold: 4`; baseline and candidate each passed their six-row source-reference audits. Both scored 1.0, and neither was promoted. This new-job evidence does not overwrite a failure or replace holdout/production approval.

If not satisfied, **do not open holdout; record incomplete acceptance**. If unavailable features prevented the Hosted matrix, you may instead select 07's SDK candidate as a separate final target. Do not call that Hosted acceptance.

**Use holdout for only one chosen final target in an experiment.** Cases already seen in an SDK run cannot later be called unseen Hosted test data.

## 2. Run final acceptance

The NC run `nc-known-final-ko` used four previously seen cases as **known-case regression** on the same frozen v2, passing 4/4, policy, and trace gates. It is not fresh unseen holdout or production approval; its original `split: holdout` record is not rewritten.

Only after all gates in 12 pass, run the block matching your **chosen final target**. Never run the IQ block against a local matrix or count local results as IQ validation.

### IQ Hosted target

```bash
python scripts/workshop.py --language en benchmark collect --split holdout --label wf-final-en --candidate wf-candidate-en --unlock-holdout --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py --language en benchmark evaluate --policy --label wf-final-en --reference wf-baseline-en --confirm-cost
python scripts/workshop.py --language en benchmark monitor --label wf-final-en
python scripts/workshop.py --language en benchmark verify --policy --baseline wf-baseline-en --candidate wf-candidate-en --holdout wf-final-en --require-native --require-traces --calibration policy-calibration-en
```

### Local-retrieval Hosted target

For 12's separately named `matrix-local-en`, keep the frozen local profile throughout collection and use only its own baseline, candidate, and calibration:

```bash
python scripts/workshop.py --language en benchmark collect --split holdout --label wf-local-final-en --candidate wf-local-candidate-en --unlock-holdout --kind workflow --pattern sequential --retrieval local --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py --language en benchmark evaluate --policy --label wf-local-final-en --reference wf-local-baseline-en --confirm-cost
python scripts/workshop.py --language en benchmark monitor --label wf-local-final-en
python scripts/workshop.py --language en benchmark verify --policy --baseline wf-local-baseline-en --candidate wf-local-candidate-en --holdout wf-local-final-en --require-native --require-traces --calibration policy-calibration-local-en
```

`benchmark verify` checks the stored run contracts and exact versions; it does **not** accept `--retrieval`. Verify the selected manifests contain `retrieval: local` and retain their original hashes. The explicit local collection and local-only labels determine which profile is verified; do not override, edit, or substitute IQ results.

For either Hosted path, inspect every row and error after each step. This guide's single Sol target requires **four core holdout rows**. Read `gate_passed`, native quality, recommendations, and `deployment_approved: false` together. A local Hosted pass does not complete Search/IQ/Hybrid or Toolbox/OpenAPI work.

### SDK-only target

**If you selected only the SDK target**, do not execute the Hosted commands. First ensure 07's `candidate-en` passed 6/6 with zero errors under matched, frozen conditions:

```bash
python scripts/workshop.py --language en collect --split holdout --label final-holdout-en --prompt v2 --retrieval local --candidate candidate-en --unlock-holdout
python scripts/workshop.py --language en evaluate --label final-holdout-en
python scripts/workshop.py --language en cloud-evaluate --policy --label final-holdout-en --confirm-cost --timeout 900
python scripts/workshop.py --language en accept --candidate candidate-en --holdout final-holdout-en
```

The business-only `accept` result does not itself verify policy grading or reference audits. Review those actual artifacts and matching policy calibration separately. Do not substitute renamed legacy calibration or scores.

Choose **one path only**. If you modify the system after observing holdout failures, you need a new final test set; do not tune against this holdout or edit it.

## 3. Explain the result in your own words

Complete the acceptance card in your workbook:

```text
Foundry is a platform for ______.
Instructions, knowledge, and tools are responsible for ______.
Prompt Agents, local MAF, and Hosted differ in ______.
I judged improvement using the actual evidence ______.
Within this synthetic lab, I have not yet verified ______.
```

Learning completion and passing the small lab quality gate are different states. Record only actual targets, versions, results, and unverified areas. Do not fill unperformed steps with success.

## 4. Stop running work first

1. Stop your local `serve`/recovery servers with `Ctrl+C` in their terminals.
2. Verify Routines and recurring evaluations are **disabled/paused**.
3. If you ran a Hosted matrix, stop sessions for labels that actually exist. For the IQ path:

```bash
python scripts/workshop.py --language en benchmark stop-session --label wf-baseline-en
python scripts/workshop.py --language en benchmark stop-session --label wf-candidate-en
python scripts/workshop.py --language en benchmark stop-session --label wf-final-en
```

For the separately selected local-retrieval path instead:

```bash
python scripts/workshop.py --language en benchmark stop-session --label wf-local-baseline-en
python scripts/workshop.py --language en benchmark stop-session --label wf-local-candidate-en
python scripts/workshop.py --language en benchmark stop-session --label wf-local-final-en
```

Do not invent missing experiment labels. Identify separate smoke/manual sessions using `azd ai agent sessions list` in the appropriate Hosted folder and stop only your sessions.

**Archive evidence before session/file expiry.** Files may still be retrieved from a stopped session while available. Follow [session-file retrieval](advanced/session-files.md) with an **absolute `--target-path`**, matching the original request/version and recorded tool-result hashes. Stopping or retaining resources does not guarantee indefinite file retention.

**Stopping does not delete volumes.** In retention mode, keep those volumes. Otherwise, after deciding they are no longer needed, inspect the current session-deletion UI/CLI before removing them. Never terminate other people's processes in bulk by name.

## 5. Reconcile your owned assets

```bash
python scripts/selfstudy.py status
python scripts/workshop.py --language en cleanup-plan
```

Neither command deletes anything. Compare the output with your workbook, the real portal, and ownership records under `outputs/`.

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

For 03's SDK File Search assets, outside retention mode, inspect the deletion plan first:

```bash
python scripts/workshop.py --language en file-search cleanup
```

Check owned names, files, stores, and references from other agents. Only after choosing deletion:

```bash
python scripts/workshop.py --language en file-search cleanup --confirm-delete
```

This removes only recorded versions, stores, and uploads—not portal-created assets or a shared project. For experiments created with another name, provide the same `--name`. In retention mode, skip both cleanup commands.

## 6. Optional deletion of the dedicated lab group

Skip this section in retention mode. If every resource is dedicated to this course and no longer needed:

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

**End of course. [Course home](../../README.md) · [Your workbook](../../worksheets/en/workbook.md) · [Review the lab](next-steps.md)**
