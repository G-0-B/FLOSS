"""
Voter adapters for the FLOSSIØULLK consensus gate.

Each voter is a sync callable `Claim -> Vote` that calls out to a specific model
provider, parses the response, and returns a Vote with a weight in
[-CERTAINTY_LIMIT, CERTAINTY_LIMIT] plus a rationale.

This is the bridge that turns "we can call Groq/Cerebras/Flowith" into
"those providers are peers in the consensus gate." Every voter produced here
plugs into `consensus_gate.decide()` with no special-casing.
"""

from __future__ import annotations

import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Callable

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.orchestrator.claim_schema import (  # noqa: E402
    CERTAINTY_LIMIT,
    Claim,
    Vote,
)  # noqa: E402

Voter = Callable[[Claim], Vote]

VOTER_PROMPT = """You are a peer voter in a multi-agent consensus gate for the
FLOSSIØULLK project.

You have been given a Claim proposed by another agent. Evaluate it on its merits
and cast a single vote.

Your vote is a float WEIGHT in the closed interval [-0.999, 0.999]:
  +0.999 = strongest possible support (near certainty the claim is good)
  +0.5   = moderate support
   0.0   = neutral / no opinion / insufficient information
  -0.5   = moderate opposition
  -0.999 = strongest possible opposition (near certainty the claim is bad)

Never use exactly +1.0 or -1.0 — the domain is open at the extremes because
absolute certainty is incompatible with the consensus model.

Also provide a brief RATIONALE (1-3 sentences) explaining your vote.

OUTPUT FORMAT — return exactly these two lines and nothing else:
WEIGHT: <float>
RATIONALE: <text>

---
CLAIM TO EVALUATE:
  Proposer:     {proposer}
  Type:         {proposal_type}
  Blast radius: {blast_radius}
  Summary:      {summary}
  Body:         {body}
---

Cast your vote now."""


_WEIGHT_RE = re.compile(
    r"WEIGHT\s*:\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))",
    re.IGNORECASE,
)
_RATIONALE_RE = re.compile(
    r"RATIONALE\s*:\s*(.+?)(?:\n\s*\n|\Z)", re.IGNORECASE | re.DOTALL
)
_ROSTER_SPLIT_RE = re.compile(r"[;,\n]+")

# Reasoning models (Qwen3, DeepSeek R1, GPT-OSS reasoning mode, ...) emit
# chain-of-thought wrapped in <think>...</think> tags BEFORE the actual
# answer. We strip those blocks before parsing so that: (a) a "0.7" the
# model mulls over during thinking can't false-match the WEIGHT regex,
# and (b) the rationale we store on the source chain is the model's
# final answer, not its internal monologue.
_THINK_BLOCK_RE = re.compile(r"<think\b[^>]*>.*?</think\s*>", re.IGNORECASE | re.DOTALL)

PROFILE_ENV = "FLOSS_VOTER_PROFILE"
ROSTER_ENV = "FLOSS_VOTER_ROSTER"
EXTRA_VOTERS_ENV = "FLOSS_EXTRA_VOTERS"
FLOWITH_API_KEY_ENV = "FLOWITH_API_KEY"
FLOWITH_CREDENTIALS_PATH_ENV = "FLOWITH_CREDENTIALS_PATH"
FLOWITH_API_URL = "https://edge.flowith.io/external/use/llm"
VOTER_REGISTRY_PATH = _THIS_DIR / "voter_registry.json"


def _strip_thinking(text: str) -> str:
    """Remove all <think>...</think> blocks (reasoning model chain-of-thought).

    Non-greedy, case-insensitive, spans newlines. An unclosed <think> block
    (caused by a max_tokens cutoff during the thinking phase) is left alone
    and will simply fail the WEIGHT regex downstream — which correctly
    surfaces as a degraded 0.0 vote rather than a silently wrong one.
    """
    return _THINK_BLOCK_RE.sub("", text).strip()


