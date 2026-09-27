"""Lab 02 minimal recipe: one billable Responses call through a Foundry project.

Standalone: needs only azure-ai-projects, azure-identity, openai and python-dotenv.
Reads AZURE_AI_PROJECT_ENDPOINT and AZURE_AI_MODEL_DEPLOYMENT_NAME from the environment or .env.
"""

import json
import os
import sys

from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv


def ask(client, deployment: str, question: str) -> dict:
    response = client.responses.create(model=deployment, input=question, store=False)
    if response.status != "completed" or not response.output_text.strip():
        raise SystemExit(f"No completed text (status={response.status}); no fallback was used.")
    return {
        "text": response.output_text,
        "response_id": response.id,
        # The OpenAI Python SDK documents `_request_id` as a public property.
        "request_id": response._request_id,
        "response_model": response.model,
    }


def main() -> None:
    load_dotenv()  # Existing environment variables win over .env values.
    # Pin the lab subscription so a multi-account Azure CLI does not pick another tenant.
    subscription = os.environ.get("AZURE_SUBSCRIPTION_ID") or None
    question = " ".join(sys.argv[1:]) or "Explain Microsoft Foundry in two sentences."
    with (
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=AzureCliCredential(subscription=subscription),
        ) as project,
        project.get_openai_client() as client,
    ):
        result = ask(client, os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"], question)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
