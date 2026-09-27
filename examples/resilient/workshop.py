#!/usr/bin/env python3
"""Bounded loopback-only runner/client for the AgentServer resilience module."""

import argparse
import fcntl
import importlib.metadata
import json
import logging
import os
import platform
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from foundry_workshop.contracts import read_json, safe_label  # noqa: E402
from foundry_workshop.resilience import (  # noqa: E402
    MODE,
    MODEL_LABEL,
    response_id,
    verify_completion,
)

OWNER = "workshop-resilience-v1"
PINNED = {"azure-ai-agentserver-core": "2.1.0", "azure-ai-agentserver-responses": "2.2.0b1"}
EVIDENCE_FILES = {
    "owner.json",
    "server.lock",
    "client.json",
    "initial-response.json",
    "completed-response.json",
    "checkpoint.json",
    "crash-checkpoint.json",
    "crash-once.json",
    "cleanup.json",
}


def evidence_json_default(value):
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.isoformat()
    raise TypeError(f"Unsupported checkpoint evidence value: {type(value).__name__}")


def write_json(path: Path, value: dict) -> None:
    if path.is_symlink():
        raise ValueError("Evidence files must not be symlinks.")
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        try:
            json.dump(value, handle, indent=2, allow_nan=False, default=evidence_json_default)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def run_directory(root: Path, label: str) -> Path:
    path = root / "outputs" / "resilience" / safe_label(label)
    for candidate in (root / "outputs", path.parent, path):
        if candidate.is_symlink():
            raise ValueError("The dedicated run path must not traverse a symlink.")
    if path.exists() and any(candidate.is_symlink() for candidate in path.rglob("*")):
        raise ValueError("The owned run directory must not contain symlinks.")
    return path


def run_marker(label: str, language: str = "en") -> dict:
    if language not in {"en", "ko"}:
        raise ValueError("Use en or ko explicitly.")
    return {"owner": OWNER, "run_id": label, **({"language": language} if language != "en" else {})}


