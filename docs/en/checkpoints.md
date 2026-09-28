# Keep making progress without hiding blockers

**English** | [한국어](../checkpoints.md) · [Course home](../../README.md)

Take one step at a time: **run → inspect → record → next**.

## Read commands and placeholders

| What you see | What to do |
|---|---|
| `python ...`, `az ...`, `azd ...` | Run one line at a time in a terminal in the README folder. |
| `bash` / `powershell` | Code-block language labels, not commands. Python commands work in either shell with the virtual environment active. |
| `YOUR-...`, `ACTUAL-...`, `<...>` | Replace with **your actual value** from the preceding step. Keep surrounding quotes, but omit angle brackets. |
| `--label baseline-en` | A name for a saved result set. First runs can use example labels. If changed, update all later evaluate/compare references. |
| `--output outputs/...json` | A new file for the response. Open it in your editor after execution. |
| A JSON/YAML block or question text | Not a shell command. Save it to the specified file or paste it into Playground as instructed. |
| Optional, alternative, or collapsed recovery section | Do not execute it in addition to every default command. Use it only when its condition applies. |

`--confirm-create`, `--confirm-cost`, and `--confirm-delete` explicitly acknowledge creation, charges, and deletion. **Model requests without these options can still incur charges.** Check the target and cost before running them.

## Terms you will encounter

| Term | Meaning in this lab |
|---|---|
| Endpoint / ARM ID | Request address / full Azure resource identifier; they are not interchangeable |
| Prefix / label | Fixed prefix identifying your Azure assets / name of a local result set |
| Managed identity (MI) / RBAC | A service's Azure identity / how it receives permissions |
| Retrieval / evidence | Finding source documents / actual documents supporting an answer |
| Baseline / candidate | Results before a change / the changed candidate to compare |
| Dev / holdout | Six cases for iterative improvement / four final cases after freezing a candidate |
| Judge / calibration | A separate scoring model / checking its decisions on known good and bad answers |
| Smoke / gate | One request before a larger run / criteria for proceeding |

## Resume on another day

**For the same project, do not start by reinstalling or recreating resources.** Keep the original folder, `.env`, `.selfstudy/`, and `outputs/`.

1. Open the existing workshop folder in your editor and start a terminal.
2. Run **only your OS's** activation command.

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If organizational policy blocks activation, use `.\.venv\Scripts\python.exe` instead of `python`; do not weaken policy.

3. After chapter 00's `configure` has been completed, run:

```bash
python scripts/workshop.py --language en doctor
python scripts/selfstudy.py values
```

Check `PASS` and **your project, prefix, and model**. `values` and `status` read saved settings, not the current existence or health of Azure resources. If prompted to run Lab 00's configure, return to [configuration](00-setup.md#8-collect-configuration-from-actual-values). For expired sign-in, use 00's normal `az login`/`azd auth login` process. `values` uses Korean field labels even in the English edition; it has no global language flag.

4. Read the **last verified result and next command** in your private workbook and continue there. To inspect an existing answer, open its file rather than calling the model again.

### Chapters with two terminals

In 05, 08, and 10, leave **terminal A** running the server. Logs without a returned prompt are normal. Open **terminal B** with your editor's new-terminal button, check the same working folder, and activate `.venv` there too. Send checks/requests from B, then use `Ctrl+C` in A to stop your server.

## Can I rerun the same name?

| Situation | Next action |
|---|---|
| A response, label, package, or preparation folder already exists | Read it first. Only for a genuinely new run, choose a new label such as `candidate-en-2`, output file, or `--run`, and update later references. |
| File Search indexing or a managed red-team job is still running | Use that chapter's same-ID/label status and resume procedure; do not create duplicates. |
| You changed settings, source, code, or model | Preserve previous results and record the change. A prompt-only comparison requires a new pair with the same code/data. |
| Cost, permissions, or feature support blocks execution | Preserve the error and remaining assets. Do not begin by repeating creation, substituting a model, or broadening access. |

## Four questions for every chapter

- What am I creating or changing?
- Am I using the intended project, model, and version?
- What result did I actually verify?
- If I stop here, what must be stopped, retained, or removed?

A completed command, an actual response, and a quality pass are different. Record failures/unsupported features honestly, then use the corresponding [troubleshooting entry](troubleshooting.md).

## Before moving on

| Stage | Gate |
|---|---|
| 00 | Local doctor `PASS`, actual saved project/deployment, and data roles; this is not yet inference success |
| 01–02 | Actual Sol response/result JSON and prompt-versus-knowledge distinction; record optional Luna/Router as run or not run |
| 03 | Six indexed files, real File Search calls, and citations to your files |
| 04–05 | Actual function/MCP executions and results; simulated approval is not real authorization |
| 06 | Actual evidence for keyword, IQ, Hybrid, and IQ Chat separately; **restore the original index** |
| 07 | All six dev rows/errors/business checks, three policy criteria, and calibration judgments; failure analysis is not final acceptance |
| 08 | Package, local response, and exact remote version's response verified separately |
| 09 | A new post-connection response located in actual traces; recurring evaluation paused |
| 10 | Toolbox listing, retrieval, answer, and Skill load; record Skill and Toolbox versions separately |
| 11 | Memory alpha/beta, real A2A delegation, and original scheduled response; Routine disabled |
| 12 | Matched Hosted cohorts with actual evaluation/traces; sessions stopped and holdout unopened |
| 13 | All rows and consistent verdicts in the actual managed job; inconsistencies hold acceptance and cannot be replaced by custom diagnostics |
| 14 | With repository permissions: OIDC authentication, exact CI version, and dev results; otherwise record not run |
| 15 | Unlock holdout only after the frozen candidate's gates; stop schedules/sessions and explicitly retain or remove stores/models |

Opening a portal or completing a CLI command does not imply the next chapter's prerequisites exist.

## If a stage is blocked

Without Search, stop Search-dependent work in 06 and Toolbox/OpenAPI in 10. Work that does not require Search, such as 07's `local` retrieval evaluation, can continue. A deliberately chosen local matrix in 12 is not Search/IQ success. If Hosted is unavailable, record remote work in 08/12 as not run and distinguish 15's SDK target.

For another project, follow [00's archive/fresh-workspace procedure](00-setup.md#start-a-new-project-without-adopting-old-state). A retained CI identity or old deployment alias does not establish new-project permissions or ownership.

**Record failures and unsupported features; do not mark them complete.** The [validation report](validation-report.md) is reference evidence, not your run. When stopping, jump to [15's stopping steps](15-capstone-cleanup.md#4-stop-running-work-first). Search Basic can incur charges without requests, and retained storage can cost money after compute stops.

## Share workshop materials safely

To package teaching materials without personal settings:

```bash
python scripts/package_workshop.py
```

The bundle is intended to contain code, data, guides, and tests, excluding `.env`, `.selfstudy`, runtime results, and virtual environments. Inspect the generated manifest before distribution, including both `README.md` and `README.ko.md`, the English/Korean guides, and worksheets. A recipient extracts it and starts at [00](00-setup.md).

Do not overwrite an existing ZIP. For a new distribution, use an unused filename such as `--output dist/workshop-new.zip` and inspect its manifest.
