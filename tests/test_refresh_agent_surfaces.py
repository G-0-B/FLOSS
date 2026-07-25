"""CLI contract tests for scripts/refresh_agent_surfaces.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "refresh_agent_surfaces.py"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        capture_output=True,
        text=True,
        check=False,
    )


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


def test_dry_run_check_exits_cleanly():
    result = run("--only", "ai-roster", "--dry-run")
    assert result.returncode in (0, 1)
    assert "ai-roster" in result.stdout


def test_build_command_includes_user_scope_for_agent_surface():
    sys.path.insert(0, str(RUNNER.parent))
    try:
        import refresh_agent_surfaces as runner

        command = runner.build_command("agent-surface", "x.py", False, False, True)
        assert "--include-user-scope" in command
    finally:
        sys.path.remove(str(RUNNER.parent))


def test_build_command_excludes_user_scope_for_other_steps():
    sys.path.insert(0, str(RUNNER.parent))
    try:
        import refresh_agent_surfaces as runner

        command = runner.build_command("skill", "x.py", False, False, True)
        assert "--include-user-scope" not in command
    finally:
        sys.path.remove(str(RUNNER.parent))


def test_build_command_composes_check_and_dry_run_flags():
    sys.path.insert(0, str(RUNNER.parent))
    try:
        import refresh_agent_surfaces as runner

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
    finally:
        sys.path.remove(str(RUNNER.parent))
