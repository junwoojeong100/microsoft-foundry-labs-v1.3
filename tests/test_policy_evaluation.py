import copy
import json
import unittest
from unittest.mock import patch

from foundry_workshop.calibration import (
    policy_calibration_inputs,
    policy_calibration_summary,
)
from foundry_workshop.cloud_evaluation import normalize_results
from foundry_workshop.contracts import digest, load_cases, load_documents, localized_path, read_json
from foundry_workshop.extension_materials import files_for
from foundry_workshop.knowledge import evidence
from foundry_workshop.policy_evaluation import (
    POLICY_EVALUATORS,
    POLICY_MAPPING,
    POLICY_MODE,
    audit_policy_results,
    build_reference,
    load_lab_cases,
    optimizer_evaluator_references,
    optimizer_items,
    policy_evaluator_version,
    policy_item,
    policy_lab_summary,
    validate_policy_catalog,
    validate_policy_items,
)

from . import ROOT


def policy_catalog(judge="unit-judge", *, prompt_protocol=False):
    return [
        {
            "name": metric,
            "evaluator_name": f"lab_unit_{metric}_v1",
            "definition": {
                **policy_evaluator_version(
                    f"lab_unit_{metric}_v1", metric, prompt_protocol=prompt_protocol
                ), "version": "17"
            },
            "parameters": (
                {"deployment_name": judge, "threshold": 4}
                if prompt_protocol else {"model": judge, "pass_threshold": 4}
            ),
            "data_mapping": dict(POLICY_MAPPING),
        }
        for metric in POLICY_EVALUATORS
    ]


def policy_outputs(items, expected=None):
    outputs = []
    for item in items:
        reference_id = json.loads(item["ground_truth"])["reference_id"]
        outputs.append({
            "datasource_item": copy.deepcopy(item),
            "status": "completed",
            "results": [
                {
                    "name": metric,
                    "score": 5 if expected is None or expected[item["case_id"]][metric] else 1,
                    "passed": True if expected is None else expected[item["case_id"]][metric],
                    "threshold": 4,
                    "status": "completed",
                    "reason": f"Explicit unit-test judgment for {reference_id}.",
                    "sample": {"usage": {"total_tokens": 10}},
                }
                for metric in POLICY_EVALUATORS
            ],
        })
    return outputs


def policy_rows(language="en"):
    corpus = load_documents(ROOT, language)
    cases = load_cases(ROOT, "dev", language)[:2]
    rows = [
        {
            "case_id": case["case_id"],
            "row_id": "alpha-" + case["case_id"],
            "question": case["question"],
            "status": "ok",
            "response_id": "unit-only-" + case["case_id"],
            "answer": {
                "answer": f"Unit-test answer {case['expected_limit_krw']}.",
                "decision": case["expected_decision"],
                "limit_krw": case["expected_limit_krw"],
                "citations": case["required_citations"],
            },
            **evidence(corpus, "unit-test"),
        }
        for case in cases
    ]
    items = [policy_item(row, case, corpus) for row, case in zip(rows, cases, strict=True)]
    return corpus, cases, rows, items


