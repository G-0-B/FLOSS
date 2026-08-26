"""Provider attribution and the bounded local-embedder probe.

Two PR41 review findings against synthesizer.py:

1. The staged Action derived `provider` from the model id's prefix, so with
   FLOSS_MODEL_BACKEND=omniroute every online voter was recorded as `groq`,
   `mistral`, and so on -- the model's vendor, not the wire the request took.
   scripts/autonomous_synthesis_loop.py records this correctly via
   active_model_backend(), so the two paths disagreed about the same run and
   corrupted exactly the provider-level comparison a transport migration needs.
2. resolve_embedder() health-probed local Ollama with the full 90s embed
   timeout before dispatching any voter. An Ollama that accepts the connection
   but stalls on the embedding endpoint therefore blocked the run past the 120s
   reasoning-MCP timeout, with a working cloud fallback available throughout.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from packages.reasoning_ensemble import synthesizer  # noqa: E402
from packages.reasoning_ensemble import transport  # noqa: E402


def _response(transport_name: str, model: str) -> synthesizer.VoterResponse:
    return synthesizer.VoterResponse(
        voter_id="v",
        model=model,
        family="f",
        response="text",
        response_hash="h",
        response_embedding=[0.1],
        duration_seconds=0.1,
        transport_name=transport_name,
    )


def test_omniroute_runs_are_attributed_to_omniroute(monkeypatch):
    monkeypatch.setenv("FLOSS_MODEL_BACKEND", "omniroute")
    label = synthesizer._provider_label(_response("litellm", "groq/openai/gpt-oss-120b"))
    assert label == "omniroute", "the wire used, not the model's vendor"


def test_litellm_runs_are_attributed_to_litellm(monkeypatch):
    monkeypatch.setenv("FLOSS_MODEL_BACKEND", "litellm")
    label = synthesizer._provider_label(_response("litellm", "groq/openai/gpt-oss-120b"))
    assert label == "litellm"


def test_local_and_flowith_voters_keep_their_own_labels(monkeypatch):
    monkeypatch.setenv("FLOSS_MODEL_BACKEND", "omniroute")
    assert synthesizer._provider_label(_response("ollama", "gemma3:12b")) == "ollama-local"
    assert synthesizer._provider_label(_response("flowith", "flowith/x")) == "flowith"


def test_the_local_probe_uses_the_short_timeout(monkeypatch):
    seen = {}

    def fake_request(path, payload, timeout):
        seen["timeout"] = timeout
        return {"embedding": [0.1, 0.2]}

    monkeypatch.setattr(synthesizer, "_ollama_request", fake_request)

    synthesizer._local_embed_probe("healthcheck")

    assert seen["timeout"] == synthesizer.EMBED_PROBE_TIMEOUT_SECONDS
    assert seen["timeout"] < synthesizer.EMBED_TIMEOUT_SECONDS


def test_real_embeds_keep_the_full_timeout(monkeypatch):
    seen = {}

    def fake_request(path, payload, timeout):
        seen["timeout"] = timeout
        return {"embedding": [0.1, 0.2]}

    monkeypatch.setattr(synthesizer, "_ollama_request", fake_request)

    synthesizer.ollama_embed("real work")

    assert seen["timeout"] == synthesizer.EMBED_TIMEOUT_SECONDS


def test_a_healthy_probe_selects_the_full_timeout_embedder():
    """The probe decides; the returned callable is the one that does the work."""
    calls = []

    def probe(text):
        calls.append(("probe", text))
        return [0.1]

    def worker(text):
        calls.append(("worker", text))
        return [0.2]

    name, fn = transport.resolve_embedder(probe, local_embed_fn=worker)

    assert name == "mxbai-embed-large"
    assert fn("payload") == [0.2]
    assert calls == [("probe", "healthcheck"), ("worker", "payload")]


def test_one_callable_still_works():
    """Callers passing a single function keep the old behaviour."""
    name, fn = transport.resolve_embedder(lambda t: [0.5])
    assert name == "mxbai-embed-large"
    assert fn("x") == [0.5]


def test_failed_generation_keeps_its_own_transport():
    """A provider failure must be attributed to the provider that failed.

    voter_transport used to be resolved inside the try, and the except branch
    built its VoterResponse without it, so the field fell back to its "litellm"
    default. Every failed ollama or flowith call was therefore recorded as a
    litellm failure in the staged artifact and in _log_synthesis_action() --
    the exact data a provider failure-rate audit reads.
    """

    def _explode(voter, prompt, timeout, ollama_generate):
        raise RuntimeError("provider exploded")

    original = synthesizer.transport.generate
    synthesizer.transport.generate = _explode
    try:
        for wire in ("ollama", "flowith", "litellm"):
            result = synthesizer._dispatch_voter(
                {
                    "voter_id": f"v-{wire}",
                    "model": f"{wire}/m",
                    "family": wire,
                    "transport": wire,
                },
                "prompt",
            )
            assert result.error.startswith("RuntimeError")
            assert result.transport_name == wire, (
                f"{wire} failure attributed to {result.transport_name}"
            )
    finally:
        synthesizer.transport.generate = original


def test_cloud_embedder_receives_the_runs_embedding_budget(monkeypatch):
    """The cloud wrapper must carry the 90s budget, not the client's 60s default.

    resolve_embedder()'s docstring already promised the resolved embedder does
    real work under the normal timeout. The cloud path passed no timeout at all,
    so an embedding finishing between 60s and 90s was recorded as failed and its
    voter dropped -- a run inside its configured budget pushed to DEGRADED by
    the budget not being forwarded.
    """
    # Pinned explicitly: FLOSS_MODEL_BACKEND is read at call time, and with it
    # left to the ambient environment this test took the omniroute branch and
    # made a live HTTP request during the suite.
    monkeypatch.setenv("FLOSS_MODEL_BACKEND", "litellm")
    seen: dict[str, object] = {}

    def _fake_embedding(model, input, timeout=None):  # noqa: A002
        seen["timeout"] = timeout
        return type("R", (), {"data": [{"embedding": [0.1, 0.2]}]})()

    import sys
    import types

    stub = types.ModuleType("litellm")
    stub.embedding = _fake_embedding
    original = sys.modules.get("litellm")
    sys.modules["litellm"] = stub
    try:
        embed = transport._cloud_embed_fn("some/model", 90.0)
        assert embed("text") == [0.1, 0.2]
        assert seen["timeout"] == 90.0
    finally:
        if original is None:
            sys.modules.pop("litellm", None)
        else:
            sys.modules["litellm"] = original


def test_resolve_embedder_threads_the_timeout_to_the_cloud_fallback():
    def _dead_local(_text):
        raise RuntimeError("no local ollama")

    captured: dict[str, object] = {}
    original = transport._cloud_embed_fn

    def _spy(model, timeout=transport.DEFAULT_EMBED_TIMEOUT_SECONDS):
        captured["model"] = model
        captured["timeout"] = timeout
        return lambda text: [0.0]

    transport._cloud_embed_fn = _spy
    try:
        transport.resolve_embedder(_dead_local, embed_timeout=90.0)
        assert captured["timeout"] == 90.0
    finally:
        transport._cloud_embed_fn = original


def test_omniroute_embedder_also_receives_the_budget(monkeypatch):
    """The other branch of the same wrapper, and the one that had the 60s default."""
    monkeypatch.setenv("FLOSS_MODEL_BACKEND", "omniroute")
    seen: dict[str, object] = {}

    import sys
    import types

    stub = types.ModuleType("packages.omniroute_client")

    def _fake_embedding(model, text, *, timeout=60.0):
        seen["timeout"] = timeout
        return [0.3, 0.4]

    stub.embedding = _fake_embedding
    original = sys.modules.get("packages.omniroute_client")
    sys.modules["packages.omniroute_client"] = stub
    try:
        assert transport._cloud_embed_fn("some/model", 90.0)("text") == [0.3, 0.4]
        assert seen["timeout"] == 90.0, (
            "omniroute_client.embedding() defaults to 60s; an embedding "
            "finishing between 60s and 90s was dropped inside its own budget"
        )
    finally:
        if original is None:
            sys.modules.pop("packages.omniroute_client", None)
        else:
            sys.modules["packages.omniroute_client"] = original
