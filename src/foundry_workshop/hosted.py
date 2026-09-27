import asyncio
import logging
import re
from contextlib import ExitStack
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from .compatibility import FOUNDRY_AGENT_DATA_PLANE
from .contracts import (
    Answer,
    ModelOutputError,
    digest,
    parse_json,
    parse_json_prefix,
    safe_label,
    validate_question,
)
from .profiles import RuntimeProfile, model_deployments, runtime_contract
from .settings import Settings, credential_for, require_env

LOGGER = logging.getLogger(__name__)
REQUEST_FIELDS = {"question", "model_key", "case_id", "run_id"}


def validate_request(value: Any, models: dict[str, str]) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != REQUEST_FIELDS:
        raise ValueError(
            "Send only question, model_key, case_id and run_id; never evaluator labels."
        )
    if any(not isinstance(value[key], str) for key in REQUEST_FIELDS):
        raise ValueError("Every invocation field must be a string.")
    if value["model_key"] not in models:
        raise ValueError("The model key is not in the server's explicit deployment allowlist.")
    safe_label(value["case_id"].lower())
    safe_label(value["run_id"])
    question = validate_question(value["question"])
    if question != value["question"]:
        raise ValueError(
            "Preserve the exact canonical question; remove surrounding whitespace first."
        )
    return dict(value)


def create_invocations_app(settings: Settings, root: Path, profile: RuntimeProfile):
    import httpx
    from azure.ai.agentserver.invocations import InvocationAgentServerHost
    from azure.core.exceptions import AzureError
    from openai import OpenAIError
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    from .runtime import run_pipeline

    if profile.protocol != "invocations":
        raise ValueError("The typed evaluation host requires protocol=invocations.")
    contract = runtime_contract(root, settings, profile)
    models = model_deployments(settings)
    app = InvocationAgentServerHost(
        openapi_spec={
            "openapi": "3.1.0",
            "info": {"title": "Synthetic policy evaluation", "version": "1"},
            "paths": {
                "/invocations": {
                    "post": {
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": sorted(REQUEST_FIELDS),
                                        "properties": {
                                            key: {"type": "string"}
                                            for key in sorted(REQUEST_FIELDS)
                                        },
                                        "additionalProperties": False,
                                    }
                                }
                            },
                        },
                        "responses": {
                            "200": {
                                "description": "Validated answer with immutable runtime lineage"
                            }
                        },
                    }
                },
            },
        }
    )

    @app.invoke_handler
    async def invoke(request: Request):
        try:
            payload = validate_request(parse_json((await request.body()).decode("utf-8")), models)
        except (ValueError, KeyError, TypeError) as exc:
            LOGGER.warning("Rejected invalid synthetic-workshop invocation: %s", exc)
            return JSONResponse(
                {"error": {"type": "invalid_request", "message": str(exc)}}, status_code=400
            )
        try:
            result = await asyncio.wait_for(
                run_pipeline(
                    replace(settings, deployment=models[payload["model_key"]]),
                    root,
                    payload["question"],
                    profile,
                    request_metadata={
                        key: payload[key] for key in ("model_key", "case_id", "run_id")
                    },
                ),
                timeout=240,
            )
        except (ValueError, TimeoutError, AzureError, OpenAIError, httpx.HTTPError) as exc:
            LOGGER.error("Synthetic-workshop invocation failed: %s", type(exc).__name__)
            details = exc.details if isinstance(exc, ModelOutputError) else {}
            return JSONResponse(
                {
                    **payload,
                    "error": {
                        "type": type(exc).__name__,
                        "message": "The selected pipeline failed; no provider, model or fixture fallback was used.",
                    },
                    "partial_lineage": details,
                },
                status_code=502,
            )
        return JSONResponse(
            {
                **result,
                **payload,
                "runtime_contract": contract,
                "runtime_contract_hash": digest(contract),
            }
        )

    return app


