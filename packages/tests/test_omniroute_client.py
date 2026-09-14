"""TDD tests for the OmniRoute OpenAI-compatible client helper.

Tests that the client posts the correct OpenAI-shaped payload and parses
the response correctly. Uses monkeypatch to avoid needing a live OmniRoute daemon.

Run: C:\\Python313\\python.exe -m pytest FLOSS/packages/tests/test_omniroute_client.py -v
"""
import sys
from pathlib import Path

import pytest

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


def _fake_error_response(monkeypatch, status_code: int, body: str = "slow down"):
    from packages import omniroute_client as oc

    class FakeResp:
        def __init__(self):
            self.status_code = status_code
            self.text = body

        def json(self):  # pragma: no cover - never reached on an error path
            raise AssertionError("json() must not be called on an error response")

    monkeypatch.setattr(oc.httpx, "post", lambda *a, **kw: FakeResp())
    monkeypatch.setenv("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1")
    monkeypatch.setenv("OMNIROUTE_API_KEY", "k")
    return oc


def test_a_rate_limit_is_identifiable_by_status_code(monkeypatch):
    """scripts/major_consolidation_sweep.py switches on `status_code == 429`.

    A bare RuntimeError carried no status, so once omniroute became the default
    backend a 429 read as an ordinary failure: no backoff, and the caller kept
    issuing requests straight into the limit.
    """
    oc = _fake_error_response(monkeypatch, 429)

    try:
        oc.completion("m", [{"role": "user", "content": "hi"}])
    except RuntimeError as exc:  # the caller's own except clause
        assert getattr(exc, "status_code", None) == 429
    else:  # pragma: no cover
        raise AssertionError("expected an error")


def test_a_rate_limit_is_identifiable_by_message_text(monkeypatch):
    """scripts/autonomous_synthesis_loop.py greps the message instead."""
    oc = _fake_error_response(monkeypatch, 429)

    try:
        oc.completion("m", [{"role": "user", "content": "hi"}])
    except RuntimeError as exc:
        message = str(exc)
        assert "RateLimitError" in message or "rate_limit_exceeded" in message
    else:  # pragma: no cover
        raise AssertionError("expected an error")


def test_a_rate_limit_is_identifiable_by_type(monkeypatch):
    oc = _fake_error_response(monkeypatch, 429)

    with pytest.raises(oc.OmniRouteRateLimitError):
        oc.completion("m", [{"role": "user", "content": "hi"}])


def test_other_http_errors_are_not_labelled_rate_limits(monkeypatch):
    oc = _fake_error_response(monkeypatch, 500, "boom")

    with pytest.raises(oc.OmniRouteHTTPError) as excinfo:
        oc.completion("m", [{"role": "user", "content": "hi"}])

    assert not isinstance(excinfo.value, oc.OmniRouteRateLimitError)
    assert excinfo.value.status_code == 500
    assert "RateLimitError" not in str(excinfo.value)


def test_embedding_errors_carry_the_status_too(monkeypatch):
    oc = _fake_error_response(monkeypatch, 429)

    with pytest.raises(oc.OmniRouteRateLimitError) as excinfo:
        oc.embedding("mistral-embed", "hello")

    assert excinfo.value.status_code == 429
    assert excinfo.value.endpoint == "embeddings"


def test_the_error_is_still_a_runtime_error(monkeypatch):
    """Existing `except RuntimeError` handlers must keep working."""
    oc = _fake_error_response(monkeypatch, 503)

    with pytest.raises(RuntimeError):
        oc.completion("m", [{"role": "user", "content": "hi"}])
