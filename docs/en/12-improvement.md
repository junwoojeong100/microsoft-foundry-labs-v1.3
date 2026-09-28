# 12. Conversation evaluation, Optimizer, and deployment quality

**English** | [한국어](../12-improvement.md) · [Course home](../../README.md)

**Outcome:** Evaluate whole conversations and compare improvement candidates and actual Hosted versions using evidence.

**Prerequisites:** Judge/dev results from 07, Hosted preparation from 08, the same-account OpenAI endpoint, and logging from 09. The IQ matrix also needs working Search/IQ from 06; the explicitly selected local matrix does not. Check costs for each feature. **Do not open holdout in this chapter.**

The corrected Sol + GA IQ **SDK candidate** scored 6/6 on all three policy criteria with valid reference audits, under the frozen GPT-5.5 catalog and threshold 4. Preserve the original groundedness 5/6 and D01's unsupported team-lead detail. The old/new SDK comparison was rejected because coupled code changes altered `code_hash`; **do not interpret those scores as isolated prompt improvement or Hosted quality**.

This chapter requires **freezing code first, then collecting a fresh Hosted baseline/candidate pair**. Fix model, corpus, language, retrieval, API, judge catalog, threshold, and generation settings; vary only instructions. If coupled code changes during the comparison, start a new matched pair under fresh labels. Do not edit manifest hashes or weaken comparison checks.

**New independently verified Hosted evidence:** actual **Hosted IQ v1/v2 with a Sol-only map each passed six dev rows, 6/6 on all three policy criteria, valid reference audits, and 6/6 actual traces**. The same frozen code and corpus allowed `benchmark compare`. Equal passing counts do not demonstrate a pass-rate improvement. The remote Toolbox Hosted agent-version-1 response was also verified against its package, calls, session, and source hash.

**Latest separate verification:** corrected **Hosted IQ deployment version 3** verified canonical dev six rows and diagnostic eight rows, including business checks, all three policy criteria, source audits, and actual traces (6+8). The diagnostic suite is version 2. Deployment version 3 is not the prompt preset `--prompt v2`; use your actual returned deployment version. Do not treat this as prompt-only improvement against older code/case contracts or as new holdout evidence.

If derived policy/Skill inputs have changed prompt/source hashes, prepare them under new input labels too. Editing local v2 files does not automatically update an already deployed agent or Skill.

## Choose the matrix retrieval mode explicitly

Conversation evaluation and Optimizer can proceed without Search when their own model, permission, and budget prerequisites are met. Before starting a Hosted matrix, choose one mode and keep it fixed through v1, v2, and final acceptance:

| Setting | IQ path | Explicit local-retrieval path |
|---|---|---|
| Every `package-hosted` and `benchmark plan` / `smoke` / `collect` profile | `--retrieval iq` | `--retrieval local` |
| English `prepare-hosted --name` | `matrix-en` | `matrix-local-en` |
| IQ reranker threshold | Set it in section 5 | **Skip it entirely** |
| Baseline / candidate labels | `wf-baseline-en` / `wf-candidate-en` | `wf-local-baseline-en` / `wf-local-candidate-en` |
| Instructions to follow | Sections 4–9 | Section 4's model map, then section 10 |

The English service suffixes correspond to the Korean guide's `matrix` and `matrix-local`, with `-en` added to keep language-specific assets distinct. Use the helper's actual returned service, folder, and version—not a guessed endpoint.

Stored-result commands such as `evaluate`, `compare`, `monitor`, and `verify` have no new `--retrieval` flag. Their exact run labels and frozen manifests must belong to the selected mode. Moving to IQ later requires new labels and a new matched pair; local retrieval does not validate Search, IQ, or vector search.

## 1. Evaluate conversations

```bash
python scripts/workshop.py --language en conversations plan
python scripts/workshop.py --language en conversations collect --label conversations-first-en --prompt v2 --confirm-cost
python scripts/workshop.py --language en conversations report --label conversations-first-en
python scripts/workshop.py --language en conversations evaluate --label conversations-first-en --level turn --confirm-cost
python scripts/workshop.py --language en conversations evaluate --label conversations-first-en --level conversation --confirm-cost
```

