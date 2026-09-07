"""Tests for the ensemble transport layer (online-primary voters + embedder fallback).

Pure-unit: no network. Monkeypatches the gateway roster resolver and the
generation transports so the routing/fallback logic is exercised deterministically.

Run: python FLOSS/packages/reasoning_ensemble/tests/test_transport.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from packages.reasoning_ensemble import transport  # noqa: E402
from packages.reasoning_ensemble import synthesizer  # noqa: E402


def test_family_from_model():
    cases = {
        "groq/openai/gpt-oss-20b": "gpt-oss",
        "cerebras/gpt-oss-120b": "gpt-oss",
        "groq/qwen/qwen3.6-27b": "qwen",
        "groq/llama-3.3-70b-versatile": "llama",
        "mistral/devstral-small-latest": "mistral",
        "mistral/open-mistral-nemo": "mistral",
        "flowith/gemini-2.5-flash": "gemini",
        "flowith/deepseek-chat": "deepseek",
        "openrouter/openai/gpt-4o-mini": "gpt",
        "phi4-mini:latest": "phi",
    }
    for model, expected in cases.items():
        got = transport.family_from_model(model)
        assert got == expected, f"{model}: expected {expected}, got {got}"


def test_transport_for_model():
    assert transport._transport_for_model("flowith/gemini-2.5-flash") == "flowith"
    assert transport._transport_for_model("ollama/gemma3:12b-it-qat") == "ollama"
    assert transport._transport_for_model("groq/openai/gpt-oss-20b") == "litellm"
    assert transport._transport_for_model("cerebras/gpt-oss-120b") == "litellm"


def test_resolve_voter_pool_modes(monkeypatch):
    # This test is about transport MAPPING, not roster independence. The pool
    # now carries the same independence bar the consensus path enforces, and
    # this three-voter fixture is deliberately below it, so opt out explicitly
    # rather than widening the fixture and losing the routing cases.
    monkeypatch.setenv("FLOSS_ALLOW_DEGRADED_ROSTER", "1")
    fake_roster = {
        "groq-gpt-oss-20b": "groq/openai/gpt-oss-20b",
        "flowith-gemini": "flowith/gemini-2.5-flash",
        "ollama-gemma": "ollama/gemma3:12b-it-qat",
    }
    monkeypatch.setattr(
        transport, "resolve_default_voter_specs", lambda **kw: dict(fake_roster)
    )

    online, mode = transport.resolve_voter_pool(mode="online")
    assert mode == "online"
    assert len(online) == 3
    transports = {v["voter_id"]: v["transport"] for v in online}
    assert transports["groq-gpt-oss-20b"] == "litellm"
    assert transports["flowith-gemini"] == "flowith"
    assert transports["ollama-gemma"] == "ollama"
    # ollama/ spec is normalized to the raw model tag ollama expects
    ollama_v = next(v for v in online if v["voter_id"] == "ollama-gemma")
    assert ollama_v["model"] == "gemma3:12b-it-qat"

    local, mode = transport.resolve_voter_pool(mode="local")
    assert mode == "local"
    assert all(v["transport"] == "ollama" for v in local)
    assert len(local) == len(transport.LOCAL_VOTER_POOL)

    mixed, mode = transport.resolve_voter_pool(mode="mixed")
    assert mode == "mixed"
    assert len(mixed) == 3 + len(transport.LOCAL_VOTER_POOL)


def test_resolve_embedder_prefers_local():
    name, fn = transport.resolve_embedder(lambda t: [0.1, 0.2, 0.3])
    assert name == "mxbai-embed-large"
    assert fn("x") == [0.1, 0.2, 0.3]


def _dead_local(_text):
    raise RuntimeError("ollama down")


def _capture_cloud_fn(monkeypatch):
    captured = {}

    def fake_cloud_fn(model, timeout=transport.DEFAULT_EMBED_TIMEOUT_SECONDS):
        captured["model"] = model
        captured["timeout"] = timeout
        return lambda t: [0.9]

    monkeypatch.setattr(transport, "_cloud_embed_fn", fake_cloud_fn)
    return captured


def _clear_embed_credentials(monkeypatch):
    monkeypatch.delenv(transport.CLOUD_EMBED_ENV, raising=False)
    for candidate in transport._CLOUD_EMBED_CANDIDATES:
        prefix = candidate.split("/", 1)[0] + "/"
        for _prefix, env_vars in transport._CREDENTIAL_ENV_BY_PREFIX_FOR_TESTS:
            if _prefix == prefix:
                for env_var in env_vars:
                    monkeypatch.delenv(env_var, raising=False)


def test_resolve_embedder_falls_back_to_cloud(monkeypatch):
    """Mistral first when its credential is present -- unchanged from before."""
    _clear_embed_credentials(monkeypatch)
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    captured = _capture_cloud_fn(monkeypatch)

    name, fn = transport.resolve_embedder(_dead_local)

    assert name == transport.DEFAULT_CLOUD_EMBED_MODEL
    assert captured["model"] == transport.DEFAULT_CLOUD_EMBED_MODEL
    assert fn("x") == [0.9]


def test_the_cloud_embedder_skips_providers_with_no_credential(monkeypatch):
    """A valid roster without Mistral must not embed against Mistral.

    The fallback was unconditionally mistral/mistral-embed. A configuration with
    enough independent Groq/HuggingFace/NVIDIA/OpenRouter voters but no Mistral
    key completed every generation call and failed every embedding call, so
    synthesize() returned DEGRADED after paying for the generations.
    """
    _clear_embed_credentials(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    captured = _capture_cloud_fn(monkeypatch)

    name, _fn = transport.resolve_embedder(_dead_local)

    assert name == "openai/text-embedding-3-small"
    assert captured["model"] == name


def test_an_explicit_embed_model_is_honoured_verbatim(monkeypatch):
    """An operator instruction is not a guess to be second-guessed."""
    _clear_embed_credentials(monkeypatch)
    monkeypatch.setenv(transport.CLOUD_EMBED_ENV, "someprovider/custom-embed")
    captured = _capture_cloud_fn(monkeypatch)

    name, _fn = transport.resolve_embedder(_dead_local)

    assert name == "someprovider/custom-embed"
    assert captured["model"] == name


def test_with_no_credentials_the_historical_default_is_kept(monkeypatch):
    """Failing at the call site beats disappearing into a None."""
    _clear_embed_credentials(monkeypatch)
    _capture_cloud_fn(monkeypatch)

    name, _fn = transport.resolve_embedder(_dead_local)

    assert name == transport.DEFAULT_CLOUD_EMBED_MODEL


def test_an_unknown_voter_mode_is_refused(monkeypatch):
    """`locla` must not silently mean `online`.

    The catch-all default sent the prompt to cloud voters when the operator had
    asked -- with one transposed letter -- for the mode that keeps prompts off
    the network entirely.
    """
    import pytest

    monkeypatch.setenv(transport.MODE_ENV, "locla")
    with pytest.raises(ValueError, match="Unknown voter mode"):
        transport.resolve_voter_pool()


def test_the_online_pool_enforces_independence(monkeypatch):
    """The ensemble must not report a roster the consensus path would refuse."""
    import pytest

    monkeypatch.delenv("FLOSS_ALLOW_DEGRADED_ROSTER", raising=False)
    monkeypatch.setattr(
        transport,
        "resolve_default_voter_specs",
        lambda **kw: {
            "groq-a": "groq/openai/gpt-oss-120b",
            "groq-b": "groq/qwen/qwen3.6-27b",
        },
    )
    with pytest.raises(RuntimeError, match="below its own independence rule"):
        transport.resolve_voter_pool(mode="online")


def test_generate_routes_by_transport(monkeypatch):
    calls = {}

    def fake_litellm(m, p, t):
        calls["litellm"] = m
        return "L"

    def fake_flowith(m, p, t):
        calls["flowith"] = m
        return "F"

    monkeypatch.setattr(transport, "_litellm_generate", fake_litellm)
    monkeypatch.setattr(transport, "_flowith_generate", fake_flowith)

    def fake_ollama(model, prompt, timeout):
        calls["ollama"] = model
        return "O"

    assert transport.generate({"transport": "litellm", "model": "groq/x"}, "p", 10, fake_ollama) == "L"
    assert transport.generate({"transport": "flowith", "model": "flowith/x"}, "p", 10, fake_ollama) == "F"
    assert transport.generate({"transport": "ollama", "model": "x:latest"}, "p", 10, fake_ollama) == "O"
    assert calls == {"litellm": "groq/x", "flowith": "flowith/x", "ollama": "x:latest"}


def test_dispatch_voter_uses_injected_embedder(monkeypatch):
    """_dispatch_voter must embed with the run's resolved embedder, not ollama_embed."""
    monkeypatch.setattr(synthesizer.transport, "generate", lambda v, p, t, og: "a full sentence response. it has two sentences.")
    used = {}

    def fake_embed(text):
        used["called"] = True
        return [1.0, 0.0]

    voter = {"voter_id": "v1", "model": "groq/x", "family": "gpt-oss", "transport": "litellm"}
    resp = synthesizer._dispatch_voter(voter, "prompt", fake_embed)
    assert used.get("called") is True
    assert resp.response_embedding == [1.0, 0.0]
    assert resp.error is None


def _run():
    import inspect

    class _MP:
        def __init__(self):
            self._undo = []

        def setattr(self, obj, name, val):
            self._undo.append((obj, name, getattr(obj, name)))
            setattr(obj, name, val)

        def undo(self):
            for obj, name, val in reversed(self._undo):
                setattr(obj, name, val)

    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        mp = _MP()
        try:
            if "monkeypatch" in inspect.signature(t).parameters:
                t(mp)
            else:
                t()
            print(f"[PASS] {t.__name__}")
            passed += 1
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] {t.__name__}: {type(e).__name__}: {e}")
        finally:
            mp.undo()
    print(f"\n{passed}/{len(tests)} passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    raise SystemExit(_run())
