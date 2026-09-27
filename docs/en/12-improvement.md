# 12. Conversation evaluation, Optimizer, and deployment quality

**English** | [한국어](../12-improvement.md) · [Course home](../../README.md)

**Outcome:** Evaluate whole conversations and compare improvement candidates and actual Hosted versions using evidence.

**Prerequisites:** Judge/dev results from 07, Hosted preparation from 08, the same-account OpenAI endpoint, and logging from 09. The IQ matrix also needs working Search/IQ from 06; the explicitly selected local matrix does not. Check costs for each feature. **Do not open holdout in this chapter.**

## Choose the matrix retrieval mode explicitly

Conversation evaluation and Optimizer can proceed without Search when their own model, permission, and budget prerequisites are met. Before starting a Hosted matrix, choose one mode and keep it fixed through v1, v2, and final acceptance:

| Setting | IQ path | Search-unavailable path |
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
3. Keep the configured answer deployment—initially Luna, or explicitly selected Sol—and the separate Sol judge from 07. When `workshop-compare` is a target, use `workshop-judge`; do not bypass the target/judge deployment-separation guard. Optimizer has a separate support list; do not assume GPT-6 is a valid replacement for its candidate-generation model.
4. Prepare extension inputs if they do not already exist for this prefix/language:

```bash
python scripts/selfstudy.py model --role optimizer
python scripts/workshop.py --language en prepare-extensions --label extensions-en
```

Inspect the **six dev rows** and reference fields in `outputs/extensions-en/optimizer-dev.jsonl`. If prepared in 10, verify hashes and prefix and reuse them instead of rerunning creation. Never include holdout.

## 3. Optimize instructions only

1. Create a **separate owned Prompt Agent** using the same English synthetic policies/instructions as 03. Distinguish it with a name such as `<prefix>-optimize-en`.
2. Select **Optimize / Create optimization run → Agent**.
3. Pin the actual target version and answer model.
4. Optimize **instructions only**, with at most **two candidates**.
5. Upload the prepared dev data and verify the `query`/`context`/`ground_truth` columns required by the evaluators. The current Prompt Agent wizard does not remap column names. The generated answer supplies the evaluator's response input; never put reference answers into the agent input.
6. Review cost and expected call scope, then submit once.
7. Read instruction differences, all rows, and evaluation results for the baseline and every candidate.

There may be no candidate or no improvement. A run incorrectly mapping reference context to the answer itself is not promotion evidence. Where available, export raw judge inputs and compare them:

```bash
python scripts/workshop.py --script export-evaluation --language en --evaluation-id "ACTUAL-EVALUATION-ID" --run-id "ACTUAL-EVALUATION-RUN-ID" --expected-rows 6 --label optimizer-raw-en --require-judge-inputs
```

If permissions/features prevent inspecting raw inputs, record the limitation and do not automatically promote. See [official Optimizer concepts](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview).

**Observed validation issue:** this environment's Prompt Optimizer + Groundedness v18 run stopped early at a baseline score of 1.0, but **all six raw judge inputs used the generated `response` itself as `context`**. That is self-grounding, not valid evidence of grounding or improvement. `judge_inputs_available: true` checks availability, not reference correctness. Compare the content with the original dataset's `context` column. Preserve the original scores and do not promote such a run.

## 4. Freeze the Hosted matrix scope

Now evaluate an **actual deployed version**. Direct SDK results from 07 are not Hosted quality evidence.

