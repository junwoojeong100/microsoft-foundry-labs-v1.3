import csv
import io
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from azure.core.exceptions import ResourceNotFoundError

from foundry_workshop import code_interpreter_lab, openapi_lab
from foundry_workshop.contracts import load_documents, read_json
from tests import workspace
from tests.test_toolbox import ENVIRONMENT, seed_ledger, settings


class AdditionalToolSDKTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, ENVIRONMENT, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def test_code_interpreter_uploads_only_derived_input_and_verifies_the_download(self):
        with workspace() as root:
            project, client = MagicMock(), MagicMock()
            project.agents.get.side_effect = ResourceNotFoundError("Unit agent absent")
            project.agents.create_version.return_value = SimpleNamespace(version="1")
            client.files.create.return_value = SimpleNamespace(id="file-source")
            raw = {
                "output": [
                    {
                        "type": "code_interpreter_call",
                        "status": "completed",
                        "container_id": "container-unit",
                        "code": "unit code",
                    },
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Generated synthetic CSV.",
                                "annotations": [
                                    {
                                        "type": "container_file_citation",
                                        "container_id": "container-unit",
                                        "file_id": "file-generated",
                                        "filename": "/mnt/data/policy-summary.csv",
                                    }
                                ],
                            }
                        ],
                    },
                ]
            }
            response = SimpleNamespace(
                status="completed",
                output_text="Generated synthetic CSV.",
                id="resp-unit",
                model="unit-model",
                usage=None,
                model_dump=lambda **_: raw,
            )
            client.responses.with_raw_response.create.return_value = SimpleNamespace(
                http_response=SimpleNamespace(json=lambda: raw), parse=lambda: response
            )
            content = io.StringIO(newline="")
            writer = csv.DictWriter(content, fieldnames=("id", "title"), lineterminator="\n")
            writer.writeheader()
            writer.writerows(
                {"id": row["id"], "title": row["title"]} for row in load_documents(root, "en")
            )
            client.containers.files.content.retrieve.return_value = io.BytesIO(
                content.getvalue().encode()
            )
            result = code_interpreter_lab.run(
                project,
                client,
                root,
                settings(),
                "unit-code",
                confirmed_create=True,
                confirmed_cost=True,
            )
            self.assertEqual(result["verified_rows"], 6)
            self.assertEqual(
                client.responses.with_raw_response.create.call_args.kwargs["extra_body"][
                    "agent_reference"
                ]["version"],
                "1",
            )
            definition = project.agents.create_version.call_args.kwargs["definition"].as_dict()
            self.assertEqual(definition["tools"][0]["container"]["file_ids"], ["file-source"])
            directory = root / "outputs/code-interpreter/unit-code"
            self.assertEqual(
                (directory / "policy-summary.csv").read_bytes(), content.getvalue().encode()
            )
            self.assertEqual(
                read_json(directory / "ownership.json")["container_ids"], ["container-unit"]
            )

    def test_openapi_spec_and_request_cannot_switch_to_a_different_index_or_auth_mode(self):
        with workspace() as root:
            seed_ledger(root)
            plan = openapi_lab.plan(settings())
            spec = plan["tool"]["openapi"]["spec"]
            self.assertEqual(plan["managed_identity_owner"], "foundry-account")
            self.assertEqual(plan["required_search_role"], "Search Index Data Reader")
            self.assertEqual(spec["servers"], [{"url": "https://unit.search.windows.net"}])
            self.assertEqual(list(spec["paths"]), ["/indexes/lab-unit-policies/docs/search"])
            self.assertEqual(
                plan["tool"]["openapi"]["auth"],
                {
                    "type": "managed_identity",
                    "security_scheme": {"audience": "https://search.azure.com"},
                },
            )
            client = MagicMock()
            raw = {
                "output": [
                    {"type": "openapi_call", "status": "completed", "call_id": "call-unit"},
                    {
                        "type": "openapi_call_output",
                        "status": "completed",
                        "call_id": "call-unit",
                        "output": json.dumps(
                            {"response": json.dumps({"value": load_documents(root, "en")})}
                        ),
                    },
                ]
            }
            response = SimpleNamespace(
                status="completed",
                output_text="Synthetic answer",
                id="resp-openapi",
                model="unit-model",
                usage=None,
                model_dump=lambda **_: raw,
            )
            client.responses.with_raw_response.create.return_value = SimpleNamespace(
                http_response=SimpleNamespace(json=lambda: raw), parse=lambda: response
            )
            result = openapi_lab.invoke(client, root, settings(), "unit-openapi", confirmed=True)
            self.assertEqual(result["mode"], "live-openapi-policy-query")
            request = client.responses.with_raw_response.create.call_args.kwargs
            parameter = spec["paths"]["/indexes/lab-unit-policies/docs/search"]["post"][
                "parameters"
            ][0]
            self.assertIs(parameter["required"], True)
            self.assertIn(
                f"{parameter['name']}={parameter['schema']['default']}",
                request["instructions"],
            )
            self.assertIn("top=6", request["instructions"])
            self.assertIn(
                "select=id,title,content,effective_from,effective_to", request["instructions"]
            )
            self.assertEqual(
                client.responses.with_raw_response.create.call_args.kwargs["extra_body"]["tools"],
                [plan["tool"]],
            )
            self.assertEqual(len(result["documents"]), 6)
            raw["output"] = []
            with self.assertRaisesRegex(ValueError, "actual OpenAPI"):
                openapi_lab.invoke(client, root, settings(), "unit-openapi-no-tool", confirmed=True)
            self.assertFalse(
                (root / "outputs/openapi-runs/unit-openapi-no-tool/summary.json").exists()
            )
