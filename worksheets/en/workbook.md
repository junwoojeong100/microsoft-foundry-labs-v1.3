# My Foundry self-study workbook — v1.5

**English** | [한국어](../workbook.md) · [Course home](../../README.md)

Save a private copy, for example under `.selfstudy/`. Record only actual identifiers and observations. Do not include tokens, passwords, API keys, or real company documents.

## Starting point

| Item | My value / verification |
|---|---|
| Entra tenant / subscription | |
| Active subscription Owner confirmed | |
| Unique WORKSHOP_PREFIX | |
| Source of project endpoint / ARM ID | |
| Dedicated resource group and actual region | |
| Source commit / actual local modifications | |
| Python, SDK, azd/extension versions | |
| Starting model/version: GPT-6 Luna / 2026-09-22 | |
| Actual configured default: Luna or explicitly selected Sol | |
| Comparison/judge model/version: GPT-6 Sol / 2026-09-22 | |
| Actual judge deployment, separate from every target (`workshop-judge` when Sol is a target) | |
| Project versus account API observations / compatibility decision | |
| Language: en / separate labels and corpus | |
| Reasoning effort / output-token cap | |
| Budget and stopping/retention/deletion plan | |

## Progress

Distinguish `planned / executed / verified / blocked / additional permission needed / design only / stopped / retained / deleted`.

| Chapter | Actual status | Result file / ID | Next action |
|---|---|---|---|
| 00 Prepare my environment | | | |
| 01 First model response | | | |
| 02 Models, prompts, Router | | | |
| 03 Prompt Agent / File Search | | | |
| 04 MAF / functions / MCP / Code Interpreter | | | |
| 05 Workflows / simulated approval and recovery | | | |
| 06 Search / IQ / Hybrid / IQ Chat | | | |
| 07 Business / native evaluation | | | |
| 08 Hosted locally / remotely | | | |
| 09 Logs / traces / Insights / recurring evaluation | | | |
| 10 Toolbox / Skills / OpenAPI / Hosted | | | |
| 11 Memory / A2A / Routines | | | |
| 12 Conversations / Optimizer / matrix / calibration | | | |
| 13 Safety / roles / networking | | | |
| 14 Additional-permission features | | | |
| 15 Final acceptance / resource lifecycle | | | |

## Result card — copy for each exercise

```text
Chapter/feature:
Actual project, agent, and exact version:
Model/deployment/version:
Instructions, data, language, retrieval, API:
Reasoning and output cap:
Actual question I sent:
Actual response/result file:
Comparison with source documents and tool results:
Response/run/trace IDs:
Original failures, unmeasured values, unsupported features:
Assets and roles I created/changed:
Stopped/retained/deleted state:
```

## Identity and role map

| Actual identity | Source of object/principal ID | Target / role / scope | Actual operation result |
|---|---|---|---|
| My CLI user | | | |
| Project managed identity | | | |
| Foundry account managed identity | | | |
| Search managed identity | | | |
| Hosted runtime identity | | | |
| Additional CI identity, if used | | | |

## Evaluation comparison

| Item | Baseline | Candidate |
|---|---|---|
| Target implementation / agent version | | |
| Actual label / folder | | |
| Model, code, instructions, and dataset hashes | | |
| Language, corpus, retrieval, API, concurrency | | |
| Hosted matrix profile: IQ or explicitly selected local retrieval | | |
| Reasoning effort / output cap | | |
| Expected rows / actual rows / errors | | |
| Business criteria | | |
| Native evaluators / judge / raw scores | | |
| Trace / calibration | | |
| Remaining issues and selection rationale | | |

**Inline, SDK, MAF, and Hosted are different targets.** Use each target's own actual results. The judge deployment must differ from every target deployment. When Sol both answers and judges through separate deployments, record the remaining model-family self-evaluation bias.

**Local-retrieval Hosted is not IQ validation.** Use distinct local labels and exact versions, retain Search-dependent blockers, and choose only one final target before unlocking holdout.

## Additional-feature records

| Item | Actual value / observation |
|---|---|
| Skill source/readback hashes and actual load | |
| Memory IDs/scopes, update/deletion, one-hour TTL | |
| A2A target/caller/card and real delegation | |
| Routine name, dispatch, answer verification, disabled state | |
| Optimizer target, candidate count, raw judge inputs, decision | |
| Actual safety policy ID, attachment, interventions/non-interventions | |
| Features needing additional permissions and whether obtained | |

## Final acceptance

| Item | My result |
|---|---|
| Chosen final target and exact version | |
| Pre-holdout gate | |
| Whether these cases were genuinely unseen | |
| Expected/actual rows, errors, business/native quality | |
| Trace/calibration and unverified areas | |
| Whether the small acceptance gate passed, and why | |
| Additional work required before production | |

Use holdout for only the chosen final target, after the dev gates. Do not reuse previously seen cases as a new unseen test.

## Apply this to my own work

- Recurring problem and current business metric:
- Approved source documents and update owner:
- Read-only tools:
- Actions prohibited without real human authorization:
- Questions that must pass:
- User authorization, networking, and log minimization:
- Cost, incident, rollback, and deletion owner:

## Resource lifecycle card

| Asset / actual group | Ownership verified | Deleted / retained / stopped | Remaining cost / next check |
|---|---|---|---|
| Foundry, models, Prompt/Hosted agents | | | |
| File Search uploads/vector stores and retention mode | | | |
| Search indexes/sources/bases/service | | | |
| Toolbox/Skills/OpenAPI connections | | | |
| Memory/A2A/Routines | | | |
| Evaluation/Optimizer/recurring schedules | | | |
| Hosted sessions/volumes | | | |
| Application Insights/Log Analytics | | | |
| Additional roles/managed identities/federation | | | |
| Other groups/earlier attempts | | | |

**Retention reminder:** No cleanup, forget, `--confirm-delete`, `azd down`, or group deletion. Keep File Search with `--retain`, disable routines, and stop compute without deleting resources or volumes. Memory store retention does not extend its one-hour item TTL.

**Learning completion status:**

**Final quality judgment:**

**Production approval:** Separate decision

**Remaining charges and next review date:**
