"""TDD tests for the shared MCP daemon bootstrap module.

Tests PID-singleton enforcement and audit-append functionality.
Run: C:\\Python313\\python.exe -m pytest FLOSS/packages/tests/test_mcp_daemon.py -v
"""

import builtins
import os
import sys
import tempfile
import time

import pytest
from pathlib import Path

# Ensure workspace root is on sys.path so `from packages import mcp_daemon` works
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from packages import mcp_daemon  # noqa: E402


def test_stale_pid_is_overwritten(tmp_path, monkeypatch):
    """A stale (dead) PID file should be overwritten and claim succeed."""
    from packages import mcp_daemon

    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    (tmp_path / "x.pid").write_text("999999999")  # almost-certainly-dead pid
    assert mcp_daemon.claim_singleton("x.pid") is True
    assert (tmp_path / "x.pid").read_text().strip() == str(os.getpid())


def test_live_pid_blocks_second_claim(tmp_path, monkeypatch):
    """Our own PID is alive — a second claim for the same slot must fail."""
    from packages import mcp_daemon

    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    (tmp_path / "y.pid").write_text(str(os.getpid()))  # our pid = alive
    assert mcp_daemon.claim_singleton("y.pid") is False


def test_audit_appender_writes_jsonl(tmp_path, monkeypatch):
    """audit_appender should write one JSONL line per call."""
    from packages import mcp_daemon

    sink = tmp_path / "audit.jsonl"
    append = mcp_daemon.audit_appender(str(sink))
    append("submit_claim", {"claim_id": "test-123"})
    append("cast_vote", {"weight": 0.5})

    lines = sink.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    import json

    row0 = json.loads(lines[0])
    assert row0["tool"] == "submit_claim"
    assert row0["payload"]["claim_id"] == "test-123"
    assert "ts" in row0
    row1 = json.loads(lines[1])
    assert row1["tool"] == "cast_vote"


def test_audit_appender_best_effort_no_crash(tmp_path):
    """audit_appender must never raise — audit is defense-in-depth, not fatal."""
    from packages import mcp_daemon

    # Make the parent a FILE so the sink path cannot be created at all.
    blocker = tmp_path / "blocker"
    blocker.write_text("x")
    impossible_sink = blocker / "audit.jsonl"  # blocker is a file, not a dir
    append = mcp_daemon.audit_appender(str(impossible_sink))
    # Should not raise
    append("some_tool", {"key": "val"})


def test_audited_preserves_tool_signature_for_schema_generation():
    """The audit wrapper must not destroy the tool schema FastMCP derives.

    FastMCP builds each tool's inputSchema from the registered callable's
    signature and annotations. A wrapper that does not set `__wrapped__`
    registers as `(*args, **kwargs)`, which silently strips every parameter
    from the published schema — the tool still appears, but with no arguments.
    functools.wraps is what prevents that, so assert it directly.
    """
    import inspect

    from packages import mcp_daemon

    def sample(claim_text: str, blast_radius: str = "Local") -> dict:
        """Sample docstring."""
        return {"claim_text": claim_text, "blast_radius": blast_radius}

    wrapped = mcp_daemon.audited(sample, lambda *_: None)

    assert wrapped.__name__ == "sample"
    assert (wrapped.__doc__ or "").strip().startswith("Sample docstring")
    assert str(inspect.signature(wrapped)) == str(inspect.signature(sample))
    assert wrapped.__annotations__ == sample.__annotations__
    assert wrapped("x", blast_radius="System")["blast_radius"] == "System"


def test_audited_records_named_arguments(tmp_path):
    """Positional args are bound to parameter names so rows stay readable."""
    import json

    from packages import mcp_daemon

    sink = tmp_path / "audit.jsonl"
    append = mcp_daemon.audit_appender(str(sink))

    def submit(proposer: str, summary: str = "s") -> str:
        return "ok"

    mcp_daemon.audited(submit, append)("claude", summary="hello")

    row = json.loads(sink.read_text(encoding="utf-8").strip())
    assert row["tool"] == "submit"
    # bound by name even though `proposer` was passed positionally
    assert row["payload"] == {"proposer": "claude", "summary": "hello"}


def test_audited_bounds_values_and_survives_hostile_repr(tmp_path):
    """A huge Claim body must not be copied wholesale into the audit sink."""
    import json

    from packages import mcp_daemon

    sink = tmp_path / "audit.jsonl"
    append = mcp_daemon.audit_appender(str(sink))

    class Hostile:
        def __repr__(self):
            raise RuntimeError("boom")

    def tool(body: str, obj: object = None) -> str:
        return "ok"

    mcp_daemon.audited(tool, append)("A" * 5000, obj=Hostile())

    row = json.loads(sink.read_text(encoding="utf-8").strip())
    assert len(row["payload"]["body"]) < 1000
    assert row["payload"]["body"].endswith("<truncated>")
    assert row["payload"]["obj"] == "<unrepresentable>"


def test_audited_wraps_async_tools(tmp_path):
    """Async tools must stay async — awaiting a sync wrapper breaks registration."""
    import asyncio
    import inspect

    import json

    from packages import mcp_daemon

    sink = tmp_path / "audit.jsonl"
    append = mcp_daemon.audit_appender(str(sink))

    async def atool(x: int) -> int:
        return x + 1

    wrapped = mcp_daemon.audited(atool, append)
    assert inspect.iscoroutinefunction(wrapped)
    assert asyncio.run(wrapped(1)) == 2
    assert json.loads(sink.read_text(encoding="utf-8").strip())["payload"] == {"x": 1}


def test_registered_consensus_tools_are_audited():
    """Regression: the consensus server must register through the audited path.

    This is the check that would have caught the original defect — audit_appender
    existed and was unit-tested, but had no production caller, so _AUDIT_SINK was
    dead config and every tool call bypassed the audit trail.
    """
    from packages.metacoordinator_mcp import server

    if server.mcp is None:
        return  # MCP SDK not installed in this environment

    import asyncio

    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert "submit_claim" in names
    # schema must survive the wrapper
    tools = {t.name: t for t in asyncio.run(server.mcp.list_tools())}
    props = set((tools["submit_claim"].inputSchema or {}).get("properties", {}))
    assert {"proposer", "summary", "blast_radius"} <= props


