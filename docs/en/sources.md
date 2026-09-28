# Official sources and verification scope

**English** | [한국어](../sources.md) · [Course home](../../README.md)

The repository includes workshop code, synthetic data, packaging tools, and tests. Use these sources to verify product details.

| Topic | Official source |
|---|---|
| Foundry concepts | [Overview](https://learn.microsoft.com/azure/foundry/what-is-foundry) |
| Project creation | [Create projects](https://learn.microsoft.com/azure/foundry/how-to/create-projects) |
| Roles and managed identities | [Foundry RBAC](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry) |
| Models and regions | [Models sold by Azure](https://learn.microsoft.com/azure/ai-foundry/foundry-models/concepts/models-sold-directly-by-azure), [Regions](https://learn.microsoft.com/azure/foundry/reference/region-support) |
| Default Sol, optional Luna, GPT-5.5 judge | [Model roles and actual aliases](model-selection.md), [Reasoning](https://learn.microsoft.com/azure/foundry/openai/how-to/reasoning) |
| SDK and Responses API | [Quickstart](https://learn.microsoft.com/azure/foundry/quickstarts/get-started-code) |
| File Search and functions | [File Search](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/file-search), [Function calling](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/function-calling) |
| Search creation/authentication | [Create Search](https://learn.microsoft.com/azure/search/search-create-service-portal), [RBAC](https://learn.microsoft.com/azure/search/search-security-enable-roles) |
| Retrieval feature plans | [Semantic ranker](https://learn.microsoft.com/azure/search/semantic-how-to-enable-disable), [Knowledge retrieval](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-enable-disable) |
| Evaluation and tracing | [Evaluation](https://learn.microsoft.com/azure/foundry/how-to/evaluate-generative-ai-app), [Tracing](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup) |
| Managed AI red-teaming regions—conflicting descriptions | [Regional matrix](https://learn.microsoft.com/azure/foundry/concepts/evaluation-regions-limits-virtual-network#supported-regions-for-ai-red-teaming), [Concept overview](https://learn.microsoft.com/azure/foundry/concepts/ai-red-teaming-agent#agentic-risks)—NC is common; see [13](13-governance.md) for the discrepancy |
| Function availability versus execution layer | [Agent Service tool/region/model table](https://learn.microsoft.com/azure/foundry/agents/concepts/limits-quotas-regions#tool-support-by-region-and-model) — distinguish NC Function no from actual local MAF calls |
| Hosted and CI/CD | [Hosted](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent), [CI/CD](https://learn.microsoft.com/azure/foundry/agents/quickstarts/set-up-cicd-hosted-agent) |
| Pricing | [Azure OpenAI](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/), [Search](https://azure.microsoft.com/pricing/details/search/) |

## What is included?

Runtime versions are pinned in [pyproject.toml](../../pyproject.toml) and [requirements.lock.txt](../../requirements.lock.txt). Use Python 3.13 and one `.venv` for installation.

See [LICENSE](../../LICENSE). Product names, APIs, model versions, and this workshop's version are separate.

English localization preserves policy IDs, KRW limits, dates, and decision rules. See [Data and localization](data-format.md); neither language is an error fallback for the other.

## How should results be interpreted?

**Local checks are not live Azure exercises.** Tests validate code, request shapes, and input contracts. Actual permissions, model quality, deployment, and traces require your own Azure evidence.

```bash
python scripts/check_workshop.py
python -m unittest discover -s tests -v
python -m unittest discover -s tests_sdk -t . -v
```

`selfstudy configure/resource` reads Azure metadata. `roles` prints commands without assigning anything. `prepare-hosted` and `capture` each accept a subcommand-specific `--language en`; both default to Korean. `capture` calls Hosted only after `--confirm-cost` and preserves raw output for separate verification.

Availability, quota, Preview access, UI, and prices can change. The source guide's review date is **2026-09-27**; this does not guarantee support in every subscription. Model/API observations are documented as environment-specific findings, not as proof that your own lab has completed.
