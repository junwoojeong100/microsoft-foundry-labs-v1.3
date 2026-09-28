# 00. Set up your own lab environment

**English** | [한국어](../00-setup.md) · [Course home](../../README.md)

**Outcome:** Create a Foundry project and model deployment in your own Azure subscription, then prepare data-access permissions and the local runtime.

Start with a **Microsoft Entra ID account, an Azure subscription, and an active subscription Owner role**. You do not need someone else's preconfigured endpoint or Search service. New resources and model requests can incur charges.

**The current target is a new North Central US (`northcentralus`) project.** Foundation creation, Sol project Responses, Prompt Agent creation/invocation, and local MAF function/MCP calls are now verified. These are path-specific results, not a guarantee for other managed tools or the whole course. Do not recreate resources already prepared.

Subsequent NC evidence includes KO/EN six-file File Search indexing/citations, a real six-row CSV, MAF workflows, Korean/English Search/GA IQ/Hybrid/IQ Chat, Hosted IQ v1/v2 dev 6/6, and an actual scheduled response. **A new Task Adherence-only managed job passed 5/5**; the earlier mixed six-row job still retains five pass/one fail and its Prohibited Actions reason/flag contradiction. This is not an all-ASR fix, and a bounded Group Chat is not convergence. Read the [current results and limits](validation-report.md).

## 1. Check your permissions