def test_claim_singleton_blocks_while_a_live_holder_exists(tmp_path, monkeypatch):
    """A live PID in the file must block a second claimant."""
    from packages import mcp_daemon

    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    monkeypatch.setattr(mcp_daemon.signal, "signal", lambda *a, **k: None)
    monkeypatch.setattr(mcp_daemon.atexit, "register", lambda *a, **k: None)
    # Anything other than us, reported alive.
    monkeypatch.setattr(mcp_daemon, "_pid_alive", lambda pid: pid != os.getpid())

    (tmp_path / "slot.pid").write_text("999999", encoding="utf-8")

    assert mcp_daemon.claim_singleton("slot.pid") is False
    # The live holder's claim must be left intact.
    assert (tmp_path / "slot.pid").read_text(encoding="utf-8").strip() == "999999"


def test_claim_singleton_reclaims_a_dead_holder(tmp_path, monkeypatch):
    """A stale PID file must not permanently block the slot."""
    from packages import mcp_daemon

    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    monkeypatch.setattr(mcp_daemon.signal, "signal", lambda *a, **k: None)
    monkeypatch.setattr(mcp_daemon.atexit, "register", lambda *a, **k: None)
    monkeypatch.setattr(mcp_daemon, "_pid_alive", lambda pid: False)

    (tmp_path / "slot.pid").write_text("999999", encoding="utf-8")

    assert mcp_daemon.claim_singleton("slot.pid") is True
    assert (tmp_path / "slot.pid").read_text(encoding="utf-8").strip() == str(
        os.getpid()
    )


def test_release_does_not_delete_another_process_claim(tmp_path, monkeypatch):
    """Cleanup must be ownership-checked.

    The original handler unlinked unconditionally, so a launcher that lost the
    port bind deleted the SURVIVING daemon's pid file on its way out, defeating
    duplicate prevention for every later start.
    """
    from packages import mcp_daemon

    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    monkeypatch.setattr(mcp_daemon.signal, "signal", lambda *a, **k: None)
    monkeypatch.setattr(mcp_daemon, "_pid_alive", lambda pid: False)

    registered = []
    monkeypatch.setattr(mcp_daemon.atexit, "register", lambda fn: registered.append(fn))

    assert mcp_daemon.claim_singleton("slot.pid") is True
    assert registered, "cleanup handler was never registered"

    # Another process takes over the slot, then our handler runs.
    (tmp_path / "slot.pid").write_text("424242", encoding="utf-8")
    registered[0]()

    assert (tmp_path / "slot.pid").exists(), "released a claim we no longer owned"
    assert (tmp_path / "slot.pid").read_text(encoding="utf-8").strip() == "424242"


def test_a_reused_pid_does_not_block_the_slot(tmp_path, monkeypatch):
    """A live PID is not proof the daemon is running.

    After a crash or a reboot the PID file survives and the OS reassigns that
    number to something unrelated. `_pid_alive()` then reported the daemon as
    running while its port went unserved: the launcher exited successfully and
    the stop script was aimed at an innocent process.

    Here the PID file names a genuinely live process (our own) but the recorded
    creation token belongs to a different one, so the holder is provably not
    the daemon and the slot must be reclaimable.
    """
    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    pid_path = tmp_path / "reused.pid"
    pid_path.write_text(str(os.getpid()), encoding="utf-8")
    mcp_daemon._identity_path(pid_path).write_text(
        "not-the-token-of-this-process", encoding="utf-8"
    )

    assert mcp_daemon.claim_singleton("reused.pid") is True
    assert pid_path.read_text(encoding="utf-8").strip() == str(os.getpid())


def test_a_matching_identity_still_blocks(tmp_path, monkeypatch):
    """The guard must not be a blanket permission to double-start."""
    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    pid_path = tmp_path / "live.pid"
    pid_path.write_text(str(os.getpid()), encoding="utf-8")
    token = mcp_daemon._process_start_token(os.getpid())
    if token is None:
        pytest.skip("no process-creation token on this platform")
    mcp_daemon._identity_path(pid_path).write_text(token, encoding="utf-8")

    assert mcp_daemon.claim_singleton("live.pid") is False


def test_a_legacy_pid_file_without_a_sidecar_keeps_blocking(tmp_path, monkeypatch):
    """Unverifiable must stay conservative.

    A false 'stale' verdict starts a second daemon on a bound port. A false
    'live' verdict is a file a human can delete. When identity cannot be
    established -- legacy PID file, unsupported platform, unopenable process --
    the old blocking behaviour is the safe one.
    """
    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    pid_path = tmp_path / "legacy.pid"
    pid_path.write_text(str(os.getpid()), encoding="utf-8")
    assert not mcp_daemon._identity_path(pid_path).exists()

    assert mcp_daemon.claim_singleton("legacy.pid") is False


def test_an_empty_sidecar_is_treated_as_unverifiable(tmp_path, monkeypatch):
    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    pid_path = tmp_path / "empty.pid"
    pid_path.write_text(str(os.getpid()), encoding="utf-8")
    mcp_daemon._identity_path(pid_path).write_text("   ", encoding="utf-8")

    assert mcp_daemon.claim_singleton("empty.pid") is False


def test_a_claim_records_its_own_identity(tmp_path, monkeypatch):
    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    assert mcp_daemon.claim_singleton("fresh.pid") is True

    pid_path = tmp_path / "fresh.pid"
    token = mcp_daemon._process_start_token(os.getpid())
    if token is None:
        pytest.skip("no process-creation token on this platform")
    assert mcp_daemon._identity_path(pid_path).read_text(encoding="utf-8") == token


def test_a_dead_pid_token_is_unavailable():
    assert mcp_daemon._process_start_token(999999999) is None
    assert mcp_daemon._process_start_token(0) is None
    assert mcp_daemon._process_start_token(-1) is None


def test_the_token_is_stable_across_calls():
    """A token that changed between calls would make every holder look reused."""
    first = mcp_daemon._process_start_token(os.getpid())
    if first is None:
        pytest.skip("no process-creation token on this platform")
    assert first == mcp_daemon._process_start_token(os.getpid())


def test_the_stale_sidecar_is_removed_before_the_pid_file(tmp_path, monkeypatch):
    """Reopening the PID slot must not leave the old token behind.

    Unlinking only the PID file leaves a window: launcher A wins the exclusive
    create and writes its new PID, launcher B still sees the STALE token beside
    it, judges A's valid claim stale, unlinks it, and claims the slot too. Both
    return success and race for the same port.
    """
    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    pid_path = tmp_path / "race.pid"
    pid_path.write_text("999999999", encoding="utf-8")  # dead pid
    mcp_daemon._identity_path(pid_path).write_text("stale-token", encoding="utf-8")

    assert mcp_daemon.claim_singleton("race.pid") is True
    # The sidecar now describes US, not the dead holder.
    token = mcp_daemon._process_start_token(os.getpid())
    if token is None:
        pytest.skip("no process-creation token on this platform")
    assert mcp_daemon._identity_path(pid_path).read_text(encoding="utf-8") == token


