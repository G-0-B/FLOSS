"""Harness attribution for edits the post-write hook accepts.

PR41 review finding: `hook_post_write.infer_surface()` had no Hermes case, so
every Hermes edit was misattributed the moment the hook was extended to cover
Hermes at all. `write_file` matched the gemini-cli branch (Gemini uses the same
tool name) and `patch` fell through to the generic `agent-tool`. That label
reaches the Claim, the signed packet's `source_systems`, the summary and the
background memory -- so the provenance this hook exists to record named the
wrong harness for every edit on its newest surface.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = REPO_ROOT / "hooks" / "hook_post_write.py"


def load_hook():
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    spec = importlib.util.spec_from_file_location("hook_post_write", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_hermes_patch_is_attributed_to_hermes():
    """`patch` is Hermes-only and fell through to the generic label."""
    hook = load_hook()

    assert hook.infer_surface("patch", "post_tool_call") == "hermes"


def test_hermes_write_file_is_not_attributed_to_gemini():
    """`write_file` is Gemini's tool name AND Hermes's, so the tool name alone
    cannot separate them. The event does: Hermes's manifest event_map emits
    pre_tool_call/post_tool_call, Gemini emits AfterTool."""
    hook = load_hook()

    assert hook.infer_surface("write_file", "post_tool_call") == "hermes"
    assert hook.infer_surface("write_file", "pre_tool_call") == "hermes"


def test_gemini_is_still_gemini():
    """Ordering the Hermes branch first must not capture Gemini's events."""
    hook = load_hook()

    assert hook.infer_surface("write_file", "AfterTool") == "gemini-cli"
    assert hook.infer_surface("replace", "AfterTool") == "gemini-cli"
    assert hook.infer_surface("write_file", "") == "gemini-cli"


def test_claude_code_is_still_claude_code():
    hook = load_hook()

    for tool in ("Write", "Edit", "MultiEdit"):
        assert hook.infer_surface(tool, "PostToolUse") == "claude-code"


def test_the_hermes_events_match_the_manifest_event_map():
    """The event names are the join between the manifest and this guard, so a
    manifest edit that renames them must break here rather than silently
    restoring the misattribution."""
    import json

    manifest = json.loads(
        (REPO_ROOT / "shared-hook-surface.json").read_text(encoding="utf-8")
    )
    event_map = manifest["targets"]["hermes_user"]["event_map"]
    hook = load_hook()

    for hermes_event in event_map.values():
        assert hook.infer_surface("write_file", hermes_event) == "hermes", hermes_event
