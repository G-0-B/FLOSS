"""Minimal MCP-over-stdio client for agentmemory, built for use inside hooks.

agentmemory (http://localhost:3111) exposes no usable REST surface -- every
plain HTTP health/status/rpc path 404s. The only working call path is the
MCP stdio server shipped as `@agentmemory/mcp`, spoken over a child process's
stdin/stdout using newline-delimited JSON-RPC 2.0 messages. A full
`initialize` handshake plus one `tools/call` measures ~240ms in practice.

Public surface:
    save(text, concepts=None, timeout=5.0) -> bool
    recall(query, limit=3, timeout=5.0) -> list[str]

Cardinal rule: this module must NEVER raise into a caller, NEVER block past
its timeout, and NEVER write anything to stdout. Hooks communicate with their
harness over stdout -- a stray byte there corrupts the hook protocol. All
diagnostics go to `FLOSS_AGENT_DIR/hook.log`, the same log file the hook
scripts already use. Every public function is a hard boundary: any failure
inside (missing node, missing server bundle, hung child, malformed JSON,
network error on the agentmemory side) is caught, logged, and turned into
the safe default return value (`False` / `[]`).

Callers are expected to pass an explicit, small `timeout` when on a latency
budget (e.g. session start injection); the 5.0s default is a generous
fallback for callers with no particular urgency (e.g. a detached background
process that is already slow).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Iterable

AGENT_DIR = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
LOG_FILE = AGENT_DIR / "hook.log"

# Absolute paths per the measured, working call path -- an npm `.cmd` shim
# fails to spawn under harnesses that filter PATH/PATHEXT (this exact
# failure already happened in this project with Hermes), so both the
# interpreter and the script are resolved to absolute paths, never via
# `agentmemory-mcp` on PATH. Overridable via env var for testing and for any
# machine where these paths differ.
#
# The defaults used to be those Windows paths unconditionally. On Linux and
# macOS `C:\Program Files\nodejs\node.exe` is a literal relative filename, so
# every spawn failed and session recall plus both detached saves were silently
# dead by default -- silently, because this module's cardinal rule is to
# swallow failures and return `False`/`[]`. The manifest carries platform Node
# defaults but only expands them into command strings; it never exports them to
# this Python child. So resolve per platform here, preferring PATH off Windows.


def _default_node_path() -> str:
    if sys.platform == "win32":
        return r"C:\Program Files\nodejs\node.exe"
    return shutil.which("node") or "node"


def _default_mcp_server_path() -> str:
    if sys.platform == "win32":
        return (
            r"C:\Users\kalis\AppData\Roaming\npm\node_modules\@agentmemory\mcp\bin.mjs"
        )
    # npm's global prefix differs by platform and installation
    # (/usr/local, /usr/lib, ~/.npm-global, nvm, homebrew...), so try the
    # common layouts and fall back to the most standard one. A caller on an
    # unusual layout sets AGENTMEMORY_MCP_BIN, which is checked first anyway.
    candidates = [
        Path.home() / ".npm-global/lib/node_modules/@agentmemory/mcp/bin.mjs",
        Path("/usr/local/lib/node_modules/@agentmemory/mcp/bin.mjs"),
        Path("/usr/lib/node_modules/@agentmemory/mcp/bin.mjs"),
        Path("/opt/homebrew/lib/node_modules/@agentmemory/mcp/bin.mjs"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(candidates[1])


NODE_PATH = Path(os.environ.get("AGENTMEMORY_NODE_PATH") or _default_node_path())
MCP_SERVER_PATH = Path(
    os.environ.get("AGENTMEMORY_MCP_BIN") or _default_mcp_server_path()
)

_PROTOCOL_VERSION = "2024-11-05"
_CLIENT_INFO = {"name": "floss-hook-agentmemory-client", "version": "0.1.0"}


def _log(msg: str) -> None:
    """Best-effort append to the shared hook log. Never raises, never prints."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass


def _spawn() -> subprocess.Popen:
    """Start the MCP stdio server child process.

    Raises on failure (missing binary, OS spawn error, etc.) -- callers are
    responsible for catching. Never touches stdout/stderr of the *parent*
    process: the child's stderr is swallowed so nothing can leak upward.
    """
    env = dict(os.environ)
    env.setdefault("AGENTMEMORY_URL", "http://localhost:3111")
    env.setdefault("AGENTMEMORY_TOOLS", "all")

    kwargs: dict[str, Any] = {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.DEVNULL,
        "env": env,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]

    return subprocess.Popen([str(NODE_PATH), str(MCP_SERVER_PATH)], **kwargs)


def _send(proc: subprocess.Popen, message: dict) -> None:
    data = (json.dumps(message) + "\n").encode("utf-8")
    assert proc.stdin is not None
    proc.stdin.write(data)
    proc.stdin.flush()


def _read_json_line(stream: Any) -> dict | None:
    """Read one line and parse it as JSON. Returns None on EOF or bad JSON."""
    line = stream.readline()
    if not line:
        return None
    try:
        return json.loads(line.decode("utf-8", errors="replace"))
    except Exception:
        return None