def test_identity_cli_exit_codes(tmp_path, monkeypatch):
    """0 = provably ours, 1 = provably not, 2 = cannot tell.

    The stop script depends on these exactly, and it must treat 2 as "do not
    kill" for the same reason claim_singleton treats it as "still blocked".
    """
    pid_path = tmp_path / "cli.pid"

    def run() -> int:
        monkeypatch.setattr(
            sys, "argv", ["mcp_daemon", "--check-identity", str(pid_path)]
        )
        return mcp_daemon._identity_cli()

    pid_path.write_text(str(os.getpid()), encoding="utf-8")
    token = mcp_daemon._process_start_token(os.getpid())
    if token is None:
        pytest.skip("no process-creation token on this platform")

    mcp_daemon._identity_path(pid_path).write_text(token, encoding="utf-8")
    assert run() == 0, "matching token must be provably ours"

    mcp_daemon._identity_path(pid_path).write_text("not-the-token", encoding="utf-8")
    assert run() == 1, "mismatched token must be provably NOT ours"

    mcp_daemon._identity_path(pid_path).unlink()
    assert run() == 2, "no sidecar means cannot tell, never a kill"

    pid_path.write_text("999999999", encoding="utf-8")
    mcp_daemon._identity_path(pid_path).write_text("anything", encoding="utf-8")
    assert run() == 1, "a dead pid is provably not our running daemon"

    pid_path.write_text("not-a-number", encoding="utf-8")
    assert run() == 2


def test_identity_cli_prints_the_verdict_on_stdout():
    """The exit code alone cannot distinguish a verdict from a failed launch.

    A checker that could not import this module also exits 1, and PowerShell does
    not enter `catch` for a failed external command -- it just records the
    status. Reading the status therefore turned "wrong interpreter" into "proven
    mismatch", which deleted the PID files and left live daemons unfindable: the
    exact outcome the identity check was added to prevent.

    A process that never ran cannot print a token it never produced.
    """
    import subprocess

    tmp = Path(tempfile.mkdtemp())
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])
    try:
        time.sleep(1.2)
        pid_path = tmp / "tok.pid"
        pid_path.write_text(str(proc.pid), encoding="utf-8")
        token = mcp_daemon._process_start_token(proc.pid)
        if token is None:
            pytest.skip("no process-creation token on this platform")

        def run():
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "packages.mcp_daemon",
                    "--check-identity",
                    str(pid_path),
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).resolve().parents[2]),
            )
            return result.stdout.strip(), result.returncode

        mcp_daemon._identity_path(pid_path).write_text(token, encoding="utf-8")
        assert run() == ("OURS", 0)

        mcp_daemon._identity_path(pid_path).write_text("bogus", encoding="utf-8")
        assert run() == ("FOREIGN", 1)

        mcp_daemon._identity_path(pid_path).unlink()
        assert run() == ("UNKNOWN", 2)
    finally:
        proc.kill()


def test_a_failed_checker_launch_produces_no_token():
    """Exit 1 with no token must not be readable as FOREIGN."""
    import subprocess

    result = subprocess.run(
        [sys.executable, "-c", "import sys; sys.exit(1)"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, "a failed launch shares the FOREIGN exit code"
    assert result.stdout.strip() == "", "but it cannot produce the token"


def test_the_stop_script_resolves_the_repository_interpreter():
    """Bare `python` may not be the interpreter the daemons were launched with."""
    script = (
        Path(__file__).resolve().parents[2] / "scripts" / "stop_mcp_daemons.ps1"
    ).read_text(encoding="utf-8")

    assert "FLOSS_PYTHON" in script, "honour the documented interpreter override"
    assert "venv" in script, "then a venv inside the checkout, as the start script does"
    assert "& $py -m packages.mcp_daemon" in script, "not a bare `python`"
    assert "Push-Location $repoRoot" in script, "and run it from the repository"
    assert "$LASTEXITCODE" not in script, "the verdict is the token, not the status"


def test_the_stop_script_does_not_force_kill_shared_node_processes():
    """ "Stop my two daemons" must not take down another agent's live session.

    The agentmemory/JanuScope block matched every node.exe on the host mentioning
    those names and force-killed all of them, checking neither parent liveness
    nor ownership -- the same over-broad match fixed for OmniRoute twenty lines
    above, in the same commit. sweep_mcp_orphans.ps1 already does this properly.
    """
    script = (
        Path(__file__).resolve().parents[2] / "scripts" / "stop_mcp_daemons.ps1"
    ).read_text(encoding="utf-8")

    assert "sweep_mcp_orphans.ps1" in script, "defer to the tool with the predicates"
    for line in script.splitlines():
        if "Stop-Process" in line and not line.strip().startswith("#"):
            assert "agentmemory" not in line and "januscope" not in line


def test_the_stop_script_delegates_the_identity_check():
    """One implementation, two callers.

    A first attempt computed the token in PowerShell and produced a DIFFERENT
    value for the same PID -- `-band 0xFFFFFFFF` does not mask an int64 there.
    An identity check written twice in two languages is the drift the register
    records as FM-4, so the script must call this module rather than reimplement.
    """
    script = (
        Path(__file__).resolve().parents[2] / "scripts" / "stop_mcp_daemons.ps1"
    ).read_text(encoding="utf-8")

    assert "--check-identity" in script, "stop path must consult the identity check"
    assert "GetProcessTimes" not in script, "the token must not be recomputed here"
    assert "ToFileTime" not in script, "the token must not be recomputed here"
    assert "$verdict -ne 'OURS'" in script, "anything but a proven match must not kill"


def test_pid_alive_is_false_for_a_terminated_process():
    """OpenProcess SUCCEEDING is not liveness.

    Found while testing the identity CLI, not reported by review. A terminated
    process stays openable while any handle to it persists, so this returned
    True for daemons that had already exited: claim_singleton reported "already
    running" when nothing was, permanently, and --check-identity said OURS about
    a corpse. GetExitCodeProcess distinguishes them.
    """
    import subprocess

    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    time.sleep(1.0)
    assert mcp_daemon._pid_alive(proc.pid) is True

    proc.kill()
    proc.wait()
    time.sleep(1.0)
    assert (
        mcp_daemon._pid_alive(proc.pid) is False
    ), "a killed and reaped process must not read as alive"
    assert mcp_daemon._pid_alive(999999999) is False
    assert mcp_daemon._pid_alive(os.getpid()) is True


def test_record_identity_writes_a_verifiable_pair(tmp_path):
    """OmniRoute is launched by PowerShell, so nothing recorded its identity."""
    import subprocess

    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])
    try:
        time.sleep(1.0)
        pid_path = tmp_path / "omniroute.pid"

        def run(*args):
            result = subprocess.run(
                [sys.executable, "-m", "packages.mcp_daemon", *args],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).resolve().parents[2]),
            )
            return result.stdout.strip(), result.returncode

        assert run("--record-identity", str(pid_path), str(proc.pid)) == ("RECORDED", 0)
        assert pid_path.read_text(encoding="utf-8").strip() == str(proc.pid)
        assert run("--check-identity", str(pid_path)) == ("OURS", 0)
    finally:
        proc.kill()
        proc.wait()

    time.sleep(1.0)
    after = subprocess.run(
        [
            sys.executable,
            "-m",
            "packages.mcp_daemon",
            "--check-identity",
            str(pid_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[2]),
    )
    assert after.stdout.strip() == "FOREIGN", "a dead recorded PID is not ours"


def test_recording_a_dead_pid_is_refused(tmp_path):
    import subprocess

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "packages.mcp_daemon",
            "--record-identity",
            str(tmp_path / "x.pid"),
            "999999999",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[2]),
    )
    assert result.stdout.strip() == "NOT_RUNNING"
    assert not (tmp_path / "x.pid").exists()


