# Live validation: North Central US

**English** | [한국어](../validation-report.md) · [Course home](../../README.md)

## Fresh run after the repository rename · 2026-09-28

**Lab execution and recording are complete; final quality acceptance is held.** The new group is `rg-mflabs15-jw-0928`, account `mflabs15-jw-0928`, project `mf15-project`, and prefix `lab-jw-mfl15-0928`. Only the confirmed previous NC lab group `rg-mf15-jw-nc-0928` was deleted, with absence verified before creating the new group. Other lab and business groups were untouched.

**3,428 files** from the previous `.env`, `.selfstudy`, `outputs`, and `.build` were privately archived with hashes before initializing fresh active state. Original recordings and published videos were retained. Execution used source revision **`7b7ca26f4be381e8065ed97573fbd8cdf1928487`** and the existing Python 3.13.15 environment. Only the initial local readiness check used Python 3.14.

| Scope | Actual new-run result |
|---|---|
| Foundation/models | New group, Foundry/project, logs, Basic Search, and six model deployments with separate answer/comparison/judge/embedding/IQ/optimizer roles. Optional Router was inspected in the catalog, not invoked |
| Responses/files/tools | Actual Sol Playground request with Web search removed; separate Korean/English Prompt Agents and six-file File Search agents. Korean current/historical/missing-policy citations, local functions/MCP, and an actual six-row CSV verified |
| Workflows/recovery | Sequential, concurrent, group chat, structured workflow, and local SDK simulated approval/resume with preserved IDs. No real human approval or claim of group-chat consensus |
| Search/IQ/Hybrid | Six Korean documents retrieved through keyword, GA IQ, actual 3,072-dimensional Hybrid, and GPT-5.6 Luna IQ Chat. Previous English retrieval was not adopted as a new run |
| SDK/model comparison | Baseline/candidate each business 6/6, all three policy criteria 6/6, valid reference audits, Korean calibration 24/24. Separate matched account-responses Sol/Luna dev comparison: each 6/6 |
| Hosted | Standalone Responses agent v1 and workflow v1 verified locally/remotely. IQ sequential/account-chat/Invocations v1/v2 each dev 6/6, all three policy criteria 6/6, and actual exported traces 6/6 |
| Complementary diagnostics | Fixed IQ Hosted v2 `rename-policy-lab`: actual 8/8, three policy criteria 8/8, traces 8/8. Not managed red teaming or a fresh holdout |
| Toolbox/Skill/OpenAPI | Plain v1, discovery v2, Skill-v1-enabled v3, actual load/search/answer/OpenAPI, and remote Toolbox v1 SSE/package/version/hash verification |
| Memory/A2A/timer | New Korean TTL-zero store: alpha readback, empty beta, same-item update. Actual A2A 1.0 delegation. Timer's original answer/trace verified through telemetry, then disabled; `Killed` attempt retained |
| Conversations | Two new conversations/six turns: Groundedness/Coherence each 6/6 at turn level and 2/2 at conversation level |
| Optimizer | `opt_bfa363582dff4c048ca6fceaea6ae953` succeeded with the original three evaluator-v1 definitions, threshold 4, and judge. Baseline 1.0/6 of 6 with a valid source audit; **zero new full candidates**, no promotion |
| Managed Task Adherence | `evalrun_a50eea6a7d124669938baa462423bdb7` completed: **six rows, five pass/one fail**. Failing row severity 0/threshold 3 contradicts `passed=false`, `attack_success=true`; audit gate failed |
| Operations/protection | Insights: one hour, three traces, zero new findings, schedule disabled. Coherence v13: one original stored response, score 5/pass, then paused. Standalone Hosted v2 references eleven preserved DefaultV2 protections; refusing false approval is not proof of a platform filter block |
| CI/CD | New identity, exact repository/Environment subject, unchanged main-only protection. Korean CI v1 and English CI v2 each six new responses/6 of 6, with stopped-session artifacts |
| Final lifecycle | All 13 observed Hosted sessions idle, active zero. Timer/continuous/Insights schedules disabled or paused. Eight original remote Toolbox JSON files downloaded and checked against hashes, answer, tools, and model lineage |

**The managed failure was not erased or retried into a pass.** Row 6's explanation criticizes a non-substantive response, while its severity is zero. Inputs are service-redacted and original response IDs unavailable, so no input was reconstructed or failure changed to success. This is not the previous NC 5/5 job. Following the guide's final gate, **no new holdout was unlocked and acceptance remains held**; the complementary 8/8 does not override it.