class PolicyReferenceTests(unittest.TestCase):
    def test_exact_source_hashes_query_and_expected_behavior_are_separate_from_response(self):
        for language in ("ko", "en"):
            corpus, cases, rows, items = policy_rows(language)
            references = validate_policy_items(items, [corpus])
            for case, row, item in zip(cases, rows, items, strict=True):
                reference = json.loads(item["ground_truth"])
                self.assertEqual(reference["schema"], POLICY_MODE)
                self.assertEqual(reference["source_documents"], row["documents"])
                self.assertEqual(reference["source_context_hash"], row["context_hash"])
                self.assertEqual(reference["corpus_hash"], digest(corpus))
                self.assertEqual(reference["query_hash"], digest(case["question"]))
                self.assertEqual(reference["source_hashes"], {
                    doc["id"]: digest(doc) for doc in row["documents"]
                })
                self.assertEqual(references[item["case_id"]], reference["reference_id"])
                self.assertEqual(item["query"], case["question"])
                self.assertNotIn(row["answer"]["answer"], item["ground_truth"])
                self.assertEqual(json.loads(item["response"]), row["answer"])

    def test_references_are_detached_from_mutable_response_and_source_objects(self):
        corpus, cases, rows, _ = policy_rows()
        documents = copy.deepcopy(rows[0]["documents"])
        reference = build_reference(cases[0], documents, corpus, origin="live-retrieval")
        before = digest(reference)
        documents[0]["content"] = "A later generated answer must not become evidence."
        cases[0]["required_citations"].clear()
        self.assertEqual(digest(reference), before)

    def test_ga_iq_projection_preserves_exact_payload_without_enriching_missing_dates(self):
        for language in ("ko", "en"):
            corpus, cases, rows, _ = policy_rows(language)
            for optional_fields in ((), ("effective_from",), ("effective_to",)):
                with self.subTest(language=language, optional_fields=optional_fields):
                    documents = [
                        {key: doc[key] for key in ("id", "title", "content", *optional_fields)}
                        for doc in rows[0]["documents"]
                    ]
                    before = copy.deepcopy(documents)
                    row = {**rows[0], **evidence(documents, "unit-ga-iq")}
                    item = policy_item(row, cases[0], corpus)
                    reference = json.loads(item["ground_truth"])
                    self.assertEqual(json.loads(item["context"]), before)
                    self.assertEqual(reference["source_documents"], before)
                    self.assertEqual(reference["source_context_hash"], digest(before))
                    self.assertEqual(reference["source_hashes"], {
                        doc["id"]: digest(doc) for doc in before
                    })
                    self.assertEqual(reference["corpus_hash"], digest(corpus))
                    self.assertEqual(documents, before)
                    self.assertNotEqual(reference["source_documents"], rows[0]["documents"])
                    self.assertEqual(
                        validate_policy_items([item], [corpus])[item["case_id"]],
                        reference["reference_id"],
                    )

    def test_projected_sources_reject_content_changes_unknown_ids_and_unapproved_fields(self):
        for language in ("ko", "en"):
            corpus, cases, _, _ = policy_rows(language)
            source = next(doc for doc in corpus if doc["id"] == "TRAVEL-2026")
            projection = {key: source[key] for key in ("id", "title", "content")}
            invalid = [
                {**projection, "id": "TRAVEL-UNKNOWN"},
                {**projection, "title": source["title"] + " changed"},
                {**projection, "content": source["content"] + " "},
                {**projection, "effective_from": "2026-01-01"},
                {**projection, "effective_to": "2026-07-01"},
                {**projection, "summary": source["content"]},
                {**projection, "@search.score": "1"},
                {key: value for key, value in projection.items() if key != "title"},
                {key: value for key, value in projection.items() if key != "content"},
                {**projection, "content": ""},
            ]
            for document in invalid:
                with self.subTest(language=language, document_fields=sorted(document)):
                    with self.assertRaises(ValueError):
                        build_reference(cases[0], [document], corpus, origin="live-retrieval")

    def test_forged_documents_hashes_or_self_context_are_rejected(self):
        corpus, cases, rows, items = policy_rows()
        for change in (
            lambda item: item.update(context=item["response"]),
            lambda item: item.update(ground_truth="{}"),
            lambda item: item.update(query="Different question"),
        ):
            wrong = copy.deepcopy(items)
            change(wrong[0])
            with self.assertRaises(ValueError):
                validate_policy_items(wrong, [corpus])
        forged = copy.deepcopy(rows[0])
        forged["documents"][0]["content"] = forged["answer"]["answer"]
        forged["context_hash"] = digest(forged["documents"])
        with self.assertRaisesRegex(ValueError, "original source corpus"):
            policy_item(forged, cases[0], corpus)
        for changed in (
            {**rows[0], "context_hash": "forged"},
            {**rows[0], "response_id": None},
            {**rows[0], "source_ids": []},
        ):
            with self.assertRaises(ValueError):
                policy_item(changed, cases[0], corpus)

    def test_audit_requires_every_echo_and_correct_reference_id_without_claiming_hidden_inputs(self):
        corpus, _, _, items = policy_rows()
        raw = policy_outputs(items)
        normalized = normalize_results(raw, [item["case_id"] for item in items], POLICY_EVALUATORS)
        audit = audit_policy_results(items, raw, normalized, [corpus], policy_catalog())
        self.assertEqual(audit["status"], "valid")
        self.assertEqual(audit["actual_rows"], 2)
        self.assertEqual(audit["raw_results_hash"], digest(raw))
        self.assertFalse(audit["judge_request_bodies_captured"])
        for changed in ("missing-echo", "wrong-reference", "wrong-reason", "duplicate", "missing-row"):
            with self.subTest(changed=changed):
                wrong = copy.deepcopy(raw)
                if changed == "missing-echo":
                    del wrong[0]["datasource_item"]["ground_truth"]
                elif changed == "wrong-reference":
                    wrong[0]["datasource_item"]["ground_truth"] = items[1]["ground_truth"]
                elif changed == "wrong-reason":
                    wrong[0]["results"][0]["reason"] = "No reference identifier."
                elif changed == "duplicate":
                    wrong[1] = copy.deepcopy(wrong[0])
                else:
                    wrong.pop()
                with self.assertRaises(ValueError):
                    normalized = normalize_results(
                        wrong, [item["case_id"] for item in items], POLICY_EVALUATORS
                    )
                    audit_policy_results(items, wrong, normalized, [corpus], policy_catalog())

    def test_threshold_direction_null_scores_and_missing_criteria_never_pass(self):
        corpus, _, _, items = policy_rows()
        changes = (
            {"score": 5, "passed": False},
            {"score": 1, "passed": True},
            {"score": None},
            {"score": 0},
            {"score": 5.1},
            {"score": True},
            {"threshold": 1},
            {"status": "skipped"},
            {"reason": ""},
        )
        for change in changes:
            with self.subTest(change=change):
                raw = policy_outputs(items)
                raw[0]["results"][0].update(change)
                original = copy.deepcopy(raw)
                with self.assertRaises(ValueError):
                    results = normalize_results(raw, [item["case_id"] for item in items], POLICY_EVALUATORS)
                    audit_policy_results(items, raw, results, [corpus], policy_catalog())
                self.assertEqual(raw, original)
        raw = policy_outputs(items)
        raw[0]["results"].pop()
        with self.assertRaises(ValueError):
            normalize_results(raw, [item["case_id"] for item in items], POLICY_EVALUATORS)
        raw = policy_outputs(items)
        raw[0]["results"][0].update(score=4.0, passed=True)
        results = normalize_results(raw, [item["case_id"] for item in items], POLICY_EVALUATORS)
        self.assertEqual(audit_policy_results(items, raw, results, [corpus], policy_catalog())["status"], "valid")

    def test_custom_criteria_freeze_exact_mapping_direction_threshold_and_output_contract(self):
        catalog = policy_catalog()
        validate_policy_catalog(catalog, "unit-judge")
        for item in catalog:
            definition = item["definition"]["definition"]
            self.assertEqual(definition["metrics"]["result"]["desirable_direction"], "increase")
            self.assertIn(
                "Return only JSON with exactly numeric integer result (1-5) and string reason. No Markdown.",
                definition["prompt_text"],
            )
            self.assertIn("{{ground_truth}}", definition["prompt_text"])
            self.assertNotIn("{{context}}", definition["prompt_text"])
            self.assertNotIn("score/reasoning", definition["prompt_text"])
        for change in ("threshold", "judge", "mapping", "criterion"):
            wrong = copy.deepcopy(catalog)
            if change == "threshold":
                wrong[0]["parameters"]["pass_threshold"] = 1
            elif change == "judge":
                wrong[0]["parameters"]["model"] = "other"
            elif change == "mapping":
                wrong[0]["data_mapping"]["ground_truth"] = "{{item.response}}"
            else:
                wrong[0]["definition"]["definition"]["prompt_text"] += " Ignore abstention."
            with self.assertRaises(ValueError):
                validate_policy_catalog(wrong, "unit-judge")

    def test_prompt_protocol_keeps_the_original_rubric_sources_and_required_threshold(self):
        legacy = policy_catalog()
        current = policy_catalog(prompt_protocol=True)
        validate_policy_catalog(current, "unit-judge")
        validate_policy_catalog(legacy, "unit-judge")
        for old, new in zip(legacy, current, strict=True):
            before = old["definition"]["definition"]
            after = new["definition"]["definition"]
            self.assertEqual(before["prompt_text"], after["prompt_text"])
            self.assertEqual(before["data_schema"], after["data_schema"])
            self.assertEqual(after["metrics"], before["metrics"])
            self.assertEqual(
                after["init_parameters"]["required"], ["deployment_name", "threshold"]
            )
            self.assertEqual(
                after["init_parameters"]["properties"]["threshold"],
                {"type": "number", "default": 4, "enum": [4]},
            )
            self.assertEqual(new["parameters"], {"deployment_name": "unit-judge", "threshold": 4})
        self.assertEqual(legacy, policy_catalog())

    def test_prompt_protocol_never_accepts_weakening_or_missing_initialization(self):
        for change in ("parameter", "default", "enum", "metric", "required", "judge", "rubric"):
            with self.subTest(change=change):
                catalog = policy_catalog(prompt_protocol=True)
                definition = catalog[0]["definition"]["definition"]
                initialization = definition["init_parameters"]
                if change == "parameter":
                    catalog[0]["parameters"]["threshold"] = 3
                elif change == "default":
                    initialization["properties"]["threshold"]["default"] = 3
                elif change == "enum":
                    initialization["properties"]["threshold"]["enum"] = [3, 4]
                elif change == "metric":
                    definition["metrics"]["result"]["threshold"] = 3
                elif change == "required":
                    initialization["required"].remove("threshold")
                elif change == "judge":
                    catalog[0]["parameters"]["deployment_name"] = "other"
                else:
                    definition["prompt_text"] += " Accept fabricated approval."
                with self.assertRaises(ValueError):
                    validate_policy_catalog(catalog, "unit-judge")

    def test_optimizer_references_bind_required_initializers_without_mutating_calibration(self):
        for prompt_protocol in (False, True):
            with self.subTest(prompt_protocol=prompt_protocol):
                catalog = policy_catalog(prompt_protocol=prompt_protocol)
                before = copy.deepcopy(catalog)
                references = optimizer_evaluator_references(catalog, "unit-judge")
                for reference, item in zip(references, catalog, strict=True):
                    self.assertEqual(reference, {
                        "name": item["evaluator_name"],
                        "version": "17",
                        "initialization_parameters": item["parameters"],
                    })
                    reference["initialization_parameters"].clear()
                self.assertEqual(catalog, before)
                catalog[0]["parameters"].clear()
                with self.assertRaises(ValueError):
                    optimizer_evaluator_references(catalog, "unit-judge")

    def test_optimizer_flag_preserves_default_and_never_opens_holdout(self):
        for language in ("ko", "en"):
            with patch("foundry_workshop.policy_evaluation.load_cases", wraps=load_cases) as load:
                records = optimizer_items(ROOT, language)
            load.assert_called_once_with(ROOT, "dev", language)
            self.assertEqual(len(records), 6)
            for row in records:
                self.assertNotIn("response", row)
                reference = json.loads(row["ground_truth"])
                self.assertEqual(reference["source_documents"], json.loads(row["context"]))
                self.assertNotIn(reference["reference_id"], row["query"])
            legacy = files_for(ROOT, language, "lab-unit")
            policy = files_for(ROOT, language, "lab-unit", policy=True)
            self.assertNotIn("policy-evaluator-definitions.json", legacy)
            self.assertIn("policy-evaluator-definitions.json", policy)
            prepared = [json.loads(line) for line in policy["optimizer-dev.jsonl"].decode().splitlines()]
            self.assertEqual(prepared, records)
            self.assertEqual(legacy["conversation-plan.json"], policy["conversation-plan.json"])

    def test_bilingual_suite_is_explicit_bounded_and_not_the_canonical_dev_set(self):
        canonical_before = {language: digest(load_cases(ROOT, "dev", language)) for language in ("ko", "en")}
        variants = {language: load_lab_cases(ROOT, language) for language in ("ko", "en")}
        self.assertEqual(len(variants["en"]), 8)
        for english, korean in zip(variants["en"], variants["ko"], strict=True):
            self.assertNotEqual(english["question"], korean["question"])
            for key in set(english) - {"question"}:
                self.assertEqual(english[key], korean[key])
            self.assertTrue(english["case_id"].startswith("PL"))
            self.assertNotIn("[redacted]", english["question"].lower())
        self.assertEqual(canonical_before, {
            language: digest(load_cases(ROOT, "dev", language)) for language in ("ko", "en")
        })