def test_neither_daemon_script_matches_omniroute_by_command_line():
    """Two wrong filters in two commits was the signal to stop filtering.

    First a host-wide `omniroute` match that killed other projects' processes.
    Then a checkout-scoped match that matched NOTHING, because
    `omniroute --no-open` produces a command line naming the global package and
    never the working directory — so our own process was classified foreign and
    left running. Identity is recorded at launch instead.
    """
    scripts = Path(__file__).resolve().parents[2] / "scripts"
    for name in ("start_mcp_daemons.ps1", "stop_mcp_daemons.ps1"):
        text = (scripts / name).read_text(encoding="utf-8")
        assert "CommandLine -match 'omniroute'" not in text, name
        assert "--record-identity" in text or "--check-identity" in text, name


def test_the_start_script_parses_under_windows_powershell_5():
    """`?.` is 7.1+, and 5.1 fails to PARSE the file, so nothing starts at all.

    The documented Scheduled Task registers this with `powershell`, which is 5.1.
    """
    text = (
        Path(__file__).resolve().parents[2] / "scripts" / "start_mcp_daemons.ps1"
    ).read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert "?." not in stripped, f"PowerShell 7-only operator in: {stripped}"


def _script(name: str) -> str:
    return (Path(__file__).resolve().parents[2] / "scripts" / name).read_text(
        encoding="utf-8"
    )


def test_no_stop_process_deletes_a_record_without_confirming(tmp_path):
    """Both kill sites must confirm before removing the record.

    The Python-daemon branch did this and explained why; the OmniRoute branch
    added later used `-ErrorAction SilentlyContinue` and deleted the PID and
    identity regardless, so an access-denied failure left a live process
    unfindable while the script reported it stopped. One file, two branches, one
    of them written without reading the other.
    """
    script = _script("stop_mcp_daemons.ps1")
    kills = [
        line
        for line in script.splitlines()
        if "Stop-Process" in line and not line.strip().startswith("#")
    ]
    assert len(kills) >= 2, "kill sites moved; update this guard"
    for line in kills:
        assert (
            "-ErrorAction Stop" in line
        ), f"a suppressed failure is indistinguishable from success: {line.strip()}"


def test_unknown_identity_is_conservative_in_every_caller():
    """UNKNOWN means occupied, everywhere.

    claim_singleton and the stop path both treat an unverifiable holder as still
    holding. The start path read the same verdict optimistically and launched a
    duplicate, which loses the port bind AFTER --record-identity has overwritten
    the record with its own PID -- leaving the original live, untracked, and
    unstoppable by the companion script.
    """
    start = _script("start_mcp_daemons.ps1")
    stop = _script("stop_mcp_daemons.ps1")

    assert "$omniVerdict -eq 'UNKNOWN'" in start, "start must handle UNKNOWN explicitly"
    assert "not starting a duplicate" in start
    assert "$verdict -ne 'OURS'" in stop, "stop kills only on a proven match"
    assert "refusing to force-kill" in stop


def test_an_empty_in_progress_claim_is_occupied_not_stale(tmp_path, monkeypatch):
    """O_EXCL creates the file before the PID is written.

    A second launcher reading it in that window saw an empty file, converted it
    to -1, called it stale, and unlinked the FIRST launcher's valid claim — so
    both returned success, defeating the guarantee O_EXCL was introduced to
    provide. The one that later loses the port bind then removes the survivor's
    record on exit, leaving a live daemon untracked.
    """
    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    claim = tmp_path / "race.pid"
    claim.write_text("", encoding="utf-8")  # created, PID not yet written

    assert mcp_daemon.claim_singleton("race.pid") is False
    assert claim.exists(), "the in-progress claim must not be reclaimed"


def test_a_genuinely_stale_numeric_claim_is_still_reclaimable(tmp_path, monkeypatch):
    """The conservative read must not wedge the slot forever."""
    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    (tmp_path / "stale.pid").write_text("999999999", encoding="utf-8")

    assert mcp_daemon.claim_singleton("stale.pid") is True


# ---------------------------------------------------------------------------
# --reserve-slot: the OmniRoute slot must be claimed BEFORE the server starts.
# ---------------------------------------------------------------------------


def _reserve(pid_path):
    import subprocess
    import sys as _sys

    return subprocess.run(
        [_sys.executable, "-m", "packages.mcp_daemon", "--reserve-slot", str(pid_path)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[2]),
    )


def test_only_one_launcher_can_reserve_the_slot(tmp_path):
    """Two start scripts with no pid file both launched, and both recorded."""
    pid_path = tmp_path / "omniroute.pid"

    first = _reserve(pid_path)
    second = _reserve(pid_path)

    assert first.stdout.strip().splitlines()[-1] == "RESERVED"
    assert second.stdout.strip().splitlines()[-1] == "OCCUPIED"


