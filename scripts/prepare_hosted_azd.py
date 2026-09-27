#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from foundry_workshop.contracts import read_json  # noqa: E402
from foundry_workshop.packaging import file_hashes  # noqa: E402
from foundry_workshop.profiles import (  # noqa: E402
    RuntimeProfile,
    model_deployments,
    packaged_profile,
    validate_inference_endpoint,
)
from foundry_workshop.search import search_configuration  # noqa: E402
from foundry_workshop.settings import (  # noqa: E402
    Settings,
    load_environment,
    owned_prefix,
    require_env,
    require_uuid,
)
from foundry_workshop.toolbox import name_for  # noqa: E402


def environment_values(settings: Settings, project_id: str) -> dict[str, str]:
    subscription = require_uuid("AZURE_SUBSCRIPTION_ID")
    if not settings.tenant_id:
        raise ValueError("Local azd initialization requires the configured workshop tenant.")
    expected = (
        f"/subscriptions/{subscription}/resourceGroups/{require_env('AZURE_RESOURCE_GROUP')}"
        f"/providers/Microsoft.CognitiveServices/accounts/{require_env('AZURE_AI_ACCOUNT_NAME')}"
        f"/projects/{settings.project_endpoint.rsplit('/', 1)[-1]}"
    )
    if project_id.casefold() != expected.casefold():
        raise ValueError("The supplied actual project ARM ID differs from the workshop scope.")
    return {
        "AZURE_AI_PROJECT_ID": project_id,
        "AZURE_AI_PROJECT_ENDPOINT": settings.project_endpoint,
        "FOUNDRY_PROJECT_ENDPOINT": settings.project_endpoint,
        "AZURE_AI_MODEL_DEPLOYMENT_NAME": settings.deployment,
        "AZURE_TENANT_ID": settings.tenant_id,
    }