@contextmanager
def owned_run(root: Path, label: str, *, create: bool = False, language: str = "en"):
    path = run_directory(root, label)
    marker = run_marker(label, language)
    if create:
        path.mkdir(parents=True, exist_ok=True)
        if not (path / "owner.json").exists():
            if any(path.iterdir()):
                raise ValueError(
                    "Refusing to adopt a nonempty directory without this module's marker."
                )
            with (path / "owner.json").open("x", encoding="utf-8") as handle:
                json.dump(marker, handle)
    if read_json(path / "owner.json") != marker:
        raise ValueError("Run ownership marker does not match; refusing to modify it.")
    if (path / "server.lock").is_symlink():
        raise ValueError("Refusing a symlinked process lock.")
    with (path / "server.lock").open("a", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError(
                "This run has an active owned server; stop that server first."
            ) from exc
        try:
            yield path
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def cleanup(root: Path, label: str, *, confirmed: bool, language: str = "en") -> dict:
    if not confirmed:
        raise ValueError("Cleanup requires --confirm-delete-local-state.")
    with owned_run(root, label, language=language) as directory:
        paths = list(directory.rglob("*"))
        if any(path.is_symlink() for path in paths):
            raise ValueError("Refusing cleanup because the owned directory contains a symlink.")
        unknown = [
            path.name
            for path in directory.iterdir()
            if path.name not in EVIDENCE_FILES and path.name != "sdk-state"
        ]
        if unknown:
            raise ValueError("Refusing to delete unrecognized files: " + ", ".join(unknown))
        sdk_state = directory / "sdk-state"
        state_paths = list(sdk_state.rglob("*")) if sdk_state.is_dir() else []
        for path in sorted(state_paths, key=lambda item: len(item.parts), reverse=True):
            if path.is_dir():
                path.rmdir()
            else:
                path.unlink()
        if sdk_state.exists():
            sdk_state.rmdir()
        result = {
            "deleted_local_sdk_state": str(sdk_state),
            "retained_evidence": sorted(
                path.name for path in directory.iterdir() if path.is_file()
            ),
            "azure_resources_changed": False,
        }
        write_json(directory / "cleanup.json", result)
    return result


def check_sdks() -> dict:
    versions = {name: importlib.metadata.version(name) for name in PINNED}
    if versions != PINNED:
        raise ValueError(f"SDK contract mismatch: expected {PINNED}, installed {versions}.")
    return {"mode": MODE, "installed": versions, "azure_requests_sent": False}


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("The local exercise refuses HTTP redirects.")


def request(port: int, method: str, path: str, value=None, *, allow_missing: bool = False):
    opener = build_opener(ProxyHandler({}), NoRedirects())
    body = None if value is None else json.dumps(value).encode("utf-8")
    query = Request(
        f"http://127.0.0.1:{port}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with opener.open(query, timeout=10) as reply:
            return json.load(reply)
    except HTTPError as exc:
        if allow_missing and exc.code == 404:
            return None
        raise ValueError(f"Local HTTP {exc.code}: {exc.read(4000).decode('utf-8')}") from exc
    except URLError as exc:
        raise ValueError(
            f"Local server unavailable; no remote or fixture fallback: {exc.reason}"
        ) from exc


def pointer(directory: Path, port: int) -> dict:
    value = read_json(directory / "client.json")
    if value.get("port") != port or value.get("mode") != MODE:
        raise ValueError("Client state does not match this local run and port.")
    response_id(value.get("response_id"))
    return value


def verify_server(directory: Path, port: int) -> None:
    actual = request(port, "GET", "/workshop/identity")
    if actual != {"mode": MODE, "agent_name": OWNER, "run_id": directory.name}:
        raise ValueError("The port is not serving this owned workshop run; refusing to send input.")


def state(directory: Path, port: int) -> tuple[dict, dict | None]:
    rid = pointer(directory, port)["response_id"]
    response = request(port, "GET", f"/responses/{rid}")
    gate = request(port, "GET", f"/workshop/approvals/{rid}", allow_missing=True)
    return response, gate


def status(directory: Path, port: int) -> dict:
    response, gate = state(directory, port)
    return {
        "mode": MODE,
        "response_id": response["id"],
        "response_status": response["status"],
        "error": response.get("error"),
        "approval_task_id": gate["task_id"] if gate else None,
        "approval_status": gate["status"] if gate else "not-created-yet",
        "human_authorization": gate["human_authorization"] if gate else "not-granted",
        "output_ids": [item["id"] for item in response["output"]],
        "gate": gate,
    }


def start(directory: Path, port: int) -> dict:
    verify_server(directory, port)
    # Reserve the client slot before POST: an ambiguous create must not silently create another task.
    with (directory / "client.json").open("x", encoding="utf-8") as handle:
        json.dump({"mode": MODE, "port": port, "response_id": None}, handle)
    query = Request(
        f"http://127.0.0.1:{port}/responses",
        data=json.dumps(
            {
                "model": MODEL_LABEL,
                "input": "D03",
                "store": True,
                "background": True,
                "stream": True,
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    rid = None
    output_seen = False
    with build_opener(ProxyHandler({}), NoRedirects()).open(query, timeout=15) as reply:
        for line in reply:
            if not line.startswith(b"data:"):
                continue
            event = json.loads(line[5:].strip())
            if event["type"] == "response.created":
                rid = response_id(event["response"]["id"])
                write_json(
                    directory / "client.json",
                    {
                        "mode": MODE,
                        "port": port,
                        "response_id": rid,
                    },
                )
            elif event["type"] == "response.output_item.done":
                output_seen = True
                break
            elif event["type"] in ("response.failed", "error"):
                raise ValueError(f"SDK stream failed before the approval checkpoint: {event}")
    if rid is None or not output_seen:
        raise ValueError(
            "Stream ended without an SDK response ID and approval output; do not re-POST."
        )
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        current, gate = state(directory, port)
        if current["status"] in ("failed", "cancelled"):
            raise ValueError(f"Response stopped before the approval checkpoint: {current}")
        evidence = directory / "checkpoint.json"
        if gate is not None and evidence.exists():
            committed = read_json(evidence)["response"]
            if committed["id"] == rid and len(committed["output"]) == 1:
                write_json(directory / "initial-response.json", committed)
                return status(directory, port)
        time.sleep(0.1)
    raise TimeoutError("Approval checkpoint was not observed in 15 seconds; do not re-POST start.")


def decide(directory: Path, port: int, choice: str, *, confirmed: bool) -> dict:
    if not confirmed:
        raise ValueError(
            "Decision requires --confirm-simulated-decision; it is NOT human authorization."
        )
    verify_server(directory, port)
    response, gate = state(directory, port)
    if response["status"] not in ("queued", "in_progress") or gate is None:
        raise ValueError("No active response with a pending gate is available.")
    return request(
        port,
        "POST",
        f"/workshop/approvals/{response['id']}",
        {
            "gate_id": gate["gate_id"],
            "request_sha256": gate["request_sha256"],
            "if_last_input_id": gate["request_input_id"],
            "input_id": f"simulated-{uuid.uuid4().hex}",
            "decision": choice,
            "simulated": True,
        },
    )


def wait(directory: Path, port: int, seconds: int, *, verify_crash: bool = False) -> dict:
    if not 1 <= seconds <= 120:
        raise ValueError("Client wait must be between 1 and 120 seconds.")
    before = (
        read_json(directory / "crash-checkpoint.json")["response"]
        if verify_crash
        else read_json(directory / "initial-response.json")
    )
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        response, gate = state(directory, port)
        if response["status"] in ("failed", "cancelled"):
            raise ValueError(f"Response did not complete; no success or quality score: {response}")
        if response["status"] == "completed":
            if gate is None:
                raise ValueError("Missing approval lineage for a completed response.")
            report = verify_completion(before, response, gate)
            write_json(directory / "completed-response.json", response)
            return {
                **report,
                "verified_against": "crash-checkpoint" if verify_crash else "initial-response",
            }
        time.sleep(0.1)
    raise TimeoutError("Bounded client wait expired; the existing response ID is unchanged.")


def checkpoint_recorder(directory: Path, crash_after: int | None, *, confirmed: bool = False):
    if (crash_after is not None) != confirmed:
        raise ValueError("A crash index and explicit owned-process confirmation are both required.")
    if crash_after is not None and (crash_after not in (0, 1) or platform.system() != "Linux"):
        raise ValueError("Only checkpoint 0 or 1 in a dedicated Linux process may be crashed.")
    owner_pid = os.getpid()

    def record(response: dict, recovered: bool) -> None:
        evidence = {"response": response, "handler_is_recovery": recovered}
        write_json(directory / "checkpoint.json", evidence)
        if crash_after is None or len(response["output"]) - 1 != crash_after:
            return
        if os.getpid() != owner_pid:
            raise ValueError("The crash hook can only exit its dedicated owning process.")
        if (directory / "crash-once.json").exists():
            logging.warning("Owned-process crash already exercised; not repeating it.")
            return
        write_json(directory / "crash-checkpoint.json", evidence)
        with (directory / "crash-once.json").open("x", encoding="utf-8") as handle:
            json.dump({"pid": owner_pid, "response_id": response["id"]}, handle)
            handle.flush()
            os.fsync(handle.fileno())
        logging.warning(
            "Explicit opt-in: exiting owned PID %s after committed checkpoint %s.",
            owner_pid,
            crash_after,
        )
        os._exit(86)

    return record


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--run-id", default="first-pass")
    value.add_argument("--port", type=int, default=8093)
    value.add_argument("--language", choices=("en", "ko"), default="en")
    commands = value.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="Check the installed SDK contract without Azure.")
    serve = commands.add_parser("serve", help="Run one owned loopback-only SDK host.")
    serve.add_argument("--approval-timeout-seconds", type=int, default=600)
    serve.add_argument("--stage-delay-seconds", type=float, default=1)
    serve.add_argument("--crash-after-checkpoint", type=int, choices=(0, 1))
    serve.add_argument("--allow-owned-process-crash", action="store_true")
    commands.add_parser("start", help="Create exactly one stored background response.")
    commands.add_parser("status", help="Read this run's existing response and durable gate.")
    decision = commands.add_parser("decide", help="Submit an explicitly simulated decision.")
    decision.add_argument("--decision", choices=("approve", "reject"), required=True)
    decision.add_argument("--confirm-simulated-decision", action="store_true")
    completion = commands.add_parser("wait", help="Verify completion and original output IDs.")
    completion.add_argument("--timeout-seconds", type=int, default=30)
    completion.add_argument("--verify-crash-checkpoint", action="store_true")
    removal = commands.add_parser(
        "cleanup", help="Delete only this stopped run's owned local state."
    )
    removal.add_argument("--confirm-delete-local-state", action="store_true")
    return value


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if not 1024 <= args.port <= 65535:
        raise ValueError("Choose an unprivileged local port between 1024 and 65535.")
    if args.command == "check":
        result = check_sdks()
    elif args.command == "serve":
        check_sdks()
        if (args.crash_after_checkpoint is not None) != args.allow_owned_process_crash:
            raise ValueError("A crash index and --allow-owned-process-crash are both required.")
        if args.allow_owned_process_crash and platform.system() != "Linux":
            raise ValueError(
                "Use Linux/WSL/a Linux container for the hard-crash branch, not macOS."
            )
        with owned_run(ROOT, args.run_id, create=True, language=args.language) as directory:
            if (directory / "cleanup.json").exists():
                raise ValueError(
                    "This run was cleaned up. Preserve its evidence and choose a new run ID."
                )
            os.environ["AGENTSERVER_STATE_ROOT"] = str(directory / "sdk-state")
            os.environ["FOUNDRY_AGENT_NAME"] = OWNER
            os.environ["FOUNDRY_AGENT_SESSION_ID"] = args.run_id
            from examples.resilient.server import create_app

            app = create_app(
                ROOT,
                language=args.language,
                approval_timeout_seconds=args.approval_timeout_seconds,
                stage_delay_seconds=args.stage_delay_seconds,
                on_checkpoint=checkpoint_recorder(
                    directory, args.crash_after_checkpoint, confirmed=args.allow_owned_process_crash
                ),
            )
            print(
                json.dumps(
                    {
                        "mode": MODE,
                        "pid": os.getpid(),
                        "state_root": os.environ["AGENTSERVER_STATE_ROOT"],
                        "url": f"http://127.0.0.1:{args.port}",
                        "azure_requests_sent": False,
                    }
                ),
                flush=True,
            )
            app.run(host="127.0.0.1", port=args.port)
        return 0
    elif args.command == "cleanup":
        result = cleanup(
            ROOT, args.run_id, confirmed=args.confirm_delete_local_state, language=args.language
        )
    else:
        directory = run_directory(ROOT, args.run_id)
        if read_json(directory / "owner.json") != run_marker(args.run_id, args.language):
            raise ValueError("This is not an owned resilience run.")
        if args.command == "start":
            result = start(directory, args.port)
        elif args.command == "status":
            result = status(directory, args.port)
        elif args.command == "decide":
            result = decide(
                directory, args.port, args.decision, confirmed=args.confirm_simulated_decision
            )
        else:
            result = wait(
                directory,
                args.port,
                args.timeout_seconds,
                verify_crash=args.verify_crash_checkpoint,
            )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TimeoutError, importlib.metadata.PackageNotFoundError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
