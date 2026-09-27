#!/usr/bin/env python3
import importlib
import importlib.metadata
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def check() -> tuple[dict, list[str]]:
    configuration = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    expected = {}
    for extra in ("cloud", "agents", "hosted"):
        for requirement in configuration["project"]["optional-dependencies"][extra]:
            if requirement.startswith(configuration["project"]["name"] + "["):
                continue
            name, separator, pinned = requirement.partition("==")
            if not separator:
                raise ValueError(f"Unpinned SDK requirement: {requirement}")
            expected[name] = pinned
    installed = {}
    errors = []
    for name, pinned in expected.items():
        try:
            installed[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            installed[name] = None
        if installed[name] != pinned:
            errors.append(f"{name}: expected {pinned}, installed {installed[name]}")
    imports = {
        "azure.ai.projects": ["AIProjectClient"],
        "azure.ai.projects.models": [
            "PromptAgentDefinition",
            "TestingCriterionAzureAIEvaluator",
            "A2ATool",
            "A2AProtocolVersion",
            "AgentCard",
            "AgentCardSkill",
            "AgentEndpointConfig",
            "ProtocolConfiguration",
            "ResponsesProtocolConfiguration",
            "A2AProtocolConfiguration",
        ],
        "openai": ["OpenAI", "AsyncOpenAI"],
        "httpx2": ["Client", "AsyncClient", "MockTransport"],
        "agent_framework": ["Agent", "tool", "MCPStdioTool"],
        "agent_framework.foundry": ["FoundryChatClient"],
        "agent_framework.orchestrations": [
            "SequentialBuilder",
            "ConcurrentBuilder",
            "GroupChatBuilder",
        ],
        "agent_framework_foundry_hosting": ["ResponsesHostServer"],
        "mcp.server.fastmcp": ["FastMCP"],
    }
    for module_name, symbols in imports.items():
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            errors.append(f"{module_name}: {type(exc).__name__}")
            continue
        for name in symbols:
            if not hasattr(module, name):
                errors.append(f"{module_name}.{name}: missing SDK surface")
    return {
        "python": sys.version.split()[0],
        "expected": expected,
        "installed": installed,
        "azure_requests_sent": False,
        "passed": not errors,
    }, errors


if __name__ == "__main__":
    report, failures = check()
    print(json.dumps(report, indent=2))
    for failure in failures:
        print("FAIL:", failure, file=sys.stderr)
    raise SystemExit(1 if failures else 0)
