# 06. Search, Foundry IQ, and Hybrid

**English** | [한국어](../06-search-iq.md) · [Course home](../../README.md#curriculum) · [Help](checkpoints.md)

**Outcome:** Create and configure Search yourself, then retrieve the same documents using keyword, IQ, and Hybrid retrieval.

**Prerequisites:** Owner access and Foundry configuration from 00. You create Search and any required models here. **Search Basic—and any explicitly selected Standard tier—incurs ongoing service charges even without requests.**

**Where you work:** Azure/Foundry portals for services and models; terminal for configuration and retrieval.

> **Restore configuration:** whether Hybrid succeeds or fails, **return to the original index at the end of section 6**. Later exercises use that index.

<a id="chapter-map"></a>

**Chapter map**

| Step | Result to check |
|---|---|
| [1. Create Search](#1-create-a-search-service) | Actual service, region, and Basic costs |
| [2. Authentication and identity](#2-configure-token-authentication-and-managed-identity) | Token authentication and user data access |
| [3. Feature billing](#3-review-per-feature-billing) | Service charges versus feature plans |
| [4. Local and keyword search](#4-compare-local-and-search-retrieval) | Original index name and retrieved sources |
| [5. GA IQ](#5-ga-foundry-iq) | Actual documents, references, and activity |
| [6. Hybrid](#6-prepare-embeddings-and-hybrid-retrieval) | Real embeddings/retrieval; original index restored |
| [7. IQ Chat](#7-model-based-iq-chat) | Separate model planning and synthesis |
| [Completion check](#completion-check) | Results and ownership for each retrieval path |

## 1. Create a Search service

1. In the Azure portal, open **Create a resource → Azure AI Search**.
2. Choose the workshop subscription, **dedicated lab group**, and a unique service name.
3. Select **North Central US** for the service and verify both **Semantic ranker and Agentic retrieval** in the [regional support table](https://learn.microsoft.com/azure/search/search-region-support). A resource group's location does not automatically determine the service's region.
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
```

**Read the required-role plan**

```bash
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
```

**Prepare the search index and documents**

```bash
python scripts/workshop.py --language en seed-search --confirm-create
```

**Inspect the retrieved source documents**

```bash
python scripts/workshop.py --language en retrieve --provider search --question "What are the domestic lodging limit and advance-approval conditions for September 2026?" --output outputs/learner-notes-en/06-search.json
```

`seed-search` creates **your prefix's index and synthetic documents**, not a new service. Read the original index name from **`configuration.index`** in the saved `outputs/learner-notes-en/06-search.json` when needed. Keep `outputs/azure-objects.json` too, and restore that original name after section 6.

**Check:** `provider: azure-ai-search-keyword`, the actual index/endpoint, and source IDs and text. Local retrieval is neither semantic search nor an Azure service call.

## 5. GA Foundry IQ

For this six-document synthetic corpus, explicitly set the **reranker retrieval threshold to 0**. The default filter can discard a lower-ranked document such as `SCOPE-01`, which is needed for an out-of-scope question. This changes retrieval, not the evaluator's passing threshold of 4. Returned sources and citations are still checked.

```bash
python scripts/selfstudy.py set WORKSHOP_IQ_RERANKER_THRESHOLD 0
```

**Prepare the search index and documents**

```bash
python scripts/workshop.py --language en seed-search --iq --confirm-create
```

**Inspect the retrieved source documents**

```bash
python scripts/workshop.py --language en retrieve --provider iq --question "What are the domestic lodging limit and advance-approval conditions for September 2026?" --output outputs/learner-notes-en/06-iq.json
```

**Ask the model using retrieved evidence**

```bash
python scripts/workshop.py --language en answer --prompt v2 --retrieval iq --question "What are the domestic lodging limit and advance-approval conditions for September 2026?" --output outputs/learner-notes-en/06-iq-answer.json
```

**Check:** `provider: foundry-iq`, the knowledge base, `api_version: 2026-04-01`, and actual documents/references/activity. The final command performs **new retrieval and inference**; it does not read the previous result file.

This GA retrieval path is not the same as the model-based planning and synthesis experiment below.

## 6. Prepare embeddings and Hybrid retrieval

### Register the model and dimensions

1. Find **text-embedding-3-large** in the same Foundry catalog.
2. Check regional support/quota and deploy it as `workshop-embedding`.
3. Confirm the actual dimensions. This model's default is **3072**; another model or configuration requires its actual dimension count.
4. Find the same Foundry account's **Azure OpenAI root endpoint**. This differs from the project endpoint.

```bash
python scripts/selfstudy.py model --role embedding
```

**Set the actual embedding dimensions**

```bash
python scripts/selfstudy.py set WORKSHOP_EMBEDDING_DIMENSIONS 3072
```

**Set the embedding API path**

```bash
python scripts/selfstudy.py set WORKSHOP_EMBEDDING_API account
```

**Register the OpenAI service-root endpoint**

```bash
python scripts/selfstudy.py set AZURE_OPENAI_ENDPOINT "YOUR-SAME-ACCOUNT-OPENAI-ROOT-URL"
```

### Retrieve from a separate index

Keep the original index and explicitly name a **new hybrid index**. Replace the illustrative prefix with yours:

```bash
python scripts/selfstudy.py set AZURE_SEARCH_INDEX_NAME "lab-yourname-nc-0928-policies-hybrid-en"
```

**Prepare the search index and documents**

```bash
python scripts/workshop.py --language en seed-search --hybrid --confirm-create --confirm-cost
```

**Inspect the retrieved source documents**

```bash
python scripts/workshop.py --language en retrieve --provider hybrid --question "What are the domestic lodging limit and advance-approval conditions for September 2026?" --output outputs/learner-notes-en/06-hybrid.json
```

**Ask the model using retrieved evidence**

```bash
python scripts/workshop.py --language en answer --prompt v2 --retrieval hybrid --question "What are the domestic lodging limit and advance-approval conditions for September 2026?" --output outputs/learner-notes-en/06-hybrid-answer.json
```

**Check:** real embedding calls and dimensions, text-plus-vector retrieval, and returned evidence. Do not insert zero vectors or rename keyword search as Hybrid.

### Always restore the original index

**Restore the original index whenever you finish or stop the Hybrid experiment, even after failure.** Open section 4's `outputs/learner-notes-en/06-search.json` and copy the **`index` value inside `configuration`** into the quotes below. Do not use the index from the new hybrid result:

```bash
python scripts/selfstudy.py set AZURE_SEARCH_INDEX_NAME "INDEX-VALUE-FROM-06-SEARCH-JSON"
```

This configuration change does not delete the hybrid index. Both remain in the ownership ledger for the final lifecycle review.

Before continuing, check that `sdk_settings.AZURE_SEARCH_INDEX_NAME` in `python scripts/selfstudy.py status` contains the original name. Preserve an unresolved Hybrid failure as incomplete.

## 7. Model-based IQ Chat

This experiment uses **`gpt-5.6-luna` / `2026-07-09`** and Search's system-assigned identity.

Keep **GPT-6 Sol** as the configured answer model. **GPT-5.6 Luna** here is Search's separate planning/synthesis model, not optional comparison model GPT-6 Luna. Keep these [model roles](model-selection.md) distinct.

1. Check availability and quota for the required model/version.
2. Deploy it in the same Foundry account with deployment name **`gpt-5.6-luna`**. Do not change the answer deployment.
3. In the Foundry account's IAM, assign **Cognitive Services User to the Search managed identity**. Do not confuse it with your user or project identity.
4. Verify the recorded OpenAI root endpoint and Search feature plans.

```bash
python scripts/selfstudy.py model --role iq
```

**Check IQ Chat prerequisites**

```bash
python scripts/workshop.py --language en iq-chat check
```

**Create IQ Chat assets**

```bash
python scripts/workshop.py --language en iq-chat setup --confirm-create
```

**Send an actual IQ Chat request · `iq-chat-first-en`**

```bash
python scripts/workshop.py --language en iq-chat ask --label iq-chat-first-en --confirm-cost
```

Inspect `model_planning_verified`, `model_synthesis_verified`, the actual **`modelQueryPlanning` / `modelAnswerSynthesis` activities and `gpt-5.6-luna` model records**, and source evidence. If the required model cannot be deployed, mark this preset **blocked**. Do not disguise another model under its name or submit GA retrieval as IQ Chat success.

<a id="completion-and-retention"></a>

## Completion check

- [ ] I checked actual results or blocked status for keyword, IQ, Hybrid, and IQ Chat separately.
- [ ] `sdk_settings.AZURE_SEARCH_INDEX_NAME` matches section 4's original index.
- [ ] I verified ownership and ongoing costs for the indexes, bases, and models I created.

Preserve results and ownership for the original index/IQ base and the hybrid index. Search is reused by Toolbox/OpenAPI in 10 and later Hosted evaluation; do not delete it yet.

---

[← 05. Workflows](05-workflows.md) · [Course home](../../README.md#curriculum) · [07. Evaluation →](07-evaluation.md) · [Chapter map ↑](#chapter-map)
