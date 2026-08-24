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
