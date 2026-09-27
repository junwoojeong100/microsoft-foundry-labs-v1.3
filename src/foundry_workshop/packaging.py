import hashlib
import shutil
import tomllib
from pathlib import Path


def runtime_dependencies(root: Path) -> tuple[str, list[str]]:
    configuration = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = []
    for extra in ("cloud", "agents", "hosted"):
        for requirement in configuration["project"]["optional-dependencies"][extra]:
            if requirement.startswith(configuration["project"]["name"] + "["):
                continue
            if "==" not in requirement:
                raise ValueError(f"Direct hosted dependency is not pinned: {requirement}")
            if requirement not in dependencies:
                dependencies.append(requirement)
    return configuration["project"]["version"], dependencies


def copy_runtime(root: Path, destination: Path) -> None:
    shutil.copytree(
        root / "src/foundry_workshop",
        destination / "foundry_workshop",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    shutil.copytree(root / "data/knowledge", destination / "data/knowledge")
    shutil.copytree(root / "prompts", destination / "prompts")
    shutil.copy2(root / "LICENSE", destination / "LICENSE")


def file_hashes(directory: Path) -> dict[str, str]:
    return {
        path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }
