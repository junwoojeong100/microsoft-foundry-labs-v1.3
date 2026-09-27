# Retrieve files from a Hosted session

**English** | [한국어](../../advanced/session-files.md) · [Course home](../../../README.md)

Use the **actual Hosted folder and session ID** from 08 or 10. Do not guess another session's identity.

## 1. Verify the session

```bash
azd ai agent sessions list --cwd "YOUR-HOSTED-ABSOLUTE-PATH" --limit 10
azd ai agent files list --cwd "YOUR-HOSTED-ABSOLUTE-PATH" --session-id "YOUR-ACTUAL-SESSION-ID"
```

Work results live under the session home. For Toolbox results, inspect `workshop-evidence/toolbox-runs/`:

```bash
azd ai agent files list "workshop-evidence/toolbox-runs" --cwd "YOUR-HOSTED-ABSOLUTE-PATH" --session-id "YOUR-ACTUAL-SESSION-ID"
```

Use paths actually returned by the listing; do not invent a remote path.

## 2. Download only the required files

```bash
azd ai agent files download "REMOTE-FILE-FROM-THE-LIST" --target-path "NEW-LOCAL-FILE-PATH" --cwd "YOUR-HOSTED-ABSOLUTE-PATH" --session-id "YOUR-ACTUAL-SESSION-ID"
```

Preserve the request, response, tool result, summary, or failure. Confirm that each downloaded file belongs to the intended request/version. This command does not invoke the model again.

## 3. Stop compute and decide retention

```bash
azd ai agent sessions stop "YOUR-ACTUAL-SESSION-ID" --cwd "YOUR-HOSTED-ABSOLUTE-PATH"
```

Stopping ends running compute but retains the persistent volume. Only consider session deletion after retrieving the files and deciding they no longer need to remain remotely. Deleting a session also removes its files. In retention mode, **stop only; keep the session's retained volume and agent resources**.

[08 Deployment](../08-hosted.md) · [10 Shared tools](../10-toolbox-skills.md) · [15 Cleanup and retention](../15-capstone-cleanup.md)
