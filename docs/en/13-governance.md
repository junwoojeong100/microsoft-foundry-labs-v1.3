# 13. Lab safety, managed identities, and Control Plane

**English** | [한국어](../13-governance.md) · [Course home](../../README.md)

**Outcome:** Inspect actual interventions by a lab-owned guardrail, and explain caller identities and owned resources.

**Prerequisites:** Your own project, tools, and actual Hosted version. Do not change shared policies, another user's roles, or business data.

## 1. Inspect permission paths

```bash
python scripts/selfstudy.py status
python scripts/workshop.py --language en doctor --cloud
python scripts/workshop.py --language en cleanup-plan
```

Compare with IAM/Identity on each actual Azure resource:

| Connection | Identity |
|---|---|
| Your CLI → Foundry | Your signed-in user |
| Project tools → Search | The selected project managed identity |
| Search → IQ Chat model | Search system-assigned identity |
| Hosted → model/tools | The actual `instance_identity.principal_id` |
| Your trace queries | Your user and its log-reading permissions |

`cleanup-plan` does not delete anything. Owner does not imply all data roles; portal success does not prove Hosted permissions; and correct roles do not guarantee correct answers.

## 2. Create your own RAI/guardrail policy

1. In Foundry **Build → Guardrails → Create**, use a name dedicated to your lab.
2. Preserve default protections and select the controls, intervention points, and blocking behavior to inspect.
3. Verify creation of the actual policy resource and record its full ARM ID.
4. Do not edit `Microsoft.DefaultV2` or policies shared by other models/teams.

If the menu or feature is unavailable, record the limitation. Entering a made-up policy ID is not a completed configuration.

## 3. Attach it to a new version of your Hosted agent

Add the following only to the intended service in the **isolated Hosted folder from 08**. Do not replace the entire YAML:

```yaml
policies:
  - type: rai_policy
    raiPolicyName: <ACTUAL-FULL-POLICY-ARM-ID>
```

After reviewing the new deployment and cost:

```bash
azd deploy "YOUR-AGENT-SERVICE-NAME" --cwd "THAT-HOSTED-ABSOLUTE-PATH"
azd ai agent show "YOUR-AGENT-SERVICE-NAME" --cwd "THAT-HOSTED-ABSOLUTE-PATH" --output json
```

Verify the policy resource, the new agent version's reference, and actual request-level intervention separately. **Leave 12's frozen matrix target unchanged; experiment on 08's separate introductory Hosted agent.**

## 4. Use normal and boundary-test synthetic questions

In new conversations, send only the **question text** from English dev cases D01/D06, using the Hanbit Technology context from 03. Inspect response status, policy-intervention information, and traces.

- Is the policy attached?
- Did a block or other intervention actually occur?
- Is the underlying answer still correct?
- Did you mistake instruction-based refusal for platform filtering?

If no block occurs, record it honestly. Do not expand into harmful inputs or weaken protections to manufacture a result.

## 5. Bounded AI red teaming

If available, open **Red teaming** in your own Prompt Agent's evaluation tab:

1. Select the exact target name/version.
2. Limit risk categories to one relevant behavior, such as **falsely claiming business approval**.
3. Remove unrelated taxonomy behaviors and set small input, strategy, and budget limits.
4. Review, submit once, and read **every actual response and judgment explanation**.
5. If ASR/aggregate scores contradict row-level judgments, record the contradiction rather than editing the numbers.

Without support, permission, or budget, mark it not run. A local D06 test is not a cloud red-team scan.

**Observed validation issue:** selecting five seeds returned only three rows. The service reported **100% ASR and `attack_success: true` while its raw explanations said no prohibited action occurred**; the returned answers refused false approval claims. Preserve requested/actual counts, scores, reasons, and whether inputs were redacted. Do not treat that aggregate as a reliable attack-success rate or safety certification, and do not change the denominator to imply all five requested cases were verified.

## 6. Inventory your lab's Control Plane resources

Match your project's agent names, exact versions, model deployments, connections, policies, and usage with Control Plane and the ownership records. Do not assume an unrecorded resource exists or passed merely because another step succeeded.

Separate read-only observations, the roles/policies you added, and resources you intend to retain. If organizational policy blocks access, preserve the original error and use the approved support process. Do not weaken protections or modify shared resources.

## Completion check

Record added policies, roles, versions, interventions/non-interventions, and unsupported features. Preserve the original configuration so you can reverse only your own changes.

**Next → [14. GitHub OIDC CI/CD lab](14-additional-permissions.md).** If the required GitHub repository permissions are unavailable, record CI as not run.
