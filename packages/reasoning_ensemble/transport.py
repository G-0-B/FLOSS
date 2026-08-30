"""Voter + embedder transport for the reasoning ensemble.

=========================================================================
WHY THIS EXISTS
=========================================================================
`synthesizer.py` shipped v0.1 as **Ollama-only** (see its DEFAULT_VOTER_POOL
note): a 4-voter local pool that reliably hit 3-of-4 timeouts on
VRAM-constrained hardware because Ollama serializes GPU access and four 3B
generates + the embed model do not co-reside in 16 GB. The `degraded` branch
then simply gave up.

This module adds the "cloud voters via LiteLLM are Later" path the synthesizer
docstring promised, and makes **online-primary** the default: generation runs
on the same provider roster the consensus gateway already uses
(`metacoordinator_mcp/voter_registry.json`), so a deliberation no longer
depends on local GPU headroom. Local Ollama remains available via
FLOSS_ENSEMBLE_VOTER_MODE=local, and a mixed pool via =mixed.

Design notes:
- We reuse the gateway's roster RESOLUTION (`resolve_default_voter_specs`) and
  Flowith HELPERS, but NOT its Vote-returning voter callables — the ensemble
  needs free-text reasoning to embed and cluster, not WEIGHT/RATIONALE votes.
- Embeddings must all come from ONE model per run (cosine similarity requires a
  shared vector space). `resolve_embedder()` prefers local mxbai and falls back
  to a single cloud embedder so the ensemble still runs with Ollama fully down.
- One broken voter never breaks the round: every generate wraps errors and the
  synthesizer treats a missing embedding as a non-participating voter.

Env:
  FLOSS_ENSEMBLE_VOTER_MODE      online (default) | local | mixed
  FLOSS_ENSEMBLE_ONLINE_PROFILE  voter_registry profile for online pool (default: diverse)
  FLOSS_ENSEMBLE_EMBED_MODEL     cloud embedder for the fallback (default: mistral/mistral-embed)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Reuse the gateway's roster resolution + Flowith helpers (transport only).
from packages.metacoordinator_mcp.voters import (  # noqa: E402
    _CREDENTIAL_ENV_BY_PREFIX,
    _credential_state_for_model,
    _flowith_endpoint,
    _load_flowith_api_key,
    _parse_flowith_models,
    assert_roster_is_independent,
    resolve_default_voter_specs,
)

MODE_ENV = "FLOSS_ENSEMBLE_VOTER_MODE"
ONLINE_PROFILE_ENV = "FLOSS_ENSEMBLE_ONLINE_PROFILE"
CLOUD_EMBED_ENV = "FLOSS_ENSEMBLE_EMBED_MODEL"

DEFAULT_MODE = "online"
DEFAULT_ONLINE_PROFILE = "diverse"
DEFAULT_CLOUD_EMBED_MODEL = "mistral/mistral-embed"
# Cloud embedders tried in order when no FLOSS_ENSEMBLE_EMBED_MODEL is set, each
# gated on its provider credential by _credential_state_for_model. Mistral stays
# first so a credentialled Mistral configuration behaves exactly as before.
_CLOUD_EMBED_CANDIDATES: tuple[str, ...] = (
    "mistral/mistral-embed",
    "openai/text-embedding-3-small",
    "huggingface/BAAI/bge-large-en-v1.5",
    "gemini/text-embedding-004",
)

# Local pool used for mode=local / mode=mixed. Mirrors synthesizer's historical
# DEFAULT_VOTER_POOL so the local path is unchanged from v0.1.
LOCAL_VOTER_POOL: list[dict] = [
    {"voter_id": "phi4-mini", "model": "phi4-mini:latest", "family": "phi", "transport": "ollama"},
    {"voter_id": "llama3.2-3b", "model": "llama3.2:3b-instruct-q4_K_S", "family": "llama", "transport": "ollama"},
    {"voter_id": "granite-code-3b", "model": "granite-code:3b-instruct-128k-q4_K_S", "family": "granite", "transport": "ollama"},
    {"voter_id": "qwen2.5-coder-3b", "model": "hf.co/unsloth/Qwen2.5-Coder-3B-Instruct-128K-GGUF:F16", "family": "qwen", "transport": "ollama"},
]

# Family keyword → label. First match wins; order matters (gpt-oss before gpt).
_FAMILY_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("gpt-oss", "gpt-oss"),
    ("qwen", "qwen"),
    ("llama", "llama"),
    ("gemini", "gemini"),
    ("deepseek", "deepseek"),
    ("devstral", "mistral"),
    ("ministral", "mistral"),
    ("codestral", "mistral"),
    ("magistral", "mistral"),
    ("mistral", "mistral"),
    ("nemo", "mistral"),
    ("granite", "granite"),
    ("phi", "phi"),
    ("gpt", "gpt"),
    ("claude", "claude"),
)


def family_from_model(model: str) -> str:
    """Derive a coarse model-family label for diversity accounting."""
    lower = model.strip().lower()
    tail = lower.split("/")[-1]
    for keyword, label in _FAMILY_KEYWORDS:
        if keyword in lower:
            return label
    return tail.split("-")[0] or tail


def _transport_for_model(model: str) -> str:
    lower = model.strip().lower()
    if lower.startswith("flowith/"):
        return "flowith"
    if lower.startswith("ollama/"):
        return "ollama"
    return "litellm"


def _online_pool(profile: str | None) -> list[dict]:
    """Resolve the online voter pool from the gateway roster (credential-gated)."""
    prof = profile or os.environ.get(ONLINE_PROFILE_ENV, DEFAULT_ONLINE_PROFILE)
    specs = resolve_default_voter_specs(profile=prof, include_unavailable=False)
    # The same independence bar the consensus path enforces, on the same roster
    # after the same credential filtering. `synthesize()` only ever checked
    # MIN_VOTERS, so `diverse` with just Groq and Mistral credentials produced
    # three voters across TWO provider surfaces, passed, and reported an
    # ensemble result that assert_roster_is_independent() would have refused --
    # two views of one roster disagreeing about whether it counts as
    # independent. Honours FLOSS_ALLOW_DEGRADED_ROSTER like the consensus path.
    assert_roster_is_independent(prof, specs)
    pool: list[dict] = []
    for voter_id, model in specs.items():
        transport = _transport_for_model(model)
        # Normalize a bare "ollama/model" spec into the raw model tag ollama expects.
        raw_model = model.split("/", 1)[1] if transport == "ollama" else model
        pool.append(
            {
                "voter_id": voter_id,
                "model": raw_model,
                "family": family_from_model(model),
                "transport": transport,
            }
        )
    return pool


def resolve_voter_pool(mode: str | None = None, online_profile: str | None = None) -> tuple[list[dict], str]:
    """Return (pool, resolved_mode). Honors FLOSS_ENSEMBLE_VOTER_MODE."""
    resolved_mode = (mode or os.environ.get(MODE_ENV, DEFAULT_MODE)).strip().lower()
    if resolved_mode == "local":
        return list(LOCAL_VOTER_POOL), resolved_mode
    if resolved_mode == "mixed":
        return _online_pool(online_profile) + list(LOCAL_VOTER_POOL), resolved_mode
    if resolved_mode in {"", "online"}:
        return _online_pool(online_profile), "online"
    # An unknown mode is a configuration error, not a request for the default.
    # `FLOSS_ENSEMBLE_VOTER_MODE=locla` -- one transposition away from `local`,
    # the mode an operator picks specifically to keep prompts off the network --
    # used to fall through this branch and send the prompt to cloud voters.
    # Silently doing the opposite of what the operator asked, at cost and with
    # disclosure, is the one outcome worth failing for.
    raise ValueError(
        f"Unknown voter mode {resolved_mode!r} (from {MODE_ENV} or the `mode` "
        "argument). Expected 'online', 'local', or 'mixed'."
    )


# ---------------------------------------------------------------------------
# Generation transports (free-text; the synthesizer supplies the framed prompt)
# ---------------------------------------------------------------------------


def _litellm_generate(model: str, prompt: str, timeout: int) -> str:
    if os.environ.get("FLOSS_MODEL_BACKEND", "litellm") == "omniroute":
        from packages.omniroute_client import completion as _omni

        # timeout forwarded. Without it omniroute_client.completion() applies
        # its own 60s default against a 180s voter budget, so a generation
        # finishing between 60s and 180s is recorded as a failed voter and can
        # push the round to DEGRADED while staying inside its configured budget.
        #
        # This is the SIBLING of the embedding-path defect fixed earlier in this
        # branch. Fixing one omniroute call site and not the other is the same
        # mistake the failure-mode register records as FM-4.
        return _omni(
            model,
            [{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.4,
            timeout=timeout,
        )
    from litellm import completion

    resp = completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0.4,
        timeout=timeout,
    )
    return (resp.choices[0].message.content or "").strip()


def _flowith_generate(model: str, prompt: str, timeout: int) -> str:
    import requests

    models = _parse_flowith_models(model)
    api_key = _load_flowith_api_key()
    host, path = _flowith_endpoint()
    body = json.dumps(
        {
            "models": models,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "thinking": False,
            "online": False,
        }
    )
    response = requests.post(
        f"https://{host}{path}",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "FLOSSI0ULLK-Ensemble/0.1",
            "Accept": "application/json",
        },
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Flowith HTTP {response.status_code}: {response.text[:200]!r}")
    payload = json.loads(response.text)
    text = payload["choices"][0]["message"]["content"].strip()
    if not text:
        raise RuntimeError("empty Flowith response")
    return text


def generate(voter: dict, prompt: str, timeout: int, ollama_generate) -> str:
    """Route one generation by voter transport. Raises on failure (caller wraps)."""
    transport = voter.get("transport", "litellm")
    if transport == "ollama":
        return ollama_generate(voter["model"], prompt, timeout)
    if transport == "flowith":
        return _flowith_generate(voter["model"], prompt, timeout)
    return _litellm_generate(voter["model"], prompt, timeout)


# ---------------------------------------------------------------------------
# Embedder resolution (ONE model per run; local mxbai preferred, cloud fallback)
# ---------------------------------------------------------------------------


# Fallback embedding budget, used only when a caller does not supply one.
# resolve_embedder()'s docstring promised that the resolved embedder does real
# work "under the normal timeout", but the cloud wrapper passed no timeout at
# all, so omniroute_client.embedding() applied its own 60s default. An
# embedding that finished between 60s and 90s was recorded as failed, its voter
# was dropped from `embedded`, and a run inside its configured budget could be
# pushed to DEGRADED by the budget not being forwarded.
DEFAULT_EMBED_TIMEOUT_SECONDS = 90.0


def _cloud_embed_fn(model: str, timeout: float = DEFAULT_EMBED_TIMEOUT_SECONDS):
    def embed(text: str) -> list[float]:
        if os.environ.get("FLOSS_MODEL_BACKEND", "litellm") == "omniroute":
            from packages.omniroute_client import embedding as _omni_embed

            return _omni_embed(model, text, timeout=timeout)
        from litellm import embedding

        resp = embedding(model=model, input=[text], timeout=timeout)
        vec = resp.data[0]["embedding"]
        if not vec:
            raise RuntimeError(f"empty embedding from {model}")
        return list(vec)

    return embed


def resolve_embedder(
    probe_fn,
    local_embed_fn=None,
    *,
    embed_timeout: float = DEFAULT_EMBED_TIMEOUT_SECONDS,
) -> tuple[str, object]:
    """Pick the run's single embedder: local mxbai if it answers, else cloud.

    `probe_fn(text) -> list[float]` is the HEALTH PROBE and should carry a short
    timeout: it runs before any voter is dispatched, and a local Ollama that
    accepts the connection but stalls on the embedding endpoint used to block
    the whole run for the full 90s embed timeout -- past the 120s reasoning-MCP
    timeout -- with a working cloud fallback available the entire time.

    `local_embed_fn` is the embedder actually used for work once the probe
    succeeds, under the normal timeout. It defaults to `probe_fn` so a caller
    that passes one callable keeps the old single-argument behaviour.

    Returns (embedder_name, embed_callable).
    """
    working_fn = local_embed_fn or probe_fn
    try:
        vec = probe_fn("healthcheck")
        if vec:
            return "mxbai-embed-large", working_fn
    except Exception:  # noqa: BLE001 — fall through to cloud
        pass
    cloud_model = _available_cloud_embed_model()
    return cloud_model, _cloud_embed_fn(cloud_model, embed_timeout)


# Re-exported for tests that need to know which env vars gate each candidate.
_CREDENTIAL_ENV_BY_PREFIX_FOR_TESTS = _CREDENTIAL_ENV_BY_PREFIX


def _available_cloud_embed_model() -> str:
    """Pick a cloud embedder whose credentials are actually present.

    The fallback was unconditionally `mistral/mistral-embed`. A perfectly valid
    online configuration -- enough independent Groq, Hugging Face, NVIDIA and
    OpenRouter voters, no Mistral key -- therefore completed every generation
    call and then failed every embedding call, so `synthesize()` returned
    DEGRADED after paying for the generations. An explicit
    FLOSS_ENSEMBLE_EMBED_MODEL is still honoured verbatim; it is an operator
    instruction, not a guess.
    """
    explicit = os.environ.get(CLOUD_EMBED_ENV, "").strip()
    if explicit:
        return explicit

    for candidate in _CLOUD_EMBED_CANDIDATES:
        available, _reason = _credential_state_for_model(candidate)
        if available:
            return candidate

    # Nothing is credentialled. Return the historical default so the failure
    # says "no Mistral credential" at the call site rather than disappearing
    # into a None, and so behaviour is unchanged for a caller that has neither.
    return DEFAULT_CLOUD_EMBED_MODEL
