# Distinguish data, results, and language

**English** | [한국어](../data-format.md) · [Course home](../../README.md)

## English materials

| Location | Contents | Purpose |
|---|---|---|
| `data/knowledge/en/policies.json` | Six synthetic Hanbit Technology policies | Retrieval and answer evidence |
| `prompts/en/v1.txt`, `prompts/en/v2.txt` | English instruction variants | Matched prompt comparison |
| `data/evaluation/en/dev.jsonl` | Six development cases | Iterative improvement |
| `data/evaluation/en/holdout.jsonl` | Four final-test cases | One final check after freezing a candidate |
| `data/evaluation/en/calibration.jsonl` | Two legacy grounding examples | Legacy checks only; not policy calibration |
| `data/evaluation/en/policy-calibration.json` | Eight policy controls | 24 expected judgments across three criteria |
| `data/evaluation/en/policy-lab.jsonl` | Eight explicit synthetic diagnostics | Separate `policy-lab` suite, not holdout |
| `data/fixtures/en/answers.json` | Prewritten responses | Offline checker practice |
| `data/localization.json` | Original freeze and active prompt revision | Localization provenance |
| `outputs/` | Results you actually generated | Review, comparison, and lifecycle records |

The `demo` fixture is not a newly generated model answer. Do not use it as evidence of live inference, citations, usage, or traces.

English preserves **document/case IDs, currency limits, effective dates, and approval/abstention judgments**. It does not convert KRW amounts to another currency. The current lodging limit remains KRW 150,000 per person/night; the historical limit is KRW 120,000 and current meals are KRW 30,000 per person/day.

The six `data/policies/*.txt` files are Korean. English File Search does **not** upload these by mistake: with `--language en`, the SDK renders English TXT content from the canonical English JSON, retaining document-ID filenames. There is no prebuilt `data/policies/en/` folder.

## Project and region boundaries

The current lab targets a **new North Central US project**. Keep Sweden `.env`, ownership ledgers, results, and packages in their private hashed archive, not in the new active workspace. Verify the new project ID/endpoint/prefix and use distinct language-specific ownership.

Example new labels are `nc-baseline-en`, `nc-candidate-en`, `nc-policy-calibration-en`, and `nc-policy-lab-en`; use `-ko` for Korean. When replacing chapter examples, update every preparation, collection, evaluation, compare, report, and verify reference consistently. Never copy old results into new labels or rewrite their hashes.

Sweden records below are historical. NC's mixed native job retains its original six rows/**five pass/one fail**; a separate Task Adherence-only job passed **5/5**. No failed row was removed and no custom diagnostic was substituted. Preserve each run's raw evidence, redacted inputs, actual returned counts, and flag direction. Neither job is holdout evidence.

## Prompt revision provenance

`data/localization.json` preserves the **initial frozen files, hashes, and timestamps**. A separate `active_prompt_revision` records the 2026-09-28 evidence-only/procedure-response revision, previous commit, old/new Korean and English prompt SHA-256 values, and English workflow hash.

The original corpus, core dev, and holdout hashes are unchanged. Checks validate the current prompt revision alongside historical provenance—not by rewriting old experiment hashes. New runs record the active revision and actual hashes while preserving earlier evidence.

## Command placement

```bash
python scripts/workshop.py --language en doctor
python scripts/workshop.py --model-deployment "ACTUAL-SOL-DEPLOYMENT" --language en model --question "Say hello in English."
python scripts/workshop.py --script package-hosted --language en
```

- `--model-deployment` and `--script` are **wrapper options** and must come first.
- `--language en` is a **global workshop option**, before `model`, `answer`, `collect`, or another runtime subcommand.
- With `--script`, arguments after the wrapper go to that helper. `package-hosted`, `prepare-hosted`, `package-toolbox`, `export-evaluation`, and `resilience` accept their own `--language en`.
- `verify-toolbox-response` derives language from the immutable package and has **no language flag**.
- `selfstudy.py` has **no global language flag**. Its `prepare-hosted` and `capture` subcommands each accept `--language en` **after the subcommand**, and default to `ko`. Always pass it for English packages/capture, as shown in 08/10. Do not add it to `configure`, `values`, or other subcommands that do not accept it.
- An English question alone does not select English policies, dev cases, or instructions.

`--api account-responses` is accepted only by direct `model`, `answer`, and `collect`; the default stays `project-responses`. It is not a universal option for agents, tools, or Hosted profiles. Both sides of a model-only comparison must use the same API.

## Policy evaluation inputs and results

