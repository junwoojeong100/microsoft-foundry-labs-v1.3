# 01. Foundry and your first model response

**English** | [한국어](../01-foundry.md) · [Course home](../../README.md#curriculum) · [Help](checkpoints.md)

**Outcome:** Explain Foundry and receive an actual response from your configured **GPT-6 Sol** deployment.

**Prerequisites:** The project, Sol deployment, permissions, and configuration from [00](00-setup.md). Do not add another model or resource in this chapter.

**Where you work:** Foundry Playground → terminal in the workshop folder → result JSON in your editor.

<a id="chapter-map"></a>

**Chapter map**

| Step | Result to check |
|---|---|
| [Start with the concepts](#what-you-are-learning-and-why) | Model, agent, and Foundry distinctions |
| [1. Portal request](#1-make-one-portal-request) | A first Sol response without retrieval |
| [2. Call the same model from code](#2-call-the-same-sol-deployment-from-code) | JSON with the real answer, model, and response ID |
| [3. Implementation types](#3-distinguish-three-implementations) | Prompt Agent, local MAF, and Hosted boundaries |
| [Completion check](#completion-check) | Only model inference has been verified |

## What you are learning and why

An employee asks, “May I book this hotel?” Speed is not enough. The assistant must distinguish dates and policies, show evidence, and respect its lack of approval authority.

| Term | Meaning in this course |
|---|---|
| Model | An engine that understands and generates language |
| Deployment name | The alias code uses to call a model; fresh labs use `workshop-chat` for Sol |
| Agent | A model connected to task instructions and permitted tools |
| Project | A space grouping agents, evaluations, connections, and file operations |
| Foundry | A platform for models, agents, knowledge, tools, evaluation, and operations |

Azure OpenAI inference is one Foundry capability. **Microsoft Agent Framework (MAF) is a code framework**; a framework and a managed platform are not the same object.

## 1. Make one portal request

1. Select your project in Foundry.
2. Open **Build → Models / Deployments → your actual Sol deployment → Playground**. Fresh labs use `workshop-chat`; existing labs use the verified Sol alias from 00.
3. Send the question below.

**Remove Web search from Tools if it was added by default.** This is a model-only request. Recheck unnecessary tools and extra-cost settings in each new tab or conversation.

```text
Write a three-line preparation checklist in English for an employee taking their first domestic business trip.
```

**Check:** a general answer about dates, purpose, and preparation demonstrates the first model call. **It has not searched Hanbit Technology's policies or executed a tool.**

## 2. Call the same Sol deployment from code

Run from the folder containing the README. The runner uses your actual configured Sol deployment:

```bash
python scripts/workshop.py --language en model --question "Write a three-line preparation checklist in English for an employee taking their first domestic business trip." --output outputs/learner-notes-en/01-sol-model.json
```

**Check:** read the real answer, base model/deployment information, response ID, and usage. Empty responses and errors are not success. Identical questions need not produce identical wording.

The core flow is `AIProjectClient → get_openai_client → responses.create`. Verify the actual **gpt-6-sol / 2026-09-22**, not just the alias. If a result file already exists, preserve it and choose a new output filename.

### Distinguish project and account APIs

This first call uses the default **`project-responses`** API. Only if you choose the optional Luna comparison in 02, use the same explicit **`account-responses`** API for both models. Success on one API does not stand in for another, and errors do not trigger an automatic switch.

An intact same-project Sol alias may be preserved, but **do not adopt deleted Sweden aliases or endpoints into NC**. Follow [00's new-project configuration](00-setup.md#8-collect-configuration-from-actual-values) and [the scope of alias reuse](model-selection.md#reuse-existing-deployments-without-changing-them).

## 3. Distinguish three implementations

| Implementation | Where definition/execution lives | Later chapter |
|---|---|---|
| Prompt Agent | Instructions, tools, and an exact version stored in Foundry | 03 |
| Local MAF/workflow | Your Python coordinates work and calls an Azure model | 04–05 |
| Hosted Agent | Your code deployed to the Foundry runtime | 08 |

They use the same synthetic scenario but are different executions. Local results do not prove remote deployment success.

## Completion check

Open `outputs/learner-notes-en/01-sol-model.json` and compare:

- [ ] There is a real answer, not an error or empty response.
- [ ] The actual model/version is `gpt-6-sol / 2026-09-22`, using `project-responses`.
- [ ] I checked the response ID and distinguished inference from retrieval or tool execution.

Use `python scripts/selfstudy.py values` to recheck the saved project and deployment settings.

**Key point:** Foundry connects models, agents, knowledge, tools, evaluation, and operations. This chapter verified only model inference.

For 401/403, check identity, tenant, and data roles. For 404, check the project endpoint and actual deployment name. For 429, check quota. See [Troubleshooting](troubleshooting.md).

---

[← 00. Setup](00-setup.md) · [Course home](../../README.md#curriculum) · [02. Models and prompts →](02-models-prompts.md) · [Chapter map ↑](#chapter-map)
