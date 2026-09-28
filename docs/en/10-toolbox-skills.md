# 10. Toolbox, Tool Search, Skills, and OpenAPI

**English** | [한국어](../10-toolbox-skills.md) · [Course home](../../README.md#curriculum) · [Help](checkpoints.md)

**Outcome:** Create a keyless connection to your own Search service and actually use versioned tools and procedures.

**Prerequisites:** The original Search index and successful retrieval from 06, the project managed identity from 00, and **08's azd Foundry extension plus the actual folder created by `prepare-hosted`**. Installing the extension alone does not create a folder for `--cwd`.

Even without a successful remote deployment in 08, **successful folder preparation in its sections 1–3 is enough for this chapter's sections 1–7**. If missing, complete [08's preparation](08-hosted.md#3-prepare-an-isolated-folder-for-the-existing-project) first. Check remote Hosted support separately for section 8.

**Where you work:** portal for roles/connections; terminal for tools, Skills, and Hosted execution. Section 8 uses terminals A and B.

> **Keep versions separate:** Skill, Toolbox, and Hosted agent versions are different values. Use the version returned by the corresponding command.

<a id="chapter-map"></a>

**Chapter map**

| Step | Result to check |
|---|---|
| [1. Project permissions](#1-grant-project-to-search-access) | Project identity's Search roles |
| [2. Keyless connection](#2-create-a-keyless-project-connection) | Actual target and authentication |
| [3. Standard Toolbox](#3-start-with-a-standard-toolbox) | Listing → actual retrieval → model answer |
| [4. Tool discovery](#4-tool-search-and-pinned-tools) | New version's discovery/pinned-tool list |
| [5. Upload Skill](#5-prepare-upload-and-read-back-a-skill) | Downloaded content matches the source |
| [6. Attach Skill](#6-attach-the-exact-skill-version) | Actual Skill load and tool results |
| [7. OpenAPI](#7-use-openapi-against-the-same-search-service) | Actual retrieval under a different caller identity |
| [8. Hosted Toolbox](#8-host-the-same-toolbox) | Local/remote responses and preserved raw evidence |
| [9. Select default version — optional](#9-manage-versions-deliberately) | Explicit selection of a reviewed version |
| [Completion check](#completion-check) | Versioned execution, ownership, and stopped sessions |

These steps require the working keyword index from 06. Keyword retrieval alone does not verify Toolbox, OpenAPI, or Hosted Toolbox; check each actual call below. If a prerequisite is missing in your environment, pause that dependent step rather than substituting File Search.

## 1. Grant project-to-Search access

Check that the **original index from 06** is selected:

```bash
python scripts/selfstudy.py status
```

**Read the required-role plan**

```bash
python scripts/selfstudy.py roles --user-object-id "YOUR-USER-OBJECT-ID"
```

The caller for this Toolbox is the **project managed identity**. Grant it **Search Index Data Reader and Search Service Contributor on your dedicated Search service**.

Search Service Contributor is not read-only. Here it provides the schema access needed by the tool; scope it **only to the dedicated lab Search service**. Do not confuse the project identity with the account identity used by another connection type.

## 2. Create a keyless project connection

Use the actual Search/project endpoints and your unique connection name. For `--cwd`, use **the folder printed by `prepare-hosted` in 08** so the command has the same project's ARM context, not the repository root or `.build` package:

```bash
azd ai connection create "YOUR-PREFIX-search-en" --kind cognitive-search --target "YOUR-SEARCH-ENDPOINT" --auth-type project-managed-identity --audience https://search.azure.com --project-endpoint "YOUR-PROJECT-ENDPOINT" --cwd "YOUR-08-HOSTED-ABSOLUTE-PATH"
```

**Check:** in Foundry **Project details → Connected resources**, read back the connection, target, and authentication type. Do not use `--force`, API keys, or another project's connection.

**Save the verified connection name**

```bash
python scripts/selfstudy.py set TOOLBOX_SEARCH_CONNECTION_NAME "YOUR-PREFIX-search-en"
```

The current SDK can report project-managed-identity authentication as **`ProjectManagedIdentity`**. Do not reject a valid connection merely because earlier code expected only legacy `AAD`. Keep the CLI's `--auth-type project-managed-identity`; do not bypass an enum mismatch with an API key or another identity.

## 3. Start with a standard Toolbox

```bash
python scripts/workshop.py --language en toolbox plan
```

Verify that the planned project, Search connection, and index belong to your lab before creating anything.

**Create the planned Toolbox**

```bash
python scripts/workshop.py --language en toolbox create --confirm-create
```

Record the actual `selected_version` and substitute it below:

```bash
python scripts/workshop.py --language en toolbox probe --version "ACTUAL-VERSION" --label toolbox-list-en
```

**Query Search through Toolbox · `toolbox-query-en`**

```bash
python scripts/workshop.py --language en toolbox query --version "ACTUAL-VERSION" --label toolbox-query-en --confirm-cost
```

**Continue only after retrieval succeeds.** A tool listing or a failed query is not enough to run `ask` below.

**Call the model using Toolbox · `toolbox-answer-en`**

```bash
python scripts/workshop.py --language en toolbox ask --version "ACTUAL-VERSION" --label toolbox-answer-en --confirm-cost
```

| Step | What it verifies |
|---|---|
| probe | Authentication, MCP connection, and tool listing |
| query | Real retrieval from Toolbox to Search |
| ask | A model answer using the actual tool result |

A successful tool listing does not prove downstream Search permissions. For a query 403, preserve the error, identify the actual calling identity, and correct only that identity's Search roles.

## 4. Tool Search and pinned tools

Standard Toolbox success does not verify Tool Search or Skills. Create a new Toolbox version and verify the additional capabilities separately.

Check feature availability/Preview status and CLI support:

```bash
azd ai skill create --help
```

**Check Skill download support**

```bash
azd ai skill download --help
```

**Review the Toolbox creation plan**

```bash
python scripts/workshop.py --language en toolbox plan --discovery --pin-policy
```

Once support is confirmed:

```bash
python scripts/workshop.py --language en toolbox add-version --discovery --pin-policy --confirm-create
```

**Inspect tools in the specified version · `discovery-list-en`**

```bash
python scripts/workshop.py --language en toolbox probe --version "NEW-SELECTED-VERSION" --label discovery-list-en
```

Verify `tool_search`, `call_tool`, and `policy_search` in the actual list. Tool Search is **tool discovery**; File Search and Search retrieve **policy information**.

## 5. Prepare, upload, and read back a Skill

### Prepare inputs and upload

```bash
python scripts/workshop.py --language en prepare-extensions --label extensions-en
```

Reuse existing inputs only when their prefix, language, and prompt/source hashes match the selected instructions. If v2 changed, use the fresh-label update path below. Read `policy-review/SKILL.md`, `manifest.json`, and source hashes under `outputs/extensions-en/`. **Upload only `policy-review/`**, because its parent also contains evaluation references.

The generated `skill_name` is `<prefix>-policy-review-en`. Use the exact value from the manifest:

```bash
azd ai skill create "SKILL-NAME-FROM-MANIFEST" --file outputs/extensions-en/policy-review --project-endpoint "YOUR-PROJECT-ENDPOINT"
```

**Read the actual Skill version**

```bash
azd ai skill show "SKILL-NAME-FROM-MANIFEST" --project-endpoint "YOUR-PROJECT-ENDPOINT" --output json
```

### Download the same version and compare

Specify the returned `default_version` and download into a **new readback folder that does not already exist**:

```bash
azd ai skill download "SKILL-NAME-FROM-MANIFEST" --version "ACTUAL-SKILL-VERSION" --output-dir .selfstudy/skill-readback-en --project-endpoint "YOUR-PROJECT-ENDPOINT"
```

**Compare the download with the original**

```bash
python scripts/selfstudy.py compare-files outputs/extensions-en/policy-review/SKILL.md .selfstudy/skill-readback-en/SKILL.md
```

**Check:** if bytes differ, investigate. Do not edit the downloaded file to force a match.

**If this is your first Skill and readback matches, continue directly to section 6.** The following procedure applies only when changing instructions in an existing Skill.

<details>
<summary>Only when instructions change: create a new Skill version</summary>

### Update an existing Skill non-destructively

The strengthened v2 limits **the facts in the answer, not just citation IDs**, to actual evidence. Do not edit an old input folder. Prepare a new label and inspect the new `SKILL.md`:

```bash
python scripts/workshop.py --language en prepare-extensions --label skill-update-inputs-en
```

Verify the new manifest's `skill_name` matches the existing owned Skill and the content is the intended v2 before updating:

```bash
azd ai skill update "EXISTING-OWNED-SKILL-NAME" --file outputs/skill-update-inputs-en/policy-review --project-endpoint "YOUR-PROJECT-ENDPOINT"
```

**Read the actual Skill version**

```bash
azd ai skill show "EXISTING-OWNED-SKILL-NAME" --project-endpoint "YOUR-PROJECT-ENDPOINT" --output json
```

Keep the previous version and use the actual newly returned version rather than guessing its number:

```bash
azd ai skill download "EXISTING-OWNED-SKILL-NAME" --version "RETURNED-NEW-SKILL-VERSION" --output-dir .selfstudy/skill-readback-v2-en --project-endpoint "YOUR-PROJECT-ENDPOINT"
```

**Compare the download with the original**

```bash
python scripts/selfstudy.py compare-files outputs/skill-update-inputs-en/policy-review/SKILL.md .selfstudy/skill-readback-v2-en/SKILL.md
```

Never overwrite an existing input label or readback directory. Explicitly bind the new Skill version into a **new Toolbox version** in section 6, then verify new calls. Updating a Skill does not rewrite an older Toolbox's pinned version or its previous execution evidence.

</details>

## 6. Attach the exact Skill version

```bash
python scripts/workshop.py --language en toolbox plan --discovery --pin-policy --skill-version "ACTUAL-SKILL-VERSION"
```

**Create a Toolbox version from reviewed settings**

```bash
python scripts/workshop.py --language en toolbox add-version --discovery --pin-policy --skill-version "ACTUAL-SKILL-VERSION" --confirm-create
```

**Inspect tools in the specified version · `skilled-list-en`**

```bash
python scripts/workshop.py --language en toolbox probe --version "NEW-TOOLBOX-VERSION" --label skilled-list-en
```

**Call the model using Toolbox · `skilled-answer-en`**

```bash
python scripts/workshop.py --language en toolbox ask --version "NEW-TOOLBOX-VERSION" --label skilled-answer-en --with-skill --confirm-cost
```

**Check:** `skill_load_verified`, actual calls, and policy results. Registration alone does not prove the Skill was read. This example does not execute arbitrary Skill scripts.

## 7. Use OpenAPI against the same Search service

Instead of creating a business API, use the read API of your own synthetic Search index. First review the plan, actual caller, and target:

```bash
python scripts/workshop.py --language en openapi plan
```

This path uses the **Foundry account's system-assigned identity**, not the Toolbox's project identity. Enable it, then reread the actual ID using `selfstudy.py configure` with the **same actual Sol alias and `--expected-model gpt-6-sol`** selected in 00. Grant this identity **Search Index Data Reader on the relevant Search service**. `selfstudy.py roles` distinguishes these identities.

```bash
python scripts/workshop.py --language en openapi invoke --label openapi-policy-en --confirm-cost
```

Verify the actual OpenAPI tool call and returned source text. Explain how `lookup_policy`, MCP, OpenAPI, and Code Interpreter are different execution mechanisms.

## 8. Host the same Toolbox

### Prepare the package and deployment folder

Start with a verified **standard Toolbox version**. If selecting a Skill-enabled version, add `--with-skill` to both packaging and serving; keep that choice consistent.

```bash
python scripts/workshop.py --script package-toolbox --language en --version "VERIFIED-TOOLBOX-VERSION"
```

**Prepare a deployment folder from the returned package**

```bash
python scripts/selfstudy.py prepare-hosted --language en --kind toolbox --package "ACTUAL-RETURNED-PACKAGE-PATH" --name toolbox-hosted-en
```

As in 08, inspect the manifest and actual project, and use the exact printed service/folder. `prepare-hosted` defaults to Korean; keep its explicit `--language en` matched to the package.

### Terminal A: start the local server

Stop any earlier local server. Leave terminal A running in the repository root:

```bash
python scripts/workshop.py --language en toolbox serve --version "VERIFIED-TOOLBOX-VERSION"
```

### Terminal B: invoke actual tools

Open terminal B in the same root and activate `.venv` there too:

```bash
python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8088/readiness', timeout=10).read().decode())"
```

**Check:** if the status is not `healthy`, inspect terminal A's server log before sending a request.

**Send the model request after checking readiness**

```bash
azd ai agent invoke --cwd "YOUR-TOOLBOX-HOSTED-ABSOLUTE-PATH" --local --port 8088 --new-session --new-conversation --timeout 210 "What advance approval is required for a KRW 170000 hotel on a domestic business trip in September 2026?"
```

**Check and stop:** verify actual tools, model response, and sources, then stop A with `Ctrl+C`.

### Deploy remotely

Decide separately whether to deploy remotely:

```bash
azd deploy "YOUR-PREFIX-toolbox-hosted-en" --cwd "YOUR-TOOLBOX-HOSTED-ABSOLUTE-PATH"
```

**Read the deployed version and runtime identity**

```bash
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

After verification, use 08's session listing/stopping procedure. Detailed evidence is under the session home's `workshop-evidence/toolbox-runs/`. Retrieval and tool-result hash matching were verified from an actual stopped session. Even without deletion, [archive with an absolute `--target-path`](advanced/session-files.md) **before service expiry**, preserving the original package, response, session, and version together.

## 9. Manage versions deliberately

**Optional:** select a version as the default for later calls only after reviewing its actual execution. This does not create a new version:

```bash
python scripts/workshop.py --language en toolbox select --version "REVIEWED-VERSION" --confirm-update
```

Keep earlier versions so the same mechanism can select a reviewed prior version.

## Completion check

- [ ] I checked listing, actual retrieval, and model answers separately.
- [ ] I verified Skill readback/load and distinguished all three kinds of version.
- [ ] I preserved actual OpenAPI/Hosted results or blocked status.
- [ ] I stopped local servers and remote sessions and retained raw responses and ownership records.

Retain assets and ledgers for later exercises. Remove them in reference order only if choosing deletion during final cleanup.

---

[← 09. Operations](09-operations.md) · [Course home](../../README.md#curriculum) · [11. State and scheduling →](11-memory-a2a-routines.md) · [Chapter map ↑](#chapter-map)
