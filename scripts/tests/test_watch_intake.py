"""Tests for watch_intake.py — overlap-spec dedup + backpressure guard.

Covers the 2026-06-16/17 1.23M-event storm root cause (overlapping watch specs
emitting a spurious 'modified' per file per scan) and the
MAX_INCOMING_QUEUE_DEPTH backpressure guard landed 2026-07-07.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

FLOSS_ROOT = Path(__file__).resolve().parents[2]


def load_watch_intake():
    spec = importlib.util.spec_from_file_location(
        "watch_intake_under_test", FLOSS_ROOT / "scripts" / "watch_intake.py"
    )
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["watch_intake_under_test"] = module
    spec.loader.exec_module(module)
    return module


def _scan(wi, ws, events, state, **kw):
    return wi.scan_once(
        workspace_root=ws,
        event_root=events,
        state_path=state,
        emit_on_first_scan=True,
        debounce_seconds=0.0,
        **kw,
    )


def _incoming(events):
    return sorted((events / "incoming").glob("*.json"))


def _events_for(events, rel_path):
    out = []
    for p in _incoming(events):
        e = json.loads(p.read_text(encoding="utf-8"))
        if e.get("rel_path") == rel_path:
            out.append(e)
    return out


def test_overlap_dedup_first_scan_one_event(tmp_path):
    """A file under FLOSS/docs is covered by both the 'canon' and broad
    'shared-surface' specs; it must emit exactly ONE created event, not two."""
    wi = load_watch_intake()
    ws = tmp_path / "workspace"
    docs = ws / "FLOSS" / "docs"
    docs.mkdir(parents=True)
    (docs / "overlap.md").write_text("v1\n", encoding="utf-8")
    events = ws / ".agent-surface" / "events"
    state = events / "watch-state.json"

    _scan(wi, ws, events, state)
    mine = _events_for(events, "FLOSS/docs/overlap.md")
    assert len(mine) == 1
    assert mine[0]["event_type"] == "created"


def test_overlap_dedup_repeated_scans_emit_zero(tmp_path):
    """The storm mechanism: repeated scans over an overlapped file must NOT
    emit a spurious 'modified' every scan. State must converge."""
    wi = load_watch_intake()
    ws = tmp_path / "workspace"
    docs = ws / "FLOSS" / "docs"
    docs.mkdir(parents=True)
    (docs / "overlap.md").write_text("v1\n", encoding="utf-8")
    events = ws / ".agent-surface" / "events"
    state = events / "watch-state.json"

    _scan(wi, ws, events, state)  # baseline
    assert _scan(wi, ws, events, state) == 0
    assert _scan(wi, ws, events, state) == 0


def test_real_modification_still_detected(tmp_path):
    """Dedup must not swallow genuine changes — a real edit emits one event."""
    wi = load_watch_intake()
    ws = tmp_path / "workspace"
    docs = ws / "FLOSS" / "docs"
    docs.mkdir(parents=True)
    target = docs / "overlap.md"
    target.write_text("v1\n", encoding="utf-8")
    events = ws / ".agent-surface" / "events"
    state = events / "watch-state.json"

    _scan(wi, ws, events, state)
    before = len(_incoming(events))
    time.sleep(0.01)
    target.write_text("v2 changed\n", encoding="utf-8")
    assert _scan(wi, ws, events, state) == 1
    new = [json.loads(p.read_text(encoding="utf-8"))
           for p in _incoming(events)[before:]]
    mods = [e for e in new if e.get("rel_path") == "FLOSS/docs/overlap.md"]
    assert len(mods) == 1
    assert mods[0]["event_type"] == "modified"


def test_backpressure_guard_suppresses_emission(tmp_path, monkeypatch):
    """Flooded incoming/ -> scan emits 0 and leaves the queue untouched."""
    wi = load_watch_intake()
    monkeypatch.setattr(wi, "MAX_INCOMING_QUEUE_DEPTH", 10)

    ws = tmp_path / "workspace"
    docs = ws / "FLOSS" / "docs"
    docs.mkdir(parents=True)
    target = docs / "overlap.md"
    target.write_text("v1\n", encoding="utf-8")
    events = ws / ".agent-surface" / "events"
    state = events / "watch-state.json"

    wi.ensure_dirs(events)
    for i in range(15):
        (events / "incoming" / f"flood-{i}.json").write_text("{}", encoding="utf-8")
    depth_before = len(_incoming(events))

    time.sleep(0.01)
    target.write_text("v2 under backpressure\n", encoding="utf-8")
    assert _scan(wi, ws, events, state) == 0
    assert len(_incoming(events)) == depth_before
