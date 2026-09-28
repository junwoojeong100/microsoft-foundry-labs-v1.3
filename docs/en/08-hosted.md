# 08. Local Hosted execution and Azure deployment

**English** | [한국어](../08-hosted.md) · [Course home](../../README.md)

**Outcome:** Package your code, make a real local request, deploy to Foundry, and invoke the exact remote version.

**Prerequisites:** The MAF function exercise from 04, project ARM ID/location from 00, and a working model. **Subscription Owner prepares deployment permissions**; runtime data permissions are separate.

**Order:** package → isolated deployment folder → local response → remote deployment → runtime roles → same-version request and session stop. The package path, deployment folder, and service name are different values; use each actual output directly in the next command.

## 1. Prepare azd Foundry commands

```bash
azd version
azd extension list --installed
```

Install `microsoft.foundry` only if missing:

```bash
azd extension install microsoft.foundry
azd auth login
azd ai agent show --help
```

Check Hosted support and capacity in your subscription/region. If unavailable, mark the chapter blocked; **do not recreate an existing project arbitrarily**. Code deployment does not require local Docker or ACR installation.

If only remote deployment is blocked, sections 1–3's **local preparation folder** can still support later project-connection steps. Retain it if preparation succeeds, while recording remote deployment/invocation as not run. Do not claim the folder is ready if preparation itself failed.

## 2. Build a safe English package

```bash
python scripts/workshop.py --script package-hosted --language en
```

Open `package-manifest.json`, `runtime-profile.json`, and `requirements.txt` at the printed location. The default English package is `.build/hosted-en/`.

Verify code, synthetic policies, and instructions are present, but `.env`, credentials, evaluation answers, and execution results are absent. The frozen runtime profile must contain `language: en`. `cloud_deployed: false` describes **packaging**, not an Azure resource check.

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

The helper reuses the saved project ID/location, derives the owned service name `<prefix>-hosted-en`, and prints its new folder and deployment commands. The destination must be new and independent of any existing azd project. This prepares a local manifest/environment attached to your existing project; it does not provision, deploy, or invoke a model. Use a new `--run` when a preparation folder already exists; do not overwrite it.

The generated `azure.yaml` must contain the existing project binding and only the intended Hosted agent service. Do not add new model deployments or turn the whole source repository into a service. There is no need to provision another Foundry project.

Record the exact service name and absolute folder path. Check `main.py`, Python 3.13, the Responses protocol, actual endpoint/model, and remote `managed-identity` authentication. Use this same service and folder in subsequent commands.

**Do not immediately execute the printed deployment commands.** Use the table below to identify each value's source, complete section 4's local check, then deploy in section 5.

| Value for the next command | Copy from | Do not substitute |
|---|---|---|
| `--package` | Section 2's returned `.build/...` package path | Repository root or `.selfstudy` folder |
| Service after `azd deploy`/`show` | The full **`Service:`** value printed by `prepare-hosted` | Only the short `hosted-en` suffix passed to `--name` |
| `--cwd` | The same output's absolute **`Directory:`** value | Package folder or path to the `azure.yaml` file |
| Remote `--version` | Section 5's actual **`version` value** from `show` | Prompt name `v2`, package name, or guessed `latest` |
| Role-assignment identity | That version's **`instance_identity.principal_id`** from `show` | Your user ID or a Client ID |

Replace only placeholders inside quotes and keep the quotes. Keep the terminal in the workshop root even when using `--cwd`. Use **that deployment's returned values** for section 7's workflow and each new deployment in 10/12.

If the terminal output is gone, open the relevant `azure.yaml` under `.selfstudy/` and read its `name` and `services`. The **absolute path of the folder containing that file** is `--cwd`; query the actual version with `show` below. No separate notes file is needed.

## 4. Make a real local request

Leave terminal A running in the v1.5 root. See [using two terminals](checkpoints.md#chapters-with-two-terminals).

```bash
python scripts/workshop.py --language en serve
```

Open terminal B in the same root and activate `.venv` there too. The Python readiness check works on macOS/Linux and PowerShell:

```bash
python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8088/readiness', timeout=10).read().decode())"
azd ai agent invoke --cwd "YOUR-HOSTED-ABSOLUTE-PATH" --local --port 8088 --new-session --new-conversation --timeout 120 "What is the domestic business-trip lodging limit for September 2026, and what is the source?"
```

If readiness fails, do not invoke. `healthy` means the server is ready; an actual answer with evidence demonstrates inference. The local server still incurs Azure model charges.

After verification, use `Ctrl+C` in A to stop your server.

## 5. Deploy remotely

Verify subscription, project, service, and code/session costs, then deploy **only that service**:

```bash
azd deploy "YOUR-AGENT-SERVICE-NAME" --cwd "YOUR-HOSTED-ABSOLUTE-PATH"
azd ai agent show "YOUR-AGENT-SERVICE-NAME" --cwd "YOUR-HOSTED-ABSOLUTE-PATH" --output json
```

After deployment failure, an older active version is not evidence that this deployment succeeded. Record the actual new `name`, `version`, `status`, and endpoint.

### Runtime roles

The **`instance_identity.principal_id`** returned by `show` is not your user, the agent's name, or a client ID.

```bash
python scripts/selfstudy.py roles --user-object-id "YOUR-USER-OBJECT-ID" --hosted-principal-id "ACTUAL-INSTANCE-IDENTITY-PRINCIPAL-ID"
```

This prints a plan. Match the identity to the **actual deployed name/version**, then grant only the required resource-scoped roles, such as Foundry User. Local `az login` does not grant permissions to the remote runtime.

## 6. Invoke the exact remote version

```bash
azd ai agent invoke --cwd "YOUR-HOSTED-ABSOLUTE-PATH" --version "ACTUAL-NEW-VERSION" --new-session --new-conversation --timeout 270 "What advance approval is required for a KRW 170000 hotel on a domestic business trip in September 2026?"
```

Record the real answer, citations, session, conversation, and trace IDs. One successful request does not replace the full quality evaluation in 07.

If you do not plan to reuse it, stop **only the session you just created**:

```bash
azd ai agent sessions list --cwd "YOUR-HOSTED-ABSOLUTE-PATH" --limit 10
azd ai agent sessions stop "YOUR-ACTUAL-SESSION-ID" --cwd "YOUR-HOSTED-ABSOLUTE-PATH"
```

Stopping ends running compute but does not delete persistent volumes. Review retention and remaining charges in the final chapter. In retention mode, keep agents, versions, and volumes.

## 7. Repeat with a workflow

After 05's `workflow-agent` succeeds:

```bash
python scripts/workshop.py --script package-hosted --language en --kind workflow --pattern sequential --retrieval local --prompt v2 --api project-responses --protocol responses
```

Prepare the **new profile's package path** under a separate name and folder:

```bash
python scripts/selfstudy.py prepare-hosted --language en --kind runtime --package "ACTUAL-ENGLISH-WORKFLOW-PACKAGE-PATH" --name workflow-en
```

Repeat sections 4–6 using the printed service/folder. Do not substitute the single-agent package or an older remote version.

For the matching local workflow profile, use this instead of the plain `serve` command:

```bash
python scripts/workshop.py --language en serve --kind workflow --pattern sequential --retrieval local --prompt v2 --api project-responses --protocol responses
```

Stop the earlier server with `Ctrl+C` first. Terminal B must use the newly printed **workflow service and folder**, not the single-agent service.

**Complete only after verifying each stage:** packaging, local inference, remote deployment, and the remote response. Preserve the Hosted folder, exact version, and session stop/retention status.

**Next → [09. Traces, Insights, and operations](09-operations.md)**
