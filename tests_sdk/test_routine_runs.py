import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from foundry_workshop.contracts import read_json
from tests import ROOT

spec = importlib.util.spec_from_file_location("routine_runs", ROOT / "scripts/routine_runs.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RoutineHistoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory())) / "history"
        self.project = MagicMock()
        self.project.beta.routines.get.return_value.as_dict.return_value = {
            "name": "lab-unit-timer", "enabled": False,
        }
        self.rows = [
            {
                "id": "run-finished", "dispatch_id": "dispatch_finished",
                "status": "Finished", "phase": "cancelled", "attempt_source": "timer_delivery",
                "response_id": "resp_original",
            },
            {
                "id": "run-killed", "dispatch_id": "dispatch_killed",
                "status": "Killed", "phase": "cancelled", "attempt_source": "timer_delivery",
            },
        ]

    def export(self, name="lab-unit-timer"):
        self.project.beta.routines.list_runs.return_value = [
            SimpleNamespace(as_dict=lambda value=row: copy.deepcopy(value)) for row in self.rows
        ]
        return module.export_runs(self.project, self.directory, name, "lab-unit")

    def test_all_attempts_are_preserved_without_claiming_answer_verification(self):
        result = self.export()
        self.assertEqual(result["runs"], self.rows)
        self.assertEqual(read_json(self.directory / "runs.json"), self.rows)
        self.assertEqual(result["returned_runs"], 2)
        self.assertFalse(result["agent_answer_verified"])
        self.assertFalse(result["routine_changed"])
        self.assertFalse(result["new_model_request"])
        self.project.beta.routines.list_runs.assert_called_once_with("lab-unit-timer", limit=100)
        self.assertEqual(
            [call[0] for call in self.project.mock_calls],
            ["beta.routines.get", "beta.routines.get().as_dict", "beta.routines.list_runs"],
        )

    def test_empty_history_is_explicit_and_not_successful_delivery(self):
        self.rows = []
        result = self.export()
        self.assertEqual(result["returned_runs"], 0)
        self.assertFalse(result["agent_answer_verified"])

    def test_unowned_names_and_existing_exports_do_not_read_the_service(self):
        for name in ("lab-other-timer", "../lab-unit-timer", "lab-unit/../other"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.export(name)
        self.project.beta.routines.get.assert_not_called()
        self.export()
        self.project.reset_mock()
        with self.assertRaises(FileExistsError):
            self.export()
        self.project.beta.routines.get.assert_not_called()

    def test_wrong_routine_duplicate_and_malformed_history_are_not_normalized(self):
        self.project.beta.routines.get.return_value.as_dict.return_value["name"] = "lab-other-timer"
        with self.assertRaisesRegex(ValueError, "requested name"):
            self.export()
        self.assertFalse((self.directory / "runs.json").exists())
        self.directory = self.directory.parent / "duplicate"
        self.project.beta.routines.get.return_value.as_dict.return_value["name"] = "lab-unit-timer"
        self.rows.append(copy.deepcopy(self.rows[0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.export()
        self.assertEqual(read_json(self.directory / "runs.json"), self.rows)
        self.directory = self.directory.parent / "malformed"
        self.rows[0]["dispatch_id"] = ""
        with self.assertRaisesRegex(ValueError, "Malformed"):
            self.export()
