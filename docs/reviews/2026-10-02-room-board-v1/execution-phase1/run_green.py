"""Run the required green set in the implementation worktree with a pinned, harmless environment.

usage: run_green.py <label> [extra pytest args...]
Writes <label>.txt and <label>.xml beside this script.
"""
import os, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = Path("C:/~shit/FLOSS/.worktrees/room-board-v1")
label = sys.argv[1]
GREEN = [
    sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
    "packages/", "tests/", "scripts/tests/",
    "--deselect",
    "scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded",
]
scratch = Path(tempfile.mkdtemp(prefix=f"green-{label}-"))
env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "COORDINATION_ROOM_BOARD", "GIT_DIR", "GIT_WORK_TREE")}
env.update(
    PYTHONDONTWRITEBYTECODE="1",
    FLOSS_AGENT_DIR=str(scratch / "agent"),
    FLOSS_AUDIT_DIR=str(scratch / "audit"),
    COORDINATION_ROOM_ROOT=str(scratch / "root"),
    COORDINATION_ROOM_LOG=str(scratch / "rooms" / "events.jsonl"),
)
head = subprocess.check_output(["git", "-C", str(WORKTREE), "rev-parse", "HEAD"], text=True).strip()
done = subprocess.run([*GREEN, f"--junitxml={HERE / (label + '.xml')}", *sys.argv[2:]], cwd=WORKTREE, env=env,
                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=1800)
text = done.stdout.decode("utf-8", "replace")
(HERE / f"{label}.txt").write_text(f"HEAD {head}\n" + text, encoding="utf-8")
print(label, "HEAD", head[:8], "exit", done.returncode, "|", text.strip().splitlines()[-1])
for line in text.splitlines():
    if line.startswith(("FAILED", "ERROR ")):
        print("  ", line[:200])