`prepare-extensions --policy` creates a new labeled input set with a source-bound `optimizer-dev.jsonl`, `policy-evaluator-definitions.json`, and manifest. It does not rewrite existing `extensions-en` inputs or evaluation evidence.

Mode `policy-reference-v1` carries a trusted original-reference envelope in evaluator input `ground_truth`. Do not pass it to the target agent or upload the whole evaluator-input directory as a Skill. Audit source hashes, complete `reference_id` values, and canonical `result` (integer 1–5) and `reason`.

`policy_groundedness`, `policy_helpfulness`, and `policy_compliance` all use **threshold 4, higher-is-better**. Calibration's 24/24 counts agreement with expected judgments, not high scores for intentionally bad controls. Eight `policy-lab` diagnostics are separate from six core dev cases and four holdout cases. Input preparation, calibration success, and real target-grading success are distinct.

### Diagnostic citations and structured fields

**Diagnostic suite version 2** uses explicit `allowed_citations` only for **PL05, PL06, and PL07 in both languages**. The allowed set must include every mandatory `required_citations` entry. IDs in the case lists and answer citations must be known document IDs without duplicates. Answers still need all required references; extra citations must remain within the allowed set, and unrelated references are rejected. Other case contracts are unchanged.

The contract was also verified on **NC Hosted IQ deployment v2's separate eight-row diagnostic**. Preserve earlier Sweden Hosted v3 and frozen suite-version-1 records unchanged. Deployment version, prompt key, and suite version are different fields; never rewrite stored versions/hashes.

For **procedure-only queries**, such as PL06's receipt question, `limit_krw` must be **`null`**. A known 150000 limit in the source is not a requested amount. These structured checks are distinct from semantic judging; the corrected instructions were verified through a new frozen runtime/label. Preserve the earlier `150000` response unchanged.

### Optimizer export audit

`scripts/audit_optimizer.py` is a standalone local helper with `--export-directory`, original `--dataset`, `--calibration-label`, its own `--language`, and a new `--output` path. Use [12's command](12-improvement.md#3-optimize-instructions-only), not an invented `workshop.py --script` alias.

It reads the original `definition.json`, `run.json`, `output-items.json`, `summary.json`, source data, and calibration without rewriting their hashes. Its `proof_level` is source echo + reason reference ID + counterfactual calibration, with **`internal_judge_requests_captured: false`**. A valid audit is not a claim of generated candidates or prompt improvement.

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
| Retained Memory store | `<prefix>-memory-retained-en`; Korean uses a separate `-ko` store |
| Memory ownership record | `outputs/memory/<store-name>/ownership.json` |

For the explicit Search-independent Hosted path, use `<prefix>-matrix-local-en` with `wf-local-baseline-en`, `wf-local-candidate-en`, and `wf-local-final-en`. Keep `--retrieval local` in every profile-bearing package, plan, smoke, and collection command; stored-result commands use those exact labels. Do not relabel this as IQ validation.

The extension material directory also contains evaluator references: do not upload the whole directory as a Skill. Reuse the existing manifest only when its prefix, language, and hashes match.

Languages are separate datasets, **never fallbacks**. Do not merge Korean and English results into one frozen experiment. A shared Search ownership ledger is corpus-specific; preserve existing state and use a fresh lab copy with distinct owned names for a separate language run.

## Memory selector and retention

`WORKSHOP_MEMORY_STORE_NAME` is a **global selector for the current run**. An explicit name is not automatically changed by `--language en`. Choose distinct names under the current prefix: `<prefix>-memory-retained-en` for English and `<prefix>-memory-retained-ko` for Korean. Set and check the correct selector whenever switching languages.

Replace `YOUR-PREFIX` with your actual prefix:

```bash
python scripts/selfstudy.py set WORKSHOP_MEMORY_STORE_NAME "YOUR-PREFIX-memory-retained-en"
python scripts/workshop.py --language en memory plan
```

Use [11's creation sequence](11-memory-a2a-routines.md#1-memory-persist-an-item-and-recall-it-in-a-new-request) with `memory create --ttl-seconds 0 --confirm-create`. **0 is the new default and means no automatic item expiry**; a positive TTL may be at most 31,536,000 seconds (365 days).

Selecting a name or viewing a local plan does not create or update a remote store. Preserve its actual name, language, TTL, and IDs in the ownership record. Older one-hour stores retain their original settings and records: no silent update, adoption, or deletion. Use new labels for the new store's results.

Keep versions and hashes when policies or instructions change. Do not edit raw responses, evaluation scores, or holdout to force a pass. Do not open holdout questions/answers before final acceptance.

[07 Evaluation](07-evaluation.md) · [15 Final acceptance](15-capstone-cleanup.md)
