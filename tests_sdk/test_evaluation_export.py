import importlib.util
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from tests import ROOT, workspace

spec = importlib.util.spec_from_file_location(
    "evaluation_export", ROOT / "scripts/export_evaluation.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def model(value):
    return SimpleNamespace(model_dump=lambda **_: value)


def client_with_rows(rows):
    client = MagicMock()
    client.evals.retrieve.return_value = model({"id": "eval_unit"})
    client.evals.runs.retrieve.return_value = model(
        {"id": "evalrun_unit", "eval_id": "eval_unit", "status": "completed"}
    )
    client.evals.runs.output_items.list.return_value = iter(model(row) for row in rows)
    return client


class EvaluationExportTests(unittest.TestCase):
    def rows(self):
        return [
            {
                "datasource_item_id": index,
                "results": [
                    {
                        "name": "groundedness",
                        "score": score,
                        "passed": score == 5,
                        "sample": {
                            "input": [{"role": "user", "content": '{"context":"original"}'}]
                        },
                    }
                ],
            }
            for index, score in enumerate((5, 1))
        ]

    def test_exports_all_rows_and_failed_scores_without_inference_or_approval(self):
        with workspace() as root:
            client = client_with_rows(self.rows())
            result = module.export_evaluation(
                client,
                root / "export",
                "eval_unit",
                "evalrun_unit",
                2,
                require_judge_inputs=True,
            )
            self.assertEqual(result["actual_rows"], 2)
            self.assertTrue(result["judge_inputs_available"])
            self.assertFalse(result["new_model_requests"])
            self.assertFalse(result["quality_approved"])
            self.assertIn('"score": 1', (root / "export/output-items.json").read_text())
            client.responses.create.assert_not_called()
            client.evals.runs.create.assert_not_called()
            with self.assertRaises(FileExistsError):
                module.export_evaluation(client, root / "export", "eval_unit", "evalrun_unit", 2)

    def test_continuous_run_ids_preserve_the_same_read_only_contract(self):
        run_id = "continuousevalrun_d4deb032-1606-49a7-9e88-d3e1302116ba"
        with workspace() as root:
            client = client_with_rows(self.rows())
            client.evals.runs.retrieve.return_value = model(
                {"id": run_id, "eval_id": "eval_unit", "status": "completed"}
            )
            result = module.export_evaluation(client, root / "export", "eval_unit", run_id, 2)
            self.assertEqual(result["run_id"], run_id)
            self.assertEqual(result["actual_rows"], 2)
            client.responses.create.assert_not_called()
            client.evals.runs.create.assert_not_called()

    def test_incomplete_duplicate_and_missing_judge_inputs_do_not_pass(self):
        scenarios = [
            ([self.rows()[0]], "Missing"),
            ([self.rows()[0], self.rows()[0]], "duplicate"),
            ([{"datasource_item_id": 0, "results": []}, self.rows()[1]], "judge inputs"),
        ]
        for rows, message in scenarios:
            with self.subTest(message=message), workspace() as root:
                with self.assertRaisesRegex(ValueError, message):
                    module.export_evaluation(
                        client_with_rows(rows),
                        root / "export",
                        "eval_unit",
                        "evalrun_unit",
                        2,
                        require_judge_inputs=True,
                    )
                self.assertTrue((root / "export/output-items.json").exists())

    def test_pending_and_wrong_scope_are_preserved_without_listing_items(self):
        for run, message in (
            (
                {"id": "evalrun_unit", "eval_id": "eval_unit", "status": "in_progress"},
                "not completed",
            ),
            ({"id": "evalrun_other", "eval_id": "eval_unit", "status": "completed"}, "IDs"),
        ):
            with self.subTest(message=message), workspace() as root:
                client = client_with_rows(self.rows())
                client.evals.runs.retrieve.return_value = model(run)
                with self.assertRaisesRegex(ValueError, message):
                    module.export_evaluation(
                        client, root / "export", "eval_unit", "evalrun_unit", 2
                    )
                client.evals.runs.output_items.list.assert_not_called()
                self.assertTrue((root / "export/run.json").exists())
