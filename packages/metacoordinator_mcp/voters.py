"""
LiteLLM voter adapters for the FLOSSIØULLK consensus gate.

Each voter is a sync callable `Claim -> Vote` that calls out to a specific model
via LiteLLM, parses the response, and returns a Vote with a weight in
[-CERTAINTY_LIMIT, CERTAINTY_LIMIT] plus a rationale.

This is the bridge that turns "we can call Groq/Cerebras" into "Groq and
Cerebras are peers in the consensus gate." Every voter produced here plugs into
`consensus_gate.decide()` with no special-casing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Callable

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from litellm import completion

from packages.orchestrator.claim_schema import CERTAINTY_LIMIT, Claim, Vote

Voter = Callable[[Claim], Vote]

VOTER_PROMPT = """You are a peer voter in a multi-agent consensus gate for the FLOSSIØULLK project.

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


_WEIGHT_RE = re.compile(r"WEIGHT\s*:\s*([+-]?\d+(?:\.\d+)?)", re.IGNORECASE)
_RATIONALE_RE = re.compile(r"RATIONALE\s*:\s*(.+?)(?:\n\s*\n|\Z)", re.IGNORECASE | re.DOTALL)

# Reasoning models (Qwen3, DeepSeek R1, GPT-OSS reasoning mode, ...) emit
# chain-of-thought wrapped in <think>...</think> tags BEFORE the actual
# answer. We strip those blocks before parsing so that: (a) a "0.7" the
# model mulls over during thinking can't false-match the WEIGHT regex,
# and (b) the rationale we store on the source chain is the model's
# final answer, not its internal monologue.
_THINK_BLOCK_RE = re.compile(r"<think\b[^>]*>.*?</think\s*>", re.IGNORECASE | re.DOTALL)


def _strip_thinking(text: str) -> str:
    """Remove all <think>...</think> blocks (reasoning model chain-of-thought).

    Non-greedy, case-insensitive, spans newlines. An unclosed <think> block
    (caused by a max_tokens cutoff during the thinking phase) is left alone
    and will simply fail the WEIGHT regex downstream — which correctly
    surfaces as a degraded 0.0 vote rather than a silently wrong one.
    """
    return _THINK_BLOCK_RE.sub("", text).strip()


def _parse_weight(text: str) -> float:
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

    name:        voter identifier written into Vote.voter (e.g. "cerebras-llama3.1-8b")
    model:       LiteLLM model string (e.g. "cerebras/llama3.1-8b", "groq/qwen/qwen3-32b")
    max_tokens:  cap on response length. Default is 2000 to give reasoning
                 models (Qwen3, DeepSeek R1, GPT-OSS reasoning) room to
                 think AND emit the WEIGHT/RATIONALE output after thinking.
                 Non-reasoning models won't use most of this budget.
    temperature: low by default; consensus prefers determinism
    """

    def voter(claim: Claim) -> Vote:
        prompt = VOTER_PROMPT.format(
            proposer=claim.proposer,
            proposal_type=claim.proposal_type.value,
            blast_radius=claim.blast_radius.value,
            summary=claim.summary,
            body=claim.body,
        )
        try:
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

DEFAULT_VOTERS: dict[str, str] = {
    "cerebras-llama3.1-8b": "cerebras/llama3.1-8b",
    "groq-gpt-oss-20b":     "groq/openai/gpt-oss-20b",
    "groq-qwen3-32b":       "groq/qwen/qwen3-32b",
}


def build_default_voters() -> list[Voter]:
    """Build the default voter roster from DEFAULT_VOTERS. Requires env keys loaded."""
    return [make_litellm_voter(name, model) for name, model in DEFAULT_VOTERS.items()]
