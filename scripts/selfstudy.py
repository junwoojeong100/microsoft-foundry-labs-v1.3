from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from foundry_workshop.model_plan import (  # noqa: E402
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_REASONING_EFFORT,
    MAX_OUTPUT_TOKENS,
    MODEL_ROLES,
    PRIMARY_MODEL,
    PRIMARY_VERSION,
    REASONING_EFFORTS,
)

STATE = ROOT / ".selfstudy/azure.json"
ENV = ROOT / ".env"
PROJECT_ID = re.compile(
    r"^/subscriptions/([^/]+)/resourceGroups/([^/]+)/providers/"
    r"Microsoft\.CognitiveServices/accounts/([^/]+)/projects/([^/]+)$",
    re.IGNORECASE,
)
RESOURCE_TYPES = {
    "search": "microsoft.search/searchservices",
    "insights": "microsoft.insights/components",
    "logs": "microsoft.operationalinsights/workspaces",
    "storage": "microsoft.storage/storageaccounts",
}
MUTABLE_KEYS = {
    "AZURE_AI_MODEL_DEPLOYMENT_NAME",
    "AZURE_AI_EVALUATION_MODEL_DEPLOYMENT_NAME",
    "AZURE_AI_EMBEDDING_DEPLOYMENT_NAME",
    "AZURE_OPENAI_ENDPOINT",
    "WORKSHOP_EMBEDDING_DIMENSIONS",
    "WORKSHOP_EMBEDDING_API",
    "WORKSHOP_MAX_OUTPUT_TOKENS",
    "WORKSHOP_REASONING_EFFORT",
    "WORKSHOP_IQ_RERANKER_THRESHOLD",
    "WORKSHOP_MODEL_DEPLOYMENTS_JSON",
    "AZURE_SEARCH_INDEX_NAME",
    "AZURE_SEARCH_KNOWLEDGE_SOURCE_NAME",
    "AZURE_SEARCH_KNOWLEDGE_BASE_NAME",
    "AZURE_SEARCH_CHAT_KNOWLEDGE_BASE_NAME",
    "TOOLBOX_SEARCH_CONNECTION_NAME",
    "TOOLBOX_NAME",
    "WORKSHOP_HOSTED_AGENT_NAME",
    "WORKSHOP_HOSTED_AGENT_VERSION",
    "WORKSHOP_HOSTED_AGENT_ENDPOINT",
    "WORKSHOP_MEMORY_STORE_NAME",
}
ROLE_IDS = {
    "Foundry User": "53ca6127-db72-4b80-b1b0-d745d6d5456d",
    "Search Index Data Contributor": "8ebe5a00-799e-43f5-93ac-243d3dce84a7",
    "Search Index Data Reader": "1407120a-92aa-4202-b7e9-c0e197c71c8f",
    "Search Service Contributor": "7ca78c08-252a-4471-8644-bb5ff32d4ba0",
    "Cognitive Services User": "a97b65f3-24c7-4388-baec-2e87135dc908",
    "Log Analytics Reader": "73c42c96-874c-492b-b04d-ab87d138a893",
    "Monitoring Reader": "43d0d8ad-25c7-4714-9337-8ba259a9fe05",
}


class SetupError(RuntimeError):
    pass


def verify_runtime() -> None:
    for name in ("src/foundry_workshop/cli.py", "data/knowledge/policies.json", "pyproject.toml"):
        if not (ROOT / name).is_file():
            raise SetupError("실습 폴더 전체가 필요합니다. README.md가 있는 폴더에서 실행하세요.")


def uuid_value(value: str) -> str:
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise SetupError("포털에서 복사한 실제 UUID를 입력하세요.") from exc


def parse_project_id(value: str) -> dict[str, str]:
    match = PROJECT_ID.fullmatch(value.rstrip("/"))
    if not match:
        raise SetupError(
            "Foundry 계정이 아닌 accounts/.../projects/... 프로젝트 ARM ID가 필요합니다."
        )
    subscription, group, account, project = match.groups()
    return {
        "subscription": uuid_value(subscription),
        "group": group,
        "account": account,
        "project": project,
        "project_id": value.rstrip("/"),
        "account_id": value[: match.end(3)],
    }


def validate_endpoint(value: str, kind: str) -> str:
    parsed = urlsplit(value)
    host = parsed.hostname or ""
    suffix = {
        "project": ".services.ai.azure.com",
        "search": ".search.windows.net",
        "openai": ".openai.azure.com",
    }[kind]
    if (
        parsed.scheme != "https"
        or not host.endswith(suffix)
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
        or parsed.query
        or parsed.fragment
    ):
        raise SetupError(f"{kind}: 인증정보·쿼리가 없는 실제 Azure HTTPS Endpoint를 입력하세요.")
    path = parsed.path.rstrip("/")
    if kind == "project":
        if not re.fullmatch(r"/api/projects/[^/]+", path):
            raise SetupError("모델 URL이 아닌 /api/projects/... 프로젝트 Endpoint가 필요합니다.")
    elif path:
        raise SetupError(f"{kind}: 서비스 루트 Endpoint만 입력하세요.")
    if any(marker in value.lower() for marker in ("your-", "replace", "<", ">")):
        raise SetupError("예시를 그대로 쓰지 말고 포털에서 실제 값을 복사하세요.")
    return value.rstrip("/")


