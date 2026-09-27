import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from foundry_workshop.routines_lab import inspect_run
from tests import workspace
from tests.test_toolbox import ENVIRONMENT, settings


class RoutineResultTests(unittest.TestCase):
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
