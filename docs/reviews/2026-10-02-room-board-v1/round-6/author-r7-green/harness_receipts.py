"""Scratch-only: run deploy_harness.ps1 as test_deploy_helpers.py does, and keep the JSON it prints."""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
import pytest

stage = Path(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(stage))
from packages.coordination_room.tests.room_server import free_port, pin_room_env, reload_server, serving

tests = stage / "packages" / "coordination_room" / "tests"
for name in ("powershell", "pwsh"):
    shell = shutil.which(name)
    if not shell:
        print(name, "not installed"); continue
    tmp = Path(tempfile.mkdtemp(prefix=f"harness-{name}-"))
    mp = pytest.MonkeyPatch()
    try:
        log = pin_room_env(mp, tmp)
        work = tmp / "work"; work.mkdir()
        port = free_port()
        with serving(reload_server().mcp.streamable_http_app(), port):
            done = subprocess.run(
                [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(tests / "deploy_harness.ps1"),
                 "-Work", str(work), "-Python", sys.executable, "-Port", str(free_port()),
                 "-RoomUrl", f"http://127.0.0.1:{port}/mcp", "-RoomLog", str(log), "-RoomRoot", str(tmp)],
                capture_output=True, text=True, timeout=300)
    finally:
        mp.undo()
    results = json.loads(done.stdout[done.stdout.rindex("\n{"):])
    (out / f"deploy-harness-{name}.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(name, "exit", done.returncode, "checks", len(results), "not true:", [k for k, v in results.items() if v is not True])
