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
    {
        "voter_id": "phi4-mini",
        "model": "phi4-mini:latest",
        "family": "phi",
        "transport": "ollama",
    },
    {
        "voter_id": "llama3.2-3b",
        "model": "llama3.2:3b-instruct-q4_K_S",
        "family": "llama",
        "transport": "ollama",
    },
    {
        "voter_id": "granite-code-3b",
        "model": "granite-code:3b-instruct-128k-q4_K_S",
        "family": "granite",
        "transport": "ollama",
    },
    {
        "voter_id": "qwen2.5-coder-3b",
        "model": "hf.co/unsloth/Qwen2.5-Coder-3B-Instruct-128K-GGUF:F16",
        "family": "qwen",
        "transport": "ollama",
    },
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


# ONE definition of the local embedder name. router and synthesizer each had
# their own copy of this env lookup, and resolve_embedder() had a third copy as
# a hardcoded literal -- so a run could embed with one model and label the row
# with another. Two earlier fixes corrected the two DOWNSTREAM copies; this is
# the one that produces the name.
EMBED_MODEL = os.environ.get("FLOSS_EMBED_MODEL", "mxbai-embed-large")


def _transport_for_model(model: str) -> str:
    lower = model.strip().lower()
    if lower.startswith("flowith/"):
        return "flowith"
    if lower.startswith("ollama/"):
        return "ollama"
    return "litellm"


def active_online_profile(profile: str | None = None) -> str:
    """The online profile a run will actually use, with aliases resolved.

    Exposed because the independence bar is re-checked on the SURVIVING voters
    after generation, and that check needs the same profile the pool was built
    from. Deriving it a second time at the call site is how two views of one
    roster end up disagreeing about whether it counts as independent.

    NORMALIZED, because the raw value can be an alias. Roster resolution follows
    the registry alias -- `mistral-free` selects the deliberately exempt
    `mistral` profile -- while the independence check received the alias, failed
    to find it in DEGRADED_OK_PROFILES, and refused the healthy single-provider
    roster the alias exists to select. One resolved name for both.
    """

    raw = profile or os.environ.get(ONLINE_PROFILE_ENV, DEFAULT_ONLINE_PROFILE)
    try:
        from packages.metacoordinator_mcp.voters import _normalize_profile

        return _normalize_profile(raw)
    except Exception:  # noqa: BLE001 -- an unreadable registry must not break routing
        return raw


def _online_pool(profile: str | None, *, check_independence: bool = True) -> list[dict]:
    """Resolve the online voter pool from the gateway roster (credential-gated).

    `check_independence=False` is for mixed mode ONLY, which appends the local
    pool afterwards and judges the combined roster. Checking here as well would
    refuse a pool that is independent once the local voters are added.
    """
    prof = active_online_profile(profile)
    specs = resolve_default_voter_specs(profile=prof, include_unavailable=False)
    # The same independence bar the consensus path enforces, on the same roster
    # after the same credential filtering. `synthesize()` only ever checked
    # MIN_VOTERS, so `diverse` with just Groq and Mistral credentials produced
    # three voters across TWO provider surfaces, passed, and reported an
    # ensemble result that assert_roster_is_independent() would have refused --
    # two views of one roster disagreeing about whether it counts as
    # independent. Honours FLOSS_ALLOW_DEGRADED_ROSTER like the consensus path.
    if check_independence:
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


def _independence_route(voter: dict) -> str:
    """A route the independence check can read the surface out of.

    _online_pool strips the `ollama/` prefix so the tag matches what Ollama
    expects, and LOCAL_VOTER_POOL carries bare tags for the same reason. Handed
    to the independence check as-is, `_derive_surface("phi4-mini:latest")`
    returns the whole tag, so four local voters read as FOUR provider surfaces
    and a mixed roster of nothing but local models would clear the surface bar
    on its own. Put the transport back on when the id has no route in it.
    """

    # TRANSPORT IS THE AUTHORITY, NEVER THE ID.
    #
    # The first version of this keyed on "does the id contain a slash", which
    # is the identical mistake generate() documents sixty lines above: the
    # retained local pool's fourth entry is
    # `hf.co/unsloth/Qwen2.5-Coder-3B-Instruct-128K-GGUF:F16`, an OLLAMA tag
    # with two slashes in it, so the heuristic read `hf.co` as a provider
    # surface and turned four local voters into two. The `transport` field
    # exists precisely because the wire is not derivable from the model id.
    model = voter["model"]
    if (voter.get("transport") or "ollama") == "ollama":
        return f"ollama/{model}"
    return model