Sections 5–9 use **workflow / sequential / IQ / account-chat / Invocations**. If Search is blocked, explicitly choose the [separately named local-retrieval matrix in section 10](#10-explicit-local-retrieval-matrix) **instead of sections 5–9**. Both are different from 08's introductory Responses profile and require new packages and azd folders.

The matrix helper accepts **local or IQ retrieval**, but still only **sequential / account-chat / Invocations / v1 or v2**. A local matrix is not IQ validation or an automatic fallback after a failed request.

Start with one actual model if needed. If both are prepared, explicitly map their real deployment names:

```bash
python scripts/selfstudy.py models primary=workshop-chat comparison=workshop-compare
```

This writes JSON configuration consistently across operating systems. For one model, omit `comparison=...` and set `primary` to the actual configured deployment; if Sol is the default, use `primary=workshop-compare`. The configured default must appear in the map, and two keys must not alias the same deployment.

The judge must be separate from **every deployment in this map**, not just the default. If it includes `workshop-compare`, first configure the actual `workshop-judge` deployment as in [07](07-evaluation.md#4-prepare-the-judge-model), and keep that judge fixed for both cohorts. Separate Sol deployments still share model-family bias.

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
python scripts/workshop.py --language en benchmark evaluate --label wf-baseline-en --confirm-cost
python scripts/workshop.py --language en benchmark report --label wf-baseline-en
python scripts/workshop.py --language en benchmark trace-plan --label wf-baseline-en
python scripts/workshop.py --language en benchmark monitor --label wf-baseline-en
```

Check collection completeness and errors before proceeding. Two models yield **12 dev rows**; per-role calls, retrieval, and judging add further work. Do not remove failed rows from the denominator.

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
python scripts/workshop.py --language en benchmark evaluate --label wf-candidate-en --reference wf-baseline-en --confirm-cost
python scripts/workshop.py --language en benchmark report --label wf-candidate-en
python scripts/workshop.py --language en benchmark monitor --label wf-candidate-en
```

Keep model map, code, language, data, retrieval, concurrency, judge, reasoning, and output cap fixed. If retrieved evidence changes, do not attribute all improvement to instructions alone.

## 8. Calibrate the judge and record regressions

```bash
python scripts/workshop.py --language en calibrate-judge --label judge-calibration-en --reference wf-candidate-en --confirm-cost
```

Use the two known good/bad examples to check groundedness judgments. **The bad example should fail; two native “passes” are not the goal.** Expected discrimination is `correct: 2` and `gate_passed: true`. Such a small calibration does not establish the judge's overall accuracy.

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

Choose this path deliberately when Search/IQ cannot be provisioned, such as the fixed-region blockers in 06. It uses **workflow / sequential / local / account-chat / Invocations** and the bundled English policies. Search, IQ, Hybrid, and Search-based Toolbox/OpenAPI remain **blocked**, regardless of this matrix's result.

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

Inspect the reported profile: `retrieval: local`, `api: account-chat`, `protocol: invocations`, and `language: en`. Stop if the exact version's smoke fails. For additional model keys, run separately labeled smoke checks against those actual keys before full collection.

```bash
python scripts/workshop.py --language en benchmark collect --label wf-local-baseline-en --kind workflow --pattern sequential --retrieval local --prompt v1 --api account-chat --protocol invocations --concurrency 1 --confirm-cost
python scripts/workshop.py --language en benchmark evaluate --label wf-local-baseline-en --confirm-cost
python scripts/workshop.py --language en benchmark report --label wf-local-baseline-en
python scripts/workshop.py --language en benchmark trace-plan --label wf-local-baseline-en
python scripts/workshop.py --language en benchmark monitor --label wf-local-baseline-en
```

Verify **six dev cases per model**, all errors, business/native results, and actual trace queries. Two models require 12 rows. Local retrieval removes the Search dependency; it does not remove model, Hosted, judge, or logging costs.

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
python scripts/workshop.py --language en benchmark evaluate --label wf-local-candidate-en --reference wf-local-baseline-en --confirm-cost
python scripts/workshop.py --language en benchmark report --label wf-local-candidate-en
python scripts/workshop.py --language en benchmark monitor --label wf-local-candidate-en
python scripts/workshop.py --language en calibrate-judge --label judge-local-calibration-en --reference wf-local-candidate-en --confirm-cost
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

**Next → [13. Safety, permissions, networking, and Control Plane](13-governance.md)**
