import hashlib
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from foundry_workshop.benchmark import (
    approve_regression,
    collect_matrix,
    compare_matrices,
    directory,
    grade_strict,
    load_matrix,
    report_matrix,
    summarize_matrix,
    verify_release,
    wilson_interval,
)
from foundry_workshop.benchmark_cli import smoke
from foundry_workshop.calibration import calibration_summary
from foundry_workshop.cli import parser
from foundry_workshop.contracts import digest, load_cases, load_documents, read_json, write_json
from foundry_workshop.hosted import HostedBinding, parse_azd_http, validate_request
from foundry_workshop.knowledge import evidence
from foundry_workshop.observability import stop_matrix_session, trace_query, validate_trace_rows
from foundry_workshop.profiles import RuntimeProfile, model_deployments, runtime_contract
from foundry_workshop.settings import Settings

from . import workspace

MODELS = {name: f"unit-{name}" for name in ("alpha", "beta", "gamma", "delta")}


def settings():
    return Settings(
        project_endpoint="https://unit.services.ai.azure.com/api/projects/workshop",
        deployment="unit-alpha",
        tenant_id="00000000-0000-0000-0000-000000000001",
        auth_mode="cli",
        managed_identity_client_id=None,
        max_output_tokens=2048,
    )


def binding(version="1"):
    return HostedBinding(
        "lab-unit-hosted",
        version,
        "https://unit.services.ai.azure.com/api/projects/workshop/agents/lab-unit-hosted/endpoint/protocols/invocations?api-version=v1",
    )


class UnitTransport:
    """Explicit test fixture; never an Azure call or a runtime fixture fallback."""

    def __init__(self, root, profile, split, fail=None, text=None):
        self.contract = runtime_contract(root, settings(), profile)
        self.cases = {case["case_id"]: case for case in load_cases(root, split)}
        self.context = evidence(load_documents(root), "unit-test")
        self.fail, self.text = fail, text
        self.requests = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass

    def create_session(self):
        return "unit-session"

    def invoke(self, payload):
        self.requests.append(payload)
        if self.fail == (payload["model_key"], payload["case_id"]):
            return {"error": {"type": "HTTP503"}}, {"status_code": 503, "body": "unit failure"}
        case = self.cases[payload["case_id"]]
        response_id = f"unit-{payload['model_key']}-{payload['case_id']}"
        usage = {"input_tokens": 10, "output_tokens": 20}
        value = {
            **payload,
            **self.context,
            "mode": "live",
            "runtime_profile": self.contract["profile"],
            "runtime_contract": self.contract,
            "runtime_contract_hash": digest(self.contract),
            "deployment": MODELS[payload["model_key"]],
            "prompt_hash": self.contract["prompt_hash"],
            "effective_prompt_hash": self.contract["effective_prompt_hash"],
            "answer": {
                "answer": self.text or f"합성 기준 {case['expected_limit_krw']}원. 운영 승인 아님.",
                "decision": case["expected_decision"],
                "limit_krw": case["expected_limit_krw"],
                "citations": case["required_citations"],
            },
            "response_id": response_id,
            "response_model": "unit-model-" + payload["model_key"],
            "model_calls": [
                {
                    "response_id": response_id,
                    "response_model": "unit-model-" + payload["model_key"],
                    "usage": usage,
                }
            ],
            "usage": usage,
            "trace_id": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[
                :32
            ],
            "approval_status": "pending-human-review",
            "external_actions_performed": False,
        }
        return value, {"status_code": 200, "body": json.dumps(value, ensure_ascii=False)}


