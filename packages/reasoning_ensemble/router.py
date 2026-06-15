"""
Reasoning-Ensemble Router — v0.1 prototype.

=========================================================================
WHAT THIS IS
=========================================================================
Local-model prompt classifier that decides whether each substantive
reasoning step needs Pass-Through / Single-Strong / Ensemble routing.
The Router is the cheap front gate of the Inline Reasoning Ensemble; it
runs <10s per call on a local Ollama model and produces a structured
decision the caller acts on.

=========================================================================
WHY THIS EXISTS
=========================================================================
1. MDASH (Microsoft 2026-05-12) empirically proved harness-around-models
   beats any single model at production scale (88.45% CyberGym). See
   `docs/research/2026-05-16-mdash-cfis-architectural-transfer.md`.
2. CFIS v0.3 (canonical at `docs/architecture/CFIS_v0.3.md`) treats
   disagreement-across-frames as positive information, not noise. The
   Router is the gate that decides when to invoke that disagreement-as-
   signal mechanism.
3. The user's "every chat = debate" instinct was correct in spirit but
   wrong literally (would 10-50× slow interactive work for marginal
   gain). Selective routing via local classifier is the defensible
   version — see `docs/research/2026-05-17-inline-reasoning-ensemble.md`
   §10 honest pushback.
4. Token-budget pressure on cloud voters (per
   `docs/specs/heartbeat-runtime-budget.spec.md`) makes local-first
   routing the right default for routine reasoning.

=========================================================================
HOW IT WORKS (high level)
=========================================================================
1. Receive prompt
2. (Optional / Upgrade A) Embed prompt via mxbai-embed-large; check
   cosine similarity against last N activity-log entries; if similar
   to a past Tier-4 divergence above threshold, force `ensemble` mode
3. Otherwise: invoke local Router model (default phi4-mini via Ollama
   at 127.0.0.1:11434) with structured JSON-format system prompt
4. Parse mode + reason + confidence from JSON response
5. Conservative fallback to `single_strong` on any failure
6. Append decision (with prompt_hash + embedding) to activity log
   for future similarity-bias lookups + frame-cousin detection

=========================================================================
SPECS, ADRS, AND RELATED RESEARCH (the WHY-it-works-this-way chain)
=========================================================================
- Architecture proposal:
  `docs/research/2026-05-17-inline-reasoning-ensemble.md` (v0.2 with §12
  external-review upgrades from Multi-Stream LLMs + Multi-Model
  Consensus Reasoning Engine papers)
- Empirical validation:
  `docs/research/2026-05-16-mdash-cfis-architectural-transfer.md`
- Epistemic substrate:
  `docs/architecture/CFIS_v0.3.md` (4-tier authority, catuskoti,
  LSM-Override — the Router implements `[auth:structural]` reasoning
  with explicit refusal handoff to Synthesizer for ensemble work)
- Decision-grade peer:
  `docs/adr/ADR-MCP-ORCHESTRATOR.md` (ADR-10, the consensus gateway
  is decision-grade; this Router is reasoning-grade — different
  retention and stakes)
- Consent enforcement (substrate-class peer):
  `docs/adr/ADR-12-consent-gate-protocol.md` +
  `docs/specs/consent-payload.spec.md` (the Router itself is a
  governed pattern at the bind level; consent applies)
- Runtime operator guide:
  `docs/architecture/RUNTIME_SURFACES.md` — emergency controls,
  cost map, override env vars, SDD discipline
- Metaharness unification:
  `docs/research/2026-05-18-metaharness-unification.md` (the Router
  emits Actions via the unified activity-log schema)
- Token-budget discipline:
  `docs/specs/heartbeat-runtime-budget.spec.md` (cloud voters opt-in
  only; default routing is local-first)
- Shared skill surface:
  `FLOSS/skill-corpus/reasoning-ensemble/SKILL.md` (canonical skill;
  materialized to Codex/Claude/Gemini/OpenCode views)
- MCP wrapper:
  `FLOSS/packages/reasoning_ensemble/mcp_server.py` (exposes
  `route_prompt` as a first-class MCP tool — see that file for
  registration)

=========================================================================

Given a prompt + recent activity context, classify the prompt into one
of:

    pass_through    Trivial lookup / file read / format conversion / recall.
                    Single cheap call, no debate.
    single_strong   Standard reasoning, single-file edits, routine synthesis.
                    Single capable model. Current default behavior.
    ensemble        Substantive reasoning, multi-file refactor, architectural
                    decision, ADR-class moves, anything with rollback cost.
                    Parallel calls to ≥3 diverse voters + cluster-based
                    Tier-1/2/4 synthesis.

The Router itself is a small local model (default: gemma3:12b-it-qat via
Ollama) acting as a classifier, NOT a reasoner. Target classification latency
~2-5s warm (after first cold-start of ~60s).

v0.2 upgrades from external Perplexity review (§12 of the proposal doc):

  - Upgrade A: activity-log-similarity bias. If a past Tier-4 divergence
    exists on a semantically-adjacent prompt (cosine > 0.7 to last ~10
    logged), force `ensemble` even if the standalone classifier says
    `single_strong`. Adjacent disagreement predicts future disagreement.
    Uses mxbai-embed-large via Ollama for embeddings.

  - Upgrade D: anti-sycophancy coherence-threshold guard (lives in the
    ensemble synthesizer, not the Router — noted here for cross-ref).

Plane A discipline:
  - Writes only to `.agent-surface/reasoning/activity.jsonl`
  - Does not touch canonical surfaces
  - Returns a structured decision; the caller (Claude session / MCP tool /
    skill) is responsible for actually invoking the chosen mode

Usage:
    # CLI smoke test
    python FLOSS/packages/reasoning_ensemble/router.py --test

    # Classify a single prompt
    python FLOSS/packages/reasoning_ensemble/router.py "Refactor the auth module to use OAuth2"

    # Force a mode (for testing or user override via --debate flag)
    python FLOSS/packages/reasoning_ensemble/router.py --force ensemble "List files"

    # As a library
    from FLOSS.packages.reasoning_ensemble.router import classify
    decision = classify("Refactor the auth module to use OAuth2")

Exit codes:
    0  classification produced + logged
    1  Ollama unreachable
    2  classifier model unavailable
    3  malformed model response (no fallback usable)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = REPO_ROOT.parent
ACTIVITY_LOG = WORKSPACE_ROOT / ".agent-surface" / "reasoning" / "activity.jsonl"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.activity_log import Action, append_action  # noqa: E402

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")  # 127.0.0.1 not localhost — Python urllib on Windows tries IPv6 first and Ollama is IPv4-only
ROUTER_MODEL = os.environ.get("FLOSS_ROUTER_MODEL", "phi4-mini:latest")  # 2.5GB, fits fully on 16GB VRAM alongside mxbai-embed-large; ~10s warm vs gemma3:12b's 40-50s. Equivalent classification accuracy on calibration sample. Set FLOSS_ROUTER_MODEL=gemma3:12b-it-qat to revert.
EMBED_MODEL = os.environ.get("FLOSS_EMBED_MODEL", "mxbai-embed-large")

# Upgrade A: activity-log-similarity bias.
# Scan the last N logged prompts; if any has a Tier-4 tag AND cosine
# similarity > THRESHOLD to the incoming prompt, force ensemble mode.
ACTIVITY_LOOKBACK = 10
TIER4_SIMILARITY_THRESHOLD = 0.70

# Latency budgets. Cold-start of either model loading into VRAM can take
# 30-60s the first time; subsequent calls reuse the resident model and finish
# in 1-5s. Budgets generous enough to cover cold-start; in steady state the
# real latencies will be far below these ceilings.
ROUTER_TIMEOUT_SECONDS = 120
EMBED_TIMEOUT_SECONDS = 90

ROUTER_SYSTEM_PROMPT = """\
You are the FLOSSI0ULLK Reasoning Ensemble Router. Your job is to classify
an incoming prompt into one of three modes for downstream routing.

