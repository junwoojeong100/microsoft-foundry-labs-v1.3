# 02. Models, prompts, comparison, and Router

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

## 3. Prepare the comparison model

Repeat the model-deployment procedure from 00:

1. In the same Foundry resource's catalog, find **`gpt-6-sol` / `2026-09-22`**.
2. Check Responses, Structured Outputs, regional availability, and quota.
3. Use a **new deployment name**, `workshop-compare`, instead of changing an existing deployment.
4. Record successful creation and the actual model/version.
5. If unavailable or outside your budget, mark model comparison as not run and continue where prerequisites permit. Two aliases for the same model are not a model-performance comparison.

Verify the actual deployed model/version. In 07, this Sol deployment may be reused as judge **only when it is not a target deployment**. If Sol is the configured answer model or part of the evaluated model matrix, prepare the separate `workshop-judge` deployment described there:

```bash
python scripts/selfstudy.py model --role comparison
```

First generate direct SDK answers with Hanbit Technology's policies. Set the same account's `AZURE_OPENAI_ENDPOINT` as checked in 01, and use **account Responses for both models**. Name both deployments explicitly, even if you selected Sol as the configured default:

```bash
python scripts/workshop.py --model-deployment workshop-chat --language en answer --api account-responses --prompt v2 --retrieval local --question "What are the domestic business-trip lodging limit and pre-booking procedure for September 2026?" --output outputs/learner-notes-en/02-model-a.json
python scripts/workshop.py --model-deployment workshop-compare --language en answer --api account-responses --prompt v2 --retrieval local --question "What are the domestic business-trip lodging limit and pre-booking procedure for September 2026?" --output outputs/learner-notes-en/02-model-b.json
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
