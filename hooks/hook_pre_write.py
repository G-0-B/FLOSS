"""
Pre-write hook for agent-native file edit tools.

This captures a deterministic checkpoint before the tool mutates the file so
the post-write hook can detect stale or intervening writes instead of trusting
snippet presence alone.

Invoked with hook JSON on stdin from surfaces such as:
    - Claude Code `PreToolUse` on `Write|Edit|MultiEdit`
    - Gemini CLI `BeforeTool` on `write_file|replace`

Behavior:
    1. Parse stdin JSON (swallow errors)
    2. Path filter — only substantive package edits
    3. Snapshot the pre-write file image when available
    4. Store a checkpoint under FLOSS_AGENT_DIR/checkpoints/pre_write
    5. Exit 0 without blocking the user
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
LOG_FILE = AGENT_DIR / "hook.log"
PRE_WRITE_CHECKPOINT_DIR = AGENT_DIR / "checkpoints" / "pre_write"
EMIT_STDOUT_JSON = "--stdout-json" in sys.argv[1:]

SUBSTANTIVE_PATH_SEGMENTS = ("/packages/",)
SUBSTANTIVE_EXTENSIONS = (".py", ".rs", ".toml")
# Mirrors hook_post_write.py. The post-write hook was widened to canon surfaces
# on 2026-08-10 and this predicate was not, so every ADR, spec and governance
# edit reached claim_pre_write_checkpoint() with no checkpoint to consume. The
# post hook then fell back to a snippet-presence check and could still label the
# result VERIFIED without ever deriving the exact post-image -- which is the one
# thing a checkpoint exists to prove. Keep the two in step.
CANON_PATH_SEGMENTS = ("/docs/adr/", "/docs/specs/", "/docs/governance/")
CANON_EXTENSIONS = (".md", ".json")
CANON_ROOT_PREFIX = "flossi0ullk_master_metaprompt"
CANON_ROOT_SUFFIX = "_kernel.md"
SKIP_SEGMENTS = ("/tests/", "/__pycache__/", "/.venv/", "/venv/", "/archive/")
MUTATING_TOOL_NAMES = {
    # Claude Code
    "write",
    "edit",
    "multiedit",
    # Gemini
    "write_file",
    "replace",
    # Hermes. `patch` is Hermes's own file-editing tool name -- the hook
    # manifest matches `write_file|patch` for both Hermes events and was
    # confirmed against tools/file_tools.py -- but it was missing here, so every
    # Hermes patch returned immediately at is_mutating_tool(): no checkpoint, no
    # Claim, while `hermes hooks list` reported the hook installed and allowed.
    # An installed hook that silently does nothing is worse than an absent one.
    "patch",
}


def log(msg: str) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass


def finish() -> int:
    if EMIT_STDOUT_JSON:
        try:
            sys.stdout.write("{}\n")
            sys.stdout.flush()
        except Exception:
            pass
    return 0


def _repo_relative(path_str: str) -> str | None:
    """The RESOLVED repository-relative path, lowercased, or None if outside.

    Containment was checked against the resolved path while every filter below
    inspected the raw spelling, so the two disagreed about the same file. A
    tool supplying `packages/tests/../prod.py` resolves to production code and
    was SKIPPED for containing "/tests/"; `packages/../docs/research/x.py`
    resolves to an intake mouth and was treated as package code. Both filters
    now read the path the filesystem agrees on.
    """

    try:
        candidate = Path(path_str).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        resolved = candidate.resolve()
        root = REPO_ROOT.resolve()
    except (OSError, ValueError):
        return None
    if resolved != root and root not in resolved.parents:
        return None
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return ""
    return "/" + relative.as_posix().lower()


def _is_inside_repo(path_str: str) -> bool:
    """Only edits within THIS checkout may be checkpointed.

    The `claude_user` target installs this hook at user scope, so it runs for
    every project on the machine. Without containment, editing
    `/other-project/packages/secret.py` wrote that unrelated file's path and
    bounded old/new source previews into ~/.floss_agent/checkpoints/pre_write.
    The post-write hook's own containment check does not undo that disclosure --
    it happens after the write is already on disk.
    """
    return _repo_relative(path_str) is not None


def _is_root_kernel(path_str: str) -> bool:
    """True for the repo-root master metaprompt kernel, at any version.

    Resolved against REPO_ROOT rather than pattern-matched on the string: hooks
    receive ABSOLUTE paths, so a "one slash means repository root" test never
    fired. Segment matching survives absolute paths by accident because
    "/docs/adr/" is a substring either way; a root-level file has no segment to
    match, so it needs the real comparison.
    """
    try:
        candidate = Path(path_str).expanduser()
        if not candidate.is_absolute():
            # Relative against REPO_ROOT, not cwd: classify_change() is called
            # with the repo-relative path and the hook's cwd is whatever the
            # editing agent happened to be in.
            candidate = REPO_ROOT / candidate
        resolved = candidate.resolve()
    except (OSError, ValueError):
        return False
    if resolved.parent != REPO_ROOT.resolve():
        return False
    name = resolved.name.lower()
    return name.startswith(CANON_ROOT_PREFIX) and name.endswith(CANON_ROOT_SUFFIX)


def is_substantive(path_str: str) -> bool:
    if not path_str:
        return False
    norm = _repo_relative(path_str)
    if norm is None:
        return False
    if any(skip in norm for skip in SKIP_SEGMENTS):
        return False
    if norm.endswith(SUBSTANTIVE_EXTENSIONS) and any(
        part in norm for part in SUBSTANTIVE_PATH_SEGMENTS
    ):
        return True
    if norm.endswith(CANON_EXTENSIONS) and any(
        part in norm for part in CANON_PATH_SEGMENTS
    ):
        return True
    return _is_root_kernel(path_str)


def is_mutating_tool(tool_name: str) -> bool:
    return (tool_name or "").strip().lower() in MUTATING_TOOL_NAMES


def extract_session_id(payload: dict) -> str:
    for key in (
        "session_id",
        "sessionId",
        "conversation_id",
        "conversationId",
        "tool_use_id",
        "toolUseId",
    ):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def main() -> int:
    try:
        payload_raw = sys.stdin.read()
        payload = json.loads(payload_raw) if payload_raw.strip() else {}
    except Exception as exc:  # noqa: BLE001
        log(f"[hook-pre] stdin parse error: {exc}")
        return finish()

    tool_call = payload.get("toolCall") or {}
    tool_name = payload.get("tool_name", "") or tool_call.get("name", "")
    tool_input = payload.get("tool_input", {}) or tool_call.get("args", {}) or {}
    file_path = (
        tool_input.get("file_path")
        or tool_input.get("filePath")
        or tool_input.get("path")
        or tool_input.get("target_file")
        or tool_input.get("TargetFile")
        or tool_input.get("targetFile")
        or ""
    )

    if not is_mutating_tool(tool_name):
        return finish()
    if not is_substantive(file_path):
        return finish()

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    try:
        from packages.metacoordinator_mcp.hashline import (
            build_pre_write_checkpoint,
            write_pre_write_checkpoint,
        )
    except Exception:  # noqa: BLE001
        log(f"[hook-pre] hashline import failed:\n{traceback.format_exc()}")
        return finish()

    path = Path(file_path)
    try:
        pre_text = path.read_text(encoding="utf-8", errors="replace")
        source_exists = True
    except FileNotFoundError:
        pre_text = None
        source_exists = False
    except Exception as exc:  # noqa: BLE001
        log(f"[hook-pre] file read failed for {file_path}: {type(exc).__name__}: {exc}")
        return finish()

    try:
        checkpoint = build_pre_write_checkpoint(
            file_path,
            tool_name,
            tool_input,
            pre_text=pre_text,
            source_exists=source_exists,
            hook_event_name=payload.get("hook_event_name", ""),
            session_id=extract_session_id(payload),
        )
        checkpoint_path = write_pre_write_checkpoint(
            PRE_WRITE_CHECKPOINT_DIR, checkpoint
        )
    except Exception:  # noqa: BLE001
        log(f"[hook-pre] checkpoint build/write failed:\n{traceback.format_exc()}")
        return finish()

    rel_path = file_path
    try:
        rel_path = str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except (ValueError, OSError):
        pass

    log(
        f"[hook-pre] checkpointed {rel_path} "
        f"→ {checkpoint.get('signature', 'unknown')} "
        f"({checkpoint_path})"
    )
    return finish()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001
        log(f"[hook-pre] top-level crash:\n{traceback.format_exc()}")
        sys.exit(finish())