@dataclass(frozen=True)
class HostedBinding:
    name: str
    version: str
    endpoint: str

    @classmethod
    def from_env(cls, settings: Settings) -> "HostedBinding":
        binding = cls(
            require_env("WORKSHOP_HOSTED_AGENT_NAME"),
            require_env("WORKSHOP_HOSTED_AGENT_VERSION"),
            require_env("WORKSHOP_HOSTED_AGENT_ENDPOINT"),
        )
        binding.validate(settings)
        return binding

    def validate(self, settings: Settings) -> None:
        if not re.fullmatch(r"lab-[a-z0-9-]{1,120}", self.name):
            raise ValueError("Use the exact workshop-prefixed Hosted agent name.")
        if not re.fullmatch(r"[1-9][0-9]*", self.version):
            raise ValueError("Pin an actual numeric Hosted agent version, never latest.")
        url = urlsplit(self.endpoint)
        project = urlsplit(settings.project_endpoint)
        query = parse_qsl(url.query, keep_blank_values=True)
        if (
            url.scheme != "https"
            or url.hostname != project.hostname
            or url.username
            or url.password
            or url.port not in (None, 443)
            or url.fragment
            or url.path
            != project.path.rstrip("/") + f"/agents/{self.name}/endpoint/protocols/invocations"
            or query not in ([], [("api-version", FOUNDRY_AGENT_DATA_PLANE.version)])
        ):
            raise ValueError(
                "Use the actual Invocations endpoint returned by azd show for this project/agent."
            )

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "version": self.version, "endpoint": self.endpoint}


