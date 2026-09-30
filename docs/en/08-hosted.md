# 08. Local Hosted execution and Azure deployment

**English** | [한국어](../08-hosted.md) · [Course home](../../README.md#curriculum) · [Help](checkpoints.md)

**Outcome:** Package your code, make a real local request, deploy to Foundry, and invoke the exact remote version.

**Prerequisites:** The MAF function exercise from 04, project ARM ID/location from 00, and a working model. **Subscription Owner prepares deployment permissions**; runtime data permissions are separate.

**Where you work:** terminal for packaging/deployment/requests, editor for manifests, Azure portal for roles. Local requests use terminals A and B.

<a id="chapter-map"></a>

**Chapter map**

| Step | Result to check |
|---|---|
| [1. Prepare azd](#1-prepare-azd-foundry-commands) | Foundry extension and Hosted availability |
| [2. Package](#2-build-a-safe-english-package) | No secrets or evaluation answers in the package |
| [3. Deployment folder](#3-prepare-an-isolated-folder-for-the-existing-project) | Actual service, folder, and project values |
| [4. Local request](#4-make-a-real-local-request) | Readiness and real inference checked separately |
| [5. Deployment and roles](#5-deploy-remotely) | New version and its runtime identity |
| [6. Remote request and stop](#6-invoke-the-exact-remote-version) | Same-version response and stopped session |
| [7. Repeat with a workflow](#7-repeat-with-a-workflow) | Local and remote workflow-profile results |
| [Completion check](#completion-check) | Packaging, local, and remote outcomes distinguished |

Package path, deployment folder, and service name are different values. Use **[section 3's value-copy table](#3-prepare-an-isolated-folder-for-the-existing-project)** and pass each actual output into the next command.

## 1. Prepare azd Foundry commands

```bash
azd version
```

**Inspect installed Foundry extensions**

```bash
azd extension list --installed
```

Install `microsoft.foundry` only if missing:

```bash
azd extension install microsoft.foundry
```

**Sign in to azd in the same tenant**

```bash
azd auth login
```

**Check that Foundry commands are available**

```bash
azd ai agent show --help
```

Check Hosted support and capacity in your subscription/region. Code deployment does not require local Docker or ACR installation.

| Blocked scope | Next action |
|---|---|
| Only remote deployment is unavailable | Retain sections 1–3's successfully prepared folder for later project connections. Record remote deployment/invocation as not run. |
| Local folder preparation also failed | Do not mark preparation complete. Stop dependent steps. |

Record the unavailable scope as blocked. **Do not recreate an existing project arbitrarily.**

## 2. Build a safe English package

```bash
python scripts/workshop.py --script package-hosted --language en
```

**Check:** open `package-manifest.json`, `runtime-profile.json`, and `requirements.txt` at the printed location. The default English package is `.build/hosted-en/`.

| Must be present | Must be absent |
|---|---|
| Code, synthetic policies, instructions | `.env`, credentials, evaluation answers, execution results |

The frozen runtime profile must contain `language: en`. `cloud_deployed: false` describes **packaging**, not an Azure resource check.

Read any existing package before rebuilding. If rebuilding is necessary, preserve that exact package in another private location first. Do not delete unrelated packages or results.

## 3. Prepare an isolated folder for the existing project

```bash
python scripts/selfstudy.py status
```

Reuse the saved project ID, region, and prefix. Supply **only the exact package path** returned above.

Use `--language en` on the **`prepare-hosted` subcommand**. Its default is Korean, so omitting this flag does not prepare an English package correctly:

```bash
python scripts/selfstudy.py prepare-hosted --language en --kind runtime --package "YOUR-ENGLISH-PACKAGE-PATH" --name hosted-en
```

If package and preparation languages differ, the helper stops; it does not automatically convert the profile to Korean.

The helper reuses the saved project ID/location and derives the owned service name `<prefix>-hosted-en`. It prints the new folder and deployment commands.

> [!NOTE]
> `prepare-hosted` prepares **only a local manifest and azd environment** attached to your existing project. It does not provision, deploy, or invoke a model. You do not need another Foundry project.

The destination must be new and independent of any existing azd project. Use a new `--run` when a preparation folder already exists; do not overwrite it.

The generated `azure.yaml` must contain **the existing project binding and only the intended Hosted service**. Do not add model deployments or turn the whole source repository into a service.

### Values to copy from preparation

Use the helper's exact service name and absolute folder path in subsequent commands.

> [!IMPORTANT]
> **Do not immediately execute the printed deployment commands.** Identify each value's source, then follow **section 4's local check → section 5's remote deployment**.

| Value for the next command | Copy from | Do not substitute |
|---|---|---|
| `--package` | Section 2's returned `.build/...` package path | Repository root or `.selfstudy` folder |
| Service after `azd deploy`/`show` | The full **`Service:`** value printed by `prepare-hosted` | Only the short `hosted-en` suffix passed to `--name` |
| `--cwd` | The same output's absolute **`Directory:`** value | Package folder or path to the `azure.yaml` file |
| Remote `--version` | Section 5's actual **`version` value** from `show` | Prompt name `v2`, package name, or guessed `latest` |
| Role-assignment identity | That version's **`instance_identity.principal_id`** from `show` | Your user ID or a Client ID |

Replace only placeholders inside quotes and keep the quotes. Keep the terminal in the workshop root even when using `--cwd`.

Use **that deployment's returned values** for section 7's workflow and each new deployment in 10/12.

### Find values after closing the terminal output

1. Open the relevant `azure.yaml` under `.selfstudy/`. Read its service name from `name` and `services`.
2. Use the **absolute path of the folder containing that file** as `--cwd`.
3. Query the actual version with section 5's `show`. No separate notes file is needed.

**Before the local request, check:** service name, `main.py`, Python 3.13, Responses protocol, actual endpoint/model, and remote `managed-identity` authentication.

## 4. Make a real local request

### Terminal A: start the server

Leave terminal A running in the v1.3 root. See [using two terminals](checkpoints.md#chapters-with-two-terminals).

```bash
python scripts/workshop.py --language en serve
```

### Terminal B: check readiness, then invoke

Open terminal B in the same root and activate `.venv` there too. The Python readiness check works on macOS/Linux and PowerShell:

```bash
python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8088/readiness', timeout=10).read().decode())"
```

**Check:** the status must be `healthy`. Otherwise, inspect terminal A's server log before sending the request below.

**Send the model request after checking readiness**

```bash
azd ai agent invoke --cwd "YOUR-HOSTED-ABSOLUTE-PATH" --local --port 8088 --new-session --new-conversation --timeout 120 "What is the domestic business-trip lodging limit for September 2026, and what is the source?"
```

**Distinguish the two results.**

| Result | Meaning |
|---|---|
| `healthy` | The local server is ready to receive requests |
| Actual answer and evidence | Model inference succeeded |

> [!WARNING]
> **The local server still incurs Azure model charges.** Local execution does not mean free or offline execution.

**Stop:** after verification, use `Ctrl+C` in A to stop your server.

## 5. Deploy remotely

Verify subscription, project, service, and code/session costs, then deploy **only that service**:

```bash
azd deploy "YOUR-AGENT-SERVICE-NAME" --cwd "YOUR-HOSTED-ABSOLUTE-PATH"
```

**Read the deployed version and runtime identity**

```bash
azd ai agent show "YOUR-AGENT-SERVICE-NAME" --cwd "YOUR-HOSTED-ABSOLUTE-PATH" --output json
```

**Values to inspect:** the actual new `name`, `version`, `status`, and endpoint.

If deployment failed, an older active version is not evidence that this deployment succeeded.

### Runtime roles

The **`instance_identity.principal_id`** returned by `show` is not your user, the agent's name, or a client ID.

```bash
python scripts/selfstudy.py roles --user-object-id "YOUR-USER-OBJECT-ID" --hosted-principal-id "ACTUAL-INSTANCE-IDENTITY-PRINCIPAL-ID"
```

This prints a **role-assignment plan**; it has not executed the assignments.

Match the identity to the actual deployed name/version, then grant only the required resource-scoped roles, such as Foundry User. Local `az login` does not grant permissions to the remote runtime.

## 6. Invoke the exact remote version

```bash
azd ai agent invoke --cwd "YOUR-HOSTED-ABSOLUTE-PATH" --version "ACTUAL-NEW-VERSION" --new-session --new-conversation --timeout 270 "What advance approval is required for a KRW 170000 hotel on a domestic business trip in September 2026?"
```

**Check:** record the real answer, citations, session, conversation, and trace IDs. One successful request does not replace the full quality evaluation in 07.

If you do not plan to reuse it, stop **only the session you just created**:

```bash
azd ai agent sessions list --cwd "YOUR-HOSTED-ABSOLUTE-PATH" --limit 10
```

**Stop only your session identified in the list**

```bash
azd ai agent sessions stop "YOUR-ACTUAL-SESSION-ID" --cwd "YOUR-HOSTED-ABSOLUTE-PATH"
```

> [!WARNING]
> **Stopping ends compute but does not delete persistent volumes.** Review remaining storage charges and deletion decisions in [15](15-capstone-cleanup.md). In retention mode, keep agents, versions, and volumes.

## 7. Repeat with a workflow

After 05's `workflow-agent` succeeds:

```bash
python scripts/workshop.py --script package-hosted --language en --kind workflow --pattern sequential --retrieval local --prompt v2 --api project-responses --protocol responses
```

Prepare the **new profile's package path** under a separate name and folder:

```bash
python scripts/selfstudy.py prepare-hosted --language en --kind runtime --package "ACTUAL-ENGLISH-WORKFLOW-PACKAGE-PATH" --name workflow-en
```

Repeat sections 4–6 using the printed service/folder.

For the matching local workflow profile, use this instead of the plain `serve` command:

```bash
python scripts/workshop.py --language en serve --kind workflow --pattern sequential --retrieval local --prompt v2 --api project-responses --protocol responses
```

**Keep the execution steps, but use the workflow's values.**

| Item | What to do for the workflow |
|---|---|
| Earlier server | Stop it with `Ctrl+C` first |
| Terminal A | Run the workflow-profile server above |
| Terminal B and remote deployment | Use the newly printed workflow service and folder |

Do not substitute the single-agent package or an older remote version.

## Completion check

- [ ] I distinguished the package, deployment folder, and service name, using actual returned values.
- [ ] I checked local readiness and real model inference separately.
- [ ] I verified the new remote version's response or recorded blocked status, and stopped sessions I created.
- [ ] I did not mix the workflow and single-agent profiles.

Preserve the Hosted folder, exact version, and session stop/retention status.

---

[← 07. Evaluation](07-evaluation.md) · [Course home](../../README.md#curriculum) · [09. Operations →](09-operations.md) · [Chapter map ↑](#chapter-map)