def az_json(*args: str) -> dict:
    executable = shutil.which("az")
    if not executable:
        raise SetupError("Azure CLI를 설치하고 az login을 먼저 실행하세요.")
    result = subprocess.run(
        [executable, *args, "--only-show-errors", "--output", "json"],
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    if result.returncode:
        raise SetupError(f"Azure 읽기 요청 실패: {result.stderr.strip()}")
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise SetupError("Azure 읽기 응답이 예상한 JSON 객체가 아닙니다.")
    return value


def write_text(path: Path, content: str) -> None:
    if not path.resolve().is_relative_to(ROOT.resolve()) or path.is_symlink():
        raise SetupError("설정 파일은 이 실습 폴더 안의 일반 파일에만 씁니다.")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(path)


def save_state(value: dict) -> None:
    write_text(STATE, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def env_values() -> dict[str, str]:
    try:
        from dotenv import dotenv_values
    except ModuleNotFoundError as exc:
        raise SetupError(
            "먼저 .venv를 활성화하고 python -m pip install -r requirements.txt를 실행하세요."
        ) from exc
    return {key: value or "" for key, value in dotenv_values(ENV, interpolate=False).items()}


def update_env(updates: dict[str, str]) -> None:
    for key, value in updates.items():
        if not value or any(part in value for part in ("\n", "\r", "\0", "${")):
            raise SetupError(f"{key}: 빈 값, 줄바꿈, 변수 확장을 허용하지 않습니다.")
    lines = (
        ENV.read_text(encoding="utf-8").splitlines()
        if ENV.exists()
        else [
            "# Generated by scripts/selfstudy.py. No passwords, keys or tokens.",
        ]
    )
    remaining = dict(updates)
    result = []
    for line in lines:
        match = re.match(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=", line)
        if match and match.group(1) in updates:
            key = match.group(1)
            if key in remaining:
                value = remaining.pop(key).replace("'", "\\'")
                result.append(f"{key}='{value}'")
        else:
            result.append(line)
    for key, value in remaining.items():
        result.append(f"{key}='" + value.replace("'", "\\'") + "'")
    write_text(ENV, "\n".join(result) + "\n")


def read_state() -> dict:
    if not STATE.exists():
        raise SetupError("먼저 Lab 00의 configure를 실행하세요.")
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if state.get("schema_version") != 1:
        raise SetupError("지원하지 않는 자가 실습 설정 형식입니다.")
    values = env_values()
    for key, expected in state["identity_env"].items():
        if values.get(key) != expected:
            raise SetupError(
                f"{key}: SDK 설정과 기록된 실습 대상이 다릅니다. 임의로 대상을 바꾸지 마세요."
            )
    return state


def validate_runtime_environment(environment: dict[str, str], *, explicit_model: bool) -> None:
    if not STATE.exists():
        return
    state = read_state()
    values = env_values()
    keys = (
        MUTABLE_KEYS
        | set(state["identity_env"])
        | {
            "AZURE_SEARCH_ENDPOINT",
            "AZURE_SEARCH_RESOURCE_GROUP",
            "AZURE_APPLICATION_INSIGHTS_APP_ID",
        }
    )
    for key in keys:
        if key == "AZURE_AI_MODEL_DEPLOYMENT_NAME" and explicit_model:
            continue
        if environment.get(key) and environment[key] != values.get(key):
            raise SetupError(
                f"{key}: 셸의 기존 값이 실습 설정과 충돌합니다. "
                "해당 export를 해제하거나 새 터미널을 사용하세요."
            )


def set_models(pairs: list[str]) -> None:
    models = {}
    for pair in pairs:
        key, separator, value = pair.partition("=")
        if (
            not separator
            or not re.fullmatch(r"[A-Za-z0-9_-]+", key)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value)
        ):
            raise SetupError("모델은 primary=실제배포 같은 형식으로 입력하세요.")
        if key in models or value in models.values():
            raise SetupError("모델 별칭이나 실제 배포를 중복 집계하지 않습니다.")
        models[key] = value
    if not 1 <= len(models) <= 8:
        raise SetupError("실제 모델 배포는 1~8개를 명시하세요.")
    set_value("WORKSHOP_MODEL_DEPLOYMENTS_JSON", json.dumps(models, ensure_ascii=False))


def compare_files(first: Path, second: Path) -> dict:
    paths = [
        (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
        for path in (first, second)
    ]
    if not all(path.is_relative_to(ROOT.resolve()) for path in paths):
        raise SetupError("이 실습 폴더 안의 두 파일만 비교합니다.")
    digests = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
    if digests[0] != digests[1]:
        raise SetupError(
            "원본과 readback 파일의 bytes가 다릅니다. 내려받은 내용을 수정하지 마세요."
        )
    return {"files_equal": True, "sha256": digests[0], "azure_requests_sent": False}


def prepare_hosted(
    kind: str, package: Path, name: str, run: str, *, language: str = "ko"
) -> dict:
    if language not in {"ko", "en"}:
        raise SetupError("언어는 ko 또는 en을 명시하세요.")
    state = read_state()
    validate_runtime_environment(os.environ.copy(), explicit_model=False)
    if kind not in {"runtime", "matrix", "toolbox"}:
        raise SetupError("지원하는 실행 방식은 runtime, matrix, toolbox입니다.")
    for value in (name, run):
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,31}", value):
            raise SetupError("이름과 run은 소문자·숫자·하이픈 1~32자로 입력하세요.")
    package = package.resolve()
    if not package.is_relative_to((ROOT / ".build").resolve()) or not package.is_dir():
        raise SetupError("이 폴더의 .build 아래에서 생성한 패키지를 사용하세요.")
    service = state["prefix"] + "-" + name
    directory = ROOT / ".selfstudy" / (service + "-" + run)
    if directory.exists():
        raise SetupError(
            "이미 준비한 폴더는 덮어쓰지 않습니다. 기존 결과를 읽거나 새 --run을 사용하세요."
        )
    environment = os.environ.copy()
    if kind == "matrix":
        environment["WORKSHOP_HOSTED_AGENT_NAME"] = service
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/prepare_hosted_azd.py"),
            "--language",
            language,
            "--kind",
            kind,
            "--package",
            str(package),
            "--directory",
            str(directory),
            "--agent-name",
            service,
            "--initialize-env",
            "--project-id",
            state["project_id"],
            "--location",
            state["location"],
        ],
        cwd=ROOT,
        check=True,
        timeout=180,
        env=environment,
    )
    manifest = json.loads((directory / "azure.yaml").read_text(encoding="utf-8"))
    if (
        manifest.get("name") != service
        or set(manifest.get("services", {})) != {"workshop-project", service}
        or manifest["services"]["workshop-project"].get("endpoint") != state["endpoint"]
    ):
        raise SetupError("생성된 Hosted 폴더가 요청한 서비스/프로젝트와 일치하지 않습니다.")
    return {
        "service": service,
        "directory": str(directory),
        "azure_deployed": False,
        "language": language,
        "next_commands": [
            f'azd deploy "{service}" --cwd "{directory}"',
            f'azd ai agent show "{service}" --cwd "{directory}" --output json',
        ],
    }


