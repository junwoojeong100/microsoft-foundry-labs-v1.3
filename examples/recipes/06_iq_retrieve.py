"""Lab 06 minimal recipe: GA Foundry IQ knowledge base retrieval over REST (no model call).

Uses the GA contract checked on 2026-09-24 (api-version 2026-04-01, minimal/extractive retrieval).
Needs AZURE_SEARCH_ENDPOINT plus the knowledge base/source names (defaults: <WORKSHOP_PREFIX>-kb/-source).
"""

import json
import os
import sys

import httpx
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

IQ_GA_API = "2026-04-01"


def retrieve(http: httpx.Client, endpoint: str, kb: str, source: str, token: str, question: str):
    response = http.post(
        f"{endpoint.rstrip('/')}/knowledgebases('{kb}')/retrieve",
        params={"api-version": IQ_GA_API},
        headers={"Authorization": f"Bearer {token}"},
        json={
            "intents": [{"type": "semantic", "search": question}],
            "includeActivity": True,
            "knowledgeSourceParams": [
                {"kind": "searchIndex", "knowledgeSourceName": source, "includeReferences": True}
            ],
        },
    )
    response.raise_for_status()  # An error is a finding; never switch to plain Search silently.
    payload = response.json()
    return {
        "references": [item.get("docKey") for item in payload.get("references", [])],
        "activity": [item.get("type") for item in payload.get("activity", [])],
    }


def main() -> None:
    load_dotenv()
    # Pin the lab subscription so a multi-account Azure CLI does not pick another tenant.
    subscription = os.environ.get("AZURE_SUBSCRIPTION_ID") or None
    prefix = os.environ.get("WORKSHOP_PREFIX", "").strip()
    kb = os.environ.get("AZURE_SEARCH_KNOWLEDGE_BASE_NAME") or f"{prefix}-kb"
    source = os.environ.get("AZURE_SEARCH_KNOWLEDGE_SOURCE_NAME") or f"{prefix}-source"
    question = " ".join(sys.argv[1:]) or "Domestic lodging limit for September 2026"
    credential = AzureCliCredential(subscription=subscription)
    token = credential.get_token("https://search.azure.com/.default").token
    with httpx.Client(timeout=90) as http:
        result = retrieve(http, os.environ["AZURE_SEARCH_ENDPOINT"], kb, source, token, question)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
