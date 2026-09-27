# 10. Toolbox, Tool Search, Skills, and OpenAPI

**English** | [한국어](../10-toolbox-skills.md) · [Course home](../../README.md)

**Outcome:** Create a keyless connection to your own Search service and actually use versioned tools and procedures.

**Prerequisites:** The original Search index and successful retrieval from 06, the project managed identity from 00, and the azd Foundry extension from 08. No preprovisioned service is needed.

**If Search is blocked in 06, the Search-based Toolbox, OpenAPI, and Hosted Toolbox steps here are blocked too.** Preparing local Skill files alone does not complete them.

## 1. Grant project-to-Search access

Check that the **original index from 06** is selected:

```bash
python scripts/selfstudy.py status
python scripts/selfstudy.py roles --user-object-id "YOUR-USER-OBJECT-ID"
```

The caller for this Toolbox is the **project managed identity**. Grant it **Search Index Data Reader and Search Service Contributor on your dedicated Search service**.

Search Service Contributor is not read-only. Here it provides the schema access needed by the tool; scope it **only to the dedicated lab Search service**. Do not confuse the project identity with the account identity used by another connection type.

## 2. Create a keyless project connection

Use the actual Search/project endpoints and your unique connection name:

```bash
azd ai connection create "YOUR-PREFIX-search-en" --kind cognitive-search --target "YOUR-SEARCH-ENDPOINT" --auth-type project-managed-identity --audience https://search.azure.com --project-endpoint "YOUR-PROJECT-ENDPOINT"
python scripts/selfstudy.py set TOOLBOX_SEARCH_CONNECTION_NAME "YOUR-PREFIX-search-en"
```

In Foundry **Project details → Connected resources**, read back the connection, target, and authentication type. Do not use `--force`, API keys, or another project's connection.

## 3. Start with a standard Toolbox

```bash
python scripts/workshop.py --language en toolbox plan
python scripts/workshop.py --language en toolbox create --confirm-create
```

Record the actual `selected_version` and substitute it below:

```bash
python scripts/workshop.py --language en toolbox probe --version "ACTUAL-VERSION" --label toolbox-list-en
python scripts/workshop.py --language en toolbox query --version "ACTUAL-VERSION" --label toolbox-query-en --confirm-cost
python scripts/workshop.py --language en toolbox ask --version "ACTUAL-VERSION" --label toolbox-answer-en --confirm-cost
```

| Step | What it verifies |
|---|---|
| probe | Authentication, MCP connection, and tool listing |
| query | Real retrieval from Toolbox to Search |
| ask | A model answer using the actual tool result |

A successful tool listing does not prove downstream Search permissions. For a query 403, preserve the error, identify the actual calling identity, and correct only that identity's Search roles.

## 4. Tool Search and pinned tools

Check feature availability/Preview status and CLI support:

```bash
azd ai skill create --help
azd ai skill download --help
python scripts/workshop.py --language en toolbox plan --discovery --pin-policy
```

Once support is confirmed:

```bash
python scripts/workshop.py --language en toolbox add-version --discovery --pin-policy --confirm-create
python scripts/workshop.py --language en toolbox probe --version "NEW-SELECTED-VERSION" --label discovery-list-en
```

Verify `tool_search`, `call_tool`, and `policy_search` in the actual list. Tool Search is **tool discovery**; File Search and Search retrieve **policy information**.

## 5. Prepare, upload, and read back a Skill

```bash
python scripts/workshop.py --language en prepare-extensions --label extensions-en
```

If already prepared for this prefix/language, inspect and reuse the existing manifest. Read `policy-review/SKILL.md`, `manifest.json`, and source hashes under `outputs/extensions-en/`. **Upload only `policy-review/`**, because its parent also contains evaluation references.

The generated `skill_name` is `<prefix>-policy-review-en`. Use the exact value from the manifest:

```bash
azd ai skill create "SKILL-NAME-FROM-MANIFEST" --file outputs/extensions-en/policy-review --project-endpoint "YOUR-PROJECT-ENDPOINT"
azd ai skill show "SKILL-NAME-FROM-MANIFEST" --project-endpoint "YOUR-PROJECT-ENDPOINT" --output json
```

Specify the returned `default_version` and download into a **new readback folder that does not already exist**:

```bash
azd ai skill download "SKILL-NAME-FROM-MANIFEST" --version "ACTUAL-SKILL-VERSION" --output-dir .selfstudy/skill-readback-en --project-endpoint "YOUR-PROJECT-ENDPOINT"
python scripts/selfstudy.py compare-files outputs/extensions-en/policy-review/SKILL.md .selfstudy/skill-readback-en/SKILL.md
```

If bytes differ, investigate. Do not edit the downloaded file to force a match.

## 6. Attach the exact Skill version

```bash
python scripts/workshop.py --language en toolbox plan --discovery --pin-policy --skill-version "ACTUAL-SKILL-VERSION"
python scripts/workshop.py --language en toolbox add-version --discovery --pin-policy --skill-version "ACTUAL-SKILL-VERSION" --confirm-create
python scripts/workshop.py --language en toolbox probe --version "NEW-TOOLBOX-VERSION" --label skilled-list-en
python scripts/workshop.py --language en toolbox ask --version "NEW-TOOLBOX-VERSION" --label skilled-answer-en --with-skill --confirm-cost
```

