"""Shared daemon bootstrap for FLOSSIØULLK Python MCP servers.

Converts per-client stdio spawns into one persistent PID-guarded HTTP daemon.
Bind 127.0.0.1 ONLY (native Windows; never expose to the network). Carries the
former JanuScope lens instruction injection (passed into FastMCP) and appends a
per-tool-call audit line to the same janus-*-audit.jsonl sink the lens used.

This module is transport-only — it does not touch consensus/ensemble domain logic.
"""
from __future__ import annotations

import atexit
import json
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path


def _pid_alive(pid: int) -> bool:
    """Return True if `pid` is a running process.

    On Windows, ``os.kill(pid, 0)`` is unreliable (raises WinError 87 or
    SystemError for various PID values). We use ``ctypes.OpenProcess`` with
    a zero access mask — it succeeds if the process exists (even if owned by
    another user) and fails with ERROR_INVALID_PARAMETER (87) if the PID
    is not in use.
    """
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        # PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        # ERROR_INVALID_PARAMETER (87) = PID not in use
        # ERROR_ACCESS_DENIED (5) = exists but owned by another user
        err = kernel32.GetLastError()
        return err == 5  # access denied means it exists
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except ValueError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else
    except (OSError, SystemError):
        return False


def claim_singleton(pid_filename: str) -> bool:
    """Return True if this process now owns the daemon slot, False if one is live.

    Writes a PID file under ``FLOSS_AGENT_DIR`` (default ``~/.floss_agent``).
    Stale PID files (dead process) are overwritten. Live PID files block.
    Registers atexit + signal handlers to clean up the PID file on exit.
    """
    pid_dir = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
    pid_dir.mkdir(parents=True, exist_ok=True)
    pid_path = pid_dir / pid_filename
    if pid_path.exists():
        try:
            existing = int(pid_path.read_text().strip())
            if _pid_alive(existing):
                return False
        except ValueError:
            pass  # stale/corrupt -> overwrite
    pid_path.write_text(str(os.getpid()))
    atexit.register(lambda: pid_path.unlink(missing_ok=True))
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: (pid_path.unlink(missing_ok=True), sys.exit(0)))
    return True


def audit_appender(sink: str):
    """Return callable(tool_name, payload) that appends one JSONL audit line.

    Audit is best-effort defense-in-depth — it must never raise.
    """
    sink_path = Path(sink)

    def _append(tool_name: str, payload: dict) -> None:
        try:
            sink_path.parent.mkdir(parents=True, exist_ok=True)
            row = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "tool": tool_name,
                "payload": payload,
            }
            with sink_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except OSError:
            pass  # audit is best-effort, never fatal

    return _append


def run_http_daemon(mcp, *, pid_filename: str, port: int) -> None:
    """Claim the singleton slot, then serve FastMCP over streamable-http on loopback.

    Binds to 127.0.0.1 ONLY (native Windows; never expose to the network).
    If a daemon is already running for this slot, prints a message and exits 0.

    Note: FastMCP's run() method does not accept host/port kwargs. The host and
    port must be set on the FastMCP instance's settings before calling run().
    This function patches ``mcp.settings.port`` in-place before serving.
    """
    if not claim_singleton(pid_filename):
        print(f"[FLOSS MCP] already running on :{port}; exiting.", file=sys.stderr)
        sys.exit(0)
    # FastMCP stores host/port in settings; run() reads them from there.
    mcp.settings.port = port
    mcp.settings.host = "127.0.0.1"
    mcp.run(transport="streamable-http")