def bind_matrix(directory: Path, service: str) -> dict:
    from foundry_workshop.bindings import hosted_binding

    state = read_state()
    validate_runtime_environment(os.environ.copy(), explicit_model=False)
    directory = directory.resolve()
    if (
        not directory.is_relative_to((ROOT / ".selfstudy").resolve())
        or not (directory / "azure.yaml").is_file()
    ):
        raise SetupError(".selfstudy 아래에서 준비한 실제 matrix 폴더를 지정하세요.")
    executable = shutil.which("azd")
    if not executable:
        raise SetupError("azd와 microsoft.foundry 확장이 필요합니다.")
    received = subprocess.run(
        [executable, "env", "get-values", "--output", "json", "--cwd", str(directory)],
        capture_output=True,
        text=True,
        check=True,
        timeout=90,
    )
    values = json.loads(received.stdout)
    if not isinstance(values, dict) or values.get("AZURE_AI_PROJECT_ENDPOINT") != state["endpoint"]:
        raise SetupError("azd 환경이 현재 실습 프로젝트와 다릅니다.")
    result = hosted_binding(values, state["endpoint"], state["prefix"], service)
    shown = subprocess.run(
        [executable, "ai", "agent", "show", service, "--cwd", str(directory), "--output", "json"],
        capture_output=True,
        text=True,
        check=True,
        timeout=90,
    )
    actual = json.loads(shown.stdout)
    if (
        actual.get("name") != service
        or str(actual.get("version")) != result["WORKSHOP_HOSTED_AGENT_VERSION"]
        or actual.get("status") not in {"active", "deployed"}
    ):
        raise SetupError("azd 환경의 버전과 실제 활성 agent 버전이 다릅니다.")
    update_env(result)
    state.setdefault("hosted_bindings", {})[service] = {
        **result,
        "directory": str(directory),
        "captured_at": datetime.now(UTC).isoformat(),
    }
    save_state(state)
    return {
        "binding": result,
        "instance_identity": actual.get("instance_identity"),
        "model_invoked": False,
        "note": "Actual version and Invocations endpoint were read and saved; no URL was guessed.",
    }


def resource_record(value: dict, kind: str) -> dict:
    if not isinstance(value.get("id"), str):
        raise SetupError("Azure 리소스 응답에 실제 ID가 없습니다.")
    identity = value.get("identity") or {}
    properties = value.get("properties") or {}
    return {
        "id": value["id"],
        "kind": kind,
        "type": value.get("type"),
        "name": value.get("name"),
        "location": value.get("location"),
        "principal_id": identity.get("principalId"),
        "app_id": properties.get("AppId") or properties.get("appId"),
        "captured_at": datetime.now(UTC).isoformat(),
    }


