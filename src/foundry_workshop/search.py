import math
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .compatibility import FOUNDRY_IQ_GA, SEARCH_REST
from .contracts import digest, load_documents, read_json, validate_question, write_json
from .knowledge import evidence
from .settings import Settings, azure_endpoint, credential_for, owned_prefix, require_env

SEARCH_API = SEARCH_REST.version
IQ_API = FOUNDRY_IQ_GA.version
SEARCH_SCOPE = "https://search.azure.com/.default"


def embedding_configuration() -> dict[str, Any]:
    api = os.environ.get("WORKSHOP_EMBEDDING_API", "project")
    if api not in {"project", "account"}:
        raise ValueError("WORKSHOP_EMBEDDING_API must explicitly select project or account.")
    dimensions = int(require_env("WORKSHOP_EMBEDDING_DIMENSIONS"))
    if not 1 <= dimensions <= 65536:
        raise ValueError(
            "WORKSHOP_EMBEDDING_DIMENSIONS must match the verified embedding model (1-65536)."
        )
    return {
        "deployment": require_env("AZURE_AI_EMBEDDING_DEPLOYMENT_NAME"),
        "dimensions": dimensions,
        "field": "content_vector",
        "api": f"{api}-embeddings",
        **(
            {"endpoint": azure_endpoint(require_env("AZURE_OPENAI_ENDPOINT"), "openai")}
            if api == "account"
            else {}
        ),
    }


def embed_texts(
    settings: Settings, texts: list[str], configuration: dict[str, Any]
) -> tuple[list[list[float]], dict[str, Any]]:
    from .cloud import project_clients

    if not texts or any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("Embedding inputs must be a nonempty list of nonempty texts.")
    if configuration["api"] not in {"project-embeddings", "account-embeddings"}:
        raise ValueError("Unknown explicitly selected embedding API.")
    with project_clients(settings, account_api=configuration["api"] == "account-embeddings") as (
        _,
        client,
    ):
        response = client.embeddings.create(model=configuration["deployment"], input=texts)
    vectors = {}
    for item in response.data:
        if (
            type(item.index) is not int
            or not 0 <= item.index < len(texts)
            or item.index in vectors
            or len(item.embedding) != configuration["dimensions"]
            or any(
                type(number) not in (int, float) or not math.isfinite(number)
                for number in item.embedding
            )
        ):
            raise ValueError(
                "Embedding response has missing/duplicate indices, wrong dimensions or invalid numbers."
            )
        vectors[item.index] = item.embedding
    if len(vectors) != len(texts) or not isinstance(response.model, str) or not response.model:
        raise ValueError("Embedding response must preserve every input and the actual model name.")
    return [vectors[index] for index in range(len(texts))], {
        "deployment": configuration["deployment"],
        "api": configuration["api"],
        "observed_model": response.model,
        "dimensions": configuration["dimensions"],
        "usage": response.usage.model_dump(mode="json") if response.usage else None,
    }


def asset_name(variable: str, suffix: str) -> str:
    import os
    import re

    value = os.environ.get(variable, "").strip() or f"{owned_prefix()}-{suffix}"
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value) or len(value) > 100:
        raise ValueError(f"{variable} must be a lowercase Search object name, not a URL.")
    return value


def search_configuration() -> dict[str, Any]:
    configuration: dict[str, Any] = {
        "endpoint": azure_endpoint(require_env("AZURE_SEARCH_ENDPOINT"), "search"),
        "index": asset_name("AZURE_SEARCH_INDEX_NAME", "policies"),
        "source": asset_name("AZURE_SEARCH_KNOWLEDGE_SOURCE_NAME", "source"),
        "knowledge_base": asset_name("AZURE_SEARCH_KNOWLEDGE_BASE_NAME", "kb"),
        "search_api": SEARCH_API,
        "iq_api": IQ_API,
    }
    threshold = os.environ.get("WORKSHOP_IQ_RERANKER_THRESHOLD", "").strip()
    if threshold:
        value = float(threshold)
        if not math.isfinite(value) or not 0 <= value <= 4:
            raise ValueError("WORKSHOP_IQ_RERANKER_THRESHOLD must be a finite value from 0 to 4.")
        configuration["iq_reranker_threshold"] = value
    return configuration


