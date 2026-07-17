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
        "groq/qwen/qwen3-32b": "qwen",
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


def test_resolve_embedder_falls_back_to_cloud(monkeypatch):
    def dead_local(_text):
        raise RuntimeError("ollama down")

    captured = {}

    def fake_cloud_fn(model):
        captured["model"] = model
        return lambda t: [0.9]

    monkeypatch.setattr(transport, "_cloud_embed_fn", fake_cloud_fn)
    name, fn = transport.resolve_embedder(dead_local)
    assert name == transport.DEFAULT_CLOUD_EMBED_MODEL
    assert captured["model"] == transport.DEFAULT_CLOUD_EMBED_MODEL
    assert fn("x") == [0.9]


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