def test_a_reservation_is_marked_and_unique(tmp_path):
    """A reservation is in-progress, not stale: it blocks, it is not reclaimed.

    It used to be an EMPTY file, which made every reservation byte-identical --
    and (st_dev, st_ino) cannot rescue that, because inode numbers are recycled:
    on ext4 a reservation reclaimed and recreated at the same path gets the same
    inode, so a loser found identity AND contents equal and deleted the winner's.
    Only Linux ever showed it.
    """
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)

    first = tmp_path / "a.pid"
    second = tmp_path / "b.pid"
    _reserve(first)
    _reserve(second)

    a = first.read_text(encoding="utf-8")
    b = second.read_text(encoding="utf-8")
    assert a.startswith(mcp_daemon._RESERVATION_MARKER)
    assert a != b, "two reservations are byte-identical"
    assert mcp_daemon._is_reservation(a)
    # Still recognised as in-progress rather than a pid, which is what makes it
    # block instead of being reclaimed as a stale holder.
    assert mcp_daemon._is_reservation("")


def test_the_verdict_is_on_stdout_not_only_in_the_exit_code(tmp_path):
    """PowerShell cannot catch a native command's failure; it reads the token."""
    pid_path = tmp_path / "omniroute.pid"

    _reserve(pid_path)
    occupied = _reserve(pid_path)

    assert "OCCUPIED" in occupied.stdout


# ---------------------------------------------------------------------------
# Slot-release ordering, pinned structurally because the shell scripts are not
# unit-testable here. Four review rounds hit this ordering in four different
# sites; a property test over every site is what finally covers the class.
# ---------------------------------------------------------------------------


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def _removal_order(script: Path) -> list[str]:
    """The pid-file and sidecar removals, in source order, as 'identity'/'pid'."""
    order = []
    for line in script.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("Remove-Item"):
            continue
        if ".identity" in stripped:
            order.append("identity")
        elif "$pidPath" in stripped or "$omniPid" in stripped:
            order.append("pid")
    return order


def test_every_slot_release_removes_the_identity_sidecar_first():
    """Freeing the slot first lets a replacement claim it and write its own
    identity inside the window, which the next line then deletes -- leaving a
    live daemon with an unverifiable record that start and stop both refuse to
    touch. mcp_daemon.py documents this on its own release path."""
    for name in ("start_mcp_daemons.ps1", "stop_mcp_daemons.ps1"):
        order = _removal_order(SCRIPTS / name)
        assert order, f"{name}: no removals found -- has the file moved?"
        assert len(order) % 2 == 0, f"{name}: an unpaired removal: {order}"
        pairs = list(zip(order[::2], order[1::2]))
        assert all(
            pair == ("identity", "pid") for pair in pairs
        ), f"{name}: removal out of order: {pairs}"


def test_a_stale_foreign_record_is_cleared_before_the_slot_is_reserved():
    """--reserve-slot is O_CREAT|O_EXCL, so a leftover FOREIGN record makes it
    return OCCUPIED forever and OmniRoute never restarts."""
    text = (SCRIPTS / "start_mcp_daemons.ps1").read_text(encoding="utf-8")

    clear_at = text.find("OmniRoute record is stale")
    # The INVOCATION, not the first mention: the explanatory comment above the
    # clearing block names --reserve-slot too, and matching that made this test
    # compare a comment against the code it explains.
    reserve_at = text.find("packages.mcp_daemon --reserve-slot")

    assert clear_at != -1, "the FOREIGN record is never cleared"
    assert reserve_at != -1, "the reservation call has moved"
    assert clear_at < reserve_at, "the stale record is cleared after reserving"


def test_the_conservative_unknown_branch_is_left_alone():
    """UNKNOWN may be a live holder we cannot verify; it must still block."""
    text = (SCRIPTS / "start_mcp_daemons.ps1").read_text(encoding="utf-8")

    assert "$omniVerdict -eq 'UNKNOWN'" in text
    assert "not starting a duplicate" in text


# ---------------------------------------------------------------------------
# The stop script's closing summary must describe what actually happened.
# ---------------------------------------------------------------------------


def _run_stop_script(agent_dir: Path):
    import shutil
    import subprocess

    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:  # pragma: no cover - non-Windows CI
        pytest.skip("no PowerShell available")
    env = dict(os.environ, FLOSS_AGENT_DIR=str(agent_dir))
    return subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPTS / "stop_mcp_daemons.ps1"),
        ],
        capture_output=True,
        text=True,
        env=env,
    )


def test_an_incomplete_shutdown_is_reported_and_exits_nonzero(tmp_path):
    """Every branch that keeps a pid file does so deliberately, but the closing
    line claimed a clean shutdown regardless -- so the careful refusals read as
    success and an operator frees a port that is still in use."""
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "consensus.pid").write_text("not-a-pid", encoding="utf-8")

    result = _run_stop_script(agent_dir)

    assert result.returncode == 1, result.stdout[-500:]
    assert "SHUTDOWN INCOMPLETE" in result.stdout
    assert "All daemons stopped" not in result.stdout
    assert (agent_dir / "consensus.pid").exists(), "the record must be kept"


def test_a_clean_shutdown_still_reports_success(tmp_path):
    """The guard must narrow to genuine leftovers, not fail every run."""
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()

    result = _run_stop_script(agent_dir)

    assert result.returncode == 0, result.stdout[-500:]
    assert "All daemons stopped" in result.stdout
    assert "SHUTDOWN INCOMPLETE" not in result.stdout


@pytest.mark.parametrize(
    "script,collector,banner,success",
    [
        (
            "start_mcp_daemons.ps1",
            "$skipped",
            "STARTUP INCOMPLETE",
            'Write-Host "[FLOSS MCP] Daemons started (consensus',
        ),
        (
            "stop_mcp_daemons.ps1",
            "$unresolved",
            "SHUTDOWN INCOMPLETE",
            'Write-Host "[FLOSS MCP] All daemons stopped',
        ),
    ],
)
def test_no_script_claims_success_it_did_not_achieve(
    script, collector, banner, success
):
    """Both scripts deliberately decline to act in several branches, and both
    then reported a clean run regardless. Fixed in stop first; the start script
    was the unswept sibling. Asserted as a property over both so the next
    script with a closing summary is covered before a reviewer finds it.

    Structural rather than behavioural for the start script specifically:
    running it launches real daemons, which a test must not do.
    """
    text = (SCRIPTS / script).read_text(encoding="utf-8")

    assert f"{collector} = @()" in text, "collector must be an explicit array"
    assert f"{collector} +=" in text, "nothing ever records a declined action"
    assert f"{collector}.Count -gt 0" in text, "the summary is unguarded"

    guard_at = text.find(f"{collector}.Count -gt 0")
    success_at = text.find(success)
    # The EMITTING STATEMENT, not the first mention: both files explain their
    # own summaries in comments above the code, and matching the prose made an
    # earlier version of this test compare a comment against the guard.
    assert success_at != -1, "the success line has moved"
    assert guard_at < success_at, "the success line is claimed before the guard"
    assert "exit 1" in text[guard_at:success_at], "an incomplete run exits 0"