def validate_model(value: dict, name: str, version: str | None) -> dict:
    properties = value.get("properties") or {}
    model = properties.get("model") or {}
    if properties.get("provisioningState") != "Succeeded":
        raise SetupError("모델 배포가 Succeeded가 아닙니다. 생성 완료/할당량을 확인하세요.")
    if model.get("name") != name or (version and model.get("version") != version):
        raise SetupError(
            f"필요한 모델은 {name}"
            + (f" / {version}" if version else "")
            + f"입니다. 실제 배포는 {model.get('name')} / {model.get('version')}입니다. "
            "기존 배포 이름만 바꾸지 말고 포털에서 실제 기반 모델을 확인하세요."
        )
    return model


def inspect_model(role: str, deployment: str | None) -> dict:
    state = read_state()
    spec = MODEL_ROLES[role]
    deployment = deployment or spec["deployment"]
    actual = az_json(
        "cognitiveservices",
        "account",
        "deployment",
        "show",
        "--name",
        state["account"],
        "--resource-group",
        state["group"],
        "--deployment-name",
        deployment,
        "--subscription",
        state["subscription"],
    )
    model = validate_model(actual, spec["model"], spec["version"])
    if spec["environment"]:
        update_env({spec["environment"]: deployment})
    state.setdefault("model_roles", {})[role] = {
        "deployment": deployment,
        "model": model,
        "captured_at": datetime.now(UTC).isoformat(),
    }
    if role == "answer":
        state["deployment_at_capture"] = model
    save_state(state)
    return {
        "role": role,
        "deployment": deployment,
        "model": model,
        "management_metadata_read": True,
        "model_invoked": False,
    }


def configure(
    project_id: str,
    endpoint: str,
    deployment: str,
    prefix: str,
    expected_model: str = PRIMARY_MODEL,
) -> dict:
    verify_runtime()
    parsed = parse_project_id(project_id)
    endpoint = validate_endpoint(endpoint, "project")
    if (
        unquote(urlsplit(endpoint).path.rsplit("/", 1)[1]).casefold()
        != parsed["project"].casefold()
    ):
        raise SetupError("프로젝트 ARM ID와 Endpoint의 프로젝트 이름이 다릅니다.")
    if not re.fullmatch(r"lab-[a-z0-9]+(?:-[a-z0-9]+)*", prefix) or len(prefix) > 32:
        raise SetupError("고유한 lab-접두사(소문자·숫자·하이픈, 최대 32자)를 사용하세요.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", deployment):
        raise SetupError("실제 모델 배포 이름을 입력하세요.")
    previous = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else None
    if previous and (
        previous["project_id"].casefold() != parsed["project_id"].casefold()
        or previous["prefix"] != prefix
    ):
        raise SetupError(
            "다른 프로젝트/접두사의 기존 설정을 덮어쓰지 않습니다. 별도 실습 폴더를 사용하세요."
        )

    subscription = az_json("account", "show", "--subscription", parsed["subscription"])
    if subscription.get("id", "").casefold() != parsed["subscription"].casefold():
        raise SetupError("Azure CLI가 요청한 구독과 다른 구독을 반환했습니다.")
    tenant = uuid_value(subscription["tenantId"])
    if subscription.get("user", {}).get("type") != "user":
        raise SetupError(
            "이 자가 실습은 본인의 Entra 사용자 로그인으로 시작합니다. 서비스 principal 로그인과 섞지 마세요."
        )
    project = az_json("resource", "show", "--ids", parsed["project_id"])
    account = az_json("resource", "show", "--ids", parsed["account_id"])
    if (
        project["id"].casefold() != parsed["project_id"].casefold()
        or account["id"].casefold() != parsed["account_id"].casefold()
    ):
        raise SetupError("조회한 Azure 리소스와 요청한 대상이 다릅니다.")
    domain = (account.get("properties") or {}).get("customSubDomainName")
    if not domain or urlsplit(endpoint).hostname != f"{domain}.services.ai.azure.com":
        raise SetupError(
            "프로젝트 Endpoint가 조회한 Foundry 리소스의 customSubDomainName과 일치하지 않습니다."
        )
    model = az_json(
        "cognitiveservices",
        "account",
        "deployment",
        "show",
        "--name",
        parsed["account"],
        "--resource-group",
        parsed["group"],
        "--deployment-name",
        deployment,
        "--subscription",
        parsed["subscription"],
    )
    validate_model(model, expected_model, PRIMARY_VERSION)
    identity = {
        "AZURE_SUBSCRIPTION_ID": parsed["subscription"],
        "AZURE_TENANT_ID": tenant,
        "AZURE_RESOURCE_GROUP": parsed["group"],
        "AZURE_AI_ACCOUNT_NAME": parsed["account"],
        "AZURE_AI_PROJECT_ENDPOINT": endpoint,
        "WORKSHOP_PREFIX": prefix,
        "WORKSHOP_AUTH_MODE": "cli",
    }
    existing = env_values() if ENV.exists() else {}
    for key, value in identity.items():
        if existing.get(key) and existing[key] != value:
            raise SetupError(f"{key}: 기존 .env의 다른 실습 설정을 덮어쓰지 않습니다.")
    updates = {**identity, "AZURE_AI_MODEL_DEPLOYMENT_NAME": deployment}
    if not existing.get("WORKSHOP_MAX_OUTPUT_TOKENS"):
        updates["WORKSHOP_MAX_OUTPUT_TOKENS"] = str(DEFAULT_MAX_OUTPUT_TOKENS)
    if not existing.get("WORKSHOP_REASONING_EFFORT"):
        updates["WORKSHOP_REASONING_EFFORT"] = DEFAULT_REASONING_EFFORT
    state = {
        "schema_version": 1,
        "workshop_version": "1.5",
        **parsed,
        "endpoint": endpoint,
        "custom_subdomain": domain,
        "prefix": prefix,
        "identity_env": identity,
        "location": project.get("location"),
        "deployment_at_capture": model.get("properties", {}).get("model"),
        "model_roles": dict(previous.get("model_roles", {})) if previous else {},
        "resources": dict(previous["resources"]) if previous else {},
        "management_metadata_read": True,
        "model_invoked": False,
    }
    for value, kind in ((project, "project"), (account, "foundry")):
        record = resource_record(value, kind)
        state["resources"][record["id"].casefold()] = record
    update_env(updates)
    save_state(state)
    return state


