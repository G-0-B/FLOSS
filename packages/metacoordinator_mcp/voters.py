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
import sys
import urllib.parse
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

# Voter callables were originally 1-arg (Claim). PR38 review thread
# PRRT_kwDOPkAi3s6UUuKj adds a 2nd context arg so voters can see the
# validated provenance_packet metadata (digest, consent decision hash,
# nested non-packet evidence roots) that submit_claim already verified.
# Legacy 1-arg voters remain valid — GatewayTools._call_voter falls back
# via arity inspection when a caller doesn't accept the context arg.
Voter = Callable[..., Vote]

# VOTER_PROMPT v2 (WS2 meta-prompting sweep, 2026-07-03).
# v1 hid `evidence` and `truth_status` from voters, producing the measured
# rubber-stamp pathology (e.g. open-mistral-nemo: 748/760 chain votes at
# exactly +0.7 with boilerplate rationales; A/B on evals/claim_verification
# dev split: v1 = 4/20 bucket accuracy, v2 = 13/20 on the same model at
# temperature 0). Delta doc: docs/superpowers/plans/2026-07-fable5-sprint-
# ws2-prompt-delta.md. v1 preserved in git history.
VOTER_PROMPT = """You are a peer voter in a multi-agent consensus gate for the
FLOSSIØULLK project. Your vote gates whether a proposed change lands, so an
undeserved positive vote is as harmful as a wrong rejection. You are not here
to be agreeable; you are here to check.

Run this checklist BEFORE choosing a weight:
1. EVIDENCE: Is evidence non-empty? Every type must be one of
   spec | test | adr | url | commit | provenance_packet | file | log | activity |
   source_chain. A commit ref must look like hex. Evidence of only
   provenance_packet type (no non-packet root) is insufficient on its own.
2. RADIUS: Does the body's actual scope match the declared blast radius?
   (Local = one file/tool; Module = one package; System = cross-package or
   wire-format/shared-config; Substrate = integrity zomes, consensus semantics,
   identity/consent.) A wide change declared narrow is a serious defect.
3. TRUTH STATUS: Verified/Validated require test or commit evidence. A proposal
   that has not landed cannot be Validated. Honest Unverified/Specified is fine.
4. GOVERNED GATE: AdrChange/SpecChange/ConfigChange at System or Substrate
   radius additionally requires provenance_packet evidence AND a consent
   reference (in context). Missing either -> vote against until supplied.
5. OVERRIDE: Human override is FORBIDDEN at Substrate radius. Any claim
   requesting it gets strong opposition regardless of other merits.
6. INVARIANTS: Anything that bypasses, weakens, or gates off symbolic/integrity
   validation, or collapses voter diversity, is an invariant violation ->
   strong opposition. Logic validates; neural assists.
7. SCOPE: Vague, unbounded, or bundled-unrelated-actions claims are not votable
   as-is. Duplicates of already-decided claims (see context) should not be
   re-approved.

Calibration — be honest, not nice:
- Reserve weights above +0.8 for exceptional claims: bounded, reversible, with
  test or commit evidence you can name.
- A routine clean claim is +0.4 to +0.7, not +0.9.
- If ANY checklist item fails, your weight must not be positive; pick the
  magnitude by severity (procedural gap: -0.3 to -0.5; invariant violation,
  forbidden override, or radius gaming: -0.7 to -0.999).
- 0.0 means genuinely insufficient information — not politeness.
- Do NOT default to the same number on every claim. If your last several votes
  were identical, you are pattern-matching, not evaluating.

Your vote is a float WEIGHT in the closed interval [-0.999, 0.999].
Never use exactly +1.0 or -1.0 — the domain is open at the extremes because
absolute certainty is incompatible with the consensus model.

RATIONALE must name the specific checklist item(s) that decided your vote and
the exact field/value that triggered them (1-3 sentences). Generic praise
("well-reasoned", "aligns with goals") is a malformed rationale.

OUTPUT FORMAT — return exactly these two lines and nothing else:
WEIGHT: <float>
RATIONALE: <text>

---
CLAIM TO EVALUATE:
  Proposer:     {proposer}
  Type:         {proposal_type}
  Blast radius: {blast_radius}
  Truth status: {truth_status}
  Summary:      {summary}
  Body:         {body}
  Evidence:     {evidence}
  Context:      {context}
---

Cast your vote now."""


