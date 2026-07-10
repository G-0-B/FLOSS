"""Tests for heartbeat.py daily_state mid-tick persistence (2026-07-08 fix).

Covers the approved Agent C patch from 2026-07-07-doc-drift-sweep.md Part 1.2:
save_daily_state() is now called immediately after the ticks_today increment
and after each rounds_today accumulation, so a mid-tick kill (SIGKILL/OOM/
crash/unhandled exception) doesn't lose the tick count or round-cap accounting.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path

FLOSS_ROOT = Path(__file__).resolve().parents[2]


def load_heartbeat_module(tmp_path: Path):
    spec = importlib.util.spec_from_file_location(
        "heartbeat_persist_under_test", FLOSS_ROOT / "scripts" / "heartbeat.py"
    )
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["heartbeat_persist_under_test"] = module
    spec.loader.exec_module(module)
    module.HEARTBEAT_DIR = tmp_path
    module.stop_requested = lambda: False
    return module


def _state_file(tmp_path: Path) -> Path:
    return tmp_path / "daily_state.json"


def _read_state(tmp_path: Path) -> dict:
    return json.loads(_state_file(tmp_path).read_text(encoding="utf-8"))


def test_mid_tick_crash_persists_tick_count(tmp_path):
    """A crash during run_work_item must NOT lose the ticks_today increment.
    Before the 2026-07-08 patch, save_daily_state() only ran at end-of-tick
    (L757), so a crash mid-tick lost the count — and a frozen daily_state
    date was an observed symptom (2026-06-14)."""
    hb = load_heartbeat_module(tmp_path)

    # Pre-seed yesterday so we also verify date rollover.
    _state_file(tmp_path).write_text(json.dumps(
        {"date": "2020-01-01", "rounds_today": 99, "ticks_today": 99}
    ), encoding="utf-8")

    # Force a crash mid-tick.
    def crashing_run(item):
        raise RuntimeError("simulated mid-tick crash")
    hb.run_work_item = crashing_run

    @dataclass
    class FakeItem:
        name: str = "crash_probe"
        script: str = "x.py"
        args: list = None
        timeout_seconds: int = 10
        flourishing_rationale: str = "test"

    hb.get_work_rotation = lambda ds: [FakeItem()]

    try:
        hb.run_one_tick()
    except RuntimeError:
        pass  # the crash propagates; that's the point

    state = _read_state(tmp_path)
    assert state["date"] == hb.utc_date(), f"date didn't roll over: {state['date']}"
    assert state["ticks_today"] == 1, f"tick count lost: {state['ticks_today']}"
    assert state["rounds_today"] == 0, f"rounds not reset on rollover: {state['rounds_today']}"


def test_date_rollover_resets_both_counters(tmp_path):
    """load_daily_state() must reset BOTH rounds_today AND ticks_today to 0
    when the stored date != today. (Verified correct by Agent C — this test
    guards against regression.)"""
    hb = load_heartbeat_module(tmp_path)
    _state_file(tmp_path).write_text(json.dumps(
        {"date": "2020-01-01", "rounds_today": 37, "ticks_today": 42}
    ), encoding="utf-8")

    state = hb.load_daily_state()
    assert state["date"] == hb.utc_date()
    assert state["rounds_today"] == 0
    assert state["ticks_today"] == 0


def test_rounds_accumulation_persists_per_item(tmp_path):
    """After each work item, save_daily_state() fires — so partial round
    accumulation survives even if a later item crashes."""
    hb = load_heartbeat_module(tmp_path)

    call_count = {"n": 0}

    def run_two_then_crash(item):
        call_count["n"] += 1
        if call_count["n"] <= 2:
            return {"returncode": 0, "duration_seconds": 0.1, "stdout": "", "stderr": ""}
        raise RuntimeError("crash on third item")

    hb.run_work_item = run_two_then_crash
    hb.estimate_rounds_from_result = lambda name, result: 5  # 5 rounds per item

    @dataclass
    class FakeItem:
        name: str = "probe"
        script: str = "x.py"
        args: list = None
        timeout_seconds: int = 10
        flourishing_rationale: str = "test"

    hb.get_work_rotation = lambda ds: [FakeItem(), FakeItem(), FakeItem()]

    try:
        hb.run_one_tick()
    except RuntimeError:
        pass

    state = _read_state(tmp_path)
    # 2 items completed × 5 rounds each = 10 rounds persisted before the crash
    assert state["rounds_today"] == 10, f"partial rounds lost: {state['rounds_today']}"
    assert state["ticks_today"] == 1, f"tick count lost: {state['ticks_today']}"
