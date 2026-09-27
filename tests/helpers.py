from __future__ import annotations

import shutil
import tempfile
from contextlib import ExitStack
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import evaluation
import workshop

REPOSITORY = Path(__file__).resolve().parents[1]


class IsolatedWorkshop(TestCase):
    def setUp(self) -> None:
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(
            self.stack.enter_context(
                tempfile.TemporaryDirectory(prefix="foundry-v15-test-")
            )
        )
        shutil.copytree(REPOSITORY / "data", self.root / "data")
        shutil.copytree(REPOSITORY / "prompts", self.root / "prompts")
        self.stack.enter_context(patch.object(workshop, "ROOT", self.root))
        self.stack.enter_context(
            patch.object(workshop, "STATE_PATH", self.root / ".lab/state.json")
        )
        self.stack.enter_context(patch.object(evaluation, "ROOT", self.root))
        self.stack.enter_context(patch("evaluation.print", create=True))
        self.settings = workshop.Settings(
            "https://offline.services.ai.azure.com/api/projects/offline",
            "workshop-chat",
            "trip-coach-test",
        )
        self.state = workshop.State(
            self.settings.endpoint,
            self.settings.model,
            self.settings.agent_name,
            workshop.knowledge_hash(),
            vector_store_id="vs_test",
            files={"01-travel-current.txt": "file_test"},
            indexed_files=["01-travel-current.txt"],
            versions=[
                {
                    "version": "7",
                    "stage": "tools",
                    "prompt": "baseline",
                    "prompt_sha256": workshop.sha256(
                        self.root / "prompts/baseline.txt"
                    ),
                }
            ],
            selected_version="7",
        )
        self.state.save()


def message(text: str = "테스트 전용 답변", *, citation: bool = True) -> dict:
    annotations = (
        [
            {
                "type": "file_citation",
                "file_id": "file_test",
                "filename": "01-travel-current.txt",
                "index": 0,
            }
        ]
        if citation
        else []
    )
    return {
        "type": "message",
        "id": "msg_test",
        "role": "assistant",
        "status": "completed",
        "content": [{"type": "output_text", "text": text, "annotations": annotations}],
    }


def function_call(
    arguments: str = '{"city":"서울","nights":2}', name: str = "estimate_trip_cost"
) -> dict:
    return {
        "type": "function_call",
        "id": "fc_test",
        "call_id": "call_test",
        "status": "completed",
        "name": name,
        "arguments": arguments,
    }


def response_payload(
    response_id: str, output: list[dict], *, status: str = "completed"
) -> dict:
    return {
        "id": response_id,
        "object": "response",
        "created_at": 0,
        "status": status,
        "model": "workshop-chat",
        "output": output,
        "error": None,
        "incomplete_details": {"reason": "max_output_tokens"}
        if status == "incomplete"
        else None,
        "instructions": None,
        "metadata": {},
        "parallel_tool_calls": True,
        "tool_choice": "auto",
        "tools": [],
        "temperature": 1,
        "top_p": 1,
        "usage": {
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens_details": {"reasoning_tokens": 0},
        },
    }


def fixture_result(settings, query: str, path: Path, *, expected_version: str) -> dict:
    state = workshop.read_state(settings)
    result = {
        "workshop_version": workshop.WORKSHOP_VERSION,
        "status": "completed",
        "query": query,
        "answer": "오프라인 테스트 전용",
        "agent_name": state.agent_name,
        "agent_version": expected_version,
        "model": state.model,
        "prompt_sha256": state.selected()["prompt_sha256"],
        "knowledge_sha256": state.knowledge_sha256,
        "responses": [
            {
                "response_id": f"resp_test_{path.stem}",
                "status": "completed",
                "usage": None,
            }
        ],
        "tool_calls": [
            {
                "name": "estimate_trip_cost",
                "arguments": '{"city":"서울","nights":2}',
                "result": {"ok": True, "total": 390000},
            }
        ],
        "citations": [{"type": "file_citation", "file_id": "file_test"}],
        "latency_ms": 1,
        "output_file": str(path),
    }
    workshop.write_json(path, result)
    return result