def _parse_weight(text: str) -> float:
    """Extract a WEIGHT float from model output, defaulting to 0.0 on parse failure."""
    m = _WEIGHT_RE.search(text)
    if not m:
        return 0.0
    try:
        w = float(m.group(1))
    except ValueError:
        return 0.0
    # Clamp into the closed interval [-CERTAINTY_LIMIT, CERTAINTY_LIMIT].
    # Models may naively output ±1.0 despite the instructions; we preserve
    # the direction of the signal rather than erroring.
    if w > CERTAINTY_LIMIT:
        return CERTAINTY_LIMIT
    if w < -CERTAINTY_LIMIT:
        return -CERTAINTY_LIMIT
    return w


def _parse_rationale(text: str) -> str:
    """Extract the RATIONALE field, falling back to a trimmed raw response slice."""
    m = _RATIONALE_RE.search(text)
    if not m:
        return text.strip()[:500]
    return m.group(1).strip()[:500]


def make_litellm_voter(
    name: str,
    model: str,
    *,
    max_tokens: int = 2000,
    temperature: float = 0.1,
) -> Voter:
    """Build a sync Voter that queries `model` via LiteLLM and returns a Vote.

    name:        voter identifier written into Vote.voter
                 (e.g. "cerebras-llama3.1-8b")
    model:       LiteLLM model string
                 (e.g. "cerebras/llama3.1-8b", "groq/qwen/qwen3-32b")
    max_tokens:  cap on response length. Default is 2000 to give reasoning
                 models (Qwen3, DeepSeek R1, GPT-OSS reasoning) room to
                 think AND emit the WEIGHT/RATIONALE output after thinking.
                 Non-reasoning models won't use most of this budget.
    temperature: low by default; consensus prefers determinism
    """

    def voter(claim: Claim) -> Vote:
        """Call LiteLLM for one claim and normalize the provider output into a Vote."""
        prompt = VOTER_PROMPT.format(
            proposer=claim.proposer,
            proposal_type=claim.proposal_type.value,
            blast_radius=claim.blast_radius.value,
            summary=claim.summary,
            body=claim.body,
        )
        try:
            from litellm import completion

            resp = completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            text = (resp.choices[0].message.content or "").strip()
        except Exception as exc:  # noqa: BLE001
            # Voter failures return a 0.0 neutral vote with the error as rationale
            # so the consensus gate can still tally — one broken voter doesn't
            # break the round.
            return Vote(
                voter=name,
                weight=0.0,
                rationale=f"[voter error] {type(exc).__name__}: {exc}"[:500],
            )

        # Strip <think> blocks BEFORE parsing so reasoning prose can't
        # false-match the WEIGHT regex and the on-chain rationale stays
        # clean (final answer, not internal monologue).
        cleaned = _strip_thinking(text)
        weight = _parse_weight(cleaned)
        rationale = _parse_rationale(cleaned)
        return Vote(voter=name, weight=weight, rationale=rationale)

    voter.__name__ = f"litellm_voter_{name}"
    return voter


