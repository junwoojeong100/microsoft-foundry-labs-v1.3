# Choose models by identity, not by deployment alias

**English** | [한국어](../model-selection.md) · [Course home](../../README.md)

**The default answer model is `gpt-6-sol` / `2026-09-22`.** Start directly with Sol for the first response, Prompt Agents, tools, and Hosted exercises. Add GPT-6 Luna only if you choose a matched model comparison.

## Deploy only when needed

These are **fresh-environment aliases**, not guarantees of the model behind an existing name.

| Role | Actual model/version | Fresh deployment name | When |
|---|---|---|---|
| Default answers, agents, and tools | **gpt-6-sol / 2026-09-22** | `workshop-chat` | 00 |
| Optional comparison | **gpt-6-luna / 2026-09-22** | `workshop-compare` | 02, only if selected |
| Judge | **gpt-5.5 / 2026-04-24** | `workshop-judge` | 07 |
| Embeddings | text-embedding-3-large | `workshop-embedding` | 06 |
| IQ model-based planning/synthesis | **gpt-5.6-luna / 2026-07-09** | `gpt-5.6-luna` | The corresponding exercise in 06 |
| Improvement candidate generation | gpt-5.5 / 2026-04-24 | `workshop-optimizer` | 12 |

**Luna comparison is not a prerequisite for the main path.** If comparing models, explicitly use the same `account-responses` API for both Sol and GPT-6 Luna. Do not mix one model's project API result with the other's account API result.

The judge is **GPT-5.5, a different base model from the GPT-6 targets**, and its **deployment must differ from every target deployment**. Another alias for the same target model is not the intended judge. Do not weaken separation checks. Different base models do not eliminate all evaluation bias; review evidence, row-level explanations, business checks, and calibration.

## Reuse existing deployments without changing them

**An alias is not a model identity.** The existing lab environment already has Sol named `workshop-compare` and GPT-5.5 named `workshop-optimizer`. Do not replace models or delete resources to match the fresh defaults.

Keep the same project, endpoint, and prefix, and explicitly select the actual Sol alias:

```bash
python scripts/selfstudy.py configure --project-id "YOUR-PROJECT-ARM-ID" --endpoint "YOUR-PROJECT-ENDPOINT" --deployment workshop-compare --expected-model gpt-6-sol --prefix "YOUR-UNCHANGED-LAB-PREFIX"
python scripts/selfstudy.py model --role judge --deployment workshop-optimizer
```

The second command reads the existing GPT-5.5 model/version and configures it as judge; it does not create a deployment. Keep this judge out of the target model map.

Only if the existing `workshop-chat` actually contains **GPT-6 Luna / 2026-09-22**, and you choose the optional comparison:

```bash
python scripts/selfstudy.py model --role comparison --deployment workshop-chat
```

Use the table's aliases in a fresh environment and verified actual aliases in an existing one. Do not edit or reuse raw results, evaluations, ownership records, or existing labels. Changed model, judge, or code conditions require a new comparison pair.

## Generation settings

```text
Reasoning effort: low
Output-token cap: 32768
Default answer API: project-responses
Optional model-comparison API: account-responses
```

The cap includes reasoning and final-answer tokens. It is neither actual usage nor prepaid capacity. Keep reasoning and output limits fixed within comparisons.

Prompt Agent reasoning belongs only in its stored **definition**. Do not resend an override with `agent_reference`. The Hosted matrix's separate `account-chat` API conveys equivalent settings through `reasoning_effort` and `max_completion_tokens`.

These limits apply to the lab's answer-generation requests, not a combined budget covering managed judges, IQ planning/synthesis, and Optimizer internals.

## IQ and Optimizer have separate roles

IQ's **`gpt-5.6-luna`** is different from optional comparison model **`gpt-6-luna`**. Do not change Search's planning/synthesis model merely because the default answer model changed. Check the separate Search and Optimizer support lists and actual deployments.

## Comparing costs

Reference figures from launch material checked on 2026-09-27, for **Global Standard, short context, per one million tokens**. They do not replace current contract, region, caching, deployment-type, or long-context prices.

| Model | Input | Output |
|---|---:|---:|
| GPT-6 Sol | USD 2.00 | USD 10.00 |
| Optional GPT-6 Luna | USD 0.10 | USD 0.50 |

GPT-5.5 judging/optimization, Search, Hosted, evaluation, and logs incur separate charges. Lower product pricing and adequate quality for this lab are separate questions.

**Official references:** [GPT-6 models and pricing](https://azure.microsoft.com/en-us/blog/gpt-6-astra-sol-and-luna-for-production-agents-in-microsoft-foundry/) · [Sol model card](https://ai.azure.com/catalog/models/gpt-6-sol) · [Luna model card](https://ai.azure.com/catalog/models/gpt-6-luna) · [Reasoning](https://learn.microsoft.com/azure/foundry/openai/how-to/reasoning) · [Search planning models](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base) · [Optimizer models](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview)
