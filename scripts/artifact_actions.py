#!/usr/bin/env python3
"""Allowlisted action runner for Cowork live-artifact GUI buttons.

Artifacts may execute ONLY the actions named here, via:
    python C:\\~shit\\FLOSS\\scripts\\artifact_actions.py <action> [arg]

Design contract (ADR-10 spirit: router, not controller):
  - Fixed allowlist; no passthrough of shell strings or arbitrary args.
  - Read/diagnose actions only. Nothing here mutates the source chain,
    canon docs, or intake queues. Claim/vote writes go through the
    metacoordinator MCP gateway, never through this runner.
  - Single JSON envelope on stdout: {"ok": bool, "action": str, "data"|"error": ...}

Added 2026-06-11 alongside the Cowork node-console artifact.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\~shit")
FLOSS = ROOT / "FLOSS"
SCRIPTS = FLOSS / "scripts"
ACTIVITY = ROOT / ".agent-surface" / "activity.jsonl"
EVENTS = ROOT / ".agent-surface" / "events"

MAX_QUERY_LEN = 300
MAX_TAIL = 200


def _run(cmd: list[str], timeout: int = 90) -> dict:
    proc = subprocess.run(
        cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout
    )
    out = proc.stdout.strip()
    try:
        data = json.loads(out)
    except (json.JSONDecodeError, ValueError):
        data = {"raw": out[-4000:]}
    if proc.returncode != 0:
        data["stderr"] = proc.stderr.strip()[-2000:]
        data["returncode"] = proc.returncode
    return data


def act_route(query: str) -> dict:
    query = (query or "").strip()[:MAX_QUERY_LEN]
    if not query:
        raise ValueError("route requires a non-empty query")
    return _run([sys.executable, str(SCRIPTS / "context_router.py"),
                 query, "--format", "json", "--limit", "5"])


def act_probe(_arg: str = "") -> dict:
    return _run([sys.executable, str(SCRIPTS / "orient_probe.py"),
                 "--root", str(ROOT), "--json"])


def act_smoke_voters(_arg: str = "") -> dict:
    return _run([sys.executable, str(SCRIPTS / "smoke_test_voters.py")], timeout=120)


def act_activity_tail(arg: str = "40") -> dict:
    try:
        n = max(1, min(int(arg or 40), MAX_TAIL))
    except ValueError:
        n = 40
    if not ACTIVITY.exists():
        return {"lines": [], "note": "activity.jsonl absent"}
    lines = ACTIVITY.read_text(encoding="utf-8", errors="replace").splitlines()
    records = []
    for line in lines[-n:]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            records.append({"unparsed": line[:300]})
    return {"total_lines": len(lines), "returned": len(records), "records": records}


def act_intake_status(_arg: str = "") -> dict:
    out: dict = {}
    summary = EVENTS / "queue-summary.json"
    if summary.exists():
        out["queue_summary"] = json.loads(summary.read_text(encoding="utf-8"))
    for sub in ("incoming", "processing", "processed", "failed"):
        d = EVENTS / sub
        out[sub] = len(list(d.iterdir())) if d.is_dir() else None
    return out


ACTIONS = {
    "route": act_route,
    "probe": act_probe,
    "smoke_voters": act_smoke_voters,
    "activity_tail": act_activity_tail,
    "intake_status": act_intake_status,
}


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    arg = sys.argv[2] if len(sys.argv) > 2 else ""
    if action not in ACTIONS:
        print(json.dumps({"ok": False, "action": action,
                          "error": f"action not in allowlist {sorted(ACTIONS)}"}))
        return 1
    try:
        data = ACTIONS[action](arg)
        print(json.dumps({"ok": True, "action": action, "data": data}, default=str))
        return 0
    except Exception as exc:  # noqa: BLE001 — envelope everything for the GUI
        print(json.dumps({"ok": False, "action": action, "error": str(exc)[:500]}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
