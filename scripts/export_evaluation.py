#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from foundry_workshop.contracts import digest, safe_label, write_json  # noqa: E402
from foundry_workshop.settings import Settings, credential_for, load_environment  # noqa: E402


def export_evaluation(
    client: Any,
    directory: Path,
    evaluation_id: str,
    run_id: str,
    expected_rows: int,
    *,
    require_judge_inputs: bool = False,
) -> dict:
    if (
        not re.fullmatch(r"eval_[A-Za-z0-9_-]+", evaluation_id)
        or not re.fullmatch(r"evalrun_[A-Za-z0-9_-]+", run_id)
        or expected_rows < 1
    ):
        raise ValueError("Use actual evaluation/run IDs and a positive expected row count.")
    directory.mkdir(parents=True, exist_ok=False)
    definition = client.evals.retrieve(evaluation_id).model_dump(mode="json")
    run = client.evals.runs.retrieve(run_id=run_id, eval_id=evaluation_id).model_dump(mode="json")
    write_json(directory / "definition.json", definition)
    write_json(directory / "run.json", run)
    if (
        definition.get("id") != evaluation_id
        or run.get("id") != run_id
        or run.get("eval_id") != evaluation_id
    ):
        raise ValueError("The returned evaluation/run IDs do not match the requested scope.")
    if run.get("status") != "completed":
        raise ValueError(
            "The run is not completed. Keep its state; inspect the same run later with a new export label."
        )
    items = [
        item.model_dump(mode="json")
        for item in client.evals.runs.output_items.list(run_id=run_id, eval_id=evaluation_id)
    ]
    write_json(directory / "output-items.json", items)
    row_ids = [item.get("datasource_item_id") for item in items]
    if (
        len(items) != expected_rows
        or any(
            isinstance(value, bool)
            or not isinstance(value, (str, int))
            or isinstance(value, str)
            and not value
            for value in row_ids
        )
        or len({str(value) for value in row_ids}) != expected_rows
    ):
        raise ValueError(
            "Missing, duplicate or unidentified output rows; original items were retained."
        )
    inputs_available = all(
        isinstance(item.get("results"), list)
        and bool(item["results"])
        and all(
            isinstance(result, dict)
            and isinstance(result.get("sample"), dict)
            and isinstance(result["sample"].get("input"), list)
            and bool(result["sample"]["input"])
            for result in item["results"]
        )
        for item in items
    )
    summary = {
        "mode": "read-only-evaluation-export",
        "evaluation_id": evaluation_id,
        "run_id": run_id,
        "expected_rows": expected_rows,
        "actual_rows": len(items),
        "judge_inputs_available": inputs_available,
        "definition_hash": digest(definition),
        "run_hash": digest(run),
        "output_items_hash": digest(items),
        "new_model_requests": False,
        "quality_approved": False,
        "note": "Export preserves scores and raw inputs. Check each evaluator's actual references; export success is not valid grounding or promotion approval.",
    }
    write_json(directory / "summary.json", summary)
    if require_judge_inputs and not inputs_available:
        raise ValueError(
            "Raw judge inputs are unavailable; review is incomplete, not a passing evaluation."
        )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read one completed Foundry evaluation without invoking a model or changing scores."
    )
    parser.add_argument("--evaluation-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--expected-rows", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--language", choices=("en", "ko"), default="ko")
    parser.add_argument("--require-judge-inputs", action="store_true")
    args = parser.parse_args()
    from azure.ai.projects import AIProjectClient
    from azure.core.exceptions import AzureError
    from openai import OpenAIError

    try:
        label = safe_label(args.label)
        load_environment(ROOT)
        settings = Settings.from_env(language=args.language)
        with (
            credential_for(settings) as credential,
            AIProjectClient(endpoint=settings.project_endpoint, credential=credential) as project,
            project.get_openai_client() as client,
        ):
            result = export_evaluation(
                client,
                ROOT / "outputs/evaluation-exports" / label,
                args.evaluation_id,
                args.run_id,
                args.expected_rows,
                require_judge_inputs=args.require_judge_inputs,
            )
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, AzureError, OpenAIError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
