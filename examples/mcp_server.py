import argparse
import json
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from foundry_workshop.knowledge import local_retrieve  # noqa: E402

server = FastMCP("synthetic-policy-library")
LANGUAGE = "ko"


@server.tool()
def lookup_policy(query: str) -> str:
    """Read synthetic Hanbit travel policies. Never access real accounts or approve payments."""
    return json.dumps(local_retrieve(ROOT, query, language=LANGUAGE), ensure_ascii=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=("ko", "en"), default="ko")
    LANGUAGE = parser.parse_args().language
    server.run(transport="stdio")
