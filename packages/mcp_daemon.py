"""Shared daemon bootstrap for FLOSSIØULLK Python MCP servers.

Converts per-client stdio spawns into one persistent PID-guarded HTTP daemon.
Bind 127.0.0.1 ONLY (native Windows; never expose to the network). Carries the
former JanuScope lens instruction injection (passed into FastMCP) and appends a
per-tool-call audit line to the same janus-*-audit.jsonl sink the lens used.

This module is transport-only — it does not touch consensus/ensemble domain logic.
"""
from __future__ import annotations

import atexit
import functools
import inspect
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


_AUDIT_VALUE_MAX_CHARS = 500


def _safe_payload(func, args: tuple, kwargs: dict) -> dict:
    """Render one call's arguments as a bounded, JSON-safe dict.

    Binds positional args to their parameter names so the audit row is readable
    regardless of how the caller invoked the tool, and truncates every value so
    a large Claim body cannot turn the audit sink into a copy of the source
    chain. Never raises: an unbindable signature or an unrepresentable value
    degrades to a marker rather than losing the audit line entirely.
    """
    def clip(v):
        try:
            s = v if isinstance(v, (str, int, float, bool, type(None))) else repr(v)
        except Exception:  # noqa: BLE001 - a hostile __repr__ must not break audit
            return "<unrepresentable>"
        if isinstance(s, str) and len(s) > _AUDIT_VALUE_MAX_CHARS:
            return s[:_AUDIT_VALUE_MAX_CHARS] + "…<truncated>"
        return s

    try:
        bound = inspect.signature(func).bind_partial(*args, **kwargs)
        return {k: clip(v) for k, v in bound.arguments.items()}
    except Exception:  # noqa: BLE001 - fall back rather than drop the row
        return {
            "args": [clip(a) for a in args],
            "kwargs": {k: clip(v) for k, v in kwargs.items()},
        }


def audited(tool, append):
    """Wrap one MCP tool so every invocation appends an audit row.

    `functools.wraps` copies `__name__`/`__doc__`/annotations and sets
    `__wrapped__`, which `inspect.signature` follows by default — so FastMCP
    still derives the same tool schema from the wrapper as it did from the bare
    function. Without that the wrapper would register as `(*args, **kwargs)`
    and silently destroy every tool's parameter schema.

    Async and sync tools are wrapped separately: returning a coroutine from a
    sync wrapper (or awaiting a sync function) would break registration.
    """
    if inspect.iscoroutinefunction(tool):
        @functools.wraps(tool)
        async def _async_wrapper(*args, **kwargs):
            append(tool.__name__, _safe_payload(tool, args, kwargs))
            return await tool(*args, **kwargs)

        return _async_wrapper

    @functools.wraps(tool)
    def _sync_wrapper(*args, **kwargs):
        append(tool.__name__, _safe_payload(tool, args, kwargs))
        return tool(*args, **kwargs)

    return _sync_wrapper


def register_audited_tools(app, tools, sink: str) -> None:
    """Register each tool on `app` with audit instrumentation attached.

    This is the production caller `audit_appender` previously lacked. Before
    this existed the appender was defined, unit-tested, and never invoked
    outside tests, so `_AUDIT_SINK` was dead config and every consensus /
    ensemble MCP invocation bypassed the JSONL audit trail that replacing
    JanuScope was justified by.
    """
    append = audit_appender(sink)
    for tool in tools:
        app.tool()(audited(tool, append))


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
