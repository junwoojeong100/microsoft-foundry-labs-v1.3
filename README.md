# Microsoft Foundry Hands-on Guide · v1.5

**English** | [한국어](README.ko.md)

Build a **travel-policy assistant** in your own Azure environment. Connect evidence and tools, evaluate its answers, then deploy it. All workshop code and synthetic data are included.

This is the successor to [microsoft-foundry-labs](https://github.com/junwoojeong100/microsoft-foundry-labs), created in November 2025 just after Microsoft Ignite 2025. You do not need to install or complete the previous version first.

| What you need now | Go to |
|---|---|
| Start for the first time | **[00. Set up your environment](docs/en/00-setup.md)** |
| Continue an existing lab | [Resume from saved results](docs/en/checkpoints.md#resume-on-another-day) |
| Find a chapter | [Full curriculum](#curriculum) |
| Resolve an error | [Troubleshooting](docs/en/troubleshooting.md) |
| Finish for today | **[Stop work and review costs](docs/en/15-capstone-cleanup.md#4-stop-running-work-first)** |

**Requirements:** a Microsoft Entra ID account, an Azure subscription, and an active subscription Owner role.

A provided ZIP needs neither a GitHub account nor Git. Work at your own pace; there is no course time limit.

> [!WARNING]
> **This is not a free workshop.** Model calls and services can incur charges. Review running work, schedules, and retained resources even when stopping early.

## Start in this order

1. **[00. Set up your environment](docs/en/00-setup.md)** — download the files, install tools, and configure Azure. Start here even if you are new to terminals.
2. **Continue from [01. First response](docs/en/01-foundry.md)** — follow one language edition in order. Run one step and inspect its result before continuing.
3. **Finish with [15. Stop and clean up](docs/en/15-capstone-cleanup.md#4-stop-running-work-first)** — even if you stop before the last chapter. Next time, follow the [resume steps](docs/en/checkpoints.md#resume-on-another-day).

No separate write-up or submission is required. Command output and saved results are your lab record.

| Conditional step | When to run it |
|---|---|
| Luna and Router comparisons in 02 | Only if you choose to compare them. |
| GitHub CI/CD in 14 | When you have the required repository permissions. |
| A feature unavailable in your subscription | Record blocked/not run; continue only where prerequisites are met. |

Not every subscription can run every feature. See [what can proceed after a blocker](docs/en/checkpoints.md#if-a-stage-is-blocked).

### How to read one step

**Check prerequisites → choose a step in the chapter map → run one command → inspect the result**

| Label | How to use it |
|---|---|
| **Where you work** | Check whether the action belongs in the portal, terminal, or editor. |
| **Chapter map** | Select a step to jump to its section. The right column identifies the result to inspect. |
| **Command block** | Copy and run one block's command, inspect its result, then move to the next block. |
| **Check** / **Completion check** | Compare against real output and files. Finishing a command is not the same as passing quality checks. |
| **Optional** / collapsed notes | Expand only when the condition applies; do not run every alternative in addition to the default. |

Lost your place in a long chapter? Use **Chapter map ↑** at the bottom.

Copy **the entire command block**, even if it extends beyond the visible box. Do not insert line breaks yourself. See [commands and placeholders](docs/en/checkpoints.md#read-commands-and-placeholders).

## What will you build?

A travel-policy assistant for the fictional company **Hanbit Technology**.

> “A hotel for my domestic business trip in September 2026 costs KRW 170,000 per night. May I book it?”

The intended answer explains the **KRW 150,000 limit, team-lead approval required before booking, and supporting documents**. Without evidence, the assistant must not guess or claim to approve, book, or pay.

Foundry connects **models, agents, knowledge, tools, evaluation, and operations** in one Azure platform. You will explore that lifecycle through the same synthetic business case.

Keep the model **roles separate**. Prepare only the answer model at first.

| Role | Base model → fresh deployment alias |
|---|---|
| Primary answers · from 00 | **GPT-6 Sol** → `workshop-chat` |
| Optional comparison · only if chosen in 02 | GPT-6 Luna → `workshop-compare` |
| Answer grading · 07 | GPT-5.5 → `workshop-judge` |

The judge uses a **different base model and a separate deployment** from the target.

Existing aliases may differ. Never replace or delete the model behind an existing name to match these examples. See [Model roles and existing aliases](docs/en/model-selection.md).

![Workshop architecture: models, knowledge, tools, evaluation, and operations](docs/assets/architecture.svg)

The shared diagram shows local CLI/MAF code calling Foundry models and agents, retrieving six synthetic policies through File Search/Search/IQ, and using evaluation, traces, and human review to improve instructions.

## Curriculum

### Setup and first responses · 00–02

| Step | What you do | Evidence you keep |
|---|---|---|
| [00 Setup](docs/en/00-setup.md) | Prepare tools, a project, a model, and permissions | Your environment |
| [01 First response](docs/en/01-foundry.md) | Call a model in the portal and from code | An actual response |
| [02 Models and prompts](docs/en/02-models-prompts.md) | Compare instructions; optionally compare Luna and Router | A reasoned selection |

### Knowledge, tools, and evaluation · 03–07

| Step | What you do | Evidence you keep |
|---|---|---|
| [03 Agents and files](docs/en/03-knowledge.md) | Create a Prompt Agent and use File Search | Exact versions and citations |
| [04 Tools](docs/en/04-tools.md) | Run functions, MCP, and Code Interpreter | Actual tool results |
| [05 Workflows](docs/en/05-workflows.md) | Run sequential, parallel, chat, and pause/resume flows | Execution records |
| [06 Retrieval](docs/en/06-search-iq.md) | Configure Search, IQ, and Hybrid | Retrieved source documents |
| [07 Evaluation](docs/en/07-evaluation.md) | Compare the same questions before and after changes | Quality evidence |

### Deployment, operations, and extensions · 08–11

| Step | What you do | Evidence you keep |
|---|---|---|
| [08 Deployment](docs/en/08-hosted.md) | Test locally, then deploy a Hosted Agent | A remote version and response |
| [09 Operations](docs/en/09-operations.md) | Inspect traces, Insights, and costs | Request-level observations |
| [10 Shared tools](docs/en/10-toolbox-skills.md) | Connect Toolbox, Skills, and OpenAPI | Reusable, versioned tools |
| [11 State and scheduling](docs/en/11-memory-a2a-routines.md) | Use Memory, A2A, and Routines | State and dispatch records |

### Improvement, verification, and cleanup · 12–15

| Step | What you do | Evidence you keep |
|---|---|---|
| [12 Improvement](docs/en/12-improvement.md) | Evaluate conversations, optimization, and deployed versions | Reviewed candidates |
| [13 Lab safety](docs/en/13-governance.md) | Verify managed AI red teaming, lab guardrails, identities, and inventory | Native run evidence and limitations |
| [14 GitHub OIDC CI/CD](docs/en/14-additional-permissions.md) | Run the included identity-based lab release workflow | Exact version and dev business checks |
| [15 Acceptance and cleanup](docs/en/15-capstone-cleanup.md) | Verify the final target and stop, retain, or remove resources | Results and lifecycle records |

Follow each chapter's **run → verify → next** sequence. [The progress guide](docs/en/checkpoints.md) explains unfamiliar terms, command placeholders, and handling existing results.

## Run in English

> [!IMPORTANT]
> These are **resume commands, after completing `configure` in chapter 00**. For a first run, start with [00. Setup](docs/en/00-setup.md).

Run all commands from **the folder containing this README**.

**1. Check local readiness**

```bash
python scripts/workshop.py --language en doctor
```

**2. Read saved connection settings**

```bash
python scripts/selfstudy.py values
```

`--language en` selects the bundled English prompts, policies, and cases. Its position depends on the script:

| Script | English option |
|---|---|
| `workshop.py` | Put `--language en` before the subcommand, after wrapper options such as `--model-deployment` and `--script`. |
| `selfstudy.py` | No global language option. Its `prepare-hosted` and `capture` subcommands require their own `--language en`. |

See [Data and localization](docs/en/data-format.md). Neither resume command above invokes a model.

| Location | Purpose |
|---|---|
| `.venv/` | This project's Python environment |
| `.env` | Private Azure configuration; do not share |
| `outputs/` | Actual results and ownership records |

Retain `.selfstudy/` too: it holds personal configuration and deployment preparation. English examples use separate labels and `outputs/learner-notes-en/`.

## Ground rules

- Use only the six synthetic policies in `data/knowledge/en/policies.json`; no real company data, secrets, tokens, bookings, payments, or approvals.
- Create services only when needed. Owner does not guarantee quota, regional availability, or preview access; keep organizational protections in place.
- Never replace errors or empty responses with fixtures, or treat one good answer as evidence that the whole lab passed.
- **Even when stopping early, follow [chapter 15](docs/en/15-capstone-cleanup.md).** In retention mode, keep resources and ownership records, disable routines, and stop compute without deleting agents or volumes.

## Validation status and limits

> [!IMPORTANT]
> **Final acceptance is held in the September 28, 2026 validation; no new holdout was run.** Execution and final quality acceptance are separate.

| Validation target | Actual result | Interpretation |
|---|---|---|
| SDK and Hosted dev | 6/6 each | Dev results, not final acceptance. |
| Managed Task Adherence | Six rows: five pass, one fail | Severity and verdict flags disagree. |
| Optimizer | No new full candidate | No improvement or promotion is claimed. |

The [live validation report](docs/en/validation-report.md) is reference evidence, not your completion record. It and the relevant chapters retain regional-document discrepancies and historical run details.

Chapter 13's managed AI red teaming cannot be replaced by the custom eight-case diagnostic.

<a id="portal-and-cli-summary-videos"></a>

## North Central US portal and CLI summary videos

**4:32 each · 31 scenes · silent with captions**

This renamed-repository rerun edition covers new-group creation through evaluation, deployment, and stopping compute. It retains the native inconsistency and acceptance hold.

Five authenticated portal scenes accompany this run's actual CLI recordings and labelled saved-evidence reviews. Login screens and credentials are excluded.

| English | 한국어 |
|---|---|
| [![English summary](docs/assets/videos/foundry-v1.5-summary-en-poster.png)](docs/assets/videos/foundry-v1.5-summary-en.mp4) | [![한국어 요약](docs/assets/videos/foundry-v1.5-summary-ko-poster.png)](docs/assets/videos/foundry-v1.5-summary-ko.mp4) |
| [Watch MP4](docs/assets/videos/foundry-v1.5-summary-en.mp4) · [Captions](docs/assets/videos/foundry-v1.5-summary-en.srt) | [MP4 보기](docs/assets/videos/foundry-v1.5-summary-ko.mp4) · [자막](docs/assets/videos/foundry-v1.5-summary-ko.srt) |

[Recording scope and provenance](docs/en/videos.md) · [Live validation findings](docs/en/validation-report.md)

Bilingual captions do not imply two complete language-specific reruns.

<details>
<summary>Where earlier video editions are preserved</summary>

The current files show the **new group's portal/CLI rerun**. Earlier editions remain in these revisions:

| Earlier edition | Revision |
|---|---|
| NC portal | `7b7ca26` |
| NC CLI | `1d53a68` |
| Sweden | `0a8ab50` |

</details>

**Help:** [Troubleshooting](docs/en/troubleshooting.md) · [Feature map](docs/en/feature-map.md) · [Checkpoints](docs/en/checkpoints.md) · [Code reading](docs/en/code-reading.md) · [Official sources](docs/en/sources.md) · [Next steps](docs/en/next-steps.md)
