import time
from pathlib import Path
from typing import Any

from .cloud import project_clients
from .contracts import digest, read_json, safe_label, write_json
from .settings import Settings, owned_prefix, require_env


def evaluate_items(
    settings: Settings,
    directory: Path,
    items: list[dict[str, Any]],
    *,
    label: str,
    source_run_id: str,
    dataset_hash: str,
    forbidden_deployments: set[str],
    evaluator_names: tuple[str, ...],
    confirmed: bool,
    timeout: int,
    reference_catalog: Path | None = None,
    retry_failed: bool = False,
    messages_input: bool = False,
    evaluation_level: str = "turn",
    custom_catalog: dict[str, dict[str, Any]] | None = None,
    reference_state: Path | None = None,
    retry_advice: bool = False,
) -> dict[str, Any]:
    from azure.ai.projects.models import TestingCriterionAzureAIEvaluator

    from .cloud_evaluation import normalize_results

    if not confirmed:
        raise ValueError("Native judges are billable; explicitly pass --confirm-cost.")
    if not 5 <= timeout <= 900 or not items or not evaluator_names:
        raise ValueError("Provide evaluation items/evaluators and a timeout of 5-900 seconds.")
    if evaluation_level not in {"turn", "conversation"} or (
        evaluation_level == "conversation" and not messages_input
    ):
        raise ValueError("Conversation-level evaluation requires explicit messages input.")
    if any(not isinstance(item, dict) or "case_id" not in item for item in items):
        raise ValueError("Every native evaluation item needs an explicit case ID.")
    ids = [item["case_id"] for item in items]
    if any(not isinstance(value, str) or not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("Native evaluation items must have unique nonempty case IDs.")
    if messages_input:
        if any(
            set(item) != {"case_id", "messages"}
            or not isinstance(item["messages"], list)
            or not item["messages"]
            or any(
                not isinstance(message, dict)
                or set(message) != {"role", "content"}
                or message["role"] not in {"system", "user", "assistant"}
                or not isinstance(message["content"], str)
                or not message["content"].strip()
                for message in item["messages"]
            )
            or item["messages"][-1]["role"] != "assistant"
            or not any(message["role"] == "user" for message in item["messages"])
            for item in items
        ):
            raise ValueError(
                "Message evaluation requires complete text conversations with explicit roles."
            )
    elif any(not isinstance(value, str) for item in items for value in item.values()):
        raise ValueError("Native evaluation items must have unique case IDs and string fields.")
    judge = require_env("AZURE_AI_EVALUATION_MODEL_DEPLOYMENT_NAME")
    if judge in forbidden_deployments:
        raise ValueError(
            "The judge deployment must be explicitly separate from every target deployment."
        )
    directory.mkdir(parents=True, exist_ok=True)
    state_path = directory / "cloud-evaluation.json"
    catalog_path = directory / "evaluator-catalog.json"
    identity = {
        "source_run_id": source_run_id,
        "input_hash": digest(items),
        "dataset_hash": dataset_hash,
        "judge_deployment": judge,
        "project_endpoint": settings.project_endpoint,
    }
    if messages_input:
        identity.update(input_format="messages", evaluation_level=evaluation_level)
    reference_run = None
    if reference_state is not None:
        if messages_input:
            raise ValueError("A shared reference evaluation applies to a query-response run.")
        reference_run = read_json(reference_state)
        if (
            reference_run.get("status") != "completed"
            or reference_run.get("validation_status") != "valid"
            or reference_run.get("evaluator_names") != list(evaluator_names)
            or reference_run.get("item_fields") != sorted(items[0])
            or reference_run.get("dataset_hash") != dataset_hash
            or reference_run.get("judge_deployment") != judge
            or reference_run.get("project_endpoint") != settings.project_endpoint
        ):
            raise ValueError(
                "The reference must be a completed, validated run with the same evaluators, "
                "fields, dataset, judge and project."
            )
        if reference_run.get("source_run_id") == source_run_id:
            raise ValueError("Compare a different run; do not reuse the reference's own responses.")
        identity["reference_run_id"] = reference_run["run_id"]
    state = read_json(state_path) if state_path.exists() else dict(identity)
    if retry_failed and state.get("reference_run_id") != identity.get("reference_run_id"):
        raise ValueError(
            "Retry with the same reference as the failed attempt; the retry then joins that evaluation."
        )
    if (
        state.get("input_format", "query-response")
        != ("messages" if messages_input else "query-response")
        or state.get("evaluation_level", "turn") != evaluation_level
    ):
        raise ValueError("The saved evaluation uses a different input format or evaluation level.")
    if "dataset_hash" not in state and "evaluation_id" in state:
        if "evaluator_names" in state or evaluator_names != ("groundedness", "relevance"):
            raise ValueError(
                "Only the original legacy evaluation schema may derive a missing dataset hash."
            )
        state["dataset_hash"] = dataset_hash
        state["legacy_schema_checked"] = True
    for key, value in identity.items():
        if state.get(key) != value:
            raise ValueError(f"The saved native evaluation changed {key}.")
    if state.get("evaluator_names", list(evaluator_names)) != list(evaluator_names):
        raise ValueError("The saved native evaluation uses a different evaluator set.")
    if "evaluator_names" not in state and "evaluation_id" in state:
        if evaluator_names != ("groundedness", "relevance"):
            raise ValueError("A legacy evaluation can only resume its original two evaluators.")
        state["legacy_schema_checked"] = True
    state["evaluator_names"] = list(evaluator_names)
    if not messages_input:
        state["item_fields"] = sorted(items[0])
    if retry_failed:
        if (
            state.get("status") not in {"failed", "canceled", "cancelled"}
            and state.get("validation_status") != "invalid"
        ):
            raise ValueError(
                "Only a failed/invalid attempt can be retried, not a completed low score."
            )
        if not catalog_path.is_file() or state.get("evaluator_hash") != digest(
            read_json(catalog_path)
        ):
            raise ValueError(
                "A failed attempt's evaluator catalog must remain unchanged before retry."
            )
        original_evaluator_hash = state["evaluator_hash"]
        attempts = directory / "native-attempts"
        attempts.mkdir(exist_ok=True)
        number = len(list(attempts.iterdir())) + 1
        attempt = attempts / f"attempt-{number}"
        attempt.mkdir()
        for name in (
            "cloud-evaluation.json",
            "cloud-evaluation-raw.json",
            "cloud-evaluation-results.json",
        ):
            path = directory / name
            if path.exists():
                path.rename(attempt / name)
        state = {
            **identity,
            "evaluator_names": list(evaluator_names),
            **({} if messages_input else {"item_fields": sorted(items[0])}),
            "evaluator_hash": original_evaluator_hash,
            "retry_of": {
                "evaluation_id": state.get("evaluation_id"),
                "run_id": state.get("run_id"),
                "attempt": number,
            },
        }
    with project_clients(settings, preview=True) as (project, client):
        if catalog_path.exists():
            catalog = read_json(catalog_path)
            if reference_catalog is not None:
                reference = [
                    item for item in read_json(reference_catalog) if item["name"] in evaluator_names
                ]
                if digest(reference) != digest(catalog):
                    raise ValueError(
                        "The requested reference catalog differs from this frozen evaluation."
                    )
        elif reference_catalog is not None:
            source = read_json(reference_catalog)
            catalog = [item for item in source if item["name"] in evaluator_names]
        else:
            catalog = []
            for name in evaluator_names:
                if custom_catalog and name in custom_catalog:
                    custom = custom_catalog[name]
                    catalog.append(
                        {
                            "name": name,
                            "evaluator_name": custom["evaluator_name"],
                            "definition": custom["definition"],
                            "parameters": {"deployment_name": judge, "pass_threshold": 1.0},
                        }
                    )
                    continue
                definition = project.beta.evaluators.get_version(
                    f"builtin.{name}", "latest"
                ).as_dict()
                properties = definition["definition"]["init_parameters"]["properties"]
                fields = [field for field in ("model", "deployment_name") if field in properties]
                if len(fields) != 1:
                    raise ValueError(
                        f"Unsupported {name} initialization schema; inspect the actual catalog."
                    )
                parameters = {fields[0]: judge}
                if "threshold" in properties:
                    parameters["threshold"] = 4
                if messages_input:
                    if evaluation_level not in definition.get("supported_evaluation_levels", []):
                        raise ValueError(
                            f"{name} does not advertise support for {evaluation_level}."
                        )
                    if "evaluation_level" in properties:
                        parameters["evaluation_level"] = evaluation_level
                catalog.append({"name": name, "definition": definition, "parameters": parameters})
        if (
            len(catalog) != len(evaluator_names)
            or {item["name"] for item in catalog} != set(evaluator_names)
            or any(not item["definition"].get("version") for item in catalog)
        ):
            raise ValueError("The catalog must pin exactly the requested evaluator versions.")
        for item in catalog:
            parameters = item["parameters"]
            if messages_input and (
                evaluation_level not in item["definition"].get("supported_evaluation_levels", [])
                or parameters.get("evaluation_level", evaluation_level) != evaluation_level
            ):
                raise ValueError(
                    "The frozen evaluator does not match the requested evaluation level."
                )
            models = [parameters[key] for key in ("model", "deployment_name") if key in parameters]
            if models != [judge]:
                raise ValueError("The frozen evaluator catalog uses a different judge deployment.")
        if state.get("evaluator_hash", digest(catalog)) != digest(catalog):
            raise ValueError("The evaluator catalog changed after job creation.")
        write_json(catalog_path, catalog)
        state["evaluator_hash"] = digest(catalog)
        if "evaluation_id" not in state and reference_run is not None:
            state["evaluation_id"] = reference_run["evaluation_id"]
            state["reference_evaluation"] = {
                "evaluation_id": reference_run["evaluation_id"],
                "run_id": reference_run["run_id"],
            }
            write_json(state_path, state)
        if "evaluation_id" not in state:
            criteria = [
                TestingCriterionAzureAIEvaluator(
                    type="azure_ai_evaluator",
                    name=item["name"],
                    evaluator_name=item.get("evaluator_name", f"builtin.{item['name']}"),
                    evaluator_version=item["definition"]["version"],
                    initialization_parameters=item["parameters"],
                    **(
                        {}
                        if "evaluator_name" in item
                        else {
                            "data_mapping": {"messages": "{{item.messages}}"}
                            if messages_input
                            else {
                                "query": "{{item.query}}",
                                "response": "{{item.response}}",
                                **(
                                    {"context": "{{item.context}}"}
                                    if item["name"] == "groundedness"
                                    else {}
                                ),
                            }
                        }
                    ),
                )
                for item in catalog
            ]
            evaluation = client.evals.create(
                name=f"{owned_prefix()}-{safe_label(label)}"[:63],
                data_source_config={
                    "type": "custom",
                    "item_schema": {
                        "type": "object",
                        "properties": {
                            key: {
                                "type": "array"
                                if messages_input and key == "messages"
                                else "string"
                            }
                            for key in items[0]
                        },
                        "required": list(items[0]),
                    },
                },
                testing_criteria=criteria,
                metadata={"source_run_id": source_run_id, "dataset_hash": dataset_hash},
            )
            state["evaluation_id"] = evaluation.id
            write_json(state_path, state)
        if "run_id" not in state:
            retry = state.get("retry_of") or {}
            if "reference_evaluation" in state and "attempt" in retry:
                # The invalid run stays in the shared evaluation; a distinct name keeps Compare runs clear.
                state["run_name"] = f"{label}-retry-{retry['attempt']}"
            run = client.evals.runs.create(
                eval_id=state["evaluation_id"],
                name=state.get("run_name", label),
                data_source={
                    "type": "jsonl",
                    "source": {
                        "type": "file_content",
                        "content": [{"item": item} for item in items],
                    },
                },
                **(
                    {"extra_body": {"evaluation_level": evaluation_level}} if messages_input else {}
                ),
            )
            state["run_id"] = run.id
            write_json(state_path, state)
        deadline = time.monotonic() + timeout
        while True:
            run = client.evals.runs.retrieve(run_id=state["run_id"], eval_id=state["evaluation_id"])
            state.update(
                status=run.status, report_url=run.report_url, run=run.model_dump(mode="json")
            )
            write_json(state_path, state)
            if run.status in {"completed", "failed", "canceled", "cancelled"}:
                break
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    "The native run is still running. Resume this label; do not submit another job."
                )
            time.sleep(5)
        if run.status != "completed":
            message = f"Native evaluation ended with {run.status}; the attempt is retained."
            raise ValueError(f"{message} {kept_attempt_advice(state)}" if retry_advice else message)
        raw_items = [
            item.model_dump(mode="json")
            for item in client.evals.runs.output_items.list(
                run_id=state["run_id"], eval_id=state["evaluation_id"]
            )
        ]
        write_json(directory / "cloud-evaluation-raw.json", raw_items)
        try:
            normalized = normalize_results(raw_items, ids, evaluator_names)
        except ValueError as error:
            state["validation_status"] = "invalid"
            write_json(state_path, state)
            if retry_advice:
                raise ValueError(f"{error} {kept_attempt_advice(state)}") from error
            raise
        state["validation_status"] = "valid"
        state["results_hash"] = digest(normalized)
        write_json(directory / "cloud-evaluation-results.json", normalized)
        write_json(state_path, state)
    return {
        "mode": "live",
        "label": label,
        "evaluation_id": state["evaluation_id"],
        "run_id": state["run_id"],
        "report_url": state["report_url"],
        "rows": len(normalized),
        "evaluator_hash": state["evaluator_hash"],
        **(
            {"reference_run_id": state["reference_evaluation"]["run_id"]}
            if "reference_evaluation" in state
            else {}
        ),
        **({"run_name": state["run_name"]} if "run_name" in state else {}),
        **(
            {"input_format": "messages", "evaluation_level": evaluation_level}
            if messages_input
            else {}
        ),
        "native_pass_counts": {
            name: {
                "passed": sum(
                    item["passed"]
                    for row in normalized
                    for item in row["results"]
                    if item["name"] == name
                ),
                "total": len(normalized),
            }
            for name in evaluator_names
        },
        "note": "Native judge scores remain separate from business checks and target-agent execution.",
    }


def kept_attempt_advice(state: dict[str, Any]) -> str:
    if state.get("retry_of"):
        return (
            "This retry is not valid either; keep native-attempts/ and report it "
            "instead of retrying again."
        )
    return "Rerun the same command once with --retry-failed; the attempt moves to native-attempts/."


def verified_native(directory: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    state = read_json(directory / "cloud-evaluation.json")
    results = read_json(directory / "cloud-evaluation-results.json")
    if state.get("status") != "completed" or state.get("validation_status") != "valid":
        raise ValueError("A completed and row-validated native evaluation is required.")
    if state.get("results_hash") != digest(results):
        raise ValueError("Native evaluation results changed after validation.")
    if state["evaluator_hash"] != digest(read_json(directory / "evaluator-catalog.json")):
        raise ValueError("The native evaluator definition changed.")
    return state, results