Evaluate the same real conversation at turn and conversation levels. Do not share Memory or conversation state across independent evaluation cases. Review contradictions, intent resolution, all rows, and errors; record differences between the two levels.

## 2. Prepare Optimizer models and data

1. Check supported models in the Foundry agent's **Optimize** screen.
2. This lab uses **`gpt-5.5` / `2026-04-24` → `workshop-optimizer`** for candidate generation. Check region, quota, and price, then deploy using the approach in 02.
3. Keep **GPT-6 Sol** as the answer model and **GPT-5.5** as the judge from 07, with a different base model and deployment from the target. Optimizer has a separate support list; do not substitute GPT-6 for its candidate-generation model.
4. Prepare extension inputs if they do not already exist for this prefix/language:

```bash
python scripts/selfstudy.py model --role optimizer
python scripts/workshop.py --language en prepare-extensions --policy --label policy-inputs-en
```

Inspect the **six dev rows** in `outputs/policy-inputs-en/optimizer-dev.jsonl`, the original-reference envelope in `ground_truth`, `policy-evaluator-definitions.json`, and the manifest. If 07 already prepared the same policy inputs, verify hashes, prefix, and language and reuse them instead of rerunning preparation. Do not overwrite 10's Skill inputs or include holdout.

## 3. Optimize instructions only

The corrected **native Prompt Optimizer job completed** with a Sol target, GPT-5.5, three pinned policy judges at threshold 4, and at most two candidates. It **stopped early at the Optimizer-reported baseline 1.0 and generated zero new candidates**. That aggregate is distinct from individual policy `result` values on the 1–5 scale. **Do not claim that it generated an improved prompt.**

1. Create a **separate owned Prompt Agent** using the same English synthetic policies/instructions as 03. Distinguish it with a name such as `<prefix>-optimize-en`.
2. Select **Optimize / Create optimization run → Agent**.
3. Pin the actual target version and answer model.
4. Optimize **instructions only**, with at most **two candidates**.
5. Upload the new policy dev inputs and verify the actual registered `policy_groundedness`, `policy_helpfulness`, and `policy_compliance` definitions/versions and `query`/`response`/`ground_truth` mapping. The current Prompt Agent wizard does not remap column names. The original-reference envelope is evaluator input, never target-agent input. Registration alone does not prove the Optimizer run used the correct mapping.
6. Review cost and expected call scope, then submit once.
7. Read instruction differences, all rows, and evaluation results for the baseline and every candidate.

Export the exact completed native evaluation/run under a **new export label**. This policy audit uses original source echoes; do not assume hidden judge requests were exposed or use the legacy `--require-judge-inputs` option as a substitute for the audit:

```bash
python scripts/workshop.py --script export-evaluation --language en --evaluation-id "ACTUAL-EVALUATION-ID" --run-id "ACTUAL-EVALUATION-RUN-ID" --expected-rows 6 --label optimizer-policy-export-en
```

Use the original policy dataset actually uploaded and its matching-language calibration. Replace the example dataset/labels with the actual new inputs and calibration:

```bash
python scripts/audit_optimizer.py --export-directory outputs/evaluation-exports/optimizer-policy-export-en --dataset outputs/policy-inputs-en/optimizer-dev.jsonl --calibration-label policy-calibration-en --language en --output outputs/optimizer-policy-audit-en.json
```

This script **audits saved files without contacting Azure**. Its actual run verified **6/6 source echoes and 6/6 on each of all three criteria**, matching original envelopes, three pinned judge versions/threshold 4, reason reference IDs, and calibration. It rejects wrong scope, references, thresholds, and response-as-reference mappings without modifying original exports or scores.

Inspect `validation_status: valid`, all six matched rows, and the stated evidence scope:

```text
proof_level: source-echo+reason-reference-id+counterfactual-calibration
internal_judge_requests_captured: false
new_model_requests: false
improvement_claimed: false
candidate_generation_assessed: false
```

**Internal judge request bodies were not captured.** Audit success establishes source-echo/reason/counterfactual reference checks, not hidden-request capture or prompt improvement. Record zero candidates/early stopping separately from the actual native job. Preserve existing exports/audit JSON and choose new output names when needed. See [official Optimizer concepts](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview).

