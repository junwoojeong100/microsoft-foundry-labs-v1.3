from __future__ import annotations

import json
import subprocess
import sys

from v12 import main

if __name__ == "__main__":
    try:
        raise SystemExit(main(managed=True))
    except (
        OSError,
        RuntimeError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
