import re
from urllib.parse import parse_qs, urlsplit


def hosted_binding(
    values: dict, project_endpoint: str, owned_prefix: str, service: str
) -> dict[str, str]:
    prefix = "AGENT_" + re.sub(r"[^A-Z0-9]", "_", service.upper())
    keys = {
        "WORKSHOP_HOSTED_AGENT_NAME": prefix + "_NAME",
        "WORKSHOP_HOSTED_AGENT_VERSION": prefix + "_VERSION",
        "WORKSHOP_HOSTED_AGENT_ENDPOINT": prefix + "_INVOCATIONS_ENDPOINT",
    }
    result = {target: values.get(source) for target, source in keys.items()}
    if any(
        not isinstance(value, str) or not value or "\n" in value or "\r" in value
        for value in result.values()
    ):
        raise ValueError("The actual azd name/version/Invocations binding is incomplete or unsafe.")
    if result["WORKSHOP_HOSTED_AGENT_NAME"] != service or not service.startswith(
        owned_prefix + "-"
    ):
        raise ValueError("The deployment returned another agent name.")
    if not result["WORKSHOP_HOSTED_AGENT_VERSION"].isdigit():
        raise ValueError("The deployed version must be the actual numeric version, never latest.")
    endpoint = urlsplit(result["WORKSHOP_HOSTED_AGENT_ENDPOINT"])
    project = urlsplit(project_endpoint)
    if (
        endpoint.scheme != "https"
        or endpoint.netloc != project.netloc
        or endpoint.path != project.path + f"/agents/{service}/endpoint/protocols/invocations"
        or parse_qs(endpoint.query).get("api-version") != ["v1"]
        or endpoint.fragment
    ):
        raise ValueError("The Invocations endpoint does not match the intended project and agent.")
    return result
