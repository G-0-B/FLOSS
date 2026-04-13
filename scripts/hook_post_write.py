"""
Claude Code PostToolUse hook — submit substantive file edits as Claims to the
local consensus gateway and kick off a detached background consensus round.

Invoked by Claude Code on Write|Edit|MultiEdit with hook JSON on stdin:
    {"tool_name": "Edit", "tool_input": {"file_path": "...", ...}, ...}

Fast path (< 100 ms wall-clock):
    1. Parse stdin JSON (swallow errors)
    2. Path filter — only packages/**/*.{py,rs,toml}; skip tests/, __pycache__/
    3. Construct a Claim and submit it via GatewayTools (local file write)
    4. Spawn a DETACHED subprocess to run the consensus round in the background
    5. Log to FLOSS_AGENT_DIR/hook.log and exit 0

Guarantees:
    - Never blocks the user: exits 0 on every failure path
    - Never recurses: edits to scripts/ (including this file) are skipped
      by the path filter, so installing the hook can't trigger the hook
    - Never burns free-tier budget on routine work: the path filter is
      intentionally narrow — broaden only when we're sure we want voters
      to evaluate edits in a given directory
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
LOG_FILE = AGENT_DIR / "hook.log"

# Substantive = worth burning a consensus round on. Intentionally narrow.
SUBSTANTIVE_PATH_SEGMENTS = ("/packages/",)
SUBSTANTIVE_EXTENSIONS = (".py", ".rs", ".toml")

# Even within substantive paths, skip these — they're routine noise.
SKIP_SEGMENTS = ("/tests/", "/__pycache__/", "/.venv/", "/venv/", "/archive/")


def log(msg: str) -> None:
    """Best-effort append to the hook log. Never raises."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass  # logging must never break the hook


def is_substantive(path_str: str) -> bool:
    """True if this edit is worth submitting as a Claim."""
    if not path_str:
        return False
    norm = "/" + path_str.replace("\\", "/").lstrip("/").lower()
    if any(skip in norm for skip in SKIP_SEGMENTS):
        return False
    if not norm.endswith(SUBSTANTIVE_EXTENSIONS):
        return False
    return any(part in norm for part in SUBSTANTIVE_PATH_SEGMENTS)


# Character budget per side of an edit or per Write body. Chosen so that
# a full 3-voter round on a typical edit still fits comfortably inside the
# context window of the 8B–32B models we're using AND inside Claim.body
# without being so tiny that voters can't actually see what changed.
_MAX_CHANGE_CHARS = 1500


def _trim(text: str, limit: int = _MAX_CHANGE_CHARS) -> str:
    """Truncate a block to `limit` chars with a visible marker when cut."""
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated, {len(text) - limit} more chars]"


def _render_change_section(tool_name: str, tool_input: dict) -> str:
    """Build a human-readable description of the actual change.

    For Edit: show old_string → new_string (the two sides of the diff).
    For MultiEdit: show each sub-edit's before/after in order.
    For Write: show the new file content.

    Everything is bounded by `_MAX_CHANGE_CHARS` per side so a single huge
    edit can't blow out the Claim body or the voter prompt.
    """
    tn = (tool_name or "").lower()

    if tn == "edit":
        old = _trim(tool_input.get("old_string", "") or "")
        new = _trim(tool_input.get("new_string", "") or "")
        return (
            "CHANGE (Edit):\n"
            "--- old ---\n"
            f"{old}\n"
            "--- new ---\n"
            f"{new}"
        )

    if tn == "multiedit":
        edits = tool_input.get("edits") or []
        if not isinstance(edits, list) or not edits:
            return "CHANGE (MultiEdit): <no edits>"
        parts = [f"CHANGE (MultiEdit, {len(edits)} sub-edits):"]
        # Cap to first 5 sub-edits to keep the Claim body bounded; a single
        # MultiEdit with 30 changes shouldn't eat 30 × 1500 chars.
        for idx, e in enumerate(edits[:5], start=1):
            old = _trim(e.get("old_string", "") or "", limit=600)
            new = _trim(e.get("new_string", "") or "", limit=600)
            parts.append(f"-- sub-edit {idx} old --\n{old}")
            parts.append(f"-- sub-edit {idx} new --\n{new}")
        if len(edits) > 5:
            parts.append(f"... [{len(edits) - 5} more sub-edits omitted]")
        return "\n".join(parts)

    if tn == "write":
        content = _trim(tool_input.get("content", "") or "")
        return "CHANGE (Write — full new file content):\n" + content

    # Unknown tool — fall back to a serialized tool_input so voters at
    # least see *something* rather than a bare filename.
    try:
        serialized = json.dumps(tool_input, indent=2, default=str)
    except Exception:  # noqa: BLE001
        serialized = str(tool_input)
    return f"CHANGE ({tool_name}):\n" + _trim(serialized)