**Preserved legacy-run warning:** an earlier Prompt Optimizer + Groundedness v18 run stopped at baseline 1.0, but **all six raw judge inputs used the generated `response` itself as `context`**. That self-grounding was not promoted as quality or improvement evidence. It is not a result of the current three policy criteria. Inspect the new job's references and raw outputs separately, without changing the historical scores or records.

## 4. Freeze the Hosted matrix scope

Now evaluate an **actual deployed version**. Direct SDK results from 07 are not Hosted quality evidence.

Sections 5–9 use **workflow / sequential / IQ / account-chat / Invocations**, after verifying IQ itself. Basic Search keyword success alone is not that verification. You may explicitly choose the [separately named local-retrieval matrix in section 10](#10-explicit-local-retrieval-matrix) **instead of sections 5–9**. Both differ from 08's introductory Responses profile and require new packages and azd folders.

The matrix helper accepts **local or IQ retrieval**, but still only **sequential / account-chat / Invocations / v1 or v2**. A local matrix is not IQ validation or an automatic fallback after a failed request.

This Hosted instruction comparison uses **one Sol target**. Optional Luna model comparison remains a separate matched `account-responses` experiment in 02/07. For a fresh environment, select the actual Sol alias:

```bash
python scripts/selfstudy.py models primary=workshop-chat
```

If the existing Sol deployment is `workshop-compare`, use this instead:

```bash
python scripts/selfstudy.py models primary=workshop-compare
```

Choose only the command matching your actual environment. Do not put the GPT-5.5 judge (`workshop-judge`, or the explicitly reused `workshop-optimizer`) in the target map. Keep it fixed across both cohorts. Different base models do not eliminate all bias. Changed model, judge, code, or retrieval conditions require a fresh pair of labels, not edits to old manifests.

The preparation helper derives the owned service name from your saved prefix and `--name`, and supplies that exact matrix name to its child configuration. **No manual `WORKSHOP_HOSTED_AGENT_NAME` setting is needed before preparation.** Keep the same name across v1/v2; `bind-matrix` later reads and saves the actual deployed binding. Use a separate service from 08's introductory Hosted agent.

## 5. Deploy the baseline profile

Explicitly set the small synthetic corpus's retrieval filter before starting. `0` is an IQ retrieval threshold, not an evaluation passing score. Keep it unchanged after baseline collection:

```bash
python scripts/selfstudy.py set WORKSHOP_IQ_RERANKER_THRESHOLD 0
```

```bash
python scripts/workshop.py --script package-hosted --language en --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations
```

Use the returned package path and a **new preparation folder**. The helper reuses the actual project ID/location from 00. Always pass its subcommand-specific `--language en`:

```bash
python scripts/selfstudy.py prepare-hosted --language en --kind matrix --package "ACTUAL-ENGLISH-V1-PACKAGE-PATH" --name matrix-en --run v1
azd deploy "YOUR-PREFIX-matrix-en" --cwd "ACTUAL-MATRIX-V1-ABSOLUTE-PATH"
azd ai agent show "YOUR-PREFIX-matrix-en" --cwd "ACTUAL-MATRIX-V1-ABSOLUTE-PATH" --output json
```

Verify the real runtime identity and roles as in 08. Use that exact service/folder to **read and save the active version and actual Invocations endpoint**:

```bash
python scripts/selfstudy.py bind-matrix --directory "ACTUAL-MATRIX-V1-FOLDER" --service "YOUR-PREFIX-matrix-en"
python scripts/workshop.py --language en benchmark smoke --label matrix-v1-smoke-en --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations --case D01 --model-key primary --confirm-cost
```

Do not run the matrix if smoke fails.

## 6. Collect, evaluate, and trace every dev row

```bash
python scripts/workshop.py --language en benchmark plan --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations
python scripts/workshop.py --language en benchmark collect --label wf-baseline-en --kind workflow --pattern sequential --retrieval iq --prompt v1 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py --language en benchmark evaluate --policy --label wf-baseline-en --confirm-cost
python scripts/workshop.py --language en benchmark report --label wf-baseline-en
python scripts/workshop.py --language en benchmark trace-plan --label wf-baseline-en
python scripts/workshop.py --language en benchmark monitor --label wf-baseline-en
```

Check collection completeness and errors before proceeding. This single Sol target requires **six core dev rows**; per-role calls, retrieval, and judging add further work. Do not remove failed rows from the denominator.

`trace-plan` generates KQL; `monitor` actually queries connected Application Insights. A trace ID in a response is not proof of verified trace export.

## 7. Change only instructions for the candidate

```bash
python scripts/workshop.py --script package-hosted --language en --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations
```

Prepare and deploy the v2 package under the **same agent name**, but in a **new matrix-v2 folder**. Do not overwrite v1:

```bash
python scripts/selfstudy.py prepare-hosted --language en --kind matrix --package "ACTUAL-ENGLISH-V2-PACKAGE-PATH" --name matrix-en --run v2
azd deploy "YOUR-PREFIX-matrix-en" --cwd "ACTUAL-MATRIX-V2-ABSOLUTE-PATH"
azd ai agent show "YOUR-PREFIX-matrix-en" --cwd "ACTUAL-MATRIX-V2-ABSOLUTE-PATH" --output json
```

Verify the actual new version and its runtime permissions, then update the binding to that version and its Invocations endpoint:

```bash
python scripts/selfstudy.py bind-matrix --directory "ACTUAL-MATRIX-V2-FOLDER" --service "YOUR-PREFIX-matrix-en"
python scripts/workshop.py --language en benchmark collect --label wf-candidate-en --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py --language en benchmark compare --baseline wf-baseline-en --candidate wf-candidate-en
python scripts/workshop.py --language en benchmark evaluate --policy --label wf-candidate-en --reference wf-baseline-en --confirm-cost
python scripts/workshop.py --language en benchmark report --label wf-candidate-en
python scripts/workshop.py --language en benchmark monitor --label wf-candidate-en
```

Keep model map, code, language, data, retrieval, concurrency, judge, reasoning, and output cap fixed. If retrieved evidence changes, do not attribute all improvement to instructions alone.

## 8. Calibrate the judge and record regressions

```bash
python scripts/workshop.py --language en calibrate-judge --policy --label policy-calibration-en --confirm-cost --timeout 900
```

If 07 already completed this calibration, reuse it only after checking matching language, judge, and criteria/catalog hashes; do not rerun the command against an existing label. Use a fresh label if conditions changed. Read **24 expected judgments across eight controls and three criteria**. Negative controls should score low; 24 high scores are not the goal. This small calibration does not itself pass dev or matrix quality.

If a genuine dev failure exists, record only that reviewed row:

```bash
python scripts/workshop.py --language en benchmark regression --label wf-baseline-en --row-id "ACTUAL-FAILED-ROW-ID" --regression-label reviewed-failure-en --reviewer "YOUR-LAB-REVIEWER-ID" --reason "Explain the actual response and supporting evidence." --confirm-review
```

The reviewer string is not an Entra-verified business approver. Creating a regression file does not automatically apply it to future collection; later dev runs must explicitly include `--regressions reviewed-failure-en`.

## 9. Preserve results and stop compute

```bash
python scripts/workshop.py --language en benchmark stop-session --label wf-baseline-en
python scripts/workshop.py --language en benchmark stop-session --label wf-candidate-en
```

Keep raw results, exact versions, and business/native/trace/calibration status. **Leave holdout for 15.** It is acceptable to record incomplete acceptance rather than relabel a failed candidate as passing. Stopping compute does not delete retained agents or volumes.

## 10. Explicit local-retrieval matrix

Choose this path deliberately as a separate local-retrieval experiment. It uses **workflow / sequential / local / account-chat / Invocations** and the bundled English policies. Record the actual Search, IQ, Hybrid, Toolbox, and OpenAPI status separately; this matrix neither proves nor replaces those exercises.

Use the model map from section 4, the same-account OpenAI endpoint from 01, and the judge/logging prerequisites. **Skip section 5's `WORKSHOP_IQ_RERANKER_THRESHOLD` setting**; local retrieval does not use it. Keep **`--retrieval local` in every package, plan, smoke, and collection command below**. Never change an existing IQ run's manifest or rename its results to local.

### Local baseline: v1

```bash
python scripts/workshop.py --script package-hosted --language en --kind workflow --pattern sequential --retrieval local --prompt v1 --api account-chat --protocol invocations
python scripts/selfstudy.py prepare-hosted --language en --kind matrix --package "ACTUAL-ENGLISH-LOCAL-V1-PACKAGE-PATH" --name matrix-local-en --run v1
azd deploy "YOUR-PREFIX-matrix-local-en" --cwd "ACTUAL-LOCAL-MATRIX-V1-ABSOLUTE-PATH"
azd ai agent show "YOUR-PREFIX-matrix-local-en" --cwd "ACTUAL-LOCAL-MATRIX-V1-ABSOLUTE-PATH" --output json
```

Use the service/folder actually printed by preparation. Inspect the new active version and grant only the required roles to its actual runtime identity as in 08. A successful earlier Responses agent is not proof this Invocations version works.

```bash
python scripts/selfstudy.py bind-matrix --directory "ACTUAL-LOCAL-MATRIX-V1-FOLDER" --service "YOUR-PREFIX-matrix-local-en"
python scripts/workshop.py --language en benchmark plan --kind workflow --pattern sequential --retrieval local --prompt v1 --api account-chat --protocol invocations
python scripts/workshop.py --language en benchmark smoke --label matrix-local-v1-smoke-en --kind workflow --pattern sequential --retrieval local --prompt v1 --api account-chat --protocol invocations --case D01 --model-key primary --confirm-cost
```

Inspect the reported profile: `retrieval: local`, `api: account-chat`, `protocol: invocations`, and `language: en`. Verify the map contains the intended single Sol target. Stop if the exact version's smoke fails.

```bash
python scripts/workshop.py --language en benchmark collect --label wf-local-baseline-en --kind workflow --pattern sequential --retrieval local --prompt v1 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py --language en benchmark evaluate --policy --label wf-local-baseline-en --confirm-cost
python scripts/workshop.py --language en benchmark report --label wf-local-baseline-en
python scripts/workshop.py --language en benchmark trace-plan --label wf-local-baseline-en
python scripts/workshop.py --language en benchmark monitor --label wf-local-baseline-en
```

Verify **all six core dev cases for Sol**, errors, business/native results, and actual trace queries. Local retrieval removes the Search dependency; it does not remove model, Hosted, judge, or logging costs.

### Local candidate: v2

Keep the same local matrix service name, but prepare a new folder and immutable package:

```bash
python scripts/workshop.py --script package-hosted --language en --kind workflow --pattern sequential --retrieval local --prompt v2 --api account-chat --protocol invocations
python scripts/selfstudy.py prepare-hosted --language en --kind matrix --package "ACTUAL-ENGLISH-LOCAL-V2-PACKAGE-PATH" --name matrix-local-en --run v2
azd deploy "YOUR-PREFIX-matrix-local-en" --cwd "ACTUAL-LOCAL-MATRIX-V2-ABSOLUTE-PATH"
azd ai agent show "YOUR-PREFIX-matrix-local-en" --cwd "ACTUAL-LOCAL-MATRIX-V2-ABSOLUTE-PATH" --output json
```

Check the new runtime identity/permissions and bind only the actual new version:

```bash
python scripts/selfstudy.py bind-matrix --directory "ACTUAL-LOCAL-MATRIX-V2-FOLDER" --service "YOUR-PREFIX-matrix-local-en"
python scripts/workshop.py --language en benchmark plan --kind workflow --pattern sequential --retrieval local --prompt v2 --api account-chat --protocol invocations
python scripts/workshop.py --language en benchmark smoke --label matrix-local-v2-smoke-en --kind workflow --pattern sequential --retrieval local --prompt v2 --api account-chat --protocol invocations --case D01 --model-key primary --confirm-cost
python scripts/workshop.py --language en benchmark collect --label wf-local-candidate-en --kind workflow --pattern sequential --retrieval local --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py --language en benchmark compare --baseline wf-local-baseline-en --candidate wf-local-candidate-en
python scripts/workshop.py --language en benchmark evaluate --policy --label wf-local-candidate-en --reference wf-local-baseline-en --confirm-cost
python scripts/workshop.py --language en benchmark report --label wf-local-candidate-en
python scripts/workshop.py --language en benchmark monitor --label wf-local-candidate-en
python scripts/workshop.py --language en calibrate-judge --policy --label policy-calibration-local-en --confirm-cost --timeout 900
```

Check each stage before continuing. All frozen-condition, row-count, native-judge, trace, calibration, and human-review rules from sections 6–8 still apply. Change only instructions between v1 and v2; both manifests must retain local retrieval and the same model map, corpus, code, language, generation settings, and concurrency.

If recording a real failed row, use its local label, not an IQ label:

```bash
python scripts/workshop.py --language en benchmark regression --label wf-local-baseline-en --row-id "ACTUAL-FAILED-LOCAL-ROW-ID" --regression-label reviewed-local-failure-en --reviewer "YOUR-LAB-REVIEWER-ID" --reason "Explain the actual local-profile response and evidence." --confirm-review
```

Do not invent a failure. Regressions are only reused when explicitly selected in a later dev collection; they are not added to holdout.

```bash
python scripts/workshop.py --language en benchmark stop-session --label wf-local-baseline-en
python scripts/workshop.py --language en benchmark stop-session --label wf-local-candidate-en
```

Keep agents, versions, volumes, and evidence in retention mode. Leave holdout locked until all required dev gates pass, then use **only [15's local Hosted acceptance path](15-capstone-cleanup.md#local-retrieval-hosted-target)** if this is your chosen final target. Stored-result `evaluate`, `compare`, `monitor`, and `verify` commands use the exact local run labels; they do not accept a new `--retrieval` override or perform a replacement collection.

## 11. Separate eight-case policy-lab diagnostics

This is an **explicit eight-case synthetic diagnostic suite, not holdout**. It does not replace the six core dev cases and does not use `--unlock-holdout`. Keep the prepared, smoke-tested exact Hosted deployment, `--prompt v2` profile, and one-Sol model map. Run **only the retrieval path you selected**, with unused result labels.

IQ path:

```bash
python scripts/workshop.py --language en benchmark collect --suite policy-lab --label policy-lab-iq-en --kind workflow --pattern sequential --retrieval iq --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py --language en benchmark evaluate --policy --label policy-lab-iq-en --confirm-cost
python scripts/workshop.py --language en benchmark policy-report --label policy-lab-iq-en --calibration policy-calibration-en
```

For the explicitly selected local path, use this instead; it is not IQ evidence:

```bash
python scripts/workshop.py --language en benchmark collect --suite policy-lab --label policy-lab-local-en --kind workflow --pattern sequential --retrieval local --prompt v2 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py --language en benchmark evaluate --policy --label policy-lab-local-en --confirm-cost
python scripts/workshop.py --language en benchmark policy-report --label policy-lab-local-en --calibration policy-calibration-local-en
```

`policy-report` reads stored results without new inference. Review requested, returned, missing, and error counts, all three scores/reasons, source/reference audits, and matching policy calibration. `policy_compliance` is **higher-is-safer**; a score below 4 is the violation direction. Do not reverse that interpretation or rewrite existing provider `attack_success` flags. Unscored/error rows stay in the denominator.

**Latest diagnostic verification:** the new frozen runtime on **Hosted IQ deployment version 3** produced 8/8 inputs/responses under diagnostic suite version 2, passed **business checks and all three policy criteria**, and verified source audits and 8/8 actual traces. Its six canonical dev rows also passed business/policy/audit/trace checks. These are fresh results, not edits to earlier failures.

Suite version 2 permits additional support only within **explicit `allowed_citations` for PL05, PL06, and PL07 in both languages**. Lists must contain known, unique IDs and include every mandatory reference; answers missing required references or adding unrelated ones remain rejected. PL06's procedure-only question returned **`limit_krw: null`** under corrected v2 instructions. Frozen version-1 results remain readable unchanged, including the earlier extra-citation failures and `150000` response, scores, sources, and labels.

These eight cases are not a new holdout. Stop completed diagnostic sessions by their actual labels and retain resources, but [archive evidence before expiry](advanced/session-files.md).

**Next → [13. Lab safety, managed identities, and Control Plane](13-governance.md)**