def test_a_blank_reservation_blocks_while_fresh(tmp_path, monkeypatch):
    """--reserve-slot creates the file empty and leaves it empty until
    --record-identity runs, so a fresh blank claim is a live launcher mid-flight
    and must still block. Reclaiming it early starts a duplicate on a bound
    port."""
    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "reserved.pid"
    pid_path.write_text("", encoding="utf-8")

    assert mcp_daemon.claim_singleton("reserved.pid") is False
    assert pid_path.exists(), "a fresh reservation was reclaimed"


def test_a_blank_reservation_is_reclaimed_once_stale(tmp_path, monkeypatch):
    """A launcher killed between --reserve-slot and --record-identity left an
    empty file that blocked the slot forever -- the comment claimed the stale
    path handled it on a later pass, and the code returned False before ever
    reaching that path."""
    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "abandoned.pid"
    pid_path.write_text("", encoding="utf-8")
    old = time.time() - (mcp_daemon._RESERVATION_STALE_SECONDS + 60)
    os.utime(pid_path, (old, old))

    assert mcp_daemon.claim_singleton("abandoned.pid") is True
    assert pid_path.read_text(encoding="utf-8").strip() == str(os.getpid())


def test_reserve_slot_reclaims_a_stale_blank_reservation(tmp_path):
    """A launcher killed between --reserve-slot and --record-identity leaves an
    empty file forever. The blank-claim recovery added to claim_singleton could
    not help: the OmniRoute path never calls it, and never reaches this function
    again either, because the file exists and O_EXCL refuses."""
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "omniroute.pid"
    pid_path.write_text("", encoding="utf-8")
    old = time.time() - (mcp_daemon._RESERVATION_STALE_SECONDS + 60)
    os.utime(pid_path, (old, old))

    result = _reserve(pid_path)

    assert result.stdout.strip().splitlines()[-1] == "RESERVED"


def test_reserve_slot_still_refuses_a_fresh_blank_reservation(tmp_path):
    """A live launcher mid-flight must still block, or two servers start."""
    pid_path = tmp_path / "omniroute.pid"
    pid_path.write_text("", encoding="utf-8")

    assert _reserve(pid_path).stdout.strip().splitlines()[-1] == "OCCUPIED"


def test_reserve_slot_never_reclaims_a_record_with_a_pid_in_it(tmp_path):
    """A populated record belongs to the identity checks, which know how to
    probe it. Age alone must not take it."""
    pid_path = tmp_path / "omniroute.pid"
    pid_path.write_text("4242", encoding="utf-8")
    old = time.time() - 86400
    os.utime(pid_path, (old, old))

    assert _reserve(pid_path).stdout.strip().splitlines()[-1] == "OCCUPIED"
    assert pid_path.read_text(encoding="utf-8") == "4242"


def test_two_launchers_cannot_both_reclaim_one_stale_reservation(tmp_path):
    """Both can pass the content and age checks; after the first unlinks and
    recreates the claim, the second deleted THAT and both returned RESERVED --
    two servers on one port, which is what the reservation exists to prevent."""
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "omniroute.pid"
    pid_path.write_bytes(b"")
    observed = mcp_daemon._inspect_claim(pid_path)

    first = mcp_daemon._reclaim_claim_if_unchanged(pid_path, observed)
    pid_path.write_bytes(b"31337")  # the winner's fresh claim

    second = mcp_daemon._reclaim_claim_if_unchanged(pid_path, observed)

    assert first is True and second is False
    assert pid_path.read_bytes() == b"31337", "the winner's claim was deleted"


def test_the_daemon_reclaim_delegates_to_the_shared_implementation():
    """A third copy of rename-then-verify is how the three sites drift apart."""
    source = (Path(__file__).resolve().parents[1] / "mcp_daemon.py").read_text(
        encoding="utf-8"
    )

    assert "from packages.activity_log.filelock import reclaim_if_unchanged" in source
    body = source.split("def _reclaim_claim_if_unchanged(", 1)[1].split("\ndef ", 1)[0]
    assert "os.rename" not in body, "reimplemented the rename here"


def test_losing_a_reclaim_race_leaves_the_winners_sidecar_intact(tmp_path):
    """Removing the sidecar up front was correct when the reclaim was an
    unconditional unlink. With an instance-checked reclaim that can REFUSE, it
    destroys the winner's freshly written identity whenever we lose --
    --check-identity then reports UNKNOWN and the stop script refuses to manage
    a live daemon."""
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "consensus.pid"
    sidecar = mcp_daemon._identity_path(pid_path)
    pid_path.write_bytes(b"")
    stale_mtime = time.time() - (mcp_daemon._RESERVATION_STALE_SECONDS + 60)
    os.utime(pid_path, (stale_mtime, stale_mtime))
    sidecar.write_text("the-winners-identity", encoding="utf-8")

    # Drive the CALLER, not the helper: the helper was already instance-checked
    # a commit ago and what changed here is the ORDER the caller removes the
    # sidecar in. A test against the helper alone passes either way.
    monkey = pytest.MonkeyPatch()
    monkey.setattr(mcp_daemon, "_reclaim_claim_if_unchanged", lambda p, o: False)
    monkey.setattr(sys, "argv", ["mcp_daemon", "--reserve-slot", str(pid_path)])
    try:
        assert mcp_daemon._reserve_slot_cli() == 1
    finally:
        monkey.undo()

    assert sidecar.read_text(encoding="utf-8") == "the-winners-identity"
    assert pid_path.exists(), "the record we lost the race for was removed"


