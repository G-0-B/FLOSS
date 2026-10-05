"""Runs deploy_harness.ps1 against ../deploy.ps1 under each installed PowerShell.

The harness uses fake checkouts, a scratch port, a scratch log, a scratch git
repository and a scratch room served by this test. It touches no real daemon,
PID file or port 7334/7335.

Production change that would make this fail: a deployment helper carrying on
after a failed precondition, accepting the wrong bus or rejecting the right
one, matching a preview by prefix, or accepting a checkout that is not the
recorded commit.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows deployment helpers")
pytest.importorskip("mcp")
pytest.importorskip("uvicorn")

from packages.coordination_room.tests.room_server import (  # noqa: E402
    free_port,
    pin_room_env,
    reload_server,
    serving,
)

SHELLS = [exe for exe in (shutil.which("powershell"), shutil.which("pwsh")) if exe]


@pytest.mark.parametrize(
    "shell", SHELLS or [pytest.param("", marks=pytest.mark.skip(reason="no PowerShell"))]
)
def test_every_helper_check_holds(shell: str, tmp_path: Path, monkeypatch):
    log = pin_room_env(monkeypatch, tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    port = free_port()
    with serving(reload_server().mcp.streamable_http_app(), port):
        done = subprocess.run(
            [
                shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                "-File", str(_THIS_DIR / "deploy_harness.ps1"),
                "-Work", str(work),
                "-Python", sys.executable,
                "-Port", str(free_port()),
                "-RoomUrl", f"http://127.0.0.1:{port}/mcp",
                "-RoomLog", str(log),
                "-RoomRoot", str(tmp_path),
            ],
            capture_output=True, text=True, timeout=300,
        )
    assert done.returncode == 0, done.stdout[-3000:] + done.stderr[-3000:]
    start = done.stdout.rindex("\n{")
    results = json.loads(done.stdout[start:])
    assert len(results) >= 40, sorted(results)
    assert [name for name, ok in results.items() if ok is not True] == []
