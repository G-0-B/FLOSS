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


def test_a_single_scan_cannot_exceed_the_cap(tmp_path, monkeypatch):
    """The depth guard bounds the START of a scan; the emits need bounding too.

    PR41 review (Codex, P1): with the queue under the cap, the guard passed and
    the scan then emitted every change it found, however many that was --
    recreating the flood the cap exists to prevent. This workspace has an
    `incoming.flood-quarantine-20260616-17` directory from one such event.
    """
    wi = load_watch_intake()
    monkeypatch.setattr(wi, "MAX_INCOMING_QUEUE_DEPTH", 5)

    ws = tmp_path / "workspace"
    docs = ws / "FLOSS" / "docs"
    docs.mkdir(parents=True)
    for i in range(20):
        (docs / f"f{i}.md").write_text(f"v{i}\n", encoding="utf-8")
    events = ws / ".agent-surface" / "events"
    wi.ensure_dirs(events)
    state = events / "watch-state.json"

    assert _scan(wi, ws, events, state) == 5
    assert len(_incoming(events)) == 5


def test_capacity_accounts_for_events_already_queued(tmp_path, monkeypatch):
    wi = load_watch_intake()
    monkeypatch.setattr(wi, "MAX_INCOMING_QUEUE_DEPTH", 10)

    ws = tmp_path / "workspace"
    docs = ws / "FLOSS" / "docs"
    docs.mkdir(parents=True)
    for i in range(20):
        (docs / f"f{i}.md").write_text(f"v{i}\n", encoding="utf-8")
    events = ws / ".agent-surface" / "events"
    wi.ensure_dirs(events)
    for i in range(4):
        (events / "incoming" / f"pre-{i}.json").write_text("{}", encoding="utf-8")
    state = events / "watch-state.json"

    assert _scan(wi, ws, events, state) == 6, "cap 10 minus 4 queued leaves 6"
    assert len(_incoming(events)) == 10


def test_withheld_events_are_re_emitted_after_a_drain(tmp_path, monkeypatch):
    """Withholding must not record the file as seen.

    `scan_once` saves `current` and the next scan diffs against it, so if a
    withheld event's fingerprint were persisted the event would never be
    emitted at all -- backpressure quietly becoming data loss. Drained rescans
    must therefore deliver exactly the same total an uncapped scan would.

    The expected total is measured rather than hardcoded: this fixture emits
    more events than it has files (33 for 12, with one pair repeating 21 times
    -- pre-existing amplification, identical at HEAD, tracked separately). The
    property under test is conservation, not the magnitude.
    """
    def _build(root):
        docs = root / "FLOSS" / "docs"
        docs.mkdir(parents=True)
        for i in range(12):
            (docs / f"f{i}.md").write_text("v" + chr(10), encoding="utf-8")
        events = root / ".agent-surface" / "events"
        return events

    wi = load_watch_intake()

    # Uncapped baseline in its own workspace.
    ws_ref = tmp_path / "reference"
    ws_ref.mkdir()
    events_ref = _build(ws_ref)
    wi.ensure_dirs(events_ref)
    monkeypatch.setattr(wi, "MAX_INCOMING_QUEUE_DEPTH", 10**6)
    expected_total = _scan(wi, ws_ref, events_ref, events_ref / "watch-state.json")
    assert expected_total > 0

    # Same workspace shape, hard cap, draining between scans.
    ws = tmp_path / "capped"
    ws.mkdir()
    events = _build(ws)
    wi.ensure_dirs(events)
    cap = 5
    monkeypatch.setattr(wi, "MAX_INCOMING_QUEUE_DEPTH", cap)
    state = events / "watch-state.json"

    counts = []
    for _ in range(40):
        n = _scan(wi, ws, events, state)
        counts.append(n)
        assert n <= cap, f"a single scan emitted {n}, above the cap {cap}"
        for queued in _incoming(events):
            queued.unlink()
        if n == 0:
            break

    assert counts[-1] == 0, f"never drained to zero: {counts}"
    assert sum(counts) == expected_total, (
        f"capped scans delivered {sum(counts)} events but an uncapped scan "
        f"delivers {expected_total}; withheld events were lost. Sequence: {counts}"
    )
