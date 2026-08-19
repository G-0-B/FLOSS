"""Tests for the ObjectGraph spike (N6) against the live skill-corpus.

Success criteria from FLOSS/docs/superpowers/specs/2026-06-12-objectgraph-spike.md.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import objectgraph_spike as og  # noqa: E402


def _index():
    return og.build_index()


def test_section_granularity_and_types():
    index = _index()
    stats = index["stats"]
    assert stats["nodes"] > stats["documents"], "section granularity must exceed doc count"
    types = {n["type"] for n in index["nodes"]}
    assert {"skill", "section"} <= types
    assert types & {"reference", "changelog"}, "expected reference/changelog doc types"


def test_edge_kinds_present():
    index = _index()
    kinds = {e["kind"] for e in index["edges"]}
    assert {"contains", "next"} <= kinds
    # refs edges exist only if corpus docs link each other; do not hard-require
    for edge in index["edges"]:
        assert "from" in edge and "to" in edge


def test_idempotent_write(tmp_path, monkeypatch):
    monkeypatch.setattr(og, "OUTPUT_PATH", tmp_path / "og.json")
    index = _index()
    assert og.write_index(index) is True, "first write must write"
    assert og.write_index(index) is False, "unchanged rewrite must be a no-op"


def test_resolve_known_answer(tmp_path, monkeypatch):
    monkeypatch.setattr(og, "OUTPUT_PATH", tmp_path / "og.json")
    og.write_index(_index())
    result = og.resolve("token budget", limit=3)
    assert result["hits"], "known-answer query must hit"
    top = result["hits"][0]
    assert "token-budget" in top["node"]
    assert "flossi0ullk-orient/SKILL.md" in top["provenance"]


def test_expand_returns_source_text(tmp_path, monkeypatch):
    monkeypatch.setattr(og, "OUTPUT_PATH", tmp_path / "og.json")
    og.write_index(_index())
    top = og.resolve("token budget", limit=1)["hits"][0]["node"]
    text = og.expand(top)
    assert "verify at the artifact" in text
    assert "T0" in text


def test_synthesis_advisory_fires_on_broad_query(tmp_path, monkeypatch):
    monkeypatch.setattr(og, "OUTPUT_PATH", tmp_path / "og.json")
    og.write_index(_index())
    result = og.resolve("consensus gateway voter skill orient memory surface", limit=5)
    assert result["advisory"], "cross-doc query must trigger the synthesis advisory"
