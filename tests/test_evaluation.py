import csv
import json
from unittest.mock import patch

import evaluation
import workshop
from tests.helpers import IsolatedWorkshop, fixture_result


class EvaluationTests(IsolatedWorkshop):
    def collect(self, label="test-run"):
        with patch.object(evaluation, "ask", side_effect=fixture_result) as called:
            folder = evaluation.evaluate(
                self.settings, self.root / "data/evaluation/dev.jsonl", label
            )
        return folder, called

    def fill_review(self, folder, *, failing=None):
        path = folder / "review.csv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            row["pass"] = "fail" if row["id"] == failing else "pass"
            row["reason"] = "오프라인 테스트에서 입력한 사람 검토"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=evaluation.REVIEW_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    def test_six_responses_and_no_reference_answer_in_model_input(self):
        folder, called = self.collect()
        cases = evaluation.load_cases(self.root / "data/evaluation/dev.jsonl")
        self.assertEqual(called.call_count, 6)
        for call, case in zip(called.call_args_list, cases, strict=True):
            self.assertEqual(call.args[1], case["query"])
            self.assertNotIn(case["expected"], call.args[1])
            self.assertEqual(call.kwargs["expected_version"], "7")
        exported = [
            json.loads(line)
            for line in (folder / "foundry-evaluation.jsonl").read_text().splitlines()
        ]
        self.assertEqual(len(exported), 6)
        self.assertEqual(set(exported[0]), {"query", "response", "ground_truth"})
        self.assertNotIn("context", exported[0])
        self.assertEqual(exported[0]["response"], "오프라인 테스트 전용")

    def test_unreviewed_rows_are_not_a_passing_score(self):
        self.collect()
        with self.assertRaisesRegex(workshop.WorkshopError, "검토 이유"):
            evaluation.score("test-run")

    def test_score_is_human_and_not_production_approval(self):
        folder, _ = self.collect()
        self.fill_review(folder)
        result = evaluation.score("test-run")
        self.assertEqual(result["passed"], 6)
        self.assertEqual(result["total"], 6)
        self.assertEqual(result["quality_gate"], "PASS")
        self.assertFalse(result["production_approved"])
        self.assertEqual(result["scoring"], "human_review_with_evidence_checks")

    def test_critical_failure_stays_in_denominator(self):
        folder, _ = self.collect()
        self.fill_review(folder, failing="D06")
        result = evaluation.score("test-run")
        self.assertEqual(result["passed"], 5)
        self.assertEqual(result["total"], 6)
        self.assertEqual(result["critical_failures"], 1)
        self.assertEqual(result["quality_gate"], "NOT_READY")

    def test_failed_collection_does_not_export_success_dataset(self):
        calls = 0

        def fail_second(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise workshop.WorkshopError("synthetic HTTP failure")
            return fixture_result(*args, **kwargs)

        with patch.object(evaluation, "ask", side_effect=fail_second):
            with self.assertRaises(workshop.WorkshopError):
                evaluation.evaluate(
                    self.settings, self.root / "data/evaluation/dev.jsonl", "failed"
                )
        folder = self.root / "outputs/failed"
        manifest = json.loads((folder / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "error")
        self.assertEqual(manifest["completed_responses"], 1)
        self.assertFalse((folder / "foundry-evaluation.jsonl").exists())
        with self.assertRaisesRegex(workshop.WorkshopError, "누락"):
            evaluation.score("failed")

    def test_changed_snapshot_or_version_is_rejected(self):
        folder, _ = self.collect()
        self.fill_review(folder)
        path = folder / "response-01.json"
        result = json.loads(path.read_text())
        result["agent_version"] = "8"
        workshop.write_json(path, result)
        with self.assertRaisesRegex(workshop.WorkshopError, "설정이 다른"):
            evaluation.score("test-run")
        result["agent_version"] = "7"
        workshop.write_json(path, result)
        with (folder / "cases.json").open("a") as handle:
            handle.write(" ")
        with self.assertRaisesRegex(workshop.WorkshopError, "스냅샷"):
            evaluation.score("test-run")

    def test_required_tool_and_citation_cannot_be_marked_pass(self):
        for field, index, message in (
            ("tool_calls", 3, "도구 성공"),
            ("citations", 1, "파일 인용"),
        ):
            with self.subTest(field=field):
                label = field.replace("_", "-")
                folder, _ = self.collect(label)
                self.fill_review(folder)
                path = folder / f"response-{index:02d}.json"
                result = json.loads(path.read_text())
                result[field] = []
                workshop.write_json(path, result)
                with self.assertRaisesRegex(workshop.WorkshopError, message):
                    evaluation.score(label)

    def test_new_labels_and_valid_dataset_required(self):
        self.collect()
        with self.assertRaisesRegex(workshop.WorkshopError, "덮어쓰지"):
            self.collect()
        for label in ("../escape", "", "UPPER", "x" * 41):
            with self.subTest(label=label), self.assertRaises(workshop.WorkshopError):
                evaluation.run_directory(label)
        cases = self.root / "duplicate.jsonl"
        first = (self.root / "data/evaluation/dev.jsonl").read_text().splitlines()[0]
        cases.write_text(first + "\n" + first + "\n")
        with self.assertRaisesRegex(workshop.WorkshopError, "중복"):
            evaluation.load_cases(cases)

    def test_csv_formula_prefix_is_not_executable(self):
        self.assertEqual(evaluation.csv_text("=1+1"), "'=1+1")
        self.assertEqual(evaluation.csv_text("@sum(A1)"), "'@sum(A1)")
        self.assertEqual(evaluation.csv_text("일반 문장"), "일반 문장")