class SearchGateway:
    def __init__(self, settings: Settings):
        import httpx

        self.configuration = search_configuration()
        self.settings = settings
        self.endpoint = self.configuration["endpoint"]
        self.index = self.configuration["index"]
        self.source = self.configuration["source"]
        self.kb = self.configuration["knowledge_base"]
        self.credential = credential_for(settings)
        self.http = httpx.Client(timeout=90, follow_redirects=False)

    def __enter__(self) -> "SearchGateway":
        return self

    def __exit__(self, *_args: Any) -> None:
        self.http.close()
        self.credential.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        api: str,
        body: dict[str, Any] | None = None,
        create_only: bool = False,
    ):
        token = self.credential.get_token(SEARCH_SCOPE)
        headers = {"Authorization": "Bearer " + token.token}
        if create_only:
            headers["If-None-Match"] = "*"
        return self.http.request(
            method,
            f"{self.endpoint}/{path}",
            params={"api-version": api},
            headers=headers,
            json=body,
        )

    def retrieve(self, question: str, provider: str) -> dict[str, Any]:
        validate_question(question)
        if provider in {"search", "hybrid"}:
            body: dict[str, Any] = {
                "search": question,
                "top": 6,
                "select": "id,title,content,effective_from,effective_to",
            }
            embedding = None
            configuration: dict[str, Any] = dict(self.configuration)
            if provider == "hybrid":
                configuration["embedding"] = embedding_configuration()
                vectors, embedding = embed_texts(
                    self.settings, [question], configuration["embedding"]
                )
                body["vectorQueries"] = [
                    {
                        "kind": "vector",
                        "vector": vectors[0],
                        "fields": configuration["embedding"]["field"],
                        "k": 6,
                    }
                ]
            response = self.request(
                "POST",
                f"indexes/{self.index}/docs/search",
                api=SEARCH_API,
                body=body,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload.get("value"), list):
                raise ValueError("Search response has no document list.")
            return {
                **evidence(
                    payload["value"],
                    "azure-ai-search-hybrid" if provider == "hybrid" else "azure-ai-search-keyword",
                ),
                "configuration": configuration,
                **({"embedding_query": embedding} if embedding is not None else {}),
            }
        if provider != "iq":
            raise ValueError(
                "SearchGateway supports search, hybrid or iq, never an automatic fallback."
            )
        response = self.request(
            "POST",
            f"knowledgebases('{self.kb}')/retrieve",
            api=IQ_API,
            body={
                "intents": [{"type": "semantic", "search": question}],
                "includeActivity": True,
                "maxRuntimeInSeconds": 30,
                "maxOutputSizeInTokens": 6000,
                "knowledgeSourceParams": [
                    {
                        "kind": "searchIndex",
                        "knowledgeSourceName": self.source,
                        "includeReferences": True,
                        "includeReferenceSourceData": True,
                        **(
                            {"rerankerThreshold": self.configuration["iq_reranker_threshold"]}
                            if "iq_reranker_threshold" in self.configuration
                            else {}
                        ),
                    }
                ],
            },
        )
        response.raise_for_status()
        payload = response.json()
        references, activity = payload.get("references"), payload.get("activity")
        if not isinstance(references, list) or not isinstance(activity, list):
            raise ValueError("Foundry IQ must return references and activity arrays.")
        if any(not isinstance(item, dict) or item.get("error") for item in activity):
            raise ValueError("Foundry IQ reported an invalid/failed retrieval activity.")
        documents = {}
        for reference in references:
            if not isinstance(reference, dict):
                raise ValueError("Invalid Foundry IQ reference.")
            source = reference.get("sourceData")
            if not isinstance(source, dict):
                key = reference.get("docKey")
                if not isinstance(key, str) or not key:
                    raise ValueError("IQ reference has neither sourceData nor a document key.")
                lookup = self.request(
                    "GET", f"indexes/{self.index}/docs/{quote(key, safe='')}", api=SEARCH_API
                )
                lookup.raise_for_status()
                source = lookup.json()
            if not isinstance(source.get("id"), str):
                raise ValueError("IQ source data has no stable document ID.")
            documents[source["id"]] = source
        return {
            **evidence(
                list(documents.values()), "foundry-iq", references=references, activity=activity
            ),
            "knowledge_base": self.kb,
            "api_version": IQ_API,
            "configuration": self.configuration,
        }

    def seed(
        self,
        root: Path,
        *,
        include_iq: bool,
        confirmed: bool,
        hybrid: bool = False,
        confirm_embedding_cost: bool = False,
    ) -> dict[str, Any]:
        if not confirmed:
            raise ValueError(
                "Cloud writes require --confirm-create. Review the lab prerequisites first."
            )
        if hybrid and not confirm_embedding_cost:
            raise ValueError(
                "Hybrid indexing makes paid embedding requests; explicitly pass --confirm-cost."
            )
        prefix = owned_prefix()
        for name in (self.index, self.source, self.kb):
            if not name.startswith(prefix + "-"):
                raise ValueError("Refusing to modify an object outside WORKSHOP_PREFIX.")
        documents = load_documents(root, self.settings.language)
        scope = {"search_endpoint": self.endpoint, "prefix": prefix}
        ledger_path = root / "outputs/azure-objects.json"
        ledger = (
            read_json(ledger_path)
            if ledger_path.exists()
            else {
                "scope": scope,
                "corpus_hash": digest(documents),
                "objects": [],
            }
        )
        if ledger["scope"] != scope or ledger["corpus_hash"] != digest(documents):
            raise ValueError(
                "Existing ownership ledger has a different scope/corpus. Use a fresh workshop copy."
            )
        index_body = {
            "name": self.index,
            "fields": [
                {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
                {"name": "title", "type": "Edm.String", "searchable": True, "retrievable": True},
                {"name": "content", "type": "Edm.String", "searchable": True, "retrievable": True},
                {
                    "name": "effective_from",
                    "type": "Edm.String",
                    "filterable": True,
                    "retrievable": True,
                },
                {
                    "name": "effective_to",
                    "type": "Edm.String",
                    "filterable": True,
                    "retrievable": True,
                },
            ],
            "semantic": {
                "defaultConfiguration": "policy-semantic",
                "configurations": [
                    {
                        "name": "policy-semantic",
                        "prioritizedFields": {
                            "titleField": {"fieldName": "title"},
                            "prioritizedContentFields": [{"fieldName": "content"}],
                        },
                    }
                ],
            },
        }
        embedding = embedding_configuration() if hybrid else None
        if embedding is not None:
            index_body["fields"].append(
                {
                    "name": embedding["field"],
                    "type": "Collection(Edm.Single)",
                    "searchable": True,
                    "retrievable": False,
                    "dimensions": embedding["dimensions"],
                    "vectorSearchProfile": "policy-vector",
                }
            )
            index_body["vectorSearch"] = {
                "algorithms": [{"name": "policy-hnsw", "kind": "hnsw"}],
                "profiles": [{"name": "policy-vector", "algorithm": "policy-hnsw"}],
            }
        index_configuration = {"hybrid": hybrid, "embedding": embedding}
        configurations = ledger.get("index_configurations", {})
        if not isinstance(configurations, dict):
            raise ValueError("The index ownership configuration must be an object.")
        if self.index in configurations and configurations[self.index] != index_configuration:
            raise ValueError(
                "The owned index has a different vector contract; use a new explicit prefix/index."
            )
        definitions = [(f"indexes/{self.index}", SEARCH_API, index_body)]
        if include_iq:
            definitions.extend(
                [
                    (
                        f"knowledgesources('{self.source}')",
                        IQ_API,
                        {
                            "name": self.source,
                            "kind": "searchIndex",
                            "searchIndexParameters": {
                                "searchIndexName": self.index,
                                "sourceDataFields": [
                                    {"name": field} for field in ("id", "title", "content")
                                ],
                            },
                        },
                    ),
                    (
                        f"knowledgebases('{self.kb}')",
                        IQ_API,
                        {
                            "name": self.kb,
                            "description": "Synthetic workshop policies only.",
                            "knowledgeSources": [{"name": self.source}],
                        },
                    ),
                ]
            )
        for path, api, body in definitions:
            existing = self.request("GET", path, api=api)
            if existing.status_code == 404:
                response = self.request("PUT", path, api=api, body=body, create_only=True)
                response.raise_for_status()
                ledger["objects"].append({"path": path, "api_version": api})
                write_json(ledger_path, ledger)
            elif existing.status_code == 200:
                if path not in {item["path"] for item in ledger["objects"]}:
                    raise ValueError(f"Refusing to overwrite an unowned Search object: {path}")
                if path.startswith("indexes/"):
                    fields = existing.json().get("fields", [])
                    vector = next(
                        (field for field in fields if field.get("name") == "content_vector"), None
                    )
                    if hybrid and (
                        vector is None
                        or vector.get("dimensions") != embedding["dimensions"]
                        or vector.get("vectorSearchProfile") != "policy-vector"
                    ):
                        raise ValueError(
                            "The existing index does not match the explicit hybrid schema; do not overwrite it."
                        )
                    if not hybrid and vector is not None:
                        raise ValueError(
                            "Do not erase an owned hybrid index's vectors with a text-only upload."
                        )
            else:
                existing.raise_for_status()
            if path.startswith("indexes/"):
                uploaded = documents
                if embedding is not None:
                    vectors, metadata = embed_texts(
                        self.settings,
                        [document["title"] + "\n" + document["content"] for document in documents],
                        embedding,
                    )
                    uploaded = [
                        {**document, embedding["field"]: vector}
                        for document, vector in zip(documents, vectors, strict=True)
                    ]
                    ledger["embedding_model"] = metadata
                response = self.request(
                    "POST",
                    f"{path}/docs/index",
                    api=SEARCH_API,
                    body={
                        "value": [{"@search.action": "upload", **document} for document in uploaded]
                    },
                )
                response.raise_for_status()
                statuses = response.json().get("value")
                if (
                    not isinstance(statuses, list)
                    or len(statuses) != len(documents)
                    or any(item.get("status") is not True for item in statuses)
                    or {item.get("key") for item in statuses}
                    != {document["id"] for document in documents}
                ):
                    raise ValueError(
                        "Partial/missing Search indexing results. Inspect the owned index before retrying."
                    )
                ledger.setdefault("index_configurations", {})[self.index] = index_configuration
                write_json(ledger_path, ledger)
        return {
            "mode": "live",
            "index": self.index,
            "knowledge_base": self.kb if include_iq else None,
            "document_count": len(documents),
            "hybrid": hybrid,
            "ledger": str(ledger_path),
            "note": "Resource creation is not retrieval verification. Run retrieve separately.",
        }