def test_no_reclaim_site_removes_a_record_by_pathname():
    """Every reclaim -- claim, sidecar, both branches -- goes through the
    instance check.

    The ordering assertion this replaced was written for the previous shape
    (sidecar only after winning) and became wrong when the sidecar moved back to
    the front, content-checked. Order is not the invariant; removing only what
    was inspected is.
    """
    source = (Path(__file__).resolve().parents[1] / "mcp_daemon.py").read_text(
        encoding="utf-8"
    )
    body = source.split("def claim_singleton(", 1)[1].split("\ndef ", 1)[0]
    reserve = source.split("def _reserve_slot_cli(", 1)[1].split("\ndef ", 1)[0]
    cli = source.split("def _reclaim_claim_cli(", 1)[1].split("\ndef ", 1)[0]

    # Only the RECLAIM and RELEASE paths are in scope. The two remaining plain
    # unlinks tidy up a claim this process created microseconds earlier and has
    # not yet published, which it holds exclusively; they remove nothing another
    # holder could own.
    for name, section in (
        ("_reserve_slot_cli", reserve),
        ("_reclaim_claim_cli", cli),
    ):
        assert (
            "unlink(missing_ok=True)" not in section
        ), f"{name} still removes a record by pathname"
        assert "_reclaim_claim_if_unchanged(" in section, f"{name} does not check"

    reclaim_branches = body.split("_blank_claim_is_stale(pid_path)")[1:]
    for branch in reclaim_branches:
        head = branch.split("continue", 1)[0]
        assert (
            "unlink(missing_ok=True)" not in head
        ), "a reclaim branch removes a record by pathname"

    # The sidecar goes through _sidecar_cleared (which reclaims it by instance
    # and distinguishes absent from unreadable); the claim goes through the
    # helper directly. Both reclaim branches, plus the release callback's pair.
    assert (
        body.count("_sidecar_cleared(pid_path, observed_sidecar)") == 2
    ), "a reclaim branch clears the sidecar without binding it to the snapshot"
    assert body.count("_reclaim_claim_if_unchanged(") == 4


def test_the_reclaim_cli_reports_its_verdict_on_stdout(tmp_path):
    """PowerShell cannot catch a native command's failure, so the verdict is a
    token, exactly as --check-identity and --reserve-slot do it."""
    import subprocess
    import sys as _sys

    pid_path = tmp_path / "omniroute.pid"
    pid_path.write_bytes(b"stale-record")

    def run():
        return subprocess.run(
            [
                _sys.executable,
                "-m",
                "packages.mcp_daemon",
                "--reclaim-claim",
                str(pid_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).resolve().parents[2]),
        )

    first = run()
    assert first.stdout.strip().splitlines()[-1] == "RECLAIMED"
    assert not pid_path.exists()

    # Already gone is success, not an error: the slot is free either way.
    assert run().stdout.strip().splitlines()[-1] == "RECLAIMED"


def test_an_unreadable_sidecar_stops_the_claim_from_being_freed(tmp_path):
    """Absent and unreadable are different answers. Absent is ordinary -- most
    stale claims never had a sidecar. Unreadable means we cannot tell whose
    identity it is, and freeing the slot under a foreign one is the
    non-conservative failure: the next claimant compares its own pid against
    someone else's token, reads FOREIGN, and reclaims a record that may be live.
    """
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "omniroute.pid"
    pid_path.write_bytes(b"")
    stale = time.time() - (mcp_daemon._RESERVATION_STALE_SECONDS + 60)
    os.utime(pid_path, (stale, stale))
    sidecar = mcp_daemon._identity_path(pid_path)
    sidecar.write_text("someone-elses-identity", encoding="utf-8")

    monkey = pytest.MonkeyPatch()
    real_read = Path.read_bytes

    def deny_the_sidecar(self):
        if self == sidecar:
            raise PermissionError(13, "denied", str(self))
        return real_read(self)

    monkey.setattr(Path, "read_bytes", deny_the_sidecar)
    monkey.setattr(sys, "argv", ["mcp_daemon", "--reserve-slot", str(pid_path)])
    try:
        assert mcp_daemon._reserve_slot_cli() == 1
    finally:
        monkey.undo()

    assert pid_path.exists(), "the slot was freed under an unreadable sidecar"
    assert sidecar.read_text(encoding="utf-8") == "someone-elses-identity"


def test_an_absent_sidecar_does_not_block_reclamation(tmp_path):
    """The guard must narrow to unreadable. Most stale claims have no sidecar at
    all, and refusing those would strand every one of them."""
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "omniroute.pid"
    pid_path.write_bytes(b"")
    stale = time.time() - (mcp_daemon._RESERVATION_STALE_SECONDS + 60)
    os.utime(pid_path, (stale, stale))
    assert not mcp_daemon._identity_path(pid_path).exists()

    assert (
        mcp_daemon._sidecar_cleared(pid_path, mcp_daemon._inspect_sidecar(pid_path))
        is True
    )

    monkey = pytest.MonkeyPatch()
    monkey.setattr(sys, "argv", ["mcp_daemon", "--reserve-slot", str(pid_path)])
    try:
        assert mcp_daemon._reserve_slot_cli() == 0
    finally:
        monkey.undo()


def test_a_foreign_sidecar_stops_the_claim_from_being_freed(tmp_path):
    """The sidecar reclaim can also REFUSE -- a winner's fresh identity. Freeing
    the pid record then leaves their token beside a slot anyone may take."""
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "consensus.pid"
    sidecar = mcp_daemon._identity_path(pid_path)
    sidecar.write_text("the-winners-identity", encoding="utf-8")

    monkey = pytest.MonkeyPatch()
    monkey.setattr(mcp_daemon, "_reclaim_claim_if_unchanged", lambda p, o: False)
    try:
        assert (
            mcp_daemon._sidecar_cleared(pid_path, mcp_daemon._inspect_sidecar(pid_path))
            is False
        )
    finally:
        monkey.undo()

    assert sidecar.read_text(encoding="utf-8") == "the-winners-identity"


def test_a_dangling_sidecar_symlink_is_not_read_as_absent(tmp_path):
    """A read failing with FileNotFoundError does not prove the path is empty:
    a dangling symlink is a directory entry whose target is missing and raises
    exactly that. Reporting the slot clear leaves an entry a later write will
    follow."""
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "consensus.pid"
    sidecar = mcp_daemon._identity_path(pid_path)
    try:
        sidecar.symlink_to(tmp_path / "target-that-does-not-exist")
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is not permitted in this environment")

    assert sidecar.exists() is False, "fixture is not actually dangling"
    with pytest.raises(FileNotFoundError):
        sidecar.read_bytes()

    assert (
        mcp_daemon._sidecar_cleared(pid_path, mcp_daemon._inspect_sidecar(pid_path))
        is False
    )


def test_a_genuinely_absent_sidecar_is_still_read_as_absent(tmp_path):
    """lstat must decide existence, not become a reason to refuse everything."""
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "consensus.pid"

    assert not mcp_daemon._identity_path(pid_path).exists()
    assert (
        mcp_daemon._sidecar_cleared(pid_path, mcp_daemon._inspect_sidecar(pid_path))
        is True
    )


