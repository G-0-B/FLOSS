"""Pytest suite for FLOSS/scripts/orient_probe.py.

Formalizes the four smoke scenarios from the orient-skill v0.2.0 handoff
(ccp-orient-skill-v020-handoff, decision #9, approved by Anthony 2026-06-11):

    1. happy      — full synthetic canon tree -> exit 0, packet lists files
    2. lock       — *.lock present in either lock dir -> exit 2, LOCKS PRESENT
    3. cold-start — empty tree -> exit 0, explicit cold-start line
    4. json       — --json emits valid JSON with the declared contract

Stdlib + pytest only. No network. Probe is exercised via its CLI (subprocess)
because exit codes are part of its contract.

Run from repo root:  python -m pytest FLOSS/tests/test_orient_probe.py -v
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROBE = Path(__file__).resolve().parents[1] / "scripts" / "orient_probe.py"

# Keep in sync with CANONICAL_FILES in orient_probe.py.
CANONICAL_PATHS = [
    ".agent-surface/context/CONTEXT_L0.md",
    ".agent-surface/context/CONTEXT_L1.md",
    "INDEX.md",
    "FLOSS/CLAUDE.md",
    "FLOSS/FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md",
    "FLOSS/scripts/context_router.py",
    "FLOSS/docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md",
    "FLOSS/docs/superpowers/plans/2026-04-19-filewatch-metaharness.md",
    "FLOSS/scripts/watch_intake.py",
    "FLOSS/scripts/process_intake_events.py",
]

EVENTS_QUEUE_FILES = 3


def run_probe(root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PROBE), "--root", str(root), "--query", "test", *extra],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def make_canon_tree(root: Path) -> None:
    """Synthetic tree containing every declared canonical artifact."""
    for rel in CANONICAL_PATHS:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# synthetic {rel}\n", encoding="utf-8")
    events = root / ".agent-surface" / "events"
    events.mkdir(parents=True, exist_ok=True)
    for i in range(EVENTS_QUEUE_FILES):
        (events / f"evt-{i}.json").write_text("{}", encoding="utf-8")


def test_happy_path(tmp_path: Path) -> None:
    make_canon_tree(tmp_path)
    result = run_probe(tmp_path)
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "FLOSSI0ULLK orientation packet" in out
    assert "LOCKS PRESENT" not in out
    assert "MISSING" not in out  # every declared file exists in the tree
    assert f"events queue depth: `{EVENTS_QUEUE_FILES}`" in out


def test_lock_present_exits_2(tmp_path: Path) -> None:
    make_canon_tree(tmp_path)
    # Confirmed writer convention: .agent-surface/events/locks/{name}.lock
    events_locks = tmp_path / ".agent-surface" / "events" / "locks"
    events_locks.mkdir(parents=True, exist_ok=True)
    (events_locks / "watch-state.lock").touch()
    # Defensive secondary scan: .agent-surface/context/*.lock
    (tmp_path / ".agent-surface" / "context" / "consolidate.lock").touch()

    result = run_probe(tmp_path)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "LOCKS PRESENT" in result.stdout
    assert "watch-state.lock" in result.stdout
    assert "consolidate.lock" in result.stdout


def test_cold_start(tmp_path: Path) -> None:
    result = run_probe(tmp_path)  # empty directory
    assert result.returncode == 0, result.stderr
    assert "cold start" in result.stdout
    assert "events queue: `(absent)`" in result.stdout
    assert "router script not found" in result.stdout  # degrade, don't fail


def test_json_mode(tmp_path: Path) -> None:
    make_canon_tree(tmp_path)
    result = run_probe(tmp_path, "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)  # must be valid JSON
    assert set(payload) >= {"query", "utc", "events_queue_depth", "locks", "router", "files"}
    assert payload["events_queue_depth"] == EVENTS_QUEUE_FILES
    assert payload["locks"] == []
    assert len(payload["files"]) == len(CANONICAL_PATHS)
    for entry in payload["files"]:
        assert entry["present"] is True
        assert entry["sha256_prefix"]
    # the synthetic router stub is valid