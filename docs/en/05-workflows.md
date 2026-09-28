# 05. Workflows, simulated approval, and local SDK pause/resume

**English** | [한국어](../05-workflows.md) · [Course home](../../README.md#curriculum) · [Help](checkpoints.md)

**Outcome:** Distinguish sequential, concurrent, and Group Chat results, and experience how pause/resume differs from real business authorization.

**Prerequisites:** Successful MAF execution in 04. Multiple roles can mean additional model calls.

**Where you work:** terminal in the workshop folder; section 5 uses two terminals, A and B.

**Chapter map**

| Step | Result to check |
|---|---|
| [1. Sequential](#1-sequential-execution) | Analysis → drafting → review |
| [2. Concurrent](#2-concurrent-execution) | Independent role outputs |
| [3. Group Chat](#3-group-chat) | A bounded role conversation |
| [4. Deployment-ready output](#4-validated-output-suitable-for-deployment) | Business answer and call lineage |
| [5. Pause/resume — macOS/Linux](#5-pause-and-resume-with-the-actual-sdk) | Stable request, gate, and output IDs |
| [Completion check](#completion-check) | Simulated versus actual approval; server stopped |

## 1. Sequential execution

```bash
python scripts/workshop.py --language en workflow --pattern sequential --output outputs/learner-notes-en/05-sequential.json
```

**Check:** the flow analyzes policy, drafts an answer, then reviews evidence. One final output does not imply one model request.

## 2. Concurrent execution

```bash
python scripts/workshop.py --language en workflow --pattern concurrent --output outputs/learner-notes-en/05-concurrent.json
```

**Check:** several roles see the same question and evidence simultaneously. Concatenating their outputs does not establish consensus or produce one automatically verified answer.

## 3. Group Chat

```bash
python scripts/workshop.py --language en workflow --pattern group-chat --output outputs/learner-notes-en/05-group-chat.json
```

**Check:** read the role conversation in its configured order. This implementation has a three-round maximum and an execution timeout. These are **code safeguards against runaway execution, not course time limits**. A round-limit message is not a business answer.

Across all three results, compare the actual question, number and meaning of outputs, missing evidence, usage, and latency. Adding participants does not necessarily improve quality.

## 4. Validated output suitable for deployment

```bash
python scripts/workshop.py --language en workflow-agent --pattern sequential --retrieval local --prompt v2 --output outputs/learner-notes-en/05-workflow-agent.json
```

This path uses real MAF orchestration, a validated business answer, and call lineage rather than merely joining strings. `pending-human-review` means a person still needs to review it, not that approval was granted.

## 5. Pause and resume with the actual SDK

**Check your OS:** this section requires macOS/Linux. Reinstalling packages will not fix Windows Python's missing `fcntl`. Use [00's approved WSL/Linux preparation](00-setup.md#2-get-the-files-and-development-tools), or record this section blocked/not run and continue to 06. The model workflows in sections 1–4 are separate.

This section uses **prewritten synthetic work without model or Azure calls** to teach local SDK simulated approval gates and checkpoints. It neither grants real business approval nor executes external business actions.

### Check the SDK

Check the pinned SDK:

```bash
python scripts/workshop.py --script resilience --language en check
```

Verify `azure-ai-agentserver-core: 2.1.0`, `azure-ai-agentserver-responses: 2.2.0b1`, and `azure_requests_sent: false`. The wrapper removes external telemetry/Foundry settings only from this helper process; it does not modify your shell or `.env`.

### Terminal A: start the server

Start the server in terminal A in the v1.5 root and leave it running. See [using two terminals](checkpoints.md#chapters-with-two-terminals).

```bash
python scripts/workshop.py --script resilience --language en --run-id first-pass-en serve
```

### Terminal B: start work and check status

After A shows the server's startup log, open a **new terminal B** in the same folder and activate `.venv` there before running:

```bash
python scripts/workshop.py --script resilience --language en --run-id first-pass-en start
python scripts/workshop.py --script resilience --language en --run-id first-pass-en status
```

Record the waiting-for-approval state, matching response/task/gate IDs, and `human_authorization: not-granted`. Work must not continue on its own before a decision.

### Terminal B: make a simulated decision

Continue **only after recognizing that this is a simulated decision**:

```bash
python scripts/workshop.py --script resilience --language en --run-id first-pass-en decide --decision approve --confirm-simulated-decision
python scripts/workshop.py --script resilience --language en --run-id first-pass-en wait --timeout-seconds 30
python scripts/workshop.py --script resilience --language en --run-id first-pass-en status
```

Verify that the same request, gate, and output IDs are preserved. `simulation_approved` is not real business approval. Decision validity and checkpoint boundaries are SDK constraints; do not arbitrarily extend them.

### Terminal A: stop the server

Keep results, then use `Ctrl+C` in A to stop **only your server**. If a port conflicts, do not terminate someone else's process. Choose another `--port` and use it consistently for every command in this run.

Continue restart, rejection, and steering exercises with [the same recovery example](advanced/recovery.md). Do not connect external bookings, payments, or other real side effects.

## Completion check

- [ ] I compared outputs, calls, evidence, and usage across the three workflows.
- [ ] I did not interpret `pending-human-review` or a simulated decision as business approval.
- [ ] I verified pause/resume IDs or recorded the OS limitation, and stopped the local server I started.

---

[← 04. Tools](04-tools.md) · [Course home](../../README.md#curriculum) · [06. Retrieval →](06-search-iq.md)
