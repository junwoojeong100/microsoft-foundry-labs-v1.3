#!/usr/bin/env python3
"""Verify an existing Azure CLI CI login without tokens, resource writes, or inference."""

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Mapping
from uuid import UUID

VARIABLES = ("AZURE_CLIENT_ID", "AZURE_TENANT_ID", "AZURE_SUBSCRIPTION_ID")


def configuration(environment: Mapping[str, str]) -> dict[str, str]:
    result = {}
    for name in VARIABLES:
        value = environment.get(name, "").strip()
        if not value:
            raise ValueError(f"Set {name} in the protected GitHub environment.")
        try:
            result[name] = str(UUID(value))
        except ValueError as exc:
            raise ValueError(f"{name} must be a UUID.") from exc
    return result


def verify_account(account: object, expected: Mapping[str, str]) -> dict[str, object]:
    if not isinstance(account, dict) or not isinstance(account.get("user"), dict):
        raise ValueError("Azure CLI did not return an account with an identity.")
    if account["user"].get("type") != "servicePrincipal":
        raise ValueError("CI must authenticate as the configured service principal, not a user.")
    actual = {
        "AZURE_CLIENT_ID": account["user"].get("name"),
        "AZURE_TENANT_ID": account.get("tenantId"),
        "AZURE_SUBSCRIPTION_ID": account.get("id"),
    }
    for name, value in actual.items():
        if not isinstance(value, str) or value.lower() != expected[name]:
            raise ValueError(f"Authenticated account does not match {name}.")
    return {
        "status": "authenticated",
        "client_id": actual["AZURE_CLIENT_ID"],
        "tenant_id": actual["AZURE_TENANT_ID"],
        "subscription_id": actual["AZURE_SUBSCRIPTION_ID"],
        "deployment_verified": False,
        "model_requests": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args(argv)
    try:
        expected = configuration(os.environ)
        if args.preflight:
            result = {"status": "configured", "authentication_verified": False}
        else:
            process = subprocess.run(
                ["az", "account", "show", "--output", "json", "--only-show-errors"],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            result = verify_account(json.loads(process.stdout), expected)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        print(f"ERROR: CI authentication verification failed: {detail or exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