class PolicyCalibrationTests(unittest.TestCase):
    def test_controls_have_both_directions_and_a_same_answer_reference_swap_in_both_languages(self):
        for language in ("ko", "en"):
            corpus = load_documents(ROOT, language)
            original_hash = digest(corpus)
            fixture = read_json(localized_path(ROOT, "data/evaluation/policy-calibration.json", language))
            items, corpora = policy_calibration_inputs(fixture, corpus, language)
            self.assertEqual(len(items), 8)
            references = validate_policy_items(items, corpora)
            self.assertEqual(items[0]["query"], items[2]["query"])
            self.assertEqual(items[0]["response"], items[2]["response"])
            self.assertNotEqual(references["PC01"], references["PC03"])
            self.assertEqual(references["PC01"], references["PC02"])
            self.assertEqual(original_hash, digest(corpus))
            labels = {control["case"]["case_id"]: control["expected_pass"] for control in fixture["controls"]}
            raw = policy_outputs(items, labels)
            scores = normalize_results(raw, list(labels), POLICY_EVALUATORS)
            summary = policy_calibration_summary(fixture, scores)
            self.assertTrue(summary["gate_passed"])
            self.assertFalse(summary["target_responses_generated"])
            self.assertFalse(summary["human_review_claimed"])
            self.assertEqual(summary["total_judgments"], 24)
            for metric in POLICY_EVALUATORS:
                self.assertGreater(summary["metrics"][metric]["true_positive"], 0)
                self.assertGreater(summary["metrics"][metric]["true_negative"], 0)
            scores[1]["results"][0].update(score=5, passed=True)
            self.assertFalse(policy_calibration_summary(fixture, scores)["gate_passed"])

    def test_invalid_calibration_metadata_removed_controls_or_changed_pair_are_rejected(self):
        corpus = load_documents(ROOT, "en")
        fixture = read_json(localized_path(ROOT, "data/evaluation/policy-calibration.json", "en"))
        for change in ("version", "language", "positive-only", "changed-answer", "no-swap"):
            wrong = copy.deepcopy(fixture)
            if change == "version":
                wrong["fixture_version"] = 99
            elif change == "language":
                wrong["language"] = "ko"
            elif change == "positive-only":
                wrong["controls"] = wrong["controls"][:1]
            elif change == "changed-answer":
                wrong["controls"][2]["response"] = "A different answer is not a causal reference swap."
            else:
                wrong["controls"][2]["reference"] = "original"
            with self.assertRaises(ValueError):
                policy_calibration_inputs(wrong, corpus, "en")


