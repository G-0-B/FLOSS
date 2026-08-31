"""Fake stdio MCP server used to test agentmemory_client.py in isolation.

Speaks just enough newline-delimited JSON-RPC 2.0 over stdin/stdout to stand
in for `@agentmemory/mcp`'s real `initialize` + `tools/call` exchange,
without ever touching a live agentmemory instance.

Mode is selected via the AGENTMEMORY_FAKE_MODE env var:
    ok          - normal initialize + tools/call responses (default)
    malformed   - the tools/call "response" is not valid JSON
    hang        - never responds to tools/call (client must time out and
                  kill this process)
    no_init     - never responds to initialize either
"""

from __future__ import annotations

import json
import os
import sys
import time

MODE = os.environ.get("AGENTMEMORY_FAKE_MODE", "ok")


def _send(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _fake_save_result(arguments: dict) -> dict:
    inner = json.dumps(
        {
            "memory": {
                "id": "mem_fake_0001",
                "content": arguments.get("content", ""),
                "concepts": (
                    (arguments.get("concepts") or "").split(",")
                    if arguments.get("concepts")
                    else []
                ),
            },
            "success": True,
        }
    )
    return {"content": [{"type": "text", "text": inner}]}


def _fake_recall_result() -> dict:
    inner = json.dumps(
        {
            "format": "full",
            "results": [
                {
                    "observation": {"narrative": "fake recalled memory one"},
                    "score": 9.1,
                },
                {
                    "observation": {"facts": ["fake recalled fact two"]},
                    "score": 5.0,
                },
            ],
            "tokens_used": 42,
            "truncated": False,
        }
    )
    return {"content": [{"type": "text", "text": inner}]}


def main() -> None:
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw)
        except Exception:
            continue

        method = msg.get("method")
        msg_id = msg.get("id")

        if method == "initialize":
            if MODE == "no_init":
                time.sleep(120)
                continue
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {"listChanged": False}},
                        "serverInfo": {"name": "fake-agentmemory", "version": "0.0.0"},
                    },
                }
            )
        elif method == "notifications/initialized":
            continue
        elif method == "tools/call":
            if MODE == "hang":
                time.sleep(120)
                continue
            if MODE == "malformed":
                sys.stdout.write("this is not json\n")
                sys.stdout.flush()
                continue

            params = msg.get("params") or {}
            tool_name = params.get("name")
            arguments = params.get("arguments") or {}

            if MODE == "nocontent":
                # A nominal success envelope carrying no success indication:
                # no isError, and no content the caller can read.
                result = {}
            elif MODE == "toolerror":
                # A well-formed JSON-RPC RESULT that reports tool failure. Not a
                # transport error: the envelope is valid, the call failed.
                result = {
                    "content": [{"type": "text", "text": "quota exceeded"}],
                    "isError": True,
                }
            elif tool_name == "memory_save":
                result = _fake_save_result(arguments)
            elif tool_name == "memory_recall":
                result = _fake_recall_result()
            else:
                result = {"content": [], "isError": True}

            _send({"jsonrpc": "2.0", "id": msg_id, "result": result})
        else:
            continue


if __name__ == "__main__":
    main()
