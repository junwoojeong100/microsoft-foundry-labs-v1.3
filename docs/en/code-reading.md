# Read only the code you need

**English** | [한국어](../code-reading.md) · [Course home](../../README.md)

**Trace what you just ran without memorizing an entire framework.** The English entrypoint is `python scripts/workshop.py --language en`, run from the v1.5 root.

| Question | Files to open |
|---|---|
| CLI arguments and dispatch | `scripts/workshop.py`, `src/foundry_workshop/cli.py` |
| Sign-in, subscription, endpoint | `src/foundry_workshop/settings.py` |
| Models and managed Prompt Agents | `src/foundry_workshop/cloud.py` |
| Functions, MCP, MAF workflows | `src/foundry_workshop/agents.py`, `runtime.py`, `examples/mcp_server.py` |
| Search, IQ, Hybrid | `src/foundry_workshop/search.py`, `iq_chat.py` |
| Evaluation, fixed conditions, calibration | `evaluation.py`, `cloud_evaluation.py`, `benchmark.py`, `calibration.py` |
| Toolbox and Hosted | `toolbox.py`, `toolbox_host.py`, `hosted.py`, `packaging.py` |
| Memory, A2A, Routines | `memory_lab.py`, `a2a_lab.py`, `routines_lab.py` |
| Managed red-team preparation, resume, and raw-flag audit | `scripts/managed_redteam.py` |
| Native Routine history when the CLI list is empty | `scripts/routine_runs.py` |
| Language-specific policies and prompts | `contracts.py`, `materials.py`, `extension_materials.py`, `profiles.py` |
| Minimal standalone SDK examples | `examples/recipes/` |

Short filenames in the table are also under `src/foundry_workshop/`.

Find the chain: inputs → permitted tools/evidence → SDK request → original result → validation/storage. Distinguish agent definitions from model deployments, and local code from remote runtimes.

`scripts/workshop.py` processes wrapper options first. `--model-deployment` and `--script` must appear **before** `--language en`; the runtime's language flag must appear before its subcommand. Helpers parse their own flags. See [localization conventions](data-format.md).

Changing source can invalidate a comparison's fixed-code condition. Preserve earlier results and collect a new dev pair with the same modified code.

A local check without Azure:

```bash
python scripts/workshop.py --language en doctor
```

For small examples, open [examples/recipes](../../examples/recipes/). Inspect each example's actual language/argument contract before running it; not every standalone script accepts the workshop CLI's flags. Change one input and run related tests. Local tests are not evidence of real model quality.

[Full course](../../README.md)
