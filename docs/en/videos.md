# Portal and CLI summary videos

**English** | [한국어](../videos.md) · [Course home](../../README.md)

Each **3:38** summary edits real Azure execution footage into a captioned walkthrough. There is no voice-over or music.

| Language | Video | Captions |
|---|---|---|
| English | [MP4](../assets/videos/foundry-v1.5-summary-en.mp4) | [SRT](../assets/videos/foundry-v1.5-summary-en.srt) |
| 한국어 | [MP4](../assets/videos/foundry-v1.5-summary-ko.mp4) | [SRT](../assets/videos/foundry-v1.5-summary-ko.srt) |

## What was recorded?

Portal scenes are actual authenticated **Playwright Headless browser interactions**. CLI scenes record a **Headless browser displaying real subprocess output live**. They are not native macOS Terminal recordings or mocked model answers.

Waiting time is shortened and some final frames are held for reading. Account/subscription identifiers and private paths are masked or cropped. Editorial captions explain real results without changing responses or original scores.

## Interpret the results correctly

- Resources were created in `swedencentral`. Search could not be provisioned because of capacity/quota, so the Hosted matrix explicitly uses **local retrieval**, not IQ.
- The English video includes actual English prompts, data, and agents. Its final verdict is an **English explanation of the shared Korean matrix result**, not a separately executed English holdout.
- Passing business checks is not the same as passing every native metric or approving production. Relevance warnings and `deployment_approved: false` remain visible.
- The CI scene proves repository-bound OIDC and branch restrictions were configured. That scene alone does not prove a release workflow executed.

See the [provenance JSON](../assets/videos/foundry-v1.5-summary-provenance.json) for original names, SHA256 hashes, segments, captions, and redactions. Raw recordings stay in the private workshop's `dist/recordings/`; the learner bundle includes only the edited media.

**Format:** 1600×1000, 25 fps, H.264/yuv420p, MP4 faststart. Each video has 5,450 frames; 33 SRT cues cover all 218 seconds.

See the [live validation report](validation-report.md) for execution coverage and limitations.
