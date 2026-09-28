# 02. Sol prompts and optional model/Router comparison

**English** | [한국어](../02-models-prompts.md) · [Course home](../../README.md)

**Outcome:** Experience the difference between instructions and knowledge, and compare model choices under fixed conditions.

**Prerequisites:** A real model response from 01. You can add a second model and Router here after checking availability and costs.

## 1. Change only the prompt

Keep the same deployment in Playground and **start a new conversation before each experiment**.

First question:

```text
Help me prepare for a business trip to Busan.
```

Second question:

```text
You help new employees prepare for business trips.
List three things to check before a trip to Busan.
The company policy, travel dates, and duration have not been provided.
Do not guess costs or approval status. Ask for the missing information.
```

Compare answer length, assumptions, and clarifying questions. A clear role, task, constraints, and format can make behavior more consistent.

## 2. Instructions cannot invent knowledge

Ask in a new conversation:

```text
What is Hanbit Technology's domestic business-trip lodging limit for September 2026?
Please provide the official source.
```

Saying it does not know is an appropriate boundary. If the model gives an amount, check whether the original source was supplied. Confidence or a citation-looking string is not proof of correctness.

**Prompts guide behavior; retrieval supplies evidence; fine-tuning changes model weights.** Editing instructions and connecting documents in this course is not fine-tuning.

<a id="3-prepare-the-comparison-model"></a>

## 3. Optionally compare Luna

This section is **optional**. Sol alone is sufficient for the main path. If you choose comparison, use the deployment procedure from 00:

1. In the same Foundry resource's catalog, find **`gpt-6-luna` / `2026-09-22`**.
2. Check Responses, Structured Outputs, regional availability, and quota.
3. Fresh labs use `workshop-compare`. If that name already contains Sol or another model, leave it unchanged and select a verified existing Luna deployment or a new unique name.
4. Record successful creation and the actual model/version.
5. If unavailable or outside your budget, mark model comparison as not run and continue where prerequisites permit. Two aliases for the same model are not a model-performance comparison.

Verify the actual deployed model/version. Insert your **actual Luna alias** below: `workshop-compare` in a fresh environment, or the existing `workshop-chat` only if it actually contains Luna. Luna is not the judge.

```bash
python scripts/selfstudy.py model --role comparison --deployment "ACTUAL-LUNA-DEPLOYMENT"
```

Find the same Foundry account's **Azure OpenAI service-root endpoint**. If the displayed value ends in `/openai/v1`, omit that path:

```bash
python scripts/selfstudy.py set AZURE_OPENAI_ENDPOINT "https://YOUR-FOUNDRY-DOMAIN.openai.azure.com"
```

Generate direct SDK answers using the same Hanbit Technology policies and **account Responses for both models**. Replace both placeholders with aliases whose actual base models you verified:

| Environment | `ACTUAL-SOL-DEPLOYMENT` | `ACTUAL-LUNA-DEPLOYMENT` |
|---|---|---|
| Fresh defaults | `workshop-chat` | `workshop-compare` |
| Reused earlier lab | `workshop-compare` | `workshop-chat`, only if verified as Luna |

```bash
python scripts/workshop.py --model-deployment "ACTUAL-SOL-DEPLOYMENT" --language en answer --api account-responses --prompt v2 --retrieval local --question "What are the domestic business-trip lodging limit and pre-booking procedure for September 2026?" --output outputs/learner-notes-en/02-sol-account.json
python scripts/workshop.py --model-deployment "ACTUAL-LUNA-DEPLOYMENT" --language en answer --api account-responses --prompt v2 --retrieval local --question "What are the domestic business-trip lodging limit and pre-booking procedure for September 2026?" --output outputs/learner-notes-en/02-luna-account.json
```

Keep instructions, question, language, and local evidence identical. `--model-deployment` changes **only this request**, not `.env` or an Azure default. Compare answers, evidence, errors, and usage without ranking models from a single question. Chapter 07 expands to the full dev set.

Use the same reasoning setting and output cap. Luna's lower product price and its accuracy on your task are separate considerations.

## 4. Explore Router

1. Find **Model Router** in the catalog.
2. Read its models/modes, supported regions, APIs, deployment types, and prices.
3. If you choose to run it, create your own dedicated deployment and submit the same question through **that deployment's supported Playground**.
4. Check whether the Router version and selected model are exposed. Otherwise record “selected model not verified.”
5. Never silently replace a failing direct model with Router and count it as success.

Router is a **system that selects models per request**, not one fixed model. Do not force the same project Responses SDK call onto a Router whose API support you have not verified. See [official Router evaluation guidance](https://learn.microsoft.com/azure/foundry/openai/how-to/evaluate-model-router).

## Completion check

- [ ] I can explain the difference between a prompt and knowledge.
- [ ] I can distinguish a model name, version, and deployment name.
- [ ] I recorded whether comparison and Router actually ran.

Reuse additional models in later comparisons. Do not delete `workshop-chat` at this point.

**Next → [03. Prompt Agents and File Search](03-knowledge.md)**
