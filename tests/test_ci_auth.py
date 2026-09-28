import contextlib
import io
import json
import os
import subprocess
import unittest
from unittest.mock import patch

from .test_packaging import load_script

AUTH = load_script("verify_ci_auth")
ENV = {
    "AZURE_CLIENT_ID": "00000000-0000-0000-0000-000000000001",
    "AZURE_TENANT_ID": "00000000-0000-0000-0000-000000000002",
    "AZURE_SUBSCRIPTION_ID": "00000000-0000-0000-0000-000000000003",
}


def account():
    return {
        "id": ENV["AZURE_SUBSCRIPTION_ID"],
        "tenantId": ENV["AZURE_TENANT_ID"],
        "user": {"name": ENV["AZURE_CLIENT_ID"], "type": "servicePrincipal"},
    }


class CIAuthenticationTests(unittest.TestCase):
    def test_configuration_requires_all_three_valid_identifiers(self):
        self.assertEqual(AUTH.configuration(ENV), ENV)
        for name in ENV:
            for value in ("", " ", "not-a-uuid"):
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    AUTH.configuration({**ENV, name: value})
            with self.subTest(missing=name), self.assertRaises(ValueError):
                AUTH.configuration({key: value for key, value in ENV.items() if key != name})

    def test_account_must_match_every_configured_identifier(self):
        expected = AUTH.configuration(ENV)
        for target, field in (("account", "id"), ("account", "tenantId"), ("user", "name")):
            for value in (None, "", "00000000-0000-0000-0000-000000000099"):
                actual = account()
                node = actual if target == "account" else actual["user"]
                node[field] = value
                with self.subTest(target=target, field=field, value=value):
                    with self.assertRaisesRegex(ValueError, "does not match"):
                        AUTH.verify_account(actual, expected)

    def test_user_login_and_malformed_accounts_are_rejected(self):
        user = account()
        user["user"]["type"] = "user"
        for actual in (None, [], {}, {"user": None}, {"user": []}, user):
            with self.subTest(actual=actual), self.assertRaises(ValueError):
                AUTH.verify_account(actual, ENV)

    def test_preflight_does_not_authenticate_or_call_azure(self):
        output = io.StringIO()
        with (
            patch.dict(os.environ, ENV, clear=True),
            patch.object(AUTH.subprocess, "run") as run,
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(AUTH.main(["--preflight"]), 0)
        run.assert_not_called()
        self.assertEqual(
            json.loads(output.getvalue()),
            {"status": "configured", "authentication_verified": False},
        )

    def test_verification_only_reads_account_metadata_and_never_exports_tokens(self):
        actual = {**account(), "accessToken": "must-not-be-exported"}
        process = subprocess.CompletedProcess([], 0, json.dumps(actual), "")
        output = io.StringIO()
        with (
            patch.dict(os.environ, ENV, clear=True),
            patch.object(AUTH.subprocess, "run", return_value=process) as run,
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(AUTH.main([]), 0)
        run.assert_called_once_with(
            ["az", "account", "show", "--output", "json", "--only-show-errors"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        result = json.loads(output.getvalue())
        self.assertEqual(result["status"], "authenticated")
        self.assertFalse(result["deployment_verified"])
        self.assertEqual(result["model_requests"], 0)
        self.assertNotIn("must-not-be-exported", output.getvalue())

    def test_cli_errors_and_invalid_json_fail_explicitly(self):
        for failure in (
            FileNotFoundError("az"),
            subprocess.TimeoutExpired(["az"], 30),
            subprocess.CalledProcessError(1, ["az"], stderr="Login required"),
        ):
            error = io.StringIO()
            with (
                self.subTest(failure=type(failure).__name__),
                patch.dict(os.environ, ENV, clear=True),
                patch.object(AUTH.subprocess, "run", side_effect=failure),
                contextlib.redirect_stderr(error),
            ):
                self.assertEqual(AUTH.main([]), 1)
            self.assertIn("ERROR: CI authentication verification failed:", error.getvalue())
        with (
            patch.dict(os.environ, ENV, clear=True),
            patch.object(
                AUTH.subprocess,
                "run",
                return_value=subprocess.CompletedProcess([], 0, "invalid-json", ""),
            ),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(AUTH.main([]), 1)
