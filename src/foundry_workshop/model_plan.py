"""Model roles and bounded generation defaults for this workshop."""

import os
from dataclasses import dataclass

PRIMARY_MODEL = "gpt-6-luna"
PRIMARY_VERSION = "2026-09-22"
PRIMARY_DEPLOYMENT = "workshop-chat"
COMPARISON_MODEL = "gpt-6-sol"
COMPARISON_VERSION = "2026-09-22"
COMPARISON_DEPLOYMENT = "workshop-compare"
DEFAULT_MAX_OUTPUT_TOKENS = 32768
MAX_OUTPUT_TOKENS = 32768
DEFAULT_REASONING_EFFORT = "low"
REASONING_EFFORTS = ("none", "low", "medium", "high")


@dataclass(frozen=True)
class GenerationConfig:
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS
    reasoning_effort: str | None = DEFAULT_REASONING_EFFORT

    @classmethod
    def from_env(cls) -> "GenerationConfig":
        try:
            tokens = int(
                os.environ.get("WORKSHOP_MAX_OUTPUT_TOKENS", str(DEFAULT_MAX_OUTPUT_TOKENS))
            )
        except ValueError as exc:
            raise ValueError(
                f"WORKSHOP_MAX_OUTPUT_TOKENS must be an integer from 256 to {MAX_OUTPUT_TOKENS}."
            ) from exc
        if not 256 <= tokens <= MAX_OUTPUT_TOKENS:
            raise ValueError(
                f"WORKSHOP_MAX_OUTPUT_TOKENS must be an integer from 256 to {MAX_OUTPUT_TOKENS}."
            )
        effort = os.environ.get("WORKSHOP_REASONING_EFFORT", DEFAULT_REASONING_EFFORT)
        if effort not in REASONING_EFFORTS:
            raise ValueError("WORKSHOP_REASONING_EFFORT must be none, low, medium or high.")
        return cls(tokens, effort)


MODEL_ROLES = {
    "answer": {
        "model": PRIMARY_MODEL,
        "version": PRIMARY_VERSION,
        "deployment": PRIMARY_DEPLOYMENT,
        "environment": "AZURE_AI_MODEL_DEPLOYMENT_NAME",
    },
    "comparison": {
        "model": COMPARISON_MODEL,
        "version": COMPARISON_VERSION,
        "deployment": COMPARISON_DEPLOYMENT,
        "environment": None,
    },
    "judge": {
        "model": COMPARISON_MODEL,
        "version": COMPARISON_VERSION,
        "deployment": COMPARISON_DEPLOYMENT,
        "environment": "AZURE_AI_EVALUATION_MODEL_DEPLOYMENT_NAME",
    },
    "embedding": {
        "model": "text-embedding-3-large",
        "version": None,
        "deployment": "workshop-embedding",
        "environment": "AZURE_AI_EMBEDDING_DEPLOYMENT_NAME",
    },
    "iq": {
        "model": "gpt-5.6-luna",
        "version": "2026-07-09",
        "deployment": "gpt-5.6-luna",
        "environment": None,
    },
    "optimizer": {
        "model": "gpt-5.5",
        "version": "2026-04-24",
        "deployment": "workshop-optimizer",
        "environment": None,
    },
}