def _flowith_credentials_path() -> Path:
    """Return the configured Flowith credentials path or the default fallback."""
    configured = os.environ.get(FLOWITH_CREDENTIALS_PATH_ENV, "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".flowith" / "credentials.json"


def _load_flowith_api_key() -> str:
    """Resolve the Flowith API key from env first, then from the credentials file."""
    env_key = os.environ.get(FLOWITH_API_KEY_ENV, "").strip()
    if env_key:
        return env_key

    path = _flowith_credentials_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(
            f"missing {FLOWITH_API_KEY_ENV} and Flowith credentials file {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in Flowith credentials file {path}") from exc

    api_key = str(payload.get("apiKey", "")).strip()
    if not api_key:
        raise ValueError(f"missing apiKey in Flowith credentials file {path}")
    return api_key


def _flowith_credential_state() -> tuple[bool, str]:
    """Return whether Flowith credentials are available plus a human-readable reason."""
    env_key = os.environ.get(FLOWITH_API_KEY_ENV, "").strip()
    if env_key:
        return True, f"credential found in {FLOWITH_API_KEY_ENV}"

    path = _flowith_credentials_path()
    if not path.exists():
        return False, f"missing {FLOWITH_API_KEY_ENV} or {path}"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, f"invalid JSON in Flowith credentials file {path}"

    api_key = str(payload.get("apiKey", "")).strip()
    if not api_key:
        return False, f"missing apiKey in Flowith credentials file {path}"
    return True, f"credential found in {path}"


def _parse_flowith_models(model: str) -> list[str]:
    """Parse a `flowith/...` model spec into the concrete model list Flowith expects."""
    prefix = "flowith/"
    if not model.strip().lower().startswith(prefix):
        raise ValueError(f"unsupported Flowith model spec {model!r}")
    raw = model.strip()[len(prefix) :]
    models = [item.strip() for item in raw.split("|") if item.strip()]
    if not models:
        raise ValueError("Flowith voter spec must include at least one model")
    return models


def _flowith_endpoint() -> tuple[str, str]:
    """Return the validated Flowith HTTPS host/path pair used for API requests."""
    parsed = urllib.parse.urlparse(FLOWITH_API_URL)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("FLOWITH_API_URL must be an https URL")
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return parsed.netloc, path


def make_flowith_voter(
    name: str,
    model: str,
    *,
    timeout_s: float = 30.0,
) -> Voter:
    """Build a sync Voter that queries Flowith's multi-model endpoint."""
    models = _parse_flowith_models(model)

    def voter(claim: Claim) -> Vote:
        """Call Flowith for one claim and normalize the provider output into a Vote."""
        prompt = VOTER_PROMPT.format(
            proposer=claim.proposer,
            proposal_type=claim.proposal_type.value,
            blast_radius=claim.blast_radius.value,
            summary=claim.summary,
            body=claim.body,
        )
        try:
            api_key = _load_flowith_api_key()
            host, path = _flowith_endpoint()
            request_body = json.dumps(
                {
                    "models": models,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "thinking": False,
                    "online": False,
                }
            ).encode("utf-8")
            request = urllib.request.Request(
                url=f"https://{host}{path}",
                data=request_body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "FLOSSI0ULLK-Consensus/0.1",
                    "Accept": "application/json",
                },
                method="POST",
            )
            context = ssl.create_default_context()
            with urllib.request.urlopen(
                request,
                timeout=timeout_s,
                context=context,
            ) as response:
                status = response.getcode()
                raw_response = response.read().decode("utf-8", "replace")
            if status >= 400:
                raise ValueError(f"Flowith HTTP {status}: {raw_response[:200]!r}")
            payload = json.loads(raw_response)
            text = payload["choices"][0]["message"]["content"].strip()
            if not text:
                raise ValueError("missing response content from Flowith")
        except Exception as exc:  # noqa: BLE001
            return Vote(
                voter=name,
                weight=0.0,
                rationale=f"[voter error] {type(exc).__name__}: {exc}"[:500],
            )

        cleaned = _strip_thinking(text)
        weight = _parse_weight(cleaned)
        rationale = _parse_rationale(cleaned)
        return Vote(voter=name, weight=weight, rationale=rationale)

    voter.__name__ = f"flowith_voter_{name}"
    return voter


