# 03. Prompt Agents and File Search

**English** | [한국어](../03-knowledge.md) · [Course home](../../README.md)

**Outcome:** Create an agent with stored instructions and an exact version, then separately verify real file retrieval and citations.

**Prerequisites:** Configuration and a working project-response deployment from 00–02. Use **only the six synthetic Hanbit Technology documents** below.

**Verified NC scope:** beyond Prompt Agent creation/invocation, **both Korean and English File Search indexed six files and returned actual file citations**. Korean current-limit KRW 150000, historical KRW 120000, and unknown-Tokyo responses were recorded. Inline agents and File Search remain distinct executions; preserve each language/version/file-ID record.

## 1. Read the original evidence first

Open `data/knowledge/en/policies.json`, the canonical English policy bundle.

| Document | Key fact |
|---|---|
| TRAVEL-2025 | Through 2026-06-30: lodging **KRW 120,000 per person per night** |
| TRAVEL-2026 | From 2026-07-01: lodging **KRW 150,000 per person per night** |
| APPROVAL-01 | Over-limit spending requires **team-lead approval before booking** |
| RECEIPT-01 | Receipts are required; ask the finance contact about a lost receipt |
| MEAL-01 | Current meals: **KRW 30,000 per person per day**, separate from lodging |
| SCOPE-01 | No international-travel or airfare policy; ask for a missing travel date |

The data explicitly describes **what is unknown**, not just what is available. These are not real company policies.

The bundled `data/policies/*.txt` files are Korean. With `--language en`, the SDK generates English upload text from `data/knowledge/en/policies.json` and preserves filenames such as `TRAVEL-2026.txt`. There is no separate prebuilt `data/policies/en/` directory to upload manually.

## 2. Create a stored Prompt Agent

The runner derives an owned, language-specific name from your prefix and records its actual version:

```bash
python scripts/workshop.py --language en prompt-agent create --confirm-create --output outputs/learner-notes-en/03-agent-created.json
```

This creates a **managed Prompt Agent** with starter instructions and the synthetic policies. It is **inline grounding**: documents are included in instructions/context. It does not complete File Search.

Invoke the exact version just recorded under `outputs/agents/`, not an arbitrarily selected latest version:

```bash
python scripts/workshop.py --language en prompt-agent invoke --question "A hotel for my domestic business trip in September 2026 costs KRW 170000 per night. May I book it?" --output outputs/learner-notes-en/03-agent-answer.json
```

In Foundry **Build → Agents**, verify the same name, version, model, and instructions. Check the date, KRW 150,000 limit, approval required before booking when over the limit, and source IDs.

## 3. Create a real File Search agent

Use the **bundled SDK commands** rather than depending on the portal's upload-button location. Use the actual Sol deployment whose project call passed in 01; an independent name is generated for this agent.

```bash
python scripts/workshop.py --language en file-search create --confirm-create
```

This uploads six synthetic documents, verifies vector-store indexing, creates a File Search Prompt Agent, and records its exact version and owned IDs. It does not paste the entire policy corpus into instructions.

Check `indexed_files: 6`, the actual `agent_name`, `agent_version`, and `vector_store_id`. Ownership is recorded in `outputs/file-search/<agent-name>/ownership.json`. IDs already created are preserved on partial failure; do not blindly upload duplicate files.

By default, the vector store **expires seven days after its last activity**. This is a retention/cost setting, not a course deadline. After expiry or a model change, inspect existing resources and use a new owned name.

**For a retained environment, use this alternative at creation time.** `--retain` omits automatic vector-store expiry. Verify `retention: retain` in the ownership record and use the same option when resuming. Storage charges may continue.

```bash
python scripts/workshop.py --language en file-search create --confirm-create --retain
```

Catalog support and successful execution on your particular deployment are different. Resolve SDK capability or permission errors rather than **silently substituting inline answers or another model**.

Reasoning is stored in the **agent definition** at creation. An `agent_reference` request must inherit it: sending another `reasoning` override produces `Not allowed when agent is specified`. The runner inherits the immutable version's reasoning and sends only the output cap on the request.

Environments using their own Storage may require additional access such as **Storage Blob Data Contributor** for the actual user/service identity. Check Basic/Standard setup and the real store in the [official File Search documentation](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/file-search), and scope assignments **only to your storage**.

## 4. Distinguish three questions

Send each question independently to the exact saved agent version:

```bash
python scripts/workshop.py --language en file-search ask --question "What is the domestic business-trip lodging limit for September 2026, and what is the source?" --label current-en
python scripts/workshop.py --language en file-search ask --question "What is the domestic business-trip lodging limit for May 2026, and what is the source?" --label previous-en
python scripts/workshop.py --language en file-search ask --question "What is the hotel limit for a business trip to Tokyo?" --label missing-en
```

Expected outcomes are **KRW 150,000 / KRW 120,000 / insufficient evidence**. Verify that current and historical effective dates are not reversed.

Check real `file_search_calls`, `file_citations` pointing to your uploaded files, and `file_search_verified: true`. The runner does not count an answer as verified without a search call and citations to owned files.

Compare raw responses in `result_directory` with the English policy source and uploaded text. In Foundry Agents, inspect the same name/version and File Search configuration. **Writing a document ID in an answer is not the same as returning an actual file citation.**

## 5. Keep the evidence

For both the inline and File Search agents, record names, versions, response IDs, file/store IDs, and source comparisons in your workbook. File storage and retrieval may incur charges beyond model tokens.

Do not overwrite labels. Use a new label such as `current-en-2` for a necessary retry, preserving the original failure. Review ownership in chapter 15 before choosing deletion.

**If blocked:** Distinguish upload completion from indexing completion; do not bypass authentication with an API key. Keep missing citations and wrong-date retrieval as actual failures.

If indexing is still in progress after a timeout, resume with the same creation command and retention option. For permanent failure or expiry, resolve the cause, inspect the inventory in 15, and create with a **new `--name`**. Retention mode also keeps earlier assets. If a remote agent exists without a recorded version, inspect the actual portal asset rather than guessing or creating another version.

**Next → [04. MAF, functions, MCP, and Code Interpreter](04-tools.md)**
