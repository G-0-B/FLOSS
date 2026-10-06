"""OpenAI-compatible client for the local OmniRoute daemon.

One helper, reused by every model call site so litellm can be retired from
the hot path. OmniRoute presents an OpenAI-compatible endpoint at
``http://127.0.0.1:20128/v1`` — this module is a thin httpx wrapper.

Environment:
    OMNIROUTE_BASE_URL   default http://127.0.0.1:20128/v1
    OMNIROUTE_API_KEY    default omniroute-local
"""
from __future__ import annotations

import os

import httpx


class OmniRouteHTTPError(RuntimeError):
    """An OmniRoute HTTP error that still knows which HTTP error it was.

    Kept a RuntimeError subclass so existing `except RuntimeError` handlers are
    unaffected, but carrying `status_code` -- and, for 429, the class name
    callers already look for.

    Callers identify a rate limit by exception type or `status_code`
    (scripts/major_consolidation_sweep.py: `type(e).__name__ == "RateLimitError"
    or getattr(e, "status_code", None) == 429`) or by LiteLLM-specific text in
    the message (scripts/autonomous_synthesis_loop.py looks for "RateLimitError"
    or "rate_limit_exceeded"). A bare `RuntimeError(f"OmniRoute HTTP 429: ...")`
    matched none of them, so once FLOSS_MODEL_BACKEND=omniroute became the
    default a rate limit read as an ordinary failure: no backoff, no retry, and
    the caller kept issuing requests straight into the limit.
    """

    def __init__(self, status_code: int, body: str, *, endpoint: str = "chat/completions"):
        self.status_code = status_code
        self.body = body
        self.endpoint = endpoint
        detail = f"OmniRoute {endpoint} HTTP {status_code}: {body!r}"
        if status_code == 429:
            # The token the text-matching callers grep for. Naming it here means
            # they need no OmniRoute-specific knowledge to back off correctly.
            detail = f"RateLimitError (rate_limit_exceeded) -- {detail}"
        super().__init__(detail)


class OmniRouteRateLimitError(OmniRouteHTTPError):
    """Raised for HTTP 429 specifically, for callers that switch on type."""


def _http_error(status_code: int, body: str, *, endpoint: str) -> OmniRouteHTTPError:
    cls = OmniRouteRateLimitError if status_code == 429 else OmniRouteHTTPError
    return cls(status_code, body, endpoint=endpoint)


def _base() -> str:
    return os.environ.get("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1").rstrip("/")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {os.environ.get('OMNIROUTE_API_KEY', 'omniroute-local')}",
        "Content-Type": "application/json",
    }


def completion(
    model: str,
    messages: list[dict],
    *,
    max_tokens: int = 2000,
    temperature: float = 0.1,
    timeout: float = 60.0,
) -> str:
    """Post an OpenAI-shaped chat completion request, return the content text.

    Raises RuntimeError on HTTP >= 400.
    """
    resp = httpx.post(
        f"{_base()}/chat/completions",
        json={
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        },
        headers=_headers(),
        timeout=timeout,
    )
    if resp.status_code >= 400:
        raise _http_error(resp.status_code, resp.text[:200], endpoint="chat/completions")
    return (resp.json()["choices"][0]["message"]["content"] or "").strip()


def embedding(model: str, text: str, *, timeout: float = 60.0) -> list[float]:
    """Post an OpenAI-shaped embedding request, return the float vector.

    Raises RuntimeError on HTTP >= 400.
    """
    resp = httpx.post(
        f"{_base()}/embeddings",
        json={"model": model, "input": [text]},
        headers=_headers(),
        timeout=timeout,
    )
    if resp.status_code >= 400:
        raise _http_error(resp.status_code, resp.text[:200], endpoint="embeddings")
    return list(resp.json()["data"][0]["embedding"])
