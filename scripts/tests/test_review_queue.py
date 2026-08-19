from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def load_review_queue_module():
    script_path = Path(__file__).resolve().parents[1] / "review_queue.py"
    spec = importlib.util.spec_from_file_location("review_queue", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_collects_harvest_and_synthesis_items_with_sidecars(tmp_path):
    review_queue = load_review_queue_module()

    harvest_dir = tmp_path / ".agent-surface" / "harvest" / "staging"
    harvest_dir.mkdir(parents=True)
    draft = harvest_dir / "0016_owner_repo_draft.yaml"
    draft.write_text(
        "\n".join(
            [
                "- id: '0016'",
                "name: owner/repo",
                "license_status: pass MIT",
                "decision_hint: investigate_high_priority",
                "notes: >",
                "  Block text with a colon: should not become metadata.",
            ]
        ),
        encoding="utf-8",
    )
    provenance = harvest_dir / "0016_owner_repo_provenance.json"
    provenance.write_text(json.dumps({"source_url": "https://github.com/owner/repo"}), encoding="utf-8")
    review = harvest_dir / "0016_owner_repo_review_20260518.json"
    review.write_text(json.dumps({"fit": "adapter candidate"}), encoding="utf-8")

    synthesis_dir = tmp_path / "FLOSS" / "docs" / "knowledge_log" / "staging"
    synthesis_dir.mkdir(parents=True)
    synthesis = synthesis_dir / "metaharness_draft.json"
    synthesis.write_text(
        json.dumps(
            {
                "file_path": str(tmp_path / "FLOSS" / "docs" / "research" / "metaharness.md"),
                "model": "test-model",
                "staged_at": "2026-05-18T00:00:00Z",
                "insights": "Dense metaharness synthesis.",
            }
        ),
        encoding="utf-8",
    )

    items = review_queue.collect_review_items(tmp_path)

    assert [item.kind for item in items] == ["harvest_draft", "synthesis_draft"]

    harvest = items[0]
    assert harvest.item_id == "0016_owner_repo"
    assert harvest.status == "reviewed"
    assert harvest.provenance_path == ".agent-surface/harvest/staging/0016_owner_repo_provenance.json"
    assert harvest.review_paths == [".agent-surface/harvest/staging/0016_owner_repo_review_20260518.json"]
    assert harvest.metadata["id"] == "0016"
    assert "- id" not in harvest.metadata
    assert "Block text with a colon" not in harvest.metadata
    assert harvest.metadata["license_status"] == "pass MIT"
    assert harvest.metadata["decision_hint"] == "investigate_high_priority"

    synth = items[1]
    assert synth.item_id == "metaharness"
    assert synth.status == "needs_review"
    assert synth.metadata["model"] == "test-model"
    assert synth.metadata["source_file"].endswith("FLOSS/docs/research/metaharness.md")


def test_markdown_summary_is_stable_and_limited(tmp_path):
    review_queue = load_review_queue_module()

    harvest_dir = tmp_path / ".agent-surface" / "harvest" / "staging"
    harvest_dir.mkdir(parents=True)
    for idx in ("0016", "0017"):
        (harvest_dir / f"{idx}_owner_repo_draft.yaml").write_text(
            f"id: '{idx}'\nname: owner/repo-{idx}\nlicense_status: pass MIT\n",
            encoding="utf-8",
        )

    items = review_queue.collect_review_items(tmp_path)
    markdown = review_queue.render_markdown(items, limit=1)

    assert markdown.startswith("# Review Queue\n")
    assert "Total queued: 2" in markdown
    assert "harvest_draft: 2" in markdown
    assert "0016_owner_repo" in markdown
    assert "0017_owner_repo" not in markdown
