import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value or any(
        marker in value.casefold() for marker in ("<", ">", "your-", "replace", "changeme")
    ):
        raise ValueError(f"Set {name} to the verified value from your setup card (.env locally).")
    return value


def require_uuid(name: str) -> str:
    value = require_env(name)
    try:
        UUID(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid UUID from your setup card.") from exc
    return value


def azure_endpoint(value: str, kind: str) -> str:
    parts = urlsplit(value)
    host = parts.hostname or ""
    if parts.scheme != "https" or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError(
            f"{kind} endpoint must be a plain HTTPS Azure endpoint without credentials."
        )
    if parts.port not in (None, 443):
        raise ValueError(f"{kind} endpoint must use port 443.")
    path = parts.path.rstrip("/")
    if kind == "project":
        if not host.endswith(".services.ai.azure.com") or not re.fullmatch(
            r"/api/projects/[^/]+", path
        ):
            raise ValueError("Use https://<resource>.services.ai.azure.com/api/projects/<project>.")
    elif kind == "search":
        if not host.endswith(".search.windows.net") or path:
            raise ValueError(
                "Use the Azure AI Search service root https://<name>.search.windows.net."
            )
    elif kind == "openai":
        if not host.endswith(".openai.azure.com") or path:
            raise ValueError(
                "Use the Foundry account's Azure OpenAI root https://<name>.openai.azure.com."
            )
    else:
        raise ValueError(f"Unknown endpoint kind: {kind}")
    return value.rstrip("/")


def load_environment(root: Path) -> None:
    from dotenv import load_dotenv

    load_dotenv(root / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    project_endpoint: str
    deployment: str
    tenant_id: str | None
    auth_mode: str
    managed_identity_client_id: str | None
    max_output_tokens: int
    openai_endpoint: str | None = None
    language: str = "ko"

    def __post_init__(self):
        if self.language not in {"ko", "en"}:
            raise ValueError("Workshop language must be ko or en.")

    @classmethod
    def from_env(cls, *, language: str = "ko") -> "Settings":
        mode = os.environ.get("WORKSHOP_AUTH_MODE", "cli")
        if mode not in {"cli", "managed-identity"}:
            raise ValueError("WORKSHOP_AUTH_MODE must be cli or managed-identity.")
        tenant = require_uuid("AZURE_TENANT_ID") if mode == "cli" else None
        client_id = (
            require_uuid("AZURE_CLIENT_ID")
            if os.environ.get("AZURE_CLIENT_ID", "").strip()
            else None
        )
        try:
            tokens = int(os.environ.get("WORKSHOP_MAX_OUTPUT_TOKENS", "2048"))
        except ValueError as exc:
            raise ValueError(
                "WORKSHOP_MAX_OUTPUT_TOKENS must be an integer from 256 to 8192."
            ) from exc
        if not 256 <= tokens <= 8192:
            raise ValueError("WORKSHOP_MAX_OUTPUT_TOKENS must be an integer from 256 to 8192.")
        return cls(
            project_endpoint=azure_endpoint(require_env("AZURE_AI_PROJECT_ENDPOINT"), "project"),
            deployment=require_env("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
            tenant_id=tenant,
            auth_mode=mode,
            managed_identity_client_id=client_id,
            max_output_tokens=tokens,
            openai_endpoint=azure_endpoint(os.environ["AZURE_OPENAI_ENDPOINT"], "openai")
            if os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
            else None,
            language=language,
        )


def credential_for(settings: Settings, *, asynchronous: bool = False):
    if asynchronous:
        from azure.identity.aio import AzureCliCredential, ManagedIdentityCredential
    else:
        from azure.identity import AzureCliCredential, ManagedIdentityCredential

    if settings.auth_mode == "cli":
        subscription = require_uuid("AZURE_SUBSCRIPTION_ID")
        profile = subprocess.run(
            [
                "az",
                "account",
                "show",
                "--subscription",
                subscription,
                "--query",
                "tenantId",
                "--output",
                "tsv",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        if (
            not settings.tenant_id
            or profile.stdout.strip().casefold() != settings.tenant_id.casefold()
        ):
            raise ValueError("The selected Azure CLI subscription does not match AZURE_TENANT_ID.")
        # Azure CLI rejects --tenant and --subscription together; the subscription selects its account.
        return AzureCliCredential(subscription=subscription, process_timeout=30)
    return ManagedIdentityCredential(client_id=settings.managed_identity_client_id)


def owned_prefix() -> str:
    value = require_env("WORKSHOP_PREFIX")
    if not re.fullmatch(r"lab-[a-z0-9]+(?:-[a-z0-9]+)*", value) or len(value) > 32:
        raise ValueError(
            "WORKSHOP_PREFIX must be a unique lab-<alias>-<date> name, at most 32 characters."
        )
    return value
