from __future__ import annotations

import hashlib
import json
import os
import re
import time
from contextlib import ExitStack, contextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit
from uuid import uuid4

from tools import ROOT, TOOL_SCHEMA, ToolInputError, execute_tool

if TYPE_CHECKING:
    from openai import OpenAI

STATE_PATH = ROOT / ".lab/state.json"
WORKSHOP_VERSION = json.loads((ROOT / "curriculum.json").read_text(encoding="utf-8"))[
    "version"
]
MAX_TOOL_ROUNDS = 3
MAX_TOOL_CALLS = 4


class WorkshopError(RuntimeError):
    pass


def now() -> str:
    return datetime.now(UTC).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def knowledge_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted((ROOT / "data/knowledge").glob("*.txt")) + [
        ROOT / "data/rates.json"
    ]:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def new_output_path(prefix: str = "ask") -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    return ROOT / "outputs" / f"{prefix}-{stamp}-{uuid4().hex[:8]}.json"


@contextmanager
def exclusive_session():
    lock = STATE_PATH.parent / "session.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = lock.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise WorkshopError(
            "같은 폴더의 다른 실습 작업이 실행 중입니다. 완료를 기다리세요. "
            "프로세스가 비정상 종료되었다면 docs/troubleshooting.md의 잠금 안내를 확인하세요."
        ) from exc
    try:
        with handle:
            handle.write(str(os.getpid()))
        yield
    finally:
        lock.unlink()


@dataclass(frozen=True)
class Settings:
    endpoint: str
    model: str
    agent_name: str

    def validate(self) -> None:
        parts = urlsplit(self.endpoint)
        host = parts.hostname or ""
        if (
            parts.scheme != "https"
            or not host.endswith(".ai.azure.com")
            or not re.fullmatch(r"/api/projects/[A-Za-z0-9._-]+", parts.path)
            or parts.query
            or parts.fragment
            or parts.username
            or parts.password
            or parts.port is not None
            or "YOUR" in self.endpoint.upper()
        ):
            raise WorkshopError(
                "프로젝트 Endpoint를 포털에서 복사해 .env에 넣으세요. 모델 Endpoint가 아닙니다."
            )
        if not self.model.strip() or "YOUR" in self.model.upper():
            raise WorkshopError(
                "FOUNDRY_MODEL_DEPLOYMENT_NAME에 실제 배포 이름을 입력하세요."
            )
        if not re.fullmatch(r"trip-coach-[a-z0-9][a-z0-9-]{1,40}", self.agent_name):
            raise WorkshopError(
                "agent 이름은 trip-coach-로 시작하는 고유한 영문 소문자/숫자/하이픈이어야 합니다."
            )
        if "yourname" in self.agent_name.lower():
            raise WorkshopError(
                "FOUNDRY_AGENT_NAME의 YOURNAME을 본인의 고유한 실습 ID로 바꾸세요."
            )


def load_settings() -> Settings:
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError as exc:
        raise WorkshopError(
            "먼저 python -m pip install -r requirements.txt를 실행하세요."
        ) from exc
    load_dotenv(ROOT / ".env", override=False)
    settings = Settings(
        endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "").rstrip("/"),
        model=os.environ.get("FOUNDRY_MODEL_DEPLOYMENT_NAME", ""),
        agent_name=os.environ.get("FOUNDRY_AGENT_NAME", ""),
    )
    settings.validate()
    return settings


@dataclass
class State:
    endpoint: str
    model: str
    agent_name: str
    knowledge_sha256: str
    vector_store_id: str = ""
    files: dict[str, str] = field(default_factory=dict)
    indexed_files: list[str] = field(default_factory=list)
    versions: list[dict[str, str]] = field(default_factory=list)
    selected_version: str = ""
    response_ids: list[str] = field(default_factory=list)

    def save(self) -> None:
        write_json(STATE_PATH, asdict(self))

    def selected(self) -> dict[str, str]:
        for version in self.versions:
            if version["version"] == self.selected_version:
                return version
        raise WorkshopError(
            "저장된 에이전트 버전이 없습니다. Lab 03의 create를 먼저 실행하세요."
        )


