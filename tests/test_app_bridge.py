from __future__ import annotations

import importlib
import json
import sys
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import workshop
from tests.helpers import REPOSITORY, IsolatedWorkshop, fixture_result


class AppAndBridgeTests(IsolatedWorkshop):
    def test_app_shows_real_result_fields_without_creating_an_agent(self):
        path = self.root / "outputs/app-test.json"
        result = fixture_result(self.settings, "서울 2박", path, expected_version="7")
        with (
            patch.object(workshop, "load_settings", return_value=self.settings),
            patch.object(workshop, "ask", return_value=result) as ask,
        ):
            app = AppTest.from_file(str(REPOSITORY / "app.py")).run()
            self.assertEqual(len(app.exception), 0)
            self.assertIn("출장 도우미", app.title[0].value)
            app.text_area[0].input("서울 2박").run()
            app.button[0].click().run()
            self.assertEqual(len(app.exception), 0)
            ask.assert_called_once_with(self.settings, "서울 2박")
            self.assertTrue(
                any("오프라인 테스트 전용" in item.value for item in app.markdown)
            )
            self.assertTrue(any("version 7" in item.value for item in app.info))
            self.assertTrue(any("file_test" in str(item.value) for item in app.json))

    def test_app_error_clears_previous_success(self):
        result = fixture_result(
            self.settings,
            "첫 질문",
            self.root / "outputs/one.json",
            expected_version="7",
        )
        with (
            patch.object(workshop, "load_settings", return_value=self.settings),
            patch.object(
                workshop,
                "ask",
                side_effect=[result, workshop.WorkshopError("테스트 실패")],
            ),
        ):
            app = AppTest.from_file(str(REPOSITORY / "app.py")).run()
            app.text_area[0].input("첫 질문").run()
            app.button[0].click().run()
            app.text_area[0].input("둘째 질문").run()
            app.button[0].click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(any("테스트 실패" in item.value for item in app.error))
            self.assertFalse(
                any("오프라인 테스트 전용" in item.value for item in app.markdown)
            )

    def test_app_setup_error_is_visible_without_remote_request(self):
        with (
            patch.object(
                workshop,
                "load_settings",
                side_effect=workshop.WorkshopError("설정 필요"),
            ),
            patch.object(workshop, "ask") as ask,
        ):
            app = AppTest.from_file(str(REPOSITORY / "app.py")).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.error[0].value, "설정 필요")
        ask.assert_not_called()

    def test_compatibility_wrapper_only_overrides_explicit_model(self):
        with patch.object(sys, "path", [str(REPOSITORY / "scripts"), *sys.path]):
            bridge = importlib.import_module("v12")
        entrypoint, args, environment = bridge.command_arguments(
            [
                "--model-deployment",
                "approved-model",
                "model",
                "--question",
                "합성 질문",
            ]
        )
        self.assertEqual(entrypoint, "scripts/workshop.py")
        self.assertEqual(args, ["model", "--question", "합성 질문"])
        self.assertEqual(
            environment["AZURE_AI_MODEL_DEPLOYMENT_NAME"], "approved-model"
        )
        entrypoint, args, _ = bridge.command_arguments(["--script", "package-hosted"])
        self.assertEqual(entrypoint, "scripts/package_hosted.py")
        self.assertEqual(args, [])
        with self.assertRaises(RuntimeError):
            bridge.command_arguments(["--script", "../../arbitrary.py"])
        with self.assertRaises(RuntimeError):
            bridge.command_arguments(["--model-deployment"])

    def test_version_is_workshop_not_sdk(self):
        curriculum = json.loads((REPOSITORY / "curriculum.json").read_text())
        reference = json.loads((REPOSITORY / "v12-reference.json").read_text())
        self.assertEqual(curriculum["version"], "1.5")
        self.assertEqual(reference["source_version"], "1.2")
        self.assertEqual(workshop.WORKSHOP_VERSION, "1.5")
