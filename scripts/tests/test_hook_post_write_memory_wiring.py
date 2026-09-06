"""Proves hook_post_write.py's synchronous <100ms fast path never calls
agentmemory, and that the terse edit-note it hands off to the DETACHED
hook_bg_round.py is correct.

Per the task spec: hook_post_write.py itself must make NO memory call on its
own synchronous path -- only the already-detached hook_bg_round.py (tested
separately in test_hook_bg_round_memory_wiring.py) is allowed to touch
agentmemory. This file's central assertion is negative: if hook_post_write's
main() ever imports or calls agentmemory_client directly, these tests fail.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

FLOSS_ROOT = Path(__file__).resolve().parents[2]


def load_hook_post_write_module(tmp_path: Path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "hook_post_write_under_test", FLOSS_ROOT / "hooks" / "hook_post_write.py"
    )
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["hook_post_write_under_test"] = module
    spec.loader.exec_module(module)

    module.AGENT_DIR = tmp_path / "agent_dir"
    module.LOG_FILE = module.AGENT_DIR / "hook.log"
    module.PRE_WRITE_CHECKPOINT_DIR = module.AGENT_DIR / "checkpoints" / "pre_write"
    # The fixtures build their edits under tmp_path/workspace, so REPO_ROOT has
    # to follow them. `is_substantive` now refuses paths outside REPO_ROOT --
    # the `claude_user` hook target runs this hook in EVERY Claude project, and
    # without containment an edit in an unrelated repository was submitted into
    # FLOSS's durable Claim chain. Pointing REPO_ROOT at the fake workspace
    # keeps these tests exercising the real predicate rather than bypassing it.
    module.REPO_ROOT = tmp_path / "workspace"
    return module


@pytest.fixture()
def poisoned_agentmemory_client(monkeypatch):
    """A fake agentmemory_client whose save()/recall() raise AssertionError
    if called -- proves the fast path never reaches them. Installed as
    sys.modules['agentmemory_client'] so any accidental `import
    agentmemory_client` inside hook_post_write's synchronous path blows up
    the test instead of silently succeeding.
    """
    poisoned = types.ModuleType("agentmemory_client")

    def poisoned_save(*args, **kwargs):
        raise AssertionError(
            "hook_post_write.py's synchronous fast path called agentmemory_client.save() "
            "-- this must only happen from the DETACHED hook_bg_round.py"
        )

    def poisoned_recall(*args, **kwargs):
        raise AssertionError(
            "hook_post_write.py's synchronous fast path called agentmemory_client.recall()"
        )

    poisoned.save = poisoned_save
    poisoned.recall = poisoned_recall
    monkeypatch.setitem(sys.modules, "agentmemory_client", poisoned)
    return poisoned


def _substantive_edit_payload(tmp_path: Path, file_path: Path) -> str:
    return json.dumps(
        {
            "hook_event_name": "PostToolUse",
            "session_id": "sess-1",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(file_path),
                "old_string": "old content",
                "new_string": "new content",
            },
        }
    )


def test_fast_path_never_imports_or_calls_agentmemory(
    tmp_path, monkeypatch, capsys, poisoned_agentmemory_client
):
    module = load_hook_post_write_module(tmp_path, monkeypatch)

    # Route the edit into a real "packages/" substantive path so the full
    # claim-submission path runs.
    pkg_dir = tmp_path / "workspace" / "packages" / "demo"
    pkg_dir.mkdir(parents=True)
    target_file = pkg_dir / "module.py"
    target_file.write_text("old content\n", encoding="utf-8")

    spawn_calls = []
    monkeypatch.setattr(
        module,
        "spawn_background_round",
        lambda claim_id, edit_note="": spawn_calls.append((claim_id, edit_note)),
    )

    payload = _substantive_edit_payload(tmp_path, target_file)
    monkeypatch.setattr(sys.stdin, "read", lambda: payload)

    exit_code = module.main()

    assert exit_code == 0
    # If this assertion is reached, poisoned_agentmemory_client's save/recall
    # were never invoked (they raise AssertionError, which would have
    # propagated out of main() and failed this test already).
    captured = capsys.readouterr()
    assert captured.out == ""


def test_substantive_edit_passes_terse_edit_note_to_spawn_background_round(
    tmp_path, monkeypatch, poisoned_agentmemory_client
):
    module = load_hook_post_write_module(tmp_path, monkeypatch)

    pkg_dir = tmp_path / "workspace" / "packages" / "demo"
    pkg_dir.mkdir(parents=True)
    target_file = pkg_dir / "module.py"
    target_file.write_text("old content\n", encoding="utf-8")

    spawn_calls = []
    monkeypatch.setattr(
        module,
        "spawn_background_round",
        lambda claim_id, edit_note="": spawn_calls.append((claim_id, edit_note)),
    )

    payload = _substantive_edit_payload(tmp_path, target_file)
    monkeypatch.setattr(sys.stdin, "read", lambda: payload)

    module.main()

    assert len(spawn_calls) == 1
    claim_id, edit_note = spawn_calls[0]
    assert claim_id  # a real claim id was submitted
    assert edit_note  # terse note handed to the detached branch
    assert "module.py" in edit_note
    assert len(edit_note) <= 200


def test_non_substantive_edit_never_spawns_or_touches_memory(
    tmp_path, monkeypatch, poisoned_agentmemory_client
):
    """A path outside packages/ is filtered out before any claim/spawn/
    memory logic runs at all -- confirms the memory wiring didn't loosen
    the existing substantive-path filter.
    """
    module = load_hook_post_write_module(tmp_path, monkeypatch)

    other_file = tmp_path / "workspace" / "docs" / "notes.md"
    other_file.parent.mkdir(parents=True)
    other_file.write_text("hello\n", encoding="utf-8")

    spawn_calls = []
    monkeypatch.setattr(
        module,
        "spawn_background_round",
        lambda claim_id, edit_note="": spawn_calls.append((claim_id, edit_note)),
    )

    payload = _substantive_edit_payload(tmp_path, other_file)
    monkeypatch.setattr(sys.stdin, "read", lambda: payload)

    module.main()

    assert spawn_calls == []


def test_spawn_background_round_forwards_edit_note_as_argv(tmp_path, monkeypatch):
    """Unit-level check of spawn_background_round itself: edit_note, when
    given, becomes argv[3] (after python, script path, claim_id).
    """
    module = load_hook_post_write_module(tmp_path, monkeypatch)

    captured_argv = {}

    class FakeProc:
        pass

    def fake_popen(argv, **kwargs):
        captured_argv["argv"] = argv
        return FakeProc()

    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)
    # Ensure the bg script "exists" per the early guard in
    # spawn_background_round without requiring a real file.
    monkeypatch.setattr(Path, "exists", lambda self: True)

    module.spawn_background_round("claim_123", "terse edit note")

    argv = captured_argv["argv"]
    assert argv[2] == "claim_123"
    assert argv[3] == "terse edit note"


def test_spawn_background_round_omits_argv_when_no_edit_note(tmp_path, monkeypatch):
    module = load_hook_post_write_module(tmp_path, monkeypatch)

    captured_argv = {}

    class FakeProc:
        pass

    def fake_popen(argv, **kwargs):
        captured_argv["argv"] = argv
        return FakeProc()

    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(Path, "exists", lambda self: True)

    module.spawn_background_round("claim_456")

    argv = captured_argv["argv"]
    assert argv == [
        sys.executable,
        str(module.REPO_ROOT / "hooks" / "hook_bg_round.py"),
        "claim_456",
    ]
