# Microsoft Foundry Hands-on Guide · v1.5

**English** | [한국어](README.ko.md)

This repository is **the v1.5 successor to [microsoft-foundry-labs](https://github.com/junwoojeong100/microsoft-foundry-labs), which was created in November 2025 just after Microsoft Ignite 2025**. Start here without first installing or completing the previous version.

**Build an AI assistant in your own Azure environment, connect evidence and tools, evaluate it, and deploy it. All workshop code and synthetic data are included.**

You need a **Microsoft Entra ID account, an Azure subscription, and an active subscription Owner role**. Work at your own pace; there is no course time limit. A workshop ZIP does not require a GitHub account or Git.

**Start here → [00. Set up your environment](docs/en/00-setup.md)**

Already started? → [Resume from saved results](docs/en/checkpoints.md#resume-on-another-day)

## Start in this order

1. **Complete 00: download the files, install tools, and configure Azure.** Start there even if you are new to terminals.
2. **Follow one language edition through 01-15.** Check each chapter's **prerequisites**, run each numbered step, inspect its result, then continue. Read sections marked optional, troubleshooting, or existing-environment only when they apply.
3. **Inspect command output and saved results; no separate write-up is required.** Use [resume instructions and checkpoints](docs/en/checkpoints.md) next time. Even if you finish early, follow [15's stopping and cleanup steps](docs/en/15-capstone-cleanup.md#4-stop-running-work-first).

Luna and Router comparisons in 02 are optional. Chapter 14 requires GitHub repository permissions. If another feature is unavailable, **record it as blocked/not run** and continue only where prerequisites are met. This is not an entirely free workshop or a guarantee that every subscription can run every feature.

## What will you build?

A travel-policy assistant for the fictional company **Hanbit Technology**.

> “A hotel for my domestic business trip in September 2026 costs KRW 170,000 per night. May I book it?”

The intended answer explains the **KRW 150,000 limit, team-lead approval required before booking, and supporting documents**. Without evidence, the assistant must not guess or claim to approve, book, or pay.

Foundry connects **models, agents, knowledge, tools, evaluation, and operations** in one Azure platform. You will explore that lifecycle through the same synthetic business case.

Start directly with **GPT-6 Sol**. **GPT-6 Luna is an optional comparison**, and **GPT-5.5 is the judge**, using a different base model and a separate target/judge deployment. Fresh deployments use `workshop-chat`, `workshop-compare`, and `workshop-judge` respectively. Existing aliases may differ: never replace the model behind an existing name or delete it to match these examples. See [Model roles and existing aliases](docs/en/model-selection.md).

![Workshop architecture: models, knowledge, tools, evaluation, and operations](docs/assets/architecture.svg)

The shared diagram shows local CLI/MAF code calling Foundry models and agents, retrieving six synthetic policies through File Search/Search/IQ, and using evaluation, traces, and human review to improve instructions.

## Curriculum

| Step | What you do | Evidence you keep |
|---|---|---|
| [00 Setup](docs/en/00-setup.md) | Prepare tools, a project, a model, and permissions | Your environment |
| [01 First response](docs/en/01-foundry.md) | Call a model in the portal and from code | An actual response |
| [02 Models and prompts](docs/en/02-models-prompts.md) | Compare instructions; optionally compare Luna and Router | A reasoned selection |
| [03 Agents and files](docs/en/03-knowledge.md) | Create a Prompt Agent and use File Search | Exact versions and citations |
| [04 Tools](docs/en/04-tools.md) | Run functions, MCP, and Code Interpreter | Actual tool results |
| [05 Workflows](docs/en/05-workflows.md) | Run sequential, parallel, chat, and pause/resume flows | Execution records |
| [06 Retrieval](docs/en/06-search-iq.md) | Configure Search, IQ, and Hybrid | Retrieved source documents |
| [07 Evaluation](docs/en/07-evaluation.md) | Compare the same questions before and after changes | Quality evidence |
| [08 Deployment](docs/en/08-hosted.md) | Test locally, then deploy a Hosted Agent | A remote version and response |
| [09 Operations](docs/en/09-operations.md) | Inspect traces, Insights, and costs | Request-level observations |
| [10 Shared tools](docs/en/10-toolbox-skills.md) | Connect Toolbox, Skills, and OpenAPI | Reusable, versioned tools |
| [11 State and scheduling](docs/en/11-memory-a2a-routines.md) | Use Memory, A2A, and Routines | State and dispatch records |
| [12 Improvement](docs/en/12-improvement.md) | Evaluate conversations, optimization, and deployed versions | Reviewed candidates |
| [13 Lab safety](docs/en/13-governance.md) | Verify managed AI red teaming, lab guardrails, identities, and inventory | Native run evidence and limitations |
| [14 GitHub OIDC CI/CD](docs/en/14-additional-permissions.md) | Run the included identity-based lab release workflow | Exact version and dev business checks |
| [15 Acceptance and cleanup](docs/en/15-capstone-cleanup.md) | Verify the final target and stop, retain, or remove resources | Results and lifecycle records |

Follow each chapter's **run → verify → next** sequence. [The progress guide](docs/en/checkpoints.md) explains unfamiliar terms, command placeholders, and handling existing results.

## Run in English

Run all commands from **the folder containing this README**. **These are resume commands, after completing `configure` in chapter 00.** For a first run, start with 00 instead.

```bash
python scripts/workshop.py --language en doctor
python scripts/selfstudy.py values
```

`--language en` selects the bundled English prompts, policies, and cases. It goes **before the workshop subcommand**; wrapper options such as `--model-deployment` and `--script` go before it. `selfstudy.py` has no global language flag, but its `prepare-hosted` and `capture` subcommands require their own `--language en` for English work. See [Data and localization](docs/en/data-format.md).

Keep `.venv/` for Python, `.env` for private Azure configuration, and `outputs/` for real results and ownership records. Retain `.selfstudy/` too: it holds personal configuration and deployment preparation. English examples use separate labels and `outputs/learner-notes-en/`. Neither command above invokes a model.

## Ground rules

- Use only the six synthetic policies in `data/knowledge/en/policies.json`; no real company data, secrets, tokens, bookings, payments, or approvals.
- Create services only when needed. Owner does not guarantee quota, regional availability, or preview access; keep organizational protections in place.
- Never replace errors or empty responses with fixtures, or treat one good answer as evidence that the whole lab passed.
- **Even when stopping early, follow [chapter 15](docs/en/15-capstone-cleanup.md).** In retention mode, keep resources and ownership records, disable routines, and stop compute without deleting agents or volumes.

## Validation status and limits

**The September 28, 2026 validation separates execution from final quality acceptance.** New SDK and Hosted dev results passed 6/6 each, but managed Task Adherence returned six rows/five pass/one fail with inconsistent severity/verdict flags. **Final acceptance is held and no new holdout was run.** Optimizer returned no new full candidate, so no improvement or promotion is claimed.

The [live validation report](docs/en/validation-report.md) is reference evidence, not your completion record. Chapter 13's managed AI red teaming cannot be replaced by the custom eight-case diagnostic. The report and relevant chapters retain regional-document discrepancies and historical run details.

<a id="portal-and-cli-summary-videos"></a>

## North Central US portal and CLI summary videos

**Renamed-repository rerun edition: 4:32 each, 31 scenes, silent with captions.** Five authenticated portal scenes accompany this run's actual CLI recordings and labelled saved-evidence reviews. The videos cover new-group creation through evaluation, deployment, and stopping compute, including the native inconsistency and acceptance hold. Login screens and credentials are excluded.

| English | 한국어 |
|---|---|
| [![English summary](docs/assets/videos/foundry-v1.5-summary-en-poster.png)](docs/assets/videos/foundry-v1.5-summary-en.mp4) | [![한국어 요약](docs/assets/videos/foundry-v1.5-summary-ko-poster.png)](docs/assets/videos/foundry-v1.5-summary-ko.mp4) |
| [Watch MP4](docs/assets/videos/foundry-v1.5-summary-en.mp4) · [Captions](docs/assets/videos/foundry-v1.5-summary-en.srt) | [MP4 보기](docs/assets/videos/foundry-v1.5-summary-ko.mp4) · [자막](docs/assets/videos/foundry-v1.5-summary-ko.srt) |

[Recording scope and provenance](docs/en/videos.md) · [Live validation findings](docs/en/validation-report.md). These files show the **new group's portal/CLI rerun**. The previous NC portal edition remains in revision `7b7ca26`, NC CLI in `1d53a68`, and Sweden in `0a8ab50`. Bilingual captions do not imply two complete language-specific reruns.

**Help:** [Troubleshooting](docs/en/troubleshooting.md) · [Feature map](docs/en/feature-map.md) · [Checkpoints](docs/en/checkpoints.md) · [Code reading](docs/en/code-reading.md) · [Official sources](docs/en/sources.md) · [Next steps](docs/en/next-steps.md)