def read_state(settings: Settings, *, check_knowledge: bool = True) -> State:
    if not STATE_PATH.exists():
        raise WorkshopError(
            ".lab/state.json이 없습니다. Lab 03의 create를 먼저 실행하세요."
        )
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != set(State.__dataclass_fields__):
        raise WorkshopError(
            "실습 상태 파일의 형식이 잘못되었습니다. 삭제하지 말고 강사에게 확인하세요."
        )
    for key in (
        "endpoint",
        "model",
        "agent_name",
        "knowledge_sha256",
        "vector_store_id",
        "selected_version",
    ):
        if not isinstance(data[key], str):
            raise WorkshopError(f"실습 상태 필드 오류: {key}")
    if not isinstance(data["files"], dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in data["files"].items()
    ):
        raise WorkshopError("실습 상태의 파일 목록이 잘못되었습니다.")
    for key in ("indexed_files", "response_ids"):
        if not isinstance(data[key], list) or not all(
            isinstance(v, str) for v in data[key]
        ):
            raise WorkshopError(f"실습 상태 필드 오류: {key}")
    if not isinstance(data["versions"], list) or not all(
        isinstance(v, dict)
        and set(v) == {"version", "stage", "prompt", "prompt_sha256"}
        and all(isinstance(value, str) for value in v.values())
        and v["stage"] in {"rag", "tools"}
        for v in data["versions"]
    ):
        raise WorkshopError("실습 상태의 버전 목록이 잘못되었습니다.")
    state = State(**data)
    if (state.endpoint, state.model, state.agent_name) != (
        settings.endpoint,
        settings.model,
        settings.agent_name,
    ):
        raise WorkshopError(
            ".env와 기존 실습 상태의 프로젝트/모델/agent가 다릅니다. 원래 설정으로 복원하세요."
        )
    if check_knowledge and state.knowledge_sha256 != knowledge_hash():
        raise WorkshopError(
            "업로드 후 정책/요금 파일이 바뀌었습니다. 기존 지식과 섞지 말고 강사에게 확인하세요."
        )
    return state


@contextmanager
def cloud_clients(settings: Settings):
    try:
        from azure.ai.projects import AIProjectClient
        from azure.core.exceptions import AzureError
        from azure.identity import AzureCliCredential
        from openai import APIError
    except ModuleNotFoundError as exc:
        raise WorkshopError(
            "먼저 python -m pip install -r requirements.txt를 실행하세요."
        ) from exc
    try:
        with ExitStack() as stack:
            credential = stack.enter_context(AzureCliCredential())
            project = stack.enter_context(
                AIProjectClient(endpoint=settings.endpoint, credential=credential)
            )
            client = stack.enter_context(
                project.get_openai_client(timeout=90.0, max_retries=1)
            )
            yield project, client
    except (AzureError, APIError) as exc:
        raise WorkshopError(
            f"{type(exc).__name__}: {exc}\n해결: docs/troubleshooting.md"
        ) from exc


def prepare_knowledge(client: OpenAI, state: State) -> None:
    from openai import NotFoundError

    if not state.vector_store_id:
        store = client.vector_stores.create(
            name=f"{state.agent_name}-knowledge",
            expires_after={"anchor": "last_active_at", "days": 1},
        )
        state.vector_store_id = store.id
        state.save()
    for path in sorted((ROOT / "data/knowledge").glob("*.txt")):
        if path.name not in state.files:
            with path.open("rb") as handle:
                uploaded = client.files.create(file=handle, purpose="assistants")
            state.files[path.name] = uploaded.id
            state.save()
        file_id = state.files[path.name]
        try:
            item = client.vector_stores.files.retrieve(
                file_id, vector_store_id=state.vector_store_id
            )
        except NotFoundError:
            item = client.vector_stores.files.create(
                vector_store_id=state.vector_store_id, file_id=file_id
            )
        deadline = time.monotonic() + 120
        while item.status == "in_progress":
            if time.monotonic() >= deadline:
                raise WorkshopError(
                    f"{path.name} 인덱싱 시간 초과. 상태를 보존했습니다. 완료 후 create를 재시도하세요."
                )
            time.sleep(2)
            item = client.vector_stores.files.retrieve(
                file_id, vector_store_id=state.vector_store_id
            )
        if item.status != "completed":
            raise WorkshopError(
                f"{path.name} 인덱싱 실패: {item.status}, {item.last_error}"
            )
        if path.name not in state.indexed_files:
            state.indexed_files.append(path.name)
            state.save()