def resolve_voter_pool(
    mode: str | None = None, online_profile: str | None = None
) -> tuple[list[dict], str]:
    """Return (pool, resolved_mode). Honors FLOSS_ENSEMBLE_VOTER_MODE."""
    resolved_mode = (mode or os.environ.get(MODE_ENV, DEFAULT_MODE)).strip().lower()
    if resolved_mode == "local":
        return list(LOCAL_VOTER_POOL), resolved_mode
    if resolved_mode == "mixed":
        # JUDGE THE POOL THAT ACTUALLY VOTES.
        #
        # _online_pool() raised before the local voters were appended, so a
        # credential-filtered online subset that is narrow ON ITS OWN refused
        # the run -- even though the same subset plus the four Ollama voters is
        # three surfaces and seven families, comfortably independent. Mixed
        # mode existed precisely to make that combination available, and the
        # only way to get it was the degraded-roster override, which says the
        # opposite of what is true about that roster.
        #
        # The check moves to the combined pool. Nothing is skipped: this is the
        # same bar on a strictly larger roster.
        combined = _online_pool(online_profile, check_independence=False) + list(
            LOCAL_VOTER_POOL
        )
        assert_roster_is_independent(
            active_online_profile(online_profile),
            {voter["voter_id"]: _independence_route(voter) for voter in combined},
        )
        return combined, resolved_mode
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
        raise RuntimeError(
            f"Flowith HTTP {response.status_code}: {response.text[:200]!r}"
        )
    payload = json.loads(response.text)
    text = payload["choices"][0]["message"]["content"].strip()
    if not text:
        raise RuntimeError("empty Flowith response")
    return text


def transport_name(voter: dict) -> str:
    """The wire this voter will actually go over. ONE definition, two readers.

    `generate()` decides the wire and the synthesizer labels the resulting
    Action with it. Those were two separate expressions with two different
    defaults for a voter that omits `transport`: this one said ollama, the
    label said litellm. Nothing failed loudly -- the call went to Ollama and
    the audit recorded LiteLLM, so provider failure rates and migration
    progress were computed from the wrong wire for exactly the pool
    (DEFAULT_VOTER_POOL) whose entries omit the field.

    Two agreeing defaults are a coincidence; one function is a coupling. The
    default itself is documented at the bottom of this module in `generate`.
    """
    return str(voter.get("transport") or "ollama")


def generate(voter: dict, prompt: str, timeout: int, ollama_generate) -> str:
    """Route one generation by voter transport. Raises on failure (caller wraps)."""
    # A LEGACY POOL HAS NO TRANSPORT FIELD, AND IS LOCAL.
    #
    # resolve_voter_pool() sets `transport` on every entry, so this default only
    # ever applies to an explicit pool passed by a caller -- which is what
    # DEFAULT_VOTER_POOL is retained for, and every entry in it is an Ollama
    # tag. Defaulting those to litellm sent local models to a provider that has
    # never heard of them, so each voter failed provider resolution and the run
    # degraded: the compatibility the retained pool exists to provide was the
    # one thing it did not have.
    #
    # OLLAMA, not an inference from the model id. The first version of this
    # keyed on a slash -- bare tag means local, provider-prefixed means litellm
    # -- and the retained pool's fourth entry is
    # `hf.co/unsloth/Qwen2.5-Coder-3B-Instruct-128K-GGUF:F16`, an Ollama tag
    # with two slashes in it. So the heuristic sent one of four local voters to
    # a cloud provider and left the nominal four-family ensemble with three.
    #
    # The `transport` field exists precisely because the wire is not derivable
    # from the model id; that tag is the proof. A pool that omits it is a v0.1
    # local pool, which is the only thing this default is for -- an explicit
    # pool of online models has to say so, and every resolved pool already does.
    transport = transport_name(voter)
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
            # The CONFIGURED local model, not the default's name. Returning the
            # literal meant `embed_name` was always truthy and always "mxbai",
            # so the `embed_name or EMBED_MODEL` fallbacks added downstream
            # could never fire: with FLOSS_EMBED_MODEL set, Tier-4 rows were
            # labelled mxbai while the router labelled its own vector with the
            # configured model, and the model-match check then skipped every
            # row it was supposed to compare.
            return EMBED_MODEL, working_fn
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
