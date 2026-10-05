"""Call one room tool over MCP and print its JSON reply.

For deployment checks and tests, so "call room_state" is a command, not a
manual step in some agent session. Works against any room version: it sends
exactly the arguments it is given.

Usage:
    python -m packages.coordination_room.client room_state
    echo {"agent_id": "a", "text": "hi"} | python -m packages.coordination_room.client room_broadcast -
    python -m packages.coordination_room.client --url http://127.0.0.1:7334/mcp room_read -
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

ROOM_URL = "http://127.0.0.1:7334/mcp"


async def call_tool(url: str, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """One short MCP session, one tool call. Raises on a tool error."""
    async with streamable_http_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, arguments)
    text = result.content[0].text if result.content else ""
    if result.isError:
        raise RuntimeError(f"{tool} failed: {text[:500]}")
    return json.loads(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--url", default=ROOM_URL)
    parser.add_argument("tool")
    parser.add_argument(
        "arguments",
        nargs="?",
        default="{}",
        help="a JSON object, or - to read one from stdin (default: {})",
    )
    options = parser.parse_args(argv)
    raw = sys.stdin.read() if options.arguments == "-" else options.arguments
    try:
        # utf-8-sig: Windows PowerShell 5.1 can put a byte-order mark on piped input.
        arguments = json.loads(raw.lstrip("\ufeff") or "{}")
        if not isinstance(arguments, dict):
            raise ValueError("arguments must be a JSON object")
        reply = asyncio.run(call_tool(options.url, options.tool, arguments))
    except Exception as exc:  # one exit path: say what failed, exit non-zero
        print(f"room call failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    # ASCII on purpose: a PowerShell caller decodes stdout with its console
    # code page, and non-ASCII text in a reply would arrive mangled.
    print(json.dumps(reply))
    return 0 if reply.get("ok", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