def initialize_environment(
    destination: Path, agent_name: str, values: dict[str, str], location: str
) -> None:
    if not re.fullmatch(r"[a-z0-9]+", location):
        raise ValueError("Use the actual existing project's Azure location code.")
    if (destination / ".azure").exists():
        raise FileExistsError("Preserve the existing azd environment; do not initialize it again.")
    manifest = read_json(destination / "azure.yaml")
    if (
        manifest.get("name") != agent_name
        or manifest["services"]["workshop-project"]["endpoint"]
        != values["AZURE_AI_PROJECT_ENDPOINT"]
    ):
        raise ValueError("Initialize only the matching prepared manifest.")

    def run(arguments: list[str]) -> str:
        result = subprocess.run(
            ["azd", *arguments],
            cwd=destination,
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
        return result.stdout.strip()

    run(
        [
            "env",
            "new",
            agent_name,
            "--subscription",
            require_env("AZURE_SUBSCRIPTION_ID"),
            "--location",
            location,
            "--no-prompt",
        ]
    )
    for key, value in values.items():
        run(["env", "set", key, value])
        if run(["env", "get-value", key]) != value:
            raise ValueError(f"azd environment readback differs for {key}.")


def prepare(
    package: Path, destination: Path, settings: Settings, agent_name: str, *, kind: str = "toolbox"
) -> Path:
    if kind not in {"toolbox", "workflow", "runtime", "matrix"}:
        raise ValueError(
            "Choose toolbox, workflow (CI), runtime (introductory Responses), or matrix (IQ Invocations)."
        )
    if not agent_name.startswith(owned_prefix() + "-") or not re.fullmatch(
        r"[a-z0-9-]{1,100}", agent_name
    ):
        raise ValueError("Use a new agent name inside the explicitly approved workshop prefix.")
    if package.is_symlink() or not package.is_dir():
        raise ValueError("Use the original regular Hosted package directory.")
    package = package.resolve()
    if any(path.is_symlink() for path in package.rglob("*")):
        raise ValueError("The deployment package must not contain symbolic links.")
    manifest = read_json(package / "package-manifest.json")
    actual = file_hashes(package)
    actual.pop("package-manifest.json")
    if manifest.get("files") != actual:
        raise ValueError("The original package files or profile changed; do not deploy drift.")
    environment = {
        "AZURE_AI_PROJECT_ENDPOINT": settings.project_endpoint,
        "AZURE_AI_MODEL_DEPLOYMENT_NAME": settings.deployment,
        "WORKSHOP_PREFIX": owned_prefix(),
        "WORKSHOP_AUTH_MODE": "managed-identity",
        "WORKSHOP_MAX_OUTPUT_TOKENS": "2048",
    }
    if kind == "toolbox":
        profile = read_json(package / "toolbox-profile.json")
        if (
            manifest.get("kind") != "synthetic-toolbox-package"
            or manifest.get("profile") != profile
        ):
            raise ValueError("The original Toolbox package profile changed.")
        search = search_configuration()
        if (
            profile.get("language") != settings.language
            or profile.get("runtime")
            != {
                "project_endpoint": settings.project_endpoint,
                "deployment": settings.deployment,
                "toolbox_name": name_for(settings),
                "search_connection": require_env("TOOLBOX_SEARCH_CONNECTION_NAME"),
            }
            or profile["source"]["search_endpoint"] != search["endpoint"]
            or profile["source"]["index"] != search["index"]
            or profile["source"]["prefix"] != owned_prefix()
        ):
            raise ValueError(
                "The package does not match this language, project, model or Search scope."
            )
        environment.update(
            AZURE_SEARCH_ENDPOINT=search["endpoint"],
            AZURE_SEARCH_INDEX_NAME=search["index"],
            TOOLBOX_NAME=name_for(settings),
            TOOLBOX_SEARCH_CONNECTION_NAME=require_env("TOOLBOX_SEARCH_CONNECTION_NAME"),
        )
        protocol = "responses"
    elif kind == "runtime":
        profile = packaged_profile(package)
        expected_profile = RuntimeProfile(
            kind=profile.kind,
            pattern=profile.pattern,
            language=settings.language,
        )
        if (
            profile != expected_profile
            or manifest.get("runtime_profile") != expected_profile.to_dict()
        ):
            raise ValueError(
                "Use a language-matched local v2 Responses policy/workflow package for --kind runtime."
            )
        environment["WORKSHOP_MAX_OUTPUT_TOKENS"] = str(settings.max_output_tokens)
        protocol = "responses"
    elif kind == "matrix":
        profile = packaged_profile(package)
        expected_profile = RuntimeProfile(
            kind="workflow",
            pattern="sequential",
            retrieval="iq",
            prompt=profile.prompt,
            api="account-chat",
            protocol="invocations",
            language=settings.language,
        )
        if (
            profile != expected_profile
            or manifest.get("runtime_profile") != expected_profile.to_dict()
        ):
            raise ValueError(
                "Use a language-matched sequential IQ/account-chat Invocations v1/v2 matrix package."
            )
        if settings.openai_endpoint is None:
            raise ValueError("The matrix requires an explicit same-account OpenAI endpoint.")
        if agent_name != require_env("WORKSHOP_HOSTED_AGENT_NAME"):
            raise ValueError("The matrix agent name must match WORKSHOP_HOSTED_AGENT_NAME.")
        validate_inference_endpoint(settings, profile)
        require_env("WORKSHOP_MODEL_DEPLOYMENTS_JSON")
        models = model_deployments(settings)
        search = search_configuration()
        environment.update(
            AZURE_OPENAI_ENDPOINT=settings.openai_endpoint,
            WORKSHOP_MODEL_DEPLOYMENTS_JSON=json.dumps(models),
            WORKSHOP_MAX_OUTPUT_TOKENS=str(settings.max_output_tokens),
            AZURE_SEARCH_ENDPOINT=search["endpoint"],
            AZURE_SEARCH_INDEX_NAME=search["index"],
            AZURE_SEARCH_KNOWLEDGE_SOURCE_NAME=search["source"],
            AZURE_SEARCH_KNOWLEDGE_BASE_NAME=search["knowledge_base"],
        )
        if "iq_reranker_threshold" in search:
            environment["WORKSHOP_IQ_RERANKER_THRESHOLD"] = str(search["iq_reranker_threshold"])
        protocol = "invocations"
    else:
        expected_profile = RuntimeProfile(
            kind="workflow",
            pattern="sequential",
            retrieval="local",
            prompt="v2",
            api="project-responses",
            protocol="invocations",
            language=settings.language,
        )
        if (
            packaged_profile(package) != expected_profile
            or manifest.get("runtime_profile") != expected_profile.to_dict()
        ):
            raise ValueError("Use only the exact language-specific sequential CI workflow profile.")
        models = json.loads(require_env("WORKSHOP_MODEL_DEPLOYMENTS_JSON"))
        if models != {"primary": settings.deployment}:
            raise ValueError(
                "The CI model map must contain only the configured primary deployment."
            )
        environment["WORKSHOP_MODEL_DEPLOYMENTS_JSON"] = json.dumps(models)
        protocol = "invocations"
    if destination.is_symlink():
        raise ValueError("Use a real, empty azd directory, not a symbolic link.")
    destination = destination.resolve()
    if destination.is_relative_to(package) or package.is_relative_to(destination):
        raise ValueError("Keep the immutable package and azd directory separate.")
    if any((parent / "azure.yaml").exists() for parent in destination.parents):
        raise ValueError("Use a directory outside any existing azd project.")
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise FileExistsError("Preserve the existing azd directory; select a new empty directory.")
    data = {
        "name": agent_name,
        "services": {
            "workshop-project": {
                "host": "azure.ai.project",
                "endpoint": settings.project_endpoint,
            },
            agent_name: {
                "project": f"src/{agent_name}",
                "host": "azure.ai.agent",
                "language": "python",
                "uses": ["workshop-project"],
                "kind": "hosted",
                "name": agent_name,
                "codeConfiguration": {
                    "runtime": "python_3_13",
                    "entryPoint": "main.py",
                    "dependencyResolution": "remote_build",
                },
                "protocols": [
                    {
                        "protocol": protocol,
                        "version": "2.0.0" if protocol == "responses" else "1.0.0",
                    }
                ],
                "env": environment,
                "container": {"resources": {"cpu": "1", "memory": "2Gi"}},
            },
        },
        "infra": {"provider": "microsoft.foundry"},
    }
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(package, destination / "src" / agent_name)
    path = destination / "azure.yaml"
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prepare a package-verified manifest in an empty azd folder, without Azure calls."
    )
    parser.add_argument("--language", choices=("en", "ko"), default="en")
    parser.add_argument(
        "--kind",
        choices=("toolbox", "workflow", "runtime", "matrix"),
        default="toolbox",
        help="toolbox; workflow for fixed CI; runtime for introductory local v2 Responses; matrix for sequential IQ/account-chat Invocations v1/v2.",
    )
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--agent-name", required=True)
    parser.add_argument("--initialize-env", action="store_true")
    parser.add_argument("--project-id")
    parser.add_argument("--location")
    args = parser.parse_args()
    if args.initialize_env and (not args.project_id or not args.location):
        parser.error("--initialize-env requires the actual --project-id and --location.")
    if not args.initialize_env and (args.project_id or args.location):
        parser.error("--project-id and --location are used only with --initialize-env.")
    try:
        load_environment(ROOT)
        settings = Settings.from_env(language=args.language)
        values = environment_values(settings, args.project_id) if args.initialize_env else None
        path = prepare(args.package, args.directory, settings, args.agent_name, kind=args.kind)
        if values is not None:
            initialize_environment(path.parent, args.agent_name, values, args.location)
        print(path)
        print("Local manifest/environment only; no provision, deployment or model request.")
    except subprocess.CalledProcessError as error:
        print(
            f"FAIL: azd exited {error.returncode}: {error.stderr or error.stdout}", file=sys.stderr
        )
        raise SystemExit(1) from error
    except (OSError, ValueError, ImportError, subprocess.TimeoutExpired) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
