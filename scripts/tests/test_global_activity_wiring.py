from __future__ import annotations

import importlib.util
import subprocess
import sys
import types
from pathlib import Path


FLOSS_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = FLOSS_ROOT.parent


def _ensure_import_stubs() -> None:
    if "dotenv" not in sys.modules:
        dotenv = types.ModuleType("dotenv")
        dotenv.load_dotenv = lambda *_args, **_kwargs: None
        sys.modules["dotenv"] = dotenv
    if "litellm" not in sys.modules:
        litellm = types.ModuleType("litellm")
        litellm.completion = lambda *_args, **_kwargs: None
        sys.modules["litellm"] = litellm


def load_module(name: str, path: Path):
    _ensure_import_stubs()
    if str(FLOSS_ROOT) not in sys.path:
        sys.path.insert(0, str(FLOSS_ROOT))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_router_activity_log_tees_to_global_action(tmp_path, monkeypatch):
    router = load_module(
        "router_under_test",
        FLOSS_ROOT / "packages" / "reasoning_ensemble" / "router.py",
    )
    actions = []
    monkeypatch.setattr(router, "ACTIVITY_LOG", tmp_path / "reasoning.jsonl")
    monkeypatch.setattr(router, "append_action", actions.append, raising=False)

    decision = router.RouterDecision(
        mode="single_strong",
        reason="forced test",
        confidence=1.0,
        prompt_hash="abc123",
        model="router-model",
        embed_model="embed-model",
        timestamp="2026-05-18T00:00:00+00:00",
        duration_seconds=0.25,
        bias_applied="force_flag",
    )

    router.append_activity(decision, "Classify this prompt")

    assert (tmp_path / "reasoning.jsonl").exists()
    assert len(actions) == 1
    action = actions[0]
    assert action.kind == "router_decision"
    assert action.harness == "reasoning_ensemble/router.py"
    assert action.routing_decision["mode"] == "single_strong"
    assert action.inputs["prompt_preview"] == "Classify this prompt"


def test_heartbeat_run_work_item_emits_global_action(monkeypatch):
    heartbeat = load_module(
        "heartbeat_under_test",
        FLOSS_ROOT / "scripts" / "heartbeat.py",
    )
    actions = []
    monkeypatch.setattr(heartbeat, "append_action", actions.append, raising=False)
    monkeypatch.setattr(heartbeat, "log_tick_line", lambda _msg: None)

    class Proc:
        returncode = 0
        stdout = "ok"
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: Proc())

    item = heartbeat.WorkItem(
        name="unit-test-work",
        script=str(FLOSS_ROOT / "scripts" / "noop.py"),
        args=["--flag"],
        flourishing_rationale="exercise global Action tee",
        timeout_seconds=5,
    )

    result = heartbeat.run_work_item(item)

    assert result["returncode"] == 0
    assert len(actions) == 1
    action = actions[0]
    assert action.kind == "heartbeat_work_item"
    assert action.success is True
    assert action.inputs["item"] == "unit-test-work"
    assert action.outputs["returncode"] == 0


def test_harvest_subsystem_activity_tees_success_to_global_action(tmp_path, monkeypatch):
    harvest = load_module(
        "harvest_under_test",
        FLOSS_ROOT / "scripts" / "harvest_reuse_ledger.py",
    )
    actions = []
    monkeypatch.setattr(harvest, "HARVEST_DIR", tmp_path)
    monkeypatch.setattr(harvest, "ACTIVITY_LOG", tmp_path / "activity.jsonl")
    monkeypatch.setattr(harvest, "append_action", actions.append, raising=False)

    harvest.append_activity(
        "harvest_success",
        target="owner/repo",
        entry_id="0016",
        model="gemini-test",
        draft_path=".agent-surface/harvest/staging/0016_owner_repo_draft.yaml",
        duration_seconds=1.2,
        license_from_metadata="MIT",
    )

    assert (tmp_path / "activity.jsonl").exists()
    assert len(actions) == 1
    action = actions[0]
    assert action.kind == "harvest_review"
    assert action.success is True
    assert action.inputs["target"] == "owner/repo"
    assert action.staging_paths == [".agent-surface/harvest/staging/0016_owner_repo_draft.yaml"]


def test_poll_payload_emits_global_action(monkeypatch):
    poll = load_module(
        "poll_under_test",
        FLOSS_ROOT / "scripts" / "poll_high_roi_actions.py",
    )
    actions = []
    monkeypatch.setattr(poll, "append_action", actions.append, raising=False)
    payload = {
        "poll_stamp": "20260518T000000Z",
        "profile": "test",
        "json_path": str(WORKSPACE_ROOT / ".agent-surface" / "polls" / "poll.json"),
        "markdown_path": str(WORKSPACE_ROOT / ".agent-surface" / "polls" / "poll.md"),
        "roster": [{"name": "voter-a", "model": "model-a", "enabled": True}],
        "results": [
            {
                "slug": "candidate-a",
                "summary": "Candidate A",
                "claim_id": "claim-1",
                "decision": {"outcome": "accepted", "tally_mean": 0.7, "votes": []},
            }
        ],
    }

    poll.emit_poll_action(payload, started_at="2026-05-18T00:00:00+00:00")

    assert len(actions) == 1
    action = actions[0]
    assert action.kind == "high_roi_poll"
    assert action.success is True
    assert action.outputs["result_count"] == 1
    assert action.staging_paths == [".agent-surface/polls/poll.json", ".agent-surface/polls/poll.md"]


def test_synthesis_stage_draft_returns_path_and_emits_global_action(tmp_path, monkeypatch):
    synthesis = load_module(
        "synthesis_under_test",
        FLOSS_ROOT / "scripts" / "autonomous_synthesis_loop.py",
    )
    actions = []
    monkeypatch.setattr(synthesis, "STAGING_DIR", tmp_path)
    monkeypatch.setattr(synthesis, "append_action", actions.append, raising=False)

    source = tmp_path / "source.md"
    source.write_text("# Source\n", encoding="utf-8")

    draft_path = synthesis.stage_draft(source, "test-model", "Extracted insights")

    assert draft_path == tmp_path / "source_draft.json"
    assert draft_path.exists()
    assert len(actions) == 1
    action = actions[0]
    assert action.kind == "knowledge_synthesis"
    assert action.success is True
    assert action.inputs["source_file"].endswith("source.md")
    assert action.staging_paths == [str(draft_path)]
