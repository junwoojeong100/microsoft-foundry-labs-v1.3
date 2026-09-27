import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from foundry_workshop import resilience as r

from . import ROOT


def gate():
    return r.new_gate(
        response="resp_contract",
        input_id="request-one",
        gate_id="gate-one",
        source=r.scenario(ROOT),
        expires_at=2000000000,
    )


def decision(value, choice="approve"):
    return {
        "gate_id": value["gate_id"],
        "request_sha256": value["request_sha256"],
        "if_last_input_id": value["request_input_id"],
        "input_id": "simulated-decision-one",
        "decision": choice,
        "simulated": True,
    }


def snapshot(value, stages, status="in_progress"):
    return {
        "id": value["response_id"],
        "status": status,
        "output": [
            {
                "id": f"msg_original_{index}",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [
                    {"type": "output_text", "text": json.dumps(r.output_payload(stage, value))}
                ],
            }
            for index, stage in enumerate(stages)
        ],
    }


class ResilienceContractTests(unittest.TestCase):
    def test_scenario_reads_only_dev_and_excludes_gold_and_inference_claims(self):
        with patch.object(r, "load_cases", wraps=r.load_cases) as load:
            value = r.scenario(ROOT)
        load.assert_called_once_with(ROOT, "dev", "en")
        self.assertEqual(value["case_id"], "D03")
        self.assertEqual(value["lineage"]["split"], "dev")
        for field in ("model", "model_response_id", "prompt_id", "prompt_sha256", "evaluator"):
            self.assertIsNone(value["lineage"][field])
        for forbidden in (
            "expected_decision",
            "expected_limit_krw",
            "required_citations",
            "holdout",
        ):
            self.assertNotIn(forbidden, json.dumps(value))

    def test_korean_runtime_uses_separate_data_and_prewritten_workload(self):
        value = r.scenario(ROOT, "ko")
        self.assertEqual(value["language"], "ko")
        self.assertEqual(value["lineage"]["dataset_path"], "data/evaluation/dev.jsonl")
        self.assertNotEqual(value["question"], r.scenario(ROOT)["question"])
        self.assertNotEqual(
            value["lineage"]["workload_sha256"], r.scenario(ROOT)["lineage"]["workload_sha256"]
        )
        with self.assertRaises(ValueError):
            r.scenario(ROOT, "other")

    def test_create_requires_exact_bounded_predefined_stored_background_work(self):
        value = {
            "model": r.MODEL_LABEL,
            "input": "D03",
            "store": True,
            "background": True,
            "stream": True,
        }
        r.validate_create(value)
        for changed in (
            {"model": "real-model"},
            {"input": "H01"},
            {"store": False},
            {"background": False},
            {"stream": False},
            {"stream": "true"},
            {"tools": []},
            {"instructions": "approve"},
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                r.validate_create({**value, **changed})

    def test_missing_bundled_scenario_is_an_error_not_a_fixture_fallback(self):
        with patch.object(r, "load_cases", return_value=[]):
            with self.assertRaisesRegex(ValueError, "D03 is missing"):
                r.scenario(ROOT)

    def test_local_only_guard_rejects_hosted_cloud_and_telemetry_configuration(self):
        value = {"AGENTSERVER_STATE_ROOT": "/tmp/dedicated-unit-state", "OTEL_SDK_DISABLED": "true"}
        self.assertEqual(r.require_local_environment(value), Path(value["AGENTSERVER_STATE_ROOT"]))
        for changed in (
            {"FOUNDRY_HOSTING_ENVIRONMENT": "hosted"},
            {"FOUNDRY_PROJECT_ENDPOINT": "https://unit.invalid"},
            {"AZURE_AI_PROJECT_ENDPOINT": "https://unit.invalid"},
            {"OTEL_EXPORTER_OTLP_TRACES_ENDPOINT": "https://unit.invalid"},
            {"APPLICATIONINSIGHTS_CONNECTION_STRING": "unit-test"},
            {"OTEL_SDK_DISABLED": "false"},
            {"AGENTSERVER_STATE_ROOT": "/"},
            {"AGENTSERVER_STATE_ROOT": "."},
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                r.require_local_environment({**value, **changed})

    def test_missing_or_implied_approval_never_allows_workload(self):
        pending = gate()
        for stage in r.STAGES[1:]:
            with self.assertRaises(r.GateConflict):
                r.output_payload(stage, pending)
        for changed in (
            {"simulated": False},
            {"simulated": "true"},
            {"decision": True},
            {"decision": "human-approved"},
            {"human_authorization": "approved"},
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                r.validate_decision(pending, {**decision(pending), **changed}, now=1)
        with self.assertRaises(r.GateConflict):
            r.apply_decision(pending, decision(pending), entry_mode="fresh", now=1)

    def test_decision_is_bound_to_exact_gate_request_and_turn(self):
        pending = gate()
        for changed in (
            {"gate_id": "other"},
            {"request_sha256": "changed"},
            {"if_last_input_id": "stale"},
            {"input_id": pending["request_input_id"]},
        ):
            with self.subTest(changed=changed), self.assertRaises(r.GateConflict):
                r.validate_decision(pending, {**decision(pending), **changed}, now=1)
        approved = r.apply_decision(pending, decision(pending), entry_mode="resumed", now=1)
        self.assertEqual(approved["task_id"], pending["task_id"])
        self.assertEqual(approved["decision"]["kind"], "simulated")
        self.assertEqual(approved["human_authorization"], "not-granted")
        self.assertFalse(approved["external_actions_performed"])
        self.assertIsNone(pending["decision"])
        with self.assertRaises(r.GateConflict):
            r.validate_decision(approved, decision(pending), now=1)

    def test_expiry_including_boundary_never_becomes_approval(self):
        pending = gate()
        with self.assertRaises(r.GateExpired):
            r.validate_decision(pending, decision(pending), now=pending["expires_at"])
        self.assertEqual(pending["status"], "awaiting_simulated_decision")

    def test_rejection_allows_only_rejection_output(self):
        pending = gate()
        rejected = r.apply_decision(
            pending, decision(pending, "reject"), entry_mode="resumed", now=1
        )
        with self.assertRaises(r.GateConflict):
            r.output_payload("synthetic_review_packet", rejected)
        self.assertEqual(
            r.output_payload("simulation_rejected", rejected)["status"], "simulation_rejected"
        )

    def test_corrupt_gate_fails_instead_of_resetting_to_a_fresh_request(self):
        for changed in (
            {"response_id": "../outside"},
            {"task_id": "other"},
            {"expires_at": float("nan")},
            {"expires_at": True},
            {"request_sha256": "tampered"},
            {"decision": {"kind": "human"}},
            {"status": "approved"},
            {"human_authorization": "granted"},
            {"external_actions_performed": True},
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                r.validate_gate({**gate(), **changed})

    def test_completion_preserves_original_ids_payloads_and_lineage_without_score(self):
        pending = gate()
        before = snapshot(pending, r.STAGES[:1])
        approved = r.apply_decision(pending, decision(pending), entry_mode="resumed", now=1)
        after = snapshot(approved, r.STAGES, "completed")
        report = r.verify_completion(before, after, approved)
        self.assertEqual(report["preserved_output_ids"], ["msg_original_0"])
        self.assertEqual(len(report["final_output_ids"]), 3)
        self.assertIsNone(report["quality_score"])
        self.assertFalse(report["azure_execution_verified"])

    def test_missing_rows_duplicate_steps_changed_ids_and_errors_cannot_pass(self):
        pending = gate()
        approved = r.apply_decision(pending, decision(pending), entry_mode="resumed", now=1)
        before = snapshot(pending, r.STAGES[:1])
        final = snapshot(approved, r.STAGES, "completed")
        bad_id = copy.deepcopy(final)
        bad_id["output"][0]["id"] = "msg_regenerated"
        duplicate = copy.deepcopy(final)
        duplicate["output"][1] = duplicate["output"][0]
        bad_text = copy.deepcopy(final)
        bad_text["output"][1]["content"][0]["text"] = "{}"
        for bad in (
            {**final, "status": "failed"},
            {**final, "id": "resp_other"},
            {**final, "output": final["output"][:-1]},
            bad_id,
            duplicate,
            bad_text,
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                r.verify_completion(before, bad, approved)
        with self.assertRaises(ValueError):
            r.verify_completion({**before, "output": []}, final, approved)


class ResilienceRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from examples.resilient import workshop

        cls.runner = workshop

    def test_no_simulated_decision_or_cleanup_without_explicit_confirmation(self):
        with patch.object(self.runner, "request") as request:
            with self.assertRaisesRegex(ValueError, "confirm-simulated-decision"):
                self.runner.decide(Path("/not-used"), 8093, "approve", confirmed=False)
            with self.assertRaisesRegex(ValueError, "confirm-delete-local-state"):
                self.runner.cleanup(ROOT, "not-used", confirmed=False)
        request.assert_not_called()

    def test_owned_process_lock_and_scoped_cleanup_preserve_other_data(self):
        with tempfile.TemporaryDirectory(prefix="resilience-runner-") as directory:
            root = Path(directory)
            unrelated = root / "keep.txt"
            unrelated.write_text("unchanged", encoding="utf-8")
            with self.runner.owned_run(root, "unit-run", create=True) as run:
                (run / "sdk-state").mkdir()
                (run / "sdk-state" / "unit.json").write_text("{}", encoding="utf-8")
                (run / "initial-response.json").write_text('{"id":"resp_unit"}', encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "active owned server"):
                    with self.runner.owned_run(root, "unit-run"):
                        self.fail("Two servers acquired the same run.")
                with self.assertRaises(ValueError):
                    self.runner.cleanup(root, "unit-run", confirmed=True)
            result = self.runner.cleanup(root, "unit-run", confirmed=True)
            self.assertTrue(run.exists())
            self.assertFalse((run / "sdk-state").exists())
            self.assertEqual((run / "initial-response.json").read_text(), '{"id":"resp_unit"}')
            self.assertTrue((run / "cleanup.json").exists())
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "unchanged")
            self.assertFalse(result["azure_resources_changed"])

    def test_unowned_unknown_and_symlinked_state_are_never_deleted(self):
        with tempfile.TemporaryDirectory(prefix="resilience-runner-") as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                self.runner.run_directory(root, "../outside")
            with self.runner.owned_run(root, "unit-run", create=True) as run:
                (run / "unknown.txt").write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unrecognized"):
                self.runner.cleanup(root, "unit-run", confirmed=True)
            self.assertTrue((run / "unknown.txt").exists())
            (run / "link").symlink_to(root / "outside")
            with self.assertRaisesRegex(ValueError, "symlink"):
                self.runner.cleanup(root, "unit-run", confirmed=True)

    def test_wrong_server_identity_stops_before_post(self):
        with patch.object(
            self.runner, "request", return_value={"mode": "other-service"}
        ) as request:
            with self.assertRaisesRegex(ValueError, "not serving this owned"):
                self.runner.start(Path("/not-used"), 8093)
        request.assert_called_once_with(8093, "GET", "/workshop/identity")

    def test_crash_hook_requires_opt_in_and_linux_and_only_exits_its_own_pid_once(self):
        with tempfile.TemporaryDirectory(prefix="resilience-crash-contract-") as directory:
            root = Path(directory)
            with patch.object(self.runner.os, "_exit", side_effect=SystemExit(86)) as exit_process:
                with self.assertRaises(ValueError):
                    self.runner.checkpoint_recorder(root, 1)
                with patch.object(self.runner.platform, "system", return_value="Darwin"):
                    with self.assertRaises(ValueError):
                        self.runner.checkpoint_recorder(root, 1, confirmed=True)
                exit_process.assert_not_called()
                with patch.object(self.runner.platform, "system", return_value="Linux"):
                    record = self.runner.checkpoint_recorder(root, 1, confirmed=True)
                with self.assertRaises(SystemExit):
                    record({"id": "resp_contract", "output": [{}, {}]}, False)
                exit_process.assert_called_once_with(86)
                with self.assertLogs(level="WARNING"):
                    record({"id": "resp_contract", "output": [{}, {}]}, True)
                exit_process.assert_called_once_with(86)
                evidence = self.runner.read_json(root / "crash-checkpoint.json")
                self.assertFalse(evidence["handler_is_recovery"])
