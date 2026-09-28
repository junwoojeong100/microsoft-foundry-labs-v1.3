# North Central US portal and CLI summary videos

**English** | [한국어](../videos.md) · [Course home](../../README.md)

Each **3:52 NC summary** combines authenticated portal reviews and real CLI sources without voice-over or music. **Playwright Headless portal recapture and both language edits are complete.** The previous CLI edition was archived separately; no Sweden portal footage was reused.

| Language | Video | Captions |
|---|---|---|
| English | [MP4](../assets/videos/foundry-v1.5-summary-en.mp4) | [SRT](../assets/videos/foundry-v1.5-summary-en.srt) |
| 한국어 | [MP4](../assets/videos/foundry-v1.5-summary-ko.mp4) | [SRT](../assets/videos/foundry-v1.5-summary-ko.srt) |

## What was recorded?

**Eight portal scenes** record the actual NC project after user sign-in and reopening the same temporary profile with `headless=True`: Agents, model deployments, the original Optimizer failure, successful fix, baseline, candidate, Prohibited Actions v5, and Task Adherence. These are **read-only reviews of completed results**, not new model calls, promotions, or permission changes.

**CLI scenes** retain earlier Playwright Headless recordings of actual subprocess output, not native macOS Terminal footage or mocked answers. `read-only-saved-NC-evidence` identifies preserved-result reviews. The visible `[local]/.../summarize_nc.py` is a private recording helper, not a course dependency; reproduce labs with each chapter's `workshop.py`, `managed_redteam.py`, and `routine_runs.py`.

The portal UI is English; **Korean/English captions explain the same footage**. Korean Optimizer evaluations are not relabelled as separate English runs. Login screens, account emails, subscription identifiers, and credentials are excluded from the edit. Authentication state was not exported to a separate file; the temporary browser and login profile were removed after capture.

Waiting and recorder viewport-shrink tails are omitted; the final full-width source frame is held for reading. Account/subscription identifiers and private paths are masked or cropped. Some early NC originals inherited a stale Sweden recorder subtitle, but their **actual commands, resources, and endpoints are NC**. The edit excludes that header and uses the original command/result panel. Responses and provider scores are not rewritten.

## Interpret the results correctly

- NC Search/IQ/Hybrid and Sol remain distinct from actual English IQ/Memory scenes. Shared Korean Hosted/diagnostic evidence retains its original-language label; it is not a separate English test.
- Hosted IQ v1/v2 dev 6/6, Korean diagnostic 8/8, calibration 24/24 per language, and four known regression cases are separate evidence. No fresh unseen holdout or production approval is claimed.
- **Task Adherence-only 5/5, the earlier mixed six-row/five-pass/one-fail run, and the follow-up one-row Prohibited Actions v5 run are separate jobs.** V5 still contradicts its Safe reason with Fail/ASR 100%. Redacted inputs and unavailable response IDs remain; this tool-free comparison does not validate Azure tool safety.
- **Both the original Optimizer failure and successful fix are shown.** Explicit required initialization retained the original evaluators/threshold 4. Baseline and candidate each passed all six rows and source-reference audits but tied at 1.0; `best` remains baseline. Intermediate minibatch failures are retained, with no promotion.
- TTL-zero Memory, the timer's original response, eight archived session files, and the **actual OIDC release/English 6/6 artifact** are verified. CI's local-retrieval profile is separate from Hosted IQ.

See the [provenance JSON](../assets/videos/foundry-v1.5-summary-provenance.json) for original names, SHA256 hashes, segments, captions, and crops. New originals remain private under `dist/recordings/portal/nc-headless-final-20260928/`; the previous CLI edition/provenance is hash-archived under `.selfstudy/archives/nc-cli-before-headless-20260928/`. The learner bundle includes only edited media.

**Format:** 1600×1000, 25 fps, H.264/yuv420p, MP4 faststart. Each video has **5,800 frames, 28 scenes, and 30 SRT cues covering 232 seconds**. Korean is approximately 13.95 MB; English 14.53 MB. Both passed full decoding and caption-consistency checks.

The earlier [NC CLI videos/provenance](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5/blob/1d53a68/docs/en/videos.md) and [Sweden R2 edition](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5/blob/0a8ab50/docs/en/videos.md) remain in their original revisions.

See the [live validation report](validation-report.md) for execution coverage and limitations.
