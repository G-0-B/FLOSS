"""Regression contracts for late PR38 review findings."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KTE_DEV_PATH = ROOT / "evals" / "knowledge_triple_extraction" / "dev.jsonl"
RESEARCH_SKILL_PATH = (
    ROOT / "skill-corpus" / "recent-open-distributed-intelligence-research" / "SKILL.md"
)


def _kte_dev_row(row_id: str) -> dict[str, object]:
    rows = (
        json.loads(line)
        for line in KTE_DEV_PATH.read_text(encoding="utf-8").splitlines()
    )
    return next(row for row in rows if row["id"] == row_id)


def test_future_tense_dev_golden_obeys_skip_future_instruction() -> None:
    row = _kte_dev_row("kte-dev-004")
    input_data = row["input"]

    assert "Skip negated, conditional, future" in input_data["context"]["instructions"]
    assert "may supersede" in input_data["text"]
    assert "next release cycle" in input_data["text"]
    assert row["golden"]["triples"] == []


def test_research_skill_has_portable_fallback_for_optional_arxiv_helper() -> None:
    text = RESEARCH_SKILL_PATH.read_text(encoding="utf-8")

    assert "If the `literature-search-arxiv` skill or its scripts are installed" in text
    assert "Otherwise, use the harness's configured live web/search/browser tools" in text
    assert "Never claim an unavailable helper ran" in text
    assert "**CRITICAL**: Invoke the `literature-search-arxiv`" not in text
