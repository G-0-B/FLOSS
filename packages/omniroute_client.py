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
        },
        headers=_headers(),
        timeout=timeout,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"OmniRoute HTTP {resp.status_code}: {resp.text[:200]!r}")
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
        raise RuntimeError(f"OmniRoute embeddings HTTP {resp.status_code}: {resp.text[:200]!r}")
    return list(resp.json()["data"][0]["embedding"])
