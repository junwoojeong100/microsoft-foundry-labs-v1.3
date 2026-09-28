import json
import os
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlsplit

import httpx
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import TestingCriterionAzureAIEvaluator
from azure.core.pipeline.transport import HttpResponse, HttpTransport

from foundry_workshop.calibration import calibrate, verify_calibration
from foundry_workshop.contracts import digest, read_json, write_json
from foundry_workshop.native import evaluate_items, verified_native
from foundry_workshop.policy_evaluation import (
    POLICY_EVALUATORS,
    POLICY_MAPPING,
    ensure_policy_evaluators,
    policy_evaluator_version,
)
from tests import workspace
from tests.test_policy_evaluation import policy_catalog, policy_outputs, policy_rows

from .test_sdk_contracts import DummyCredential, settings


class PolicyNativeTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {
            "WORKSHOP_PREFIX": "lab-unit",
            "AZURE_AI_EVALUATION_MODEL_DEPLOYMENT_NAME": "unit-judge",
            "WORKSHOP_MODEL_DEPLOYMENTS_JSON": '{"target":"unit-deployment"}',
        }, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.corpus, _, _, self.items = policy_rows("ko")
        self.create_calls, self.run_calls = [], []
        self.raw_transform = lambda raw: raw
        self.labels = None
        self.status = "completed"

    @contextmanager
    def clients(self, *_args, **_kwargs):
        def create(**kwargs):
            self.create_calls.append(kwargs)
            return SimpleNamespace(id=f"eval_unit_{len(self.create_calls)}")

        def create_run(**kwargs):
            self.run_calls.append(kwargs)
            return SimpleNamespace(id=f"evalrun_unit_{len(self.run_calls)}")

        def retrieve(**_kwargs):
            return SimpleNamespace(
                status=self.status, report_url="https://ai.azure.com/unit-policy",
                model_dump=lambda **_: {"status": self.status},
            )

        def output_items(**_kwargs):
            inputs = [row["item"] for row in self.run_calls[-1]["data_source"]["source"]["content"]]
            raw = self.raw_transform(policy_outputs(inputs, self.labels))
            return [SimpleNamespace(model_dump=lambda value=value, **_: value) for value in raw]

        client = SimpleNamespace(evals=SimpleNamespace(
            create=create,
            runs=SimpleNamespace(
                create=create_run, retrieve=retrieve,
                output_items=SimpleNamespace(list=output_items),
            ),
        ))
        yield SimpleNamespace(), client

    def evaluate(self, path, **kwargs):
        custom = {
            item["name"]: {key: value for key, value in item.items() if key != "name"}
            for item in policy_catalog()
        }
        options = {
            "label": "unit-policy", "source_run_id": "unit-source", "dataset_hash": "unit-dataset",
            "forbidden_deployments": {"unit-deployment"}, "evaluator_names": POLICY_EVALUATORS,
            "confirmed": True, "timeout": 5, "custom_catalog": custom,
            "policy_reference_audit": True, "policy_source_corpora": [self.corpus],
            **kwargs,
        }
        with patch("foundry_workshop.native.project_clients", self.clients):
            return evaluate_items(settings(), path, self.items, **options)

    def test_explicit_custom_parameters_mapping_and_all_raw_scores_are_preserved(self):
        with workspace() as root:
            result = self.evaluate(root / "native")
            state, scores = verified_native(root / "native")
            self.assertEqual(result["validation_status"], "valid")
            self.assertEqual(result["rows"], 2)
            self.assertEqual(state["policy_reference_audit_hash"], digest(
                read_json(root / "native/policy-reference-audit.json")
            ))
            self.assertEqual(read_json(root / "native/policy-evaluation-inputs.json"), self.items)
            for item in self.create_calls[0]["testing_criteria"]:
                self.assertEqual(item["type"], "azure_ai_evaluator")
                self.assertEqual(item["evaluator_version"], "17")
                self.assertEqual(item["initialization_parameters"], {"model": "unit-judge", "pass_threshold": 4})
                self.assertEqual(item["data_mapping"], POLICY_MAPPING)
            self.assertEqual(scores[0]["results"], policy_outputs(self.items)[0]["results"])
            self.assertFalse(result["policy_reference_audit"]["judge_request_bodies_captured"])

    def test_ga_iq_projections_survive_native_submission_and_reference_audit_unchanged(self):
        from foundry_workshop.knowledge import evidence
        from foundry_workshop.policy_evaluation import policy_item

        self.corpus, cases, rows, _ = policy_rows("ko")
        self.items = []
        for row, case in zip(rows, cases, strict=True):
            documents = [
                {key: doc[key] for key in ("id", "title", "content")}
                for doc in row["documents"]
            ]
            self.items.append(policy_item({**row, **evidence(documents, "unit-ga-iq")}, case, self.corpus))
        with workspace() as root:
            self.evaluate(root / "native")
            state, _ = verified_native(root / "native")
            submitted = self.run_calls[0]["data_source"]["source"]["content"]
            saved = read_json(root / "native/policy-evaluation-inputs.json")
            self.assertEqual(saved, self.items)
            self.assertEqual(state["validation_status"], "valid")
            for source, item in zip(submitted, self.items, strict=True):
                self.assertEqual(source["item"], item)
                reference = json.loads(item["ground_truth"])
                self.assertEqual(reference["source_documents"], json.loads(item["context"]))
                self.assertTrue(all(
                    set(doc) == {"id", "title", "content"} for doc in reference["source_documents"]
                ))
            self.assertEqual(read_json(root / "native/policy-source-corpora.json"), [self.corpus])

    def test_valid_policy_cache_is_read_only_and_does_not_resubmit_or_fetch_outputs(self):
        with workspace() as root:
            path = root / "native"
            first = self.evaluate(path)
            before = {file.name: file.read_bytes() for file in path.iterdir()}
            with patch("foundry_workshop.native.project_clients") as clients:
                # The helper must not enter the client even if a provider would now return other scores.
                self.raw_transform = lambda _: []
                self.assertEqual(self.evaluate(path), first)
                clients.assert_not_called()
            self.assertEqual(before, {file.name: file.read_bytes() for file in path.iterdir()})
            self.assertEqual(len(self.run_calls), 1)
            with self.assertRaisesRegex(ValueError, "Only a failed/invalid"):
                self.evaluate(path, retry_failed=True)

    def test_invalid_provider_direction_is_retained_and_retry_archives_the_invalid_audit(self):
        def contradiction(raw):
            raw[0]["results"][0].update(score=5, passed=False)
            return raw

        self.raw_transform = contradiction
        with workspace() as root:
            path = root / "native"
            with self.assertRaisesRegex(ValueError, "pass iff score"):
                self.evaluate(path)
            self.assertFalse((path / "cloud-evaluation-results.json").exists())
            state = read_json(path / "cloud-evaluation.json")
            self.assertEqual(state["validation_status"], "invalid")
            before = (path / "cloud-evaluation-raw.json").read_bytes()
            self.raw_transform = lambda raw: raw
            self.evaluate(path, retry_failed=True)
            attempt = path / "native-attempts/attempt-1"
            self.assertEqual((attempt / "cloud-evaluation-raw.json").read_bytes(), before)
            self.assertEqual(read_json(attempt / "policy-reference-audit.json")["status"], "invalid")
            self.assertEqual(read_json(path / "policy-reference-audit.json")["status"], "valid")
            self.assertEqual(self.create_calls[0]["testing_criteria"], self.create_calls[1]["testing_criteria"])

    def test_missing_duplicate_echo_or_reason_never_sets_valid(self):
        def wrong_echo(raw):
            raw[0]["datasource_item"]["ground_truth"] = self.items[1]["ground_truth"]
            return raw

        def missing_reason(raw):
            raw[0]["results"][0]["reason"] = "Safe but no reference identifier."
            return raw

        for change in (
            lambda raw: raw[:-1],
            lambda raw: [raw[0], raw[0]],
            wrong_echo,
            missing_reason,
        ):
            with workspace() as root:
                self.raw_transform = change
                with self.assertRaises(ValueError):
                    self.evaluate(root / "native")
                self.assertEqual(read_json(root / "native/cloud-evaluation.json")["validation_status"], "invalid")
                self.assertFalse((root / "native/cloud-evaluation-results.json").exists())
                self.assertTrue((root / "native/cloud-evaluation-raw.json").exists())

    def test_verification_requires_the_original_audit_artifacts_and_mode(self):
        for changed in ("audit", "inputs", "raw", "mode", "threshold"):
            with self.subTest(changed=changed), workspace() as root:
                path = root / "native"
                self.evaluate(path)
                if changed == "audit":
                    value = read_json(path / "policy-reference-audit.json")
                    value["status"] = "invalid"
                    write_json(path / "policy-reference-audit.json", value)
                elif changed == "inputs":
                    value = read_json(path / "policy-evaluation-inputs.json")
                    value[0]["ground_truth"] = value[0]["response"]
                    write_json(path / "policy-evaluation-inputs.json", value)
                elif changed == "raw":
                    value = read_json(path / "cloud-evaluation-raw.json")
                    value.pop()
                    write_json(path / "cloud-evaluation-raw.json", value)
                elif changed == "mode":
                    value = read_json(path / "cloud-evaluation.json")
                    value.pop("policy_mode")
                    write_json(path / "cloud-evaluation.json", value)
                else:
                    value = read_json(path / "evaluator-catalog.json")
                    value[0]["parameters"]["pass_threshold"] = 1
                    write_json(path / "evaluator-catalog.json", value)
                with self.assertRaises(ValueError):
                    verified_native(path)

    def test_reference_runs_share_exact_criteria_but_cannot_change_mapping(self):
        with workspace() as root:
            base = root / "baseline"
            self.evaluate(base)
            options = {
                "source_run_id": "candidate-source",
                "reference_catalog": base / "evaluator-catalog.json",
                "reference_state": base / "cloud-evaluation.json",
            }
            self.items[0]["response"] += " Different generated target response."
            candidate = self.evaluate(root / "candidate", **options)
            self.assertEqual(candidate["reference_run_id"], "evalrun_unit_1")
            self.assertEqual(len(self.create_calls), 1)
            self.assertEqual(self.run_calls[0]["eval_id"], self.run_calls[1]["eval_id"])
            frozen = read_json(base / "evaluator-catalog.json")
            frozen[0]["data_mapping"]["ground_truth"] = "{{item.response}}"
            write_json(base / "evaluator-catalog.json", frozen)
            with self.assertRaises(ValueError):
                self.evaluate(root / "another", **options)

    def test_policy_names_cannot_bypass_audit_or_replace_cached_reference_versions(self):
        with workspace() as root:
            with self.assertRaisesRegex(ValueError, "explicit source-reference audit"):
                self.evaluate(
                    root / "unverified", policy_reference_audit=False, policy_source_corpora=None
                )
            self.assertFalse(self.create_calls)
            path = root / "native"
            self.evaluate(path)
            reference = policy_catalog()
            reference[0]["definition"]["version"] = "18"
            write_json(root / "changed-reference.json", reference)
            with self.assertRaisesRegex(ValueError, "reference catalog differs"):
                self.evaluate(path, reference_catalog=root / "changed-reference.json")
            self.assertEqual(len(self.run_calls), 1)

    def test_policy_calibration_has_separate_fixture_mode_and_acceptance_validates_metadata(self):
        with workspace() as root:
            reference = root / "known-catalog.json"
            write_json(reference, policy_catalog())
            fixture = read_json(root / "data/evaluation/policy-calibration.json")
            self.labels = {control["case"]["case_id"]: control["expected_pass"] for control in fixture["controls"]}
            with patch("foundry_workshop.native.project_clients", self.clients):
                result = calibrate(
                    root, settings(), "policy-controls", confirmed=True, timeout=5,
                    reference_catalog=reference, policy=True,
                )
            self.assertTrue(result["gate_passed"])
            self.assertEqual(result["total_controls"], 8)
            self.assertFalse(result["target_responses_generated"])
            self.labels = None
            target = root / "target"
            self.evaluate(target)
            verified = verify_calibration(root, "policy-controls", target, policy=True)
            self.assertTrue(verified["gate_passed"])
            self.corpus, _, _, self.items = policy_rows("en")
            self.evaluate(root / "other-language")
            with self.assertRaisesRegex(ValueError, "source language/corpus"):
                verify_calibration(root, "policy-controls", root / "other-language", policy=True)
            with self.assertRaisesRegex(ValueError, "mode"):
                verify_calibration(root, "policy-controls", target)
            metadata_path = root / "outputs/judge-calibration/policy-controls/manifest.json"
            metadata = read_json(metadata_path)
            metadata["criteria_hash"] = "legacy-or-revised"
            write_json(metadata_path, metadata)
            with self.assertRaisesRegex(ValueError, "fresh"):
                verify_calibration(root, "policy-controls", target, policy=True)

    def test_cloud_policy_mode_preserves_existing_builtin_evidence_and_pins_reference_runs(self):
        from foundry_workshop.cloud_evaluation import evaluate_cloud
        from foundry_workshop.contracts import load_documents
        from foundry_workshop.experiments import collect
        from foundry_workshop.knowledge import evidence

        with workspace() as root:
            def response(case):
                return {
                    **evidence(load_documents(root), "unit-test"),
                    "response_id": "unit-response-" + case["case_id"],
                    "response_model": "unit-model",
                    "answer": {
                        "answer": f"Explicit unit fixture {case['expected_limit_krw']}.",
                        "decision": case["expected_decision"],
                        "limit_krw": case["expected_limit_krw"],
                        "citations": case["required_citations"],
                    },
                }

            for label in ("baseline", "candidate"):
                collect(
                    root, label=label, split="dev", prompt_version="v2", retrieval="local",
                    mode="live", deployment="unit-deployment", answer_case=response,
                )
            earlier = root / "outputs/baseline/cloud-evaluation-raw.json"
            write_json(earlier, [{"builtin": "preserve this earlier result verbatim"}])
            before = earlier.read_bytes()
            custom = {
                entry["name"]: {key: value for key, value in entry.items() if key != "name"}
                for entry in policy_catalog()
            }
            with (
                patch("foundry_workshop.native.project_clients", self.clients),
                patch("foundry_workshop.cloud.project_clients", self.clients),
                patch("foundry_workshop.policy_evaluation.ensure_policy_evaluators", return_value=custom),
            ):
                baseline = evaluate_cloud(
                    root, settings(), "baseline", timeout=5, confirmed=True, policy=True
                )
                candidate = evaluate_cloud(
                    root, settings(), "candidate", timeout=5, confirmed=True, policy=True,
                    reference="baseline",
                )
            self.assertEqual(earlier.read_bytes(), before)
            self.assertEqual(set(baseline["native_pass_counts"]), set(POLICY_EVALUATORS))
            self.assertEqual(baseline["rows"], 6)
            self.assertEqual(candidate["reference_run_id"], baseline["run_id"])
            self.assertEqual(len(self.create_calls), 1)
            sources = self.run_calls[0]["data_source"]["source"]["content"]
            d05 = next(row["item"] for row in sources if row["item"]["case_id"] == "D05")
            self.assertEqual(json.loads(d05["ground_truth"])["expected_decision"], "insufficient_evidence")
            self.assertEqual(json.loads(d05["ground_truth"])["corpus_hash"], digest(load_documents(root)))


