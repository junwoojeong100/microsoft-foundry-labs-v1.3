# 06. Search, Foundry IQ, and Hybrid

**English** | [한국어](../06-search-iq.md) · [Course home](../../README.md)

**Outcome:** Create and configure Search yourself, then retrieve the same documents using keyword, IQ, and Hybrid retrieval.

**Prerequisites:** Owner access and Foundry configuration from 00. You create Search and any required models here. **Search Basic—and any explicitly selected Standard tier—incurs ongoing service charges even without requests.**

## 1. Create a Search service

1. In the Azure portal, open **Create a resource → Azure AI Search**.
2. Choose the workshop subscription, **dedicated lab group**, and a unique service name.
3. Verify both **Semantic ranker and Agentic retrieval** in the [regional support table](https://learn.microsoft.com/azure/search/search-region-support).
4. Start with **Basic**, compute type **Default**, and a small replica/partition configuration. A higher SKU or Confidential compute is not the default for this lab.
5. Review pricing, create, and wait for completion.
6. Record the **URL** from Overview, the **full resource ID** from JSON View, and the actual SKU, replica count, partition count, and ongoing price.

### If regional capacity or quota blocks creation

**Observed on 2026-09-27 in Sweden Central:** Both **Basic and Standard S1** creation returned `ResourcesForSkuUnavailable`. This is **regional service capacity**, not a missing Owner or RBAC role. Repeating Create or assigning more permissions does not resolve it.

The one explicitly chosen **Standard S2 attempt, with one replica and one partition**, also failed: **`ServiceQuotaExceeded`, `0 out of 0`**. This is a separate blocker: the subscription's service quota for that SKU is zero. **No Search service was created in this fixed Sweden Central run.**

**Keep Sweden Central fixed and stop tier escalation.** More Owner/RBAC permissions do not solve either blocker. Use the official Search quota-increase process where needed, and resume only when the required regional capacity or SKU quota is available. Do not keep repeating Create, silently upgrade again, or switch regions.

Record each attempted SKU and its outcome. Before any later approved higher-tier deployment, record the **actual SKU, replica/partition configuration, and higher ongoing service cost**; do not keep describing it as Basic. Free retrieval-feature allowances do not remove a provisioned service's charge.

Preserve original errors and any resource/ownership IDs. Mark this chapter's **Azure Search, IQ, and Hybrid**, and [10's Search-based Toolbox/OpenAPI](10-toolbox-skills.md), **BLOCKED**. File Search and local retrieval are separate results, not substitutes for Azure Search completion. Continue independent exercises whose prerequisites are available.

An explicitly selected, separately named **[local-retrieval Hosted matrix](12-improvement.md#10-explicit-local-retrieval-matrix)** can be prepared without Search. It is not IQ validation: actual deployment, smoke, native evaluation, traces, and acceptance must still pass for that precise local profile. Keep its results distinct from IQ and leave the Search-dependent exercises blocked. In retention mode, continue skipping all deletion; do not delete retained resources to work around these failures.

## 2. Configure token authentication and managed identity

Under Search **Settings → Keys → API access control**, select **Role-based access control**, or **Both** during a transition. Change only your new personal service; do not copy an API key.

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

`seed-search` creates **your prefix's index and synthetic documents**, not a new service. Keep the actual index name and `outputs/azure-objects.json`.

Check `provider: azure-ai-search-keyword`, the actual index/endpoint, and source IDs and text. Local retrieval is neither semantic search nor an Azure service call.

## 5. GA Foundry IQ

```bash
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
python scripts/selfstudy.py set AZURE_SEARCH_INDEX_NAME "lab-yourname-0927-policies-hybrid-en"
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

Keep your configured answer model—Luna initially, or the explicitly selected Sol compatibility deployment. The model here is **a separate model used by Search for planning/synthesis**, governed by a [separate support list](model-selection.md).

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

Inspect `model_planning_verified`, `model_synthesis_verified`, actual planning/synthesis activity, and source evidence. If the required model cannot be deployed, mark this preset **blocked**. Do not disguise another model under its name or submit GA retrieval as IQ Chat success.

## Completion and retention

Preserve results and ownership for the original index/IQ base and the hybrid index. Search is reused by Toolbox/OpenAPI in 10 and later Hosted evaluation; do not delete it yet.

**Next → [07. Business and Foundry evaluation](07-evaluation.md)**
