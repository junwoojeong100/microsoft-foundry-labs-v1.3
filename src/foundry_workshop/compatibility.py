"""Dated service API versions used by raw REST calls.

Keep every hard-coded service contract here so a compatibility review has one place to check.
A check date records when the contract was verified for this workshop; it is not a support guarantee.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiContract:
    version: str
    checked: str
    status: str
    source: str


SEARCH_REST = ApiContract(
    version="2024-07-01",
    checked="2026-09-24",
    status="GA keyword search and index management",
    source="https://learn.microsoft.com/rest/api/searchservice/",
)
FOUNDRY_IQ_GA = ApiContract(
    version="2026-04-01",
    checked="2026-09-24",
    status="GA knowledge base retrieval (minimal, extractive)",
    source="https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base",
)
FOUNDRY_IQ_PREVIEW = ApiContract(
    version="2026-08-01-preview",
    checked="2026-09-24",
    status="Preview model planning and answer synthesis",
    source="https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base",
)
FOUNDRY_AGENT_DATA_PLANE = ApiContract(
    version="v1",
    checked="2026-09-24",
    status="GA project data-plane routes without a typed SDK method in the pinned azure-ai-projects",
    source="https://learn.microsoft.com/azure/foundry/agents/how-to/tools/toolbox",
)
A2A_PROTOCOL = ApiContract(
    version="1.0",
    checked="2026-09-24",
    status="A2A protocol header for the agent card; no 0.3 fallback",
    source="https://learn.microsoft.com/azure/foundry/agents/how-to/tools/agent-to-agent",
)

CONTRACTS = {
    "search_rest": SEARCH_REST,
    "foundry_iq_ga": FOUNDRY_IQ_GA,
    "foundry_iq_preview": FOUNDRY_IQ_PREVIEW,
    "foundry_agent_data_plane": FOUNDRY_AGENT_DATA_PLANE,
    "a2a_protocol": A2A_PROTOCOL,
}