class HostedTransport:
    def __init__(self, settings: Settings, binding: HostedBinding):
        self.settings, self.binding = settings, binding
        binding.validate(settings)
        self.session_id: str | None = None
        self.credential = None
        self.project = None
        self.http = None
        self._stack = None
        self._token_provider = None

    def __enter__(self):
        import httpx
        from azure.ai.projects import AIProjectClient
        from azure.identity import get_bearer_token_provider

        with ExitStack() as stack:
            self.credential = stack.enter_context(credential_for(self.settings))
            self.project = stack.enter_context(
                AIProjectClient(endpoint=self.settings.project_endpoint, credential=self.credential)
            )
            self.http = stack.enter_context(httpx.Client(timeout=270, follow_redirects=False))
            self._token_provider = get_bearer_token_provider(
                self.credential, "https://ai.azure.com/.default"
            )
            self._stack = stack.pop_all()
        return self

    def __exit__(self, *_args):
        if self._stack is not None:
            self._stack.close()

    def create_session(self) -> str:
        from azure.ai.projects.models import VersionRefIndicator

        if self.project is None:
            raise RuntimeError("Open the Hosted transport before creating a session.")
        version = self.project.agents.get_version(self.binding.name, self.binding.version).as_dict()
        if (
            version.get("definition", {}).get("kind") != "hosted"
            or version.get("status") != "active"
        ):
            raise ValueError("The pinned version is not an active Hosted agent.")
        session = self.project.agents.create_session(
            self.binding.name,
            version_indicator=VersionRefIndicator(agent_version=self.binding.version),
        )
        self.session_id = session.agent_session_id
        if not isinstance(self.session_id, str) or not self.session_id:
            raise ValueError("The service did not return a real session ID.")
        return self.session_id

    def invoke(self, payload: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
        import httpx

        if not self.session_id or self.http is None or self._token_provider is None:
            raise ValueError("Create and record a pinned-version session before collecting.")
        endpoint = httpx.URL(self.binding.endpoint).copy_merge_params(
            {"agent_session_id": self.session_id}
        )
        response = self.http.post(
            endpoint,
            headers={"Authorization": "Bearer " + self._token_provider()},
            json=payload,
        )
        raw = {
            "status_code": response.status_code,
            "body": response.text,
            "request_id": response.headers.get("x-request-id"),
        }
        if not response.is_success:
            return {
                "error": {
                    "type": f"HTTP{response.status_code}",
                    "message": "Hosted request failed.",
                }
            }, raw
        try:
            parsed = parse_json(response.text)
        except ValueError:
            parsed = {
                "error": {"type": "InvalidJSON", "message": "Hosted response was not valid JSON."}
            }
        return parsed, raw

    def stop_session(self, session_id: str) -> dict[str, Any]:
        if self.project is None:
            raise RuntimeError("Open the Hosted transport before stopping its recorded session.")
        self.project.agents.stop_session(self.binding.name, session_id)
        return self.project.agents.get_session(self.binding.name, session_id).as_dict()


def validate_response(
    value: Any, payload: dict[str, str], contract: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("error"):
        raise ValueError("The selected Hosted invocation failed.")
    for key in REQUEST_FIELDS:
        if value.get(key) != payload[key]:
            raise ValueError(f"The Hosted response changed request field {key}.")
    if value.get("runtime_contract") != contract or value.get("runtime_contract_hash") != digest(
        contract
    ):
        raise ValueError(
            "The deployed code, prompt, models or retrieval differ from the frozen local contract."
        )
    if value.get("deployment") != contract["models"][payload["model_key"]]:
        raise ValueError("The Hosted response used a different deployment.")
    for key in ("prompt_hash", "effective_prompt_hash"):
        if value.get(key) != contract[key]:
            raise ValueError(f"The actual response has a different {key}.")
    if value.get("runtime_profile") != contract["profile"] or value.get("mode") != "live":
        raise ValueError("The response does not belong to the frozen live runtime profile.")
    Answer.from_dict(value.get("answer"))
    if (
        not isinstance(value.get("response_id"), str)
        or not value["response_id"]
        or not isinstance(value.get("response_model"), str)
        or not value["response_model"]
        or value.get("external_actions_performed") is not False
        or value.get("approval_status") != "pending-human-review"
    ):
        raise ValueError(
            "Missing actual response/model lineage or violated action/approval boundary."
        )
    documents = value.get("documents")
    from .knowledge import evidence

    actual = evidence(documents, value.get("provider"))
    if actual["context_hash"] != value.get("context_hash") or actual["source_ids"] != value.get(
        "source_ids"
    ):
        raise ValueError("Returned source documents do not match their declared evidence lineage.")
    calls = value.get("model_calls")
    if (
        not isinstance(calls, list)
        or not calls
        or any(
            not isinstance(call, dict)
            or not isinstance(call.get("response_id"), str)
            or not call["response_id"]
            or not isinstance(call.get("response_model"), str)
            or not call["response_model"]
            for call in calls
        )
    ):
        raise ValueError(
            "Preserve the actual service-call lineage, not only a wrapper response ID."
        )
    from .runtime import usage_totals

    usage = usage_totals(calls)
    if (
        usage is None
        or value.get("usage") != usage
        or calls[-1]["response_id"] != value["response_id"]
        or calls[-1]["response_model"] != value["response_model"]
    ):
        raise ValueError("Model-call IDs or token accounting are incomplete/inconsistent.")
    return value


def parse_azd_http(raw: bytes) -> tuple[dict[str, Any], str | None]:
    separator = b"\r\n\r\n" if b"\r\n\r\n" in raw else b"\n\n"
    header, found, body = raw.partition(separator)
    if not found or not header.startswith(b"HTTP/"):
        raise ValueError("Expected the complete raw HTTP response from azd.")
    match = re.fullmatch(rb"HTTP/\S+ ([0-9]{3})(?: .*)?", header.splitlines()[0])
    if not match or not 200 <= int(match[1]) < 300:
        raise ValueError("azd returned a non-success or invalid HTTP status.")
    lengths = [
        line.partition(b":")[2].strip()
        for line in header.splitlines()[1:]
        if line.partition(b":")[0].lower() == b"content-length"
    ]
    if len(lengths) > 1 or lengths and not lengths[0].isdigit():
        raise ValueError("Expected an unambiguous HTTP Content-Length.")
    if lengths:
        length = int(lengths[0])
        if len(body) < length:
            raise ValueError("The azd HTTP body was truncated.")
        payload = parse_json(body[:length].decode("utf-8"))
        suffix = body[length:].decode("utf-8").strip()
    else:
        text = body.decode("utf-8")
        payload, end = parse_json_prefix(text)
        suffix = text[end:].strip()
    if suffix and not re.fullmatch(r"Update available: [^\n]+\nTo update, run `[^\n]+`", suffix):
        raise ValueError(
            "Unknown trailing azd output; do not extract a success-shaped JSON substring."
        )
    if not isinstance(payload, dict):
        raise ValueError("Expected an object from the typed Hosted endpoint.")
    return payload, suffix or None
