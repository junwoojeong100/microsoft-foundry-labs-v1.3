import json
import unittest
from copy import deepcopy
from types import SimpleNamespace

from foundry_workshop import business_rubric_grader as grader
from foundry_workshop.contracts import ANSWER_SCHEMA, DECISIONS
from foundry_workshop.evaluation import grade, load_run
from foundry_workshop.experiments import offline_demo
from foundry_workshop.tool_evaluation import summarize_tool_results, tool_calls

from . import workspace


def item_for(row, case):
    return {
        "answer_json": json.dumps(row.get("answer"), ensure_ascii=False),
        "ground_truth": json.dumps(
            {
                key: case[key]
                for key in ("expected_decision", "expected_limit_krw", "required_citations")
            }
        ),
        "source_ids": json.dumps(row.get("source_ids", [])),
    }


class BusinessRubricGraderTests(unittest.TestCase):
    def test_grader_constants_match_the_answer_contract(self):
        self.assertEqual(grader.DECISIONS, DECISIONS)
        self.assertEqual(set(grader.FIELDS), set(ANSWER_SCHEMA["required"]))

    def test_foundry_grader_reproduces_every_local_business_check(self):
        mutations = (
            lambda answer, _case: answer,
            lambda answer, _case: {**answer, "decision": "insufficient_evidence"},
            lambda answer, _case: {**answer, "limit_krw": 1},
            lambda answer, _case: {**answer, "limit_krw": True},
            lambda answer, _case: {**answer, "citations": []},
            lambda answer, _case: {**answer, "citations": [*answer["citations"], "NOT-RETRIEVED"]},
            lambda answer, _case: {**answer, "citations": answer["citations"] * 2},
            lambda answer, _case: {**answer, "extra": "field"},
            lambda answer, _case: {**answer, "answer": " "},
        )
        with workspace() as root:
            for label, prompt in (("fixture-v1", "v1"), ("fixture-v2", "v2")):
                offline_demo(root, label, prompt)
                _, rows, cases = load_run(root, label)
                by_id = {case["case_id"]: case for case in cases}
                for row in rows:
                    case = by_id[row["case_id"]]
                    for mutate in mutations:
                        changed = deepcopy(row)
                        changed["answer"] = mutate(deepcopy(row["answer"]), case)
                        with self.subTest(
                            label=label, case=row["case_id"], answer=changed["answer"]
                        ):
                            local = grade(changed, case)
                            expected = {
                                key: value
                                for key, value in local["checks"].items()
                                if key != "completed"
                            }
                            item = item_for(changed, case)
                            self.assertEqual(grader.business_checks(item), expected)
                            score = grader.grade({}, item)
                            self.assertEqual(score, sum(expected.values()) / len(expected))
                            self.assertEqual(score >= 1.0, local["passed"])

    def test_malformed_items_score_zero_instead_of_raising(self):
        for item in ({}, {"answer_json": "{", "ground_truth": "{}", "source_ids": "[]"}):
            self.assertEqual(grader.grade({}, item), 0.0)


class ToolEvaluationSummaryTests(unittest.TestCase):
    def cases(self):
        return [
            {"case_id": "D01", "question": "Q1"},
            {"case_id": "D02", "question": "Q2"},
        ]

    def item(self, query, relevance=True, drop=False):
        results = [{"name": "tool_call_accuracy", "score": 5.0, "passed": True}]
        if not drop:
            results.append({"name": "relevance", "score": 2.0, "passed": relevance})
        return {"datasource_item": {"query": query}, "status": "completed", "results": results}

    def responses(self):
        return [{"text": "A1", "tool_calls": [{"name": "lookup_policy"}]}] * 2

    def summarize(self, items, status="completed"):
        return summarize_tool_results(
            status=status, output_items=items, cases=self.cases(), responses=self.responses()
        )

    def test_items_join_by_query_not_order_and_failures_stay_failures(self):
        summary = self.summarize([self.item("Q2", relevance=False), self.item("Q1")])
        self.assertTrue(summary["complete"])
        self.assertEqual([row["case_id"] for row in summary["rows"]], ["D01", "D02"])
        self.assertTrue(summary["rows"][0]["scores"]["relevance"]["passed"])
        self.assertFalse(summary["rows"][1]["scores"]["relevance"]["passed"])
        self.assertEqual(summary["native_pass_counts"]["tool_call_accuracy"]["passed"], 2)
        self.assertEqual(summary["native_pass_counts"]["relevance"]["passed"], 1)

    def test_missing_duplicate_or_unmapped_items_are_errors_not_passes(self):
        for items in (
            [self.item("Q1")],
            [self.item("Q1"), self.item("Q1")],
            [self.item("Q1"), self.item("unknown")],
            [self.item("Q1"), self.item("Q2", drop=True)],
        ):
            with self.subTest(items=items):
                summary = self.summarize(items)
                self.assertFalse(summary["complete"])
                self.assertFalse(summary["gate_passed"])
                self.assertGreaterEqual(summary["errors"], 1)

    def test_a_failed_or_timed_out_run_keeps_its_status_without_scores(self):
        for status in ("failed", "canceled", "timeout"):
            with self.subTest(status=status):
                summary = self.summarize([], status=status)
                self.assertFalse(summary["complete"])
                self.assertEqual(summary["errors"], 2)
                self.assertIn(status, summary["problems"][0])

    def test_only_function_calls_are_recorded(self):
        response = SimpleNamespace(
            messages=[
                SimpleNamespace(
                    contents=[
                        SimpleNamespace(type="text", text="ignored"),
                        SimpleNamespace(
                            type="function_call", name="lookup_policy", arguments={"query": "q"}
                        ),
                    ]
                )
            ]
        )
        self.assertEqual(
            tool_calls(response), [{"name": "lookup_policy", "arguments": {"query": "q"}}]
        )


if __name__ == "__main__":
    unittest.main()