def render_voter_prompt(claim: "Claim", context: str = "(none)") -> str:
    """Render VOTER_PROMPT from a Claim, including evidence + truth status.

    v1 omitted evidence/truth_status entirely — voters were structurally unable
    to ground their votes. Single shared renderer so all voter backends stay
    in sync with the template's field set.
    """
    evidence = json.dumps(
        [entry.to_dict() for entry in claim.evidence],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return VOTER_PROMPT.format(
        proposer=claim.proposer,
        proposal_type=claim.proposal_type.value,
        blast_radius=claim.blast_radius.value,
        truth_status=claim.truth_status.value,
        summary=claim.summary,
        body=claim.body,
        evidence=evidence,
        context=context,
    )


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


# ---------------------------------------------------------------------------
# PERSONA SYSTEM PROMPTS — each persona shapes the underlying model's cognitive
# style so a single LLM can vote with several different "minds." The
# architectural value is *style* diversity on top of model-family diversity:
# different dispositions notice different things.
#
# LICENSE NOTE (2026-08-12). A prior version of the executability persona was
# adapted from oh-my-opencode v4.0.0's MOMUS_DEFAULT_PROMPT. That upstream is
# SUL-1.0 — source-available, not OSI-approved — and is incompatible with this
# project's AGPL-3.0-or-later grant (ADR-7). The prompt below is a CLEAN-ROOM
# REPLACEMENT: written from this repo's own consensus schema (analog weights,
# blast-radius thresholds, truth labels, evidence-ref types) rather than from
# the upstream text. No SUL-1.0 material remains in this file.
#
# CRITIC_PERSONA_SYSTEM below was original FLOSSI0ULLK text from the start —
# it encodes the UTN "Don't Force Machinery" constraint and was never derived
# from an external source. Only its registry NAME prefix was borrowed.
# ---------------------------------------------------------------------------

# PR38 invariant, verbatim: a persona may sharpen the shared checklist
# but never waive or narrow it. Prefixed onto every persona below.
_PERSONA_SHARED_GATE_SYSTEM = (
    "The shared seven-item checklist is mandatory for every consensus voter. "
    "Evaluate all seven checklist items in the user message before applying this "
    "persona's specialist lens. If ANY shared checklist item fails, your weight "
    "must not be positive. Only after every shared checklist item passes may "
    "persona-specific positive calibration apply. The persona may add stricter "
    "objections, but it may never waive or narrow the shared checklist."
)


EXECUTABILITY_REVIEWER_SYSTEM = (
    _PERSONA_SHARED_GATE_SYSTEM
    + """

You are the executability reviewer on a FLOSSI0ULLK consensus roster.
Every other voter is asking whether a Claim is *right*. You are asking something narrower and more mechanical, which is why you exist: **could a competent contributor act on this Claim without hitting a dead end?**

## Your one question

Not "is this the best approach?" — another voter covers that.
Not "is this architecturally sound?" — another voter covers that.
Yours: **is it actionable as written, and do the things it points at actually exist?**

## What you check

1. **Referenced artifacts resolve.** A Claim citing an ADR, spec, file, commit or test is only as good as those references. Treat an unresolvable reference as a real defect — it is the most common way a confident Claim turns out to be hollow.
2. **Evidence type matches evidence content.** `evidence_refs` carry a type: `spec`, `test`, `adr`, `url`, `commit`, `provenance_packet`, `file`, `log`, `activity`, `source_chain`. Prose asserting a test passed is not a `test` ref. At least one non-packet evidence root must exist somewhere in the chain.
3. **Negatives state their scope.** "Not found" is only as strong as the search behind it. A Claim asserting absence without saying what was searched is unverified, not verified.
4. **Truth labels are earned.** `Verified` means retrieved this session from a primary source, with the scope named. `Specified` means designed but not observed. Watch for `Verified` doing work that only `Specified` supports — that is the failure mode this project has been bitten by most often.
5. **A first step exists.** Someone picking this up should know what to do on day one.

## What you deliberately do NOT check

This narrows your *specialist lens only* — never the shared checklist above,
which you evaluate in full first, on every claim.

Beyond that checklist, leave these to other voters: optimality, elegance, style, hypothetical edge cases, performance, or whether a different design would be better. Those belong to other voters, and duplicating them collapses the roster's diversity into a single opinion. Staying in your lane is the point.

## Disposition

Lean toward approval. Ambiguity is normal and a Claim that is 80% specified is usually actionable. Reserve negative weight for defects that would genuinely stop work: a reference that does not resolve, a truth label the evidence does not support, or an internal contradiction. Name at most three; if there are more, the first three are what matters.

## Vote format

Weights are analog floats in the CLOSED interval [-0.999, +0.999]. Never ±1.0 — certainty is asymptotic here by design.

Calibrate against the blast radius the Claim carries, because approval thresholds differ: Local 0.30, Module 0.50, System 0.60, Substrate 0.85. A +0.5 is decisive for a Local change and insufficient for a Substrate one.

- References resolve, evidence types fit, actionable → **+0.55 to +0.75**
- Actionable with minor gaps you can name → **+0.25 to +0.45**
- Too underspecified to judge, or you could not check the references → **near 0.0**, and say which
- A blocking defect: dead reference, unsupported `Verified`, contradiction → **-0.6 to -0.9**

You are one input to a router, not a decision-maker. The gateway tallies; it does not obey you. If you disagree with the rest of the roster, say so plainly and let the variance stand — preserved disagreement above the polarization threshold surfaces a CONFLICT for a human, which is a better outcome than false agreement.

Emit the WEIGHT/RATIONALE format the user prompt specifies. Rationale is 1-3 sentences naming either what you checked that gave you confidence, or the specific defect and where it is."""
)


def _model_completion(
    model: str,
    messages: list[dict],
    *,
    max_tokens: int = 2000,
    temperature: float = 0.1,
) -> str:
    """Call the configured model backend and return the response text.

    Routes to OmniRoute (httpx) when FLOSS_MODEL_BACKEND=omniroute,
    otherwise falls back to litellm. Keeps all parsing logic in the caller.
    """
    if os.environ.get("FLOSS_MODEL_BACKEND", "litellm") == "omniroute":
        from packages.omniroute_client import completion as _omni

        return _omni(model, messages, max_tokens=max_tokens, temperature=temperature)
    from litellm import completion

    resp = completion(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return (resp.choices[0].message.content or "").strip()


def make_executability_voter(
    name: str,
    model: str,
    *,
    max_tokens: int = 3000,
    temperature: float = 0.1,
) -> Voter:
    """Build an executability-reviewer voter — reference and actionability check.

    Narrower than the other voters by design: it asks whether a Claim can be
    acted on and whether the artifacts it cites resolve, and explicitly leaves
    optimality and architecture to the rest of the roster. That lane discipline
    is what makes it add diversity instead of a second general opinion.

    The model gets EXECUTABILITY_REVIEWER_SYSTEM as a SYSTEM message and the
    standard VOTER_PROMPT as USER message, then parses WEIGHT/RATIONALE output
    the same way other voters do.

    Renamed 2026-08-12 from `make_omo_momus_voter`. The old name is kept as a
    module-level alias for callers and registry keys that still use it.

    Architectural value: adds cognitive-style diversity. Momus notices things
    a vanilla "evaluate this claim" voter does not, because it specifically
    looks for unresolved references and dead-on-arrival executability gaps
    rather than generally vibing on the proposal.
    """

    def voter(claim: Claim, context: str = "(none)") -> Vote:
        """Call the underlying model with Momus persona + standard voter prompt."""
        user_prompt = render_voter_prompt(claim, context)
        try:
            text = _model_completion(
                model,
                [
                    {"role": "system", "content": EXECUTABILITY_REVIEWER_SYSTEM},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
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

    voter.__name__ = f"omo_momus_voter_{name}"
    return voter


CRITIC_PERSONA_SYSTEM = (
    _PERSONA_SHARED_GATE_SYSTEM
    + """

You are the anti-sycophancy critic, a practical plan reviewer for the FLOSSI0ULLK project. Your goal is to review the supervisor's proposed claim or plan to ensure it adheres to the "Don't Force Machinery" (UTN) constraint.

## Your Purpose
You exist to answer ONE question: "Is this plan sycophantic or forcing machinery?"

You ARE here to:
- Review the proposer's plan critically.
- Flag if it is just agreeing with the user without critical thought (sycophancy).
- Reject if it acts without proper readiness (forcing machinery).

## Translating to consensus vote
Map your verdict into the WEIGHT format the consensus gate expects:
- No sycophancy, thoughtful plan, ready to execute → WEIGHT around +0.6 to +0.8
- Minor concerns but proceedable → WEIGHT around +0.2
- Genuine blockers (sycophantic or forces machinery) → WEIGHT around -0.7 to -0.9
- Insufficient information to judge → WEIGHT around 0.0

Output the WEIGHT/RATIONALE format the user prompt asks for. Your rationale should be 1-3 sentences naming either: (a) what you verified that gave you confidence, or (b) the specific sycophancy/readiness blockers you found."""
)


# Back-compat alias. `make_omo_momus_voter` was the name until 2026-08-12, when
# the persona was rewritten clean-room to remove SUL-1.0-derived text (ADR-7).
# Kept so external callers and any pinned roster config keep working.
make_omo_momus_voter = make_executability_voter


def make_omo_critic_voter(
    name: str,
    model: str,
    *,
    max_tokens: int = 3000,
    temperature: float = 0.1,
) -> Voter:
    """Build a Critic-style consensus voter — anti-sycophancy and readiness checker.

    Wraps a chosen model with the Yumeichan critic philosophy (anti-sycophancy,
    don't force machinery). The model gets Critic as a SYSTEM message and
    the standard VOTER_PROMPT as USER message.
    """

    def voter(claim: Claim, context: str = "(none)") -> Vote:
        """Call the underlying model with Critic persona + standard voter prompt."""
        user_prompt = render_voter_prompt(claim, context)
        try:
            text = _model_completion(
                model,
                [
                    {"role": "system", "content": CRITIC_PERSONA_SYSTEM},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
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

    voter.__name__ = f"omo_critic_voter_{name}"
    return voter


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

    def voter(claim: Claim, context: str = "(none)") -> Vote:
        """Call the model backend for one claim and normalize the output into a Vote."""
        prompt = render_voter_prompt(claim, context)
        try:
            text = _model_completion(
                model,
                [{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
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

    def voter(claim: Claim, context: str = "(none)") -> Vote:
        """Call Flowith for one claim and normalize the provider output into a Vote."""
        prompt = render_voter_prompt(claim, context)
        try:
            import requests

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
            )
            response = requests.post(
                f"https://{host}{path}",
                data=request_body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "FLOSSI0ULLK-Consensus/0.1",
                    "Accept": "application/json",
                },
                timeout=timeout_s,
            )
            raw_response = response.text
            if response.status_code >= 400:
                raise ValueError(
                    f"Flowith HTTP {response.status_code}: {raw_response[:200]!r}"
                )
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
# - qwen/qwen3.6-27b            Groq LPU, Alibaba Qwen 3.6, production
#                               (replaced qwen3-32b which was decommissioned 2026-07)
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
    # Added 2026-08-12 alongside the probed voter-registry repair. Any prefix
    # absent from this table falls through to "no built-in credential gate for
    # provider" -- i.e. reported as AVAILABLE unconditionally -- so a voter on
    # an ungated provider passes the `include_unavailable=False` filter and is
    # enrolled in a live poll that can only fail at request time. That is the
    # same failure shape the removed flowith voters had (credential file
    # present, endpoint gone), and it is why every provider newly referenced by
    # voter_registry.json must be gated here at the same time.
    ("huggingface/", ("HUGGINGFACE_API_KEY", "HF_TOKEN")),
    ("nvidia/", ("NVIDIA_NIM_API_KEY", "NVIDIA_API_KEY")),
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


# Per-voter wall clock. Named here rather than left to the OmniRoute client's
# default so the round budget below is derived from the same number the call
# actually uses.
VOTER_CALL_TIMEOUT_SECONDS = 60.0

# A consensus round polls voters SEQUENTIALLY (tools._collect_new_votes), so the
# round costs roster size times the per-voter timeout -- four default voters is
# 240 seconds against MCP projections that capped the tool at 120. A valid round
# therefore failed at the client while the server kept polling and could still
# write a decision afterwards, which is the worst of both: no answer, and a
# durable record the caller never saw.
#
# Summed from the REGISTRY, for the same reason the ensemble's
# WORST_CASE_RUN_SECONDS is summed from its own constants: a config that has to
# clear a budget must read the budget.
#
# The first version of this hardcoded four, which is `balanced`. The registry
# also exposes diverse (6), diverse-plus (8) and diverse-max (12), all
# selectable -- so a valid diverse-max round costs 720 seconds against a
# projection derived from 4, recreating the exact failure this budget exists to
# prevent. Typing a number instead of reading the source of truth is what the
# comment above was already warning about.


# Everything a round does BESIDES calling voters: building prompts, validating
# and tallying votes, appending to the source chain, serialising the response.
# The projections were set equal to the call budget, so a 12-voter round that
# used its full per-voter time left zero seconds for any of it and the client
# could time out while the server was still committing the decision.
ROUND_OVERHEAD_SECONDS = 60.0


def largest_selectable_roster() -> int:
    """Voter count of the biggest profile the registry offers."""

    try:
        _aliases, profiles = _load_builtin_registry()
    except Exception:  # noqa: BLE001 -- an unreadable registry must not crash callers
        return 0
    sizes = [len(spec) for spec in profiles.values() if isinstance(spec, dict)]
    return max(sizes) if sizes else 0


def worst_case_round_seconds() -> int:
    """Wall clock a full round can legitimately take.

    Voters are polled SEQUENTIALLY (tools._collect_new_votes), so the round
    costs roster size times the per-voter timeout. A client timeout below this
    fails a round that is behaving correctly, and the server keeps polling and
    may still write a decision the caller never sees.
    """

    return int(
        largest_selectable_roster() * VOTER_CALL_TIMEOUT_SECONDS
        + ROUND_OVERHEAD_SECONDS
    )


def roster_exceeds_projected_budget(resolved: dict[str, str]) -> str | None:
    """Warn when a CUSTOM roster is larger than any projection could cover.

    FLOSS_VOTER_ROSTER is unbounded, so no static projection can promise to
    cover it. Saying so is the honest version of a budget: the registry
    profiles are covered, and anything beyond them is named rather than
    silently over-running the client.
    """

    largest = largest_selectable_roster()
    if largest and len(resolved) > largest:
        return (
            f"roster of {len(resolved)} voters exceeds the largest registry "
            f"profile ({largest}); a sequential round can take "
            f"{int(len(resolved) * VOTER_CALL_TIMEOUT_SECONDS)}s, beyond the "
            f"{worst_case_round_seconds()}s the MCP timeouts are projected for"
        )
    return None


MIN_INDEPENDENT_SURFACES = 3
MIN_INDEPENDENT_FAMILIES = 4
ALLOW_DEGRADED_ENV = "FLOSS_ALLOW_DEGRADED_ROSTER"

# Profiles that are intentionally narrow. Mirrors EXEMPT_PROFILES in
# tests/test_voter_independence.py, which enforces the same rule against the
# registry FILE. This one enforces it against the roster that actually votes.
DEGRADED_OK_PROFILES = frozenset({"fast", "mistral", "local"})


def _derive_surface(model: str) -> str:
    """Provider surface for a model the probe index has never seen.

    Every model id here is a litellm route, so the text before the first `/` is
    the provider: `groq/openai/gpt-oss-120b` -> `groq`. That is enough to judge
    the surface half of the independence rule without the registry, which is
    what makes a custom `FLOSS_VOTER_ROSTER` judgeable at all.
    """
    return model.strip().lower().split("/", 1)[0] or model.strip().lower()


def _model_index() -> dict[str, dict[str, str]]:
    """Model id -> {family, surface} from the registry's probe record."""
    try:
        raw = json.loads(VOTER_REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    index = (raw.get("_probe") or {}).get("verified_working") or {}
    return {k: v for k, v in index.items() if isinstance(v, dict)}


def roster_independence_problem(profile: str, resolved: dict[str, str]) -> str | None:
    """Enforce the registry's independence rule on the roster that will vote.

    The registry states the rule and a test checks the file, but the file is not
    what votes. `resolve_default_voter_specs(include_unavailable=False)` drops
    voters whose credentials are missing, so a compliant four-surface profile can
    arrive here as one voter on one surface and still poll normally, returning a
    confident tally nobody flags.

    That is not hypothetical: `balanced` degraded to two voters BOTH on groq
    after cerebras died, voted, and nothing detected it -- the incident recorded
    in the registry's own `independence_rule` note.

    Refusing is the honest failure. A poll that cannot meet its own independence
    bar has not produced consensus, and reporting one is worse than reporting
    nothing. Set FLOSS_ALLOW_DEGRADED_ROSTER=1 to proceed deliberately.

    Returns the reason as a string, or None if the roster clears the bar.
    `assert_roster_is_independent` raises on it; the reasoning ensemble uses the
    same answer to DEGRADE a run rather than abort it, because a poll whose
    voters died mid-run still has responses worth returning verbatim. Two
    callers, two reactions, one definition of independence.
    """
    oversized = roster_exceeds_projected_budget(resolved)
    if oversized:
        print(f"[voters] WARNING: {oversized}", file=sys.stderr)
    if profile in DEGRADED_OK_PROFILES:
        return None
    if os.environ.get(ALLOW_DEGRADED_ENV, "").strip().lower() in {"1", "true", "yes"}:
        return None

    index = _model_index()
    models = list(resolved.values())

    # Models the probe index has never seen are NOT dropped from the accounting.
    # Dropping them meant a four-provider custom FLOSS_VOTER_ROSTER counted zero
    # surfaces and zero families and was refused outright, so the documented
    # override only ever worked with the registry's own hardcoded model ids.
    unclassified = sorted({model for model in models if model not in index})

    surfaces = {
        index[model]["surface"] if model in index else _derive_surface(model)
        for model in models
    }
    # Family is a claim about the model's lineage and cannot be parsed out of an
    # id, so an unclassified model counts as its own family and is named as
    # unverified. That is weaker than a probed family -- two ids could be the
    # same model behind two vendors -- which is exactly why the warning below
    # exists and why the refusal message lists them.
    families = {index[model]["family"] for model in models if model in index}
    families |= {f"unverified:{model}" for model in unclassified}

    if unclassified:
        print(
            f"[voters] independence check: {len(unclassified)} model(s) absent "
            f"from the registry probe index, counted as distinct unverified "
            f"families: {', '.join(unclassified)}. Probe them into "
            f"{VOTER_REGISTRY_PATH.name} to have their real family counted.",
            file=sys.stderr,
        )

    if (
        len(surfaces) >= MIN_INDEPENDENT_SURFACES
        and len(families) >= MIN_INDEPENDENT_FAMILIES
    ):
        return None

    return (
        f"Profile {profile!r} resolved to a roster below its own independence "
        f"rule: {len(surfaces)} provider surface(s) {sorted(surfaces)} and "
        f"{len(families)} model family/families {sorted(families)}, against a "
        f"bar of >={MIN_INDEPENDENT_SURFACES} surfaces and "
        f">={MIN_INDEPENDENT_FAMILIES} families. Voters resolved: "
        f"{sorted(resolved)}. Models absent from the probe index, counted as "
        f"unverified families: {unclassified or 'none'}. "
        f"Load the missing provider credentials, choose a "
        f"wider profile, or set {ALLOW_DEGRADED_ENV}=1 to poll anyway and "
        "accept that the result is not independent consensus."
    )


def assert_roster_is_independent(profile: str, resolved: dict[str, str]) -> None:
    """Raise if the roster that will vote is below the independence bar."""

    problem = roster_independence_problem(profile, resolved)
    if problem is not None:
        raise RuntimeError(problem)


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
    assert_roster_is_independent(_normalize_profile(profile), resolved)
    voters: list[Voter] = []
    for name, model in resolved.items():
        lower_name = name.strip().lower()
        lower_model = model.strip().lower()
        # Route by voter NAME prefix (omo agents inject persona via system
        # message; the model is just the substrate). Then by model prefix
        # (flowith) for non-omo voters. Default to standard litellm.
        # `exec-review-` is the current prefix; `omo-momus-` is the pre-2026-08-12
        # name, kept so existing rosters and env overrides keep resolving.
        if lower_name.startswith(("exec-review-", "omo-momus-")):
            voters.append(make_executability_voter(name, model))
        elif lower_name.startswith("omo-critic-"):
            voters.append(make_omo_critic_voter(name, model))
        elif lower_model.startswith("flowith/"):
            voters.append(make_flowith_voter(name, model))
        else:
            voters.append(make_litellm_voter(name, model))
    return voters
