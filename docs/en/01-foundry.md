# 01. Foundry and your first model response

**English** | [한국어](../01-foundry.md) · [Course home](../../README.md)

**Outcome:** Explain Foundry and receive an actual response from your deployed model.

**Prerequisites:** The project, model, permissions, and configuration from [00](00-setup.md). No additional resource is needed unless the explicit compatibility path below is necessary.

## What you are learning and why

An employee asks, “May I book this hotel for a business trip?” Speed alone is not enough. The assistant must know the policy, distinguish effective dates, show evidence, and respect its lack of approval authority.

| Term | Meaning in this course |
|---|---|
| Model | An engine that understands and generates language |
| Deployment name | The name your code uses to call that model, such as `workshop-chat` |
| Agent | An assistant connecting a model to task instructions and permitted tools |
| Project | A space grouping agents, evaluations, connections, and file operations |
| Foundry | A platform covering models, agents, knowledge, tools, evaluation, and operations |

Azure OpenAI model inference is one capability of this platform. Microsoft 365 Copilot provides a work experience; Copilot Studio provides a low-code authoring environment; **Microsoft Agent Framework (MAF) is a code framework**. These are not interchangeable products.

## 1. Make one portal request

1. Select your project in Foundry.
2. Open **Build → Models / Deployments → workshop-chat → Playground**.
3. Send the question below.

**Remove Web search from Tools if it was added by default.** This exercise is a model-only request, without unnecessary Bing calls, extra cost, or data transfer. Recheck tool settings in a new tab or conversation.

```text
Write a three-line preparation checklist in English for an employee taking their first domestic business trip.
```

A general answer about dates, purpose, and preparation is a successful first model call. **It has not searched Hanbit Technology's policies or connected to business systems.**

## 2. Call the same deployment from code

Run from the v1.5 root in your workshop terminal:

```bash
python scripts/workshop.py --language en model --question "Write a three-line preparation checklist in English for an employee taking their first domestic business trip." --output outputs/learner-notes-en/01-model.json
```

The real result is at `outputs/learner-notes-en/01-model.json`; use the path printed by the runner.

Read the answer, actual model/deployment information, response ID, and usage. Identical questions do not need to produce identical wording. Empty responses and errors are not success.

The core flow is `AIProjectClient → get_openai_client → responses.create`. Understand the connection to **your project's actual deployment** rather than memorizing library internals.

### Distinguish project and account APIs

Portal success and project API success are separate observations. If the project request reports `Unsupported parameter: reasoning.effort`, or still returns 500 when the setting is omitted, preserve the original error. Do not recreate the model or automatically strip reasoning settings.

Check the **Azure OpenAI endpoint** on the same Foundry home and configure only its service root. If the displayed value ends in `/openai/v1`, omit that path portion:

```bash
python scripts/selfstudy.py set AZURE_OPENAI_ENDPOINT "https://YOUR-FOUNDRY-DOMAIN.openai.azure.com"
python scripts/workshop.py --language en model --api account-responses --question "Write a three-line preparation checklist in English for an employee taking their first domestic business trip." --output outputs/learner-notes-en/01-model-account.json
```

This explicitly chooses **account Responses for the same deployment**. Record `inference_api: account-responses`. It does not prove that project assets such as Prompt Agents or File Search work. Only `model`, `answer`, and `collect` accept this option; `project-responses` remains the default, with no automatic switch after errors.

**If the same symptom occurs in Sweden Central:** first prepare `workshop-compare` (**GPT-6 Sol / 2026-09-22**) using [02's deployment steps](02-models-prompts.md#3-prepare-the-comparison-model). Probe it once through the project API:

```bash
python scripts/workshop.py --model-deployment workshop-compare --language en model --question "Say hello in one English sentence." --output outputs/learner-notes-en/01-sol-project-check.json
```

After verifying success, **explicitly select Sol as the default execution deployment for chapter 03 onward**. Use the **same project ID, endpoint, and prefix** as in 00:

```bash
python scripts/selfstudy.py configure --project-id "YOUR-PROJECT-ARM-ID" --endpoint "YOUR-PROJECT-ENDPOINT" --deployment workshop-compare --expected-model gpt-6-sol --prefix "lab-yourname-0927"
```

Keep the existing Luna deployment. From this point, “default model” means your actual configured model; do not claim to have validated Luna's agent path. If agents or results already exist, choose new owned names and labels, and pass the same `--name` when creating and invoking the agent.

**Before native evaluation in 07, prepare a separate judge deployment.** When `workshop-compare` is the Sol target, it cannot also be the judge: the evaluator correctly rejects a judge deployment identical to any target. Deploy **GPT-6 Sol / 2026-09-22** separately as `workshop-judge`, review quota/cost, and verify creation before registering it:

```bash
python scripts/selfstudy.py model --role judge --deployment workshop-judge
```

This is required deployment separation, not a reason to weaken the guard. Sol still belongs to the same model family on both sides, so record self-evaluation bias and retain independent business checks and human source review. See [07's judge preparation](07-evaluation.md#4-prepare-the-judge-model).

This compatibility observation is specific to the tested environment: **Luna 2026-09-22 worked in model Playground and account Responses, but project Responses rejected reasoning and returned 500 without it; Sol 2026-09-22 worked through project Responses**. It is neither a worldwide support determination nor an automatic fallback.

## 3. Distinguish three implementations

| Implementation | Where definition/execution lives | Later chapter |
|---|---|---|
| Prompt Agent | Instructions, tools, and versions stored in Foundry | 03 |
| Local MAF/workflow | Python coordinates the work locally; the model runs in Azure | 04–05 |
| Hosted Agent | Your code deployed to the Foundry runtime | 08 |

They use the same synthetic scenario but are not the same object. Do not reuse local results as proof of remote deployment success.

## Record and verify

Record the project, base model/version, deployment name, API, response ID, and result file in your workbook.

**Explain it yourself:** “Foundry is ______. Beyond model inference, it also handles ______.”

**If blocked:** For 401/403, check the user, tenant, and data roles. For 404, check the project endpoint and **deployment name**. For 429, check quota first. See [Troubleshooting](troubleshooting.md).

**Next → [02. Models, prompts, comparison, and Router](02-models-prompts.md)**
