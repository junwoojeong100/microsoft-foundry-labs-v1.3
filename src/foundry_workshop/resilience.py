"""Contracts for the local, prewritten AgentServer resilience exercise.

This module has no SDK dependency, model client, or real-action executor.
The runnable SDK host is in examples/resilient/server.py.
"""

import hashlib
import math
import os
import re
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .contracts import digest, load_cases, parse_json

MODEL_LABEL = "synthetic-runtime-only"
TASK_NAME = "workshop-simulated-review-v1"
REQUEST_INPUT = "D03"
MODE = "local-sdk-prewritten-synthetic"
HUMAN_AUTHORIZATION = "not-granted"
STAGES = ("approval_request", "synthetic_review_packet", "human_handoff_required")
WORKLOAD = {
    "synthetic_review_packet": (
        "Prewritten synthetic review packet. No booking, payment, email, or submission occurred."
    ),
    "human_handoff_required": (
        "The simulation is finished. A separately authenticated, authorized human must review "
        "any real action in a different system; this workshop grants no human authorization."
    ),
    "simulation_rejected": "The simulated decision was rejection. No workload steps were executed.",
}
KOREAN_WORKLOAD = {
    "synthetic_review_packet": "미리 작성한 합성 검토 자료입니다. 예약·지급·이메일·신청을 수행하지 않았습니다.",
    "human_handoff_required": "모의 실행이 끝났습니다. 실제 작업은 별도 시스템에서 인증·권한을 가진 사람이 검토해야 하며 이 실습은 사람의 승인을 부여하지 않습니다.",
    "simulation_rejected": "모의 결정은 반려입니다. 후속 작업 단계를 실행하지 않았습니다.",
}


def workload_for(language: str) -> dict[str, str]:
    if language not in {"en", "ko"}:
        raise ValueError("Use the explicit English or Korean synthetic workload.")
    return WORKLOAD if language == "en" else KOREAN_WORKLOAD


class GateConflict(ValueError):
    """A decision is stale or does not belong to this pending gate."""


class GateExpired(GateConflict):
    """The bounded demonstration's approval window has expired."""


def response_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"(?:caresp|resp)_[A-Za-z0-9_-]{1,200}", value
    ):
        raise ValueError("Expected an SDK response ID, not a path or a task label.")
    return value


def task_id(value: str) -> str:
    return f"approval-{response_id(value)}"


def require_local_environment(environment: Mapping[str, str] | None = None) -> Path:
    env = os.environ if environment is None else environment
    forbidden = (
        "FOUNDRY_HOSTING_ENVIRONMENT",
        "FOUNDRY_PROJECT_ENDPOINT",
        "AZURE_AI_PROJECT_ENDPOINT",
        "AZURE_AIPROJECT_ENDPOINT",
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
        "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
        "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
    )
    present = [key for key in forbidden if env.get(key)]
    if present:
        raise ValueError("Local-only exercise: unset these variables first: " + ", ".join(present))
    if env.get("OTEL_SDK_DISABLED") != "true":
        raise ValueError("Set OTEL_SDK_DISABLED=true for this local-only exercise.")
    state = Path(env.get("AGENTSERVER_STATE_ROOT", ""))
    if not state.is_absolute() or state == Path(state.anchor) or state == Path.home():
        raise ValueError("AGENTSERVER_STATE_ROOT must be an absolute, dedicated local directory.")
    return state


def scenario(root: Path, language: str = "en") -> dict[str, Any]:
    """Read only the selected development scenario; never load a prompt or holdout."""
    workload = workload_for(language)
    case = next(
        (row for row in load_cases(root, "dev", language) if row["case_id"] == REQUEST_INPUT), None
    )
    if case is None:
        raise ValueError("The bundled development scenario D03 is missing.")
    dataset = "data/evaluation/en/dev.jsonl" if language == "en" else "data/evaluation/dev.jsonl"
    corpus = (
        "data/knowledge/en/policies.json" if language == "en" else "data/knowledge/policies.json"
    )
    return {
        "schema_version": 1,
        "mode": MODE,
        "case_id": REQUEST_INPUT,
        "language": language,
        "question": case["question"],
        "lineage": {
            "dataset_path": dataset,
            "dataset_sha256": hashlib.sha256((root / dataset).read_bytes()).hexdigest(),
            "split": "dev",
            "question_sha256": digest(case["question"]),
            "corpus_path": corpus,
            "corpus_sha256": hashlib.sha256((root / corpus).read_bytes()).hexdigest(),
            "corpus_used_for_inference": False,
            "prompt_id": None,
            "prompt_sha256": None,
            "model_response_id": None,
            "model": None,
            "evaluator": None,
            "workload_sha256": digest(workload),
        },
    }


