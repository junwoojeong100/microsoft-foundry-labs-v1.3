#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from foundry_workshop.contracts import (  # noqa: E402
    Answer,
    code_hash,
    digest,
    parse_json,
    read_json,
    write_json,
)


def completed_response(text: str) -> dict:
    if len(text.encode()) > 10_485_760:
        raise ValueError("The recorded response exceeds the bounded verification input size.")
    text = text.replace("\r\n", "\n")
    if text.startswith("HTTP/"):
        header, separator, body = text.partition("\n\n")
        lines = header.splitlines()
        if not separator or not re.fullmatch(r"HTTP/\d(?:\.\d)? 200(?: .*)?", lines[0]):
            raise ValueError(
                "The original HTTP response must be successful before parsing its stream."
            )
        headers = {}
        for line in lines[1:]:
            key, colon, value = line.partition(":")
            if not colon:
                raise ValueError("Malformed original HTTP response header.")
            headers[key.casefold()] = value.strip()
        if not headers.get("content-type", "").casefold().startswith("text/event-stream"):
            raise ValueError("The original response is not an SSE stream.")
        text = body
    events = []
    data = []
    for line in [*text.splitlines(), ""]:
        if not line:
            if data:
                body = "\n".join(data)
                if body != "[DONE]":
                    event = parse_json(body)
                    if not isinstance(event, dict):
                        raise ValueError("Every response event must be an object.")
                    events.append(event)
                data = []
        elif line.startswith("data:"):
            data.append(line[5:].lstrip(" "))
        elif line.startswith(("event:", "id:", "retry:", ":")):
            continue
        else:
            raise ValueError(
                "Supply the original --output raw SSE file, not a CLI status transcript."
            )
    if any(
        event.get("type") in {"error", "response.failed", "response.incomplete"} for event in events
    ):
        raise ValueError(
            "The service stream contains a failure/incomplete event; exit0 does not pass."
        )
    finals = [
        event.get("response") for event in events if event.get("type") == "response.completed"
    ]
    if (
        len(finals) != 1
        or not isinstance(finals[0], dict)
        or finals[0].get("status") != "completed"
        or finals[0].get("error")
    ):
        raise ValueError("The stream must contain one actual completed response without an error.")
    return finals[0]


def verify(text: str, package: Path, agent_name: str, agent_version: str) -> dict:
    response = completed_response(text)
    reference = response.get("agent_reference")
    if (
        not isinstance(reference, dict)
        or reference.get("name") != agent_name
        or reference.get("version") != agent_version
    ):
        raise ValueError(
            "The completed response does not match the requested actual agent version."
        )
    profile = read_json(package / "toolbox-profile.json")
    messages = [
        content["text"]
        for item in response.get("output", [])
        if item.get("type") == "message"
        for content in item.get("content", [])
        if content.get("type") == "output_text"
    ]
    if len(messages) != 1:
        raise ValueError("Expected the one actual Toolbox result envelope.")
    result = parse_json(messages[0])
    expected = {
        "mode": "live-toolbox-agent",
        "language": profile["language"],
        "toolbox_name": profile["runtime"]["toolbox_name"],
        "toolbox_version": profile["toolbox_version"],
        "deployment": profile["runtime"]["deployment"],
        "corpus_hash": profile["source"]["corpus_hash"],
        "code_hash": code_hash(package),
        "model_invoked": True,
        "tool_invoked": True,
    }
    if not isinstance(result, dict) or any(
        result.get(key) != value for key, value in expected.items()
    ):
        raise ValueError(
            "The actual runtime result differs from the pinned package or did not execute its tools/models."
        )
    calls = result.get("model_calls")
    functions = result.get("function_calls")
    if (
        not isinstance(calls, list)
        or not calls
        or any(not item.get("response_id") or not item.get("response_model") for item in calls)
    ):
        raise ValueError("Actual model call identities are required.")
    if (
        not isinstance(functions, list)
        or not functions
        or any(item.get("completed") is not True for item in functions)
    ):
        raise ValueError("Every recorded tool function must have completed.")
    if profile["with_skill"]:
        if result.get("skill_load_verified") is not True or not any(
            item.get("name") == "load_skill" for item in functions
        ):
            raise ValueError("The pinned Skill must have actually loaded.")
        Answer.from_dict(result.get("structured_answer"))
    if not response.get("agent_session_id") or not response.get("id"):
        raise ValueError("Preserve the actual service session and response IDs.")
    return {
        "mode": "verification-of-recorded-hosted-response",
        "azure_requests_sent": False,
        "verified": True,
        "agent_name": agent_name,
        "agent_version": agent_version,
        "response_id": response["id"],
        "session_id": response["agent_session_id"],
        "conversation": response.get("conversation"),
        "toolbox_version": result["toolbox_version"],
        "skill_ref": result.get("skill_ref"),
        "structured_answer": result.get("structured_answer"),
        "model_response_ids": [item["response_id"] for item in calls],
        "runtime_code_hash": result["code_hash"],
        "response_hash": digest(response),
        "remote_evidence_directory": result["output_directory"],
        "note": "Verification reads the preserved service stream; it does not issue another model request or grant production approval.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verify the original Hosted Toolbox response stream, not CLI exit status."
    )
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--agent-name", required=True)
    parser.add_argument("--agent-version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise FileExistsError("Preserve the previous verification output.")
        result = verify(args.file.read_text(), args.package, args.agent_name, args.agent_version)
        write_json(args.output, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
