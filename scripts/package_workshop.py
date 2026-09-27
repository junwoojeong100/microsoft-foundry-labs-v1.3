from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = (
    "README.md",
    "curriculum.json",
    "LICENSE",
    "pyproject.toml",
    "requirements.lock.txt",
    ".gitignore",
    ".env.example",
    "requirements.txt",
)
DIRECTORIES = (
    "docs",
    "scripts",
    "src",
    "examples",
    "worksheets",
    "tests",
    "tests_sdk",
    "data",
    "prompts",
    ".github",
)
ALLOWED_SUFFIXES = {
    ".md",
    ".py",
    ".txt",
    ".json",
    ".jsonl",
    ".svg",
    ".csv",
    ".yaml",
    ".yml",
}


def input_files() -> list[Path]:
    files = [ROOT / name for name in ROOT_FILES]
    for directory in DIRECTORIES:
        files.extend(
            path
            for path in (ROOT / directory).rglob("*")
            if path.is_file()
            and (path.suffix in ALLOWED_SUFFIXES or path.name == ".agentignore")
            and not any(
                (part.startswith(".") and part not in {".github", ".agentignore"})
                or part == "__pycache__"
                for part in path.relative_to(ROOT).parts
            )
        )
    for path in files:
        if (
            not path.is_file()
            or path.is_symlink()
            or not path.resolve().is_relative_to(ROOT.resolve())
        ):
            raise ValueError(f"Bundle input is missing, linked or outside the workshop: {path}")
    return sorted(set(files))


def build(output: Path) -> Path:
    output = output.resolve()
    if not output.is_relative_to((ROOT / "dist").resolve()):
        raise ValueError("Only an output inside this workshop's dist/ is allowed.")
    if output.exists():
        raise FileExistsError("The bundle already exists. Preserve it and choose a new filename.")
    files = input_files()
    manifest = {
        "workshop_version": "1.5",
        "pacing": "self-paced",
        "package": tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
            "name"
        ],
        "runtime_included": True,
        "runtime_download_required": False,
        "excluded": [
            ".git",
            ".reference",
            ".venv",
            ".env",
            ".selfstudy",
            ".lab",
            "outputs",
            "dist",
        ],
        "files": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "x", compression=ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, "microsoft-foundry-v1.5-labs/" + path.relative_to(ROOT).as_posix())
        archive.writestr(
            "microsoft-foundry-v1.5-labs/bundle-manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        )
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build a learner ZIP without credentials, environments or execution records."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist/microsoft-foundry-v1.5-standalone.zip",
    )
    args = parser.parse_args()
    print(build(args.output))
