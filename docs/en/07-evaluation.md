# 07. Business and Foundry evaluation

**English** | [한국어](../07-evaluation.md) · [Course home](../../README.md)

**Outcome:** Compare instructions on the same cases and apply a Foundry judge to actual responses.

**Prerequisites:** Your configured Sol deployment, Hanbit Technology data, and real SDK responses. This chapter evaluates **direct SDK inference with retrieval performed before generation**. It is not the managed agent from 03 or a later Hosted version.

Labels below are fresh-lab examples. If results already exist, choose new baseline/candidate labels and use them consistently in every later reference. Never overwrite files or scores from earlier model, judge, or code conditions.

**Order:** collect/check baseline → collect/compare candidate → prepare judge → calibrate and evaluate policies. First compare the bundled `v1`/`v2` instructions; **do not change code or source documents between runs**. Historical scores and failures are in the separate [validation report](validation-report.md).

## 1. Keep dev and holdout separate

| Dataset | Purpose |
|---|---|
| Six dev cases | Failure analysis, instruction improvement, and comparison |
| Four holdout cases | Final acceptance after freezing a candidate |
| Eight policy calibration controls | Check three criteria on positive, negative, abstention, and counterfactual controls |
| Eight policy-lab cases | A separate synthetic diagnostic suite in 12, not holdout |

Do not open holdout until 15. Do not put expected-answer fields in model inputs. `--language en` selects `data/evaluation/en/`; it is not just an output-language hint.

## 2. Collect the baseline

```bash
python scripts/workshop.py --language en collect --split dev --label baseline-en --prompt v1 --retrieval local
python scripts/workshop.py --language en evaluate --label baseline-en
```

Open `manifest.json`, `responses.jsonl`, and `business-evaluation.json` under `outputs/baseline-en/`.

Read `total`, `passed`, `errors`, `business_gate_passed`, and **every check for all six cases**. This is deterministic business validation, not an LLM judge.

Exit code 1 with `business_gate_passed: false` can mean the evaluator **found an incorrect answer**, provided all six responses exist without request errors. Analyze that failure before comparing the candidate. Missing responses or authentication/API errors require resolving the cause, not blindly collecting again.

| Case | Check |
|---|---|
| D01 | Current lodging limit: KRW 150,000 / TRAVEL-2026 |
| D02 | Historical lodging limit: KRW 120,000 / TRAVEL-2025 |
| D03 | A KRW 170,000 hotel requires advance approval |
| D04 | Meals: KRW 30,000/day |
| D05 | Insufficient evidence for international travel |
| D06 | Do not obey demands to ignore rules and claim approval |

Record actual failed IDs and reasons; do not copy a hypothetical failure ID:

```bash
python scripts/workshop.py --language en feedback --label baseline-en --case "ACTUAL-FAILED-CASE-ID" --reason "Explain the actual response and failed check."
```

This creates a pending-review record, not business approval. If all cases pass, record that review in the workbook instead of inventing a failure.

## 3. Collect a matched candidate

Compare `prompts/en/v1.txt` and `prompts/en/v2.txt`. These are the two instruction sets. Keep model, code, source documents, questions, language, and retrieval unchanged.

```bash
python scripts/workshop.py --language en collect --split dev --label candidate-en --prompt v2 --retrieval local
python scripts/workshop.py --language en evaluate --label candidate-en
python scripts/workshop.py --language en compare --baseline baseline-en --candidate candidate-en --variable prompt
```

Inspect the conditions, both metrics, and `changed_context_cases` in `comparison-vs-baseline-en.json`. Do not edit raw responses, scores, or hashes. An unchanged score can legitimately mean “no improvement demonstrated on these six cases.”

If you changed code, collect a new baseline/candidate pair with that same code. Do not lower the rubric or remove error rows to manufacture improvement.

A file still named `v2` is not the same frozen instruction if its bytes/hash changed. Preserve earlier responses, packages, agent versions, and labels, and compare new executions that actually use the revised instructions.

## 4. Prepare the judge model

1. In a fresh environment, deploy **`gpt-5.5` / `2026-04-24`** as **`workshop-judge`** in the same Foundry account.
2. Verify its actual base model, version, cost, and completed creation. It must use a **different base model and deployment** from the Sol target.
3. Register the actual alias as judge. This metadata/configuration command does not create a deployment:

```bash
python scripts/selfstudy.py model --role judge --deployment workshop-judge
```

<details>
<summary>Existing environments only: reuse an existing GPT-5.5 judge alias</summary>

After verifying `workshop-optimizer` is GPT-5.5 / 2026-04-24 in the same intact project, use the following **instead**. The fresh-environment default is `workshop-judge`:

```bash
python scripts/selfstudy.py model --role judge --deployment workshop-optimizer
```

</details>

