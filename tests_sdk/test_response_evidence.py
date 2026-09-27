import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import httpx
from openai import BadRequestError

from foundry_workshop.cloud import response_with_payload


class ResponseEvidenceTests(unittest.TestCase):
    def test_http_error_keeps_original_body_without_retry(self):
        body = {"error": {"code": "unit_error", "message": "Synthetic diagnostic"}}
        error = BadRequestError(
            "Synthetic diagnostic",
            response=httpx.Response(
                400,
                json=body,
                headers={"x-request-id": "req-unit"},
                request=httpx.Request("POST", "https://unit.invalid/responses"),
            ),
            body=body,
        )
        client = MagicMock()
        client.responses.with_raw_response.create.side_effect = error
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "service-error.json"
            with self.assertRaisesRegex(ValueError, "HTTP 400"):
                response_with_payload(client, error_path=path, input="Synthetic input")
            result = json.loads(path.read_text())
        self.assertEqual(json.loads(result["response_body"]), body)
        self.assertEqual(result["request_id"], "req-unit")
        self.assertFalse(result["provider_fallback_used"])
        client.responses.with_raw_response.create.assert_called_once_with(input="Synthetic input")
