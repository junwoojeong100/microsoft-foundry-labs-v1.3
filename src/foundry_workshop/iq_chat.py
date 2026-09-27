import os
import subprocess
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

from .compatibility import FOUNDRY_IQ_PREVIEW
from .contracts import (
    digest,
    load_documents,
    parse_json,
    read_json,
    safe_label,
    validate_question,
    write_json,
)
from .knowledge import evidence
from .profiles import RuntimeProfile, validate_inference_endpoint
from .search import IQ_API, SearchGateway, asset_name, search_configuration
from .settings import Settings, owned_prefix, require_env

CHAT_API = FOUNDRY_IQ_PREVIEW.version
# Search knowledge bases accepted no GPT-6 model on 2026-09-23 ("Unsupported model type"), so the
# optional IQ Chat preset stays on the listed gpt-5.6-luna model instead of the answer model.
CHAT_MODEL = "gpt-5.6-luna"
CHAT_DEPLOYMENT = "gpt-5.6-luna"
CHAT_MODEL_VERSION = "2026-07-09"
COGNITIVE_SERVICES_USER = "a97b65f3-24c7-4388-baec-2e87135dc908"


def chat_name(settings: Settings) -> str:
    name = asset_name("AZURE_SEARCH_CHAT_KNOWLEDGE_BASE_NAME", f"chat-{settings.language}-kb")
    if not name.startswith(owned_prefix() + "-"):
        raise ValueError("The IQ chat base must be within WORKSHOP_PREFIX.")
    return name


def definition(settings: Settings, name: str, source: str) -> dict[str, Any]:
    validate_inference_endpoint(
        settings, RuntimeProfile(api="account-chat", language=settings.language)
    )
    return {
        "name": name,
        "description": "Synthetic workshop IQ chat preset. No company data or business actions.",
        "knowledgeSources": [{"name": source}],
        "models": [
            {
                "kind": "azureOpenAI",
                "azureOpenAIParameters": {
                    "resourceUri": settings.openai_endpoint,
                    "deploymentId": CHAT_DEPLOYMENT,
                    "modelName": CHAT_MODEL,
                    "authIdentity": None,
                },
            }
        ],
        "retrievalReasoningEffort": {"kind": "low"},
        "outputMode": "answerSynthesis",
    }


def validate_definition(actual: Any, expected: dict[str, Any]) -> None:
    if not isinstance(actual, dict) or actual.get("name") != expected["name"]:
        raise ValueError("The IQ chat base identity differs from the requested preset.")
    sources = actual.get("knowledgeSources")
    if (
        not isinstance(sources, list)
        or any(not isinstance(item, dict) for item in sources)
        or [item.get("name") for item in sources]
        != [item["name"] for item in expected["knowledgeSources"]]
    ):
        raise ValueError("The IQ chat base references a different knowledge source.")
    models = actual.get("models")
    if not isinstance(models, list) or len(models) != 1 or not isinstance(models[0], dict):
        raise ValueError("The IQ chat preset requires exactly one configured Luna model.")
    parameters = models[0].get("azureOpenAIParameters")
    wanted = expected["models"][0]["azureOpenAIParameters"]
    if (
        models[0].get("kind") != "azureOpenAI"
        or not isinstance(parameters, dict)
        or parameters.get("deploymentId") != wanted["deploymentId"]
        or parameters.get("modelName") != wanted["modelName"]
        or not isinstance(parameters.get("resourceUri"), str)
        or parameters["resourceUri"].rstrip("/") != wanted["resourceUri"]
        or parameters.get("apiKey") is not None
        or parameters.get("authIdentity") is not None
        or actual.get("retrievalReasoningEffort") != {"kind": "low"}
        or actual.get("outputMode") != "answerSynthesis"
        or any(
            actual.get(key) is not None
            for key in ("retrievalInstructions", "answerInstructions", "retrieveDefaults")
        )
    ):
        raise ValueError(
            "IQ chat configuration differs from the fixed Luna/system-assigned/low/answerSynthesis preset. "
            "Do not overwrite it or choose a fallback model; ask the environment owner to review it."
        )


