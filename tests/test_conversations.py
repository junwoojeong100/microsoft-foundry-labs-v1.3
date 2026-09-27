import copy
import json
import unittest
from unittest.mock import patch

from foundry_workshop import conversations
from foundry_workshop.contracts import ModelOutputError, load_cases, read_json, write_json
from foundry_workshop.settings import Settings

from . import ROOT, workspace


def settings():
    return Settings(
        "https://unit.services.ai.azure.com/api/projects/workshop",
        "unit-target",
        None,
        "managed-identity",
        None,
        2048,
        language="en",
    )


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.answers = read_json(ROOT / "data/fixtures/en/answers.json")
        self.cases = load_cases(ROOT, "dev", "en")
        self.by_question = {item["question"]: item["case_id"] for item in self.cases}
        self.fail_case = None

    def invoke(self, messages, instructions):
        self.calls.append((copy.deepcopy(messages), instructions))
        case_id = self.by_question[messages[-1]["content"]]
        if case_id == self.fail_case:
            raise ModelOutputError(
                "Explicit unit-test failure",
                {"raw": {"status": "incomplete"}, "response_id": "resp_failed"},
            )
        return {
            "status": "completed",
            "text": json.dumps(self.answers[case_id]),
            "response_id": f"resp_{case_id}",
            "response_model": "unit-model",
            "usage": {"input_tokens": 20, "output_tokens": 30},
            "raw": {"unit_test_fixture": True},
        }

    def collect(self, root, label="unit"):
        return conversations.collect(root, settings(), label, "v2", self.invoke, (ValueError,))

    def test_plan_reads_dev_only_and_has_two_three_turn_conversations(self):
        with patch("foundry_workshop.conversations.load_cases", wraps=load_cases) as loader:
            plan = conversations.plan(ROOT, "en")
        loader.assert_called_once_with(ROOT, "dev", "en")
        self.assertEqual(plan["target_turns"], 6)
        self.assertEqual(plan["conversation_count"], 2)
        self.assertFalse(plan["azure_requests_sent"])
        self.assertFalse(plan["holdout_loaded"])

    def test_histories_reuse_only_the_same_conversation_and_never_send_gold(self):
        with workspace() as root:
            result = self.collect(root)
            self.assertTrue(result["gate_passed"])
            self.assertEqual(result["business"]["turn_checks"]["total"], 6)
            self.assertEqual(result["business"]["turn_checks"]["passed"], 6)
            _, _, rows, whole = conversations.load(root, "unit")
            self.assertEqual(len(rows), 6)
            self.assertEqual(len(whole), 2)
            self.assertIn("code_hash", result)
        self.assertEqual([len(messages) for messages, _ in self.calls], [2, 4, 6, 2, 4, 6])
        for messages, _ in self.calls:
            serialized = json.dumps(messages)
            self.assertNotIn("expected_decision", serialized)
            self.assertNotIn("required_citations", serialized)
            self.assertNotIn("ground_truth", serialized)
        self.assertNotIn(
            json.dumps(self.answers["D01"]),
            [message["content"] for message in self.calls[3][0]],
        )

    def test_failure_preserves_denominator_raw_error_and_blocks_later_turns(self):
        self.fail_case = "D02"
        with workspace() as root:
            result = self.collect(root)
            self.assertFalse(result["gate_passed"])
            report = result["business"]["turn_checks"]
            self.assertEqual(report["total"], 6)
            self.assertEqual(report["errors"], 2)
            self.assertLessEqual(report["passed"], 4)
            directory = root / "outputs/conversations/unit"
            self.assertEqual(
                read_json(directory / "D02-response-error.json")["raw"]["status"], "incomplete"
            )
            self.assertFalse((directory / "D03-request.json").exists())
            with patch("foundry_workshop.native.evaluate_items") as evaluator:
                with self.assertRaisesRegex(ValueError, "complete real run"):
                    conversations.evaluate_native(
                        root, settings(), "unit", "conversation", confirmed=True, timeout=5
                    )
                evaluator.assert_not_called()
        self.assertEqual(len(self.calls), 5)

    def test_native_turn_and_conversation_inputs_have_different_complete_denominators(self):
        with workspace() as root:
            self.collect(root)
            with patch("foundry_workshop.native.evaluate_items", return_value={}) as evaluate:
                conversations.evaluate_native(
                    root, settings(), "unit", "turn", confirmed=True, timeout=5
                )
                turn_call = evaluate.call_args
                conversations.evaluate_native(
                    root, settings(), "unit", "conversation", confirmed=True, timeout=5
                )
                conversation_call = evaluate.call_args
            self.assertEqual(len(turn_call.args[2]), 6)
            self.assertEqual(len(conversation_call.args[2]), 2)
            self.assertEqual(
                conversation_call.kwargs["evaluator_names"], ("groundedness", "coherence")
            )
            self.assertTrue(conversation_call.kwargs["messages_input"])
            self.assertEqual(conversation_call.kwargs["evaluation_level"], "conversation")
            self.assertEqual(len(self.calls), 6)

    def test_existing_output_and_changed_messages_are_rejected(self):
        with workspace() as root:
            self.collect(root)
            with self.assertRaises(FileExistsError):
                self.collect(root)
            path = root / "outputs/conversations/unit/conversations.json"
            data = read_json(path)
            data[0]["messages"][-1]["content"] = "Altered output"
            write_json(path, data)
            with self.assertRaisesRegex(ValueError, "changed"):
                conversations.business_report(root, "unit")