def set_value(key: str, value: str) -> None:
    state = read_state()
    if key not in MUTABLE_KEYS:
        raise SetupError(
            "이 키는 변경할 수 없습니다. 비밀 값·구독·프로젝트·접두사는 set 대상이 아닙니다."
        )
    if key == "AZURE_OPENAI_ENDPOINT":
        value = validate_endpoint(value, "openai")
        if urlsplit(value).hostname != f"{state['custom_subdomain']}.openai.azure.com":
            raise SetupError("같은 Foundry 계정의 OpenAI Endpoint만 사용하세요.")
    elif key == "WORKSHOP_EMBEDDING_DIMENSIONS":
        if not value.isdigit() or not 1 <= int(value) <= 65536:
            raise SetupError("실제 embedding 차원을 양의 정수로 입력하세요.")
    elif key == "WORKSHOP_EMBEDDING_API" and value not in {"account", "project"}:
        raise SetupError("embedding API는 account 또는 project를 명시하세요.")
    elif key == "WORKSHOP_MAX_OUTPUT_TOKENS":
        if not value.isdigit() or not 256 <= int(value) <= MAX_OUTPUT_TOKENS:
            raise SetupError(f"출력 토큰 한도는 256~{MAX_OUTPUT_TOKENS}입니다.")
    elif key == "WORKSHOP_REASONING_EFFORT" and value not in REASONING_EFFORTS:
        raise SetupError("Reasoning은 none, low, medium, high 중에서 명시하세요.")
    elif key == "WORKSHOP_IQ_RERANKER_THRESHOLD":
        threshold = float(value)
        if not math.isfinite(threshold) or not 0 <= threshold <= 4:
            raise SetupError("IQ 검색 필터는 유한한 0~4 값이어야 합니다.")
    elif key == "WORKSHOP_MEMORY_STORE_NAME":
        if not re.fullmatch(r"[a-z0-9-]{1,100}", value) or not value.startswith(
            state["prefix"] + "-"
        ):
            raise SetupError("Memory 저장소는 현재 실습 접두사 아래의 고유한 이름이어야 합니다.")
    elif key == "WORKSHOP_MODEL_DEPLOYMENTS_JSON":
        models = json.loads(value)
        if (
            not isinstance(models, dict)
            or not models
            or not all(
                isinstance(k, str) and isinstance(v, str) and v.strip() for k, v in models.items()
            )
        ):
            raise SetupError("모델 map은 별칭과 실제 배포 이름으로 된 JSON 객체여야 합니다.")
        if env_values()["AZURE_AI_MODEL_DEPLOYMENT_NAME"] not in models.values():
            raise SetupError("모델 map에 현재 기본 배포를 포함하세요.")
    update_env({key: value})


def register_resource(kind: str, resource_id: str, endpoint: str | None) -> dict:
    state = read_state()
    if not resource_id.casefold().startswith(
        f"/subscriptions/{state['subscription']}/resourcegroups/".casefold()
    ):
        raise SetupError("현재 실습 구독의 리소스만 등록합니다.")
    value = az_json("resource", "show", "--ids", resource_id)
    if (
        value["id"].casefold() != resource_id.casefold()
        or value.get("type", "").casefold() != RESOURCE_TYPES[kind]
    ):
        raise SetupError("조회한 리소스 ID 또는 종류가 요청한 대상과 다릅니다.")
    record = resource_record(value, kind)
    updates = {}
    if kind == "search":
        if not endpoint:
            raise SetupError("Search Overview에서 복사한 --endpoint가 필요합니다.")
        endpoint = validate_endpoint(endpoint, "search")
        if urlsplit(endpoint).hostname != f"{value['name']}.search.windows.net":
            raise SetupError("Search 리소스 이름과 Endpoint가 다릅니다.")
        existing = env_values().get("AZURE_SEARCH_ENDPOINT")
        if existing and existing != endpoint:
            raise SetupError("기존 Search 소유권 기록과 섞지 않도록 서비스 변경을 거부합니다.")
        updates = {
            "AZURE_SEARCH_ENDPOINT": endpoint,
            "AZURE_SEARCH_RESOURCE_GROUP": resource_id.split("/")[4],
        }
        record["endpoint"] = endpoint
    elif kind == "insights":
        if not record["app_id"]:
            raise SetupError("Application Insights 응답에 AppId가 없습니다.")
        updates["AZURE_APPLICATION_INSIGHTS_APP_ID"] = uuid_value(record["app_id"])
    elif kind == "logs":
        customer_id = (value.get("properties") or {}).get("customerId")
        if not customer_id:
            raise SetupError("Log Analytics 응답에 실제 customerId가 없습니다.")
        updates["AZURE_LOG_ANALYTICS_WORKSPACE_ID"] = uuid_value(customer_id)
        updates["AZURE_AI_PROJECT_ID"] = state["project_id"]
    if updates:
        update_env(updates)
    state["resources"][record["id"].casefold()] = record
    save_state(state)
    return record


