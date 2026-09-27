import os
import unittest
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

from agent_framework.exceptions import AgentFrameworkException

from foundry_workshop.toolbox import QUESTIONS
from foundry_workshop.toolbox_host import build_agent
from tests import ROOT
from tests.test_toolbox import ENVIRONMENT, settings


@contextmanager
def clients(*_args, **_kwargs):
    yield object(), object()


class ToolboxHostTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_workflow_adapter_invokes_the_same_guarded_toolbox_path(self):
        result = {
            "mode": "unit-test-transport",
            "model_calls": [{"response_id": "resp_unit", "response_model": "unit-model"}],
            "toolbox_version": "2",
        }
        with (
            patch.dict(os.environ, ENVIRONMENT, clear=True),
            patch("foundry_workshop.cloud.project_clients", clients),
            patch("foundry_workshop.toolbox_host.snapshot", return_value={"selected_version": "2"}),
            patch(
                "foundry_workshop.toolbox_host.execute", new=AsyncMock(return_value=result)
            ) as execute,
        ):
            agent = build_agent(ROOT, settings(), "2")
            response = await agent.run(QUESTIONS["en"])
            self.assertIn("unit-test-transport", response.text)
            self.assertEqual(execute.call_args.kwargs["question"], QUESTIONS["en"])
            self.assertTrue(execute.call_args.kwargs["confirmed"])

    async def test_unapproved_question_never_reaches_the_model_or_toolbox(self):
        with (
            patch.dict(os.environ, ENVIRONMENT, clear=True),
            patch("foundry_workshop.toolbox_host.execute", new=AsyncMock()) as execute,
        ):
            agent = build_agent(ROOT, settings(), "2")
            with self.assertRaises((ValueError, AgentFrameworkException)):
                await agent.run("Read a real customer's private account.")
            execute.assert_not_called()

    async def test_packaged_host_refuses_application_directory_for_evidence(self):
        with patch.dict(os.environ, ENVIRONMENT, clear=True):
            with self.assertRaisesRegex(ValueError, "writable session"):
                build_agent(
                    ROOT,
                    settings(),
                    "2",
                    packaged_source={},
                    questions=["Synthetic"],
                    evidence_root=ROOT / "outputs",
                )