# ----------------------------------------------------------------------------
# Default registry for the current free-tier inference stack.
#
# Diversity matters more than raw count: two Llama 3.1 8B endpoints gave us
# variance=0.000 on 2026-04-12 because they share training weights. This roster
# spans three model families (Meta Llama, OpenAI GPT-OSS, Alibaba Qwen) and
# three size classes (8B, 20B, 32B) so real disagreement is observable.
#
# - cerebras/llama3.1-8b        Cerebras WSE-3, Meta, production
# - openai/gpt-oss-20b          Groq LPU, OpenAI open-weight, production (1000 t/s)
# - qwen/qwen3-32b              Groq LPU, Alibaba Qwen 3, PREVIEW (may be dropped
#                               at short notice; voter error path handles that)
#
# Rate limits checked: 250K–300K TPM, 1K RPM on each — plenty of headroom for
# consensus rounds. Upgrade to 70B / 120B / Llama 4 once we want heavier signal.
# ----------------------------------------------------------------------------

_CREDENTIAL_ENV_BY_PREFIX: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("cerebras/", ("CEREBRAS_API_KEY",)),
    ("groq/", ("GROQ_API_KEY",)),
    ("mistral/", ("MISTRAL_API_KEY",)),
    ("gemini/", ("GOOGLE_API_KEY", "GEMINI_API_KEY")),
    ("openrouter/", ("OPENROUTER_API_KEY",)),
    ("xai/", ("XAI_API_KEY",)),
    ("openai/", ("OPENAI_API_KEY",)),
    ("anthropic/", ("ANTHROPIC_API_KEY",)),
)


@lru_cache(maxsize=1)
def _load_builtin_registry() -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    """Load and normalize the built-in voter registry aliases and profiles."""
    try:
        raw = json.loads(VOTER_REGISTRY_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Missing voter registry file: {VOTER_REGISTRY_PATH}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in voter registry {VOTER_REGISTRY_PATH}: {exc}"
        ) from exc

    aliases_raw = raw.get("aliases", {})
    profiles_raw = raw.get("profiles", {})
    if not isinstance(aliases_raw, dict) or not isinstance(profiles_raw, dict):
        raise RuntimeError(
            "Voter registry "
            f"{VOTER_REGISTRY_PATH} must contain object-valued aliases and profiles"
        )

    aliases: dict[str, str] = {}
    for name, target in aliases_raw.items():
        if not isinstance(name, str) or not isinstance(target, str):
            raise RuntimeError(
                f"Voter registry aliases must be string -> string: {name!r}"
            )
        aliases[name.strip().lower()] = target.strip().lower()

    profiles: dict[str, dict[str, str]] = {}
    for profile_name, roster in profiles_raw.items():
        if not isinstance(profile_name, str) or not isinstance(roster, dict):
            raise RuntimeError(
                "Voter registry profiles must map names to object rosters: "
                f"{profile_name!r}"
            )
        normalized_profile = profile_name.strip().lower()
        normalized_roster: dict[str, str] = {}
        for voter_name, model in roster.items():
            if not isinstance(voter_name, str) or not isinstance(model, str):
                raise RuntimeError(
                    "Voter registry roster entries must be string -> string: "
                    f"{profile_name!r}"
                )
            normalized_roster[voter_name.strip()] = model.strip()
        profiles[normalized_profile] = normalized_roster

    for alias_name, target_name in aliases.items():
        if target_name not in profiles:
            raise RuntimeError(
                f"Voter registry alias {alias_name!r} points to unknown profile "
                f"{target_name!r}"
            )

    if "balanced" not in profiles:
        raise RuntimeError(
            f"Voter registry {VOTER_REGISTRY_PATH} must define a 'balanced' profile"
        )

    return aliases, profiles


def _normalize_profile(profile: str | None) -> str:
    """Resolve the active profile name, falling back to the built-in default."""
    normalized = (profile or os.environ.get(PROFILE_ENV, "balanced")).strip().lower()
    if not normalized:
        return "balanced"
    aliases, _profiles = _load_builtin_registry()
    return aliases.get(normalized, normalized)


