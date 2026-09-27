import contextlib
import io
import unittest

from foundry_workshop.cli import main
from foundry_workshop.contracts import (
    ModelOutputError,
    load_cases,
    load_documents,
    read_json,
    write_json,
)
from foundry_workshop.evaluation import (
    acceptance_report,
    compare_runs,
    evaluate_run,
    grade,
    load_run,
    record_feedback,
    summarize,
    validate_matrix,
)
from foundry_workshop.experiments import collect, offline_demo
from foundry_workshop.knowledge import evidence

from . import workspace


class EvaluationTests(unittest.TestCase):
    def live_test_run(
        self, root, label, *, split="dev", prompt="v2", candidate=None, callback=None
    ):
        """Exercise production control flow with explicit unit-test responses, never an Azure call."""
        context = evidence(load_documents(root), "unit-test")

        def fixture(case):
            return {
                **context,
                "answer": {
                    "answer": "Unit-test response, not an LLM result.",
                    "decision": case["expected_decision"],
                    "limit_krw": case["expected_limit_krw"],
                    "citations": case["required_citations"],
                },
                "response_id": "unit-" + case["case_id"],
                "response_model": "unit-model",
                "usage": None,
            }

        return collect(
            root,
            label=label,
            split=split,
            prompt_version=prompt,
            retrieval="local",
            mode="live",
            deployment="unit-deployment",
            inference={"project_endpoint": "https://unit.invalid", "max_output_tokens": 2048},
            answer_case=callback or fixture,
            candidate=candidate,
        )

    def test_fixture_scores_and_no_fake_usage(self):
        with workspace() as root:
            baseline = offline_demo(root, "demo-v1", "v1")
            candidate = offline_demo(root, "demo-v2", "v2")
            self.assertEqual((baseline["passed"], candidate["passed"]), (0, 6))
            self.assertIsNone(candidate["input_tokens"])
            self.assertIsNone(candidate["median_latency_seconds"])
            comparison = compare_runs(root, "demo-v1", "demo-v2", "prompt")
            self.assertIn("OFFLINE FIXTURES", comparison["note"])

    def test_existing_run_is_not_overwritten(self):
        with workspace() as root:
            offline_demo(root, "demo", "v2")
            before = (root / "outputs/demo/responses.jsonl").read_bytes()
            with self.assertRaises(FileExistsError):
                offline_demo(root, "demo", "v1")
            self.assertEqual(before, (root / "outputs/demo/responses.jsonl").read_bytes())

    def test_errors_are_in_the_denominator(self):
        def failed(_case):
            raise ValueError("simulated collection error")

        with workspace() as root:
            result = self.live_test_run(root, "errors", callback=failed)
            self.assertEqual((result["total"], result["errors"], result["failed"]), (6, 6, 6))
            self.assertEqual(result["pass_rate"], 0)
            self.assertFalse(result["business_gate_passed"])
            self.assertEqual(evaluate_run(root, "errors")["total"], 6)
            _, rows, _ = load_run(root, "errors")
            self.assertTrue(all("dev case" in row["error"] for row in rows))
            self.assertTrue(all("answer command" in row["error"] for row in rows))

    def test_holdout_error_guidance_preserves_rejection_without_repeating_cases(self):
        calls = []

        def failed(case):
            calls.append(case["case_id"])
            raise ModelOutputError(
                "Synthetic invalid output.",
                {
                    "response_id": "unit-" + case["case_id"],
                    "response_model": "unit-model",
                    "raw_response_text": "not JSON",
                },
            )

        with workspace() as root:
            self.live_test_run(root, "candidate")
            result = self.live_test_run(
                root, "holdout", split="holdout", candidate="candidate", callback=failed
            )
            self.assertEqual((result["total"], result["errors"], result["failed"]), (4, 4, 4))
            self.assertEqual(result["pass_rate"], 0)
            self.assertFalse(result["business_gate_passed"])
            manifest, rows, _ = load_run(root, "holdout")
            self.assertEqual(manifest["status"], "completed_with_errors")
            for row in rows:
                self.assertIn("Do not repeat or recollect holdout", row["error"])
                self.assertIn("evaluate", row["error"])
                self.assertIn("accept", row["error"])
                self.assertIn("locally", row["error"])
                self.assertNotIn("answer command", row["error"])
                self.assertEqual(row["response_id"], "unit-" + row["case_id"])
                self.assertEqual(row["raw_response_text"], "not JSON")
            saved = (root / "outputs/holdout/responses.jsonl").read_bytes()
            self.assertEqual(evaluate_run(root, "holdout")["errors"], 4)
            report = acceptance_report(root, "candidate", "holdout")
            self.assertEqual(report["recommendation"], "reject")
            self.assertFalse(report["deployment_approved"])
            self.assertEqual(saved, (root / "outputs/holdout/responses.jsonl").read_bytes())
            self.assertEqual(calls, ["H01", "H02", "H03", "H04"])

    def test_holdout_without_observed_models_keeps_an_incomplete_handoff(self):
        def failed(_case):
            raise ValueError("Synthetic request failed before receiving a model response.")

        with workspace() as root:
            self.live_test_run(root, "candidate")
            self.live_test_run(
                root, "holdout", split="holdout", candidate="candidate", callback=failed
            )
            _, rows, _ = load_run(root, "holdout")
            self.assertTrue(all("prerequisites are incomplete" in row["error"] for row in rows))
            self.assertEqual(evaluate_run(root, "holdout")["errors"], 4)
            with self.assertRaisesRegex(ValueError, "observed_models"):
                acceptance_report(root, "candidate", "holdout")
            self.assertFalse((root / "outputs/holdout/acceptance.json").exists())

    def test_fixture_error_guidance_does_not_send_learners_to_azure(self):
        def failed(_case):
            raise ValueError("Synthetic fixture failure.")

        with workspace() as root:
            result = collect(
                root,
                label="fixture-errors",
                split="dev",
                prompt_version="v2",
                retrieval="offline-fixture",
                mode="offline-fixture",
                deployment="not-a-model",
                answer_case=failed,
            )
            self.assertEqual((result["total"], result["errors"]), (6, 6))
            self.assertFalse(result["business_gate_passed"])
            _, rows, _ = load_run(root, "fixture-errors")
            for row in rows:
                self.assertIn("offline checker", row["error"])
                self.assertIn("do not make an Azure call", row["error"])
                self.assertNotIn("answer command", row["error"])
                self.assertIsNone(row["latency_seconds"])

    def test_invalid_model_output_preserves_response_id(self):
        def failed(_case):
            raise ModelOutputError(
                "invalid JSON", {"response_id": "unit-response", "raw_response_text": "not json"}
            )

        with workspace() as root:
            self.live_test_run(root, "bad-json", callback=failed)
            _, rows, _ = load_run(root, "bad-json")
            self.assertEqual(rows[0]["response_id"], "unit-response")
            self.assertEqual(rows[0]["raw_response_text"], "not json")
            self.assertEqual(rows[0]["status"], "error")

    def test_missing_duplicate_and_extra_rows_are_rejected(self):
        with workspace() as root:
            offline_demo(root, "demo", "v2")
            _, rows, cases = load_run(root, "demo")
            for invalid in (
                rows[:-1],
                rows + [rows[0]],
                rows[:-1] + [{**rows[0], "case_id": "UNKNOWN"}],
            ):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    validate_matrix(invalid, cases)

    def test_wrong_question_and_source_are_not_a_pass(self):
        with workspace() as root:
            offline_demo(root, "demo", "v2")
            _, rows, cases = load_run(root, "demo")
            with self.assertRaises(ValueError):
                validate_matrix([{**rows[0], "question": "different"}] + rows[1:], cases)
            row = {**rows[0], "source_ids": []}
            self.assertFalse(grade(row, cases[0])["passed"])
            row = {**rows[0], "answer": {**rows[0]["answer"], "citations": ["TRAVEL-2025"]}}
            self.assertFalse(grade(row, cases[0])["passed"])

    def test_tampered_response_fails_hash_check(self):
        with workspace() as root:
            offline_demo(root, "demo", "v2")
            path = root / "outputs/demo/responses.jsonl"
            path.write_text(path.read_text().replace("150000", "990000"), encoding="utf-8")
            with self.assertRaises(ValueError):
                evaluate_run(root, "demo")

    def test_incomplete_run_is_not_scored(self):
        with workspace() as root:
            offline_demo(root, "demo", "v2")
            path = root / "outputs/demo/manifest.json"
            manifest = read_json(path)
            manifest["status"] = "collecting"
            write_json(path, manifest)
            with self.assertRaises(ValueError):
                evaluate_run(root, "demo")

    def test_fixture_is_never_accepted_as_live_holdout(self):
        with workspace() as root:
            offline_demo(root, "demo", "v2")
            with self.assertRaises(ValueError):
                acceptance_report(root, "demo", "demo")
            with self.assertRaises(ValueError):
                record_feedback(
                    root, "demo", "D01", "A sufficiently detailed synthetic review reason."
                )

    def test_holdout_requires_frozen_candidate(self):
        with workspace() as root:
            with self.assertRaises(ValueError):
                self.live_test_run(root, "holdout", split="holdout")
            self.live_test_run(root, "candidate")
            with self.assertRaises(ValueError):
                self.live_test_run(
                    root, "changed", split="holdout", prompt="v1", candidate="candidate"
                )
            self.assertFalse((root / "outputs/changed").exists())

    def test_holdout_is_bound_but_does_not_approve_deployment(self):
        with workspace() as root:
            self.live_test_run(root, "candidate")
            self.live_test_run(root, "holdout", split="holdout", candidate="candidate")
            report = acceptance_report(root, "candidate", "holdout")
            self.assertTrue(report["business_gate_passed"])
            self.assertFalse(report["deployment_approved"])
            self.assertEqual(report["recommendation"], "ready-for-human-review")
            with self.assertRaises(ValueError):
                record_feedback(
                    root, "holdout", "H01", "This must not be harvested into development data."
                )

    def test_failed_candidate_does_not_unlock_holdout(self):
        with workspace() as root:
            self.live_test_run(root, "candidate", callback=lambda _case: {})
            with self.assertRaises(ValueError):
                self.live_test_run(root, "holdout", split="holdout", candidate="candidate")

    def test_review_is_pending_and_not_overwritten(self):
        with workspace() as root:
            self.live_test_run(root, "candidate")
            path = record_feedback(
                root, "candidate", "D01", "Review the synthetic answer against the original policy."
            )
            self.assertEqual(read_json(path)["approval_status"], "pending-human-review")
            with self.assertRaises(FileExistsError):
                record_feedback(
                    root, "candidate", "D01", "Do not overwrite the earlier review record."
                )

    def test_no_evidence_diagnostic_fails_honestly_and_never_enters_review(self):
        def withheld(case):
            return {
                **evidence([], "none"),
                "answer": {
                    "answer": "Unit-test response without evidence, not an LLM result.",
                    "decision": "insufficient_evidence",
                    "limit_krw": None,
                    "citations": [],
                },
                "response_id": "unit-" + case["case_id"],
                "response_model": "unit-model",
                "usage": None,
            }

        with workspace() as root:
            collect(
                root,
                label="diagnostic",
                split="dev",
                prompt_version="v1",
                retrieval="none",
                mode="live",
                deployment="unit-deployment",
                inference={"provider": "none", "max_documents": 0},
                answer_case=withheld,
            )
            result = evaluate_run(root, "diagnostic")
            self.assertEqual((result["passed"], result["errors"]), (0, 0))
            self.assertFalse(result["business_gate_passed"])
            self.assertTrue(
                all(not item["checks"]["citations_retrieved"] for item in result["checks"])
            )
            with self.assertRaisesRegex(ValueError, "no-evidence"):
                record_feedback(root, "diagnostic", "D01", "Evidence was removed on purpose here.")
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()) as errors,
            ):
                for extra in (
                    ["--split", "holdout", "--unlock-holdout", "--candidate", "diagnostic"],
                    ["--candidate", "diagnostic"],
                ):
                    self.assertEqual(
                        main(root, ["collect", "--label", "x", "--retrieval", "none", *extra]), 2
                    )
            self.assertIn("dev-only diagnostic", errors.getvalue())
            self.assertFalse((root / "outputs/x").exists())

    def test_compare_rejects_changed_inference_configuration(self):
        with workspace() as root:
            self.live_test_run(root, "first")
            self.live_test_run(root, "second")
            path = root / "outputs/second/manifest.json"
            manifest = read_json(path)
            manifest["inference"]["max_output_tokens"] = 8192
            write_json(path, manifest)
            with self.assertRaises(ValueError):
                compare_runs(root, "first", "second", "prompt")

    def test_evaluate_exit_code_and_path_rejection(self):
        with (
            workspace() as root,
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(main(root, ["demo", "--label", "bad", "--prompt", "v1"]), 0)
            self.assertEqual(main(root, ["evaluate", "--label", "bad"]), 1)
            self.assertEqual(main(root, ["evaluate", "--label", "../outside"]), 2)

    def test_unknown_latency_is_not_zero(self):
        with workspace() as root:
            offline_demo(root, "demo", "v2")
            _, rows, cases = load_run(root, "demo")
            result = summarize(rows, cases)
            self.assertEqual(result["latency_observations"], 0)
            self.assertIsNone(result["median_latency_seconds"])
            self.assertEqual(len(load_cases(root, "dev")), result["total"])


if __name__ == "__main__":
    unittest.main()