def _reap_detached(proc: subprocess.Popen) -> None:
    """Wait for an already-killed child on a daemon thread.

    `Popen.__del__` warns about a still-running child, and a zombie lingers on
    POSIX until someone waits on it -- but doing that wait on the request path
    is what blew the caller's timeout budget. A daemon thread reaps it without
    holding anyone up, and does not keep the interpreter alive at exit.
    """
    threading.Thread(
        target=lambda: _swallow(lambda: proc.wait(timeout=30)),
        daemon=True,
        name="agentmemory-reap",
    ).start()


def _swallow(fn) -> None:
    try:
        fn()
    except Exception:
        pass  # best-effort cleanup; nothing here is actionable


def _kill(proc: subprocess.Popen) -> None:
    """Unconditionally terminate the child so nothing lingers as an orphan.

    Must not block. This runs *after* `_call_tool` has already spent the
    caller's full `timeout`, so a synchronous `proc.wait(timeout=2)` here added
    up to two more seconds on top of a bound the caller was promised -- turning
    a 2.5s recall budget into 4.5s of session startup, precisely when the server
    is wedged and the wait is most likely to run its full length.
    """
    # Each step is independently best-effort: the child may already be dead,
    # its pipes already closed, or it may ignore the kill until the wait times
    # out. None of those are actionable and all three must still be attempted,
    # so each is swallowed separately rather than sharing one try block --
    # a failure in kill() must not skip the stdin close or the reap.
    try:
        proc.kill()
    except Exception:
        pass  # already exited, or never started
    try:
        if proc.stdin is not None:
            proc.stdin.close()
    except Exception:
        pass  # pipe already broken/closed
    # Reap off the request path. The child has already been killed above; all
    # that remains is collecting its exit status, which no caller waits for.
    _reap_detached(proc)


def _call_tool(tool_name: str, arguments: dict, timeout: float) -> dict | None:
    """Run one MCP `initialize` + `tools/call` round trip against a fresh
    child process and return the parsed `tools/call` JSON-RPC response, or
    None on any failure (spawn error, timeout, EOF, malformed JSON).

    The whole exchange runs on a worker thread so a hung child can be
    reliably bounded by `timeout` via `Thread.join` -- a bare blocking
    `readline()` in the main thread would have no clean way to time out.
    """
    try:
        proc = _spawn()
    except Exception as exc:  # noqa: BLE001 -- missing node/bin, OS error, etc.
        _log(f"[agentmemory] spawn failed for {tool_name}: {type(exc).__name__}: {exc}")
        return None

    outcome: dict[str, Any] = {}

    def worker() -> None:
        try:
            _send(
                proc,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": _PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": _CLIENT_INFO,
                    },
                },
            )
            init_resp = _read_json_line(proc.stdout)
            if init_resp is None:
                return

            _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})

            _send(
                proc,
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments},
                },
            )
            call_resp = _read_json_line(proc.stdout)
            if call_resp is not None:
                outcome["response"] = call_resp
        except Exception as exc:  # noqa: BLE001 -- broken pipe, child died, etc.
            _log(
                f"[agentmemory] worker error for {tool_name}: "
                f"{type(exc).__name__}: {exc}"
            )

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        _log(f"[agentmemory] {tool_name} timed out after {timeout}s, killing child")
        _kill(proc)
        return None

    _kill(proc)
    return outcome.get("response")


def _call_failed(response: dict) -> bool:
    """True when the envelope itself reports failure.

    `_extract_text` already refused an `isError` result by returning None, but
    `save()` read that None as "unparseable payload" and fell back to "a result
    dict is present, so it worked" -- reporting confirmed persistence for an
    explicit tool failure. The two readers disagreed because each decided for
    itself what an error was. One definition, both callers.
    """

    if "error" in response:
        return True
    result = response.get("result")
    if not isinstance(result, dict):
        return True
    return bool(result.get("isError"))


def _extract_text(response: dict) -> str | None:
    """Pull the `result.content[0].text` string out of a tools/call response."""
    if _call_failed(response):
        return None
    result = response.get("result")
    if not isinstance(result, dict):
        return None
    content = result.get("content")
    if not isinstance(content, list) or not content:
        return None
    first = content[0]
    if not isinstance(first, dict):
        return None
    text = first.get("text")
    return text if isinstance(text, str) else None


def _coerce_concepts(concepts: Iterable[str] | str | None) -> str | None:
    if concepts is None:
        return None
    if isinstance(concepts, str):
        return concepts or None
    joined = ",".join(str(c) for c in concepts if c)
    return joined or None


