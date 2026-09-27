import copy
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from azure.core.exceptions import ResourceNotFoundError

from foundry_workshop import memory_lab
from foundry_workshop.contracts import read_json
from tests import workspace
from tests.test_memory_lab import ENVIRONMENT
from tests.test_toolbox import settings


class Value:
    def __init__(self, value):
        self.value = copy.deepcopy(value)
        for key, data in value.items():
            setattr(self, key, data)

    def as_dict(self):
        return copy.deepcopy(self.value)


class MemoryOperations:
    def __init__(self):
        self.store = None
        self.items = {}

    def get(self, name):
        if self.store is None or self.store["name"] != name:
            raise ResourceNotFoundError("Unit store absent")
        return Value(self.store)

    def create(self, **kwargs):
        self.store = {**kwargs, "definition": kwargs["definition"].as_dict()}
        return Value(self.store)

    def create_memory(self, name, scope, content, kind):
        value = {
            "memory_id": f"mem-{len(self.items) + 1}",
            "scope": scope,
            "content": content,
            "kind": kind,
        }
        self.items[value["memory_id"]] = value
        return Value(value)

    def get_memory(self, name, memory_id):
        if memory_id not in self.items:
            raise ResourceNotFoundError("Unit item absent")
        return Value(self.items[memory_id])

    def list_memories(self, name, scope):
        return [Value(item) for item in self.items.values() if item["scope"] == scope]

    def update_memory(self, name, memory_id, content):
        self.items[memory_id]["content"] = content
        return Value(self.items[memory_id])

    def delete_memory(self, name, memory_id):
        del self.items[memory_id]
        return Value({"memory_id": memory_id, "deleted": True})

    def delete(self, name):
        self.store = None
        return Value({"name": name, "deleted": True})

    def search_memories(self, name, scope, items):
        return Value(
            {
                "search_id": "unit-search",
                "memories": [
                    {"memory_item": item} for item in self.items.values() if item["scope"] == scope
                ],
                "usage": {"unit_fixture": True},
            }
        )


class MemorySDKTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, ENVIRONMENT, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        self.operations = MemoryOperations()
        self.project = MagicMock()
        self.project.agents.list.return_value = []
        self.project.beta.memory_stores = self.operations
        self.client = MagicMock()

        def respond(**kwargs):
            records = json.loads(kwargs["input"])["memories"]
            text = records[0]["content"] if records else "No memory is available."
            return SimpleNamespace(
                status="completed",
                output_text=text,
                id="resp-unit",
                model="unit-model",
                usage=SimpleNamespace(input_tokens=10, output_tokens=20),
                model_dump=lambda **_: {
                    "status": "completed",
                    "output_text": text,
                    "unit_fixture": True,
                },
            )

        self.client.responses.create.side_effect = respond

    def test_actual_option_serialization_and_complete_owned_item_lifecycle(self):
        with workspace() as root:
            created = memory_lab.create(self.project, root, settings(), confirmed=True)
            self.assertEqual(created["store"]["definition"]["options"]["default_ttl_seconds"], 3600)
            item = memory_lab.put(
                self.project,
                root,
                settings(),
                "alpha",
                "D02",
                confirmed_write=True,
                confirmed_cost=True,
            )
            memory_id = item["item"]["memory_id"]
            self.assertEqual(
                len(memory_lab.inspect_scope(self.project, root, settings(), "alpha")["items"]), 1
            )
            self.assertEqual(
                memory_lab.inspect_scope(self.project, root, settings(), "beta")["items"], []
            )
            alpha = memory_lab.recall(
                self.project, self.client, root, settings(), "alpha", "alpha", confirmed=True
            )
            beta = memory_lab.recall(
                self.project, self.client, root, settings(), "beta", "beta", confirmed=True
            )
            self.assertEqual(alpha["retrieved_memory_ids"], [memory_id])
            self.assertEqual(beta["retrieved_memory_ids"], [])
            self.assertFalse(alpha["native_agent_memory_tool_used"])
            updated = memory_lab.put(
                self.project,
                root,
                settings(),
                "alpha",
                "D01",
                confirmed_write=True,
                confirmed_cost=True,
                memory_id=memory_id,
            )
            self.assertNotEqual(updated["item"]["content"], item["item"]["content"])
            with self.assertRaisesRegex(ValueError, "Forget the owned items"):
                memory_lab.cleanup(self.project, root, settings(), confirmed=True)
            self.assertTrue(
                memory_lab.forget(self.project, root, settings(), memory_id, confirmed=True)[
                    "verified_absent"
                ]
            )
            self.assertTrue(
                memory_lab.cleanup(self.project, root, settings(), confirmed=True)[
                    "verified_absent"
                ]
            )
            self.assertTrue(
                memory_lab.ownership_path(root, settings()).with_name("cleanup.json").exists()
            )

    def test_search_scope_leak_is_rejected_before_model_call(self):
        with workspace() as root:
            memory_lab.create(self.project, root, settings(), confirmed=True)
            memory_lab.put(
                self.project,
                root,
                settings(),
                "alpha",
                "D02",
                confirmed_write=True,
                confirmed_cost=True,
            )
            original = self.operations.search_memories
            self.operations.search_memories = lambda **kwargs: original(
                **{**kwargs, "scope": memory_lab.scope_name(settings(), "alpha")}
            )
            with self.assertRaisesRegex(ValueError, "requested scope"):
                memory_lab.recall(
                    self.project, self.client, root, settings(), "beta", "leak", confirmed=True
                )
            self.client.responses.create.assert_not_called()
            self.assertTrue((root / "outputs/memory-runs/leak/search.json").exists())
            self.assertFalse((root / "outputs/memory-runs/leak/summary.json").exists())

    def test_wrong_owner_marker_does_not_delete_or_change_the_store(self):
        with workspace() as root:
            memory_lab.create(self.project, root, settings(), confirmed=True)
            path = memory_lab.ownership_path(root, settings())
            original = read_json(path)
            self.operations.store["metadata"]["workshop_owner"] = "another-owner"
            with self.assertRaisesRegex(ValueError, "ownership marker"):
                memory_lab.cleanup(self.project, root, settings(), confirmed=True)
            self.assertIsNotNone(self.operations.store)
            self.assertEqual(read_json(path), original)

    def test_already_absent_item_does_not_claim_a_new_delete(self):
        with workspace() as root:
            memory_lab.create(self.project, root, settings(), confirmed=True)
            item = memory_lab.put(
                self.project,
                root,
                settings(),
                "alpha",
                "D02",
                confirmed_write=True,
                confirmed_cost=True,
            )
            memory_id = item["item"]["memory_id"]
            del self.operations.items[memory_id]
            with patch.object(self.operations, "delete_memory") as delete:
                result = memory_lab.forget(
                    self.project, root, settings(), memory_id, confirmed=True
                )
            delete.assert_not_called()
            self.assertTrue(result["already_absent"])
            self.assertFalse(result["delete_requested"])
            self.assertTrue(result["verified_absent"])

    def test_eventual_deletion_is_read_back_without_another_delete(self):
        with workspace() as root:
            memory_lab.create(self.project, root, settings(), confirmed=True)
            item = memory_lab.put(
                self.project,
                root,
                settings(),
                "alpha",
                "D02",
                confirmed_write=True,
                confirmed_cost=True,
            )
            memory_id = item["item"]["memory_id"]
            with (
                patch.object(
                    self.operations,
                    "get_memory",
                    side_effect=[
                        Value(item["item"]),
                        Value(item["item"]),
                        ResourceNotFoundError("Deleted"),
                    ],
                ),
                patch("foundry_workshop.memory_lab.time.sleep") as sleep,
                patch.object(
                    self.operations, "delete_memory", wraps=self.operations.delete_memory
                ) as delete,
            ):
                result = memory_lab.forget(
                    self.project, root, settings(), memory_id, confirmed=True
                )
            self.assertTrue(result["verified_absent"])
            delete.assert_called_once()
            sleep.assert_called_once()

    def test_acknowledged_write_retries_only_readback(self):
        with workspace() as root:
            memory_lab.create(self.project, root, settings(), confirmed=True)
            original_get = self.operations.get_memory
            reads = 0

            def eventually_visible(name, memory_id):
                nonlocal reads
                reads += 1
                if reads == 1:
                    raise ResourceNotFoundError("Not visible yet")
                return original_get(name, memory_id)

            with (
                patch.object(self.operations, "get_memory", side_effect=eventually_visible),
                patch.object(
                    self.operations, "create_memory", wraps=self.operations.create_memory
                ) as create,
                patch("foundry_workshop.memory_lab.time.sleep") as sleep,
            ):
                result = memory_lab.put(
                    self.project,
                    root,
                    settings(),
                    "alpha",
                    "D02",
                    confirmed_write=True,
                    confirmed_cost=True,
                )
            self.assertEqual(result["item"]["scope"], memory_lab.scope_name(settings(), "alpha"))
            create.assert_called_once()
            sleep.assert_called_once()
