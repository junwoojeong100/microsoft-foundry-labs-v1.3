# Keep making progress without hiding blockers

**English** | [한국어](../checkpoints.md) · [Course home](../../README.md)

Take one step at a time: **run → inspect → record → next**.

The current region is North Central US. **The fresh repository-rerun Task Adherence job returned six rows/five pass/one fail; inconsistent severity/flags hold final acceptance.** Earlier NC mixed-job and separate 5/5 results are historical. Verify each job/label in the [current report](validation-report.md); old passes or custom diagnostics do not override new limitations.

## Four questions for every chapter

- What am I creating or changing?
- Am I using the intended project, model, and version?
- What result did I actually verify?
- If I stop here, what must be stopped, retained, or removed?

A completed command, an actual response, and a quality pass are different. Record failures/unsupported features honestly, then use the corresponding [troubleshooting entry](troubleshooting.md).

## Before moving on

| Stage | Gate |
|---|---|
| 00–02 | Verify the actual Sol alias is GPT-6 Sol / 2026-09-22 and obtain a response. Fresh labs use `workshop-chat`; Luna comparison is optional. |
| 03 | Six indexed files, real File Search calls, and citations to your files |
| 04–05 | Actual function/MCP executions and results; simulated approval is not real authorization |
| 06 | Your Search, embeddings, and IQ roles verified; the answer model and Search planning model are separate |
| 07 | GPT-5.5 judge uses a different base model and deployment from the targets; review all dev rows, errors, business checks, and actual evaluation explanations |
| 08–11 | Exact deployed versions, runtime identities, traces, tools, and state results verified |
| 12 | Explicitly select IQ or the separately named local matrix; `bind-matrix` reads its actual version/endpoint, and comparisons keep retrieval, generation settings, and data fixed |
| 13 | NC is common to both official sources, whose wider lists conflict. Verify the actual managed job and metric direction; custom diagnostics or region changes are not substitutes. |
| 15 | Unlock holdout only after the frozen candidate's gates; stop schedules/sessions and explicitly retain or remove stores/models |

Opening a portal or completing a CLI command does not imply the next chapter's prerequisites exist.

## Preserve configuration and evidence

Keep settings and results together. If you forget a value:

```bash
python scripts/selfstudy.py values
```

Read existing results before recreating resources or files. Do not use another person's tokens, responses, or accounts. Keep one corpus language per experiment and separate `-en` labels for English results.

For another project, follow [00's archive/fresh-workspace procedure](00-setup.md#start-a-new-project-without-adopting-old-state). A retained CI identity or old deployment alias does not establish new-project permissions or ownership.

## Share workshop materials safely

To package teaching materials without personal settings:

```bash
python scripts/package_workshop.py
```

The bundle is intended to contain code, data, guides, and tests, excluding `.env`, `.selfstudy`, runtime results, and virtual environments. Inspect the generated manifest before distribution, including both `README.md` and `README.ko.md`, the English/Korean guides, and worksheets. A recipient extracts it and starts at [00](00-setup.md).