def role_plan(user_id: str, hosted_id: str | None = None) -> dict:
    state = read_state()
    user_id = uuid_value(user_id)
    rows = []
    pending = []

    def add(principal: str | None, principal_type: str, role: str, scope: str, reason: str) -> None:
        if not principal:
            raise SetupError(
                f"{reason}: 관리 ID가 없습니다. 해당 리소스의 Identity를 켜고 다시 등록하세요."
            )
        principal = uuid_value(principal)
        rows.append(
            {
                "principal": principal,
                "principal_type": principal_type,
                "role": role,
                "scope": scope,
                "reason": reason,
                "command": (
                    f'az role assignment create --assignee-object-id "{principal}" '
                    f'--assignee-principal-type "{principal_type}" --role "{ROLE_IDS[role]}" '
                    f'--scope "{scope}" --subscription "{state["subscription"]}"'
                ),
            }
        )

    add(
        user_id,
        "User",
        "Foundry User",
        state["account_id"],
        "내 모델·agent 데이터 작업",
    )
    project = state["resources"][state["project_id"].casefold()]
    account = state["resources"][state["account_id"].casefold()]
    add(
        project["principal_id"],
        "ServicePrincipal",
        "Foundry User",
        state["account_id"],
        "프로젝트 서비스의 모델·agent 호출",
    )
    for item in state["resources"].values():
        if item["kind"] == "search":
            add(
                user_id,
                "User",
                "Search Index Data Contributor",
                item["id"],
                "내 합성 문서 읽기/쓰기; 관리 작업은 기존 Owner",
            )
            add(
                project["principal_id"],
                "ServicePrincipal",
                "Search Index Data Reader",
                item["id"],
                "고정 Toolbox의 프로젝트 관리 ID 검색",
            )
            add(
                project["principal_id"],
                "ServicePrincipal",
                "Search Service Contributor",
                item["id"],
                "고정 Toolbox의 스키마 접근; 실습 Search에만 허용",
            )
            add(
                item["principal_id"],
                "ServicePrincipal",
                "Cognitive Services User",
                state["account_id"],
                "IQ Chat의 Search 관리 ID 모델 호출",
            )
            if account["principal_id"]:
                add(
                    account["principal_id"],
                    "ServicePrincipal",
                    "Search Index Data Reader",
                    item["id"],
                    "직접 OpenAPI의 Foundry 계정 관리 ID 검색",
                )
            else:
                pending.append(
                    "OpenAPI: Foundry 계정의 system-assigned identity를 켜고 configure로 다시 조회하세요."
                )
        elif item["kind"] in {"insights", "logs"}:
            add(user_id, "User", "Log Analytics Reader", item["id"], "내 trace 조회")
            if item["kind"] == "insights":
                add(
                    project["principal_id"],
                    "ServicePrincipal",
                    "Monitoring Reader",
                    item["id"],
                    "Insights 분석을 위한 프로젝트 관리 ID의 telemetry 조회",
                )
    if hosted_id:
        add(
            hosted_id,
            "ServicePrincipal",
            "Foundry User",
            state["project_id"],
            "실제로 배포한 Hosted 런타임",
        )
        for item in state["resources"].values():
            if item["kind"] == "search":
                add(
                    hosted_id,
                    "ServicePrincipal",
                    "Search Index Data Reader",
                    item["id"],
                    "Hosted의 합성 검색",
                )
    return {
        "mode": "plan-only",
        "role_assignments_executed": False,
        "assignments": rows,
        "pending": pending,
    }


