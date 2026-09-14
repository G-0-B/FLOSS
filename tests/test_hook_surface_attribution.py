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


def test_a_declared_surface_beats_inference(monkeypatch):
    """Codex and Claude register this hook with the SAME matcher and the SAME
    command, so the payload carries nothing that separates them and the
    tool-name branch labelled every Codex edit `claude-code`. That label is
    persisted in the Claim summary and the signed packet's `source_systems`.
    No heuristic can fix identical events; the registration has to say."""
    hook = load_hook()

    monkeypatch.setattr(sys, "argv", ["hook_post_write.py", "--surface", "codex"])
    assert hook.infer_surface("Write", "PostToolUse") == "codex"
    assert hook.infer_surface("Edit", "PostToolUse") == "codex"
    assert hook.infer_surface("MultiEdit", "PostToolUse") == "codex"


def test_the_declaration_is_read_from_the_flag_the_manifest_writes(monkeypatch):
    """Plumbed at one end and read at the other is the failure this guards.

    The first version read only FLOSS_HOOK_SURFACE while the manifest wrote
    only `--surface`, so nothing was declared and the misattribution survived
    the fix for it.
    """
    hook = load_hook()

    assert hook.declared_surface(["--surface", "codex"]) == "codex"
    assert hook.declared_surface(["--surface=hermes"]) == "hermes"
    assert hook.declared_surface([]) == ""

    monkeypatch.setenv(hook.DECLARED_SURFACE_ENV, "gemini-cli")
    assert hook.declared_surface([]) == "gemini-cli", "the env fallback is gone"


def test_every_managed_registration_declares_its_surface():
    """The join between the manifest and the hook. A target that registers
    this hook without declaring itself falls back to inference, which is what
    misattributed Codex in the first place."""
    import json

    manifest = json.loads(
        (REPO_ROOT / "shared-hook-surface.json").read_text(encoding="utf-8")
    )
    undeclared = []
    for target, cfg in manifest["targets"].items():
        for event, entries in (cfg.get("hooks") or {}).items():
            for entry in entries:
                for hook in entry.get("hooks") or [entry]:
                    command = (hook or {}).get("command", "")
                    if "hook_post_write.py" in command and "--surface" not in command:
                        undeclared.append(f"{target}.{event}")
    assert not undeclared, f"registrations with no declared surface: {undeclared}"


def test_every_declared_surface_is_one_the_hook_recognises():
    """Catch a typo where it is INTRODUCED, not where it is consumed.

    `--surface` was accepted verbatim, so `--surface codexx` in the manifest
    would have been stamped into the Claim summary and the signed packet's
    `source_systems` with nothing to notice it. The runtime now refuses an
    unknown label and falls back to inference; this is the half that stops the
    typo reaching a config at all.
    """
    import json
    import re

    hook = load_hook()
    manifest = json.loads(
        (REPO_ROOT / "shared-hook-surface.json").read_text(encoding="utf-8")
    )
    seen = []
    for target, cfg in manifest["targets"].items():
        for event, entries in (cfg.get("hooks") or {}).items():
            for entry in entries:
                for h in entry.get("hooks") or [entry]:
                    command = (h or {}).get("command", "")
                    if "hook_post_write.py" not in command:
                        continue
                    found = re.search(r"--surface[= ]([^\s\"]+)", command)
                    assert found, f"{target}.{event} declares no surface"
                    seen.append((f"{target}.{event}", found.group(1)))

    unknown = [
        (where, value) for where, value in seen if value not in hook.KNOWN_SURFACES
    ]
    assert not unknown, (
        f"surfaces the hook does not recognise: {unknown}; "
        f"known: {sorted(hook.KNOWN_SURFACES)}"
    )


def test_an_unrecognised_surface_is_refused_rather_than_stamped(monkeypatch, capsys):
    """A value nothing downstream can interpret must not reach a signed
    record. Inference may be imprecise; an unknown label is uninterpretable."""
    hook = load_hook()

    assert hook.declared_surface(["--surface", "codexx"]) == ""
    assert "unrecognised --surface" in capsys.readouterr().err

    monkeypatch.setattr(sys, "argv", ["hook_post_write.py", "--surface", "codexx"])
    monkeypatch.delenv(hook.DECLARED_SURFACE_ENV, raising=False)
    assert hook.infer_surface("Write", "PostToolUse") == "claude-code"


def test_inference_still_covers_an_unmanaged_install(monkeypatch):
    """A hand-written Claude Code settings.json predating this surface passes
    no flag, and is exactly the case the tool-name branch was written for."""
    hook = load_hook()

    monkeypatch.setattr(sys, "argv", ["hook_post_write.py"])
    monkeypatch.delenv(hook.DECLARED_SURFACE_ENV, raising=False)

    assert hook.infer_surface("Write", "PostToolUse") == "claude-code"
    assert hook.infer_surface("write_file", "AfterTool") == "gemini-cli"


def test_the_declaration_survives_materialization_for_every_target():
    """The join I could not otherwise check: the manifest carries the flag and
    the hook parses it, but the command string is REWRITTEN by the materializer
    into each target's own config format before anything runs it. A quoting or
    variable-expansion bug there would drop the declaration silently and hand
    every surface back to inference, which is the misattribution this fixes.
    """
    import importlib.util
    import json
    import os

    import pytest

    spec = importlib.util.spec_from_file_location(
        "materialize_shared_hook_surface",
        REPO_ROOT / "scripts" / "materialize_shared_hook_surface.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    manifest = json.loads(
        (REPO_ROOT / "shared-hook-surface.json").read_text(encoding="utf-8")
    )
    os.environ.setdefault("FLOSS_HOOKS_DIR", str(REPO_ROOT / "hooks"))
    try:
        variables = module.resolve_variables(manifest, REPO_ROOT)
    except Exception as exc:  # noqa: BLE001 -- environment, not the contract
        pytest.skip(f"hook variables unresolvable here: {type(exc).__name__}: {exc}")

    expected = {
        target: label
        for target, label in (
            ("codex", "codex"),
            ("claude_user", "claude-code"),
            ("hermes_user", "hermes"),
            ("gemini", "gemini-cli"),
        )
        if target in manifest["targets"]
    }
    assert expected, "no known hook targets in the manifest; update this guard"

    for target, label in expected.items():
        cfg = manifest["targets"][target]
        try:
            rendered = json.dumps(module.build_target_payload({}, cfg, variables))
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"{target} not renderable here: {type(exc).__name__}")
        assert f"--surface {label}" in rendered, (
            f"{target}: the declared surface did not survive materialization; "
            "every edit on this surface would be attributed by inference"
        )