class BenchmarkTests(unittest.TestCase):
    def test_cleanup_records_already_idle_session_without_conflicting_stop(self):
        manifest = {
            "runtime_contract": {"project_endpoint": settings().project_endpoint},
            "binding": binding().to_dict(),
            "session_id": "unit-idle",
        }
        transport = MagicMock()
        transport.project.agents.get_session.return_value.as_dict.return_value = {
            "agent_session_id": "unit-idle",
            "status": "idle",
            "version_indicator": {"agent_version": "1"},
        }
        factory = MagicMock()
        factory.return_value.__enter__.return_value = transport
        with workspace() as root:
            with patch("foundry_workshop.benchmark.load_matrix", return_value=(manifest, [], [])):
                with patch("foundry_workshop.observability.HostedTransport", factory):
                    result = stop_matrix_session(root, settings(), "unit")
        transport.stop_session.assert_not_called()
        self.assertEqual(result["status"], "idle")
        self.assertFalse(result["stop_requested"])

    def test_smoke_does_not_combine_endpoint_and_protocol_flags(self):
        with patch.dict(
            os.environ,
            {
                "WORKSHOP_HOSTED_AGENT_NAME": binding().name,
                "WORKSHOP_HOSTED_AGENT_VERSION": binding().version,
                "WORKSHOP_HOSTED_AGENT_ENDPOINT": binding().endpoint,
            },
        ):
            for local in (True, False):
                with workspace() as root:
                    standalone = root / "standalone"
                    standalone.mkdir()
                    (standalone / "azure.yaml").write_text("name: explicit-unit-project\n")
                    with patch(
                        "foundry_workshop.benchmark_cli.subprocess.run",
                        return_value=SimpleNamespace(
                            returncode=1,
                            stdout=b"",
                            stderr=b"explicit unit-test failure",
                        ),
                    ) as invoked:
                        with self.assertRaises(ValueError):
                            smoke(
                                root,
                                settings(),
                                RuntimeProfile(protocol="invocations"),
                                label="smoke",
                                local=local,
                                model_key="alpha",
                                case_id="D01",
                                confirmed=True,
                                azd_directory=standalone if local else None,
                            )
                    command = invoked.call_args.args[0]
                    self.assertEqual(
                        command[:3], ["azd", "--cwd", str(standalone.resolve() if local else root)]
                    )
                    self.assertEqual("--protocol" in command, local)
                    self.assertEqual("--agent-endpoint" in command, not local)

    def test_local_smoke_requires_a_directory_before_any_output_or_azd_call(self):
        with (
            workspace() as root,
            patch("foundry_workshop.benchmark_cli.subprocess.run") as invoked,
            patch("foundry_workshop.benchmark_cli.runtime_contract") as contract,
        ):
            with self.assertRaisesRegex(ValueError, "--azd-directory"):
                smoke(
                    root,
                    settings(),
                    RuntimeProfile(protocol="invocations"),
                    label="missing-directory",
                    local=True,
                    model_key="alpha",
                    case_id="D01",
                    confirmed=True,
                )
            invoked.assert_not_called()
            contract.assert_not_called()
            self.assertFalse((root / "outputs").exists())

    def test_local_smoke_uses_explicit_azd_directory_but_keeps_evidence_in_source_copy(self):
        with (
            workspace() as root,
            patch.dict(os.environ, {"WORKSHOP_HOSTED_AGENT_NAME": binding().name}),
        ):
            standalone = root / "standalone"
            standalone.mkdir()
            (standalone / "azure.yaml").write_text("name: explicit-unit-project\n")
            arguments = parser().parse_args(
                [
                    "benchmark",
                    "smoke",
                    "--local",
                    "--label",
                    "smoke",
                    "--azd-directory",
                    str(standalone),
                ]
            )
            self.assertEqual(arguments.azd_directory, standalone)
            with patch(
                "foundry_workshop.benchmark_cli.subprocess.run",
                return_value=SimpleNamespace(
                    returncode=1, stdout=b"retained failed response", stderr=b"unit-test failure"
                ),
            ) as invoked:
                with self.assertRaisesRegex(ValueError, "azd smoke failed"):
                    smoke(
                        root,
                        settings(),
                        RuntimeProfile(protocol="invocations"),
                        label="smoke",
                        local=True,
                        model_key="alpha",
                        case_id="D01",
                        confirmed=True,
                        azd_directory=standalone,
                    )
            command = invoked.call_args.args[0]
            self.assertEqual(command[:3], ["azd", "--cwd", str(standalone.resolve())])
            self.assertIn(binding().name, command)
            self.assertEqual(
                (root / "outputs/smoke/smoke/response.http").read_bytes(),
                b"retained failed response",
            )
            self.assertFalse((standalone / "outputs").exists())

    def test_smoke_rejects_bad_local_scope_and_remote_override_before_execution(self):
        with workspace() as root:
            standalone = root / "standalone"
            standalone.mkdir()
            missing = root / "missing"
            linked = root / "linked"
            linked.symlink_to(standalone, target_is_directory=True)
            for local, directory in (
                (True, missing),
                (True, standalone),
                (True, linked),
                (False, standalone),
            ):
                with (
                    self.subTest(local=local, directory=directory),
                    patch("foundry_workshop.benchmark_cli.subprocess.run") as invoked,
                    self.assertRaises(ValueError),
                ):
                    smoke(
                        root,
                        settings(),
                        RuntimeProfile(protocol="invocations"),
                        label="rejected-scope",
                        local=local,
                        model_key="alpha",
                        case_id="D01",
                        confirmed=True,
                        azd_directory=directory,
                    )
                invoked.assert_not_called()
            self.assertFalse((root / "outputs/smoke/rejected-scope").exists())

    def setUp(self):
        self.environment = patch.dict(
            os.environ, {"WORKSHOP_MODEL_DEPLOYMENTS_JSON": json.dumps(MODELS)}, clear=True
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def collect(self, root, label, *, prompt="v2", split="dev", candidate=None, **options):
        profile = RuntimeProfile(prompt=prompt, protocol="invocations")
        holder = []
        failure = options.pop("fail", None)

        def transport(_settings, _binding):
            instance = UnitTransport(root, profile, split, failure)
            holder.append(instance)
            return instance

        result = collect_matrix(
            root,
            settings(),
            profile,
            binding("1" if prompt == "v1" else "2"),
            label=label,
            split=split,
            candidate=candidate,
            unlock_holdout=split == "holdout",
            confirmed=True,
            transport_factory=transport,
            **options,
        )
        return result, holder

    def test_four_model_matrix_has_exactly_twenty_four_query_only_requests(self):
        with workspace() as root:
            result, transports = self.collect(root, "dev", concurrency=4)
            self.assertEqual(result["actual_rows"], 24)
            self.assertEqual(result["errors"], 0)
            self.assertTrue(result["business_gate_passed"])
            self.assertEqual(len(transports), 1)
            for request in transports[0].requests:
                self.assertEqual(set(request), {"question", "case_id", "model_key", "run_id"})
            for model in MODELS:
                self.assertEqual(result["models"][model]["passed"], 6)
                self.assertEqual(result["models"][model]["input_tokens"], 60)

    def test_failed_request_remains_in_matrix_and_cannot_improve_score_or_usage(self):
        with workspace() as root:
            result, _ = self.collect(root, "failed", fail=("alpha", "D01"))
            self.assertEqual((result["actual_rows"], result["errors"]), (24, 1))
            self.assertEqual(result["models"]["alpha"]["passed"], 5)
            self.assertEqual(result["models"]["alpha"]["total"], 6)
            self.assertIsNone(result["models"]["alpha"]["input_tokens"])
            self.assertFalse(result["business_gate_passed"])
            self.assertEqual(
                read_json(directory(root, "failed") / "http/alpha-D01.json")["status_code"], 503
            )

    def test_matrix_is_immutable_and_missing_rows_never_pass(self):
        with workspace() as root:
            self.collect(root, "dev")
            with self.assertRaises(FileExistsError):
                self.collect(root, "dev")
            manifest, rows, cases = load_matrix(root, "dev")
            for bad in (rows[:-1], rows + [rows[0]]):
                with self.subTest(rows=len(bad)), self.assertRaises(ValueError):
                    summarize_matrix(bad, cases, manifest["model_keys"])
            path = directory(root, "dev") / "responses.jsonl"
            path.write_text(path.read_text().replace("150000", "990000"))
            with self.assertRaises(ValueError):
                load_matrix(root, "dev")

    def test_holdout_is_not_opened_without_an_eligible_frozen_candidate(self):
        with workspace() as root:
            with (
                patch("foundry_workshop.benchmark.load_cases") as loader,
                self.assertRaises(ValueError),
            ):
                collect_matrix(
                    root,
                    settings(),
                    RuntimeProfile(protocol="invocations"),
                    binding(),
                    label="holdout",
                    split="holdout",
                    confirmed=True,
                    unlock_holdout=False,
                )
            loader.assert_not_called()
            self.collect(root, "candidate", fail=("alpha", "D01"))
            with self.assertRaises(ValueError):
                self.collect(root, "bad-holdout", split="holdout", candidate="candidate")
            self.assertFalse(directory(root, "bad-holdout").exists())

    def test_final_acceptance_does_not_rank_holdout_or_approve_deployment(self):
        with workspace() as root:
            self.collect(root, "baseline", prompt="v1")
            self.collect(root, "candidate")
            self.collect(root, "holdout", split="holdout", candidate="candidate")
            final, rows, _ = load_matrix(root, "holdout")
            self.assertEqual(len(rows), 16)
            self.assertEqual(final["frozen_candidate"]["label"], "candidate")
            result = verify_release(
                root, "baseline", "candidate", "holdout", require_native=False, require_traces=False
            )
            self.assertTrue(result["gate_passed"])
            self.assertFalse(result["deployment_approved"])
            with self.assertRaises(ValueError):
                compare_matrices(root, "candidate", "holdout")
            with self.assertRaises(ValueError):
                approve_regression(
                    root,
                    "holdout",
                    rows[0]["row_id"],
                    "invalid",
                    "reviewer",
                    "Do not harvest holdout.",
                )

    def test_reviewed_regression_is_consumed_and_ground_truth_cannot_be_changed(self):
        with workspace() as root:
            self.collect(root, "baseline", prompt="v1")
            record = approve_regression(
                root,
                "baseline",
                "alpha-D06",
                "reviewed",
                "team-01",
                "Inspect the original approval boundary and preserve the existing reference.",
            )
            self.collect(root, "candidate", regressions="reviewed")
            _, rows, _ = load_matrix(root, "candidate")
            affected = [row for row in rows if row["case_id"] == "D06"]
            self.assertEqual(len(affected), 4)
            self.assertTrue(
                all(row["regression_source"]["lineage"]["source_trace_id"] for row in affected)
            )
            data = read_json(record)
            data["case"]["expected_limit_krw"] = 999999
            write_json(record, data)
            with self.assertRaises(ValueError):
                self.collect(root, "changed", regressions="reviewed")

    def test_missing_cost_confirmation_prevents_session_creation(self):
        with workspace() as root, self.assertRaises(ValueError):
            collect_matrix(
                root,
                settings(),
                RuntimeProfile(protocol="invocations"),
                binding(),
                label="no-cost",
                split="dev",
                confirmed=False,
                transport_factory=lambda *_: self.fail("No session should be opened."),
            )

    def test_report_escapes_model_text_and_distinguishes_missing_measurements(self):
        with workspace() as root:
            profile = RuntimeProfile(protocol="invocations")
            collect_matrix(
                root,
                settings(),
                profile,
                binding(),
                label="html",
                split="dev",
                confirmed=True,
                transport_factory=lambda *_: UnitTransport(
                    root, profile, "dev", text="<script>alert(1)</script>"
                ),
            )
            page = report_matrix(root, "html").read_text()
            self.assertNotIn("<script>", page)
            self.assertIn("&lt;script&gt;", page)
            self.assertIn("None", page)

    def test_stricter_business_rubric_checks_narrative_amount_and_irrelevant_citations(self):
        with workspace() as root:
            self.collect(root, "dev")
            _, rows, cases = load_matrix(root, "dev")
            row = next(row for row in rows if row["case_id"] == "D01")
            case = next(case for case in cases if case["case_id"] == "D01")
            row["answer"] = {**row["answer"], "answer": "1박 12만원"}
            self.assertFalse(grade_strict(row, case)["checks"]["answer_contains_limit"])
            row["answer"] = {
                **row["answer"],
                "answer": "1박 15만 원",
                "citations": ["TRAVEL-2026", "MEAL-01"],
            }
            result = grade_strict(row, case)
            self.assertTrue(result["checks"]["answer_contains_limit"])
            self.assertFalse(result["checks"]["citations_relevant"])

    def test_small_sample_intervals_do_not_claim_perfect_certainty(self):
        lower, upper = wilson_interval(6, 6)
        self.assertLess(lower, 0.7)
        self.assertAlmostEqual(upper, 1)
        with self.assertRaises(ValueError):
            wilson_interval(0, 0)

    def test_trace_plan_scopes_exact_ids_agent_and_time_and_rejects_missing_results(self):
        with workspace() as root:
            self.collect(root, "dev")
            manifest, rows, _ = load_matrix(root, "dev")
            query = trace_query(manifest, rows)
            self.assertIn("requests", query)
            self.assertIn("operation_Id in (expected)", query)
            self.assertIn("timestamp between", query)
            self.assertIn(manifest["binding"]["name"], query)
            expected = [row["trace_id"] for row in rows]
            valid = [
                {
                    "trace_id": value,
                    "matching_requests": 1,
                    "request_errors": 0,
                    "duration_ms": 12.0,
                }
                for value in expected
            ]
            self.assertEqual(len(validate_trace_rows(valid, expected)), 24)
            for wrong in ([], valid[:-1], valid + [valid[0]]):
                with self.assertRaises(ValueError):
                    validate_trace_rows(wrong, expected)

    def test_model_allowlist_and_hosted_endpoint_never_choose_fallbacks(self):
        self.assertEqual(model_deployments(settings()), MODELS)
        with (
            patch.dict(os.environ, {"WORKSHOP_MODEL_DEPLOYMENTS_JSON": "{}"}),
            self.assertRaises(ValueError),
        ):
            model_deployments(settings())
        with self.assertRaises(ValueError):
            HostedBinding(binding().name, "latest", binding().endpoint).validate(settings())
        with self.assertRaises(ValueError):
            HostedBinding(
                binding().name, "1", binding().endpoint.replace("unit.services", "other.services")
            ).validate(settings())
        with self.assertRaises(ValueError):
            validate_request(
                {"question": "q", "model_key": "unknown", "case_id": "D01", "run_id": "run"}, MODELS
            )

    def test_azd_raw_http_checks_utf8_byte_lengths_duplicates_and_known_notice(self):
        data = json.dumps({"answer": "한국어"}, ensure_ascii=False).encode()
        header = f"HTTP/1.1 200 OK\r\nContent-Length: {len(data)}\r\n\r\n".encode()
        notice = b"\nUpdate available: 1 -> 2 (https://github.com/Azure/azure-dev)\nTo update, run `example`\n"
        parsed, suffix = parse_azd_http(header + data + notice)
        self.assertEqual(parsed, {"answer": "한국어"})
        self.assertIn("Update available", suffix)
        self.assertEqual(parse_azd_http(b"HTTP/1.1 200 OK\n\n" + data)[0], parsed)
        for raw in (
            header + data[:-1],
            header + data + b"\nunknown failure",
            b"HTTP/1.1 500 Error\n\n{}",
            b'HTTP/1.1 200 OK\n\n{"a":1,"a":2}',
        ):
            with self.assertRaises(ValueError):
                parse_azd_http(raw)

    def test_calibration_counts_false_positives_and_never_scores_empty_or_missing_rows(self):
        cases = [
            {"case_id": "C1", "expected_grounded": True},
            {"case_id": "C2", "expected_grounded": False},
        ]
        results = [
            {"case_id": key, "results": [{"name": "groundedness", "passed": True, "score": 5}]}
            for key in ("C1", "C2")
        ]
        result = calibration_summary(cases, results)
        self.assertEqual(result["correct"], 1)
        self.assertEqual(result["confusion"]["false_positive"], 1)
        self.assertFalse(result["gate_passed"])
        for bad_cases, bad_results in (([], []), (cases, results[:1])):
            with self.assertRaises(ValueError):
                calibration_summary(bad_cases, bad_results)