def capture_hosted(
    directory: Path,
    service: str,
    version: str,
    output: Path,
    confirmed: bool,
    *,
    language: str = "ko",
) -> dict:
    if language not in {"ko", "en"}:
        raise SetupError("언어는 ko 또는 en을 명시하세요.")
    if not confirmed:
        raise SetupError("실제 모델/도구 호출입니다. 검토 후 --confirm-cost를 명시하세요.")
    state = read_state()
    directory = directory.resolve()
    output = output.resolve()
    private_root = (ROOT / ".selfstudy").resolve()
    if not directory.is_relative_to(private_root) or not (directory / "azure.yaml").is_file():
        raise SetupError(".selfstudy 아래에 준비한 독립 Hosted 프로젝트만 사용하세요.")
    if (
        not output.is_relative_to(private_root)
        or output.exists()
        or output.with_suffix(".stderr.txt").exists()
    ):
        raise SetupError(".selfstudy 아래의 아직 없는 새 출력 파일을 사용하세요.")
    if not service.startswith(state["prefix"] + "-") or not version.strip():
        raise SetupError("본인 prefix의 서비스와 실제 버전을 명시하세요.")
    executable = shutil.which("azd")
    if not executable:
        raise SetupError("azd와 microsoft.foundry 확장을 먼저 설치하세요.")
    environment = os.environ.copy()
    validate_runtime_environment(environment, explicit_model=False)
    for key in ("FOUNDRY_PROJECT_ENDPOINT", "AZURE_AIPROJECT_ENDPOINT"):
        if environment.get(key) and environment[key] != state["endpoint"]:
            raise SetupError(f"{key}: 다른 Foundry 대상의 셸 설정을 제거하세요.")
    environment["FOUNDRY_PROJECT_ENDPOINT"] = state["endpoint"]
    environment["AZURE_AI_PROJECT_ENDPOINT"] = state["endpoint"]
    endpoint = (
        subprocess.run(
            [
                executable,
                "env",
                "get-value",
                "AZURE_AI_PROJECT_ENDPOINT",
                "--cwd",
                str(directory),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
            env=environment,
        )
        .stdout.strip()
        .strip('"')
    )
    if endpoint != state["endpoint"]:
        raise SetupError("Hosted 프로젝트가 현재 실습과 다른 Foundry를 가리킵니다.")
    shown = subprocess.run(
        [
            executable,
            "ai",
            "agent",
            "show",
            service,
            "--cwd",
            str(directory),
            "--output",
            "json",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=90,
        env=environment,
    )
    actual = json.loads(shown.stdout)
    if (
        actual.get("name") != service
        or str(actual.get("version")) != version
        or actual.get("status") not in {"active", "deployed"}
    ):
        raise SetupError("요청한 실제 활성 서비스/버전과 조회 결과가 다릅니다.")
    question = (
        "What advance approval is needed for a KRW 170000 hotel on a domestic business trip in September 2026?"
        if language == "en"
        else "2026년 9월 국내 출장에서 170000원 호텔의 사전 승인 조건은?"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        completed = subprocess.run(
            [
                executable,
                "ai",
                "agent",
                "invoke",
                service,
                "--cwd",
                str(directory),
                "--version",
                version,
                "--new-session",
                "--new-conversation",
                "--output",
                "raw",
                "--timeout",
                "240",
                question,
            ],
            capture_output=True,
            check=False,
            timeout=300,
            env=environment,
        )
    except subprocess.TimeoutExpired as exc:
        output.write_bytes(exc.stdout or b"")
        output.with_suffix(".stderr.txt").write_bytes(exc.stderr or b"")
        raise SetupError(f"호출 시간 초과의 부분 bytes를 보관했습니다: {output}") from exc
    output.write_bytes(completed.stdout)
    output.with_suffix(".stderr.txt").write_bytes(completed.stderr)
    if completed.returncode:
        raise SetupError(f"호출 실패를 원본 bytes로 보관했습니다: {output}")
    return {
        "mode": "captured-not-verified",
        "raw_file": str(output),
        "agent": service,
        "version": version,
        "agent_response_verified": False,
        "language": language,
    }


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="자가 실습 설정/읽기. capture만 --confirm-cost 후 실제 추론 수행"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    config = commands.add_parser("configure", help="포털에서 만든 프로젝트/배포를 읽고 설정 기록")
    config.add_argument("--project-id", required=True)
    config.add_argument("--endpoint", required=True)
    config.add_argument("--deployment", default="workshop-chat")
    config.add_argument("--prefix", required=True)
    config.add_argument(
        "--expected-model", choices=("gpt-6-luna", "gpt-6-sol"), default=PRIMARY_MODEL
    )
    model = commands.add_parser("model", help="역할에 맞는 실제 모델/버전을 읽고 연결 설정")
    model.add_argument("--role", choices=MODEL_ROLES, required=True)
    model.add_argument("--deployment")
    commands.add_parser("status", help="기록한 설정/자원 표시; Azure 현재 상태 조회가 아님")
    commands.add_parser("values", help="다음 명령에 복사할 핵심 설정만 표시")
    setting = commands.add_parser("set", help="허용된 비밀 아닌 SDK 설정만 변경")
    setting.add_argument("key", choices=sorted(MUTABLE_KEYS))
    setting.add_argument("value")
    models = commands.add_parser("models", help="JSON 셸 escaping 없이 모델 map 설정")
    models.add_argument("pairs", nargs="+", help="primary=실제배포 comparison=다른배포")
    comparison = commands.add_parser("compare-files", help="실습 내 원본/readback bytes 비교")
    comparison.add_argument("first", type=Path)
    comparison.add_argument("second", type=Path)
    hosted = commands.add_parser("prepare-hosted", help="저장한 Azure 값으로 독립 Hosted 폴더 준비")
    hosted.add_argument("--kind", choices=("runtime", "matrix", "toolbox"), default="runtime")
    hosted.add_argument("--package", type=Path, required=True)
    hosted.add_argument("--name", required=True, help="접두사 뒤에 붙일 짧은 이름")
    hosted.add_argument("--run", default="default", help="같은 서비스의 새 준비 폴더 구분")
    hosted.add_argument("--language", choices=("ko", "en"), default="ko")
    bind = commands.add_parser(
        "bind-matrix", help="실제 활성 matrix 버전·Invocations Endpoint를 읽어 저장"
    )
    bind.add_argument("--directory", type=Path, required=True)
    bind.add_argument("--service", required=True)
    resource = commands.add_parser("resource", help="직접 만든 추가 자원을 읽어 등록")
    resource.add_argument("--kind", choices=RESOURCE_TYPES, required=True)
    resource.add_argument("--id", required=True)
    resource.add_argument("--endpoint")
    roles = commands.add_parser("roles", help="역할 명령 생성만; 직접 검토 후 필요한 항목만 실행")
    roles.add_argument("--user-object-id", required=True)
    roles.add_argument("--hosted-principal-id")
    capture = commands.add_parser("capture", help="검토한 Hosted 버전을 호출하고 raw bytes 보존")
    capture.add_argument("--directory", type=Path, required=True)
    capture.add_argument("--service", required=True)
    capture.add_argument("--version", required=True)
    capture.add_argument("--output", type=Path, required=True)
    capture.add_argument("--confirm-cost", action="store_true")
    capture.add_argument("--language", choices=("ko", "en"), default="ko")
    return parser


def main() -> None:
    args = argument_parser().parse_args()
    if args.command == "configure":
        result = configure(
            args.project_id, args.endpoint, args.deployment, args.prefix, args.expected_model
        )
    elif args.command == "model":
        result = inspect_model(args.role, args.deployment)
    elif args.command == "values":
        state = read_state()
        values = env_values()
        result = {
            "접두사": state["prefix"],
            "프로젝트 Endpoint": state["endpoint"],
            "프로젝트 ARM ID": state["project_id"],
            "리전 코드": state["location"],
            "기본 모델 배포": values["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            "확인한 모델": state.get("deployment_at_capture"),
            "Reasoning": values.get("WORKSHOP_REASONING_EFFORT", DEFAULT_REASONING_EFFORT),
            "출력 토큰 한도": values.get(
                "WORKSHOP_MAX_OUTPUT_TOKENS", str(DEFAULT_MAX_OUTPUT_TOKENS)
            ),
            "기본 agent 이름": state["prefix"] + "-policy-ko",
            "agent 버전": "생성 후 outputs/agents/에서 확인",
            "Search Endpoint": values.get("AZURE_SEARCH_ENDPOINT", "아직 연결하지 않음"),
            "결과 폴더": str(ROOT / "outputs"),
        }
    elif args.command == "status":
        state = read_state()
        visible_keys = (
            MUTABLE_KEYS
            | set(state["identity_env"])
            | {
                "AZURE_SEARCH_ENDPOINT",
                "AZURE_SEARCH_RESOURCE_GROUP",
                "AZURE_APPLICATION_INSIGHTS_APP_ID",
                "AZURE_LOG_ANALYTICS_WORKSPACE_ID",
                "AZURE_AI_PROJECT_ID",
            }
        )
        result = {
            "captured_context": state,
            "sdk_settings": {
                key: value for key, value in env_values().items() if key in visible_keys
            },
            "azure_requests_sent": False,
        }
    elif args.command == "set":
        set_value(args.key, args.value)
        result = {
            "updated": args.key,
            "azure_requests_sent": False,
            "env_file": str(ENV),
        }
    elif args.command == "models":
        set_models(args.pairs)
        result = {
            "updated": "WORKSHOP_MODEL_DEPLOYMENTS_JSON",
            "azure_requests_sent": False,
        }
    elif args.command == "compare-files":
        result = compare_files(args.first, args.second)
    elif args.command == "prepare-hosted":
        result = prepare_hosted(
            args.kind, args.package, args.name, args.run, language=args.language
        )
        if args.language == "en":
            print(f"Service: {result['service']}\nDirectory: {result['directory']}")
            print("Not deployed to Azure. Review the target and cost before running these commands.")
        else:
            print(f"서비스: {result['service']}\n폴더: {result['directory']}")
            print("아직 Azure에 배포하지 않았습니다. 대상과 비용을 확인한 뒤 다음 명령을 실행하세요.")
        for command in result["next_commands"]:
            print(command)
        return
    elif args.command == "bind-matrix":
        result = bind_matrix(args.directory, args.service)
    elif args.command == "capture":
        result = capture_hosted(
            args.directory,
            args.service,
            args.version,
            args.output,
            args.confirm_cost,
            language=args.language,
        )
    elif args.command == "resource":
        result = register_resource(args.kind, args.id, args.endpoint)
    else:
        result = role_plan(args.user_object_id, args.hosted_principal_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (
        SetupError,
        OSError,
        ValueError,
        KeyError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
