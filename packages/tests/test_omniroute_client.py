"""TDD tests for the OmniRoute OpenAI-compatible client helper.

Tests that the client posts the correct OpenAI-shaped payload and parses
the response correctly. Uses monkeypatch to avoid needing a live OmniRoute daemon.

Run: C:\\Python313\\python.exe -m pytest FLOSS/packages/tests/test_omniroute_client.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def test_completion_posts_openai_shape(monkeypatch):
    """completion() should POST an OpenAI-shaped request and return content text."""
    from packages import omniroute_client as oc

    seen = {}

    class FakeResp:
        status_code = 200
        text = ""

        def json(self):
            return {"choices": [{"message": {"content": "WEIGHT: 0.5\nRATIONALE: ok"}}]}

    def fake_post(url, json=None, headers=None, timeout=None):
        seen.update(url=url, json=json, headers=headers)
        return FakeResp()

    monkeypatch.setattr(oc.httpx, "post", fake_post)
    monkeypatch.setenv("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1")
    monkeypatch.setenv("OMNIROUTE_API_KEY", "test-key")

    text = oc.completion(
        "groq/openai/gpt-oss-20b",
        [{"role": "user", "content": "hi"}],
        max_tokens=8,
        temperature=0.1,
    )

    assert text == "WEIGHT: 0.5\nRATIONALE: ok"
    assert seen["url"].endswith("/v1/chat/completions")
    assert seen["json"]["model"] == "groq/openai/gpt-oss-20b"
    assert seen["json"]["max_tokens"] == 8
    assert seen["headers"]["Authorization"] == "Bearer test-key"


def test_completion_raises_on_http_error(monkeypatch):
    """completion() should raise RuntimeError on HTTP >= 400."""
    from packages import omniroute_client as oc

    class FakeResp:
        status_code = 500
        text = "Internal Server Error"

        def json(self):
            return {}

    monkeypatch.setattr(oc.httpx, "post", lambda *a, **kw: FakeResp())
    monkeypatch.setenv("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1")
    monkeypatch.setenv("OMNIROUTE_API_KEY", "k")

    try:
        oc.completion("any/model", [{"role": "user", "content": "x"}])
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "500" in str(e)


def test_embedding_returns_float_list(monkeypatch):
    """embedding() should POST to /embeddings and return a list of floats."""
    from packages import omniroute_client as oc

    seen = {}

    class FakeResp:
        status_code = 200
        text = ""

        def json(self):
            return {"data": [{"embedding": [0.1, 0.2, 0.3]}]}

    def fake_post(url, json=None, headers=None, timeout=None):
        seen.update(url=url, json=json)
        return FakeResp()

    monkeypatch.setattr(oc.httpx, "post", fake_post)
    monkeypatch.setenv("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1")
    monkeypatch.setenv("OMNIROUTE_API_KEY", "k")

    vec = oc.embedding("mistral-embed", "hello world")

    assert vec == [0.1, 0.2, 0.3]
    assert seen["url"].endswith("/v1/embeddings")
    assert seen["json"]["input"] == ["hello world"]
