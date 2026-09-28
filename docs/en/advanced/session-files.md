# Retrieve files from a Hosted session

**English** | [한국어](../../advanced/session-files.md) · [Course home](../../../README.md)

Use the **actual Hosted folder and session ID** from 08 or 10. Do not guess another session's identity.

NC also retrieved **eight JSON files from a successful Hosted Toolbox session**, checking sizes/SHA256 and the original tool-result digest. The failed SSE and successful canonical capture remain separate records. Read Sweden files from their archive rather than querying the deleted group's sessions.

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

## 2. Archive to absolute paths before expiry

In NC, the response reported `/home/session/workshop-evidence/...`, but the CLI file API required a **session-home-relative remote path**. Remove `/home/session/`, list the actual `workshop-evidence/...` directory, and select returned filenames. An absolute remote-path 404 does not establish expiry. In contrast, the **local `--target-path` must be absolute**, as described below.

**Files in the current project's stopped session can be downloaded while still available.** The previous Sweden retrieval/hash match is historical, not a guarantee of remote availability after that group was deleted. Do not generate replacement inference to recreate missing evidence.

Archive only the required request, response, tool result, summary, or failure **before service-managed session/file expiry**. Retaining resources or stopping compute does not guarantee indefinite file retention. Check actual retention conditions; do not substitute a different response for expired evidence.

From the README folder, create a new private archive directory. If it exists, choose a new name:

```bash
python -c "from pathlib import Path; p=Path('.selfstudy/session-archive-en').resolve(); p.mkdir(parents=True,exist_ok=False); print(p)"
```

Use a new file inside that printed absolute directory as `--target-path`. **A relative target can resolve against azd's `--cwd`, not the terminal's current folder**, so always supply an absolute target:

```bash
azd ai agent files download "REMOTE-FILE-FROM-THE-LIST" --target-path "ABSOLUTE-NEW-LOCAL-FILE-PATH" --cwd "YOUR-HOSTED-ABSOLUTE-PATH" --session-id "YOUR-ACTUAL-SESSION-ID"
```

Replace the target with a real absolute path, such as `/.../session-archive-en/file.json` on macOS/Linux or `C:/.../session-archive-en/file.json` on Windows. Record session ID, agent version, remote/local paths, and download time.

Record the local file's byte SHA-256 with:

```bash
python -c "import hashlib,sys; from pathlib import Path; print(hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())" "ABSOLUTE-DOWNLOADED-FILE-PATH"
```

Compare against recorded tool results using the **same payload and hash algorithm**. File-byte SHA-256 differs from canonical JSON digests such as `tool_results_hash`; check whether the recorded hash covers the whole JSON or an inner payload. Never edit raw evidence to force a match. Privately retain the original package, SSE capture, and verification results alongside the archive.

## 3. Stop compute and decide retention

```bash
azd ai agent sessions stop "YOUR-ACTUAL-SESSION-ID" --cwd "YOUR-HOSTED-ABSOLUTE-PATH"
```

Stop only your running session; an already stopped session may still support the retrieval above. Compute stopping, volume retention, and service expiry are separate. In retention mode, **do not delete the session/volume**. Completing a local archive does not authorize removal of shared resources.

[08 Deployment](../08-hosted.md) · [10 Shared tools](../10-toolbox-skills.md) · [15 Cleanup and retention](../15-capstone-cleanup.md)
