#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from foundry_workshop.contracts import write_json  # noqa: E402
from foundry_workshop.settings import Settings, require_env  # noqa: E402
from scripts.prepare_ci_azd import validate_config  # noqa: E402

FOUNDRY_USER = "53ca6127-db72-4b80-b1b0-d745d6d5456d"


def runtime_principal(actual: dict, service: str, version: str) -> str:
    if (
        actual.get("name") != service
        or actual.get("version") != version
        or actual.get("status") not in {"active", "deployed"}
    ):
        raise ValueError(
            "The runtime identity must come from the exact active deployed agent/version."
        )
    identity = actual.get("instance_identity")
    principal = identity.get("principal_id") if isinstance(identity, dict) else None
    if not isinstance(principal, str) or str(UUID(principal)) != principal.casefold():
        raise ValueError("The deployed agent did not return a valid principal object ID.")
    return principal


def ensure(service: str, output: Path, *, confirmed: bool) -> dict:
    if not confirmed:
        raise ValueError("Runtime role creation requires explicit --confirm-role.")
    settings = Settings.from_env()
    validate_config(settings, service)
    version = require_env("WORKSHOP_HOSTED_AGENT_VERSION")
    scope = require_env("AZURE_AI_PROJECT_ID")

    def command(arguments):
        completed = subprocess.run(
            arguments, capture_output=True, text=True, check=True, timeout=120
        )
        return json.loads(completed.stdout)

    actual = command(["azd", "ai", "agent", "show", service, "--output", "json"])
    principal = runtime_principal(actual, service, version)
    assignments = command(
        [
            "az",
            "role",
            "assignment",
            "list",
            "--subscription",
            require_env("AZURE_SUBSCRIPTION_ID"),
            "--scope",
            scope,
            "--output",
            "json",
        ]
    )
    matches = [
        item
        for item in assignments
        if item.get("principalId") == principal
        and item.get("roleDefinitionId", "").endswith("/" + FOUNDRY_USER)
        and item.get("scope", "").casefold() == scope.casefold()
    ]
    if len(matches) > 1:
        raise ValueError("Duplicate role assignments require owner review.")
    created = not matches
    assignment = (
        matches[0]
        if matches
        else command(
            [
                "az",
                "role",
                "assignment",
                "create",
                "--subscription",
                require_env("AZURE_SUBSCRIPTION_ID"),
                "--assignee-object-id",
                principal,
                "--assignee-principal-type",
                "ServicePrincipal",
                "--role",
                FOUNDRY_USER,
                "--scope",
                scope,
                "--output",
                "json",
            ]
        )
    )
    if (
        assignment.get("principalId") != principal
        or assignment.get("scope", "").casefold() != scope.casefold()
    ):
        raise ValueError(
            "The returned role assignment does not match the intended runtime/project."
        )
    result = {
        "agent": service,
        "version": version,
        "principal": principal,
        "role": FOUNDRY_USER,
        "scope": scope,
        "assignment_id": assignment["id"],
        "created": created,
        "data_plane_access_verified": False,
    }
    write_json(output, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Grant only project-scoped Foundry User to the actual owned runtime identity."
    )
    parser.add_argument("--service", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--confirm-role", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(ensure(args.service, args.output, confirmed=args.confirm_role), indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
