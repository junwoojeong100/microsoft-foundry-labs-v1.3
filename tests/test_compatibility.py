import re
import unittest
from datetime import date

from foundry_workshop import compatibility, hosted, iq_chat, search, toolbox
from foundry_workshop.contracts import openai_request_id

from . import ROOT


class CompatibilityRegistryTests(unittest.TestCase):
    def test_every_contract_is_dated_and_sourced(self):
        self.assertTrue(compatibility.CONTRACTS)
        for name, contract in compatibility.CONTRACTS.items():
            with self.subTest(contract=name):
                self.assertTrue(contract.version.strip())
                self.assertLessEqual(date.fromisoformat(contract.checked), date(2026, 9, 24))
                self.assertTrue(contract.source.startswith("https://learn.microsoft.com/"))
                self.assertTrue(contract.status.strip())

    def test_modules_use_the_registry_values(self):
        self.assertEqual(search.SEARCH_API, compatibility.SEARCH_REST.version)
        self.assertEqual(search.IQ_API, compatibility.FOUNDRY_IQ_GA.version)
        self.assertEqual(iq_chat.CHAT_API, compatibility.FOUNDRY_IQ_PREVIEW.version)
        self.assertIn("toolbox", toolbox.__name__)
        self.assertIn("hosted", hosted.__name__)

    def test_no_service_api_version_is_hard_coded_outside_the_registry(self):
        literal = re.compile(
            r"api-version=(?!\{)[\w.-]+"
            r"|[\"']api-version[\"']\s*[:,]\s*[\"'][\w.-]+[\"']"
            r"|\b[A-Z_]*API\s*=\s*[\"'][\w.-]+[\"']"
        )
        offenders = []
        for path in sorted((ROOT / "src/foundry_workshop").glob("*.py")):
            if path.name == "compatibility.py":
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if literal.search(line):
                    offenders.append(f"{path.name}:{number}: {line.strip()}")
        self.assertEqual(offenders, [])


class RequestIdTests(unittest.TestCase):
    def test_openai_request_id_reads_only_a_nonempty_string(self):
        class Parsed:
            _request_id = "req_unit"

        class Empty:
            _request_id = ""

        class NotString:
            _request_id = 42

        self.assertEqual(openai_request_id(Parsed()), "req_unit")
        self.assertIsNone(openai_request_id(Empty()))
        self.assertIsNone(openai_request_id(NotString()))
        self.assertIsNone(openai_request_id(object()))
