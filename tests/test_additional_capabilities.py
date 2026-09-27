import csv
import io
import json
import os
import unittest
from unittest.mock import MagicMock, patch

from foundry_workshop import a2a_lab, code_interpreter_lab
from foundry_workshop.contracts import load_documents

from . import ROOT, workspace
from .test_toolbox import settings


class AdditionalCapabilityTests(unittest.TestCase):
    def test_a2a_plan_explicitly_selects_v1_card_and_the_same_owned_project(self):
        with patch.dict(os.environ, {"WORKSHOP_PREFIX": "lab-unit"}, clear=True):
            value = a2a_lab.plan(settings())
        self.assertEqual(value["protocol"], "1.0")
        self.assertEqual(value["transport"], "JSONRPC")
        self.assertTrue(value["card_url"].endswith("/agentCard/v1.0"))
        self.assertTrue(value["target_base"].startswith(settings().project_endpoint))
        self.assertIn("lab-unit-a2a-target-en", value["target_base"])
        self.assertFalse(value["azure_requests_sent"])

    def test_additional_cloud_operations_are_opt_in(self):
        project, client = MagicMock(), MagicMock()
        with workspace() as root:
            with self.assertRaisesRegex(ValueError, "confirm-create"):
                a2a_lab.target(project, root, settings(), confirmed=False)
            with self.assertRaisesRegex(ValueError, "confirm-create"):
                a2a_lab.caller(project, root, settings(), confirmed=False)
            with self.assertRaisesRegex(ValueError, "confirm-cost"):
                a2a_lab.invoke(project, client, root, settings(), "unit", confirmed=False)
            with self.assertRaisesRegex(ValueError, "confirm-create"):
                code_interpreter_lab.run(
                    project,
                    client,
                    root,
                    settings(),
                    "unit",
                    confirmed_create=False,
                    confirmed_cost=True,
                )
            with self.assertRaisesRegex(ValueError, "confirm-delete"):
                code_interpreter_lab.cleanup(
                    project, client, root, settings(), "unit", confirmed=False
                )
        self.assertEqual(project.mock_calls, [])
        self.assertEqual(client.mock_calls, [])

    def test_a2a_interface_selection_never_uses_advertised_legacy_or_other_urls(self):
        url = "https://unit.services.ai.azure.com/api/projects/workshop/agents/unit/endpoint/protocols/a2a"
        card = {
            "supportedInterfaces": [
                {"url": url, "protocolVersion": "0.3", "protocolBinding": "HTTP+JSON"},
                {"url": url, "protocolVersion": "1.0", "protocolBinding": "JSONRPC"},
            ]
        }
        self.assertEqual(a2a_lab.select_v1_interface(card, url)["protocolVersion"], "1.0")
        with self.assertRaises(ValueError):
            a2a_lab.select_v1_interface(card, url + "/other")
        with self.assertRaises(ValueError):
            a2a_lab.select_v1_interface({"protocolVersion": "1.0"}, url)

    def test_legacy_event_names_require_an_accepted_ga_configuration_and_target_output(self):
        with patch.dict(os.environ, {"WORKSHOP_PREFIX": "lab-unit"}, clear=True):
            accepted = {
                "definition": {
                    "tools": [
                        {
                            "type": "a2a",
                            "a2a_version": "1.0",
                            "project_connection_id": "unit-link",
                        }
                    ]
                }
            }
            raw = {
                "output": [
                    {
                        "type": "a2a_preview_call",
                        "status": "completed",
                        "call_id": "unit-call",
                        "name": a2a_lab.names(settings())["connection"],
                    },
                    {
                        "type": "a2a_preview_call_output",
                        "status": "completed",
                        "call_id": "unit-call",
                        "output": json.dumps(
                            {
                                "answer": "Synthetic answer",
                                "decision": "needs_approval",
                                "limit_krw": 150000,
                                "citations": ["TRAVEL-2026", "APPROVAL-01"],
                            }
                        ),
                    },
                ]
            }
            result = a2a_lab.validate_delegation(raw, accepted, ROOT, settings(), "unit-link")
            self.assertEqual(result["accepted_a2a_version"], "1.0")
            self.assertEqual(result["observed_event_types"], ["a2a_preview_call"])
            self.assertFalse(result["protocol_packet_capture_performed"])
            accepted["definition"]["tools"][0]["a2a_version"] = "0.3"
            with self.assertRaises(ValueError):
                a2a_lab.validate_delegation(raw, accepted, ROOT, settings(), "unit-link")

    def test_generated_file_must_belong_to_an_actual_completed_code_call(self):
        raw = {
            "output": [
                {
                    "type": "code_interpreter_call",
                    "status": "completed",
                    "container_id": "cntr-unit",
                },
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "annotations": [
                                {
                                    "type": "container_file_citation",
                                    "container_id": "cntr-unit",
                                    "file_id": "file-unit",
                                    "filename": "/mnt/data/policy-summary.csv",
                                }
                            ],
                        }
                    ],
                },
            ]
        }
        self.assertEqual(code_interpreter_lab.generated_csv_citation(raw)["file_id"], "file-unit")
        raw["output"][1]["content"][0]["annotations"][0]["container_id"] = "another-container"
        with self.assertRaises(ValueError):
            code_interpreter_lab.generated_csv_citation(raw)
        with self.assertRaises(ValueError):
            code_interpreter_lab.generated_csv_citation({"output": []})

    def test_generated_csv_requires_all_original_ids_titles_and_order(self):
        documents = load_documents(ROOT, "en")
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=("id", "title"), lineterminator="\n")
        writer.writeheader()
        writer.writerows({"id": item["id"], "title": item["title"]} for item in documents)
        data = stream.getvalue().encode()
        self.assertEqual(len(code_interpreter_lab.validate_csv(data, documents)), 6)
        with self.assertRaises(ValueError):
            code_interpreter_lab.validate_csv(data, list(reversed(documents)))
        with self.assertRaises(ValueError):
            code_interpreter_lab.validate_csv(
                data.replace(b"TRAVEL-2026", b"ALTERED-DOC"), documents
            )
        with self.assertRaises(ValueError):
            code_interpreter_lab.validate_csv(b"id,title\n", documents)