class SDKReply(HttpResponse):
    def __init__(self, request, status, payload):
        super().__init__(request, None)
        self.status_code = status
        self.headers = {"content-type": "application/json"}
        self.content_type = "application/json"
        self._body = json.dumps(payload).encode()

    def body(self):
        return self._body

    def json(self):
        return json.loads(self._body)


class EvaluatorTransport(HttpTransport):
    def __init__(self):
        self.requests = []
        self.versions = {}

    def open(self):
        return self

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def send(self, request, **_kwargs):
        self.requests.append(request)
        path = urlsplit(request.url).path
        if "evaluators" not in path:
            raise AssertionError(f"Unexpected offline SDK request: {path}")
        if request.method == "POST":
            payload = json.loads(request.body)
            saved = {**payload, "version": "17"}
            self.versions[payload["name"]] = saved
            return SDKReply(request, 201, saved)
        values = [value for name, value in self.versions.items() if name in path]
        if not values:
            return SDKReply(request, 404, {"error": {"code": "NotFound", "message": "Unit missing evaluator"}})
        return SDKReply(request, 200, {"data": values, "value": values, "has_more": False})


class PolicySDKContractTests(unittest.TestCase):
    def test_real_sdk_preserves_custom_definition_and_ground_truth_mapping(self):
        transport = EvaluatorTransport()
        serialized = []

        def handler(request):
            body = json.loads(request.content)
            serialized.append(body)
            return httpx.Response(200, json={
                "id": "eval_unit", "object": "eval", "created_at": 1,
                "name": body["name"], "data_source_config": body["data_source_config"],
                "testing_criteria": body["testing_criteria"], "metadata": {},
            })

        with AIProjectClient(
            endpoint=settings().project_endpoint, credential=DummyCredential(), transport=transport
        ) as project:
            catalog = ensure_policy_evaluators(project, "lab-unit", "unit-judge")
            repeated = ensure_policy_evaluators(project, "lab-unit", "unit-judge")
            self.assertEqual(catalog, repeated)
            with httpx.Client(transport=httpx.MockTransport(handler)) as http:
                with project.get_openai_client(http_client=http, max_retries=0) as client:
                    client.evals.create(
                        name="unit-policy",
                        data_source_config={"type": "custom", "item_schema": {"type": "object"}},
                        testing_criteria=[
                            TestingCriterionAzureAIEvaluator(
                                type="azure_ai_evaluator", name=metric,
                                evaluator_name=entry["evaluator_name"],
                                evaluator_version=entry["definition"]["version"],
                                initialization_parameters=entry["parameters"],
                                data_mapping=entry["data_mapping"],
                            )
                            for metric, entry in catalog.items()
                        ],
                    )
        posts = [request for request in transport.requests if request.method == "POST"]
        self.assertEqual(len(posts), 3)
        for request in posts:
            body = json.loads(request.body)
            metric = next(name for name in POLICY_EVALUATORS if name in body["name"])
            self.assertEqual(body, policy_evaluator_version(body["name"], metric))
        for criterion in serialized[0]["testing_criteria"]:
            self.assertEqual(criterion["evaluator_version"], "17")
            self.assertEqual(criterion["initialization_parameters"], {"model": "unit-judge", "pass_threshold": 4})
            self.assertEqual(criterion["data_mapping"], POLICY_MAPPING)
            self.assertNotIn("sample.output", json.dumps(criterion))
