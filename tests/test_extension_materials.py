import csv
import io
import json
import unittest
from unittest.mock import patch

from foundry_workshop.contracts import load_cases, load_documents
from foundry_workshop.extension_materials import files_for, prepare

from . import ROOT, workspace


class ExtensionMaterialTests(unittest.TestCase):
    def test_only_canonical_dev_is_loaded_and_every_case_is_used_once(self):
        for language in ("en", "ko"):
            with patch(
                "foundry_workshop.extension_materials.load_cases", wraps=load_cases
            ) as loader:
                files = files_for(ROOT, language, "lab-unit")
            loader.assert_called_once_with(ROOT, "dev", language)
            plan = json.loads(files["conversation-plan.json"])
            cases = load_cases(ROOT, "dev", language)
            turns = [
                turn for conversation in plan["conversations"] for turn in conversation["turns"]
            ]
            self.assertEqual(
                turns,
                [{"case_id": item["case_id"], "question": item["question"]} for item in cases],
            )
            self.assertFalse(plan["holdout_loaded"])
            self.assertNotIn("ground_truth", files["conversation-plan.json"].decode())

    def test_optimizer_references_preserve_the_original_answers(self):
        files = files_for(ROOT, "en", "lab-unit")
        records = [json.loads(line) for line in files["optimizer-dev.jsonl"].decode().splitlines()]
        cases = load_cases(ROOT, "dev", "en")
        for row, case in zip(records, cases, strict=True):
            self.assertEqual(row["query"], case["question"])
            expected = json.loads(row["ground_truth"])
            for key in ("expected_decision", "expected_limit_krw", "required_citations"):
                self.assertEqual(expected[key], case[key])
        self.assertNotIn("response", records[0])

    def test_policy_csv_contains_only_the_six_original_documents(self):
        for language in ("en", "ko"):
            files = files_for(ROOT, language, "lab-unit")
            records = list(
                csv.DictReader(io.StringIO(files["policy-records.csv"].decode("utf-8-sig")))
            )
            self.assertEqual(records, load_documents(ROOT, language))
            self.assertIn(
                f"name: lab-unit-policy-review-{language}",
                files["policy-review/SKILL.md"].decode(),
            )

    def test_prepare_is_explicit_local_and_never_overwrites(self):
        with workspace() as root:
            result = prepare(root, "en", "lab-unit", "extensions")
            self.assertFalse(result["azure_requests_sent"])
            self.assertTrue((root / "outputs/extensions/manifest.json").is_file())
            with self.assertRaises(FileExistsError):
                prepare(root, "en", "lab-unit", "extensions")
            with self.assertRaises(ValueError):
                prepare(root, "en", "../bad-prefix", "another")
