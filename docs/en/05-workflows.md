# 05. Workflows, simulated approval, and local SDK pause/resume

**English** | [한국어](../05-workflows.md) · [Course home](../../README.md)

**Outcome:** Distinguish sequential, concurrent, and Group Chat results, and experience how pause/resume differs from real business authorization.

**Prerequisites:** Successful MAF execution in 04. Multiple roles can mean additional model calls.

**NC execution record:** sequential, concurrent, and group-chat patterns all ran. Ending Group Chat at its maximum three rounds demonstrates bounded execution—not business convergence, consensus, or a quality pass.

## 1. Sequential execution

```bash
python scripts/workshop.py --language en workflow --pattern sequential --output outputs/learner-notes-en/05-sequential.json
```

The flow analyzes policy, drafts an answer, then reviews evidence. One final output does not imply one model request.

## 2. Concurrent execution

```bash
python scripts/workshop.py --language en workflow --pattern concurrent --output outputs/learner-notes-en/05-concurrent.json
```

Several roles see the same question and evidence simultaneously. Concatenating their outputs does not establish consensus or produce one automatically verified answer.

## 3. Group Chat

```bash
python scripts/workshop.py --language en workflow --pattern group-chat --output outputs/learner-notes-en/05-group-chat.json
```

Read the role conversation in its configured order. This implementation has a three-round maximum and an execution timeout. These are **code safeguards against runaway execution, not course time limits**. A round-limit message is not a business answer.

Across all three results, compare the actual question, number and meaning of outputs, missing evidence, usage, and latency. Adding participants does not necessarily improve quality.

## 4. Validated output suitable for deployment

```bash
python scripts/workshop.py --language en workflow-agent --pattern sequential --retrieval local --prompt v2 --output outputs/learner-notes-en/05-workflow-agent.json
```

This path uses real MAF orchestration, a validated business answer, and call lineage rather than merely joining strings. `pending-human-review` means a person still needs to review it, not that approval was granted.

## 5. Pause and resume with the actual SDK

This section uses **prewritten synthetic work without model or Azure calls** to teach local SDK simulated approval gates and checkpoints. It neither grants real business approval nor executes external business actions.

Check the pinned SDK:

```bash
python scripts/workshop.py --script resilience --language en check
```

Verify `azure-ai-agentserver-core: 2.1.0`, `azure-ai-agentserver-responses: 2.2.0b1`, and `azure_requests_sent: false`. The wrapper removes external telemetry/Foundry settings only from this helper process; it does not modify your shell or `.env`.

Terminal A, in the v1.5 root:

```bash
python scripts/workshop.py --script resilience --language en --run-id first-pass-en serve
```

Terminal B, in the same folder and virtual environment:

```bash
python scripts/workshop.py --script resilience --language en --run-id first-pass-en start
python scripts/workshop.py --script resilience --language en --run-id first-pass-en status
```

Record the waiting-for-approval state, matching response/task/gate IDs, and `human_authorization: not-granted`. Work must not continue on its own before a decision.

Continue **only after recognizing that this is a simulated decision**:

```bash
python scripts/workshop.py --script resilience --language en --run-id first-pass-en decide --decision approve --confirm-simulated-decision
python scripts/workshop.py --script resilience --language en --run-id first-pass-en wait --timeout-seconds 30
python scripts/workshop.py --script resilience --language en --run-id first-pass-en status
```

Verify that the same request, gate, and output IDs are preserved. `simulation_approved` is not real business approval. Decision validity and checkpoint boundaries are SDK constraints; do not arbitrarily extend them.

Keep results, then use `Ctrl+C` in A to stop **only your server**. If a port conflicts, do not terminate someone else's process. Choose another `--port` and use it consistently for every command in this run.

Continue restart, rejection, and steering exercises with [the same recovery example](advanced/recovery.md). Do not connect external bookings, payments, or other real side effects.

**Next → [06. Search, Foundry IQ, and Hybrid](06-search-iq.md)**
