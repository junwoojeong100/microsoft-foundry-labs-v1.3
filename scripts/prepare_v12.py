from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = json.loads((ROOT / "v12-reference.json").read_text(encoding="utf-8"))
SOURCE = ROOT / REFERENCE["directory"]


def run(*args: str, cwd: Path = ROOT) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def verify_source() -> None:
    completed = subprocess.run(
        ["git", "-C", str(SOURCE), "rev-parse", "HEAD"],
        check=True,
        text=True,
        capture_output=True,
    )
    if completed.stdout.strip() != REFERENCE["commit"]:
        raise RuntimeError(
            "호환 소스의 커밋이 다릅니다. 기존 파일을 덮어쓰지 않고 중단합니다."
        )
    for name in (
        "LICENSE",
        "pyproject.toml",
        "scripts/workshop.py",
        "src/foundry_workshop/cli.py",
    ):
        if not (SOURCE / name).is_file():
            raise RuntimeError(
                f"호환 소스 파일이 없습니다: {name}. 기존 폴더를 보존하고 확인하세요."
            )


def prepare(install: bool) -> None:
    if shutil.which("git") is None:
        raise RuntimeError("Git이 필요합니다. 먼저 Git을 설치하세요.")
    if SOURCE.exists():
        verify_source()
        print(
            "기존 고정 커밋을 재사용합니다. 원본 소스와 개인 설정을 덮어쓰지 않습니다."
        )
    else:
        SOURCE.mkdir(parents=True)
        run("git", "init", "--quiet", str(SOURCE))
        run(
            "git", "-C", str(SOURCE), "remote", "add", "origin", REFERENCE["repository"]
        )
        run(
            "git",
            "-C",
            str(SOURCE),
            "fetch",
            "--quiet",
            "--depth=1",
            "--filter=blob:none",
            "origin",
            REFERENCE["commit"],
        )
        run(
            "git",
            "-C",
            str(SOURCE),
            "sparse-checkout",
            "set",
            "--no-cone",
            "/*",
            "!/recording/",
            "!/videos/",
            "!/docs/assets/",
        )
        run(
            "git",
            "-C",
            str(SOURCE),
            "checkout",
            "--quiet",
            "--detach",
            REFERENCE["commit"],
        )
        verify_source()
    (SOURCE / "outputs/learner-notes-ko").mkdir(parents=True, exist_ok=True)
    if install:
        python = shutil.which("python3.13")
        launcher = (
            [python] if python else ["py", "-3.13"] if shutil.which("py") else None
        )
        if launcher is None:
            raise RuntimeError(
                "v1.2 호환 SDK에는 Python 3.13을 사용합니다. 설치 후 --install을 재실행하세요."
            )
        if not (SOURCE / ".venv").exists():
            run(*launcher, "-m", "venv", str(SOURCE / ".venv"))
        executable = (
            SOURCE
            / ".venv"
            / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        )
        version = subprocess.run(
            [
                str(executable),
                "-c",
                "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if version != "3.13":
            raise RuntimeError(
                "호환 소스의 기존 .venv가 Python 3.13이 아닙니다. 자동 교체하지 않습니다."
            )
        run(
            str(executable),
            "-m",
            "pip",
            "install",
            "--quiet",
            "-e",
            ".[hosted,dev]",
            cwd=SOURCE,
        )
        run(str(executable), "-m", "pip", "check", cwd=SOURCE)
    print(f"v1.2 기능 소스: {SOURCE}")
    print(f"기준 커밋: {REFERENCE['commit']}")
    print("Azure 호출·리소스 생성·인증정보 복사는 수행하지 않았습니다.")
    print(
        "다음: docs/00-setup.md에서 같은 실습 가상 환경을 활성화하고 계정·프로젝트 준비를 계속하세요."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="v1.2 기능 소스를 고정 커밋으로 준비. Azure 작업 없음."
    )
    parser.add_argument(
        "--install", action="store_true", help="별도 Python 3.13 환경에 v1.2 SDK도 설치"
    )
    args = parser.parse_args()
    try:
        prepare(args.install)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(
            f"ERROR: {exc}\n부분 다운로드가 있으면 {SOURCE}를 보존하고 확인하세요.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