def save(
    text: str,
    concepts: Iterable[str] | str | None = None,
    timeout: float = 5.0,
) -> bool:
    """Save an observation to agentmemory. Returns True on confirmed success,
    False on any failure whatsoever (outage, timeout, malformed response).
    Never raises, never blocks past `timeout`, never prints to stdout.
    """
    try:
        if not text or not text.strip():
            return False

        arguments: dict[str, Any] = {"content": text}
        coerced_concepts = _coerce_concepts(concepts)
        if coerced_concepts:
            arguments["concepts"] = coerced_concepts

        response = _call_tool("memory_save", arguments, timeout)
        if response is None:
            return False

        text_payload = _extract_text(response)
        if text_payload is None:
            # NO CONTENT IS NOT A CONFIRMATION.
            #
            # Two rounds of narrowing here. First this returned True whenever a
            # result dict was present, so `isError: true` read as a save. Then
            # it returned True whenever the call had not explicitly failed --
            # which still accepted `{"result": {}}`, a response carrying no
            # success indication at all, and a caller that discards its data on
            # a True is entitled to more than the absence of an error.
            #
            # A content list that is present but whose text will not parse is
            # still a save: the tool answered. A missing or empty one is not.
            if _call_failed(response):
                return False
            content = (response.get("result") or {}).get("content")
            return isinstance(content, list) and len(content) > 0

        try:
            parsed = json.loads(text_payload)
        except Exception:
            # Inner text wasn't JSON, but the tool call itself didn't error.
            return True

        if isinstance(parsed, dict) and "success" in parsed:
            return bool(parsed["success"])
        return True
    except Exception as exc:  # noqa: BLE001 -- absolute last-resort guard
        _log(f"[agentmemory] save() crashed: {type(exc).__name__}: {exc}")
        return False


def recall_status(
    query: str, limit: int = 3, timeout: float = 5.0
) -> tuple[bool, list[str]]:
    """Like `recall()`, but distinguishes failure from a genuinely empty result.

    Returns `(ok, items)`. `ok` is False only when the call itself failed --
    dead server, timeout, malformed envelope, unparseable payload. A healthy
    server that simply has nothing to say returns `(True, [])`.

    This exists because `recall()` collapses both cases to `[]`, which made a
    total agentmemory outage look identical to "no memories exist" at session
    start -- so the warning that was written specifically to surface an outage
    was omitted precisely during one. Observed live on 2026-08-18: the REST
    engine was wedged (port held, every request returning nothing) and the
    session-start block rendered as though memory were merely empty.

    Same hard guarantees as the rest of this module: never raises, never blocks
    past `timeout`, never writes to stdout.
    """
    try:
        if not query or not query.strip():
            return True, []

        response = _call_tool(
            "memory_recall", {"query": query, "limit": limit}, timeout
        )
        if response is None:
            return False, []

        text_payload = _extract_text(response)
        if text_payload is None:
            return False, []

        try:
            parsed = json.loads(text_payload)
        except Exception:
            return False, []

        results = parsed.get("results") if isinstance(parsed, dict) else None
        if not isinstance(results, list):
            return False, []

        return True, _narratives(results, limit)
    except Exception as exc:  # noqa: BLE001 -- absolute last-resort guard
        _log(f"[agentmemory] recall_status() crashed: {type(exc).__name__}: {exc}")
        return False, []


def _narratives(results: list, limit: int) -> list[str]:
    """Pull up to `limit` human-readable strings out of a results list."""
    out: list[str] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        observation = item.get("observation")
        if not isinstance(observation, dict):
            continue
        narrative = observation.get("narrative")
        if isinstance(narrative, str) and narrative.strip():
            out.append(narrative.strip())
            continue
        facts = observation.get("facts")
        if isinstance(facts, list) and facts:
            joined = "; ".join(str(f) for f in facts if f)
            if joined:
                out.append(joined)
        if len(out) >= limit:
            break
    return out[:limit]


def recall(query: str, limit: int = 3, timeout: float = 5.0) -> list[str]:
    """Recall up to `limit` short strings relevant to `query` from
    agentmemory. Returns [] on any failure whatsoever. Never raises, never
    blocks past `timeout`, never prints to stdout.

    Callers that need to tell an outage apart from an empty result should use
    `recall_status()` instead -- this function deliberately collapses both.
    """
    try:
        if not query or not query.strip():
            return []

        response = _call_tool(
            "memory_recall", {"query": query, "limit": limit}, timeout
        )
        if response is None:
            return []

        text_payload = _extract_text(response)
        if text_payload is None:
            return []

        try:
            parsed = json.loads(text_payload)
        except Exception:
            return []

        results = parsed.get("results") if isinstance(parsed, dict) else None
        if not isinstance(results, list):
            return []

        out: list[str] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            observation = item.get("observation")
            if not isinstance(observation, dict):
                continue
            narrative = observation.get("narrative")
            if isinstance(narrative, str) and narrative.strip():
                out.append(narrative.strip())
                continue
            facts = observation.get("facts")
            if isinstance(facts, list) and facts:
                joined = "; ".join(str(f) for f in facts if f)
                if joined:
                    out.append(joined)
            if len(out) >= limit:
                break
        return out[:limit]
    except Exception as exc:  # noqa: BLE001 -- absolute last-resort guard
        _log(f"[agentmemory] recall() crashed: {type(exc).__name__}: {exc}")
        return []
