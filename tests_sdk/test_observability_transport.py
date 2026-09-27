import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from azure.core.credentials import AccessToken

from foundry_workshop.observability import monitor_matrix

from .test_sdk_contracts import settings


class TraceCredential:
    def __init__(self):
        self.scopes = []

    def get_token(self, *scopes):
        self.scopes.extend(scopes)
        return AccessToken("unit-test-not-a-real-token", 4102444800)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass


class ObservabilityTransportTests(unittest.TestCase):
    def test_trace_query_uses_explicit_appinsights_audience_and_exact_application(self):
        credential = TraceCredential()
        requests = []
        app_id = "00000000-0000-0000-0000-000000000003"
        trace_id = "a" * 32
        manifest = {
            "runtime_contract": {"project_endpoint": settings().project_endpoint},
            "responses_hash": "unit-responses",
        }
        rows = [{"trace_id": trace_id}]

        def handle(request):
            requests.append(request)
            return httpx.Response(
                200,
                json={
                    "tables": [
                        {
                            "columns": [
                                {"name": key}
                                for key in (
                                    "trace_id",
                                    "matching_requests",
                                    "request_errors",
                                    "duration_ms",
                                )
                            ],
                            "rows": [[trace_id, 1, 0, 12.0]],
                        }
                    ]
                },
            )

        client = httpx.Client(transport=httpx.MockTransport(handle))
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary) / "outputs/benchmarks/unit"
            evidence.mkdir(parents=True)
            (evidence / "trace-query.kql").write_text("original incomplete query")
            (evidence / "trace-query-result.json").write_text('{"original_failed_attempt":true}')
            with (
                patch.dict(
                    os.environ,
                    {
                        "AZURE_SUBSCRIPTION_ID": "00000000-0000-0000-0000-000000000002",
                        "AZURE_APPLICATION_INSIGHTS_APP_ID": app_id,
                    },
                    clear=True,
                ),
                patch("foundry_workshop.benchmark.load_matrix", return_value=(manifest, rows, [])),
                patch("foundry_workshop.observability.Settings.from_env", return_value=settings()),
                patch(
                    "foundry_workshop.observability.write_trace_plan",
                    return_value={"query": "requests | take 1"},
                ),
                patch("foundry_workshop.observability.credential_for", return_value=credential),
                patch("httpx.Client", return_value=client),
            ):
                result = monitor_matrix(Path(temporary), "unit")
            archived = evidence / "trace-attempts/attempt-001"
            self.assertEqual(
                (archived / "trace-query.kql").read_text(), "original incomplete query"
            )
            self.assertTrue(
                json.loads((archived / "trace-query-result.json").read_text())[
                    "original_failed_attempt"
                ]
            )
        self.assertEqual(credential.scopes, ["https://api.applicationinsights.io/.default"])
        self.assertEqual(
            str(requests[0].url), f"https://api.applicationinsights.io/v1/apps/{app_id}/query"
        )
        self.assertEqual(json.loads(requests[0].content), {"query": "requests | take 1"})
        self.assertEqual(result["source"], "actual-scoped-application-insights-rest-query")
        self.assertEqual(result["verified_traces"], 1)
