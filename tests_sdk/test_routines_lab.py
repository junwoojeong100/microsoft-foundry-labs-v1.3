import copy
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from foundry_workshop.routines_lab import inspect_run, telemetry_query, validate_telemetry_response
from tests import workspace
from tests.test_toolbox import ENVIRONMENT, settings


class RoutineResultTests(unittest.TestCase):
    def telemetry(self):
        return [{
            "AgentName": "lab-unit-agent",
            "TraceId": "a" * 32,
            "SpanId": "b" * 16,
            "Attributes": json.dumps({
                "gen_ai.response.id": "resp-unit",
                "gen_ai.operation.name": "invoke_agent",
                "gen_ai.agent.version": "1",
                "gen_ai.azure_ai_project.id": "/subscriptions/unit/projects/lab",
            }),
            "OutputMessages": json.dumps([{
                "role": "assistant", "parts": [{"type": "text", "content": "Actual saved answer"}],
                "finish_reason": "stop",
            }]),
        }]

    def test_telemetry_requires_exact_response_agent_project_and_one_span(self):
        rows = self.telemetry()
        result = validate_telemetry_response(
            rows, "lab-unit-agent", "resp-unit", "/subscriptions/unit/projects/lab"
        )
        self.assertEqual(result["answer"], "Actual saved answer")
        self.assertEqual(result["trace_id"], "a" * 32)
        for name, response, project in (
            ("lab-other-agent", "resp-unit", "/subscriptions/unit/projects/lab"),
            ("lab-unit-agent", "resp-other", "/subscriptions/unit/projects/lab"),
            ("lab-unit-agent", "resp-unit", "/subscriptions/other/projects/lab"),
        ):
            with self.subTest(name=name, response=response, project=project), self.assertRaises(ValueError):
                validate_telemetry_response(rows, name, response, project)
        for value in ([], rows + copy.deepcopy(rows)):
            with self.subTest(rows=len(value)), self.assertRaisesRegex(ValueError, "one exact"):
                validate_telemetry_response(
                    value, "lab-unit-agent", "resp-unit", "/subscriptions/unit/projects/lab"
                )

    def test_query_is_bounded_and_matches_the_original_response(self):
        query = telemetry_query("lab-unit-agent", "resp-unit", 1790546486)
        self.assertIn("TimeGenerated between", query)
        self.assertIn('== "resp-unit"', query)
        self.assertIn("'invoke_agent'", query)
        with self.assertRaises(ValueError):
            telemetry_query("lab-unit-agent", "resp-unit", None)

    def test_incomplete_telemetry_output_cannot_pass(self):
        rows = self.telemetry()
        output = json.loads(rows[0]["OutputMessages"])
        output[0]["finish_reason"] = "length"
        rows[0]["OutputMessages"] = json.dumps(output)
        with self.assertRaisesRegex(ValueError, "nonempty assistant"):
            validate_telemetry_response(
                rows, "lab-unit-agent", "resp-unit", "/subscriptions/unit/projects/lab"
            )

    def test_scheduled_delivery_is_not_relabelled_as_manual_or_reinvoked(self):
        with workspace() as root, patch.dict(os.environ, ENVIRONMENT, clear=True):
            project, client = MagicMock(), MagicMock()
            project.beta.routines.get.return_value.as_dict.return_value = {
                "enabled": False, "action": {"agent_name": "lab-unit-agent"},
            }
            project.beta.routines.list_runs.return_value = [SimpleNamespace(as_dict=lambda: {
                "id": "run-unit", "dispatch_id": "dispatch_unit", "attempt_source": "timer_delivery",
                "phase": "completed", "status": "Finished", "response_id": "resp-unit",
                "trigger_type": "timer", "scheduled_fire_at": 100, "triggered_at": 100,
            })]
            with patch("foundry_workshop.routines_lab.retrieve_telemetry", return_value={
                "answer": "Actual saved answer", "trace_id": "a" * 32,
            }):
                result = inspect_run(
                    project, client, root, settings(), "lab-unit-timer", "dispatch_unit",
                    "scheduled", verify_response=True, response_source="telemetry", scheduled=True,
                )
            self.assertTrue(result["scheduled_trigger_verified"])
            self.assertFalse(result["manual_delivery_verified"])
            self.assertTrue(result["agent_answer_verified"])
            self.assertEqual(result["response_retrieval"], "verified-telemetry")
            client.responses.with_raw_response.retrieve.assert_not_called()
            client.responses.create.assert_not_called()

    def test_finished_timer_cancelled_after_disable_requires_exact_telemetry(self):
        with workspace() as root, patch.dict(os.environ, ENVIRONMENT, clear=True):
            project, client = MagicMock(), MagicMock()
            project.beta.routines.get.return_value.as_dict.return_value = {
                "enabled": False, "action": {"agent_name": "lab-unit-agent"},
            }
            project.beta.routines.list_runs.return_value = [SimpleNamespace(as_dict=lambda: {
                "id": "run-unit", "dispatch_id": "dispatch_unit", "attempt_source": "timer_delivery",
                "phase": "cancelled", "status": "Finished", "response_id": "resp-unit",
                "trigger_type": "timer", "scheduled_fire_at": 100, "triggered_at": 100,
            })]
            with self.assertRaisesRegex(ValueError, "not completed"):
                inspect_run(
                    project, client, root, settings(), "lab-unit-timer", "dispatch_unit",
                    "unverified", scheduled=True,
                )
            with patch("foundry_workshop.routines_lab.retrieve_telemetry", return_value={
                "answer": "Actual saved answer", "trace_id": "a" * 32,
            }):
                result = inspect_run(
                    project, client, root, settings(), "lab-unit-timer", "dispatch_unit",
                    "verified", scheduled=True, verify_response=True, response_source="telemetry",
                )
            self.assertEqual(result["run_phase"], "cancelled")
            self.assertTrue(result["requires_exact_response_for_cancelled_phase"])
            self.assertTrue(result["agent_answer_verified"])

    def test_finished_dispatch_requires_its_actual_completed_response(self):
        with workspace() as root, patch.dict(os.environ, ENVIRONMENT, clear=True):
            project, client = MagicMock(), MagicMock()
            project.beta.routines.get.return_value.as_dict.return_value = {
                "enabled": False,
                "action": {"agent_name": "lab-unit-agent"},
            }
            project.beta.routines.list_runs.return_value = [
                SimpleNamespace(
                    as_dict=lambda: {
                        "id": "run-unit",
                        "dispatch_id": "dispatch_unit",
                        "attempt_source": "queued_dispatch",
                        "phase": "completed",
                        "status": "Finished",
                        "response_id": "resp-unit",
                    }
                ),
            ]
            raw = {"agent_reference": {"name": "lab-unit-agent", "version": "1"}}
            response = SimpleNamespace(
                id="resp-unit", status="completed", output_text="Synthetic answer"
            )
            client.responses.with_raw_response.retrieve.return_value = SimpleNamespace(
                http_response=SimpleNamespace(json=lambda: raw),
                parse=lambda: response,
            )
            result = inspect_run(
                project,
                client,
                root,
                settings(),
                "lab-unit-timer",
                "dispatch_unit",
                "unit",
                verify_response=True,
            )
            self.assertTrue(result["manual_delivery_verified"])
            self.assertTrue(result["agent_answer_verified"])
            self.assertFalse(result["scheduled_trigger_verified"])
            client.responses.create.assert_not_called()
            response.output_text = ""
            with self.assertRaises(ValueError):
                inspect_run(
                    project,
                    client,
                    root,
                    settings(),
                    "lab-unit-timer",
                    "dispatch_unit",
                    "empty",
                    verify_response=True,
                )
            delivery = inspect_run(
                project, client, root, settings(), "lab-unit-timer", "dispatch_unit", "delivery"
            )
            self.assertTrue(delivery["manual_delivery_verified"])
            self.assertFalse(delivery["agent_answer_verified"])
