import contextlib
import hashlib
import io
import json
import re
import unittest
from dataclasses import replace
from unittest.mock import patch

from foundry_workshop.benchmark import report_matrix
from foundry_workshop.cli import DEFAULT_QUESTION_EN, main
from foundry_workshop.contracts import (
    digest,
    load_cases,
    load_documents,
    load_prompt,
    read_json,
)
from foundry_workshop.evaluation import load_run
from foundry_workshop.experiments import offline_demo
from foundry_workshop.knowledge import local_retrieve
from foundry_workshop.profiles import RuntimeProfile, runtime_contract
from foundry_workshop.runtime import instruction_snapshot

from . import ROOT, workspace
from .test_benchmark import settings


class LanguageTests(unittest.TestCase):
    def test_html_report_uses_its_frozen_language_without_changing_scores(self):
        with workspace() as root:
            manifest = {"runtime_contract": {"profile": {"language": "en"}}, "model_keys": []}
            summary = {"models": {}, "unmodified_unit_test_value": 7}
            (root / "outputs/benchmarks/report-en").mkdir(parents=True)
            with (
                patch("foundry_workshop.benchmark.load_matrix", return_value=(manifest, [], [])),
                patch("foundry_workshop.benchmark.summarize_matrix", return_value=summary),
            ):
                path = report_matrix(root, "report-en")
            self.assertIn("lang='en'", path.read_text())
            self.assertIn("All rows and failures", path.read_text())
            self.assertIsNone(re.search("[가-힣]", path.read_text()))
            self.assertEqual(read_json(path.parent / "business-evaluation.json"), summary)

    def test_original_and_translated_assets_match_the_frozen_bundle(self):
        manifest = read_json(ROOT / "data/localization.json")
        self.assertTrue(manifest["holdout_prepared"])
        self.assertLess(
            manifest["development_frozen_at"], manifest["holdout_translation_frozen_at"]
        )
        for item in manifest["files"]:
            for path, expected in (
                ("source", "source_sha256"),
                ("translation", "translation_sha256"),
            ):
                self.assertEqual(
                    hashlib.sha256((ROOT / item[path]).read_bytes()).hexdigest(), item[expected]
                )
            self.assertIsNone(re.search("[가-힣]", (ROOT / item["translation"]).read_text()))
        for prompt in ("v1", "v2"):
            self.assertEqual(
                digest(
                    instruction_snapshot(
                        ROOT, RuntimeProfile(kind="workflow", prompt=prompt, language="en")
                    )
                ),
                manifest["english_workflow_instruction_hashes"][prompt],
            )

    def test_document_ids_dates_and_reference_judgments_are_preserved(self):
        for original, translated in zip(
            load_documents(ROOT), load_documents(ROOT, "en"), strict=True
        ):
            for field in ("id", "effective_from", "effective_to"):
                self.assertEqual(original[field], translated[field])
            self.assertNotEqual(original["content"], translated["content"])
            self.assertEqual(
                set(re.findall(r"\d{4,}", original["content"])),
                set(re.findall(r"\d{4,}", translated["content"])),
            )
        for split in ("dev", "holdout"):
            original, translated = load_cases(ROOT, split), load_cases(ROOT, split, "en")
            self.assertEqual(
                [
                    {key: value for key, value in row.items() if key != "question"}
                    for row in original
                ],
                [
                    {key: value for key, value in row.items() if key != "question"}
                    for row in translated
                ],
            )
            self.assertNotEqual(digest(original), digest(translated))

    def test_english_fixtures_keep_offline_and_failure_boundaries(self):
        with workspace() as root:
            baseline = offline_demo(root, "english-v1", "v1", language="en")
            candidate = offline_demo(root, "english-v2", "v2", language="en")
            self.assertEqual(baseline["passed"], 0)
            self.assertEqual(candidate["passed"], 6)
            manifest, rows, cases = load_run(root, "english-v2")
            self.assertEqual(manifest["language"], "en")
            self.assertEqual(cases[0]["question"], DEFAULT_QUESTION_EN)
            for row in rows:
                self.assertIsNone(row["response_id"])
                self.assertIsNone(row["usage"])
                self.assertIsNone(re.search("[가-힣]", row["answer"]["answer"]))

    def test_missing_english_asset_never_falls_back_to_korean(self):
        with workspace() as root:
            (root / "prompts/en/v1.txt").unlink()
            with self.assertRaises(FileNotFoundError):
                load_prompt(root, "v1", "en")
            self.assertTrue(load_prompt(root, "v1", "ko")[0])
        with self.assertRaises(ValueError):
            load_documents(ROOT, "unknown")

    def test_cli_default_and_local_retrieval_are_really_english(self):
        with patch("foundry_workshop.cli.cloud_command", return_value={}) as called:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(ROOT, ["--language", "en", "model"]), 0)
        self.assertEqual(called.call_args.args[1].question, DEFAULT_QUESTION_EN)
        result = local_retrieve(ROOT, DEFAULT_QUESTION_EN, language="en")
        self.assertIn("TRAVEL-2026", result["source_ids"])
        self.assertIsNone(re.search("[가-힣]", json.dumps(result, ensure_ascii=False)))

    def test_profile_language_is_explicit_and_legacy_korean_remains_readable(self):
        profile = RuntimeProfile(kind="workflow", language="en")
        self.assertEqual(profile.to_dict()["language"], "en")
        self.assertTrue(profile.package_name.endswith("-en"))
        self.assertEqual(RuntimeProfile.from_dict(RuntimeProfile().to_dict()).language, "ko")
        config = replace(settings(), language="en")
        with patch.dict("os.environ", {}, clear=True):
            contract = runtime_contract(ROOT, config, profile)
        self.assertEqual(contract["corpus_hash"], digest(load_documents(ROOT, "en")))
        with self.assertRaises(ValueError):
            runtime_contract(ROOT, settings(), profile)
