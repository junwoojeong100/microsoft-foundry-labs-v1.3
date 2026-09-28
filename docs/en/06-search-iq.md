# 06. Search, Foundry IQ, and Hybrid

**English** | [한국어](../06-search-iq.md) · [Course home](../../README.md)

**Outcome:** Create and configure Search yourself, then retrieve the same documents using keyword, IQ, and Hybrid retrieval.

**Prerequisites:** Owner access and Foundry configuration from 00. You create Search and any required models here. **Search Basic—and any explicitly selected Standard tier—incurs ongoing service charges even without requests.**

**Order:** prepare Search, permissions, and billing in 1–3, then verify keyword (4), IQ (5), Hybrid (6), and IQ Chat (7) separately. **Restore the original index after section 6.** These are not interchangeable features or a single model.

## 1. Create a Search service

1. In the Azure portal, open **Create a resource → Azure AI Search**.
2. Choose the workshop subscription, **dedicated lab group**, and a unique service name.
3. Verify both **Semantic ranker and Agentic retrieval** in the [regional support table](https://learn.microsoft.com/azure/search/search-region-support).
4. Start with **Basic**, compute type **Default**, **one replica and one partition**. A higher SKU or Confidential compute is not the default for this lab.
5. Review pricing, create, and wait for completion.
6. Record the **URL** from Overview, the **full resource ID** from JSON View, and the actual SKU, replica count, partition count, and ongoing price.

<a id="if-regional-capacity-or-quota-blocks-creation"></a>

<details>
<summary>Only if creation is blocked: regional capacity and subscription quota</summary>

### Current setup and historical capacity errors

For `ResourcesForSkuUnavailable`, inspect capacity; for `ServiceQuotaExceeded`, inspect subscription quota. Preserve the actual error and retry only in a bounded way after the relevant condition changes. More Owner/RBAC roles, repeated Create clicks, arbitrary group deletion, or automatic tier escalation are not solutions.

Record Search-dependent work as blocked until Search is ready. File Search and local retrieval are different features. See [independent steps you can still take](checkpoints.md#if-a-stage-is-blocked), the explicitly selected [local Hosted matrix](12-improvement.md#10-explicit-local-retrieval-matrix), and [historical regional validation](validation-report.md).

</details>

## 2. Configure token authentication and managed identity

Under Search **Settings → Keys → API access control**, select **Role-based access control** and disable key authentication. Apply this only to your lab service; do not copy an API key.

Select **Identity → System assigned → On → Save**. This identity is used later when Search calls the IQ Chat model.

```bash
python scripts/selfstudy.py resource --kind search --id "YOUR-SEARCH-ARM-ID" --endpoint "YOUR-SEARCH-URL"
python scripts/selfstudy.py roles --user-object-id "YOUR-USER-OBJECT-ID"
```

Registration reads Azure metadata and saves local configuration; it does not assign roles. Compare **your user → Search Index Data Contributor on this Search service** with IAM and add it only if missing. Existing Owner access covers management operations.

The project's Toolbox roles are used in 10; the Search identity's model role is used below for IQ Chat. Do not blindly execute every line of the role plan.

## 3. Review per-feature billing

Under **Settings → Premium features**, inspect Semantic ranker and Knowledge retrieval separately. You may start with their offered **Free feature plans**, but **that does not make the Search service free**, whether Basic or an explicitly selected Standard tier.

If the included allowance is exhausted, stop and review the cost before selecting a Standard feature plan. A Standard feature plan is separate from a Standard S1/S2 service SKU. Never automatically upgrade or change retrieval providers to hide an error.

## 4. Compare local and Search retrieval

Use one language throughout this workspace. An existing Korean Search ownership ledger cannot be reused for the English corpus. Preserve earlier resources and results; use a fresh lab copy with distinct owned names for a separate language experiment.

```bash
python scripts/workshop.py --language en retrieve --provider local --question "What are the domestic lodging limit and advance-approval conditions for September 2026?" --output outputs/learner-notes-en/06-local.json
python scripts/workshop.py --language en seed-search --confirm-create
python scripts/workshop.py --language en retrieve --provider search --question "What are the domestic lodging limit and advance-approval conditions for September 2026?" --output outputs/learner-notes-en/06-search.json
```

`seed-search` creates **your prefix's index and synthetic documents**, not a new service. Record its actual name as **“06 original index”** in your workbook and retain `outputs/azure-objects.json`. Restore this name after section 6.

Check `provider: azure-ai-search-keyword`, the actual index/endpoint, and source IDs and text. Local retrieval is neither semantic search nor an Azure service call.

## 5. GA Foundry IQ

For this six-document synthetic corpus, explicitly set the **reranker retrieval threshold to 0**. The default filter can discard a lower-ranked document such as `SCOPE-01`, which is needed for an out-of-scope question. This changes retrieval, not the evaluator's passing threshold of 4. Returned sources and citations are still checked.

```bash
python scripts/selfstudy.py set WORKSHOP_IQ_RERANKER_THRESHOLD 0
python scripts/workshop.py --language en seed-search --iq --confirm-create
python scripts/workshop.py --language en retrieve --provider iq --question "What are the domestic lodging limit and advance-approval conditions for September 2026?" --output outputs/learner-notes-en/06-iq.json
python scripts/workshop.py --language en answer --prompt v2 --retrieval iq --question "What are the domestic lodging limit and advance-approval conditions for September 2026?" --output outputs/learner-notes-en/06-iq-answer.json
```

Inspect `provider: foundry-iq`, the knowledge base, `api_version: 2026-04-01`, and actual documents/references/activity. The final command performs **new retrieval and inference**; it does not read the previous result file.

This GA retrieval path is not the same as the model-based planning and synthesis experiment below.

## 6. Prepare embeddings and Hybrid retrieval

1. Find **text-embedding-3-large** in the same Foundry catalog.
2. Check regional support/quota and deploy it as `workshop-embedding`.
3. Confirm the actual dimensions. This model's default is **3072**; another model or configuration requires its actual dimension count.
4. Find the same Foundry account's **Azure OpenAI root endpoint**. This differs from the project endpoint.

```bash
python scripts/selfstudy.py model --role embedding
python scripts/selfstudy.py set WORKSHOP_EMBEDDING_DIMENSIONS 3072
python scripts/selfstudy.py set WORKSHOP_EMBEDDING_API account
python scripts/selfstudy.py set AZURE_OPENAI_ENDPOINT "YOUR-SAME-ACCOUNT-OPENAI-ROOT-URL"
```

Keep the original index and explicitly name a **new hybrid index**. Replace the illustrative prefix with yours:

```bash
python scripts/selfstudy.py set AZURE_SEARCH_INDEX_NAME "lab-yourname-nc-0928-policies-hybrid-en"
python scripts/workshop.py --language en seed-search --hybrid --confirm-create --confirm-cost
python scripts/workshop.py --language en retrieve --provider hybrid --question "What are the domestic lodging limit and advance-approval conditions for September 2026?" --output outputs/learner-notes-en/06-hybrid.json
python scripts/workshop.py --language en answer --prompt v2 --retrieval hybrid --question "What are the domestic lodging limit and advance-approval conditions for September 2026?" --output outputs/learner-notes-en/06-hybrid-answer.json
```

Verify real embedding calls and dimensions, text-plus-vector retrieval, and returned evidence. Do not insert zero vectors or rename keyword search as Hybrid.

**Restore the original index before continuing.** Use the exact name printed in section 4:

```bash
python scripts/selfstudy.py set AZURE_SEARCH_INDEX_NAME "YOUR-ORIGINAL-INDEX-FROM-SECTION-4"
```

This configuration change does not delete the hybrid index. Both remain in the ownership ledger for the final lifecycle review.

## 7. Model-based IQ Chat

This experiment uses **`gpt-5.6-luna` / `2026-07-09`** and Search's system-assigned identity.

Keep **GPT-6 Sol** as the configured answer model. **GPT-5.6 Luna** here is Search's separate planning/synthesis model, not optional comparison model GPT-6 Luna. Keep these [model roles](model-selection.md) distinct.

1. Check availability and quota for the required model/version.
2. Deploy it in the same Foundry account with deployment name **`gpt-5.6-luna`**. Do not change the answer deployment.
3. In the Foundry account's IAM, assign **Cognitive Services User to the Search managed identity**. Do not confuse it with your user or project identity.
4. Verify the recorded OpenAI root endpoint and Search feature plans.

```bash
python scripts/selfstudy.py model --role iq
python scripts/workshop.py --language en iq-chat check
python scripts/workshop.py --language en iq-chat setup --confirm-create
python scripts/workshop.py --language en iq-chat ask --label iq-chat-first-en --confirm-cost
```

Inspect `model_planning_verified`, `model_synthesis_verified`, the actual **`modelQueryPlanning` / `modelAnswerSynthesis` activities and `gpt-5.6-luna` model records**, and source evidence. If the required model cannot be deployed, mark this preset **blocked**. Do not disguise another model under its name or submit GA retrieval as IQ Chat success.

## Completion and retention

Preserve results and ownership for the original index/IQ base and the hybrid index. Search is reused by Toolbox/OpenAPI in 10 and later Hosted evaluation; do not delete it yet.

**Next → [07. Business and Foundry evaluation](07-evaluation.md)**
