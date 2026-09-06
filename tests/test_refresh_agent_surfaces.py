"""CLI contract tests for scripts/refresh_agent_surfaces.py."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "refresh_agent_surfaces.py"

# The materializer steps run against the WORKSPACE, which is the parent of this
# repository -- `.mcp.json`, `.claude/`, `.gemini/` and the OpenCode roster all
# live there, in a different repository. Tests that actually execute a step
# therefore need that two-repo layout to exist.
#
# CI checks out FLOSS alone, so the parent directory is bare and the ai-roster
# step fails with `AIRosterError: Missing file: .../.mcp.json`. That is the
# step behaving correctly on an incomplete workspace, not a regression, so
# these skip rather than fail. The twelve pure-function and argument-parsing
# tests in this file are unaffected and still run everywhere.
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
HAS_WORKSPACE = (WORKSPACE_ROOT / ".mcp.json").exists()
requires_workspace = pytest.mark.skipif(
    not HAS_WORKSPACE,
    reason=(
        f"needs the workspace layout: no .mcp.json at {WORKSPACE_ROOT}. "
        "Run from a checkout nested inside the FLOSSI0ULLK workspace."
    ),
)


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _load_runner():
    """Import scripts/refresh_agent_surfaces.py as a module, in-process.

    Used only for unit-testing pure functions (`build_command`, `summarize`)
    directly. No subprocess is spawned and no materializer runs.
    """
    spec = importlib.util.spec_from_file_location("refresh_agent_surfaces", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_list_names_every_step():
    result = run("--list")
    assert result.returncode == 0
    for name in (
        "agent-surface",
        "context",
        "skill",
        "agent-memory",
        "hook",
        "ai-roster",
    ):
        assert name in result.stdout


def test_only_rejects_unknown_step():
    result = run("--only", "nope")
    assert result.returncode != 0
    assert "nope" in (result.stderr + result.stdout)


@requires_workspace
def test_dry_run_only_exits_zero_and_names_the_step():
    """A pure --dry-run run (no --check) always exits 0: materializers report
    their plan without erroring, regardless of whether writes are pending."""
    result = run("--only", "ai-roster", "--dry-run")
    assert result.returncode == 0
    assert "ai-roster" in result.stdout


@requires_workspace
def test_dry_run_only_summary_says_planned_not_clean():
    """Regression test: a --dry-run-only run must not claim to be 'clean'
    when it has pending writes it never applied — it must say 'planned'."""
    result = run("--only", "ai-roster", "--dry-run")
    assert "planned" in result.stdout
    assert "clean" not in result.stdout


@requires_workspace
def test_check_and_dry_run_together_uses_check_semantics():
    """--check takes precedence over --dry-run when both are given.

    Asserts only the wording contract (CHECK vocabulary, never PLAN). The
    exit code is deliberately NOT asserted: it depends on whether the
    workspace happens to be drifted at the moment the test runs, and an
    earlier version of this test pinned exit 1 against ambient drift --
    which broke the moment a real propagation run cleaned that drift up.
    Exit-code semantics are covered by the `summarize` unit tests, which
    are independent of workspace state.
    """
    result = run("--only", "ai-roster", "--check", "--dry-run")
    assert "CHECK" in result.stdout
    assert "PLAN" not in result.stdout
    assert result.returncode in (0, 1)


def test_build_command_includes_user_scope_for_agent_surface():
    runner = _load_runner()
    command = runner.build_command("agent-surface", "x.py", False, False, True)
    assert "--include-user-scope" in command


def test_build_command_excludes_user_scope_for_other_steps():
    # `skill` used to be the example here, because that materializer had no
    # scope support. It has both the flag and two user-scope targets now
    # (~/.codex/skills, the Hermes skills directory), so the example moved to a
    # step that genuinely does not accept the flag -- forwarding it there would
    # just fail with an argparse error.
    # scripts/tests/test_refresh_runner_forwards_user_scope.py derives the whole
    # set from the materializer sources, so this stays honest as they change.
    runner = _load_runner()
    command = runner.build_command("context", "x.py", False, False, True)
    assert "--include-user-scope" not in command
    assert "context" not in runner.USER_SCOPE_STEPS


def test_build_command_composes_check_and_dry_run_flags():
    runner = _load_runner()

    command = runner.build_command("hook", "x.py", True, True, False)
    assert "--check" in command
    assert "--dry-run" in command
    assert "--include-user-scope" not in command

    command_neither = runner.build_command("hook", "x.py", False, False, False)
    assert "--check" not in command_neither
    assert "--dry-run" not in command_neither

    # include_user_scope requested but step is not agent-surface: still excluded
    command_agent_surface_check_only = runner.build_command(
        "agent-surface", "x.py", True, False, False
    )
    assert "--check" in command_agent_surface_check_only
    assert "--include-user-scope" not in command_agent_surface_check_only


def test_summarize_all_ok():
    runner = _load_runner()
    lines, exit_code = runner.summarize(
        [("agent-surface", 0), ("skill", 0)], check=False, dry_run=False
    )
    assert exit_code == 0
    assert any("clean" in line for line in lines)
    assert not any("planned" in line for line in lines)


def test_summarize_drift_under_check():
    runner = _load_runner()
    lines, exit_code = runner.summarize(
        [("agent-surface", 0), ("ai-roster", 1)], check=True, dry_run=False
    )
    assert exit_code == 1
    joined = "\n".join(lines)
    assert "ai-roster" in joined
    assert "DRIFT" in joined
    assert "step error" in joined  # ambiguity caveat must be visible in the label


def test_summarize_hard_failure_uncommon_exit_code():
    runner = _load_runner()
    lines, exit_code = runner.summarize(
        [("agent-surface", 0), ("hook", 2)], check=False, dry_run=False
    )
    assert exit_code == 1
    joined = "\n".join(lines)
    assert "hook" in joined
    assert "FAILED (exit 2)" in joined


def test_summarize_mixed_batch():
    runner = _load_runner()
    lines, exit_code = runner.summarize(
        [
            ("agent-surface", 1),
            ("context", 0),
            ("skill", 2),
        ],
        check=True,
        dry_run=False,
    )
    assert exit_code == 1
    joined = "\n".join(lines)
    assert "2 of 3 step(s) need attention." in joined
    assert "DRIFT" in joined  # agent-surface, code 1, under check
    assert "FAILED (exit 2)" in joined  # skill, code 2


def test_summarize_dry_run_only_reports_planned():
    runner = _load_runner()
    lines, exit_code = runner.summarize(
        [("agent-surface", 0), ("ai-roster", 0)], check=False, dry_run=True
    )
    assert exit_code == 0
    joined = "\n".join(lines)
    assert "planned" in joined
    assert "clean" not in joined


def test_summarize_dry_run_only_still_surfaces_a_failing_step():
    """A step that fails during dry-run must not hide behind "planned".

    Dry-run materializers normally exit 0 regardless of what they would
    write, so a nonzero code here means a genuine error -- it has to beat
    the "planned" framing, not be absorbed by it.
    """
    runner = _load_runner()
    lines, exit_code = runner.summarize(
        [("agent-surface", 0), ("ai-roster", 1)], check=False, dry_run=True
    )
    assert exit_code == 1
    joined = "\n".join(lines)
    assert "FAILED" in joined
    assert "need attention" in joined


def test_summarize_check_and_dry_run_together_prefers_check_wording():
    runner = _load_runner()
    lines, exit_code = runner.summarize(
        [("agent-surface", 0), ("ai-roster", 0)], check=True, dry_run=True
    )
    assert exit_code == 0
    joined = "\n".join(lines)
    assert "clean" in joined
    assert "planned" not in joined
