# How to choose the workshop models

**English** | [한국어](../model-selection.md) · [Course home](../../README.md)

**The starting answer-model candidate is `gpt-6-luna` / `2026-09-22`.** This course favors responsiveness and cost efficiency for short policy queries, repeated evaluations, and tool calls.

Microsoft describes Luna as a smaller, faster model for high-frequency tasks. Sol targets complex knowledge work, coding, and agent workflows, so this guide uses it for **comparison and judging**. Product characteristics are a starting point; judge task-specific quality using your actual dev results.

**Check observed compatibility before continuing.** The source guide records that, in a new Sweden Central project on 2026-09-27, Luna worked through account Responses and model Playground, but project Responses rejected `reasoning.effort` with 400 and returned 500 when it was omitted. Sol's project calls, Prompt Agent, and File Search succeeded in that environment. If you see the same symptom, follow [01's explicit Sol compatibility path](01-foundry.md#distinguish-project-and-account-apis). This is neither a worldwide declaration that Luna is unsupported nor an automatic fallback. It does not establish Luna agent support.

## Deploy only when needed

| Role | Actual model/version | Deployment name | When to prepare it |
|---|---|---|---|
| Starting answer/agent/tool candidate | **gpt-6-luna / 2026-09-22** | `workshop-chat` | 00; verify the actual API path in 01 |
| Comparison / explicit compatibility target | **gpt-6-sol / 2026-09-22** | `workshop-compare` | 02, or earlier for 01; may judge only when not itself a target |
| Separate judge when Sol is a target | **gpt-6-sol / 2026-09-22** | `workshop-judge` | Before native evaluation in 07; reuse for Sol-containing matrices in 12 |
| Embeddings | text-embedding-3-large | `workshop-embedding` | 06 |
| IQ model-based planning/synthesis | gpt-5.6-luna / 2026-07-09 | `gpt-5.6-luna` | The corresponding experiment in 06 |
| Improvement candidate generation | gpt-5.5 / 2026-04-24 | `workshop-optimizer` | 12 |

**Do not deploy everything at once.** Reuse `workshop-compare` as judge only if it is not among the evaluated targets. When Sol `workshop-compare` answers, or appears in a Luna/Sol target matrix, a separate actual `workshop-judge` deployment is **required**, not an unnecessary duplicate.

Native evaluation correctly refuses a judge deployment identical to any target. Create `workshop-judge` as **GPT-6 Sol / 2026-09-22**, verify its deployment and quota/cost, then configure:

```bash
python scripts/selfstudy.py model --role judge --deployment workshop-judge
```

Do not weaken the separation guard or pretend that two labels are distinct deployments. Keep the judge out of the target model map and fixed across comparisons.

Model names and deployment names are different. Code calls `workshop-chat`, whose actual base model should be `gpt-6-luna`. The configuration helper verifies model, version, and provisioning state—not just the alias.

If selecting Sol for compatibility, preserve the same project/prefix, set `--deployment workshop-compare --expected-model gpt-6-sol`, and retain Luna. Future “default model” references mean the actual configured deployment. Even with separate target/judge deployments, Sol-family self-evaluation bias remains; keep deterministic checks and human source review.

## Generation settings

```text
Reasoning effort: low
Output-token cap: 32768
Primary execution API: Responses
```

The cap includes **both reasoning and final-answer tokens**. A short-answer instruction does not itself bound reasoning cost. The cap is a maximum generation allowance, not prepaid or reserved tokens.

32768 gives initial reasoning headroom for the workshop; it does not imply every request consumes that amount. Review actual usage before adjusting. Keep the same cap and reasoning setting during matched comparisons.

Responses, Prompt Agents, MAF, and Hosted use the same generation settings. Prompt Agent reasoning belongs only in the stored **definition**; an `agent_reference` request must inherit it rather than send another override. The matrix's Chat Completions path conveys equivalent settings through `reasoning_effort` and `max_completion_tokens`.

The cap applies to **answer-generation requests sent by this code**, not a combined budget for managed judges, IQ planning/synthesis, Optimizer, or nested-agent internal calls. Review each service's settings, usage, and additional charges separately.

For direct `model`, `answer`, and `collect` calls, `project-responses` is the default; `--api account-responses` is an explicit alternative. A model-only comparison must use the **same API and endpoint** for both models. Account Responses is distinct from the Hosted matrix's `account-chat` profile.

## Why not use GPT-6 for every role?

The Foundry catalog lists Agent v2, tool calling, File Search, and Code Interpreter capabilities for these GPT-6 models. **Catalog support and actual behavior in a region, deployment, API, or portal UI are separate**. Verify the first real request for each chapter.

Azure AI Search knowledge-base planning and Agent Optimizer candidate generation have **separate model support lists**. Do not assume GPT-6 is on them as of the guide's review date. A GPT-6 agent using a Search tool is not the same as Search calling GPT-6 as its own planning model.

## Cost-comparison basis

The official launch material lists these prices for **Global Standard, short-context requests, per one million tokens**:

| Model | Input | Output |
|---|---:|---:|
| GPT-6 Luna | USD 0.10 | USD 0.50 |
| GPT-6 Sol | USD 2.00 | USD 10.00 |

These are **launch-material figures checked on 2026-09-27**, not a substitute for your current contract, region, deployment type, caching, or long-context rates. The whole lab's costs do not necessarily scale by the same ratio. Search, evaluation, Hosted, and logs have separate charges.

**Official references:** [Model launch, use cases, and pricing](https://azure.microsoft.com/en-us/blog/gpt-6-astra-sol-and-luna-for-production-agents-in-microsoft-foundry/) · [Luna model card](https://ai.azure.com/catalog/models/gpt-6-luna) · [Sol model card](https://ai.azure.com/catalog/models/gpt-6-sol) · [Reasoning settings](https://learn.microsoft.com/azure/foundry/openai/how-to/reasoning) · [Search planning models](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base) · [Optimizer models](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview)
