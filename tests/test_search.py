import os
import unittest
from dataclasses import replace
from unittest.mock import Mock, patch

from foundry_workshop.contracts import digest, load_documents, read_json, write_json
from foundry_workshop.search import IQ_API, SEARCH_API, SearchGateway, search_configuration
from foundry_workshop.settings import Settings

from . import ROOT, workspace


class Reply:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise ValueError(f"Unit-test HTTP {self.status_code}")


class SearchContractTests(unittest.TestCase):
    def test_explicit_iq_threshold_is_sent_without_changing_provider_or_question(self):
        requests = []

        def handle(method, path, **kwargs):
            requests.append((method, path, kwargs))
            return Reply({"references": [], "activity": []})

        gateway = self.gateway(handle)
        gateway.configuration["iq_reranker_threshold"] = 0.0
        value = gateway.retrieve("English dev recall question", "iq")
        body = requests[0][2]["body"]
        self.assertEqual(
            body["intents"], [{"type": "semantic", "search": "English dev recall question"}]
        )
        self.assertEqual(body["knowledgeSourceParams"][0]["rerankerThreshold"], 0.0)
        self.assertEqual(value["provider"], "foundry-iq")
        self.assertEqual(value["configuration"]["iq_reranker_threshold"], 0.0)

    def test_iq_threshold_rejects_nonfinite_and_out_of_range_values(self):
        for value in ("nan", "inf", "-1", "4.1", "not-a-number"):
            with patch.dict(
                os.environ,
                {
                    "AZURE_SEARCH_ENDPOINT": "https://unit.search.windows.net",
                    "WORKSHOP_PREFIX": "lab-unit",
                    "WORKSHOP_IQ_RERANKER_THRESHOLD": value,
                },
                clear=True,
            ):
                with self.assertRaises(ValueError):
                    search_configuration()

    def gateway(self, handler):
        gateway = object.__new__(SearchGateway)
        gateway.endpoint = "https://unit.search.windows.net"
        gateway.index = "lab-unit-policies"
        gateway.source = "lab-unit-source"
        gateway.kb = "lab-unit-kb"
        gateway.configuration = {"endpoint": gateway.endpoint, "index": gateway.index}
        gateway.settings = Settings(
            "https://unit.services.ai.azure.com/api/projects/workshop",
            "unit-model",
            None,
            "cli",
            None,
            2048,
        )
        gateway.request = handler
        return gateway

    def test_ga_retrieval_uses_intents_and_preserves_evidence(self):
        requests = []

        def handle(method, path, **kwargs):
            requests.append((method, path, kwargs))
            return Reply(
                {
                    "references": [
                        {"id": "0", "docKey": "TRAVEL-2026", "sourceData": load_documents(ROOT)[1]}
                    ],
                    "activity": [{"type": "searchIndex", "count": 1}],
                }
            )

        result = self.gateway(handle).retrieve("2026년 국내 출장 숙박비", "iq")
        _, path, parameters = requests[0]
        self.assertEqual(path, "knowledgebases('lab-unit-kb')/retrieve")
        self.assertEqual(parameters["api"], "2026-04-01")
        self.assertIn("intents", parameters["body"])
        self.assertNotIn("messages", parameters["body"])
        self.assertGreater(parameters["body"]["maxOutputSizeInTokens"], 5000)
        self.assertNotIn("retrievalReasoningEffort", parameters["body"])
        self.assertEqual(result["source_ids"], ["TRAVEL-2026"])
        self.assertEqual(result["references"][0]["id"], "0")
        self.assertEqual(result["provider"], "foundry-iq")

    def test_missing_or_failed_activity_does_not_become_success(self):
        for payload in (
            {"references": []},
            {"references": [], "activity": [{"error": {"message": "failed"}}]},
            {"references": [{"id": "0"}], "activity": []},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.gateway(lambda *_args, _payload=payload, **_kwargs: Reply(_payload)).retrieve(
                    "질문", "iq"
                )

    def test_iq_fetches_actual_document_key_not_reference_number(self):
        requested = []

        def handle(method, path, **_kwargs):
            requested.append(path)
            if method == "POST":
                return Reply({"references": [{"id": "0", "docKey": "TRAVEL-2026"}], "activity": []})
            return Reply(load_documents(ROOT)[1])

        result = self.gateway(handle).retrieve("질문", "iq")
        self.assertEqual(requested[1], "indexes/lab-unit-policies/docs/TRAVEL-2026")
        self.assertEqual(result["source_ids"], ["TRAVEL-2026"])

    def test_seed_is_create_only_and_has_no_preview_planner(self):
        requests = []

        def handle(method, path, **kwargs):
            requests.append((method, path, kwargs))
            if method == "GET":
                return Reply({}, 404)
            if method == "POST":
                return Reply(
                    {
                        "value": [
                            {"key": document["id"], "status": True}
                            for document in load_documents(ROOT)
                        ]
                    }
                )
            return Reply({}, 201)

        with (
            workspace() as root,
            patch.dict(os.environ, {"WORKSHOP_PREFIX": "lab-unit"}, clear=True),
        ):
            self.gateway(handle).seed(root, include_iq=True, confirmed=True)
            puts = [item for item in requests if item[0] == "PUT"]
            self.assertEqual(len(puts), 3)
            self.assertTrue(all(item[2]["create_only"] for item in puts))
            self.assertEqual(puts[0][2]["api"], SEARCH_API)
            self.assertEqual(puts[2][2]["api"], IQ_API)
            self.assertEqual(
                puts[0][2]["body"]["semantic"]["defaultConfiguration"], "policy-semantic"
            )
            base = puts[2][2]["body"]
            self.assertNotIn("models", base)
            self.assertNotIn("outputMode", base)
            self.assertNotIn("retrievalReasoningEffort", base)
            self.assertEqual(len(read_json(root / "outputs/azure-objects.json")["objects"]), 3)

    def test_seed_never_overwrites_unowned_existing_index(self):
        writes = []

        def handle(method, _path, **_kwargs):
            if method != "GET":
                writes.append(method)
            return Reply({})

        with (
            workspace() as root,
            patch.dict(os.environ, {"WORKSHOP_PREFIX": "lab-unit"}, clear=True),
        ):
            with self.assertRaises(ValueError):
                self.gateway(handle).seed(root, include_iq=False, confirmed=True)
        self.assertEqual(writes, [])

    def test_seed_requires_confirmation_before_network(self):
        calls = []
        gateway = self.gateway(lambda *args, **kwargs: calls.append((args, kwargs)))
        with workspace() as root, self.assertRaises(ValueError):
            gateway.seed(root, include_iq=True, confirmed=False)
        self.assertEqual(calls, [])

    def test_language_or_prefix_changes_cannot_reuse_the_previous_ownership_ledger(self):
        with (
            workspace() as root,
            patch.dict(os.environ, {"WORKSHOP_PREFIX": "lab-unit"}, clear=True),
        ):
            request = Mock(side_effect=AssertionError("This guard must run before network access."))
            gateway = self.gateway(request)
            ledger_path = root / "outputs/azure-objects.json"
            write_json(
                ledger_path,
                {
                    "scope": {"search_endpoint": gateway.endpoint, "prefix": "lab-unit"},
                    "corpus_hash": digest(load_documents(root, "ko")),
                    "objects": [],
                },
            )
            original = ledger_path.read_bytes()
            for language, prefix in (("en", "lab-unit"), ("ko", "lab-new")):
                with self.subTest(language=language, prefix=prefix):
                    gateway.settings = replace(gateway.settings, language=language)
                    os.environ["WORKSHOP_PREFIX"] = prefix
                    gateway.index, gateway.source, gateway.kb = [
                        f"{prefix}-{suffix}" for suffix in ("policies", "source", "kb")
                    ]
                    with self.assertRaisesRegex(ValueError, "fresh workshop copy"):
                        gateway.seed(root, include_iq=True, confirmed=True)
                    self.assertEqual(ledger_path.read_bytes(), original)
            request.assert_not_called()

    def test_partial_upload_is_failure_with_ownership_retained(self):
        def handle(method, _path, **_kwargs):
            if method == "GET":
                return Reply({}, 404)
            if method == "POST":
                return Reply({"value": [{"key": "TRAVEL-2025", "status": True}]})
            return Reply({}, 201)

        with (
            workspace() as root,
            patch.dict(os.environ, {"WORKSHOP_PREFIX": "lab-unit"}, clear=True),
        ):
            with self.assertRaises(ValueError):
                self.gateway(handle).seed(root, include_iq=False, confirmed=True)
            self.assertEqual(len(read_json(root / "outputs/azure-objects.json")["objects"]), 1)

    def test_hybrid_query_contains_both_text_and_actual_vector(self):
        requests = []
        gateway = self.gateway(
            lambda method, path, **kwargs: (
                requests.append((method, path, kwargs))
                or Reply({"value": [load_documents(ROOT)[1]]})
            )
        )
        configuration = {
            "deployment": "unit-embedding",
            "dimensions": 3,
            "field": "content_vector",
            "api": "project-embeddings",
        }
        with patch("foundry_workshop.search.embedding_configuration", return_value=configuration):
            with patch(
                "foundry_workshop.search.embed_texts",
                return_value=([[0.1, 0.2, 0.3]], {"observed_model": "unit-embedding-model"}),
            ):
                result = gateway.retrieve("합성 숙박 규정", "hybrid")
        body = requests[0][2]["body"]
        self.assertEqual(body["search"], "합성 숙박 규정")
        self.assertEqual(body["vectorQueries"][0]["vector"], [0.1, 0.2, 0.3])
        self.assertEqual(body["vectorQueries"][0]["fields"], "content_vector")
        self.assertEqual(result["provider"], "azure-ai-search-hybrid")
        self.assertEqual(result["embedding_query"]["observed_model"], "unit-embedding-model")

    def test_hybrid_seed_uses_real_embedding_shape_for_all_six_documents(self):
        requests = []

        def handle(method, path, **kwargs):
            requests.append((method, path, kwargs))
            if method == "GET":
                return Reply({}, 404)
            if method == "POST":
                return Reply(
                    {
                        "value": [
                            {"key": document["id"], "status": True}
                            for document in load_documents(ROOT)
                        ]
                    }
                )
            return Reply({}, 201)

        gateway = self.gateway(handle)
        configuration = {
            "deployment": "unit-embedding",
            "dimensions": 3,
            "field": "content_vector",
            "api": "project-embeddings",
        }
        with (
            workspace() as root,
            patch.dict(os.environ, {"WORKSHOP_PREFIX": "lab-unit"}, clear=True),
        ):
            with patch(
                "foundry_workshop.search.embedding_configuration", return_value=configuration
            ):
                with patch(
                    "foundry_workshop.search.embed_texts",
                    return_value=(
                        [[0.1, 0.2, 0.3] for _ in range(6)],
                        {"observed_model": "unit-embedding-model"},
                    ),
                ) as embed:
                    result = gateway.seed(
                        root,
                        include_iq=False,
                        confirmed=True,
                        hybrid=True,
                        confirm_embedding_cost=True,
                    )
            self.assertTrue(result["hybrid"])
            self.assertEqual(len(embed.call_args.args[1]), 6)
            definition = next(item[2]["body"] for item in requests if item[0] == "PUT")
            vector = next(
                field for field in definition["fields"] if field["name"] == "content_vector"
            )
            self.assertEqual(vector["dimensions"], 3)
            self.assertEqual(vector["vectorSearchProfile"], "policy-vector")
            upload = next(item[2]["body"] for item in requests if item[0] == "POST")
            self.assertEqual(len(upload["value"]), 6)
            self.assertTrue(
                all(item["content_vector"] == [0.1, 0.2, 0.3] for item in upload["value"])
            )
            self.assertIn(
                gateway.index,
                read_json(root / "outputs/azure-objects.json")["index_configurations"],
            )

    def test_hybrid_seed_requires_cost_approval_and_does_not_silently_convert_owned_text_index(
        self,
    ):
        calls = []
        gateway = self.gateway(lambda *args, **kwargs: calls.append((args, kwargs)) or Reply({}))
        with workspace() as root, self.assertRaises(ValueError):
            gateway.seed(
                root, include_iq=False, confirmed=True, hybrid=True, confirm_embedding_cost=False
            )
        self.assertEqual(calls, [])
        with (
            workspace() as root,
            patch.dict(os.environ, {"WORKSHOP_PREFIX": "lab-unit"}, clear=True),
        ):
            from foundry_workshop.contracts import digest, write_json

            write_json(
                root / "outputs/azure-objects.json",
                {
                    "scope": {"search_endpoint": gateway.endpoint, "prefix": "lab-unit"},
                    "corpus_hash": digest(load_documents(root)),
                    "objects": [{"path": f"indexes/{gateway.index}", "api_version": SEARCH_API}],
                },
            )
            with (
                patch(
                    "foundry_workshop.search.embedding_configuration",
                    return_value={
                        "deployment": "unit-embedding",
                        "dimensions": 3,
                        "field": "content_vector",
                        "api": "project-embeddings",
                    },
                ),
                patch("foundry_workshop.search.embed_texts") as embed,
            ):
                with self.assertRaises(ValueError):
                    gateway.seed(
                        root,
                        include_iq=False,
                        confirmed=True,
                        hybrid=True,
                        confirm_embedding_cost=True,
                    )
            embed.assert_not_called()
            self.assertTrue(all(call[0][0] == "GET" for call in calls))


if __name__ == "__main__":
    unittest.main()
