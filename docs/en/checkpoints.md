# Keep making progress without hiding blockers

**English** | [한국어](../checkpoints.md) · [Course home](../../README.md)

Take one step at a time: **run → inspect → record → next**.

## Four questions for every chapter

- What am I creating or changing?
- Am I using the intended project, model, and version?
- What result did I actually verify?
- If I stop here, what must be stopped, retained, or removed?

A completed command, an actual response, and a quality pass are different. Record failures/unsupported features honestly, then use the corresponding [troubleshooting entry](troubleshooting.md).

## Before moving on

| Stage | Gate |
|---|---|
| 00–02 | Verify `workshop-chat` is GPT-6 Luna / 2026-09-22, then obtain actual responses. If its project API fails, explicitly select/probe Sol as in 01 and record actual model/API; never claim Luna agent validation. |
| 03 | Six indexed files, real File Search calls, and citations to your files |
| 04–05 | Actual function/MCP executions and results; simulated approval is not real authorization |
| 06 | Your Search, embeddings, and IQ roles verified; the answer model and Search planning model are separate |
| 07 | Judge deployment is separate from every target; all dev rows, errors, business checks, and actual Sol judge results reviewed without claiming all metrics passed |
| 08–11 | Exact deployed versions, runtime identities, traces, tools, and state results verified |
| 12 | Explicitly select IQ or the separately named local matrix; `bind-matrix` reads its actual version/endpoint, and comparisons keep retrieval, generation settings, and data fixed |
| 15 | Unlock holdout only after the frozen candidate's gates; stop schedules/sessions and explicitly retain or remove stores/models |

Opening a portal or completing a CLI command does not imply the next chapter's prerequisites exist.

## Preserve configuration and evidence

Keep settings and results together. If you forget a value:

```bash
python scripts/selfstudy.py values
```

Read existing results before recreating resources or files. Do not use another person's tokens, responses, or accounts. Keep one corpus language per experiment and separate `-en` labels for English results.

## Share workshop materials safely

To package teaching materials without personal settings:

```bash
python scripts/package_workshop.py
```

The bundle is intended to contain code, data, guides, and tests, excluding `.env`, `.selfstudy`, runtime results, and virtual environments. Inspect the generated manifest before distribution, including both `README.md` and `README.ko.md`, the English/Korean guides, and worksheets. A recipient extracts it and starts at [00](00-setup.md).
