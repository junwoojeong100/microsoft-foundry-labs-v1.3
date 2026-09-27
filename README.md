# Microsoft Foundry Hands-on Guide · v1.5

**English** | [한국어](README.ko.md)

**Build an AI assistant in your own Azure environment, connect evidence and tools, evaluate it, and deploy it. All workshop code and synthetic data are included.**

You need a **Microsoft Entra ID account, an Azure subscription, and an active subscription Owner role**. Work at your own pace; there is no course time limit. A workshop ZIP does not require a GitHub account or Git.

**Start here → [00. Set up your environment](docs/en/00-setup.md)**

Already started? → [Your workbook](worksheets/en/workbook.md)

## What will you build?

A travel-policy assistant for the fictional company **Hanbit Technology**.

> “A hotel for my domestic business trip in September 2026 costs KRW 170,000 per night. May I book it?”

The intended answer explains the **KRW 150,000 limit, team-lead approval required before booking, and supporting documents**. Without evidence, the assistant must not guess or claim to approve, book, or pay.

Foundry connects **models, agents, knowledge, tools, evaluation, and operations** in one Azure platform. You will explore that lifecycle through the same synthetic business case.

**GPT-6 Luna** is the starting model candidate; **GPT-6 Sol** is used for comparison and judging. Deployment roles and observed API limitations are in [Model selection](docs/en/model-selection.md). If Luna's project API fails, use the [explicit Sol compatibility path](docs/en/01-foundry.md#distinguish-project-and-account-apis)—not an automatic fallback or a claim of validated Luna agent support.

![Workshop architecture: models, knowledge, tools, evaluation, and operations](docs/assets/architecture.svg)

The shared diagram shows local CLI/MAF code calling Foundry models and agents, retrieving six synthetic policies through File Search/Search/IQ, and using evaluation, traces, and human review to improve instructions.

## Curriculum

| Step | What you do | Evidence you keep |
|---|---|---|
| [00 Setup](docs/en/00-setup.md) | Prepare tools, a project, a model, and permissions | Your environment |
| [01 First response](docs/en/01-foundry.md) | Call a model in the portal and from code | An actual response |
| [02 Models and prompts](docs/en/02-models-prompts.md) | Compare instructions, models, and Router | A reasoned selection |
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
| [13 Governance](docs/en/13-governance.md) | Inspect policies, identities, and networking | Controls and limitations |
| [14 Additional integrations](docs/en/14-additional-permissions.md) | Check extra permissions and product prerequisites | Execution or design-only status |
| [15 Acceptance and cleanup](docs/en/15-capstone-cleanup.md) | Verify the final target and stop, retain, or remove resources | Results and lifecycle records |

Follow each chapter's **run → verify → next** sequence. No second repository or separate learning path is required.

## Run in English

Run all commands from **the folder containing this README**, after the setup in chapter 00.

```bash
python scripts/workshop.py --language en doctor
python scripts/selfstudy.py values
```

`--language en` selects the bundled English prompts, policies, and cases. It goes **before the workshop subcommand**; wrapper options such as `--model-deployment` and `--script` go before it. `selfstudy.py` has no global language flag, but its `prepare-hosted` and `capture` subcommands require their own `--language en` for English work. See [Data and localization](docs/en/data-format.md).

Keep `.venv/` for Python, `.env` for private Azure configuration, and `outputs/` for real results and ownership records. English examples use separate labels and `outputs/learner-notes-en/`.

## Ground rules

- Use only the six synthetic policies in `data/knowledge/en/policies.json`; no real company data, secrets, tokens, bookings, payments, or approvals.
- Create services only when needed. Owner does not guarantee quota, regional availability, preview access, or other products' licenses.
- Never replace errors or empty responses with fixtures, and never treat one good answer as production approval.
- **Even when stopping early, follow [chapter 15](docs/en/15-capstone-cleanup.md).** In retention mode, keep resources and ownership records, disable routines, and stop compute without deleting agents or volumes.

## Portal and CLI summary videos

**3:38 each, silent with captions.** These are edited recordings of real portal interactions and live CLI output—not simulated model answers.

| English | 한국어 |
|---|---|
| [![English summary](docs/assets/videos/foundry-v1.5-summary-en-poster.png)](docs/assets/videos/foundry-v1.5-summary-en.mp4) | [![한국어 요약](docs/assets/videos/foundry-v1.5-summary-ko-poster.png)](docs/assets/videos/foundry-v1.5-summary-ko.mp4) |
| [Watch MP4](docs/assets/videos/foundry-v1.5-summary-en.mp4) · [Captions](docs/assets/videos/foundry-v1.5-summary-en.srt) | [MP4 보기](docs/assets/videos/foundry-v1.5-summary-ko.mp4) · [자막](docs/assets/videos/foundry-v1.5-summary-ko.srt) |

[Recording scope and provenance](docs/en/videos.md) · [Live validation findings](docs/en/validation-report.md). Search capacity blockers and native-quality warnings remain explicit; the videos do not imply production approval.

**Help:** [Troubleshooting](docs/en/troubleshooting.md) · [Feature map](docs/en/feature-map.md) · [Checkpoints](docs/en/checkpoints.md) · [Code reading](docs/en/code-reading.md) · [Official sources](docs/en/sources.md) · [Next steps](docs/en/next-steps.md)
