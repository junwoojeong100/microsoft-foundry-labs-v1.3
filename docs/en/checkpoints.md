# Keep making progress without hiding blockers

**English** | [한국어](../checkpoints.md) · [Course home](../../README.md)

Take one step at a time: **run → inspect → next**. No separate write-up or submission is required. Keep the configuration and result files produced by the commands.

**On a first run, follow the default route in one language.** Historical validation reports and collapsed recovery commands are not additional assignments. If you skipped a chapter, check the next chapter's **prerequisites** before proceeding.

## Find the help you need

| Your question | Go to |
|---|---|
| Where do I perform each action? | Follow **Where you work → Chapter map → Completion check** in each chapter. Select a step in the map to jump to it. |
| Which values do I replace? | [Commands and placeholders](#read-commands-and-placeholders) |
| What should I read in the output? | [Reading results](#read-results-and-carry-values-into-the-next-command) · [Saved locations](#find-saved-configuration-and-results) |
| What does this term mean? | [Glossary](#terms-you-will-encounter) |
| How do I continue yesterday's work? | [Resume instructions](#resume-on-another-day) · [Two terminals](#chapters-with-two-terminals) |
| There is an error or an existing file | [Interpreting errors](#can-i-continue-after-an-error) · [Rerunning names](#can-i-rerun-the-same-name) |
| Can I move to the next chapter? | [Completion gates](#before-moving-on) · [Blocked steps](#if-a-stage-is-blocked) |
| I am stopping for today | **[Stop work and review costs](15-capstone-cleanup.md#4-stop-running-work-first)** |
| How do I share the materials? | [Package without personal settings](#share-workshop-materials-safely) |

**Check off only what you actually verified.** Preserving a blocked/not-run status is not the same as feature success. You do not need to edit the guide's checkboxes or submit a separate file.

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

The lab chapters use **one command per executable block**. Read **the explanation above → run that command → check the result below**. For ordinary commands, wait for the prompt to return and inspect the result before the next block. Long-running servers such as `serve` are the exception; their chapters explain terminals A and B.

For long commands, scroll horizontally or use the block's copy button to copy **the entire line**. Visual wrapping is fine; do not insert Enter, a backslash, or a PowerShell backtick yourself. Quoted questions, paths, and options must remain part of the same command.

JSON, YAML, questions, and example output can span multiple lines. Do not execute those blocks in the terminal; use the editor, Playground, or result-viewing location specified immediately above them.

`--confirm-create`, `--confirm-cost`, and `--confirm-delete` explicitly acknowledge creation, charges, and deletion. **Model requests without these options can still incur charges.** Check the target and cost before running them.

## Read results and carry values into the next command

Open the printed path in your editor's file explorer. A created folder or a printed path alone does not establish success.

| Output/file | How to read it |
|---|---|
| `.json` | Uses `"name": value`. Copy **the value, not the field name**, into the next command. |
| `.jsonl` | One case per line. For six cases, check all six rows and their errors; do not convert the file into a JSON array. |
| `.html` | Open the file in a browser to read tables and per-case results, rather than only viewing source in the editor. |
| `true` / `false` / `null` | True / false / no value. `null` usage does not mean zero cost or no request. |
| `manifest.json` | Records the run's model, instructions, data, and settings. Read the actual answer in its response file. |
| `result_directory` or a saved path | Open that folder/file. Responses, evaluations, and ownership records are different artifacts. |

**Names have different roles too.** In `prepare-hosted --name hosted-en`, `hosted-en` is a **suffix after your prefix**. Use the full service name printed by the helper in subsequent `azd deploy` commands. In contrast, `prompt-agent create --name` takes the **full agent name including your prefix**. Do not substitute the same string into every `--name`.

From 08 onward, use [08's value-copying table](08-hosted.md#3-prepare-an-isolated-folder-for-the-existing-project) to copy the package path, preparation folder, service, and version **directly from command output into the next command**. `--cwd` selects the target folder for one azd command; it does not change your terminal's working directory. Keep the terminal in the README folder.

## Find saved configuration and results

| Value/result needed | Existing location or lookup |
|---|---|
| Your project, prefix, and model | `python scripts/selfstudy.py values` or `status`, reading `.env` and `.selfstudy/azure.json` |
| Responses from 01, 04, 05, and similar exercises | Chapter-numbered JSON files in `outputs/learner-notes-en/` |
| 03's agent names, versions, and file IDs | Creation/ownership records under `outputs/agents/` and `outputs/file-search/` |
| 06's original Search index | `configuration.index` in `outputs/learner-notes-en/06-search.json` |
| 07's before/after evaluations | `outputs/baseline-en/` and `outputs/candidate-en/`, or the actual labels you chose |
| 08/10/12's deployment folder and service | `name` and `services` in the relevant `.selfstudy/` `azure.yaml`; query the actual version using `azd ai agent show` with that folder |
| 12's Hosted evaluations and calibration | `outputs/benchmarks/` and `outputs/judge-calibration/` |
| Portal-only work | The relevant Foundry agent, Traces, or evaluation page; GitHub Actions logs and downloaded artifacts |

File existence is not completion. Compare the chapter's **completion check** with actual row counts, errors, and verdicts. Do not assume every portal-only action is saved locally.

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

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

If organizational policy blocks activation, use `.\.venv\Scripts\python.exe` instead of `python`; do not weaken policy.

**Then, on every operating system**

3. After chapter 00's `configure` has been completed, run:

```bash
python scripts/workshop.py --language en doctor
```

After checking local readiness, read the saved settings.

```bash
python scripts/selfstudy.py values
```

Check `PASS` and **your project, prefix, and model**. `values` and `status` read saved settings, not the current existence or health of Azure resources. If prompted to run Lab 00's configure, return to [configuration](00-setup.md#8-collect-configuration-from-actual-values). For expired sign-in, use 00's normal `az login`/`azd auth login` process. `values` uses Korean field labels even in the English edition; it has no global language flag.

4. Locate the chapter's saved result using the table above, compare it with the **completion check**, and continue at the next unperformed step. To inspect an existing answer, open its file rather than calling the model again.

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

### Can I continue after an error?

| Actual state | Next action |
|---|---|
| `ERROR`, traceback, authentication/API errors, or missing responses | Stop dependent commands and consult that chapter and troubleshooting. A saved file is not a success. |
| All six responses in 07, zero request errors, but failed business checks | Analyze the failures and continue the instruction comparison. Do not repeatedly recollect to erase low scores. |
| A managed job is still running when the local wait times out | Follow that chapter's same-ID/label read/resume procedure; do not submit another job. |
| Failed quality criteria or inconsistent managed verdicts | Preserve the analysis and hold final acceptance/holdout. Still perform [15's stopping and cleanup](15-capstone-cleanup.md#4-stop-running-work-first). |

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

| Blocked feature | What can proceed |
|---|---|
| 00–01's primary Sol deployment/first call | Stop Azure exercises without substituting a model; inventory any created resources in 15. |
| Only File Search in 03 or Code Interpreter in 04 | Record that tool as not run. With a working primary model, local MAF/functions/MCP in 04 and workflows in 05 can proceed. |
| Only Hybrid or IQ Chat in 06 | Keep keyword/IQ evidence separate. 07 uses local retrieval; 10 needs the original keyword index, not successful Hybrid/IQ Chat. |
| Only remote Hosted deployment in 08 | If local preparation succeeds, retain sections 1–3's folder for connections. Continue with 09's Prompt Agent trace, 10's non-Hosted tools, and independently prepared features in 11. |
| Only Memory or embeddings in 11 | Mark Memory not run. A2A can proceed with 08's preparation folder; Routines separately need 03's Prompt Agent and 09's logs. |
| Optimizer unavailable or no candidates in 12 | Record the outcome; continue with bundled Hosted `v1`/`v2` comparison if its prerequisites exist. Do not change sources or criteria to force a candidate. |
| Hosted guardrail exercise unavailable in 13 | Mark sections 2–4 not run. Section 5's managed verification can be checked separately with its Prompt Agent, judge, and logging prerequisites. |
| No GitHub permissions in 14 | Continue to 15. Skipping 14 does not waive other quality gates. |

For another project, follow [00's archive/fresh-workspace procedure](00-setup.md#start-a-new-project-without-adopting-old-state). A retained CI identity or old deployment alias does not establish new-project permissions or ownership.

**Keep failure output; do not treat unsupported or unperformed work as complete.** The [validation report](validation-report.md) is reference evidence, not your run. When stopping, jump to [15's stopping steps](15-capstone-cleanup.md#4-stop-running-work-first). Search Basic can incur charges without requests, and retained storage can cost money after compute stops.

## Share workshop materials safely

To package teaching materials without personal settings:

```bash
python scripts/package_workshop.py
```

The bundle is intended to contain code, data, guides, and tests, excluding `.env`, `.selfstudy`, runtime results, and virtual environments. Inspect the generated manifest before distribution, including both `README.md` and `README.ko.md` and the English/Korean guides. A recipient extracts it and starts at [00](00-setup.md).

Do not overwrite an existing ZIP. For a new distribution, use an unused filename such as `--output dist/workshop-new.zip` and inspect its manifest.

---

[Course home](../../README.md#curriculum) · [Help index](#find-the-help-you-need) · [Troubleshooting](troubleshooting.md)
