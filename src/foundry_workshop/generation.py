from typing import Any

from .model_plan import GenerationConfig
from .settings import Settings


def response_options(settings: Settings | GenerationConfig) -> dict[str, Any]:
    options: dict[str, Any] = {"max_output_tokens": settings.max_output_tokens}
    if settings.reasoning_effort is not None:
        options["reasoning"] = {"effort": settings.reasoning_effort}
    return options


def agent_options(settings: Settings | GenerationConfig) -> dict[str, Any]:
    if settings.reasoning_effort is None:
        return {}
    from azure.ai.projects.models import Reasoning

    return {"reasoning": Reasoning(effort=settings.reasoning_effort)}


def agent_response_options(settings: Settings | GenerationConfig) -> dict[str, Any]:
    # Agent-reference calls inherit reasoning from the immutable agent definition.
    return {"max_output_tokens": settings.max_output_tokens}


def maf_options(
    settings: Settings | GenerationConfig, *, api: str = "project-responses"
) -> dict[str, Any]:
    options: dict[str, Any] = {"store": False, "max_tokens": settings.max_output_tokens}
    if settings.reasoning_effort is not None:
        if api == "account-chat":
            options["reasoning_effort"] = settings.reasoning_effort
        else:
            options["reasoning"] = {"effort": settings.reasoning_effort}
            if settings.reasoning_effort != "none":
                # Foundry does not add encrypted reasoning for stateless tool replay automatically.
                options["include"] = ["reasoning.encrypted_content"]
    return options


def generation_metadata(settings: Settings | GenerationConfig) -> dict[str, Any]:
    return {
        "max_output_tokens": settings.max_output_tokens,
        "reasoning_effort": settings.reasoning_effort,
    }