def spawn_background_round(claim_id: str) -> None:
    """Fire-and-forget subprocess to run the consensus round.

    On Windows uses DETACHED_PROCESS + CREATE_NO_WINDOW so the child lives
    past the hook's exit and doesn't flash a console window. On POSIX we
    use start_new_session to detach from the hook's process group.
    """
    bg_script = REPO_ROOT / "scripts" / "hook_bg_round.py"
    if not bg_script.exists():
        log(f"[hook] bg script missing: {bg_script}")
        return
    try:
        kwargs: dict = {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "close_fds": True,
        }
        if sys.platform == "win32":
            kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
            )
        else:
            kwargs["start_new_session"] = True
        subprocess.Popen(
            [sys.executable, str(bg_script), claim_id],
            **kwargs,
        )
        log(f"[hook] spawned bg round for {claim_id}")
    except Exception as exc:  # noqa: BLE001
        log(f"[hook] bg spawn failed for {claim_id}: {type(exc).__name__}: {exc}")


def main() -> int:
    try:
        payload_raw = sys.stdin.read()
        payload = json.loads(payload_raw) if payload_raw.strip() else {}
    except Exception as exc:  # noqa: BLE001
        log(f"[hook] stdin parse error: {exc}")
        return 0

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path") or tool_input.get("filePath") or ""

    if not is_substantive(file_path):
        # Uncomment for verbose debugging:
        # log(f"[hook] skip {tool_name} {file_path}")
        return 0

    # Lazy import — only reached for substantive paths, so cold-start cost
    # is paid on exactly the edits that warrant it.
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    try:
        from packages.metacoordinator_mcp.tools import GatewayTools
    except Exception:  # noqa: BLE001
        log(f"[hook] GatewayTools import failed:\n{traceback.format_exc()}")
        return 0

    try:
        dna_hash = os.environ.get("FLOSS_DNA_HASH", "0" * 64)
        gw = GatewayTools(base_dir=AGENT_DIR, dna_hash=dna_hash)
    except Exception:  # noqa: BLE001
        log(f"[hook] GatewayTools init failed:\n{traceback.format_exc()}")
        return 0

    rel_path = file_path
    try:
        rel_path = str(Path(file_path).resolve().relative_to(REPO_ROOT.resolve()))
    except (ValueError, OSError):
        pass

    # Include the actual change in the body so voters have something real to
    # evaluate. Without this, voters get the filename and nothing else and
    # correctly abstain (0.0) because there is no content to judge — the
    # whole round becomes meaningless audit noise.
    change_section = _render_change_section(tool_name, tool_input)

    summary = f"{tool_name} → {Path(file_path).name}"[:200]
    body = (
        f"Auto-Claim from Claude Code PostToolUse hook.\n"
        f"Tool:  {tool_name}\n"
        f"Path:  {rel_path}\n"
        f"\n"
        f"{change_section}\n"
        f"\n"
        f"Evaluate whether the change preserves module invariants, matches "
        f"existing conventions in the surrounding code, and carries no "
        f"obvious security or correctness risks. Blast radius is Local — "
        f"the hook never auto-escalates."
    )

    try:
        result_str = gw.submit_claim(
            proposer="claude-code-hook",
            proposal_type="CodeChange",
            summary=summary,
            body=body,
            blast_radius="Local",
        )
        result = json.loads(result_str)
    except Exception:  # noqa: BLE001
        log(f"[hook] submit_claim crashed:\n{traceback.format_exc()}")
        return 0

    if "error" in result:
        log(f"[hook] submit_claim error for {rel_path}: {result['error']}")
        return 0

    claim_id = result.get("claim_id", "")
    log(f"[hook] claimed {rel_path} → {claim_id}")

    spawn_background_round(claim_id)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 — absolute last-resort guard
        log(f"[hook] top-level crash:\n{traceback.format_exc()}")
        sys.exit(0)