Execution blockers remain recorded. The initial Hosted account-chat 401 occurred because project-scoped access does not authorize the parent account API. **Cognitive Services OpenAI User on this lab account, for the exact runtime principal**, fixed the same version. [Chapter 12's permission guidance](12-improvement.md#5-deploy-the-baseline-profile) now distinguishes these scopes. A2A's immediate post-creation 400 passed after the same connection propagated, under a new label. Parent-resource model-write conflicts were resolved by serializing writes. Do not run settings writers concurrently in one checkout.

The first Optimizer inline submission was rejected for the `dataset_items` wire field. The SDK model description and service contract differed; a **new request using the public mapping constructor and `train_dataset.items`** succeeded. Required evaluator `initialization_parameters` and threshold 4 remained unchanged. Baseline evaluation `eval_14fc534255ff4927a1582ad18fe3e186` / `evalrun_b72615bcffe74ebfb3971ec004afeb2b` was audited against all six submitted dev rows and source references. Candidate generation and improvement remain separate, unclaimed outcomes.

On the same source revision, [repository checks](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3/actions/runs/36405755604), [new OIDC authentication](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3/actions/runs/36409519229), [Korean release](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3/actions/runs/36409523146), and [English release](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3/actions/runs/36410260357) succeeded. CI local retrieval is distinct from the separate IQ Hosted matrix.

New originals remain private in `outputs/rename-*`, `outputs/benchmarks/rename-*`, `.selfstudy/rename-*`, and `dist/recordings/rename-20260928/`. The [new summaries](videos.md) are **4:32/31 scenes per language**, with no old NC/Sweden footage mixed in. The Korean main-guide run and separate English file/agent/CI exercises are distinguished; bilingual captions do not imply a second complete English rerun.

**New resources are retained.** Search Basic, files/volumes, and logs can keep incurring charges; the next cost review date is 2026-09-29. The new group's actual-cost query has no posted rows yet, so total cost is not established. This is not a zero-cost claim or a spending cap.

## Archived NC record before the repository rerun

“Current,” “new,” retention, 5/5, and candidate-generation statements below describe the **then-existing `rg-mf15-jw-nc-0928` environment, now deleted**. They are not adopted as the new run's results or remote assets.

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
| Follow-up Prohibited Actions v5 | A separate one-row run again contradicts its Safe (No Defect)/score-0 reason with `passed: false`/`attack_success: true`. Neither the original mixed job nor its ASR was changed |
| Separate managed Task Adherence | New evaluation/run: 5/5, severity 0, native threshold 3, `attack_success: false`. Redacted inputs and unavailable original response IDs remain explicit |
| Optimizer initialization | A new job succeeded with the original evaluator versions, judge, and explicit threshold 4. Baseline/candidate each passed 6/6 and source audits, tied at 1.0. No promotion |
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

## Follow-up verification and remaining limits

**Optimizer's missing `pass_threshold` initialization is resolved.** Original failure `opt_3aa677fe825a4b3ea433904433b57e53` remains intact. The authenticated portal exposed per-evaluator `initialization_parameters`; the SDK's public mapping constructor retained **all three original names/version 1 and required `pass_threshold: 4`**. The actual HTTP request body was checked too. New job **`opt_6f23f99c0f2d49f7b930c7b25629543f` succeeded**.

| New job's full evaluation | Actual rows | Three policy criteria | Source-reference audit | Native average score |
|---|---:|---|---|---:|
| Baseline | 6/6 | Each 6/6 | valid | 1.0 |
| Candidate 1 | 6/6 | Each 6/6 | valid | 1.0 |

Evaluation group: `eval_c0909152f8804fa9b21bb477415f407b`; baseline run: `evalrun_6c84c68860064630b1a040e76ce90caf`; candidate run: `evalrun_bbf1e2df5e394983a499920de4852bc8`. The candidate changes instructions only, retaining Sol and the original Korean `nc-policy-cal-ko` calibration. **Two entries were returned, including baseline: one new candidate.** `best` remains baseline; average tokens rose from 1,530 to approximately 2,074.17. No improvement or promotion is claimed, and published version 1's instructions/model remain unchanged.

`max_candidates: 2` is not a request cap. This job performed two full six-row evaluations and eleven three-row minibatches; service telemetry reports **45 agent calls**, not 45 distinct test cases. All intermediate results remain, including minibatch 3's three failures. This is neither failure-erasing success nor a fresh holdout.

In a counterexperiment, `deployment_name`/required-`threshold` definitions passed all 24 controls, but name/version-only Optimizer job `opt_ed3d8823d9fe41aaa7921ec69297ec8b` again failed with missing `threshold`. Renaming the field or declaring a schema `default` was not sufficient. The successful path **explicitly binds the original evaluators' required initialization**. The installed azd standalone instruction/metadata preflight issue is not claimed as fixed.

**Prohibited Actions remains unresolved.** Separate v5 evaluation `eval_d550312fc1134d179fc79cc68a21686c` / run `evalrun_72efb1dd0ed84486a88bd92bf2b19c12` again returned one row with `Safe (No Defect)`/score 0 contradicting fail/attack-success flags; the portal also shows ASR 100%. This tool-free response comparison does not validate Azure tool-call safety. The original mixed six rows, redacted inputs, and unavailable response IDs remain unchanged; no inverted flags or corrected ASR were manufactured.

New originals, HTTP body, both full audits, intermediate results, and preservation hashes are under `outputs/nc-resume-20260928/` and `outputs/evaluation-exports/nc-optimizer-initialized-{baseline,candidate}/`. Service verification is recorded in `outputs/nc-resume-20260928/verification-final.json`; subsequent video completion is in that directory's `media-completion.json`. All 19 original failure-file hashes remain unchanged; the replaced CLI videos are separately archived with their original hashes.

Earlier CI identity, project role, account Reader, repository/Environment federation, and main-only protection verification remains valid for its recorded scope. Code commit **`edf0990`** passed [repository checks](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3/actions/runs/36382485708) and the [actual NC OIDC release](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3/actions/runs/36382758497) at that time. Original artifacts retain **CI agent v1, six English responses/6 of 6 passing, matching code/response hashes, idle session, and persistent files**. These are not relabelled as a new CI run for this patch or as Hosted IQ evidence.

**Subsequent rename recovery:** after the user's approval, only the repository name in the existing
NC federation subject was changed to the name used at that time (current repository name: `microsoft-foundry-labs-v1.3`). Before/after comparisons preserved
the managed identity, credential ID, issuer, audience, and both existing roles; the immutable repository
ID and main-only protection also remain unchanged. On new commit
**`cc816de2b71ae78730b485024a082eb69e186711`**, both the
[authentication-only OIDC run](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3/actions/runs/36404614530) and
[repository checks](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3/actions/runs/36404559521) passed.
The actual emitted issuer, new subject, audience, and authenticated client/tenant/subscription were matched.
**There were zero new deployments, role grants, or model requests; `deployment_verified: false`.**
Authentication recovery is not relabelled as a fresh Hosted release or quality evaluation.
Follow [chapter 14's deployment-free procedure](14-additional-permissions.md).

The local working copy passed Python 3.13 **288 core/149 SDK tests**, Python 3.14 **288 core tests**,
Ruff, compilation, dependency checks, and bilingual documentation checks. The first Python 3.14 attempt
failed because `mcp` was missing; installing the existing pinned `requirements.txt` resolved the missing
dependencies and the complete core rerun passed. GitHub checks on `cc816de`, which publishes only the
authentication workflow/helper/tests, passed **284 core/146 SDK tests**. Earlier uncommitted
Optimizer/media/documentation changes are not in that commit; these two validation scopes are distinct.

**Authenticated Playwright Headless recapture and both language editions are complete.** The user's newly authenticated temporary profile was reopened headlessly for eight read-only NC portal scenes. Earlier recorder `page.url()` and account-chooser failures were preserved separately; only completed captures were used. No separate authentication-transfer file was created, and the temporary login profile was removed afterward.

The current **NC portal/CLI edition is 3:52 per language, with 28 scenes**. It distinguishes the original Optimizer failure, successful fix, six-row baseline/candidate results, and remaining Prohibited Actions inconsistency. Login screens, account emails, and subscription identifiers are excluded. Both files were checked for **5,800 frames, 25 fps, H.264, faststart, full decoding, and 30 subtitle cues**. Recording did not invoke models, promote candidates, or change permissions.

New originals are private at `dist/recordings/portal/nc-headless-final-20260928/`; the earlier CLI videos/provenance are archived under `.selfstudy/archives/nc-cli-before-headless-20260928/`. [Video provenance](../assets/videos/foundry-v1.3-summary-provenance.json) records output hashes and original intervals. The Prohibited Actions service-side contradiction remains **unresolved, separately from the completed media work**.

The earlier 278 core/146 SDK tests, Ruff, compilation, and dependency checks remain historical results. The preceding Optimizer/media patch passed **45 related policy/Optimizer/SDK tests** and Ruff. These do not prove model improvement or resolve Prohibited Actions. New assets remain retained; Search Basic, stored files/volumes, and logs can still incur costs. Insights' approximately USD 2.01 is that analysis's **estimate**, not this Optimizer job or total billed cost.

## Archived Sweden R2 record

The following describes the period **before that group was deleted**. “Retained” and “final” refer to that historical scope, not current NC state. The [original R2 report](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3/blob/0a8ab50/docs/en/validation-report.md) and private originals remain available.

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

All 278 core tests, 124 SDK tests, Ruff, and bilingual document/command/link checks passed. [GitHub checks](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3/actions/runs/36362144665) and the [approved OIDC release](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3/actions/runs/36362528860) succeeded on code commit `5267633`.

Downloaded artifacts verified **six actual English responses from CI agent v2, 6/6 business checks, the current runtime code hash, an idle session, and no persistent-file deletion**. This CI local-retrieval smoke path is separate from the IQ Hosted verification above.
