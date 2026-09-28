# Live validation: North Central US

**English** | [한국어](../validation-report.md) · [Course home](../../README.md)

**The September 28, 2026 continuation verified a fresh North Central US environment.** The current group is `rg-mf15-jw-nc-0928`, account `mf15-jw-nc-0928`, and project `mf15-project`. The answer model is GPT-6 Sol / `workshop-chat`; the different-base judge is GPT-5.5 / `workshop-judge`.

The old Sweden group was deleted at the user's explicit request and its absence confirmed. Configuration, original results, ownership, and deployments were archived with hashes in `.selfstudy/archives/sweden-20260928-before-northcentral/` first. **New NC resources are retained.** Every result below applies only to its actual run scope.

## Current NC results

| Scope | Actual result and limitation |
|---|---|
| Foundation and models | New group/Foundry/project and seven model deployments verified; answer, comparison, judge, embedding, IQ, Router, and optimizer roles remain distinct |
| Agents, files, local tools | Korean/English Prompt Agents/File Search, six-row Code Interpreter CSVs, function/MCP and MAF workflows executed. A bounded Group Chat is not proof of convergence |
| Search, IQ, Hybrid, IQ Chat | Separate Korean/English workspaces and ledgers verified actual retrieval, 3072-dimensional embeddings, and IQ Chat planning/synthesis |
| SDK dev and calibration | Both languages passed dev 6/6 and calibration 24/24 each. The original English 5/6 and retrieval correction remain separate |
| Hosted IQ prompt comparison | Deployments v1/v2 each passed business 6/6, all three policy criteria 6/6, and trace 6/6. Code/model/corpus stayed fixed; no pass-rate improvement claimed |
| Complementary diagnostic | Korean `policy-lab` on v2: 8/8, 0/8 policy violations, trace 8/8. Not managed red teaming or a new holdout |
| Known-case final regression | The same v2 passed 4/4, policy, and trace gates. These previously used cases are regression evidence, not fresh unseen holdout. `deployment_approved: false` |
| Mixed managed red team | Original six rows/five pass/one fail retained. Prohibited Actions severity 0/Safe reason contradicts fail/attack-success flags |
| Separate managed Task Adherence | New evaluation/run: 5/5, severity 0, native threshold 3, `attack_success: false`. Redacted inputs and unavailable original response IDs remain explicit |
| Toolbox, Skills, OpenAPI | Actual Korean Toolbox v1/v3, Skill v1 loading, and OpenAPI verified. Hosted Toolbox v1's canonical capture was independently checked against the final SSE event, package, and hashes |
| Memory, A2A, Routine | Korean/English TTL-zero items read back, Korean A2A delegation, and the timer's original response telemetry verified. Both `Finished/cancelled` and a separate `Killed` attempt remain |
| Insights | Sixteen traces in a one-hour window analyzed; one finding. Suggestions are not ground truth or automatically applied; scheduling is disabled |
| Continuous | Coherence v1 initialization/zero-row failure retained. With the same judge and threshold 3, pinned catalog v13 completed a separate one-row run tied to the original stored response, score 5/pass. Both rules paused |
| Lab RAI policy | Eleven current DefaultV2 filters preserved in a private policy; its reference verified on the separate basic Hosted v2. False-approval request returned `needs_approval`, not evidence of a platform filter block |
| Session files | Eight JSON files retrieved from the successful Hosted Toolbox session; sizes/SHA256 recorded. Original HTTP/SSE, package, and session identities remain |

Primary private evidence is under `outputs/benchmarks/nc-iq-baseline/`, `nc-iq-candidate/`, `nc-policy-lab-ko/`, `nc-known-final-ko/`, `outputs/nc-managed-task-adherence/`, `outputs/nc-observability/`, and `outputs/nc-session-archive/`. English retrieval/evaluation has separate ownership in `.selfstudy/nc-en-workspace/`. Originals are excluded from the public bundle.

## Actual workflow corrections

The first English IQ dev run lost `SCOPE-01` to retrieval filtering, failing D05's mandatory citation. Explicit threshold 0 produced 6/6 under a **new label**, preserving the original 5/6 and every response/score. This is a retrieval change, not prompt-only improvement.

Routine CLI history returned `value: null` although native SDK history contained two attempts. `scripts/routine_runs.py` preserves every ID; telemetry verified the original `Finished` response without substitute inference.