def az_json(arguments: list[str]) -> Any:
    completed = subprocess.run(
        ["az", *arguments, "--output", "json"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode:
        raise ValueError(
            "The read-only IQ readiness check failed. Check the selected subscription, resource group "
            "and ARM/role-assignment read permissions. No resource or role was changed. "
            + completed.stderr.strip()[:1000]
        )
    return parse_json(completed.stdout)


def check_model(settings: Settings) -> dict[str, Any]:
    from .cloud import doctor_cloud

    if settings.auth_mode != "cli":
        raise ValueError(
            "Run the IQ chat preset from the local CLI environment, not a Hosted runtime."
        )
    account_name = require_env("AZURE_AI_ACCOUNT_NAME")
    if urlsplit(settings.openai_endpoint).hostname != f"{account_name}.openai.azure.com".lower():
        raise ValueError(
            "AZURE_AI_ACCOUNT_NAME must identify the same account as AZURE_OPENAI_ENDPOINT."
        )
    preflight = doctor_cloud(replace(settings, deployment=CHAT_DEPLOYMENT))
    deployment = preflight.get("deployment") if isinstance(preflight, dict) else None
    model = deployment.get("model") if isinstance(deployment, dict) else None
    if (
        not isinstance(deployment, dict)
        or deployment.get("name") != CHAT_DEPLOYMENT
        or deployment.get("state") != "Succeeded"
        or not isinstance(model, dict)
        or model.get("name") != CHAT_MODEL
        or model.get("version") != CHAT_MODEL_VERSION
    ):
        raise ValueError(
            f"Prepare Succeeded deployment {CHAT_DEPLOYMENT} with model {CHAT_MODEL} version {CHAT_MODEL_VERSION}. "
            "This dated preset never silently substitutes a different model/version."
        )
    return deployment


def check(root: Path, settings: Settings) -> dict[str, Any]:
    configuration = search_configuration()
    name = chat_name(settings)
    expected = definition(settings, name, configuration["source"])
    deployment = check_model(settings)
    subscription = require_env("AZURE_SUBSCRIPTION_ID")
    resource_group = require_env("AZURE_RESOURCE_GROUP")
    search_group = os.environ.get("AZURE_SEARCH_RESOURCE_GROUP", "").strip() or resource_group
    service_name = urlsplit(configuration["endpoint"]).hostname.split(".")[0]
    service = az_json(
        [
            "search",
            "service",
            "show",
            "--subscription",
            subscription,
            "--resource-group",
            search_group,
            "--name",
            service_name,
            "--query",
            "{id:id,identity:identity,sku:sku.name}",
        ]
    )
    identity = service.get("identity") if isinstance(service, dict) else None
    principal = identity.get("principalId") if isinstance(identity, dict) else None
    identity_type = identity.get("type") if isinstance(identity, dict) else None
    sku = service.get("sku") if isinstance(service, dict) else None
    if (
        not isinstance(principal, str)
        or not isinstance(identity_type, str)
        or "SystemAssigned" not in {part.strip() for part in identity_type.split(",")}
        or not isinstance(sku, str)
        or sku.casefold()
        not in {
            "basic",
            "standard",
            "standard2",
            "standard3",
            "storage_optimized_l1",
            "storage_optimized_l2",
        }
    ):
        raise ValueError(
            "The fixed IQ chat preset needs Basic-or-higher Search with a system-assigned identity."
        )
    try:
        UUID(principal)
    except ValueError as exc:
        raise ValueError("The Search system-assigned principal ID is not a valid UUID.") from exc
    account_id = az_json(
        [
            "cognitiveservices",
            "account",
            "show",
            "--subscription",
            subscription,
            "--resource-group",
            resource_group,
            "--name",
            require_env("AZURE_AI_ACCOUNT_NAME"),
            "--query",
            "id",
        ]
    )
    expected_account_id = (
        f"/subscriptions/{subscription}/resourceGroups/{resource_group}"
        f"/providers/Microsoft.CognitiveServices/accounts/{require_env('AZURE_AI_ACCOUNT_NAME')}"
    )
    if not isinstance(account_id, str) or account_id.casefold() != expected_account_id.casefold():
        raise ValueError(
            "The model account lookup did not return the configured training account's resource ID."
        )
    assignments = az_json(
        [
            "role",
            "assignment",
            "list",
            "--subscription",
            subscription,
            "--scope",
            account_id,
            "--include-inherited",
            "--query",
            f"[?principalId=='{principal}'].roleDefinitionId",
        ]
    )
    if not isinstance(assignments, list) or not any(
        isinstance(item, str) and item.rsplit("/", 1)[-1].lower() == COGNITIVE_SERVICES_USER
        for item in assignments
    ):
        raise ValueError(
            "The documented Cognitive Services User assignment was not found for Search identity "
            f"{principal} on the model account. Ask the owner to grant or review equivalent access; "
            "the workshop does not assign roles."
        )
    with SearchGateway(settings) as gateway:
        source = gateway.request("GET", f"knowledgesources('{gateway.source}')", api=IQ_API)
        source.raise_for_status()
        value = source.json()
        parameters = value.get("searchIndexParameters") if isinstance(value, dict) else None
        if (
            not isinstance(value, dict)
            or value.get("kind") != "searchIndex"
            or not isinstance(parameters, dict)
            or parameters.get("searchIndexName") != gateway.index
        ):
            raise ValueError("The configured source is not the intended synthetic Search index.")
        existing = gateway.request("GET", f"knowledgebases('{name}')", api=CHAT_API)
        if existing.status_code == 404:
            configured = False
        else:
            existing.raise_for_status()
            validate_definition(existing.json(), expected)
            configured = True
    return {
        "check": "read-only-iq-chat-preset",
        "language": settings.language,
        "ready_for_setup": True,
        "configured": configured,
        "knowledge_base": name,
        "preset": expected,
        "model_deployment": deployment,
        "model_version": CHAT_MODEL_VERSION,
        "api_version": CHAT_API,
        "search_identity": principal,
        "role_scope": account_id,
        "model_inference_verified": False,
        "cloud_changes": False,
        "next_step": "iq-chat ask --label <new-label> --confirm-cost"
        if configured
        else "iq-chat setup --confirm-create",
    }


def setup(root: Path, settings: Settings, *, confirmed: bool) -> dict[str, Any]:
    if not confirmed:
        raise ValueError(
            "IQ chat setup creates an owned Preview base; explicitly pass --confirm-create."
        )
    readiness = check(root, settings)
    configuration = search_configuration()
    path = f"knowledgebases('{readiness['knowledge_base']}')"
    ledger_path = root / "outputs/azure-objects.json"
    if not ledger_path.is_file():
        raise ValueError("Run the documented seed-search --iq step in this workshop copy first.")
    ledger = read_json(ledger_path)
    if (
        not isinstance(ledger, dict)
        or not isinstance(ledger.get("objects"), list)
        or any(
            not isinstance(item, dict)
            or not isinstance(item.get("path"), str)
            or not isinstance(item.get("api_version"), str)
            for item in ledger["objects"]
        )
        or ledger.get("scope")
        != {"search_endpoint": configuration["endpoint"], "prefix": owned_prefix()}
        or ledger.get("corpus_hash") != digest(load_documents(root, settings.language))
        or (f"knowledgesources('{configuration['source']}')", IQ_API)
        not in {(item["path"], item["api_version"]) for item in ledger["objects"]}
    ):
        raise ValueError("The synthetic source ownership/corpus does not match this workshop copy.")
    recorded = [item for item in ledger["objects"] if item["path"] == path]
    if any(item["api_version"] != CHAT_API for item in recorded):
        raise ValueError("The existing chat-base ownership record uses a different API version.")
    owned = bool(recorded)
    if readiness["configured"] and not owned:
        raise ValueError(
            "An existing IQ chat base is not owned by this local ledger; do not overwrite it."
        )
    created = False
    if not readiness["configured"]:
        with SearchGateway(settings) as gateway:
            response = gateway.request(
                "PUT", path, api=CHAT_API, body=readiness["preset"], create_only=True
            )
            response.raise_for_status()
            if not owned:
                ledger["objects"].append({"path": path, "api_version": CHAT_API})
                write_json(ledger_path, ledger)
            saved = gateway.request("GET", path, api=CHAT_API)
            saved.raise_for_status()
            validate_definition(saved.json(), readiness["preset"])
        created = True
    return {
        **readiness,
        "configured": True,
        "created": created,
        "cloud_changes": created,
        "existing_ga_base_modified": False,
        "model_deployments_or_roles_created": False,
        "next_step": "iq-chat ask --label <new-label> --confirm-cost",
    }


def request_body(question: str, source: str) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": validate_question(question)}]}
        ],
        "retrievalReasoningEffort": {"kind": "low"},
        "outputMode": "answerSynthesis",
        "includeActivity": True,
        "maxRuntimeInSeconds": 60,
        "maxOutputSize": 6000,
        "knowledgeSourceParams": [
            {
                "kind": "searchIndex",
                "knowledgeSourceName": source,
                "includeReferences": True,
                "includeReferenceSourceData": True,
            }
        ],
    }