def validate_create(value: Any) -> None:
    required = {"model", "input", "store", "background", "stream"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("Supply exactly model, input, store, background, and stream.")
    if value["model"] != MODEL_LABEL or value["input"] != REQUEST_INPUT:
        raise ValueError("Only the prewritten synthetic-runtime-only / D03 exercise is accepted.")
    if any(value[key] is not True for key in ("store", "background", "stream")):
        raise ValueError("This exercise requires store=true, background=true, and stream=true.")


def new_gate(
    *,
    response: str,
    input_id: str,
    gate_id: str,
    source: dict[str, Any],
    expires_at: float,
) -> dict[str, Any]:
    gate = {
        "schema_version": 1,
        "mode": MODE,
        "response_id": response_id(response),
        "task_id": task_id(response),
        "gate_id": gate_id,
        "request_input_id": input_id,
        "request_sha256": digest(source),
        "scenario": source,
        "expires_at": expires_at,
        "status": "awaiting_simulated_decision",
        "decision": None,
        "human_authorization": HUMAN_AUTHORIZATION,
        "external_actions_performed": False,
    }
    validate_gate(gate)
    return gate


def validate_gate(gate: Any) -> None:
    if not isinstance(gate, dict) or set(gate) != {
        "schema_version",
        "mode",
        "response_id",
        "task_id",
        "gate_id",
        "request_input_id",
        "request_sha256",
        "scenario",
        "expires_at",
        "status",
        "decision",
        "human_authorization",
        "external_actions_performed",
    }:
        raise ValueError("Invalid persisted approval-request shape.")
    if (
        type(gate["schema_version"]) is not int
        or gate["schema_version"] != 1
        or gate["mode"] != MODE
        or gate["task_id"] != task_id(gate["response_id"])
        or gate["human_authorization"] != HUMAN_AUTHORIZATION
        or gate["external_actions_performed"] is not False
    ):
        raise ValueError("Persisted gate identity or safety contract changed.")
    for key in ("gate_id", "request_input_id"):
        if not isinstance(gate[key], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,240}", gate[key]):
            raise ValueError(f"Invalid persisted {key}.")
    if not isinstance(gate["scenario"], dict) or digest(gate["scenario"]) != gate["request_sha256"]:
        raise ValueError("Persisted request lineage does not match its digest.")
    deadline = gate["expires_at"]
    if type(deadline) not in (int, float) or not math.isfinite(deadline) or deadline <= 0:
        raise ValueError("Invalid persisted approval deadline.")
    decision = gate["decision"]
    if gate["status"] == "awaiting_simulated_decision":
        if decision is not None:
            raise ValueError("Pending gate cannot contain a decision.")
    elif gate["status"] in ("simulation_approved", "simulation_rejected"):
        if not isinstance(decision, dict) or set(decision) != {
            "kind",
            "decision",
            "input_id",
            "entry_mode",
        }:
            raise ValueError("Invalid persisted simulated decision.")
        if (
            decision["kind"] != "simulated"
            or decision["decision"] not in ("approve", "reject")
            or gate["status"]
            != f"simulation_{'approved' if decision['decision'] == 'approve' else 'rejected'}"
            or not isinstance(decision["input_id"], str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,240}", decision["input_id"])
            or decision["entry_mode"] not in ("resumed", "recovered")
        ):
            raise ValueError("Persisted decision is not a valid simulated continuation.")
    else:
        raise ValueError("Unknown persisted gate status.")


def validate_decision(gate: dict[str, Any], value: Any, *, now: float | None = None) -> None:
    validate_gate(gate)
    if not isinstance(value, dict) or set(value) != {
        "gate_id",
        "request_sha256",
        "if_last_input_id",
        "input_id",
        "decision",
        "simulated",
    }:
        raise ValueError("Supply the exact gate binding, input IDs, decision, and simulated=true.")
    if value["simulated"] is not True or value["decision"] not in ("approve", "reject"):
        raise ValueError("Only explicitly simulated approve/reject decisions are supported.")
    if not isinstance(value["input_id"], str) or not re.fullmatch(
        r"[A-Za-z0-9_-]{1,240}", value["input_id"]
    ):
        raise ValueError("A new, bounded input_id is required.")
    if gate["status"] != "awaiting_simulated_decision":
        raise GateConflict(
            "This gate is no longer pending; decisions cannot be replayed or changed."
        )
    if (time.time() if now is None else now) >= gate["expires_at"]:
        raise GateExpired("The simulated approval window expired; start a new response.")
    if (
        value["gate_id"] != gate["gate_id"]
        or value["request_sha256"] != gate["request_sha256"]
        or value["if_last_input_id"] != gate["request_input_id"]
        or value["input_id"] == gate["request_input_id"]
    ):
        raise GateConflict("Decision does not match this request, gate, and previous input ID.")


def apply_decision(
    gate: dict[str, Any], value: dict[str, Any], *, entry_mode: str, now: float | None = None
) -> dict[str, Any]:
    validate_decision(gate, value, now=now)
    if entry_mode not in ("resumed", "recovered"):
        raise GateConflict("A decision must resume an existing SDK task, never open a fresh one.")
    result = {
        **gate,
        "status": f"simulation_{'approved' if value['decision'] == 'approve' else 'rejected'}",
        "decision": {
            "kind": "simulated",
            "decision": value["decision"],
            "input_id": value["input_id"],
            "entry_mode": entry_mode,
        },
    }
    validate_gate(result)
    return result


def output_payload(stage: str, gate: dict[str, Any]) -> dict[str, Any]:
    validate_gate(gate)
    common = {
        "stage": stage,
        "mode": MODE,
        "response_id": gate["response_id"],
        "approval_task_id": gate["task_id"],
        "gate_id": gate["gate_id"],
        "request_sha256": gate["request_sha256"],
        "human_authorization": HUMAN_AUTHORIZATION,
        "external_actions_performed": False,
        "model_inference_performed": False,
        "quality_evaluation_performed": False,
    }
    if stage == "approval_request":
        return {
            **common,
            "status": "awaiting_simulated_decision",
            "request_input_id": gate["request_input_id"],
            "expires_at": gate["expires_at"],
            "scenario": gate["scenario"],
        }
    if stage not in WORKLOAD:
        raise ValueError("Unknown prewritten workload stage.")
    expected = "simulation_rejected" if stage == "simulation_rejected" else "simulation_approved"
    if gate["status"] != expected:
        raise GateConflict(
            "No workload output is permitted without the matching simulated decision."
        )
    return {
        **common,
        "status": gate["status"],
        "simulated_decision": gate["decision"],
        "text": workload_for(gate["scenario"].get("language", "en"))[stage],
    }


def checkpoint_outputs(response: Mapping[str, Any], gate: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate the whole committed prefix, not just its length."""
    if response.get("id") != gate["response_id"]:
        raise ValueError("Checkpoint belongs to a different response.")
    items = response.get("output")
    if not isinstance(items, list):
        raise ValueError("Checkpoint output must be a list.")
    order = (
        ("approval_request", "simulation_rejected")
        if gate["status"] == "simulation_rejected"
        else STAGES
    )
    if len(items) > len(order):
        raise ValueError("Checkpoint contains extra or duplicated stages.")
    ids = []
    for item, stage in zip(items, order, strict=False):
        if (
            not isinstance(item, dict)
            or item.get("type") != "message"
            or item.get("role") != "assistant"
            or item.get("status") != "completed"
            or not isinstance(item.get("id"), str)
            or not item["id"]
        ):
            raise ValueError("Checkpoint contains an unfinished or invalid output item.")
        contents = item.get("content")
        if (
            not isinstance(contents, list)
            or len(contents) != 1
            or not isinstance(contents[0], dict)
            or contents[0].get("type") != "output_text"
            or not isinstance(contents[0].get("text"), str)
            or parse_json(contents[0]["text"]) != output_payload(stage, gate)
        ):
            raise ValueError("Checkpoint stage order, payload, or lineage changed.")
        ids.append(item["id"])
    if len(set(ids)) != len(ids):
        raise ValueError("Checkpoint repeats an output ID.")
    return items


def verify_completion(
    before: Mapping[str, Any], after: Mapping[str, Any], gate: dict[str, Any]
) -> dict[str, Any]:
    original = checkpoint_outputs(before, gate)
    final = checkpoint_outputs(after, gate)
    expected = 2 if gate["status"] == "simulation_rejected" else len(STAGES)
    if not original or after.get("status") != "completed" or len(final) != expected:
        raise ValueError("Completion evidence is missing, unfinished, or has missing rows.")
    if final[: len(original)] != original:
        raise ValueError(
            "Recovery changed a committed item, its content, or its original output ID."
        )
    return {
        "mode": MODE,
        "response_id": after["id"],
        "approval_task_id": gate["task_id"],
        "preserved_output_ids": [item["id"] for item in original],
        "final_output_ids": [item["id"] for item in final],
        "human_authorization": HUMAN_AUTHORIZATION,
        "external_actions_performed": False,
        "quality_score": None,
        "azure_execution_verified": False,
    }
