# 07. Business and Foundry evaluation

**English** | [한국어](../07-evaluation.md) · [Course home](../../README.md)

**Outcome:** Compare instructions on the same cases and apply a Foundry judge to actual responses.

**Prerequisites:** Your configured model, Hanbit Technology data, and real SDK responses. This chapter evaluates **direct SDK inference with retrieval performed before generation**. It is not the managed agent from 03 or a later Hosted version.

## 1. Keep dev and holdout separate

| Dataset | Purpose |
|---|---|
| Six dev cases | Failure analysis, instruction improvement, and comparison |
| Four holdout cases | Final acceptance after freezing a candidate |
| Calibration | Check how the judge distinguishes known good and bad examples |

Do not open holdout until 15. Do not put expected-answer fields in model inputs. `--language en` selects `data/evaluation/en/`; it is not just an output-language hint.

## 2. Collect the baseline

```bash
python scripts/workshop.py --language en collect --split dev --label baseline-en --prompt v1 --retrieval local
python scripts/workshop.py --language en evaluate --label baseline-en
```

Open `manifest.json`, `responses.jsonl`, and `business-evaluation.json` under `outputs/baseline-en/`.

Read `total`, `passed`, `errors`, `business_gate_passed`, and **every check for all six cases**. This is deterministic business validation, not an LLM judge.

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

## 4. Prepare the judge model

The native evaluator requires a judge deployment **different from every target deployment**. It correctly refuses to judge a target using that same deployment. Do not weaken the guard, rename result files, or use two labels pointing to one deployment.

**If the only target is Luna `workshop-chat`**, reuse **`workshop-compare` — GPT-6 Sol / 2026-09-22** from 02. If missing, deploy it using 02's procedure, then register it:

```bash
python scripts/selfstudy.py model --role judge --deployment workshop-compare
```

**If Sol `workshop-compare` is the target**, as in 01's compatibility path, or is included in a Luna/Sol matrix:

1. Create another actual **GPT-6 Sol / 2026-09-22** deployment in the same Foundry account, named **`workshop-judge`**.
2. Review its quota, deployment type, and costs. Wait for `Succeeded` and verify the actual model/version.
3. Register this separate judge; do not include it in the target model map:

```bash
python scripts/selfstudy.py model --role judge --deployment workshop-judge
```

The two Sol deployments are intentional: target/judge deployment separation is mandatory, even though their model family is the same. Keep the chosen judge fixed across baseline/candidate and later native comparisons. Preserve earlier evaluations rather than editing their judge metadata to match a new configuration.

After configuring the appropriate judge:

```bash
python scripts/workshop.py --language en cloud-evaluate --label candidate-en --timeout 300 --confirm-cost
```

This evaluates previously collected responses. **It does not collect new target answers.** Keep native evaluation/run IDs, all raw per-row scores and errors, and the actual judge configuration.

Find the same run under Foundry **Evaluation** and verify row count and completion state. `Partial`, missing evaluators, and empty results are not completion. A general Relevance judge may penalize an appropriate “insufficient evidence” answer; read its explanation.

If Sol judges Sol-generated answers through separate deployments, **model-family self-evaluation bias remains**. Deployment separation does not make the judge independent at the model-family level. Do not omit deterministic checks or human source review.

### Interpret completion and quality separately

One verified run completed all six native candidate rows with **groundedness 6/6 and relevance 5/6**. Its baseline and candidate each passed **6/6 dev cases on the business gate**, so **no business pass-rate improvement was demonstrated**. Completion is not an all-metrics pass.

Keep the actual per-row explanations and the nonpassing relevance result; do not relabel this as a perfect score or change thresholds. These observations do not replace your own English run's evidence, nor do they establish general model quality or production approval.

## 5. Add the custom business rubric and compare runs

If the Preview feature is available and you accept the extra cost:

```bash
python scripts/workshop.py --language en cloud-evaluate --label baseline-en --business-evaluator --timeout 300 --confirm-cost
python scripts/workshop.py --language en cloud-evaluate --label candidate-en --business-evaluator --reference baseline-en --timeout 300 --confirm-cost
```

Verify the actual evaluator list, all six rows, and agreement with local business checks. Preserve missing custom results as failures. Do not selectively rerun only low-scoring cases.

## 6. Extend to model comparison

If both deployments' project APIs work and the default `candidate-en` was actually generated by Luna, collect the second deployment under the **same v2/local/dev conditions**:

```bash
python scripts/workshop.py --model-deployment workshop-compare --language en collect --split dev --label model-compare-en --prompt v2 --retrieval local
python scripts/workshop.py --language en evaluate --label model-compare-en
python scripts/workshop.py --language en compare --baseline candidate-en --candidate model-compare-en --variable model
```

**If you used 01's Sol compatibility path**, collecting Sol again is not a model comparison. Instead use a separate matched pair with **account Responses for both models**, as in 02:

```bash
python scripts/workshop.py --model-deployment workshop-chat --language en collect --api account-responses --split dev --label model-luna-en --prompt v2 --retrieval local
python scripts/workshop.py --model-deployment workshop-compare --language en collect --api account-responses --split dev --label model-sol-en --prompt v2 --retrieval local
python scripts/workshop.py --language en evaluate --label model-luna-en
python scripts/workshop.py --language en evaluate --label model-sol-en
python scripts/workshop.py --language en compare --baseline model-luna-en --candidate model-sol-en --variable model
```

Mixing account and project API results changes more than the model. Fix `inference.api` and the actual endpoint in collection manifests as well as reasoning and output limits. Review quality, errors, tokens, and latency together. Explain why you change or keep the model. Do not use Router or another provider as an error fallback.

## Completion check

Keep six real rows, a before/after comparison, judge results, and your own review. **Do not open holdout yet.** Preserve the candidate and its exact configuration.

**Next → [08. Local Hosted execution and Azure deployment](08-hosted.md)**