MODES:
  - pass_through: Trivial lookup, file read, directory listing, format
    conversion, simple recall, status check, acknowledgment. Anything that
    has no reasoning content to debate. Examples: "Read line 47 of foo.py",
    "Reformat this YAML", "Sum these numbers", "What's the current time?"

  - single_strong: Standard reasoning, single-file code edits, routine
    synthesis, code explanation, memory recall with light reasoning. Most
    actual work falls here. Examples: "Explain what this function does",
    "Write a test for this method", "Fix the bug in line 32".

  - ensemble: Substantive reasoning, architectural decisions, multi-file
    refactors, design proposals, ADR-class moves, anything that would be a
    Claim if it landed in the consensus gateway. Anything where being wrong
    has rollback cost. Examples: "Refactor the auth module to OAuth2 across
    5 files", "Design the schema for the new event-sourcing layer",
    "Should we switch from REST to GraphQL?"

GUIDANCE:
  - Default to single_strong on ambiguous cases. The error budget is
    skewed toward over-routing rather than under-routing, BUT do not
    over-classify trivial reads as substantive.
  - "I'm not sure" is NOT a valid response. Pick one mode with reasoning.
  - Multi-file or cross-system implications → ensemble.
  - Anything tagged `--debate` or "let's debate this" by user → ensemble.

