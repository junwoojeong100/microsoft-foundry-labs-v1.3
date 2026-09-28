# North Central US CLI summary videos

**English** | [한국어](../videos.md) · [Course home](../../README.md)

Each **3:28 NC summary** edits fresh North Central US execution and original-evidence reviews into a captioned walkthrough. There is no voice-over or music. **This edition is CLI-only:** authenticated portal recapture needs renewed sign-in, and Sweden portal footage is not reused.

| Language | Video | Captions |
|---|---|---|
| English | [MP4](../assets/videos/foundry-v1.5-summary-en.mp4) | [SRT](../assets/videos/foundry-v1.5-summary-en.srt) |
| 한국어 | [MP4](../assets/videos/foundry-v1.5-summary-ko.mp4) | [SRT](../assets/videos/foundry-v1.5-summary-ko.srt) |

## What was recorded?

Scenes record a **Playwright Headless browser displaying actual subprocess output live**. They are not native macOS Terminal recordings or mocked model answers. Some scenes explicitly show `read-only-saved-NC-evidence`: **reviews of preserved real results**, not another model invocation.

The visible `[local]/.../summarize_nc.py` is a private recording helper that abbreviates original results, not a course dependency. Reproduce the labs with each chapter's included `workshop.py`, `managed_redteam.py`, and `routine_runs.py` commands.

Waiting and recorder viewport-shrink tails are omitted; the final full-width source frame is held for reading. Account/subscription identifiers and private paths are masked or cropped. Some early NC originals inherited a stale Sweden recorder subtitle, but their **actual commands, resources, and endpoints are NC**. The edit excludes that header and uses the original command/result panel. Responses and provider scores are not rewritten.

## Interpret the results correctly

- NC Search/IQ/Hybrid and Sol remain distinct from actual English IQ/Memory scenes. Shared Korean Hosted/diagnostic evidence retains its original-language label; it is not a separate English test.
- Hosted IQ v1/v2 dev 6/6, Korean diagnostic 8/8, calibration 24/24 per language, and four known regression cases are separate evidence. No fresh unseen holdout or production approval is claimed.
- **The new managed Task Adherence-only 5/5 and earlier mixed six-row/five-pass/one-fail result belong to different jobs.** Prohibited Actions inconsistency, redacted inputs, and unavailable response IDs remain.
- Optimizer's required-initialization error is shown as **blocked**. A separate Coherence v13 success did not fix that error or Prohibited Actions.
- TTL-zero Memory, the timer's original response, eight archived session files, and the **actual OIDC release/English 6/6 artifact** are verified. CI's local-retrieval profile is separate from Hosted IQ.

See the [provenance JSON](../assets/videos/foundry-v1.5-summary-provenance.json) for original names, SHA256 hashes, segments, captions, and redactions. Raw recordings stay in the private workshop's `dist/recordings/`; the learner bundle includes only the edited media.

**Format:** 1600×1000, 25 fps, H.264/yuv420p, MP4 faststart. Each video has 5,200 frames and 25 scenes; 27 SRT cues cover all 208 seconds.

The earlier [Sweden R2 videos/provenance](https://github.com/junwoojeong100/microsoft-foundry-v1.5-labs/blob/0a8ab50/docs/en/videos.md) remain in their original revision.

See the [live validation report](validation-report.md) for execution coverage and limitations.
