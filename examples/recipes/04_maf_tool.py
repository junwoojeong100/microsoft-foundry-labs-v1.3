"""Lab 04 minimal recipe: a local MAF agent with one read-only function tool (billable model call).

The tool reads the bundled English synthetic policies. Korean learners can set
WORKSHOP_POLICIES_FILE=data/knowledge/policies.json. An empty result means "no evidence".
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

POLICIES = Path(
    os.environ.get("WORKSHOP_POLICIES_FILE")
    or Path(__file__).resolve().parents[2] / "data/knowledge/en/policies.json"
)


@tool(approval_mode="never_require")
def lookup_policy(query: str) -> str:
    """Search the synthetic travel policies. Read-only; no real company data or actions."""
    words = {word.lower().strip(".,?") for word in query.split() if len(word) > 2}
    policies = json.loads(POLICIES.read_text(encoding="utf-8"))
    matches = [
        p for p in policies if words & set((p["title"] + " " + p["content"]).lower().split())
    ]
    return json.dumps(matches, ensure_ascii=False)  # Empty means no evidence, not a fallback.


def build_agent(chat_client) -> Agent:
    return Agent(
        client=chat_client,
        name="PolicyGuide",
        instructions=(
            "Call lookup_policy first and cite policy IDs. If it returns no policy, say the "
            "evidence is missing. Never approve, book or pay."
        ),
        tools=[lookup_policy],
    )


async def main() -> None:
    load_dotenv()
    # Pin the lab subscription so a multi-account Azure CLI does not pick another tenant.
    subscription = os.environ.get("AZURE_SUBSCRIPTION_ID") or None
    question = " ".join(sys.argv[1:]) or "Can I book a KRW 170000 hotel in September 2026?"
    async with AzureCliCredential(subscription=subscription) as credential:
        client = FoundryChatClient(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        )
        async with build_agent(client) as agent:
            result = await agent.run(question)
    print(result.text)


if __name__ == "__main__":
    asyncio.run(main())