OUTPUT FORMAT — JSON ONLY, no prose preamble:
{
  "mode": "pass_through" | "single_strong" | "ensemble",
  "reason": "<one-sentence justification under 200 chars>",
  "confidence": <float 0.0-1.0>
}
"""


@dataclass
class RouterDecision:
    """The classification result + provenance for the activity log."""
    mode: str
    reason: str
    confidence: float
    prompt_hash: str
    model: str
    embed_model: str
    timestamp: str
    duration_seconds: float
    bias_applied: Optional[str] = None  # None, "tier4_similarity", "force_flag"
    similar_prior_prompt_hash: Optional[str] = None
    similar_prior_similarity: Optional[float] = None
    raw_model_output: Optional[str] = None


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def _ollama_request(path: str, payload: dict, timeout: int) -> dict:
    """POST to Ollama HTTP API. Returns parsed JSON. Raises on error."""
    url = f"{OLLAMA_BASE_URL.rstrip('/')}{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ollama_embed(text: str) -> list[float]:
    """Return the mxbai-embed-large embedding of `text` (1024-d vector)."""
    response = _ollama_request("/api/embeddings",
                               {"model": EMBED_MODEL, "prompt": text},
                               timeout=EMBED_TIMEOUT_SECONDS)
    embedding = response.get("embedding", [])
    if not embedding:
        raise RuntimeError(f"Empty embedding from {EMBED_MODEL}")
    return embedding


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two equal-dimension vectors. Returns [-1, 1]."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _read_activity_tail(n_lines: int = ACTIVITY_LOOKBACK) -> list[dict]:
    """Read the last N entries from the activity log. Empty list on no log."""
    if not ACTIVITY_LOG.exists():
        return []
    try:
        lines = ACTIVITY_LOG.read_text(encoding="utf-8").strip().splitlines()
    except OSError:
        return []
    out: list[dict] = []
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(out) >= n_lines:
            break
    return out


def check_tier4_similarity_bias(prompt_embedding: list[float]) -> tuple[Optional[str], Optional[float]]:
    """Upgrade A: If a recent activity-log entry has a Tier-4 tag and the
    incoming prompt's embedding is similar to that entry's embedding above
    threshold, return (prior_prompt_hash, similarity_score) to trigger a
    forced ensemble bias. Otherwise return (None, None).
    """
    recent = _read_activity_tail(ACTIVITY_LOOKBACK)
    best_hash: Optional[str] = None
    best_sim: float = 0.0
    for entry in recent:
        if entry.get("tier_classification") != "tier4":
            continue
        prior_embed = entry.get("prompt_embedding")
        if not prior_embed:
            continue
        sim = cosine_similarity(prompt_embedding, prior_embed)
        if sim > best_sim:
            best_sim = sim
            best_hash = entry.get("prompt_hash")
    if best_sim >= TIER4_SIMILARITY_THRESHOLD and best_hash:
        return best_hash, best_sim
    return None, None


def _parse_router_output(raw: str) -> dict:
    """Extract the JSON object from the Router model's reply. Permissive —
    Ollama sometimes wraps in code fences, sometimes streams whitespace."""
    raw = raw.strip()
    # Strip code fences if present
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    # Find first { and last } for resilience against leading/trailing prose
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"No JSON object found in router output: {raw[:200]}")
    return json.loads(raw[start:end + 1])


def invoke_router(prompt: str) -> tuple[dict, float, str]:
    """Call the local Router model. Returns (parsed_decision, duration_s, raw_output)."""
    full_prompt = f"{ROUTER_SYSTEM_PROMPT}\n\nPROMPT TO CLASSIFY:\n{prompt}\n\nJSON OUTPUT:"
    started = time.perf_counter()
    response = _ollama_request("/api/generate", {
        "model": ROUTER_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "format": "json",  # request structured JSON output
        "options": {"temperature": 0.1, "num_predict": 256},
    }, timeout=ROUTER_TIMEOUT_SECONDS)
    duration = time.perf_counter() - started
    raw = response.get("response", "")
    parsed = _parse_router_output(raw)
    return parsed, duration, raw


def append_activity(decision: RouterDecision, prompt: str,
                    prompt_embedding: Optional[list[float]] = None) -> None:
    """Append a one-line JSON event to the reasoning activity log."""
    record = asdict(decision)
    record["event"] = "router_decision"
    record["prompt_preview"] = prompt[:200]
    # Include embedding for future Upgrade A lookups (truncated for log size)
    if prompt_embedding:
        record["prompt_embedding"] = prompt_embedding
    # tier_classification is populated by the synthesizer, not the Router;
    # but seed the field for log-shape compatibility
    record.setdefault("tier_classification", None)

    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as e:
        # Activity log failure is non-fatal — log to stderr and continue.
        print(f"[router] WARN: failed to append activity log: {e}", file=sys.stderr)

    response_hash = (
        prompt_hash(decision.raw_model_output)
        if decision.raw_model_output
        else ""
    )
    append_action(Action(
        action_id=f"router-{decision.prompt_hash}",
        kind="router_decision",
        harness="reasoning_ensemble/router.py",
        started_at=decision.timestamp,
        ended_at=decision.timestamp,
        duration_seconds=decision.duration_seconds,
        success=True,
        inputs={
            "prompt_hash": decision.prompt_hash,
            "prompt_preview": prompt[:200],
            "prompt_embedding_present": bool(prompt_embedding),
        },
        outputs={
            "mode": decision.mode,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "bias_applied": decision.bias_applied,
            "similar_prior_prompt_hash": decision.similar_prior_prompt_hash,
            "similar_prior_similarity": decision.similar_prior_similarity,
        },
        llm_calls=[{
            "model": decision.model,
            "provider": "ollama-local" if decision.model != "forced" else "caller",
            "prompt_hash": decision.prompt_hash,
            "response_hash": response_hash,
            "duration_seconds": decision.duration_seconds,
            "error": None,
        }],
        routing_decision={
            "mode": decision.mode,
            "reason": decision.reason,
            "confidence": decision.confidence,
            "bias_applied": decision.bias_applied,
        },
    ))


def classify(prompt: str, force_mode: Optional[str] = None) -> RouterDecision:
    """Main entry point. Classify a prompt into one of the three modes.

    If `force_mode` is supplied (from a user `--debate` flag or explicit
    override), skip the classifier and return that mode directly.
    """
    started = time.perf_counter()
    p_hash = prompt_hash(prompt)
    ts = utc_iso()

    if force_mode:
        if force_mode not in ("pass_through", "single_strong", "ensemble"):
            raise ValueError(f"Invalid force_mode: {force_mode}")
        decision = RouterDecision(
            mode=force_mode,
            reason="Forced by caller (--debate flag or explicit override)",
            confidence=1.0,
            prompt_hash=p_hash,
            model="forced",
            embed_model="n/a",
            timestamp=ts,
            duration_seconds=round(time.perf_counter() - started, 3),
            bias_applied="force_flag",
        )
        append_activity(decision, prompt, prompt_embedding=None)
        return decision

    # Upgrade A: get embedding + check Tier-4 similarity bias
    prompt_embedding: Optional[list[float]] = None
    bias_applied: Optional[str] = None
    similar_hash: Optional[str] = None
    similar_sim: Optional[float] = None
    try:
        prompt_embedding = ollama_embed(prompt)
        similar_hash, similar_sim = check_tier4_similarity_bias(prompt_embedding)
        if similar_hash is not None:
            bias_applied = "tier4_similarity"
    except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as e:
        # Embedding failure is non-fatal — Router can still classify without it.
        # TimeoutError covers a stalled Ollama that accepts the connection but
        # never responds within the urlopen timeout (socket.timeout aliases
        # TimeoutError since 3.10), which is not a URLError.
        print(f"[router] WARN: embed step failed (continuing without similarity bias): {e}",
              file=sys.stderr)

    # If similarity bias triggered, short-circuit to ensemble without invoking the Router LLM
    if bias_applied == "tier4_similarity":
        decision = RouterDecision(
            mode="ensemble",
            reason=f"Adjacent past Tier-4 divergence (similarity={similar_sim:.3f}); forcing ensemble per Upgrade A",
            confidence=0.85,  # high but not 1.0 — bias is a heuristic
            prompt_hash=p_hash,
            model=ROUTER_MODEL,
            embed_model=EMBED_MODEL,
            timestamp=ts,
            duration_seconds=round(time.perf_counter() - started, 3),
            bias_applied=bias_applied,
            similar_prior_prompt_hash=similar_hash,
            similar_prior_similarity=similar_sim,
        )
        append_activity(decision, prompt, prompt_embedding=prompt_embedding)
        return decision

    # Normal Router classification path
    try:
        parsed, model_duration, raw = invoke_router(prompt)
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as e:
        # Hard failure — fall back to single_strong (conservative default).
        # TimeoutError included so a stalled Ollama degrades gracefully here too.
        print(f"[router] ERROR: Router invocation failed; defaulting to single_strong: {e}",
              file=sys.stderr)
        decision = RouterDecision(
            mode="single_strong",
            reason=f"Router failed ({type(e).__name__}); conservative fallback",
            confidence=0.3,
            prompt_hash=p_hash,
            model=ROUTER_MODEL,
            embed_model=EMBED_MODEL,
            timestamp=ts,
            duration_seconds=round(time.perf_counter() - started, 3),
            bias_applied="fallback_on_error",
        )
        append_activity(decision, prompt, prompt_embedding=prompt_embedding)
        return decision

    # Validate mode field
    mode = parsed.get("mode", "single_strong")
    if mode not in ("pass_through", "single_strong", "ensemble"):
        print(f"[router] WARN: Router returned invalid mode {mode!r}; coercing to single_strong",
              file=sys.stderr)
        mode = "single_strong"

    decision = RouterDecision(
        mode=mode,
        reason=str(parsed.get("reason", "(no reason)"))[:400],
        confidence=float(parsed.get("confidence", 0.5)),
        prompt_hash=p_hash,
        model=ROUTER_MODEL,
        embed_model=EMBED_MODEL,
        timestamp=ts,
        duration_seconds=round(time.perf_counter() - started, 3),
        bias_applied=None,
        raw_model_output=raw[:1000] if raw else None,
    )
    append_activity(decision, prompt, prompt_embedding=prompt_embedding)
    return decision


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _test_suite() -> int:
    """Run a small calibration suite of representative prompts.

    The expected classification is annotated; the Router's actual output is
    printed for review. This is NOT a strict pass/fail test — model
    classification is probabilistic — it's a calibration aid.
    """
    cases = [
        ("Read line 47 of foo.py", "pass_through"),
        ("List files in the docs/ directory", "pass_through"),
        ("What is the current value of FOO in config.yaml?", "pass_through"),
        ("Reformat this JSON to be pretty-printed", "pass_through"),
        ("Explain what this regex matches", "single_strong"),
        ("Write a unit test for the parse_url function", "single_strong"),
        ("Fix the bug in the for-loop on line 142", "single_strong"),
        ("Refactor the authentication module to use OAuth2 instead of session cookies, touching 5 files including the database migration", "ensemble"),
        ("Design the schema for a new event-sourcing layer", "ensemble"),
        ("Should we switch the consensus gateway from analog vote to weighted analog with reputation?", "ensemble"),
        ("Propose an ADR for the new threat model", "ensemble"),
    ]
    print(f"Router test — model={ROUTER_MODEL}, embed={EMBED_MODEL}")
    print(f"Workspace: {WORKSPACE_ROOT}")
    print(f"Activity log: {ACTIVITY_LOG}")
    print("=" * 80)
    correct = 0
    for i, (prompt, expected) in enumerate(cases, 1):
        d = classify(prompt)
        marker = "✓" if d.mode == expected else "✗"
        if d.mode == expected:
            correct += 1
        print(f"\n[{i:2d}] {marker} expected={expected:14s} got={d.mode:14s} "
              f"conf={d.confidence:.2f} dur={d.duration_seconds:.1f}s"
              + (f" [bias={d.bias_applied}]" if d.bias_applied else ""))
        print(f"     prompt:  {prompt[:90]}{'...' if len(prompt) > 90 else ''}")
        print(f"     reason:  {d.reason[:120]}")
    print(f"\n{'=' * 80}")
    print(f"Score: {correct}/{len(cases)} ({100 * correct / len(cases):.0f}%)")
    print(f"Note: classification is probabilistic; treat as calibration aid, not strict test.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("prompt", nargs="?", help="Prompt to classify")
    parser.add_argument("--test", action="store_true",
                        help="Run the calibration test suite")
    parser.add_argument("--force", choices=["pass_through", "single_strong", "ensemble"],
                        help="Force a mode without invoking the classifier")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.test:
        return _test_suite()
    if not args.prompt:
        print("ERROR: provide a prompt or --test flag", file=sys.stderr)
        return 1
    try:
        decision = classify(args.prompt, force_mode=args.force)
    except urllib.error.URLError as e:
        print(f"ERROR: Ollama unreachable at {OLLAMA_BASE_URL}: {e}", file=sys.stderr)
        return 1
    print(json.dumps(asdict(decision), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