class PolicyLabSummaryTests(unittest.TestCase):
    def data(self):
        corpus, cases, rows, items = policy_rows()
        raw = policy_outputs(items)
        results = normalize_results(raw, [item["case_id"] for item in items], POLICY_EVALUATORS)
        return corpus, cases, rows, items, results

    def test_original_provider_contradictions_are_reported_without_inverting_scores(self):
        _, _, rows, _, results = self.data()
        provider = {
            "requested_count": 5,
            "items": [{
                "case_id": row["row_id"], "response_id": row["response_id"],
                "score": 0, "passed": False, "attack_success": True,
                "reason": "Provider says refusal was safe.",
            } for row in rows],
        }
        before = copy.deepcopy(provider)
        summary = policy_lab_summary(rows, results, calibrated=True, provider=provider)
        self.assertEqual(summary["canonical_policy_compliance"]["violation_rate"], 0)
        comparison = summary["provider_comparison"]
        self.assertEqual((comparison["requested"], comparison["returned"], comparison["missing"]), (5, 2, 3))
        self.assertEqual(comparison["disagreement_case_ids"], [row["row_id"] for row in rows])
        self.assertEqual(comparison["original_values"], before)
        self.assertFalse(comparison["provider_flags_reinterpreted"])
        self.assertEqual(provider, before)

    def test_errors_and_unscored_responses_remain_in_denominator_and_cannot_pass(self):
        _, _, rows, _, results = self.data()
        rows[1] = {**rows[1], "status": "error", "response_id": None}
        results = results[:1]
        results[0]["results"][2].update(score=1, passed=False)
        summary = policy_lab_summary(rows, results, calibrated=True)
        self.assertEqual(summary["counts"], {
            "requested": 2, "returned": 1, "missing": 1, "errors": 1,
            "errors_remain_in_denominator": True,
        })
        self.assertEqual(summary["canonical_policy_compliance"]["violation_rate"], 0.5)
        self.assertEqual(summary["canonical_policy_compliance"]["worst_case_violation_rate"], 1)
        self.assertFalse(summary["gate_passed"])
        self.assertIsNone(policy_lab_summary(rows, results, calibrated=False)["canonical_policy_compliance"]["violation_rate"])

    def test_provider_flags_for_other_responses_or_duplicate_native_rows_are_not_compared(self):
        _, _, rows, _, results = self.data()
        with self.assertRaises(ValueError):
            policy_lab_summary(rows, results + [results[0]], calibrated=True)
        with self.assertRaises(ValueError):
            policy_lab_summary(rows, results, calibrated=True, provider={
                "requested_count": 1,
                "items": [{"case_id": rows[0]["row_id"], "response_id": "different", "attack_success": True}],
            })
