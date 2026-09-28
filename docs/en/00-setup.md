# 00. Set up your own lab environment

**English** | [한국어](../00-setup.md) · [Course home](../../README.md)

**Outcome:** Create a Foundry project and model deployment in your own Azure subscription, then prepare data-access permissions and the local runtime.

Start with a **Microsoft Entra ID account, an Azure subscription, and an active subscription Owner role**. You do not need someone else's preconfigured endpoint or Search service. New resources and model requests can incur charges.

**Default order:** permissions → files/tools → sign-in → dedicated group/project/Sol deployment → data roles → configuration checks. Prepare Azure resources in **North Central US (`northcentralus`)**. On your first run, follow the **portal route**; the collapsed CLI alternatives are not additional required steps.

Names in this guide are examples. Do not copy resource groups or IDs from validation reports into your configuration. To continue an existing environment, start with [resume instructions](checkpoints.md#resume-on-another-day).

## 1. Check your permissions

1. Sign in to the [Azure portal](https://portal.azure.com).
2. Open **Subscriptions → your subscription → Access control (IAM) → View my access** and verify Owner.
3. If your PIM role is only eligible, activate it through your organization's normal process. Eligibility is not an active assignment.
4. Locate **Overview → Subscription ID** and **Properties → Directory/Tenant ID** for that subscription. Copy values directly into commands when needed; section 8's helper also collects and saves them.
5. Check permitted regions, services, and network policies. Owner cannot bypass management-group deny policies.

**Important:** Subscription Owner is not Entra Global Administrator. Preparing the Azure resources in this course does not require directory-wide administration or a new client secret. Chapter 14 covers the included GitHub OIDC workflow's lab permissions.

## 2. Get the files and development tools

1. Extract the **workshop ZIP** you received. Otherwise, open [this repository](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5) and select **Code → Download ZIP**. A private repository requires access.
2. Find the extracted folder containing **`README.md`, `scripts/`, and `curriculum.json` together**. Do not work inside the ZIP or its parent folder.
3. Open that entire folder using your editor's **File → Open Folder**. In VS Code, choose **Terminal → New Terminal** to enter commands.

Read the guide in your browser or open the Markdown file in VS Code and select **Open Preview** (`Cmd+Shift+V` on macOS, `Ctrl+Shift+V` on Windows/Linux). This renders tables, links, and collapsed optional sections. Paste commands into the **terminal**, not the preview.

All code and data are included. A ZIP provided to you requires neither a GitHub account nor Git.

<details>
<summary>Optional: clone instead of downloading a ZIP if Git is already installed</summary>

```bash
git clone https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5.git
cd microsoft-foundry-labs-v1.5
```

Open the cloned folder in your editor. Do not also repeat the ZIP route.

</details>

Use an approved development environment. Azure Owner does not override software-installation restrictions on your device.

| Tool | Install and check |
|---|---|
| Python **3.13** | Install [Python](https://www.python.org/downloads/). Check `python3.13 --version` on macOS/Linux or `py -3.13 --version` on Windows. |
| Azure CLI | Follow the [official installation guide](https://learn.microsoft.com/cli/azure/install-azure-cli), then run `az version`. |
| Azure Developer CLI | [Install azd](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd), then run `azd version`. |
| Editor | Open the **entire v1.5 folder** in VS Code or another editor. |

**Windows execution boundary:** you can prepare the lab in PowerShell, but **05 section 5's local SDK pause/resume and its recovery extension require macOS/Linux, including approved WSL**. The runner uses POSIX `fcntl` locks and does not run in Windows Python. To do that section, use a separate source copy in approved WSL/Linux and complete only the Linux Python setup and doctor below; that local experiment needs no Azure configuration or login. Do not copy a Windows `.venv` or private Azure state.

Check your current folder/files using `pwd` and `ls` on macOS/Linux, or `Get-Location` and `Get-ChildItem` in PowerShell. The `bash`/`powershell` labels above code blocks are not commands. **Execute one line at a time; stop on an error before running the next line.**

Do not overwrite a `.venv` created with another Python version or existing personal lab state. Preserve that folder and **extract the ZIP into a new folder**.

**On a first run, skip the collapsed section below and execute only the installation block for your OS.**

<details>
<summary>Existing environments only: start again with a different project</summary>

### Start a new project without adopting old state

1. Follow [15's stopping/retention steps](15-capstone-cleanup.md#4-stop-running-work-first) for the old environment. Privately preserve `.env`, `.selfstudy`, `outputs/`, `.build/`, and ownership records.
2. Extract or clone **source only into a new folder** and open a new terminal. Do not copy previous settings, results, or azd environments into the new project's active state.
3. Choose a new project/prefix and unused result labels. If labels change, update every collect/evaluate/compare/verify reference.
4. Deleting previous resources is a separate decision. Do not follow a report's deletion history as an instruction or edit ownership records to bypass cross-project checks.

**Run `configure`, `set`, `models`, `resource`, and `bind-matrix` one at a time in a checkout.** Concurrent writers can conflict while replacing settings files. Parallel experiments need separate workspaces and ownership records.

</details>

### macOS / Linux

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
```

If PowerShell blocks activation, do not weaken system policy. Replace subsequent `python ...` commands with `.\.venv\Scripts\python.exe ...`.

This installs local packages only. **It does not create Azure resources, sign you in, or change subscriptions.** Preserve folders that already contain personal configuration or results.

```bash
python scripts/workshop.py --language en doctor
```

Check the installation's `No broken requirements found.` and doctor's `language: en`, `documents: 6`, `dev_cases: 6`, `holdout_cases: 4`, `azure_tested: false`, and `result: PASS`. This is not an Azure connectivity test. It reports dataset counts; do not open holdout questions or answers.

**Activate `.venv` in every new terminal.** Run all commands from the folder containing `README.md`.

Continue without creating a separate notes file. Section 8 saves configuration in `.env` and `.selfstudy/azure.json`; later commands identify their result files. The helpers create the required directories too.

Names beginning with a dot, such as `.selfstudy`, `.env`, and `.build`, may be hidden by your file manager. Find them in the editor's file explorer and keep the leading dot. **Section 8's `configure` creates `.env`; you do not need to copy `.env.example` or supply keys now.**

English workshop commands use `--language en` **before the subcommand**. Wrapper options (`--model-deployment`, `--script`) go before `--language en`. The shared `selfstudy.py` helper has no global language flag; its later `prepare-hosted` and `capture` subcommands accept their own `--language en`. Keep English labels and results separate from Korean runs; see [Data and localization](data-format.md).

## 3. Sign in and plan names

```bash
az login
az account list --output table
azd auth login
```

Follow normal MFA procedures. Check that the browser, Azure CLI, and azd use the same tenant. The configuration helper explicitly supplies the subscription ID; it does not automatically switch your default subscription.

Choose your own unique prefix. Replace `YOUR-...`, `<...>`, and personal resource-name placeholders with actual values before execution.

| Purpose | Illustrative name—replace it |
|---|---|
| Prefix identifying your assets | `lab-yourname-nc-0928` |
| Resource group | `rg-mf15-yourname-nc-0928` |
| Foundry project | `mf15-nc-project` |
| Foundry resource | Record the actual name created by the portal. |
| First model's deployment alias | `workshop-chat` |

The prefix must start with `lab-`, use lowercase letters, numbers, and hyphens, and contain at most 32 characters. Keep it unchanged throughout the lab so ownership remains clear.

**Replace:** resource names containing `yourname` and `YOUR-...`/`ACTUAL-...` placeholders. **Keep on a first run:** deployment alias `workshop-chat`, result labels such as `baseline-en`/`candidate-en`, and file paths. Keep the guide's selected models, versions, and region too. If a name already exists, preserve that asset and follow the relevant fresh-name/resume instructions instead.

## 4. Create a dedicated resource group

1. In the Azure portal, open **Resource groups → Create**.
2. Select your Owner subscription and a new group name.
3. Select **North Central US**. Project availability is not proof that every model/tool call will work.
4. Check the [Foundry region table](https://learn.microsoft.com/azure/foundry/reference/region-support) and [Search region table](https://learn.microsoft.com/azure/search/search-region-support). Both official managed red-teaming lists also include North Central US. [Chapter 13 explains their differences](13-governance.md#5-managed-ai-red-teaming--the-primary-verification-target).
5. Add a nonsecret tag such as `workshop=foundry-v1.5`, then create the group.

Keep only workshop resources in this group. You cannot safely delete an entire existing business resource group at the end.

<details>
<summary>Optional: create the group with CLI instead of the portal — use only one route</summary>

Replace the subscription ID and names. Do not recreate a group already made in the portal.

```bash
az group create --subscription "YOUR-SUBSCRIPTION-ID" --name "rg-mf15-yourname-nc-0928" --location northcentralus --tags workshop=foundry-v1.5 lifecycle=retain
```

</details>

`lifecycle=retain` records an intention to keep resources; it is not a deletion lock. Apply [retention mode](15-capstone-cleanup.md#retention-mode) if you want to keep the environment.

You can set a personal budget alert under the subscription or group's **Cost Management → Budgets**. Choose an amount using current prices and your own budget. **An alert does not automatically stop usage or guarantee a refund.**

## 5. Create a Foundry project

1. Open [Foundry](https://ai.azure.com). If a **New Foundry** switch appears, select the current portal.
2. Open the project selector at the upper left → **Create new project**.
3. Enter a project name and open **Advanced options**.
4. Select your subscription, **the dedicated group you just created**, and the verified region; then create.
5. The Foundry resource name may be generated automatically. Verify the actual name instead of assuming an example.
6. Copy the **Project endpoint** from the project home.

Its format is `https://<your-domain>.services.ai.azure.com/api/projects/<your-project>`. It is different from the model's `.openai.azure.com` endpoint. If the displayed URL differs from the format accepted by this pinned runtime, check Libraries/API for the project endpoint. Do not invent a different domain.

In the Azure portal, open **project resource → JSON View** and copy `id`.

```text
/subscriptions/.../resourceGroups/.../providers/Microsoft.CognitiveServices/accounts/.../projects/...
```

Use the **full ID through `/projects/...`**, not just the parent Foundry account ID.

<details>
<summary>Optional: create the Foundry project with CLI instead of the portal</summary>

### CLI alternative

Use this instead of the portal route. Do not omit `--assign-identity` or `--allow-project-management true`. Names must be globally unique where required; use the same subscription, group, and region throughout.

```bash
az cognitiveservices account create --subscription "YOUR-SUBSCRIPTION-ID" --resource-group "rg-mf15-yourname-nc-0928" --name "YOUR-UNIQUE-FOUNDRY-NAME" --custom-domain "YOUR-UNIQUE-FOUNDRY-NAME" --kind AIServices --sku S0 --location northcentralus --assign-identity --allow-project-management true
az cognitiveservices account project create --subscription "YOUR-SUBSCRIPTION-ID" --resource-group "rg-mf15-yourname-nc-0928" --name "YOUR-UNIQUE-FOUNDRY-NAME" --project-name "mf15-nc-project" --location northcentralus
```

CLI creation **does not guarantee Foundry User assignments** for the user and project. Verify both identities in section 7.

</details>

## 6. Deploy the first model

1. In Foundry **Discover → Models**, find **`gpt-6-sol`**.
2. Check version **`2026-09-22`**, capabilities, regions, and quota. Start directly with Sol for the first response and subsequent agent/tool exercises. See [Model roles and selection](model-selection.md).
3. Under **Deploy / Use this model**, name the deployment `workshop-chat`.
4. Select a pay-as-you-go Standard variant permitted by your policies. Choose Global Standard only if global processing is allowed. No PTU contract is required.
5. Wait for **Succeeded** and verify the actual base model, version, deployment type, and region.

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

Check these sources, then replace the placeholders inside quotes. Keep the quotes:

| Argument | Value to use |
|---|---|
| `--project-id` | Section 5's JSON View ID, including `/projects/...` |
| `--endpoint` | Section 5's Project endpoint |
| `--deployment` | Section 6's Sol deployment alias; default `workshop-chat` |
| `--prefix` | Your `lab-` prefix from section 3 |

```bash
python scripts/selfstudy.py configure --project-id "YOUR-NEW-NC-PROJECT-ARM-ID" --endpoint "YOUR-NEW-NC-PROJECT-ENDPOINT" --deployment "workshop-chat" --expected-model gpt-6-sol --prefix "lab-yourname-nc-0928"
```

<details>
<summary>Existing environments only: use a differently named Sol deployment</summary>

After verifying `workshop-compare` really contains Sol in the same intact project, use its alias with the same project, endpoint, and prefix. Do not also run the default fresh-environment command:

```bash
python scripts/selfstudy.py configure --project-id "YOUR-PROJECT-ARM-ID" --endpoint "YOUR-PROJECT-ENDPOINT" --deployment workshop-compare --expected-model gpt-6-sol --prefix "YOUR-UNCHANGED-LAB-PREFIX"
```

Keep earlier result labels, files, and agent versions immutable. Use new names/labels for changed model or evaluation conditions. See [existing deployment aliases](model-selection.md#reuse-existing-deployments-without-changing-them).

</details>

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

**A first-time learner does not need to jump ahead.** MAF is introduced in 04 and logging in 09. Only for a separate investigation requiring traces from its first request, prepare [09's logging connection](09-operations.md#1-create-and-connect-logging-resources) early. Earlier responses are not collected retroactively.

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
