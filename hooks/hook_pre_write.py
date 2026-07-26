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
SKIP_SEGMENTS = ("/tests/", "/__pycache__/", "/.venv/", "/venv/", "/archive/")
MUTATING_TOOL_NAMES = {
    "write",
    "edit",
    "multiedit",
    "write_file",
    "replace",
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


def is_substantive(path_str: str) -> bool:
    if not path_str:
        return False
    norm = "/" + path_str.replace("\\", "/").lstrip("/").lower()
    if any(skip in norm for skip in SKIP_SEGMENTS):
        return False
    if not norm.endswith(SUBSTANTIVE_EXTENSIONS):
        return False
    return any(part in norm for part in SUBSTANTIVE_PATH_SEGMENTS)


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

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    file_path = (
        tool_input.get("file_path")
        or tool_input.get("filePath")
        or tool_input.get("path")
        or tool_input.get("target_file")
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
