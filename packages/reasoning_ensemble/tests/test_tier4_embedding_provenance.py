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


# ---------------------------------------------------------------------------
# The name that labels the vector must be the model that produced it -- at the
# source, not only at the two places that consume it.
# ---------------------------------------------------------------------------


def test_the_resolved_embedder_reports_the_configured_model(monkeypatch):
    """resolve_embedder returned the literal "mxbai-embed-large" whatever the
    probe actually used, so embed_name was always truthy and always wrong under
    FLOSS_EMBED_MODEL -- which meant the `embed_name or EMBED_MODEL` fallbacks
    added downstream could never fire.

    Patches the module attribute rather than reloading: a reload rebinds the
    name to a new object and leaves every module that imported it pointing at
    the old one, which is a test artefact rather than anything about the code.
    """
    from packages.reasoning_ensemble import transport

    monkeypatch.setattr(transport, "EMBED_MODEL", "nomic-embed-text")

    name, fn = transport.resolve_embedder(lambda text: [0.1])

    assert name == "nomic-embed-text"
    assert fn("x") == [0.1]


def test_one_definition_of_the_local_embedder_name():
    """Three copies of this lookup is how a vector came to be embedded by one
    model and labelled with another."""
    from packages.reasoning_ensemble import router, synthesizer, transport

    assert synthesizer.EMBED_MODEL == transport.EMBED_MODEL
    assert router.EMBED_MODEL == transport.EMBED_MODEL

    source = Path(transport.__file__).parent
    derivations = sorted(
        path.name
        for path in source.glob("*.py")
        if 'EMBED_MODEL = os.environ.get("FLOSS_EMBED_MODEL"'
        in path.read_text(encoding="utf-8")
    )
    assert derivations == ["transport.py"], f"re-derived in {derivations}"


def test_every_legacy_pool_entry_routes_to_ollama_not_litellm(monkeypatch):
    """DEFAULT_VOTER_POOL entries carry no `transport`, and defaulting them to
    litellm sent local models to a provider that has never heard of them.

    EVERY entry, not the first. The version of this test that checked
    DEFAULT_VOTER_POOL[0] passed against a slash-based heuristic that still
    misrouted the fourth entry -- an Ollama tag with two slashes in it -- so a
    four-family local ensemble quietly ran with three voters.
    """
    from packages.reasoning_ensemble import synthesizer, transport

    routed = []

    def fake_ollama(model, prompt, timeout):
        routed.append(model)
        return "local answer"

    def must_not_run(model, prompt, timeout):
        raise AssertionError(f"{model} was routed off-box")

    monkeypatch.setattr(transport, "_litellm_generate", must_not_run)
    monkeypatch.setattr(transport, "_flowith_generate", must_not_run)
    for voter in synthesizer.DEFAULT_VOTER_POOL:
        assert "transport" not in voter, f"{voter['voter_id']} is not legacy"
        assert transport.generate(voter, "prompt", 5, fake_ollama) == "local answer"

    assert routed == [v["model"] for v in synthesizer.DEFAULT_VOTER_POOL]
    assert any("/" in model for model in routed), "no slash-bearing tag covered"


def test_a_declared_transport_still_wins_over_the_inference(monkeypatch):
    """The inference applies only where the field is absent. An entry that
    names litellm must reach litellm even though its model has no slash."""
    from packages.reasoning_ensemble import transport

    routed = {}
    monkeypatch.setattr(
        transport,
        "_litellm_generate",
        lambda model, prompt, timeout: routed.setdefault("via", "litellm"),
    )

    def must_not_run(model, prompt, timeout):
        raise AssertionError("a declared litellm voter was routed to ollama")

    transport.generate(
        {"model": "bare-tag-no-slash", "transport": "litellm"},
        "prompt",
        5,
        must_not_run,
    )

    assert routed["via"] == "litellm"


def test_an_online_pool_must_declare_its_transport(monkeypatch):
    """This test previously asserted the opposite, and was wrong to.

    It encoded the slash heuristic -- provider-prefixed means litellm -- which
    the retained pool's own `hf.co/...` tag disproves. The wire is not derivable
    from a model id, which is why the field exists. A fieldless entry is a v0.1
    LOCAL pool; an online pool has to say so, and every resolved pool does.
    """
    from packages.reasoning_ensemble import transport

    routed = {}
    monkeypatch.setattr(
        transport,
        "_litellm_generate",
        lambda model, prompt, timeout: routed.setdefault("via", "litellm"),
    )

    transport.generate(
        {"model": "groq/llama-3.1-8b-instant", "transport": "litellm"},
        "prompt",
        5,
        lambda *a: (_ for _ in ()).throw(AssertionError("declared litellm hit ollama")),
    )

    assert routed["via"] == "litellm"