1. Sign in to the [Azure portal](https://portal.azure.com).
2. Open **Subscriptions → your subscription → Access control (IAM) → View my access** and verify Owner.
3. If your PIM role is only eligible, activate it through your organization's normal process. Eligibility is not an active assignment.
4. Record the subscription ID and associated tenant ID in your private workbook.
5. Check permitted regions, services, and network policies. Owner cannot bypass management-group deny policies.

**Important:** Subscription Owner is not Entra Global Administrator. Preparing the Azure resources in this course does not require directory-wide administration or a new client secret. Chapter 14 covers the included GitHub OIDC workflow's lab permissions.

## 2. Get the files and development tools

Extract the **workshop ZIP**, or clone this repository if you have access. Code and data are bundled; do not download another repository. GitHub and Git are optional when using the ZIP.

Use an approved development environment. Azure Owner does not override software-installation restrictions on your device.

| Tool | Install and check |
|---|---|
| Python **3.13** | Install [Python](https://www.python.org/downloads/). Check `python3.13 --version` on macOS/Linux or `py -3.13 --version` on Windows. |
| Azure CLI | Follow the [official installation guide](https://learn.microsoft.com/cli/azure/install-azure-cli), then run `az version`. |
| Azure Developer CLI | [Install azd](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd), then run `azd version`. |
| Editor | Open the **entire v1.5 folder** in VS Code or another editor. |

Your terminal's current directory must contain `README.md`, `scripts/`, and `curriculum.json`.

Do not overwrite a `.venv` created with another Python version or existing personal lab state. Preserve that folder and **extract the ZIP into a new folder**.

### Start a new project without adopting old state

1. Privately archive the previous `.env`, `.selfstudy` configuration/ownership records, CI identity information, `outputs/`, and `.build/`, retaining original hashes. Keep raw recordings unchanged.
2. In this transition, only the explicitly verified previous Sweden E2E group was deleted. Local state was preserved under `.selfstudy/archives/sweden-20260928-before-northcentral`. This is history, not permission to delete other groups, CI identities, or evidence.
3. Use a fresh source copy/workspace and terminal. Do not copy old `.env`, active `.selfstudy`, result folders, or azd environments into the new project's active state. If reusing a checkout, verify the archive/hashes first and initialize only fresh active state through the supported setup flow.
4. Choose a new NC prefix and unused labels, for example `lab-yourname-nc-0928`, `nc-baseline-en`, and `nc-candidate-en`. If replacing example labels, update every collect/evaluate/compare/verify reference consistently.
5. Never delete or edit `.env`/ownership ledgers to bypass cross-project checks. Retaining a previous CI identity does not establish its roles or access in the new project.

The commands below target **the fresh workspace and new NC resources**. Do not adopt archived Sweden responses, traces, evaluations, or deployment versions as new results.

### macOS / Linux

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, do not weaken system policy. Replace subsequent `python ...` commands with `.\.venv\Scripts\python.exe ...`.

This installs local packages only. **It does not create Azure resources, sign you in, or change subscriptions.** Preserve folders that already contain personal configuration or results.

```bash
python scripts/workshop.py --language en doctor
```

Check `language: en`, `documents: 6`, `dev_cases: 6`, `holdout_cases: 4`, `azure_tested: false`, and `result: PASS`. This is not an Azure connectivity test. It reports dataset counts; do not open holdout questions or answers.

**Activate `.venv` in every new terminal.** Run all commands from the folder containing `README.md`.

English workshop commands use `--language en` **before the subcommand**. Wrapper options (`--model-deployment`, `--script`) go before `--language en`. The shared `selfstudy.py` helper has no global language flag; its later `prepare-hosted` and `capture` subcommands accept their own `--language en`. Keep English labels and results separate from Korean runs; see [Data and localization](data-format.md).

## 3. Sign in and plan names

```bash
az login
az account list --output table
azd auth login
```

Follow normal MFA procedures. Check that the browser, Azure CLI, and azd use the same tenant. The configuration helper explicitly supplies the subscription ID; it does not automatically switch your default subscription.

Choose your own unique prefix. Replace every `YOUR-...`, `<...>`, and illustrative name in this guide with the actual value before execution.

| Purpose | Illustrative name—replace it |
|---|---|
| Prefix identifying your assets | `lab-yourname-nc-0928` |
| Resource group | `rg-mf15-yourname-nc-0928` |
| Foundry project | `mf15-nc-project` |
| Foundry resource | Record the actual name created by the portal. |
| First model's deployment alias | `workshop-chat` |

The prefix must start with `lab-`, use lowercase letters, numbers, and hyphens, and contain at most 32 characters. Keep it unchanged throughout the lab so ownership remains clear.

## 4. Create a dedicated resource group

1. In the Azure portal, open **Resource groups → Create**.
2. Select your Owner subscription and a new group name.
3. Select **North Central US**. Project availability is not proof that every model/tool call will work.
4. Check the [Foundry region table](https://learn.microsoft.com/azure/foundry/reference/region-support) and [Search region table](https://learn.microsoft.com/azure/search/search-region-support). The managed red-teaming [regional matrix](https://learn.microsoft.com/azure/foundry/concepts/evaluation-regions-limits-virtual-network#supported-regions-for-ai-red-teaming) and [concept overview](https://learn.microsoft.com/azure/foundry/concepts/ai-red-teaming-agent#agentic-risks) disagree on the wider list, but **both include North Central US**. Keep this region without treating the discrepancy as proof that Sweden was unsupported or caused the ASR error.
5. Add a nonsecret tag such as `workshop=foundry-v1.5`, then create the group.

Keep only workshop resources in this group. You cannot safely delete an entire existing business resource group at the end.

For the CLI alternative, replace the subscription ID and names. Do not recreate a group already made in the portal.

```bash
az group create --subscription "YOUR-SUBSCRIPTION-ID" --name "rg-mf15-nc-your-lab" --location northcentralus --tags workshop=foundry-v1.5 lifecycle=retain
```

`lifecycle=retain` records an intention to keep resources; it is not a deletion lock. Apply [retention mode](15-capstone-cleanup.md#retention-mode) if you want to keep the environment.

You can set a personal budget alert under the subscription or group's **Cost Management → Budgets**. Choose an amount using current prices and your own budget. **An alert does not automatically stop usage or guarantee a refund.**

## 5. Create a Foundry project

1. Open [Foundry](https://ai.azure.com). If a **New Foundry** switch appears, select the current portal.
2. Open the project selector at the upper left → **Create new project**.
3. Enter a project name and open **Advanced options**.
4. Select your subscription, **the dedicated group you just created**, and the verified region; then create.
5. The Foundry resource name may be generated automatically. Record the actual name instead of assuming an example.
6. Copy the **Project endpoint** from the project home.

Its format is `https://<your-domain>.services.ai.azure.com/api/projects/<your-project>`. It is different from the model's `.openai.azure.com` endpoint. If the displayed URL differs from the format accepted by this pinned runtime, check Libraries/API for the project endpoint. Do not invent a different domain.

In the Azure portal, open **project resource → JSON View** and copy `id`.

```text
/subscriptions/.../resourceGroups/.../providers/Microsoft.CognitiveServices/accounts/.../projects/...
```

Use the **full ID through `/projects/...`**, not just the parent Foundry account ID.

### CLI alternative

Use this instead of the portal route. Do not omit `--assign-identity` or `--allow-project-management true`. Names must be globally unique where required; use the same subscription, group, and region throughout.

```bash
az cognitiveservices account create --subscription "YOUR-SUBSCRIPTION-ID" --resource-group "rg-mf15-nc-your-lab" --name "YOUR-UNIQUE-FOUNDRY-NAME" --custom-domain "YOUR-UNIQUE-FOUNDRY-NAME" --kind AIServices --sku S0 --location northcentralus --assign-identity --allow-project-management true
az cognitiveservices account project create --subscription "YOUR-SUBSCRIPTION-ID" --resource-group "rg-mf15-nc-your-lab" --name "YOUR-UNIQUE-FOUNDRY-NAME" --project-name "mf15-nc-project" --location northcentralus
```

CLI creation **does not guarantee Foundry User assignments** for the user and project. Verify both identities in section 7.

## 6. Deploy the first model

1. In Foundry **Discover → Models**, find **`gpt-6-sol`**.
2. Check version **`2026-09-22`**, capabilities, regions, and quota. Start directly with Sol for the first response and subsequent agent/tool exercises. See [Model roles and selection](model-selection.md).
3. Under **Deploy / Use this model**, name the deployment `workshop-chat`.
4. Select a pay-as-you-go Standard variant permitted by your policies. Choose Global Standard only if global processing is allowed. No PTU contract is required.
5. Wait for **Succeeded** and record the actual base model, version, deployment type, and region.

If quota is unavailable or the model is not offered, **do not repeatedly click Create**. Check current availability, request the required quota, or pause until it is available. Keep a required region and the Sol selection fixed; do not substitute another model and present it as the same success.

Sol is the default answer model. The GPT-6 Luna comparison in 02 is optional; the judge in 07 is **GPT-5.5 / 2026-04-24**. Prepare IQ Chat's separate `gpt-5.6-luna` model and Optimizer only in their respective chapters.

If a different model already uses the same deployment name, **do not replace or delete it**. Explicitly reuse the actual existing Sol deployment or choose a new unique name. The setup helper checks the real model/version. Do not relabel existing agents or evaluations as results from a new model.

## 7. Verify data-access roles

In the Azure portal, inspect **your actual Foundry resource → IAM → Role assignments**.

| Identity | Role | Scope |
|---|---|---|
| Your signed-in user | **Foundry User** | This workshop's Foundry resource |
| This project's managed identity | **Foundry User** | The same Foundry resource |

Do not duplicate assignments already created by the portal. If missing, use **Add role assignment → Foundry User → Members** and select the correct identity. The older name **Azure AI User** may appear; the role ID is `53ca6127-db72-4b80-b1b0-d745d6d5456d`.

The managed identity is not your user account or a project-name string. Identify it through **project resource → JSON View → identity.principalId**. If no identity exists, check the project's managed-identity configuration before continuing.

Subscription Owner's resource-management permission does not replace data-plane permission. Do not create an app registration or client secret for this step.

## 8. Collect configuration from actual values

Replace the three values and prefix inside quotes:

```bash
python scripts/selfstudy.py configure --project-id "YOUR-NEW-NC-PROJECT-ARM-ID" --endpoint "YOUR-NEW-NC-PROJECT-ENDPOINT" --deployment "workshop-chat" --expected-model gpt-6-sol --prefix "lab-yourname-nc-0928"
```

**Only when resuming an intact, unchanged project:** after freshly verifying that `workshop-compare` contains Sol, its alias may be reused with the same project, endpoint, and prefix. **This exception is not the new NC rebuild.** Do not adopt a deleted Sweden project's aliases or archived state into the new project:

```bash
python scripts/selfstudy.py configure --project-id "YOUR-PROJECT-ARM-ID" --endpoint "YOUR-PROJECT-ENDPOINT" --deployment workshop-compare --expected-model gpt-6-sol --prefix "YOUR-UNCHANGED-LAB-PREFIX"
```

Keep earlier result labels, files, and agent versions immutable. Use new names/labels for changed model or evaluation conditions. See [existing deployment aliases](model-selection.md#reuse-existing-deployments-without-changing-them).

This helper **only reads subscription, project, account, and deployment metadata** through Azure CLI. After verifying ID/endpoint consistency and deployment state, it records:

- `.env`: one set of SDK configuration values.
- `.selfstudy/azure.json`: actual resource IDs, managed identities, region, and verification time.

It does not store tokens, passwords, or API keys, and does not overwrite configuration for a different existing project. Distinguish `management_metadata_read: true` from `model_invoked: false`.

New configuration uses **reasoning `low` and a `32768` output-token cap**. Reasoning tokens count toward this cap. If reusing older personal settings, inspect and explicitly align them, then use new agents and experiment labels:

```bash
python scripts/selfstudy.py set WORKSHOP_REASONING_EFFORT low
python scripts/selfstudy.py set WORKSHOP_MAX_OUTPUT_TOKENS 32768
```

```bash
python scripts/selfstudy.py values
python scripts/workshop.py --language en doctor --cloud
```

Check the subscription, tenant, and deployment. `doctor --cloud` checks authentication and metadata, not inference.

**Pass the first real Sol request in the next chapter before creating agents.** Deployment status `Succeeded` is not proof that every tool/API path works. Preserve original errors and use [Troubleshooting](troubleshooting.md) when needed.

Before adding dependent resources, also perform [04's bare MAF model → local function probes](04-tools.md#1-run-a-maf-agent) early. A regional Function table and local Python execution are different evidence layers; record both actual requests separately.

For region-specific checks that need traces from their first requests, **optionally prepare [09's logging resources and connection](09-operations.md#1-create-and-connect-logging-resources) early**. Logging resources were created early in this NC run for that purpose. The normal course still introduces logging in 09; do not assume responses from before connection were backfilled.

## 9. Generate role-assignment commands when needed

Find your user Object ID in the Azure portal or use:

```bash
az ad signed-in-user show --query id --output tsv
python scripts/selfstudy.py roles --user-object-id "YOUR-USER-OBJECT-ID"
```

`roles` **prints a plan; it does not execute assignments**. Compare it with Portal IAM and apply only missing roles. Do not grant Owner to another identity or broaden permissions to the whole subscription.

## Completion check

- [ ] I created my dedicated group, Foundry project, and model deployment.
- [ ] I verified data roles for my user and the project's managed identity.
- [ ] I saved one consistent configuration and read back its actual values.
- [ ] I understand cost boundaries and additional-permission requirements.

Resolve blockers using [Troubleshooting](troubleshooting.md). If stopping, review [cleanup and retention](15-capstone-cleanup.md) now.

**Next → [01. Foundry and your first model response](01-foundry.md)**
