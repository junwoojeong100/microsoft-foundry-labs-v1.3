# Live validation: Sweden Central

**English** | [한국어](../validation-report.md) · [Course home](../../README.md)

**The September 28, 2026 rerun successfully created Search and exercised IQ, Hybrid, and connected tools. GPT-6 Sol is now explicit, with separately verified source-reference and task-aware evaluation contracts.**

The group is `rg-mf15-jw-0927-e2e`, region `swedencentral`, and project `mf15-project`. Previous resources and failures were not deleted. Private configuration and original evidence remain in `.selfstudy/`, `.env`, and `outputs/`, outside the repository bundle.

## 1. Remediation outcomes

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

## 2. Final IQ Hosted verification

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

## 3. Evaluation inputs and judgments

The metrics are `policy_groundedness`, `policy_helpfulness`, and `policy_compliance`, with a **4/5 threshold** and higher scores meaning better-supported, more appropriate responses.

For each language, eight controls covered a correct answer, wrong amount, counterfactual reference, justified abstention, irrelevant refusal, false approval, correct approval-boundary guidance, and fabricated citation. **All 24 judgments matched their expected outcomes.** Negative examples were required to fail.

Audits verify reference-envelope hashes, returned source echoes, reference IDs in reasons, and score/pass direction. **Internal judge request bodies were not captured.** A counterfactual control also confirmed that changing the reference causes the same answer to fail.

The new Sol Optimizer run reached a baseline score of 1.0 and stopped without generating candidates. `scripts/audit_optimizer.py` checked all six original/returned inputs, evaluator versions, thresholds, judge, and references. **Reference transport was verified; prompt improvement and new candidates were not claimed, and nothing was promoted.**

## 4. Connected tools, English execution, and scheduling

Toolbox v1 performed real Search queries and Sol inference. Tool Search/Skill execution included `load_skill`, `tool_search`, and `call_tool`. Corrected Skill instructions were uploaded as a new version with byte-exact download verification, preserving the previous version. OpenAPI and remote Hosted Toolbox also used actual Search results.

The English path uses a separate prefix/index/ledger in `.selfstudy/r2-en-workspace/`; it never overwrote the Korean index. Six English Sol/IQ dev responses passed all three policy evaluators. English Search, IQ, Hybrid, IQ Chat, and OpenAPI were also exercised.

Routines used a stateless timer with explicit `action.input`. Passing caller-created conversations failed with `conversation_not_found`, and those attempts remain. Disabling a completed timer can change its service phase to `cancelled`; the verifier requires `Finished` plus the exact original completed response trace and preserves that raw phase rather than rewriting it.

## 5. Retention and interpretation

Existing resources, agent versions, evaluations, files, and ownership records were not deleted. Completed compute sessions are stopped and schedules/monitors disabled. Memory/vector-store expiration and managed-session lifetimes are distinct. Downloaded evidence is retained with hashes in `outputs/r2-session-archive/`.

Search Basic, storage, and logs can continue to incur charges. An empty posted-cost query is not proof of zero total cost.

Earlier failures were not overwritten with successful results. Original capacity errors, Luna project errors, self-grounding, contradictory ASR, unavailable caller conversations, and response/citation-contract failures remain separate evidence. This report describes the **latest verified lab scope**.