def parse_response(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("IQ chat returned an invalid response object.")
    if payload.get("error") is not None:
        raise ValueError("IQ chat returned a service error, not a successful answer.")
    activity, references = payload.get("activity"), payload.get("references")
    if (
        not isinstance(activity, list)
        or not isinstance(references, list)
        or any(not isinstance(item, dict) or item.get("error") for item in activity)
    ):
        raise ValueError("IQ chat did not return complete, error-free activity and references.")
    calls = [
        item
        for item in activity
        if item.get("type") in {"modelQueryPlanning", "modelAnswerSynthesis"}
    ]
    if {item["type"] for item in calls} != {"modelQueryPlanning", "modelAnswerSynthesis"} or any(
        not isinstance(item.get("model"), dict)
        or item["model"].get("modelName") != CHAT_MODEL
        or item["model"].get("deploymentId") != CHAT_DEPLOYMENT
        for item in calls
    ):
        raise ValueError("Actual IQ planning/synthesis did not match the fixed Luna preset.")
    documents = {}
    for reference in references:
        if not isinstance(reference, dict) or not isinstance(reference.get("sourceData"), dict):
            raise ValueError("IQ chat must return actual reference sourceData.")
        document = reference["sourceData"]
        identifier = document.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError("IQ chat evidence is missing a stable document ID.")
        if identifier in documents and documents[identifier] != document:
            raise ValueError("Conflicting evidence was returned for the same document ID.")
        documents[identifier] = document
    context = evidence(
        list(documents.values()), "foundry-iq-chat", references=references, activity=activity
    )
    responses = payload.get("response")
    if not isinstance(responses, list):
        raise ValueError("IQ chat has no answer response.")
    texts = []
    for message in responses:
        if not isinstance(message, dict) or not isinstance(message.get("content"), list):
            raise ValueError("IQ chat returned an invalid answer message.")
        for content in message["content"]:
            if not isinstance(content, dict):
                raise ValueError("IQ chat returned invalid answer content.")
            if content.get("type") == "text":
                if not isinstance(content.get("text"), str):
                    raise ValueError("IQ chat returned non-text answer content.")
                texts.append(content["text"])
    text = "\n".join(texts)
    if not text.strip() or not context["documents"]:
        raise ValueError("IQ chat returned no answer or no original evidence.")
    return {"answer": text, **context}


def validate_corpus_evidence(root: Path, documents: list[dict[str, Any]], language: str) -> None:
    canonical = {item["id"]: item for item in load_documents(root, language)}
    if not documents:
        raise ValueError("IQ chat must return actual canonical synthetic evidence.")
    for document in documents:
        original = canonical.get(document["id"])
        # The source can project only id/title/content; never fill unreturned date fields.
        if original is None or any(
            key not in original or value != original[key] for key, value in document.items()
        ):
            raise ValueError(
                "IQ chat returned evidence outside the selected canonical synthetic language corpus."
            )


def ask(
    root: Path, settings: Settings, question: str, label: str, *, confirmed: bool
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError(
            "IQ Chat calls a billable planning/answer model; explicitly pass --confirm-cost."
        )
    import httpx
    from azure.core.exceptions import AzureError

    name = chat_name(settings)
    configuration = search_configuration()
    expected = definition(settings, name, configuration["source"])
    body = request_body(question, configuration["source"])
    directory = root / "outputs/iq-chat" / safe_label(label)
    directory.mkdir(parents=True, exist_ok=False)
    write_json(directory / "request.json", body)
    stage = "model-preflight"
    try:
        deployment = check_model(settings)
        write_json(directory / "model-preflight.json", deployment)
        stage = "knowledge-base-preflight"
        with SearchGateway(settings) as gateway:
            saved = gateway.request("GET", f"knowledgebases('{name}')", api=CHAT_API)
            write_json(
                directory / "knowledge-base-response.json",
                {"status_code": saved.status_code, "body": saved.text},
            )
            saved.raise_for_status()
            validate_definition(saved.json(), expected)
            stage = "retrieve"
            response = gateway.request(
                "POST", f"knowledgebases('{name}')/retrieve", api=CHAT_API, body=body
            )
            write_json(
                directory / "http-response.json",
                {"status_code": response.status_code, "body": response.text},
            )
            response.raise_for_status()
            if response.status_code != 200:
                raise ValueError("A partial IQ chat response is not successful.")
            stage = "response-validation"
            payload = parse_json(response.text)
            write_json(directory / "response.json", payload)
            parsed = parse_response(payload)
            validate_corpus_evidence(root, parsed["documents"], settings.language)
    except (ValueError, OSError, subprocess.SubprocessError, httpx.HTTPError, AzureError) as exc:
        write_json(
            directory / "failure.json",
            {
                "status": "failed",
                "stage": stage,
                "error_type": type(exc).__name__,
                "message": str(exc),
                "fallback_used": False,
            },
        )
        raise
    result = {
        "mode": "live",
        "language": settings.language,
        "knowledge_base": name,
        "api_version": CHAT_API,
        "model": CHAT_MODEL,
        "deployment": CHAT_DEPLOYMENT,
        "model_deployment": deployment,
        "authentication": "search-system-assigned-identity",
        **parsed,
        "recorded_at": datetime.now(UTC).isoformat(),
        "request_hash": digest(body),
        "response_hash": digest(payload),
        "model_planning_verified": True,
        "model_synthesis_verified": True,
        "output_directory": str(directory),
        "note": "A real IQ chat integration check, not a benchmark score or business approval.",
    }
    write_json(directory / "summary.json", result)
    return result