Check `skill_load_verified`, actual calls, and policy results. Registration alone does not prove the Skill was read. This example does not execute arbitrary Skill scripts.

## 7. Use OpenAPI against the same Search service

Instead of creating a business API, use the read API of your own synthetic Search index. First review the plan, actual caller, and target:

```bash
python scripts/workshop.py --language en openapi plan
```

This path uses the **Foundry account's system-assigned identity**, not the Toolbox's project identity. Enable the account identity, then reread its actual ID using the same `selfstudy.py configure` command as 00/01, including your explicit Sol deployment/`--expected-model` if selected. Grant this identity **Search Index Data Reader on the relevant Search service**. `selfstudy.py roles` distinguishes these identities.

```bash
python scripts/workshop.py --language en openapi invoke --label openapi-policy-en --confirm-cost
```

Verify the actual OpenAPI tool call and returned source text. Explain how `lookup_policy`, MCP, OpenAPI, and Code Interpreter are different execution mechanisms.

## 8. Host the same Toolbox

Start with a verified **standard Toolbox version**. If selecting a Skill-enabled version, add `--with-skill` to both packaging and serving; keep that choice consistent.

```bash
python scripts/workshop.py --script package-toolbox --language en --version "VERIFIED-TOOLBOX-VERSION"
python scripts/selfstudy.py prepare-hosted --language en --kind toolbox --package "ACTUAL-RETURNED-PACKAGE-PATH" --name toolbox-hosted-en
```

As in 08, inspect the manifest and actual project, and use the exact printed service/folder. `prepare-hosted` defaults to Korean; keep its explicit `--language en` matched to the package.

Local terminal A:

```bash
python scripts/workshop.py --language en toolbox serve --version "VERIFIED-TOOLBOX-VERSION"
```

Terminal B:

```bash
curl --fail http://127.0.0.1:8088/readiness
azd ai agent invoke --cwd "YOUR-TOOLBOX-HOSTED-ABSOLUTE-PATH" --local --port 8088 --new-session --new-conversation --timeout 210 "What advance approval is required for a KRW 170000 hotel on a domestic business trip in September 2026?"
```

Verify actual tools, model response, and sources, then stop A with `Ctrl+C`. Decide separately whether to deploy remotely:

```bash
azd deploy "YOUR-PREFIX-toolbox-hosted-en" --cwd "YOUR-TOOLBOX-HOSTED-ABSOLUTE-PATH"
azd ai agent show "YOUR-PREFIX-toolbox-hosted-en" --cwd "YOUR-TOOLBOX-HOSTED-ABSOLUTE-PATH" --output json
```

Verify/grant the actual new runtime identity's necessary Foundry User access as in 08. Check that the active version and project match your intended target.

### Capture one English invocation for offline verification

Preserve raw response bytes so the verifier can examine the same invocation. `selfstudy.py capture --language en` selects the English synthetic hotel question. The default is Korean, so keep the flag explicit. The helper checks the project and exact active service/version, preserves stdout/stderr bytes, and refuses existing output files.

**This command makes one real model/tool request and can incur cost.** Replace the service, actual `.selfstudy` Hosted folder, and exact version before consenting:

```bash
python scripts/selfstudy.py capture --language en --directory "YOUR-TOOLBOX-HOSTED-ABSOLUTE-PATH" --service "YOUR-PREFIX-toolbox-hosted-en" --version "ACTUAL-AGENT-VERSION" --output .selfstudy/toolbox-remote-en/response.raw --confirm-cost
```

Only after the invocation finishes, use the raw file's printed absolute path to validate the preserved response without calling the model again:

```bash
python scripts/workshop.py --script verify-toolbox-response --file "ABSOLUTE-PATH-TO-RESPONSE-RAW" --package "ACTUAL-PACKAGE-ABSOLUTE-PATH" --agent-name "YOUR-PREFIX-toolbox-hosted-en" --agent-version "ACTUAL-AGENT-VERSION" --output "NEW-VERIFICATION-RESULT-ABSOLUTE-PATH"
```

The verifier derives language from the package; it has no `--language` option. It checks actual SSE completion, version, package, and tool/Skill evidence. Capturing stdout is not itself verification. On failure, inspect the preserved raw/error files and that same session's original logs.

After verification, use 08's session listing/stopping procedure. Detailed remote evidence is under the session home's `workshop-evidence/toolbox-runs/`; [retrieve session files](advanced/session-files.md) before any optional deletion.

## 9. Manage versions deliberately

After review, change the selected default with:

```bash
python scripts/workshop.py --language en toolbox select --version "REVIEWED-VERSION" --confirm-update
```

Keep earlier versions so the same mechanism can select a reviewed prior version.

**Completion:** Record listing, actual retrieval, model answers, and Skill readback/load separately. Retain assets and ledgers for later exercises. If deleting at the end, respect reference order; in retention mode, keep them.

**Next → [11. Memory, A2A, and Routines](11-memory-a2a-routines.md)**
