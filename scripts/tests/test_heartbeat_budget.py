from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


FLOSS_ROOT = Path(__file__).resolve().parents[2]


def load_heartbeat_module():
    if str(FLOSS_ROOT) not in sys.path:
        sys.path.insert(0, str(FLOSS_ROOT))
    spec = importlib.util.spec_from_file_location(
        "heartbeat_budget_under_test", FLOSS_ROOT / "scripts" / "heartbeat.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["heartbeat_budget_under_test"] = module
    spec.loader.exec_module(module)
    return module


def write_slate(path: Path, slug: str = "review-synthesis-staging") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "generated_at": "2026-05-19T00:00:00+00:00",
                "poll_compatible": [
                    {
                        "slug": slug,
                        "proposal_type": "Other",
                        "summary": "Review staged synthesis drafts",
                        "body": "Review staged synthesis drafts.",
                        "evidence": [{"type": "spec", "ref": "docs/specs/x.md"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_routine_high_roi_poll_uses_balanced_profile(tmp_path, monkeypatch):
    heartbeat = load_heartbeat_module()
    slate = tmp_path / "next_slate.json"
    write_slate(slate)
    monkeypatch.setattr(heartbeat, "DYNAMIC_SLATE_PATH", slate, raising=False)
    monkeypatch.setattr(heartbeat, "POLL_STATE_FILE", tmp_path / "poll_state.json", raising=False)
    monkeypatch.setenv("FLOSS_HEARTBEAT_WIDE_INTERVAL_TICKS", "0")

    rotation = heartbeat.get_work_rotation({"rounds_today": 0, "ticks_today": 1})

    poll_items = [item for item in rotation if item.name.startswith("poll_high_roi_actions")]
    assert len(poll_items) == 1
    assert poll_items[0].args == ["--profile", "balanced"]


def test_unchanged_slate_skips_repeated_poll(tmp_path, monkeypatch):
    heartbeat = load_heartbeat_module()
    slate = tmp_path / "next_slate.json"
    write_slate(slate)
    monkeypatch.setattr(heartbeat, "DYNAMIC_SLATE_PATH", slate, raising=False)
    monkeypatch.setattr(heartbeat, "POLL_STATE_FILE", tmp_path / "poll_state.json", raising=False)
    monkeypatch.setenv("FLOSS_HEARTBEAT_CONFIRM_INTERVAL_TICKS", "72")

    signature = heartbeat.compute_poll_slate_signature()
    heartbeat.save_poll_state(
        {
            "last_slate_signature": signature,
            "last_poll_tick": 10,
            "last_poll_profile": "balanced",
            "last_poll_at": "2026-05-19T00:00:00+00:00",
        }
    )

    rotation = heartbeat.get_work_rotation({"rounds_today": 5, "ticks_today": 12})

    assert not any(item.name.startswith("poll_high_roi_actions") for item in rotation)


def test_completed_poll_records_slate_so_next_tick_skips_repetition(tmp_path, monkeypatch):
    heartbeat = load_heartbeat_module()
    slate = tmp_path / "next_slate.json"
    write_slate(slate)
    monkeypatch.setattr(heartbeat, "DYNAMIC_SLATE_PATH", slate, raising=False)
    monkeypatch.setattr(heartbeat, "POLL_STATE_FILE", tmp_path / "poll_state.json", raising=False)
    monkeypatch.setenv("FLOSS_HEARTBEAT_CONFIRM_INTERVAL_TICKS", "72")

    first_rotation = heartbeat.get_work_rotation({"rounds_today": 0, "ticks_today": 1})
    poll_item = next(
        item for item in first_rotation if item.name.startswith("poll_high_roi_actions")
    )
    heartbeat.mark_high_roi_poll_completed(poll_item, {"ticks_today": 1})

    second_rotation = heartbeat.get_work_rotation({"rounds_today": 5, "ticks_today": 2})

    assert not any(item.name.startswith("poll_high_roi_actions") for item in second_rotation)


def test_daily_round_cap_skips_poll_before_voter_spend(tmp_path, monkeypatch):
    heartbeat = load_heartbeat_module()
    slate = tmp_path / "next_slate.json"
    write_slate(slate)
    monkeypatch.setattr(heartbeat, "DYNAMIC_SLATE_PATH", slate, raising=False)
    monkeypatch.setattr(heartbeat, "POLL_STATE_FILE", tmp_path / "poll_state.json", raising=False)
    monkeypatch.setenv("FLOSS_DAILY_ROUND_CAP", "40")
    monkeypatch.setenv("FLOSS_HEARTBEAT_POLL_ROUND_COST", "5")

    rotation = heartbeat.get_work_rotation({"rounds_today": 38, "ticks_today": 1})

    assert not any(item.name.startswith("poll_high_roi_actions") for item in rotation)


def test_default_wide_sweep_does_not_use_diverse_max_every_two_hours(tmp_path, monkeypatch):
    heartbeat = load_heartbeat_module()
    slate = tmp_path / "next_slate.json"
    write_slate(slate)
    monkeypatch.setattr(heartbeat, "DYNAMIC_SLATE_PATH", slate, raising=False)
    monkeypatch.setattr(heartbeat, "POLL_STATE_FILE", tmp_path / "poll_state.json", raising=False)
    monkeypatch.delenv("FLOSS_HEARTBEAT_WIDE_INTERVAL_TICKS", raising=False)

    rotation = heartbeat.get_work_rotation({"rounds_today": 0, "ticks_today": 12})

    poll_items = [item for item in rotation if item.name.startswith("poll_high_roi_actions")]
    assert len(poll_items) == 1
    assert poll_items[0].args == ["--profile", "balanced"]


def test_profile_qualified_poll_name_counts_actual_ranked_actions():
    heartbeat = load_heartbeat_module()
    result = {
        "returncode": 0,
        "stdout_tail": "\n".join(
            [
                "Ranked actions:",
                "1. review-synthesis-staging outcome=accepted mean=+0.7 var=0.1",
                "2. radicle-bridge-spike outcome=accepted mean=+0.5 var=0.2",
            ]
        ),
    }

    assert heartbeat.estimate_rounds_from_result(
        "poll_high_roi_actions[balanced]", result
    ) == 2


def test_autonomous_synthesis_skips_when_staging_queue_exceeds_cap(tmp_path, monkeypatch):
    heartbeat = load_heartbeat_module()
    staging = tmp_path / "staging"
    staging.mkdir()
    for idx in range(3):
        (staging / f"draft_{idx}_draft.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(heartbeat, "SYNTHESIS_STAGING_DIR", staging, raising=False)
    monkeypatch.setenv("FLOSS_SYNTHESIS_STAGING_CAP", "2")
    monkeypatch.setenv("FLOSS_HEARTBEAT_DISABLE_POLLS", "1")

    rotation = heartbeat.get_work_rotation({"rounds_today": 0, "ticks_today": 1})

    assert not any(item.name == "autonomous_synthesis" for item in rotation)
