"""Scratch-only: rebuild base / phase1 / proposal from the plan's sources and run the green set on each."""

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(r"C:\~shit\FLOSS")
BASE = "4aab13e30f3c2960da787b47c90926256b4b5b73"
A2A = "225287c2ed310158a3f699688447db2964e425b2"
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=False)


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(REPO), *args])


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ps1 = load("ps1_edits")
p2t = load("p2_test_edits")


def apply(path: Path, pairs) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        assert text.count(old) == 1, (path, old[:60])
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8", newline="\n")


def copy_from_scratch(stage: Path, rel: str) -> None:
    target = stage / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / rel, target)


baseline = OUT / "baseline"
with zipfile.ZipFile(io.BytesIO(git("archive", "--format=zip", BASE))) as archive:
    archive.extractall(baseline)

phase1 = OUT / "phase1"
shutil.copytree(baseline, phase1)
for rel in [
    "docs/specs/coordination-room.schema.json",
    "scripts/tests/test_daemon_scope.py",
    "docs/specs/coordination-room.spec.md",
    "packages/coordination_room/evidence.py",
    "packages/coordination_room/board.py",
    "packages/coordination_room/log.py",
    "packages/coordination_room/room.py",
    "packages/coordination_room/gateway.py",
    "packages/coordination_room/server.py",
    "packages/coordination_room/client.py",
    "packages/coordination_room/deploy.ps1",
    "packages/coordination_room/tests/room_server.py",
    "packages/coordination_room/tests/test_evidence.py",
    "packages/coordination_room/tests/test_board.py",
    "packages/coordination_room/tests/test_message_board.py",
    "packages/coordination_room/tests/test_gateway_board.py",
    "packages/coordination_room/tests/test_schema.py",
    "packages/coordination_room/tests/test_v01_compat.py",
    "packages/coordination_room/tests/test_server_tools.py",
    "packages/coordination_room/tests/test_server_http.py",
    "packages/coordination_room/tests/deploy_harness.ps1",
    "packages/coordination_room/tests/test_deploy_helpers.py",
]:
    copy_from_scratch(phase1, rel)
apply(phase1 / "scripts/start_mcp_daemons.ps1", ps1.START_PHASE1)
apply(phase1 / "scripts/stop_mcp_daemons.ps1", ps1.STOP_PHASE1)
reqs = phase1 / "requirements-ci.txt"
raw = reqs.read_bytes()
assert raw.count(b"\nmcp\n") == 1
reqs.write_bytes(raw.replace(b"\nmcp\n", b"\nmcp>=1.27,<2\n"))

proposal = OUT / "proposal"
shutil.copytree(phase1, proposal)
names = git("ls-tree", "-r", "--name-only", A2A, "--", "packages/a2a_mesh").decode().splitlines()
for name in names:
    target = proposal / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(git("show", f"{A2A}:{name}"))
base_reqs = git("show", f"{BASE}:requirements-ci.txt")
a2a_reqs = git("show", f"{A2A}:requirements-ci.txt")
assert a2a_reqs.startswith(base_reqs)
reqs = proposal / "requirements-ci.txt"
reqs.write_bytes(reqs.read_bytes() + a2a_reqs[len(base_reqs):])
for rel in [
    "packages/a2a_mesh/room_bridge.py",
    "packages/a2a_mesh/tests/test_room_bridge_parse.py",
    "packages/a2a_mesh/tests/test_room_bridge_pair.py",
    "packages/a2a_mesh/tests/test_room_bridge_invariants.py",
    "packages/a2a_mesh/tests/test_room_bridge_e2e.py",
]:
    copy_from_scratch(proposal, rel)
apply(proposal / "scripts/start_mcp_daemons.ps1", ps1.START_PHASE2)
apply(proposal / "scripts/stop_mcp_daemons.ps1", ps1.STOP_PHASE2)
apply(proposal / "scripts/tests/test_daemon_scope.py", p2t.PAIRS)

GREEN = [
    sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
    "packages/", "tests/", "scripts/tests/",
    "--deselect",
    "scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded",
]
results = {}
for stage in (baseline, phase1, proposal):
    scratch = Path(tempfile.mkdtemp(prefix=f"green-{stage.name}-"))
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "COORDINATION_ROOM_BOARD")}
    env.update(
        PYTHONDONTWRITEBYTECODE="1",
        FLOSS_AGENT_DIR=str(scratch / "agent"),
        FLOSS_AUDIT_DIR=str(scratch / "audit"),
        COORDINATION_ROOM_ROOT=str(scratch / "root"),
        COORDINATION_ROOM_LOG=str(scratch / "rooms" / "events.jsonl"),
    )
    junit = OUT / f"{stage.name}.xml"
    done = subprocess.run(
        [*GREEN, f"--junitxml={junit}"], cwd=stage, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=1800,
    )
    text = done.stdout.decode("utf-8", "replace")
    (OUT / f"{stage.name}.txt").write_text(text, encoding="utf-8")
    failed = [line for line in text.splitlines() if line.startswith("FAILED") or line.startswith("ERROR ")]
    results[stage.name] = {"exit": done.returncode, "summary": text.strip().splitlines()[-1], "failed": failed}
    print(stage.name, results[stage.name]["summary"], flush=True)
(OUT / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps(results, indent=2))
