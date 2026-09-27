# Verify interruption, restart, and rejection

**English** | [한국어](../../advanced/recovery.md) · [Course home](../../../README.md)

Complete the basic run in 05 first. These are **synthetic tasks and simulated decisions**, with no Azure calls or real business authorization.

## Resume the same interrupted task

Choose a new `run-id`. Terminal A:

```bash
python scripts/workshop.py --script resilience --language en --run-id restart-check-en serve
```

Terminal B:

```bash
python scripts/workshop.py --script resilience --language en --run-id restart-check-en start
python scripts/workshop.py --script resilience --language en --run-id restart-check-en status
```

Record response, gate, and output IDs. Once the task is waiting for approval, use `Ctrl+C` in A to stop **only this server**.

Restart the same `serve` command in A. In B, run **status, not start**:

```bash
python scripts/workshop.py --script resilience --language en --run-id restart-check-en status
python scripts/workshop.py --script resilience --language en --run-id restart-check-en decide --decision approve --confirm-simulated-decision
python scripts/workshop.py --script resilience --language en --run-id restart-check-en wait --timeout-seconds 30
```

Verify the same response/gate and original output IDs. If the decision expired while you waited, record that failure. Do not substitute a new task and call it the same resumed execution.

## Reject instead of approving

Using a separate `run-id`, perform `serve → start → status`, then send the simulated rejection:

```bash
python scripts/workshop.py --script resilience --language en --run-id reject-check-en decide --decision reject --confirm-simulated-decision
python scripts/workshop.py --script resilience --language en --run-id reject-check-en status
```

Verify it does not continue as though approved. Giving an explicit decision to a waiting task is this example's steering mechanism; it does not authorize arbitrary new work or external payments.

## What did you verify?

You checked checkpoints, persisted state, and the link between the original request and decision. You did not establish exactly-once effects in external systems, actual human authorization, or recovery from every possible failure.

Preserve results and stop your servers. If choosing to remove local state, first inspect that run's `cleanup --help` and owned run ID. In [retention mode](../15-capstone-cleanup.md#retention-mode), keep state and skip cleanup.

[Return to 05](../05-workflows.md)