def test_reclamation_fails_closed_without_the_shared_helper(tmp_path, monkeypatch):
    """The ImportError fallback unlinked by pathname -- the exact removal every
    caller was changed to stop doing, and applied to the sidecar it deletes a
    replacement's token. Refusing leaves a stale record for an operator; a wrong
    deletion cannot be undone."""
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    record = tmp_path / "some.pid"
    record.write_bytes(b"a-live-record")

    real_import = builtins.__import__

    def block_filelock(name, *args, **kwargs):
        if name == "packages.activity_log.filelock":
            raise ImportError("filelock unavailable in this install")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", block_filelock)

    assert mcp_daemon._reclaim_claim_if_unchanged(record, b"a-live-record") is False
    assert record.read_bytes() == b"a-live-record", "removed by pathname anyway"


def test_two_blank_reservations_are_told_apart(tmp_path):
    """Every blank reservation is b"", so a content check could not distinguish
    an abandoned empty claim from the fresh empty claim a faster launcher had
    just created in its place -- and both reclaimers removed "the old one",
    both got RESERVED, and two servers started on one port."""
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "omniroute.pid"
    _reserve(pid_path)
    observed = mcp_daemon._inspect_claim(pid_path)

    # The winner reclaims and reserves again at the same path. On ext4 that
    # recreated file can carry the SAME inode, which is why the reservation
    # needs a token of its own rather than relying on filesystem identity.
    assert mcp_daemon._reclaim_claim_if_unchanged(pid_path, observed) is True
    _reserve(pid_path)

    # The loser arrives with what it inspected.
    assert mcp_daemon._reclaim_claim_if_unchanged(pid_path, observed) is False
    assert pid_path.exists(), "the winner's fresh reservation was deleted"
    assert pid_path.read_bytes() != observed.data, "the two were indistinguishable"


def test_an_inspection_carries_filesystem_identity(tmp_path):
    """Identity survives a rename and differs for a new file at the same path;
    that is the whole basis for telling two byte-identical claims apart."""
    from packages.activity_log import filelock

    a = tmp_path / "claim"
    a.write_bytes(b"")
    first = filelock.inspect_for_reclaim(a)

    moved = tmp_path / "claim.moved"
    os.rename(a, moved)
    assert filelock.inspect_for_reclaim(moved)[:2] == first[:2], "rename changed it"

    a.write_bytes(b"")
    assert filelock.inspect_for_reclaim(a)[:2] != first[:2], "a new file matched"


def test_a_file_rewritten_in_place_is_still_caught(tmp_path):
    """Identity alone is not enough either: a file rewritten in place keeps it,
    so contents are still compared."""
    from packages.activity_log import filelock

    path = tmp_path / "claim"
    path.write_bytes(b"first")
    observed = filelock.inspect_for_reclaim(path)
    path.write_bytes(b"second")

    assert filelock.reclaim_if_unchanged(path, observed) is False
    assert path.read_bytes() == b"second"


def test_an_inode_collision_alone_does_not_authorise_a_reclaim(tmp_path):
    """The Linux failure, forced rather than waited for.

    ext4 recycles inode numbers, so a reservation reclaimed and recreated at
    the same path can carry the SAME (st_dev, st_ino) as the one that was
    inspected. Identity therefore cannot be the only check -- and when both
    reservations were empty, contents could not separate them either. This
    pairs a real current identity with the OLD contents and requires a refusal,
    which is what the token makes possible.
    """
    import importlib

    from packages import mcp_daemon
    from packages.activity_log import filelock

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "omniroute.pid"
    _reserve(pid_path)
    old_data = pid_path.read_bytes()

    pid_path.unlink()
    _reserve(pid_path)
    live = filelock.inspect_for_reclaim(pid_path)

    # Exactly what inode reuse produces: same identity, earlier contents.
    collided = filelock.Inspection(live.dev, live.ino, old_data)

    assert mcp_daemon._reclaim_claim_if_unchanged(pid_path, collided) is False
    assert pid_path.exists(), "a colliding inode was enough to delete a live claim"


def test_the_powershell_start_script_knows_the_reservation_marker():
    """Reservations were empty files and the start script tested emptiness.
    Marking them without teaching it the marker would send every new
    reservation down the UNVERIFIABLE path and never start OmniRoute again."""
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    script = (
        Path(__file__).resolve().parents[2] / "scripts" / "start_mcp_daemons.ps1"
    ).read_text(encoding="utf-8")

    assert (
        f"'{mcp_daemon._RESERVATION_MARKER}*'" in script
    ), "the start script still recognises only empty reservations"


def test_a_replacements_sidecar_written_after_our_snapshot_is_left_alone(tmp_path):
    """Re-inspecting asked what sidecar exists NOW. A launcher that took the
    freed slot after our snapshot wrote its own token, that removal deleted it,
    and the claim reclaim then correctly refused -- leaving a live daemon with
    no identity, --check-identity returning UNKNOWN, and the stop script
    refusing to manage it."""
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "consensus.pid"
    sidecar = mcp_daemon._identity_path(pid_path)

    # Nothing there when we look.
    seen = mcp_daemon._inspect_sidecar(pid_path)
    assert seen is mcp_daemon._SIDECAR_ABSENT

    # A replacement claims the slot and records its identity.
    sidecar.write_text("the-replacements-identity", encoding="utf-8")

    assert mcp_daemon._sidecar_cleared(pid_path, seen) is False
    assert sidecar.read_text(encoding="utf-8") == "the-replacements-identity"


def test_a_sidecar_replaced_since_our_snapshot_is_left_alone(tmp_path):
    """Same window, the other starting state: there WAS one, and it is not the
    one there now."""
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "consensus.pid"
    sidecar = mcp_daemon._identity_path(pid_path)
    sidecar.write_text("the-stale-identity", encoding="utf-8")

    seen = mcp_daemon._inspect_sidecar(pid_path)
    sidecar.write_text("the-replacements-identity", encoding="utf-8")

    assert mcp_daemon._sidecar_cleared(pid_path, seen) is False
    assert sidecar.read_text(encoding="utf-8") == "the-replacements-identity"


def test_the_sidecar_we_actually_inspected_is_still_removed(tmp_path):
    """Binding to the snapshot must not become refusing to clean up."""
    import importlib

    from packages import mcp_daemon

    importlib.reload(mcp_daemon)
    pid_path = tmp_path / "consensus.pid"
    sidecar = mcp_daemon._identity_path(pid_path)
    sidecar.write_text("the-stale-identity", encoding="utf-8")

    seen = mcp_daemon._inspect_sidecar(pid_path)

    assert mcp_daemon._sidecar_cleared(pid_path, seen) is True
    assert not sidecar.exists()
