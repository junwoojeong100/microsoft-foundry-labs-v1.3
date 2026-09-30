# Lab rerun videos after the repository rename

**English** | [한국어](../videos.md) · [Course home](../../README.md)

Each **4:32/31-scene summary** covers the actual new North Central US group `rg-mflabs15-jw-0928`, with Korean/English captions and no voice-over or music. No old NC/Sweden footage was reused. The new managed failure and final acceptance hold are included, not edited away.

| Language | Video | Captions |
|---|---|---|
| English | [MP4](../assets/videos/foundry-v1.3-summary-en.mp4) | [SRT](../assets/videos/foundry-v1.3-summary-en.srt) |
| 한국어 | [MP4](../assets/videos/foundry-v1.3-summary-ko.mp4) | [SRT](../assets/videos/foundry-v1.3-summary-ko.srt) |

## What was recorded?

**Five authenticated portal scenes:** new model deployments, the first Sol Playground response, Agents, Hosted candidate evaluation, and managed Task Adherence results. The first-response scene is an **actual new request with default Web search removed**; the others read resources/results created in this run.

**CLI scenes** record actual subprocess output displayed live in a Playwright Headless panel, not the native macOS Terminal app. Sources cover new-group creation through files, tools, retrieval, evaluation, deployment, and stopping compute. `review-*-settled` scenes **read this run's preserved original evidence** without new inference. Footer labels distinguish live execution from saved-evidence review. Private recording helpers are not course dependencies; use the included chapter runners to reproduce exercises.

**Language scope:** the Korean main-guide run includes separate English Prompt Agent/File Search exercises and both language OIDC releases. Portal UI is English; both caption editions describe the same originals. Korean retrieval, Memory, and evaluation are not relabelled as separate English runs, and two full language reruns are not claimed.

**Editing and privacy:** normal-speed original video intervals are followed by a hold of **the actual result screenshot captured during that same recording**. Waiting and recorder viewport-shrink frames are omitted. No response text or score is synthesized. A fast-output final-frame synchronization problem was fixed by waiting for rendering and recapturing only saved-evidence reviews. Original recordings remain unchanged; every scene's held result frame was numerically compared with its original screenshot.

Login screens, account emails, subscription identifiers, credentials, and private paths are cropped or masked out. The previously authorized browser session was used only in memory, without exporting authentication state to a file. Temporary recording contexts were closed; the existing user's profile was not deleted.

## Interpret the results correctly

- SDK/Hosted IQ before-and-after dev 6/6, all three policy criteria 6/6, Korean calibration 24/24, and complementary diagnostics 8/8 are distinct evidence. High scores do not replace final safety acceptance.
- **The new managed Task Adherence run returned six rows, five pass/one fail.** The failing row's severity 0/threshold 3 contradicts its original fail/attack-success flags. Previous 5/5 results were not copied; flags/ASR, redacted inputs, and unavailable response IDs remain unchanged.
- **The new Optimizer returned a 1.0 baseline and zero new full candidates.** Original evaluators/threshold 4 and the six-row source audit were verified, but no improvement or promotion occurred. Earlier NC candidates are not mixed into this result.
- The timer's original response, eight session files, and **Korean CI v1/English CI v2 artifacts each passing 6/6** were checked. CI local retrieval and the separate IQ Hosted matrix are different profiles.
- The failed native gate **holds acceptance; no new holdout was unlocked**. All 13 observed lab sessions are idle, and timer/continuous/Insights schedules are off. Retained Search, files/volumes, and logs still incur costs.

The [provenance JSON](../assets/videos/foundry-v1.3-summary-provenance.json) records original videos/result screenshots, SHA256 hashes, intervals, hold durations, captions, and crops. New originals remain private under `dist/recordings/rename-20260928/`; previous state/videos were privately hash-archived. The learner bundle includes only edited media.

**Format:** 1600×1000, 25 fps, H.264/yuv420p, MP4 faststart. Each video has **6,800 frames, 31 scenes, and 31 SRT cues covering 272 seconds**, under 20 MB. Full decoding, caption consistency, and **every scene's final actual-result frame** were checked.

The earlier [NC portal edition](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3/blob/7b7ca26/docs/en/videos.md), [NC CLI edition](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3/blob/1d53a68/docs/en/videos.md), and [Sweden R2 edition](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3/blob/0a8ab50/docs/en/videos.md) remain in their original revisions.

See the [live validation report](validation-report.md) for execution coverage and limitations.
