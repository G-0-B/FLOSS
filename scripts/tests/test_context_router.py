from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


FLOSS_ROOT = Path(__file__).resolve().parents[2]


def load_context_router_module():
    if str(FLOSS_ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(FLOSS_ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "context_router_under_test",
        FLOSS_ROOT / "scripts" / "context_router.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["context_router_under_test"] = module
    spec.loader.exec_module(module)
    return module


def corpus(
    corpus_id: str,
    *,
    priority: int,
    keywords: list[str] | None = None,
    route_intents: list[str] | None = None,
) -> dict[str, object]:
    return {
        "id": corpus_id,
        "uri": f"floss://{corpus_id}",
        "tier": "L1",
        "priority": priority,
        "summary": f"{corpus_id} test corpus",
        "keywords": keywords or [],
        "route_label": f"{corpus_id} route",
        "route_policy": f"Route here for {corpus_id} intent.",
        "route_intents": route_intents or [],
        "roots": [f"FLOSS/{corpus_id}"],
    }


def test_route_intents_beat_generic_priority_for_source_chain_queries():
    router = load_context_router_module()
    manifest = {
        "corpora": [
            corpus(
                "canon",
                priority=100,
                keywords=["decision"],
                route_intents=["canonical authority", "ADR decision"],
            ),
            corpus(
                "source-chain",
                priority=80,
                keywords=["decision"],
                route_intents=["claim vote", "consensus provenance", "source chain"],
            ),
        ]
    }

    results = router.choose_corpora(
        manifest,
        "decision claim vote consensus provenance",
        limit=2,
    )

    assert [item["id"] for item in results] == ["source-chain", "canon"]
    assert "claim vote" in results[0]["matched_intents"]
    assert "consensus provenance" in results[0]["matched_intents"]
    assert results[0]["route_label"] == "source-chain route"


def test_routing_manifest_selects_expected_real_corpus_lanes():
    router = load_context_router_module()
    manifest = router.load_manifest(FLOSS_ROOT / "shared-context-surface.json")

    cases = [
        (
            "RAGRoute arxiv open distributed intelligence research report",
            "research",
            "research intake and synthesis",
        ),
        (
            "context_router.py implementation function class pytest bug",
            "code",
            "implementation and tests",
        ),
        (
            "AGENTMEMORY durable recall shared memory user preference",
            "agent-memory",
            "shared agent memory",
        ),
        (
            "published papers books background reference library",
            "reference",
            "published reference library",
        ),
    ]

    for query, expected_id, expected_label in cases:
        result = router.choose_corpora(manifest, query, limit=1)[0]

        assert result["id"] == expected_id
        assert result["route_label"] == expected_label
        assert result["matched_intents"], query


def test_markdown_shows_route_policy_and_intent_matches():
    router = load_context_router_module()
    manifest = {
        "corpora": [
            corpus(
                "research",
                priority=60,
                keywords=["research"],
                route_intents=["arxiv paper", "research report"],
            )
        ]
    }
    results = router.choose_corpora(
        manifest,
        "arxiv paper research report",
        limit=1,
    )

    markdown = router.render_markdown(results, "arxiv paper research report")

    assert "- Route label: `research route`" in markdown
    assert "- Route policy: Route here for research intent." in markdown
    assert "- Matched route intents:" in markdown
    assert "  - `arxiv paper`" in markdown