`scripts/managed_redteam.py` provides taxonomy review, frozen versions/scope, safe resume, failed-attempt retention, and raw-flag auditing. **New 5/5 and earlier five pass/one fail belong to different jobs.** Prohibited Actions metrics were not corrected.

## Remaining limits and publication state

**Optimizer remains blocked.** The actual NC SDK job failed because required custom-evaluator `pass_threshold` was missing. The name/version-only SDK reference contract and installed azd instruction/metadata preflight failure are recorded. Evaluators and required fields were not weakened; no improvement or promotion is claimed.

A new CI identity, project-scoped role, account Reader, exact immutable repository/Environment federation, and unchanged main-only protection are configured. **The current NC release run still requires verification after publication.**

The currently linked R2 videos belong to the Sweden history below. Fresh NC CLI captures are being edited; **authenticated portal re-recording requires renewed sign-in**. Old portal footage is not relabelled as NC evidence.

All 278 core tests, 146 SDK tests, Ruff, compilation, and dependency checks passed. These do not substitute for model quality or resolved service limitations. New assets are retained; Search Basic, stored files/volumes, and logs continue to incur costs. Insights' approximately USD 2.01 is that analysis's service **estimate**, not total billed cost.

## Archived Sweden R2 record

The following describes the period **before that group was deleted**. “Retained” and “final” refer to that historical scope, not current NC state. The [original R2 report](https://github.com/junwoojeong100/microsoft-foundry-v1.5-labs/blob/0a8ab50/docs/en/validation-report.md) and private originals remain available.

**The September 28, 2026 rerun successfully created Search and exercised IQ, Hybrid, and connected tools. GPT-6 Sol is now explicit, with separately verified source-reference and task-aware evaluation contracts.**

The group is `rg-mf15-jw-0927-e2e`, region `swedencentral`, and project `mf15-project`. Previous resources and failures were not deleted. Private configuration and original evidence remain in `.selfstudy/`, `.env`, and `outputs/`, outside the repository bundle.

### 1. Remediation outcomes

| Area | Actual remediation and evidence |
|---|---|
| Search creation | Basic, one replica/partition, managed identity, and disabled key authentication succeeded after older resources were freed |
| Search, IQ, Hybrid | Separate Korean/English indexes and ownership ledgers verified keyword, GA IQ, actual 3072-dimensional embeddings/Hybrid, and IQ Chat planning/synthesis |
| Luna project API | Existing Luna deployments were preserved. Sol was explicitly selected and verified through project Responses and real agents |
| Judge separation | GPT-5.5 is a different base model from the Sol target, not merely another deployment alias |
| Optimizer self-grounding | Original documents, expected behavior, and reference IDs travel in `ground_truth` to three custom evaluators. All six returned rows, pinned versions, thresholds, and references were audited |
| Abstention penalized by Relevance | `policy_helpfulness` distinguishes justified abstention from needless refusal; separate grounding/compliance criteria reject unsupported claims |
| Inconsistent red-team aggregate | Original provider metrics remain unchanged. Eight explicit saved diagnostic inputs and real response IDs are graded with a calibrated compliance direction |
| Memory retention | New Korean/English retained stores use TTL `0`; old one-hour stores remain. A Korean item was still readable after 4,063 seconds |
| Routine response readback | Original manual and actual scheduled responses were verified by exact response ID, agent/version/project/trace and original answer, without substitute inference |
| Session evidence | Files from the stopped Hosted session were downloaded to a local archive and hash-checked; the session and volume remain |

This existing environment explicitly reuses the Sol deployment `workshop-compare` and GPT-5.5 deployment `workshop-optimizer`. New learners may use the default aliases in setup; verify the **actual model and version**, not an alias's wording.

### 2. Final IQ Hosted verification

The provider is **actual Foundry IQ**, workflow **sequential**, model API **account-chat**, remote protocol **Invocations**, and target model **Sol**. Local retrieval was not substituted.

| Run | Actual responses/business checks | Three policy evaluators | Actual traces |
|---|---|---|---|
| IQ Hosted v1 dev | 6/6 | 6/6 each | 6/6 |
| IQ Hosted v2 dev | 6/6 | 6/6 each | 6/6 |
| Final v3 dev | 6/6 | 6/6 each | 6/6 |
| Final v3 diagnostic suite v2 | 8/8 | 8/8 each | 8/8 |

The v1/v2 comparison checked the same code, model, and original evidence. Both passed, so no pass-rate improvement is claimed. Version 3 contains the follow-on response-contract repairs identified by diagnostics.

The final diagnostic has eight requested inputs, eight responses, zero missing/error requests, and **0/8 violations under the calibrated policy-compliance criterion**. This is the lab's diagnostic rate, not a rewritten Microsoft managed Red-team UI ASR.

The new diagnostic suite's optional `allowed_citations` explicitly permits supported additional citations only for PL05/PL06/PL07. Mandatory references remain mandatory; unknown, unretrieved, or unrelated extras fail. Procedure-only questions require `limit_krw: null`. Previous version-1 failures and frozen datasets remain unchanged.

**Evidence:** `outputs/benchmarks/r2-iq-final-dev/` and `outputs/benchmarks/r2-iq-final-lab/`. These diagnostics are not called a new holdout. The earlier holdout remains its original historical run.

### 3. Evaluation inputs and judgments

The metrics are `policy_groundedness`, `policy_helpfulness`, and `policy_compliance`, with a **4/5 threshold** and higher scores meaning better-supported, more appropriate responses.

For each language, eight controls covered a correct answer, wrong amount, counterfactual reference, justified abstention, irrelevant refusal, false approval, correct approval-boundary guidance, and fabricated citation. **All 24 judgments matched their expected outcomes.** Negative examples were required to fail.

Audits verify reference-envelope hashes, returned source echoes, reference IDs in reasons, and score/pass direction. **Internal judge request bodies were not captured.** A counterfactual control also confirmed that changing the reference causes the same answer to fail.

The new Sol Optimizer run reached a baseline score of 1.0 and stopped without generating candidates. `scripts/audit_optimizer.py` checked all six original/returned inputs, evaluator versions, thresholds, judge, and references. **Reference transport was verified; prompt improvement and new candidates were not claimed, and nothing was promoted.**

### 4. Connected tools, English execution, and scheduling

Toolbox v1 performed real Search queries and Sol inference. Tool Search/Skill execution included `load_skill`, `tool_search`, and `call_tool`. Corrected Skill instructions were uploaded as a new version with byte-exact download verification, preserving the previous version. OpenAPI and remote Hosted Toolbox also used actual Search results.

The English path uses a separate prefix/index/ledger in `.selfstudy/r2-en-workspace/`; it never overwrote the Korean index. Six English Sol/IQ dev responses passed all three policy evaluators. English Search, IQ, Hybrid, IQ Chat, and OpenAPI were also exercised.

Routines used a stateless timer with explicit `action.input`. Passing caller-created conversations failed with `conversation_not_found`, and those attempts remain. Disabling a completed timer can change its service phase to `cancelled`; the verifier requires `Finished` plus the exact original completed response trace and preserves that raw phase rather than rewriting it.

### 5. Retention and interpretation

Existing resources, agent versions, evaluations, files, and ownership records were not deleted. Completed compute sessions are stopped and schedules/monitors disabled. Memory/vector-store expiration and managed-session lifetimes are distinct. Downloaded evidence is retained with hashes in `outputs/r2-session-archive/`.

Search Basic, storage, and logs can continue to incur charges. An empty posted-cost query is not proof of zero total cost.

Earlier failures were not overwritten with successful results. Original capacity errors, Luna project errors, self-grounding, contradictory ASR, unavailable caller conversations, and response/citation-contract failures remain separate evidence. This report describes the **latest verified lab scope**.

### 6. Code and CI reproducibility

All 278 core tests, 124 SDK tests, Ruff, and bilingual document/command/link checks passed. [GitHub checks](https://github.com/junwoojeong100/microsoft-foundry-v1.5-labs/actions/runs/36362144665) and the [approved OIDC release](https://github.com/junwoojeong100/microsoft-foundry-v1.5-labs/actions/runs/36362528860) succeeded on code commit `5267633`.

Downloaded artifacts verified **six actual English responses from CI agent v2, 6/6 business checks, the current runtime code hash, an idle session, and no persistent-file deletion**. This CI local-retrieval smoke path is separate from the IQ Hosted verification above.
