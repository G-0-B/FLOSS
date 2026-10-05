"""Dry-run tests for `-Only` on start_mcp_daemons.ps1 and stop_mcp_daemons.ps1.

Review round 2 (R2-02, R2-03): a room deployment must touch only the room,
through the scripts' own interpreter, path and identity handling.

Nothing is started or stopped. -DryRun returns before any launch or kill, and
the environment makes a regression harmless as well: FLOSS_PYTHON is
where.exe, PATH holds only System32 (no `omniroute`, no `python`), and
FLOSS_AGENT_DIR is an empty temp directory, so no PID file names a process.

Production change that would make these fail: `-Only room` starting or
stopping anything besides the room, a dry run reaching a launch, the default
selection dropping a daemon the scheduled task relies on, or the room log
resolving somewhere other than the workspace intake mouth.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows daemon scripts")

FLOSS_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = FLOSS_ROOT / "scripts"
SYSTEM_ROOT = Path(os.environ.get("SystemRoot", r"C:\Windows"))
SYSTEM32 = SYSTEM_ROOT / "System32"
SHELLS = [exe for exe in (shutil.which("powershell"), shutil.which("pwsh")) if exe]
ROOM = "[FLOSS MCP] WOULD_START packages.coordination_room.server (coordination room (:7334))"


def _intake_log() -> str:
    # Same rule as the launcher: a checkout under FLOSS\.worktrees\<name> pins
    # the log three levels up, any other checkout one level up.
    root = FLOSS_ROOT
    intake = root.parent.parent.parent if "\\.worktrees\\" in str(root).lower() else root.parent
    return str(intake / ".agent-surface" / "rooms" / "default" / "events.jsonl")


def _run(shell: str, script: str, *args: str, agent_dir: Path) -> subprocess.CompletedProcess:
    env = {
        "SystemRoot": str(SYSTEM_ROOT),
        "PATH": f"{SYSTEM32};{SYSTEM32 / 'WindowsPowerShell' / 'v1.0'}",
        "FLOSS_AGENT_DIR": str(agent_dir),
        "FLOSS_PYTHON": str(SYSTEM32 / "where.exe"),
        "USERPROFILE": str(agent_dir),
        "TEMP": str(agent_dir),
        "TMP": str(agent_dir),
    }
    return subprocess.run(
        [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-File", str(SCRIPTS / script), *args],
        capture_output=True,
        text=True,
        env=env,
        # Not the checkout: with this bare environment Windows creates a literal
        # `%SystemDrive%` directory in the working directory on a launch.
        cwd=str(agent_dir),
        timeout=120,
    )


def _lines(done: subprocess.CompletedProcess, marker: str) -> list[str]:
    return [line.strip() for line in done.stdout.splitlines() if marker in line]


shells = pytest.mark.parametrize(
    "shell", SHELLS or [pytest.param("", marks=pytest.mark.skip(reason="no PowerShell"))]
)


@shells
def test_start_only_room_considers_nothing_but_the_room(shell: str, tmp_path: Path):
    done = _run(shell, "start_mcp_daemons.ps1", "-Only", "room", "-DryRun", agent_dir=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert _lines(done, "WOULD_START") == [ROOM]
    assert "OmniRoute not selected (-Only)" in done.stdout
    assert f"coordination room log: {_intake_log()}" in done.stdout
    assert "nothing was started (selected: room)" in done.stdout


@shells
def test_start_default_still_considers_every_daemon(shell: str, tmp_path: Path):
    done = _run(shell, "start_mcp_daemons.ps1", "-DryRun", agent_dir=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    starts = _lines(done, "WOULD_START")
    assert [s.split()[3] for s in starts] == [
        "packages.metacoordinator_mcp.server",
        "packages.reasoning_ensemble.mcp_server",
        "packages.coordination_room.server",
        "omniroute",
    ]


@shells
def test_stop_only_room_considers_nothing_but_the_room(shell: str, tmp_path: Path):
    done = _run(shell, "stop_mcp_daemons.ps1", "-Only", "room", "-DryRun", agent_dir=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert _lines(done, "WOULD_STOP") == [
        "[FLOSS MCP] WOULD_STOP coordination_room.pid (only if its identity check says OURS)"
    ]
    assert "OmniRoute not selected (-Only)" in done.stdout
    assert "nothing was stopped (selected: room)" in done.stdout


@shells
def test_stop_default_still_considers_every_daemon(shell: str, tmp_path: Path):
    done = _run(shell, "stop_mcp_daemons.ps1", "-DryRun", agent_dir=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert [s.split()[3] for s in _lines(done, "WOULD_STOP")] == [
        "consensus.pid",
        "reasoning_ensemble.pid",
        "coordination_room.pid",
        "omniroute",
    ]


@shells
def test_real_stop_only_room_leaves_other_records_alone(shell: str, tmp_path: Path):
    """Not a dry run. The room has no record here, so nothing is stopped; the
    point is that the other daemons' records are neither acted on nor changed."""
    others = {"consensus.pid": "4242", "reasoning_ensemble.pid": "4243", "omniroute.pid": "4244"}
    for name, value in others.items():
        (tmp_path / name).write_text(value, encoding="ascii")
    done = _run(shell, "stop_mcp_daemons.ps1", "-Only", "room", agent_dir=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert {p.name: p.read_text(encoding="ascii") for p in tmp_path.glob("*.pid")} == others
    assert "Stopped: room." in done.stdout


@shells
def test_real_start_only_room_attempts_only_the_room(shell: str, tmp_path: Path):
    """Not a dry run. FLOSS_PYTHON is where.exe, so the one launch attempted
    exits at once and is reported; no other launch is attempted."""
    (tmp_path / "consensus.pid").write_text("4242", encoding="ascii")
    done = _run(shell, "start_mcp_daemons.ps1", "-Only", "room", agent_dir=tmp_path)
    assert done.returncode == 1, done.stdout + done.stderr
    assert "coordination room (:7334) exited immediately" in done.stdout
    for other in ("consensus gateway", "reasoning ensemble", "OmniRoute started", "WOULD_START"):
        assert other not in done.stdout
    assert (tmp_path / "consensus.pid").read_text(encoding="ascii") == "4242"
    # A failed selected start reports itself and claims no success.
    assert "STARTUP INCOMPLETE" in done.stdout
    assert "Started or already running" not in done.stdout
    assert "Daemons started" not in done.stdout


@shells
def test_real_stop_with_no_arguments_keeps_its_original_success_line(shell: str, tmp_path: Path):
    """Review round 3, R3-01: the scheduled-task style run (no -Only) still
    prints the line packages/tests/test_mcp_daemon.py expects, because every
    daemon was selected and none had a record to act on."""
    done = _run(shell, "stop_mcp_daemons.ps1", agent_dir=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "All daemons stopped. PID files cleaned." in done.stdout


@shells
def test_several_names_go_in_one_comma_separated_argument(shell: str, tmp_path: Path):
    """Review round 6 (Grok), m2: under `-File`, `-Only a,b` arrives as one
    string. It must select both, not be rejected."""
    start = _run(shell, "start_mcp_daemons.ps1", "-Only", "room,ensemble", "-DryRun", agent_dir=tmp_path)
    assert start.returncode == 0, start.stdout + start.stderr
    assert [s.split()[3] for s in _lines(start, "WOULD_START")] == [
        "packages.reasoning_ensemble.mcp_server",
        "packages.coordination_room.server",
    ]
    stop = _run(shell, "stop_mcp_daemons.ps1", "-Only", "room,ensemble", "-DryRun", agent_dir=tmp_path)
    assert [s.split()[3] for s in _lines(stop, "WOULD_STOP")] == [
        "reasoning_ensemble.pid",
        "coordination_room.pid",
    ]


@shells
@pytest.mark.parametrize("script", ["start_mcp_daemons.ps1", "stop_mcp_daemons.ps1"])
def test_a_second_bare_name_is_an_error_not_a_silent_drop(shell: str, script: str, tmp_path: Path):
    """`-Only room ensemble` used to act on `room` alone and say nothing."""
    done = _run(shell, script, "-Only", "room", "ensemble", "-DryRun", agent_dir=tmp_path)
    assert done.returncode != 0
    assert "WOULD_" not in done.stdout


@shells
@pytest.mark.parametrize("script", ["start_mcp_daemons.ps1", "stop_mcp_daemons.ps1"])
def test_unknown_daemon_name_is_refused_before_anything_runs(shell: str, script: str, tmp_path: Path):
    done = _run(shell, script, "-Only", "everything", "-DryRun", agent_dir=tmp_path)
    assert done.returncode != 0
    assert "WOULD_" not in done.stdout


@shells
def test_a_real_run_writes_nothing_where_pytest_was_started(shell: str, tmp_path: Path, monkeypatch):
    """Found while executing the plan: these runs use a bare environment (no
    SystemDrive, no ProgramData), and on a launch Windows then creates a literal
    `%SystemDrive%` directory in the process's working directory. Inherited from
    pytest, that directory was the checkout. It must be the test's own."""
    started_from = tmp_path / "started-from"
    started_from.mkdir()
    agent = tmp_path / "agent"
    agent.mkdir()
    monkeypatch.chdir(started_from)
    _run(shell, "start_mcp_daemons.ps1", "-Only", "room", agent_dir=agent)
    assert list(started_from.iterdir()) == []
