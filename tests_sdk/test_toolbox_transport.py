import copy
import json
import os
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from azure.ai.projects import AIProjectClient
from azure.core.pipeline.transport import HttpResponse, HttpTransport

from foundry_workshop import toolbox
from foundry_workshop.contracts import read_json
from tests import workspace
from tests.test_toolbox import ENVIRONMENT, seed_ledger, settings

from .test_sdk_contracts import DummyCredential


class Reply(HttpResponse):
    def __init__(self, request, status, payload):
        super().__init__(request, None)
        self.status_code = status
        self.headers = {"content-type": "application/json"}
        self.content_type = "application/json"
        self._body = json.dumps(payload).encode()

    def body(self):
        return self._body

    def json(self):
        return json.loads(self._body)


class ToolboxTransport(HttpTransport):
    def __init__(self, *, existing=False, authentication="AAD"):
        self.requests = []
        self.versions = {"1": toolbox.definition()} if existing else {}
        self.default = "1" if existing else None
        self.authentication = authentication

    def open(self):
        return self

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def send(self, request, **_kwargs):
        self.requests.append(request)
        path = urlsplit(request.url).path
        name = "lab-unit-tools-en"
        if path.endswith("/connections/lab-unit-search"):
            return Reply(
                request,
                200,
                {
                    "name": "lab-unit-search",
                    "id": "unit-connection-id",
                    "type": "CognitiveSearch",
                    "target": "https://unit.search.windows.net",
                    "is_default": False,
                    "credentials": {"type": self.authentication},
                    "metadata": {},
                },
            )
        if path.endswith("/agents"):
            return Reply(request, 200, {"data": [], "has_more": False})
        if path.endswith("/versions") and request.method == "POST":
            version = str(len(self.versions) + 1)
            self.versions[version] = json.loads(request.body)
            if self.default is None:
                self.default = version
            return Reply(request, 200, {"name": name, "version": version, **self.versions[version]})
        if "/versions/" in path:
            version = path.rsplit("/", 1)[-1]
            return Reply(request, 200, {"name": name, "version": version, **self.versions[version]})
        if path.endswith("/versions"):
            return Reply(
                request,
                200,
                {
                    "data": [
                        {"name": name, "version": version, **body}
                        for version, body in self.versions.items()
                    ],
                    "has_more": False,
                },
            )
        if request.method == "PATCH":
            self.default = json.loads(request.body)["default_version"]
        if request.method == "DELETE":
            self.versions.clear()
            self.default = None
            return Reply(request, 204, {})
        if not self.versions:
            return Reply(
                request,
                404,
                {"error": {"code": "ResourceNotFound", "message": "Unit Toolbox absent"}},
            )
        return Reply(request, 200, {"id": name, "name": name, "default_version": self.default})


class ToolboxSDKTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, ENVIRONMENT, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def test_sdk_create_snapshot_promotion_rollback_and_cleanup_are_owned_and_exact(self):
        transport = ToolboxTransport()
        with workspace() as root:
            seed_ledger(root)
            with AIProjectClient(
                endpoint=settings().project_endpoint,
                credential=DummyCredential(),
                transport=transport,
            ) as project:
                first = toolbox.create_version(project, root, settings(), confirmed=True)
                self.assertEqual(first["selected_version"], "1")
                second = toolbox.create_version(
                    project, root, settings(), confirmed=True, new_version=True
                )
                self.assertEqual(second["default_version"], "1")
                self.assertEqual(second["selected_version"], "2")
                promoted = toolbox.select_version(project, root, settings(), "2", confirmed=True)
                self.assertEqual(promoted["default_change"]["after"], "2")
                restored = toolbox.select_version(project, root, settings(), "1", confirmed=True)
                self.assertEqual(restored["default_change"]["after"], "1")
                receipt = toolbox.delete_owned(project, root, settings(), confirmed=True)
            self.assertTrue(receipt["verified_absent"])
            ownership = read_json(toolbox.ledger_file(root, settings()))
            self.assertEqual(set(ownership["versions"]), {"1", "2"})
            self.assertTrue(
                toolbox.ledger_file(root, settings()).with_name("cleanup.json").exists()
            )
        bodies = [
            json.loads(request.body) for request in transport.requests if request.method == "POST"
        ]
        self.assertEqual(len(bodies), 2)
        self.assertEqual(bodies[0]["tools"][0]["azure_ai_search"]["indexes"][0]["top_k"], 6)
        self.assertEqual(
            bodies[0]["tools"][0]["azure_ai_search"]["indexes"][0]["project_connection_id"],
            "unit-connection-id",
        )
        self.assertTrue(all("api-version=" in request.url for request in transport.requests))

    def test_project_managed_identity_connection_is_accepted_without_credentials(self):
        transport = ToolboxTransport(authentication="ProjectManagedIdentity")
        with workspace() as root:
            seed_ledger(root)
            with AIProjectClient(
                endpoint=settings().project_endpoint,
                credential=DummyCredential(),
                transport=transport,
            ) as project:
                result = toolbox.create_version(project, root, settings(), confirmed=True)
            self.assertEqual(result["connection"]["authentication"], "ProjectManagedIdentity")
            self.assertEqual(result["selected_version"], "1")

    def test_existing_unowned_toolbox_never_produces_a_write(self):
        transport = ToolboxTransport(existing=True)
        with workspace() as root:
            seed_ledger(root)
            with (
                AIProjectClient(
                    endpoint=settings().project_endpoint,
                    credential=DummyCredential(),
                    transport=transport,
                ) as project,
                self.assertRaisesRegex(ValueError, "already exists"),
            ):
                toolbox.create_version(project, root, settings(), confirmed=True)
            self.assertFalse(toolbox.ledger_file(root, settings()).exists())
        self.assertTrue(all(request.method == "GET" for request in transport.requests))

    def test_metadata_drift_is_rejected_before_model_or_tool_inference(self):
        transport = ToolboxTransport(existing=True)
        changed = copy.deepcopy(transport.versions["1"])
        changed["tools"][0]["azure_ai_search"]["indexes"][0]["index_name"] = "another-index"
        transport.versions["1"] = changed
        with (
            AIProjectClient(
                endpoint=settings().project_endpoint,
                credential=DummyCredential(),
                transport=transport,
            ) as project,
            self.assertRaisesRegex(ValueError, "preset"),
        ):
            toolbox.snapshot(project, settings())
        self.assertTrue(all(request.method == "GET" for request in transport.requests))
