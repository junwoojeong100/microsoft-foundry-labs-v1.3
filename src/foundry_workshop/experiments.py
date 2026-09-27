import json
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .contracts import (
    ModelOutputError,
    code_hash,
    digest,
    load_cases,
    load_documents,
    load_prompt,
    localized_path,
    read_json,
    safe_label,
    write_json,
)
from .evaluation import load_run, summarize
from .knowledge import evidence


def collect(
    root: Path,
    *,
    label: str,
    split: str,
    prompt_version: str,
    retrieval: str,
    mode: str,
    deployment: str,
    answer_case: Callable[[dict[str, Any]], dict[str, Any]],
    recoverable_errors: tuple[type[Exception], ...] = (ValueError,),
    inference: dict[str, Any] | None = None,
    candidate: str | None = None,
    language: str = "ko",
) -> dict[str, Any]:
    label = safe_label(label)
    if mode not in {"live", "offline-fixture"}:
        raise ValueError("Unknown execution mode.")
    if mode == "offline-fixture" and split != "dev":
        raise ValueError("Offline fixtures are dev-only; never fabricate holdout results.")
    cases = load_cases(root, split, language)
    if len(cases) > 20:
        raise ValueError(
            "Workshop batches are capped at 20 cases. Review costs before designing a larger experiment."
        )
    _, prompt_hash = load_prompt(root, prompt_version, language)
    manifest = {
        "run_id": str(uuid.uuid4()),
        "created_at": datetime.now(UTC).isoformat(),
        "status": "collecting",
        "mode": mode,
        "language": language,
        "split": split,
        "prompt_version": prompt_version,
        "prompt_hash": prompt_hash,
        "retrieval": retrieval,
        "deployment": deployment,
        "dataset_hash": digest(cases),
        "corpus_hash": digest(load_documents(root, language)),
        "code_hash": code_hash(root),
        "inference": inference,
        "expected_rows": len(cases),
        "concurrency": 1,
        "frozen_candidate": None,
    }
    if split == "holdout":
        if not candidate:
            raise ValueError("Holdout requires an explicit frozen --candidate dev run.")
        frozen, frozen_rows, frozen_cases = load_run(root, candidate)
        if frozen["mode"] != "live" or frozen["split"] != "dev":
            raise ValueError("The frozen candidate must be a real dev run.")
        if frozen.get("language", "ko") != language:
            raise ValueError("Holdout language differs from the frozen candidate.")
        if not summarize(frozen_rows, frozen_cases)["business_gate_passed"]:
            raise ValueError(
                "Resolve the candidate's dev business failures before opening holdout."
            )
        for key in (
            "mode",
            "prompt_hash",
            "deployment",
            "retrieval",
            "corpus_hash",
            "code_hash",
            "inference",
        ):
            if frozen[key] != manifest[key]:
                raise ValueError(f"Holdout differs from the frozen candidate's {key}.")
        manifest["frozen_candidate"] = {
            "label": candidate,
            "run_id": frozen["run_id"],
            "manifest_hash": digest(frozen),
        }
    elif candidate:
        raise ValueError("--candidate applies only to holdout.")
    directory = root / "outputs" / label
    directory.mkdir(parents=True, exist_ok=False)
    write_json(directory / "manifest.json", manifest)
    rows = []
    with (directory / "responses.jsonl").open("x", encoding="utf-8") as handle:
        for case in cases:
            common = {
                key: manifest[key]
                for key in ("run_id", "mode", "prompt_hash", "deployment", "retrieval")
            }
            common.update(case_id=case["case_id"], question=case["question"])
            started = time.perf_counter()
            try:
                response = answer_case(case)
                if mode == "live" and (
                    not isinstance(response.get("response_id"), str)
                    or not isinstance(response.get("response_model"), str)
                    or not response["response_id"]
                    or not response["response_model"]
                ):
                    raise ValueError(
                        "A real response must include its service response ID and observed model."
                    )
                row = {**response, **common, "status": "ok"}
            except recoverable_errors as exc:
                if split == "holdout":
                    guidance = (
                        "Do not repeat or recollect holdout cases. Preserve every row and use "
                        "evaluate and accept locally on this saved run; if its prerequisites "
                        "are incomplete, hand off that outcome."
                    )
                elif mode == "offline-fixture":
                    guidance = "Inspect the bundled fixture and offline checker; do not make an Azure call."
                else:
                    guidance = (
                        "Investigate this dev case with the answer command only after checking "
                        "the configuration and request cost."
                    )
                row = {
                    **(exc.details if isinstance(exc, ModelOutputError) else {}),
                    **common,
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error": f"Collection failed. {guidance} No fallback was used.",
                }
            row["latency_seconds"] = (
                round(time.perf_counter() - started, 4) if mode == "live" else None
            )
            rows.append(row)
            handle.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
            handle.flush()
    manifest.update(
        status="completed_with_errors"
        if any(row["status"] == "error" for row in rows)
        else "completed",
        actual_rows=len(rows),
        responses_hash=digest(rows),
        observed_models=sorted(
            {
                row["response_model"]
                for row in rows
                if isinstance(row.get("response_model"), str) and row["response_model"]
            }
        ),
    )
    write_json(directory / "manifest.json", manifest)
    summary = {"label": label, "mode": mode, "split": split, **summarize(rows, cases)}
    write_json(directory / "business-evaluation.json", summary)
    return summary


def offline_demo(
    root: Path, label: str, prompt_version: str, *, language: str = "ko"
) -> dict[str, Any]:
    fixture = read_json(localized_path(root, "data/fixtures/answers.json", language))
    context = evidence(load_documents(root, language), "offline-fixture")

    def answer_case(case: dict[str, Any]) -> dict[str, Any]:
        answer = dict(fixture[case["case_id"]])
        if prompt_version == "v1":
            answer["citations"] = []
        return {
            "answer": answer,
            **context,
            "response_id": None,
            "request_id": None,
            "trace_id": None,
            "usage": None,
            "fixture_notice": "Manually specified teaching fixture; no LLM, retrieval service or Azure call.",
        }

    return collect(
        root,
        label=label,
        split="dev",
        prompt_version=prompt_version,
        retrieval="offline-fixture",
        mode="offline-fixture",
        deployment="not-a-model",
        answer_case=answer_case,
        language=language,
    )
