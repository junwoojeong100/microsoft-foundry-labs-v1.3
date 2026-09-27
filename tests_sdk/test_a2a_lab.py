import json
import os
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from azure.ai.projects import AIProjectClient
from azure.core.pipeline.transport import HttpTransport

from foundry_workshop import a2a_lab
from foundry_workshop.contracts import read_json
from tests import workspace
from tests.test_toolbox import settings

from .test_sdk_contracts import DummyCredential
from .test_toolbox_transport import Reply


class A2ATransport(HttpTransport):
    def __init__(self):
        self.requests = []
        self.agents = {}
        self.versions = {}
        self.card_version = "1.0"
        self.patches = []

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
        if path.endswith("/agentCard/v1.0"):
            return Reply(
                request,
                200,
                {
                    "supportedInterfaces": [
                        {
                            "url": a2a_lab.base_path(settings()),
                            "protocolBinding": "JSONRPC",
                            "protocolVersion": self.card_version,
                        }
                    ],
                    "description": "Synthetic policy",
                    "skills": [],
                },
            )
        if "/connections/" in path:
            return Reply(
                request,
                200,
                {
                    "name": a2a_lab.names(settings())["connection"],
                    "id": "unit-a2a-link",
                    "type": "RemoteA2A",
                    "target": a2a_lab.base_path(settings()),
                    "is_default": False,
                    "credentials": {"type": "AAD"},
                    "metadata": {},
                },
            )
        if path.endswith("/agents"):
            return Reply(request, 200, {"data": [], "has_more": False})
        if path.endswith("/versions"):
            name = path.split("/")[-2]
            if request.method == "POST":
                self.agents[name] = json.loads(request.body)
                versions = self.versions.setdefault(name, [])
                item = {"name": name, "version": str(len(versions) + 1), **self.agents[name]}
                versions.append(item)
                return Reply(request, 200, item)
            return Reply(
                request,
                200,
                {"data": self.versions[name], "has_more": False},
            )
        name = path.rsplit("/", 1)[-1]
        if request.method == "PATCH":
            self.patches.append(json.loads(request.body))
            return Reply(request, 200, {"name": name, "id": name, "versions": {}})
        if name not in self.agents:
            return Reply(
                request,
                404,
                {"error": {"code": "ResourceNotFound", "message": "Unit agent absent"}},
            )
        return Reply(request, 200, {"name": name, "versions": {"latest": {"version": "1"}}})


class A2ASDKTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {"WORKSHOP_PREFIX": "lab-unit"}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def test_typed_sdk_requests_serialize_to_the_recorded_v1_contract(self):
        transport = A2ATransport()
        with workspace() as root:
            with AIProjectClient(
                endpoint=settings().project_endpoint,
                credential=DummyCredential(),
                transport=transport,
            ) as project:
                target = a2a_lab.target(project, root, settings(), confirmed=True)
                inspected = a2a_lab.inspect(project, root, settings())
                caller = a2a_lab.caller(project, root, settings(), confirmed=True)
            self.assertEqual(target["agent_version"], "1")
            self.assertEqual(inspected["selected_interface"]["protocolVersion"], "1.0")
            self.assertEqual(caller["requested_protocol"], "1.0")
            ledger = read_json(a2a_lab.ledger_path(root, settings()))
            tool = ledger["caller_request"]["definition"]["tools"][0]
            self.assertEqual(tool["type"], "a2a")
            self.assertEqual(tool["a2a_version"], "1.0")
            self.assertEqual(tool["project_connection_id"], "unit-a2a-link")
            self.assertEqual(tool["base_url"], a2a_lab.base_path(settings()))
            self.assertIs(tool["send_credentials_for_agent_card"], True)
            sent = transport.agents[a2a_lab.names(settings())["caller"]]
            self.assertEqual(sent["definition"], ledger["caller_request"]["definition"])
        card_requests = [
            request for request in transport.requests if request.url.endswith("/agentCard/v1.0")
        ]
        self.assertTrue(card_requests)
        self.assertTrue(all(request.headers["A2A-Version"] == "1.0" for request in card_requests))
        self.assertTrue(all(not request.body for request in card_requests))
        self.assertEqual(transport.patches, [a2a_lab.incoming_patch()])
        self.assertFalse(
            any("api-version=v1" in request.url for request in card_requests),
            "The protocol card uses the A2A header, not a management API version.",
        )

    def test_owned_caller_update_is_explicit_and_preserves_version_history(self):
        transport = A2ATransport()
        with workspace() as root:
            with AIProjectClient(
                endpoint=settings().project_endpoint,
                credential=DummyCredential(),
                transport=transport,
            ) as project:
                a2a_lab.target(project, root, settings(), confirmed=True)
                a2a_lab.caller(project, root, settings(), confirmed=True)
                with self.assertRaisesRegex(ValueError, "implicitly"):
                    a2a_lab.caller(project, root, settings(), confirmed=True)
                result = a2a_lab.caller(
                    project, root, settings(), confirmed=True, new_version=True
                )
            ledger = read_json(a2a_lab.ledger_path(root, settings()))
            self.assertEqual(result["agent_version"], "2")
            self.assertEqual(ledger["caller_version"], "2")
            self.assertEqual(ledger["previous_callers"][0]["version"], "1")
            self.assertEqual(len(transport.versions[a2a_lab.names(settings())["caller"]]), 2)
            self.assertFalse(any(request.method == "DELETE" for request in transport.requests))

    def test_preview_card_is_not_accepted_as_ga(self):
        transport = A2ATransport()
        with workspace() as root:
            with AIProjectClient(
                endpoint=settings().project_endpoint,
                credential=DummyCredential(),
                transport=transport,
            ) as project:
                a2a_lab.target(project, root, settings(), confirmed=True)
                transport.card_version = "0.3"
                with self.assertRaisesRegex(ValueError, "A2A 1.0 JSONRPC"):
                    a2a_lab.inspect(project, root, settings())