def create_agent(settings: Settings, stage: str, prompt: str) -> State:
    from azure.ai.projects.models import (
        FileSearchTool,
        FunctionTool,
        PromptAgentDefinition,
        Tool,
    )
    from azure.core.exceptions import ResourceNotFoundError

    if stage not in {"rag", "tools"} or prompt not in {"baseline", "improved"}:
        raise WorkshopError("지원하지 않는 stage 또는 prompt입니다.")
    path = ROOT / "prompts" / f"{prompt}.txt"
    instructions = path.read_text(encoding="utf-8")
    with cloud_clients(settings) as (project, client):
        if STATE_PATH.exists():
            state = read_state(settings)
        else:
            try:
                project.agents.get(agent_name=settings.agent_name)
            except ResourceNotFoundError:
                state = State(
                    settings.endpoint,
                    settings.model,
                    settings.agent_name,
                    knowledge_hash(),
                )
                state.save()
            else:
                raise WorkshopError(
                    "같은 이름의 agent가 이미 있습니다. 기존 agent를 바꾸지 말고 고유한 이름을 쓰세요."
                )
        prepare_knowledge(client, state)
        tools: list[Tool] = [
            FileSearchTool(vector_store_ids=[state.vector_store_id], max_num_results=5)
        ]
        if stage == "tools":
            tools.append(FunctionTool(**TOOL_SCHEMA))
        agent = project.agents.create_version(
            agent_name=settings.agent_name,
            definition=PromptAgentDefinition(
                model=settings.model, instructions=instructions, tools=tools
            ),
            description="Synthetic travel workshop. Read-only guidance; no approvals or payments.",
        )
        state.versions.append(
            {
                "version": agent.version,
                "stage": stage,
                "prompt": prompt,
                "prompt_sha256": sha256(path),
            }
        )
        state.selected_version = agent.version
        state.save()
    return state


def select_version(settings: Settings, version: str) -> State:
    state = read_state(settings)
    if version not in {item["version"] for item in state.versions}:
        raise WorkshopError("이 실습에서 생성·기록한 버전만 선택할 수 있습니다.")
    state.selected_version = version
    state.save()
    return state


def response_details(response) -> dict[str, object]:
    return {
        "response_id": response.id,
        "status": response.status,
        "usage": response.usage.model_dump() if response.usage else None,
        "output": [item.model_dump(mode="json") for item in response.output],
    }


def file_citations(response) -> list[dict[str, object]]:
    citations = []
    for item in response.output:
        if item.type == "message":
            for content in item.content:
                if content.type == "output_text":
                    for annotation in content.annotations:
                        if annotation.type == "file_citation":
                            citations.append(annotation.model_dump(mode="json"))
    return citations


def ask(
    settings: Settings,
    query: str,
    output_path: Path | None = None,
    *,
    expected_version: str | None = None,
) -> dict[str, object]:
    from openai.types.responses import ResponseInputParam

    if not query.strip() or len(query) > 4000:
        raise WorkshopError("질문은 1~4000자여야 합니다.")
    state = read_state(settings)
    selected = state.selected()
    if expected_version and state.selected_version != expected_version:
        raise WorkshopError(
            "평가 중 선택 버전이 바뀌었습니다. 버전을 섞지 않고 중단합니다."
        )
    path = output_path or new_output_path()
    if path.exists():
        raise WorkshopError(f"실행 기록을 덮어쓰지 않습니다: {path}")
    record = {
        "workshop_version": WORKSHOP_VERSION,
        "status": "error",
        "started_at": now(),
        "query": query,
        "agent_name": state.agent_name,
        "agent_version": state.selected_version,
        "model": state.model,
        "prompt_sha256": selected["prompt_sha256"],
        "knowledge_sha256": state.knowledge_sha256,
        "responses": [],
        "tool_calls": [],
        "citations": [],
        "answer": "",
        "output_file": str(path.relative_to(ROOT))
        if path.is_relative_to(ROOT)
        else str(path),
    }
    started = time.monotonic()
    reference = {
        "name": state.agent_name,
        "version": state.selected_version,
        "type": "agent_reference",
    }
    try:
        with cloud_clients(settings) as (_, client):
            next_input: str | ResponseInputParam = query
            previous_id: str | None = None
            for round_index in range(MAX_TOOL_ROUNDS + 1):
                followup = {"previous_response_id": previous_id} if previous_id else {}
                response = client.responses.create(
                    input=next_input,
                    extra_body={"agent_reference": reference},
                    include=["file_search_call.results"],
                    max_output_tokens=4096,
                    **followup,
                )
                state.response_ids.append(response.id)
                state.save()
                record["responses"].append(response_details(response))
                if response.status != "completed":
                    raise WorkshopError(
                        f"응답이 완료되지 않았습니다: {response.status}. 기록을 확인하세요."
                    )
                calls = [
                    item for item in response.output if item.type == "function_call"
                ]
                if not calls:
                    if not response.output_text.strip():
                        raise WorkshopError(
                            "답변 텍스트가 비어 있습니다. refusal/출력 토큰 한도 등 기록을 확인하세요."
                        )
                    record["answer"] = response.output_text
                    record["citations"] = file_citations(response)
                    record["status"] = "completed"
                    break
                if (
                    round_index == MAX_TOOL_ROUNDS
                    or len(record["tool_calls"]) + len(calls) > MAX_TOOL_CALLS
                ):
                    raise WorkshopError(
                        "도구 호출 상한에 도달했습니다. 반복 호출을 중단하고 기록을 보존합니다."
                    )
                if selected["stage"] != "tools":
                    raise WorkshopError(
                        "이 에이전트 버전에서는 로컬 함수 실행을 허용하지 않습니다."
                    )
                outputs: ResponseInputParam = []
                for call in calls:
                    try:
                        result = execute_tool(call.name, call.arguments)
                    except ToolInputError as exc:
                        result = {
                            "ok": False,
                            "error": {
                                "code": "invalid_tool_input",
                                "message": str(exc),
                            },
                        }
                    record["tool_calls"].append(
                        {
                            "name": call.name,
                            "arguments": call.arguments,
                            "result": result,
                        }
                    )
                    outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": json.dumps(result, ensure_ascii=False),
                        }
                    )
                next_input = outputs
                previous_id = response.id
    except WorkshopError as exc:
        record["error"] = str(exc)
        raise
    finally:
        record["latency_ms"] = round((time.monotonic() - started) * 1000)
        write_json(path, record)
    return record


