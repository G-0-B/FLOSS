"""Grok SessionStart: register the session with agentmemory. Stdout unused.

Official Grok Build docs (10-hooks.md, 2026-08-30): SessionStart stdout is
ignored. This hook only POSTs /agentmemory/session/start so later captures
attach to the right session. Fail-open, never block startup.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

REST = os.environ.get("AGENTMEMORY_URL", "http://localhost:3111").rstrip("/")


def main() -> int:
    raw = sys.stdin.read() or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}
    session_id = (
        data.get("sessionId")
        or data.get("session_id")
        or os.environ.get("GROK_SESSION_ID")
        or ""
    )
    cwd = data.get("cwd") or data.get("workspaceRoot") or os.getcwd()
    body = json.dumps(
        {"sessionId": session_id, "project": "flossi0ullk", "cwd": cwd}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{REST}/agentmemory/session/start",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=1.5)
    except (urllib.error.URLError, TimeoutError, OSError):
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
