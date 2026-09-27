from pathlib import Path
from typing import Any

from .contracts import digest, load_documents, parse_json, read_json, safe_label, write_json
from .generation import response_options
from .search import SEARCH_API, search_configuration
from .settings import Settings
from .toolbox import QUESTIONS, require_synthetic_index


def specification() -> dict[str, Any]:
    configuration = search_configuration()
    return {
        "openapi": "3.1.0",
        "info": {"title": "Owned synthetic policy lookup", "version": "1.0.0"},
        "servers": [{"url": configuration["endpoint"]}],
        "paths": {
            f"/indexes/{configuration['index']}/docs/search": {
                "post": {
                    "operationId": "SearchSyntheticPolicies",
                    "description": "Read only the six owned synthetic policies. This POST is a search query, not a document write.",
                    "parameters": [
                        {
                            "name": "api-version",
                            "in": "query",
                            "required": True,
                            "description": f"Always supply the exact query key api-version with value {SEARCH_API}; a schema default does not send it.",
                            "schema": {
                                "type": "string",
                                "enum": [SEARCH_API],
                                "default": SEARCH_API,
                            },
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "search": {
                                            "type": "string",
                                            "description": "The synthetic policy question.",
                                        },
                                        "top": {"type": "integer", "enum": [6], "default": 6},
                                        "select": {
                                            "type": "string",
                                            "enum": [
                                                "id,title,content,effective_from,effective_to"
                                            ],
                                            "default": "id,title,content,effective_from,effective_to",
                                        },
                                    },
                                    "required": ["search", "top", "select"],
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Actual Search results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "value": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        key: {"type": "string"}
                                                        for key in (
                                                            "id",
                                                            "title",
                                                            "content",
                                                            "effective_from",
                                                            "effective_to",
                                                        )
                                                    },
                                                },
                                            }
                                        },
                                        "required": ["value"],
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }


def plan(settings: Settings) -> dict[str, Any]:
    spec = specification()
    tool = {
        "type": "openapi",
        "openapi": {
            "name": "synthetic_policy_api",
            "description": "Read-only lookup in the owned synthetic policy index.",
            "spec": spec,
            "auth": {
                "type": "managed_identity",
                "security_scheme": {"audience": "https://search.azure.com"},
            },
        },
    }
    return {
        "mode": "local-openapi-plan",
        "language": settings.language,
        "tool": tool,
        "specification_hash": digest(spec),
        "managed_identity_owner": "foundry-account",
        "required_search_role": "Search Index Data Reader",
        "azure_requests_sent": False,
    }


def invoke(
    client: Any, root: Path, settings: Settings, label: str, *, confirmed: bool
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("The OpenAPI/model request requires --confirm-cost.")
    from .cloud import response_metadata, response_with_payload

    require_synthetic_index(root, settings)
    configuration = plan(settings)
    directory = root / "outputs/openapi-runs" / safe_label(label)
    directory.mkdir(parents=True, exist_ok=False)
    write_json(directory / "plan.json", configuration)
    request = {
        "model": settings.deployment,
        "input": QUESTIONS[settings.language],
        "instructions": (
            "Query the provided synthetic policy API before answering. "
            f"Always supply the required query parameter api-version={SEARCH_API}, "
            "using the exact key api-version. Set top=6 and "
            "select=id,title,content,effective_from,effective_to. "
            "Do not omit required parameters because their schema has a default. "
            "Cite original document IDs and applicable dates. Never approve, book or pay anything."
        ),
        "tool_choice": "required",
        "store": False,
        "extra_body": {"tools": [configuration["tool"]]},
        **response_options(settings),
    }
    write_json(directory / "request.json", request)
    response, raw = response_with_payload(
        client, error_path=directory / "service-error.json", **request
    )
    write_json(directory / "response.json", raw)
    calls = [item for item in raw.get("output", []) if item.get("type") == "openapi_call"]
    if not calls or any(item.get("error") or item.get("status") != "completed" for item in calls):
        raise ValueError(
            "A successful actual OpenAPI call was not observed; no native Search/tool substitution is allowed."
        )
    documents = validate_tool_outputs(raw, root, settings.language)
    result = {
        "mode": "live-openapi-policy-query",
        "language": settings.language,
        "specification_hash": configuration["specification_hash"],
        "request_hash": digest(read_json(directory / "request.json")),
        "openapi_calls": calls,
        "documents": documents,
        "context_hash": digest(documents),
        "answer": response.output_text,
        **response_metadata(response),
        "note": "Managed-identity OpenAPI search, not a native Search Toolbox or IQ invocation.",
    }
    write_json(directory / "summary.json", result)
    return result


def validate_tool_outputs(raw: dict[str, Any], root: Path, language: str) -> list[dict[str, Any]]:
    calls = [item for item in raw.get("output", []) if item.get("type") == "openapi_call"]
    outputs = [item for item in raw.get("output", []) if item.get("type") == "openapi_call_output"]
    ids = [item.get("call_id") for item in calls]
    if (
        not calls
        or any(not isinstance(value, str) or not value for value in ids)
        or len(set(ids)) != len(ids)
        or {item.get("call_id") for item in outputs} != set(ids)
        or len(outputs) != len(calls)
    ):
        raise ValueError("Every actual OpenAPI call needs its matching original tool output.")
    canonical = {item["id"]: item for item in load_documents(root, language)}
    seen = {}
    for output in outputs:
        if output.get("status") != "completed" or output.get("error"):
            raise ValueError("An OpenAPI tool output failed.")
        envelope = parse_json(output["output"])
        if not isinstance(envelope, dict) or not isinstance(envelope.get("response"), str):
            raise ValueError("The OpenAPI tool did not return its actual Search response.")
        response = parse_json(envelope["response"])
        if (
            not isinstance(response, dict)
            or not isinstance(response.get("value"), list)
            or not response["value"]
        ):
            raise ValueError("The OpenAPI Search response is empty or malformed.")
        for item in response["value"]:
            if not isinstance(item, dict) or item.get("id") not in canonical:
                raise ValueError("The OpenAPI tool returned a source outside the synthetic corpus.")
            document = {key: item[key] for key in canonical[item["id"]] if key in item}
            if any(key not in document for key in ("id", "title", "content")) or any(
                value != canonical[item["id"]][key] for key, value in document.items()
            ):
                raise ValueError(
                    "The OpenAPI tool altered or omitted required canonical source content."
                )
            if item["id"] in seen and seen[item["id"]] != document:
                raise ValueError("OpenAPI calls returned conflicting source content.")
            seen[item["id"]] = document
    return [seen[key] for key in sorted(seen)]
