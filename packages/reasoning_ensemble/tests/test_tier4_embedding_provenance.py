"""The Tier-4 prompt embedding must come from the run's resolved embedder.

PR41 review finding against synthesizer.py: _log_synthesis_action() called
ollama_embed(prompt) directly. Two consequences, both silent:

1. When the local health probe had already failed and the run resolved to a
   cloud embedder, the logging path re-tried the backend the run had just
   ruled out -- under the full 90s timeout, erasing the short-probe benefit --
   and on failure dropped prompt_embedding entirely, so the Tier-4 row could
   never bias adjacent-prompt routing.
2. When it succeeded, the row held an mxbai vector while the run's own vectors
   were cloud vectors. check_tier4_similarity_bias() cosine-compares those as
   if they shared a vector space. They do not.

These tests assert the property (the logged embedding comes from the resolved
embedder, and comparisons are model-matched), not the specific call site.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from packages.reasoning_ensemble import router  # noqa: E402
from packages.reasoning_ensemble import synthesizer  # noqa: E402


def _tier4_result() -> synthesizer.EnsembleSynthesis:
    return synthesizer.EnsembleSynthesis(
        prompt="p",
        prompt_hash="h",
        timestamp="2026-08-30T00:00:00Z",
        duration_seconds=1.0,
        voter_responses=[],
        tier_classification=synthesizer.TierClassification(
            tier="tier4",
            cluster_assignments={},
            cluster_sizes={},
            largest_cluster_id=0,
            largest_cluster_fraction=1.0,
            minority_coherent_voters=[],
            similarity_matrix=[],
            separation={},
        ),
        final_synthesis="s",
    )


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _log(monkeypatch, tmp_path, **kwargs) -> list[dict]:
    log = tmp_path / "reasoning-activity.jsonl"
    monkeypatch.setattr(synthesizer, "REASONING_ACTIVITY_LOG", log)
    monkeypatch.setattr(synthesizer, "append_action", lambda action: None)
    synthesizer._log_synthesis_action(
        _tier4_result(), "prompt", "h", "2026-08-30T00:00:00Z", success=True, **kwargs
    )
    return _rows(log)


def test_the_resolved_embedder_is_used_not_the_one_the_run_ruled_out(
    monkeypatch, tmp_path
):
    def must_not_run(text, timeout=None):
        raise AssertionError("re-probed the backend the run already ruled out")

    monkeypatch.setattr(synthesizer, "ollama_embed", must_not_run)

    rows = _log(
        monkeypatch,
        tmp_path,
        embed_fn=lambda text: [0.5, 0.5],
        embed_name="mistral/mistral-embed",
    )

    assert rows[0]["prompt_embedding"] == [0.5, 0.5]


def test_the_row_records_which_embedder_produced_the_vector(monkeypatch, tmp_path):
    rows = _log(
        monkeypatch,
        tmp_path,
        embed_fn=lambda text: [0.5],
        embed_name="mistral/mistral-embed",
    )

    assert rows[0]["prompt_embedding_model"] == "mistral/mistral-embed"


def test_a_failed_embed_leaves_no_embedding_behind(monkeypatch, tmp_path):
    def boom(text):
        raise RuntimeError("embedder down")

    rows = _log(monkeypatch, tmp_path, embed_fn=boom, embed_name="whatever")

    assert "prompt_embedding" not in rows[0]
    assert "prompt_embedding_model" not in rows[0]
    assert rows[0]["tier_classification"] == "tier4"


def test_similarity_skips_rows_from_a_different_vector_space(monkeypatch):
    monkeypatch.setattr(
        router,
        "_read_activity_tail",
        lambda n=None: [
            {
                "tier_classification": "tier4",
                "prompt_hash": "cloud-row",
                "prompt_embedding": [1.0, 0.0],
                "prompt_embedding_model": "mistral/mistral-embed",
            }
        ],
    )

    # Identical vector, different space: a cosine of 1.0 here would be a lie.
    assert router.check_tier4_similarity_bias([1.0, 0.0], "mxbai-embed-large") == (
        None,
        None,
    )


def test_rows_predating_the_model_field_are_treated_as_the_legacy_embedder(
    monkeypatch,
):
    monkeypatch.setattr(
        router,
        "_read_activity_tail",
        lambda n=None: [
            {
                "tier_classification": "tier4",
                "prompt_hash": "legacy-row",
                "prompt_embedding": [1.0, 0.0],
            }
        ],
    )

    prior, sim = router.check_tier4_similarity_bias(
        [1.0, 0.0], router.LEGACY_EMBED_MODEL
    )

    assert prior == "legacy-row"
    assert sim >= router.TIER4_SIMILARITY_THRESHOLD


def test_the_two_modules_agree_on_the_legacy_embedder_name(monkeypatch, tmp_path):
    """synthesizer cannot import router (cycle), so the default is duplicated.

    Pin the duplication: a rename on one side must not silently make every
    historical row unmatchable on the other.
    """
    monkeypatch.setattr(synthesizer, "ollama_embed", lambda text, timeout=None: [0.1])

    rows = _log(monkeypatch, tmp_path, embed_fn=None, embed_name=None)

    assert rows[0]["prompt_embedding_model"] == router.LEGACY_EMBED_MODEL