If an earlier `workshop-judge` contains Sol, leave it unchanged. Do not put the judge in the target model map, weaken separation checks, or infer the base model from an alias. Keep the judge fixed across comparable runs and preserve previous evaluation metadata.

GPT-5.5 differs from the GPT-6 targets, but **this does not eliminate all evaluation bias**. Review actual sources, row-level explanations, business checks, and calibration.

### Interpret completion and quality separately

If baseline and candidate both pass 6/6 dev cases, no business pass-rate improvement has been demonstrated. Completion is not an all-metrics pass. Keep actual explanations and nonpassing criteria; do not relabel a result as perfect or change thresholds to fit it.

## 5. Evaluate policies with audited original references

Prepare a new input label. `--policy` is a separate mode; it does not rewrite earlier Skill inputs or legacy evaluation results.

```bash
python scripts/workshop.py --language en prepare-extensions --policy --label policy-inputs-en
python scripts/workshop.py --language en calibrate-judge --policy --label policy-calibration-en --confirm-cost --timeout 900
```

Inspect `optimizer-dev.jsonl`, `policy-evaluator-definitions.json`, and the input manifest. `ground_truth` contains a **trusted original-reference envelope** for the evaluator, not answer material to pass to the target agent.

| Criterion | What it checks | Passing direction |
|---|---|---|
| `policy_groundedness` | Agreement with the supplied original evidence | At least 4; higher is better |
| `policy_helpfulness` | Useful guidance, clarification, or appropriate abstention | At least 4; higher is better |
| `policy_compliance` | Following policy without false approval claims | At least 4; higher is better |

Canonical evaluator output is integer **`result` (1–5)** and string **`reason`**. Eight controls × three criteria test 24 expected judgments. Bad answers should score low: **24/24 agreement does not mean all 24 scores should be at least 4**. Inspect correct abstention, false-approval, and counterfactual discrimination. Korean calibration success is not English calibration evidence.

These criteria have fixed semantics different from legacy generic Relevance. Appropriate abstention can be useful under `policy_helpfulness`. Do not rename old Relevance scores as policy scores or calculate improvement by subtracting numbers from different criteria.

Evaluate the complete dev responses **collected under new labels** above. Replace both example labels consistently with your actual new names:

```bash
python scripts/workshop.py --language en cloud-evaluate --policy --label baseline-en --confirm-cost --timeout 900
python scripts/workshop.py --language en cloud-evaluate --policy --label candidate-en --reference baseline-en --confirm-cost --timeout 900
```

This judges saved target responses; **it does not perform new target inference**. Preserve the returned `foundry-policy/` results, including `cloud-evaluation-raw.json`, `cloud-evaluation-results.json`, and `policy-reference-audit.json`. Verify all three criteria on every row, source hashes, and the complete `reference_id` echoed in the returned input and `reason`.

The audit checks **submitted sources and echoed reference IDs**, not a capture of every hidden judge request. Do not turn partial results, errors, missing criteria, wrong references, or self-grounding (`context=response`) into passes. Do not combine `--policy` with `--business-evaluator`, or relabel older Relevance/grounding scores and two-fixture calibration as policy evidence.

**D01 lesson:** A fact somewhere in the repository is not automatically evidence for this response. Without actually retrieving `APPROVAL-01`, do not invent approver details such as “team lead.” Never add documents to the original source list or `ground_truth` afterward to justify an answer. If another retrieval is needed, record it as a new run with a new label.

## 6. Optional Sol/Luna model comparison

Run this only if you selected the optional Luna comparison in 02. Verify actual aliases and the same-account endpoint, then collect a new pair with **the same v2/local/dev/account-responses conditions**. Do not reuse the earlier Sol project-API candidate as one side.

```bash
python scripts/workshop.py --model-deployment "ACTUAL-SOL-DEPLOYMENT" --language en collect --api account-responses --split dev --label model-sol-en --prompt v2 --retrieval local
python scripts/workshop.py --model-deployment "ACTUAL-LUNA-DEPLOYMENT" --language en collect --api account-responses --split dev --label model-luna-en --prompt v2 --retrieval local
python scripts/workshop.py --language en evaluate --label model-sol-en
python scripts/workshop.py --language en evaluate --label model-luna-en
python scripts/workshop.py --language en compare --baseline model-sol-en --candidate model-luna-en --variable model
```

Mixing account and project API results changes more than the model. Fix `inference.api`, the actual endpoint, reasoning, and output limits. This optional comparison does not automatically change the configured Sol target or judge. Review quality, errors, tokens, and latency together. Do not use Router or another provider as an error fallback.

## Completion check

Keep six real rows, a before/after comparison, judge results, and your own review. **Do not open holdout yet.** Preserve the candidate and its exact configuration.

**Next → [08. Local Hosted execution and Azure deployment](08-hosted.md)**
