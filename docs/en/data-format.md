# Distinguish data, results, and language

**English** | [한국어](../data-format.md) · [Course home](../../README.md)

## English materials

| Location | Contents | Purpose |
|---|---|---|
| `data/knowledge/en/policies.json` | Six synthetic Hanbit Technology policies | Retrieval and answer evidence |
| `prompts/en/v1.txt`, `prompts/en/v2.txt` | English instruction variants | Matched prompt comparison |
| `data/evaluation/en/dev.jsonl` | Six development cases | Iterative improvement |
| `data/evaluation/en/holdout.jsonl` | Four final-test cases | One final check after freezing a candidate |
| `data/evaluation/en/calibration.jsonl` | Known good/bad answers | Judge calibration |
| `data/fixtures/en/answers.json` | Prewritten responses | Offline checker practice |
| `data/localization.json` | Translation contract and source hashes | Localization provenance |
| `outputs/` | Results you actually generated | Review, comparison, and lifecycle records |

The `demo` fixture is not a newly generated model answer. Do not use it as evidence of live inference, citations, usage, or traces.

English preserves **document/case IDs, currency limits, effective dates, and approval/abstention judgments**. It does not convert KRW amounts to another currency. The current lodging limit remains KRW 150,000 per person/night; the historical limit is KRW 120,000 and current meals are KRW 30,000 per person/day.

The six `data/policies/*.txt` files are Korean. English File Search does **not** upload these by mistake: with `--language en`, the SDK renders English TXT content from the canonical English JSON, retaining document-ID filenames. There is no prebuilt `data/policies/en/` folder.

## Command placement

```bash
python scripts/workshop.py --language en doctor
python scripts/workshop.py --model-deployment workshop-chat --language en model --question "Say hello in English."
python scripts/workshop.py --script package-hosted --language en
```

- `--model-deployment` and `--script` are **wrapper options** and must come first.
- `--language en` is a **global workshop option**, before `model`, `answer`, `collect`, or another runtime subcommand.
- With `--script`, arguments after the wrapper go to that helper. `package-hosted`, `prepare-hosted`, `package-toolbox`, `export-evaluation`, and `resilience` accept their own `--language en`.
- `verify-toolbox-response` derives language from the immutable package and has **no language flag**.
- `selfstudy.py` has **no global language flag**. Its `prepare-hosted` and `capture` subcommands each accept `--language en` **after the subcommand**, and default to `ko`. Always pass it for English packages/capture, as shown in 08/10. Do not add it to `configure`, `values`, or other subcommands that do not accept it.
- An English question alone does not select English policies, dev cases, or instructions.

`--api account-responses` is accepted only by direct `model`, `answer`, and `collect`; the default stays `project-responses`. It is not a universal option for agents, tools, or Hosted profiles. Both sides of a model-only comparison must use the same API.

## Artifact conventions

| Artifact | English convention |
|---|---|
| Ad hoc chapter results | `outputs/learner-notes-en/` |
| Experiment labels | `baseline-en`, `candidate-en`, `wf-baseline-en`, `wf-candidate-en`, `wf-final-en` |
| Derived extension materials | `outputs/extensions-en/` |
| Skill upload directory | `outputs/extensions-en/policy-review/` only |
| Skill name | `<prefix>-policy-review-en`, read from its manifest |
| Skill readback | `.selfstudy/skill-readback-en/` |
| Default Hosted package | `.build/hosted-en/`; other English profiles end in `-en` |
| Hosted names/folders | Distinct owned names such as `<prefix>-hosted-en` and `<prefix>-matrix-en` |

For the explicit Search-independent Hosted path, use `<prefix>-matrix-local-en` with `wf-local-baseline-en`, `wf-local-candidate-en`, and `wf-local-final-en`. Keep `--retrieval local` in every profile-bearing package, plan, smoke, and collection command; stored-result commands use those exact labels. Do not relabel this as IQ validation.

The extension material directory also contains evaluator references: do not upload the whole directory as a Skill. Reuse the existing manifest only when its prefix, language, and hashes match.

Languages are separate datasets, **never fallbacks**. Do not merge Korean and English results into one frozen experiment. A shared Search ownership ledger is corpus-specific; preserve existing state and use a fresh lab copy with distinct owned names for a separate language run.

Keep versions and hashes when policies or instructions change. Do not edit raw responses, evaluation scores, or holdout to force a pass. Do not open holdout questions/answers before final acceptance.

[07 Evaluation](07-evaluation.md) · [15 Final acceptance](15-capstone-cleanup.md)