def ask_model(settings: Settings, query: str) -> dict[str, object]:
    if not query.strip() or len(query) > 4000:
        raise WorkshopError("질문은 1~4000자여야 합니다.")
    with cloud_clients(settings) as (_, client):
        response = client.responses.create(
            model=settings.model, input=query, max_output_tokens=4096, store=False
        )
        if response.status != "completed" or not response.output_text.strip():
            raise WorkshopError(
                f"모델 응답이 완료되지 않았거나 비어 있습니다: {response.status}"
            )
        return {"answer": response.output_text, **response_details(response)}


def cleanup(settings: Settings, confirm: str | None) -> State:
    from azure.core.exceptions import ResourceNotFoundError
    from openai import NotFoundError

    state = read_state(settings, check_knowledge=False)
    if confirm is None:
        return state
    if confirm != state.agent_name:
        raise WorkshopError(
            "--confirm은 상태 파일에 기록된 agent 이름과 정확히 같아야 합니다."
        )
    with cloud_clients(settings) as (project, client):
        for response_id in list(state.response_ids):
            try:
                deleted = client.responses.delete(response_id)
                if not deleted.deleted:
                    raise WorkshopError(
                        f"응답 삭제가 확인되지 않았습니다: {response_id}"
                    )
            except NotFoundError:
                print(f"이미 없는 응답: {response_id}")
            state.response_ids.remove(response_id)
            state.save()
        for version in list(reversed(state.versions)):
            try:
                project.agents.delete_version(
                    agent_name=state.agent_name, agent_version=version["version"]
                )
            except ResourceNotFoundError:
                print(f"이미 없는 버전: {version['version']}")
            state.versions.remove(version)
            state.selected_version = ""
            state.save()
        if state.vector_store_id:
            try:
                deleted = client.vector_stores.delete(state.vector_store_id)
                if not deleted.deleted:
                    raise WorkshopError(
                        f"벡터 저장소 삭제가 확인되지 않았습니다: {state.vector_store_id}"
                    )
            except NotFoundError:
                print(f"이미 없는 벡터 저장소: {state.vector_store_id}")
            state.vector_store_id = ""
            state.indexed_files.clear()
            state.save()
        for filename, file_id in list(state.files.items()):
            try:
                deleted = client.files.delete(file_id)
                if not deleted.deleted:
                    raise WorkshopError(
                        f"업로드 파일 삭제가 확인되지 않았습니다: {file_id}"
                    )
            except NotFoundError:
                print(f"이미 없는 업로드 파일: {file_id}")
            del state.files[filename]
            state.save()
    return state