def _parse_voter_map(raw: str, *, source: str) -> dict[str, str]:
    """Parse `name=model` pairs separated by `;`, `,`, or newlines."""
    parsed: dict[str, str] = {}
    for item in _ROSTER_SPLIT_RE.split(raw):
        part = item.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(
                f"{source}: invalid voter spec {part!r}; expected name=model"
            )
        name, model = (chunk.strip() for chunk in part.split("=", 1))
        if not name or not model:
            raise ValueError(
                f"{source}: invalid voter spec {part!r}; name and model are required"
            )
        if name in parsed:
            raise ValueError(f"{source}: duplicate voter name {name!r}")
        parsed[name] = model
    return parsed


def _credential_state_for_model(model: str) -> tuple[bool, str]:
    """Report whether built-in credentials exist for the provider behind `model`."""
    lower = model.strip().lower()
    if lower.startswith("flowith/"):
        return _flowith_credential_state()
    for prefix, env_vars in _CREDENTIAL_ENV_BY_PREFIX:
        if lower.startswith(prefix):
            for env_var in env_vars:
                if os.environ.get(env_var):
                    return True, f"credential found in {env_var}"
            return False, f"missing {' or '.join(env_vars)}"
    return True, "no built-in credential gate for provider"


def resolve_default_voter_specs(
    profile: str | None = None,
    *,
    include_unavailable: bool = False,
) -> dict[str, str]:
    """Resolve the active roster from built-in profiles plus env overrides.

    Precedence:
      1. `FLOSS_VOTER_ROSTER` fully replaces the built-in profile
      2. `FLOSS_EXTRA_VOTERS` appends to the selected built-in profile
      3. `FLOSS_VOTER_PROFILE` selects the built-in profile (`balanced` default)

    When `include_unavailable=False`, voters whose provider keys are missing are
    filtered out up front instead of wasting a round on guaranteed error-votes.
    """
    normalized = _normalize_profile(profile)
    _aliases, builtin_profiles = _load_builtin_registry()
    try:
        resolved = dict(builtin_profiles[normalized])
    except KeyError as exc:
        allowed = ", ".join(sorted(builtin_profiles))
        raise ValueError(
            f"Unknown voter profile {normalized!r}. Expected one of: {allowed}"
        ) from exc

    roster_override = os.environ.get(ROSTER_ENV, "").strip()
    if roster_override:
        resolved = _parse_voter_map(roster_override, source=ROSTER_ENV)
    else:
        extra_voters = os.environ.get(EXTRA_VOTERS_ENV, "").strip()
        if extra_voters:
            resolved.update(_parse_voter_map(extra_voters, source=EXTRA_VOTERS_ENV))

    if include_unavailable:
        return resolved

    return {
        name: model
        for name, model in resolved.items()
        if _credential_state_for_model(model)[0]
    }


def describe_default_roster(profile: str | None = None) -> list[dict[str, str | bool]]:
    """Return the resolved roster plus enable/disable reasons for logging/UI."""
    enabled = resolve_default_voter_specs(profile=profile, include_unavailable=False)
    described: list[dict[str, str | bool]] = []
    for name, model in resolve_default_voter_specs(
        profile=profile, include_unavailable=True
    ).items():
        is_enabled, reason = _credential_state_for_model(model)
        described.append(
            {
                "name": name,
                "model": model,
                "enabled": name in enabled,
                "reason": reason if not is_enabled else "enabled",
            }
        )
    return described


def build_default_voters(profile: str | None = None) -> list[Voter]:
    """Build the active voter roster from env-aware profile resolution."""
    resolved = resolve_default_voter_specs(profile=profile, include_unavailable=False)
    if not resolved:
        active_profile = _normalize_profile(profile)
        raise RuntimeError(
            "No enabled voters were resolved for profile "
            f"{active_profile!r}. Load provider credentials or configure "
            f"{ROSTER_ENV}/{EXTRA_VOTERS_ENV}."
        )
    voters: list[Voter] = []
    for name, model in resolved.items():
        if model.strip().lower().startswith("flowith/"):
            voters.append(make_flowith_voter(name, model))
        else:
            voters.append(make_litellm_voter(name, model))
    return voters
