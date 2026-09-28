# Portal and CLI summary videos

**English** | [한국어](../videos.md) · [Course home](../../README.md)

Each **3:52 R2 summary** edits real Azure revalidation footage into a captioned walkthrough. There is no voice-over or music.

| Language | Video | Captions |
|---|---|---|
| English | [MP4](../assets/videos/foundry-v1.5-summary-en.mp4) | [SRT](../assets/videos/foundry-v1.5-summary-en.srt) |
| 한국어 | [MP4](../assets/videos/foundry-v1.5-summary-ko.mp4) | [SRT](../assets/videos/foundry-v1.5-summary-ko.srt) |

## What was recorded?

Portal scenes are actual authenticated **Playwright Headless browser interactions**. CLI scenes record a **Headless browser displaying real subprocess output live**. They are not native macOS Terminal recordings or mocked model answers.

Waiting time is shortened and some final frames are held for reading. Account/subscription identifiers and private paths are masked or cropped. Editorial captions explain real results without changing responses or original scores.

## Interpret the results correctly

- Basic Search was created in `swedencentral`; the final Hosted workflow uses **actual Foundry IQ and Sol**. The initial capacity errors remain historical evidence.
- The English video includes actual English Sol, IQ, and Memory executions. The shared final Korean eight-case diagnostic is clearly labeled, not called a separate English eight-case test or fresh holdout.
- Source-reference evaluation, 24/24 calibration judgments per language, and 0/8 policy violations in the explicit diagnostic are distinct. Calibration fixtures are not generated agent responses; a small diagnostic is not an operational safety certificate.
- Optimizer evidence uses source echoes, reference IDs, and counterfactual controls, not captured internal judge requests. No new candidate or performance improvement is claimed.
- The videos show TTL-0 memory, original scheduled-response readback, and retained evidence. The CI scene records OIDC configuration; subsequent live-release evidence is separate in the [validation report](validation-report.md).

See the [provenance JSON](../assets/videos/foundry-v1.5-summary-provenance.json) for original names, SHA256 hashes, segments, captions, and redactions. Raw recordings stay in the private workshop's `dist/recordings/`; the learner bundle includes only the edited media.

**Format:** 1600×1000, 25 fps, H.264/yuv420p, MP4 faststart. Each video has 5,800 frames; 36 SRT cues cover all 232 seconds.

See the [live validation report](validation-report.md) for execution coverage and limitations.
