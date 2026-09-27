import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@contextmanager
def workspace():
    with tempfile.TemporaryDirectory(prefix="foundry-test-") as directory:
        root = Path(directory)
        for name in ("data", "prompts", "src", "examples"):
            shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(ROOT / "pyproject.toml", root / "pyproject.toml")
        shutil.copy2(ROOT / "LICENSE", root / "LICENSE")
        yield root
