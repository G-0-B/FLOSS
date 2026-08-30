"""Ensemble Synthesizer — Tier-1/2/4 classification from voter responses.

=========================================================================
WHAT THIS IS
=========================================================================
Partner to `router.py`. When the Router decides `mode=ensemble`, this
module dispatches parallel calls to ≥3 diverse voter models, embeds
each response, clusters them, classifies into Tier-1 (unanimous) /
Tier-2 (majority + dissent) / Tier-4 (preserved divergence), and
produces a synthesized response with named tensions.

=========================================================================
WHY THIS EXISTS
=========================================================================
1. CFIS v0.3 (canonical at `docs/architecture/CFIS_v0.3.md`) names
   Tier-4 divergence as the highest-information event: disagreement
   that survives multi-model exposure is real signal about a hard
   question or a blindspot none can see past. The Synthesizer makes
   this operational at the reasoning-step layer (Router decides; this
   Synthesizer executes).
2. Multi-Model Consensus Reasoning Engine paper (arXiv Jan 2026)
   empirically showed cluster-based Tier classification (via embedding
   similarity + Graph Attention Networks) beats single best model by
   4.6 points and majority vote by 8.1 points on hard reasoning
   benchmarks. Implementation here uses agglomerative clustering as
   the v0.1 approximation (GAT comes in v0.2 once activity-log labels
   accumulate).
3. The MDASH lesson (`docs/research/2026-05-16-mdash-cfis-
   architectural-transfer.md`): a minority-but-coherent voter is often
   correct on hard truthfulness questions. Upgrade D coherence-
   threshold guard (≥0.6 reasoning quality) is the safety net against
   amplifying incoherent noise.

=========================================================================
HOW IT WORKS (high level)
=========================================================================
1. Resolve voter pool from VOTER_POOL constant (env-overridable). Each
   voter is a distinct model family for ensemble independence per the
   ADR-Suite v2.0 ≥3 providers / ≥4 model families diversity policy.
2. Dispatch parallel async calls to all voters via Ollama HTTP API.
   Each voter sees the same prompt + reasoning context. No voter sees
   another voter's output (CFIS-relevant: prevents reasoning
   contamination across frames).
3. Embed each voter's response via mxbai-embed-large.
4. Build pairwise cosine-similarity matrix.
5. Greedy clustering at CLUSTER_SIMILARITY_THRESHOLD (default 0.75).
6. Tier classification from cluster shape:
   - Tier-1: all responses in one cluster (unanimous consensus)
   - Tier-2: dominant cluster with ≥⌈N/2⌉ + flagged dissent
   - Tier-4: roughly-equal clusters OR small minority-but-coherent
     cluster passing the COHERENCE_THRESHOLD guard
7. Synthesize final response with named consensus + named tensions +
   Tier-4 preserved-divergence flags.
8. Write durable draft to `.agent-surface/reasoning/ensemble/<ts>_
   <hash>_synthesis.json`; append global Action.

=========================================================================
SPECS, ADRS, AND RELATED RESEARCH
=========================================================================
- Sibling: `router.py` (mode classifier; this module is the executor)
- Architecture proposal: `docs/research/2026-05-17-inline-reasoning-
  ensemble.md` (full design + v0.2 §12 cluster-based Tier upgrades)
- Epistemic substrate: `docs/architecture/CFIS_v0.3.md` (Tier-1/2/4
  semantics, 4-tier authority, LSM-Override)
- Empirical validation: `docs/research/2026-05-16-mdash-cfis-
  architectural-transfer.md` (MDASH harness-over-model evidence)
- Decision-grade peer: `docs/adr/ADR-10-local-agent-node.md` (ADR-10
  consensus gateway — different stakes, different retention)
- Voter diversity policy: ADR-Suite v2.0 §"Voter roster"
- Consent: `docs/adr/ADR-12-consent-gate-protocol.md` (voter pool
  composition is itself a governed pattern; consent applies)
- Operator guide: `docs/architecture/RUNTIME_SURFACES.md`
- Token-budget discipline: `docs/specs/heartbeat-runtime-budget.spec.md`
  (Synthesizer is invoked on-demand, not on cadence; default voter pool
  is local-only to avoid the heartbeat-poll bleed pattern)
- Unified Action schema: `FLOSS/packages/activity_log/schema.py` +
  `docs/research/2026-05-18-metaharness-unification.md`
- MCP wrapper: `FLOSS/packages/reasoning_ensemble/mcp_server.py`
  exposes `deliberate(prompt)` as a first-class MCP tool

=========================================================================

Partner to `router.py`. When the Router decides `mode=ensemble`, this
module:

  1. Dispatches parallel calls to ≥3 diverse voter models
  2. Embeds each response via mxbai-embed-large
  3. Computes pairwise cosine similarity matrix
  4. Runs greedy clustering (small-N appropriate — no sklearn dependency)
  5. Classifies into Tier-1 (unanimous) / Tier-2 (majority + dissent) /
     Tier-4 (preserved divergence; minority-but-coherent surfaces verbatim)
  6. Applies the coherence-threshold guard per Inline Reasoning Ensemble v0.2 §12.5
  7. Produces a synthesized response
  8. Emits one Action to the global activity log

Voter pool: **online-primary by default** (v0.2). Generation runs on the
consensus-gateway provider roster via `transport.py`
(FLOSS_ENSEMBLE_VOTER_MODE=online), because the local Ollama pool reliably
degraded on VRAM-constrained hardware (see DEFAULT_VOTER_POOL note below).
Local-only (=local) and mixed (=mixed) modes remain available. Embeddings use
local mxbai when reachable, else a single cloud embedder — resolved once per run.

Plane A: drafts go to `.agent-surface/reasoning/ensemble/<id>_synthesis.json`
for review; never auto-promotes to canon.

Usage as library:
    from FLOSS.packages.reasoning_ensemble.synthesizer import synthesize
    result = synthesize(prompt="...")

CLI:
    python FLOSS/packages/reasoning_ensemble/synthesizer.py "Should we adopt OAuth2?"
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Allow running both as a module and as a CLI script
try:
    from FLOSS.packages.activity_log import Action, append_action
    from FLOSS.packages.activity_log.schema import prompt_hash, utc_iso
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from packages.activity_log import Action, append_action
    from packages.activity_log.schema import prompt_hash, utc_iso

try:
    from FLOSS.packages.reasoning_ensemble import transport
except ImportError:
    from packages.reasoning_ensemble import transport

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
ENSEMBLE_STAGING = WORKSPACE_ROOT / ".agent-surface" / "reasoning" / "ensemble"
# Same file the Router appends its decision rows to and scans in
# check_tier4_similarity_bias(). The synthesizer must record the tier here (not
# only in the global Action) so the Tier-4 similarity bias can fire for adjacent
# prompts.
REASONING_ACTIVITY_LOG = (
    WORKSPACE_ROOT / ".agent-surface" / "reasoning" / "activity.jsonl"
)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.environ.get("FLOSS_EMBED_MODEL", "mxbai-embed-large")

# LEGACY (v0.1) local pool. As of v0.2 the live pools are resolved in
# `transport.resolve_voter_pool()` (transport.LOCAL_VOTER_POOL mirrors this for
# mode=local/mixed). Kept for reference / direct-call callers that pass an
# explicit voter_pool. Edit transport.LOCAL_VOTER_POOL, not this, to change the
# local roster.
# All local. ~$0 cost. Each is a distinct family, satisfying the ≥3 providers /
# ≥4 model families diversity policy (provider = model family lineage, not host).
#
# Note: per the reasoning-ensemble v0.2 §12.6 frame-cousin detection,
# voters that always cluster together over time become flagged as "frame
# cousins" sharing a hidden meta-assumption. This pool is a starting
# composition; the activity log will empirically refine it.
DEFAULT_VOTER_POOL = [
    # Small-model pool for v0.1 — fits comfortably alongside mxbai-embed-large
    # (1.2GB) in 16GB VRAM, allowing Ollama to keep all loaded simultaneously
    # without thrashing. Total ≈ 6.4GB + 1.2GB = 7.6GB. Calibrated 2026-05-18
    # after a 4-voter heavy pool (gemma3:12b + llama3.1 + phi4-mini + qwen-coder-3b)
    # hit 3-of-4 timeouts due to GPU serialization. The heavy models become
    # ensemble voters in v0.2 once we tier voter pools by latency budget.
    {"voter_id": "phi4-mini", "model": "phi4-mini:latest", "family": "phi"},
    {
        "voter_id": "llama3.2-3b",
        "model": "llama3.2:3b-instruct-q4_K_S",
        "family": "llama",
    },
    {
        "voter_id": "granite-code-3b",
        "model": "granite-code:3b-instruct-128k-q4_K_S",
        "family": "granite",
    },
    {
        "voter_id": "qwen2.5-coder-3b",
        "model": "hf.co/unsloth/Qwen2.5-Coder-3B-Instruct-128K-GGUF:F16",
        "family": "qwen",
    },
]
# Minimum voters required to call it an ensemble — per ADR-Suite v2.0 diversity
# floor (≥3 providers, ≥4 model families). Below this we degrade to single-strong.
MIN_VOTERS = 3

# Latency budgets. Voter calls run in parallel — total latency ≈ slowest voter.
# Bumped from 120s to 180s after 2026-05-18 calibration showed Ollama GPU
# serialization can stretch the slowest voter when models are swapping.
VOTER_TIMEOUT_SECONDS = 180
EMBED_TIMEOUT_SECONDS = 90
# Health-probe timeout for the local embedder, distinct from the real embed
# timeout above. resolve_embedder() probes local Ollama before any voter is
# dispatched; at 90s a machine where Ollama accepts the connection but stalls on
# the embedding endpoint blocked the whole run past the 120s reasoning-MCP
# timeout, even though the cloud fallback was sitting right there.
EMBED_PROBE_TIMEOUT_SECONDS = 5

# Cluster-similarity threshold for grouping voter responses into the same cluster.
# Cosine similarity > THRESHOLD → same cluster.
# Calibrated based on mxbai-embed-large semantic similarity for related-but-distinct
# answers. 0.75 = "saying basically the same thing"; 0.85 = "near-paraphrase."
CLUSTER_SIMILARITY_THRESHOLD = 0.75

# Measured 2026-08-25 across all six syntheses in .agent-surface/reasoning/ensemble:
# the LOWEST off-diagonal cosine similarity in the entire corpus is 0.791, and the
# median run sits between 0.86 and 0.94. Every pair, in every run -- including four
# prompts explicitly written to elicit disagreement, one of which said "Attack it.
# Do not summarize or agree" -- is above 0.75. All six runs therefore reported
# largest_cluster_fraction = 1.0 with an empty minority set.
#
# That is not six unanimous panels. It is one metric with no discriminative power.
# Whole-response cosine similarity over long-form model prose is dominated by
# topic, vocabulary and register, not by position: six models asked the same
# question about the same repository name the same files in the same voice, and
# land at ~0.9 regardless of whether they agree. Raising the threshold does not
# fix this -- at 0.79 it still separates nothing, and by 0.90 it is splitting on
# writing style rather than on claims.
#
# The threshold is left where it is on purpose. It is not the defect, and moving
# it would hide the defect behind a number that looks tuned. Instead
# separation_diagnostics() below detects when the clustering could not have
# separated anything and refuses to report the result as consensus.
SIMILARITY_FLOOR_OBSERVED = 0.791

# Marker emitted when every pair sits above the clustering threshold, so a
# single cluster was the only reachable outcome.
CONSENSUS_NOT_MEASURED = "E_CONSENSUS_NOT_MEASURED"

# The machine-readable tier for a run whose clustering could not have separated
# anything. `tier1` means unanimous consensus in the spec, and every automated
# consumer -- the staged JSON, the activity action, the deliberate() MCP
# response -- exported it verbatim while the warning went only into human prose.
# A reader parsing `tier` therefore treated an explicitly unmeasured run as
# corroboration. The tier itself has to carry the finding.
TIER_UNMEASURED = "unmeasured"

# Coherence threshold for the anti-sycophancy override (v0.2 §12.5).
# A single-voter dissent is only surfaced verbatim if its response_length and
# internal_coherence_proxy meet a minimum bar. Otherwise logged but not surfaced.
COHERENCE_MIN_RESPONSE_CHARS = (
    100  # Below this = too short to count as substantive dissent
)
COHERENCE_MIN_SENTENCE_COUNT = 2  # Below this = too fragmentary


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class VoterResponse:
    voter_id: str
    model: str
    family: str
    response: str
    response_hash: str
    response_embedding: Optional[list[float]]
    duration_seconds: float
    error: Optional[str] = None
    # Which wire this voter actually went over ("ollama" / "litellm" /
    # "flowith"), carried through so the staged Action can name the real
    # provider instead of guessing from the model id.
    transport_name: str = "litellm"

    @property
    def is_coherent(self) -> bool:
        """v0.2 §12.5 coherence guard: enough content + structure to be substantive."""
        if not self.response or self.error:
            return False
        if len(self.response) < COHERENCE_MIN_RESPONSE_CHARS:
            return False
        sentence_count = sum(self.response.count(p) for p in ".!?")
        return sentence_count >= COHERENCE_MIN_SENTENCE_COUNT


@dataclass
class TierClassification:
    tier: str  # "tier1" | "tier2" | "tier4"
    cluster_assignments: dict[str, int]  # voter_id → cluster_id
    cluster_sizes: dict[int, int]  # cluster_id → count
    largest_cluster_id: int
    largest_cluster_fraction: float
    minority_coherent_voters: list[str]  # voter_ids of small but coherent dissenters
    similarity_matrix: list[list[float]]  # N×N for log/debug
    # Whether the clustering could have produced more than one cluster at all.
    # False means the tier is an artifact of the metric, not a finding about the
    # voters. Defaulted so existing constructors keep working; every real path
    # sets it explicitly.
    separation: dict[str, object] = field(default_factory=dict)

    @property
    def consensus_was_measurable(self) -> bool:
        return bool(self.separation.get("discriminative", True))


@dataclass
class EnsembleSynthesis:
    prompt: str
    prompt_hash: str
    timestamp: str
    duration_seconds: float
    voter_responses: list[VoterResponse]
    tier_classification: TierClassification
    final_synthesis: str
    staging_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Ollama helpers
# ---------------------------------------------------------------------------


def _ollama_request(path: str, payload: dict, timeout: int) -> dict:
    url = f"{OLLAMA_BASE_URL.rstrip('/')}{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ollama_embed(text: str, timeout: int = EMBED_TIMEOUT_SECONDS) -> list[float]:
    """Get a 1024-d mxbai embedding for text. Raises on failure."""
    response = _ollama_request(
        "/api/embeddings",
        {"model": EMBED_MODEL, "prompt": text},
        timeout=timeout,
    )
    emb = response.get("embedding", [])
    if not emb:
        raise RuntimeError(f"Empty embedding from {EMBED_MODEL}")
    return emb


def _local_embed_probe(text: str) -> list[float]:
    """Health-probe the local embedder under a short, separate timeout."""
    return ollama_embed(text, timeout=EMBED_PROBE_TIMEOUT_SECONDS)


def _provider_label(response: "VoterResponse") -> str:
    """Name the transport a voter's call actually went over.

    The staged Action used to read the model id's prefix, so with
    FLOSS_MODEL_BACKEND=omniroute every online voter was recorded as `groq`,
    `mistral`, and so on -- the model's vendor, not the wire the request took.
    scripts/autonomous_synthesis_loop.py already records this correctly via
    active_model_backend(); the two paths disagreed about the same run, which is
    exactly what provider-level audit and migration comparison cannot tolerate.
    """
    if response.transport_name == "ollama":
        return "ollama-local"
    if response.transport_name == "flowith":
        return "flowith"
    if os.environ.get("FLOSS_MODEL_BACKEND", "litellm") == "omniroute":
        return "omniroute"
    return "litellm"


def ollama_generate(
    model: str, prompt: str, timeout: int = VOTER_TIMEOUT_SECONDS
) -> str:
    """Single non-streaming generate call. Returns response text."""
    response = _ollama_request(
        "/api/generate",
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.4, "num_predict": 600},
        },
        timeout=timeout,
    )
    return response.get("response", "")


# ---------------------------------------------------------------------------
# Voter dispatch
# ---------------------------------------------------------------------------


def _dispatch_voter(voter: dict, prompt: str, embed_fn=ollama_embed) -> VoterResponse:
    """Call one voter. Wraps errors into the response. Never raises.

    Generation is routed by the voter's transport (ollama / litellm / flowith)
    via transport.generate. `embed_fn` is the run's single resolved embedder
    (local mxbai or a cloud fallback) so every voter shares one vector space.
    """
    started = time.perf_counter()
    # Resolved OUTSIDE the try. When it lived inside, the except branch below
    # built its VoterResponse without it and the field fell back to its
    # "litellm" default -- so every failed ollama or flowith call was attributed
    # to litellm in the staged artifact and in _log_synthesis_action(), which is
    # precisely the data a provider failure-rate audit reads.
    try:
        voter_transport = str(voter.get("transport") or "litellm")
    except Exception:  # noqa: BLE001 -- a malformed voter must not raise here
        voter_transport = "litellm"
    try:
        text = transport.generate(voter, prompt, VOTER_TIMEOUT_SECONDS, ollama_generate)
        duration = time.perf_counter() - started
        if not text:
            return VoterResponse(
                voter_id=voter["voter_id"],
                model=voter["model"],
                family=voter["family"],
                response="",
                response_hash="",
                response_embedding=None,
                duration_seconds=duration,
                error="empty_response",
                transport_name=voter_transport,
            )
        # Embed in this voter's thread to keep things parallel-friendly
        try:
            emb = embed_fn(text)
        except Exception as e:  # noqa: BLE001
            emb = None
            embed_err = f"embed_failed: {e}"
        else:
            embed_err = None
        return VoterResponse(
            voter_id=voter["voter_id"],
            model=voter["model"],
            family=voter["family"],
            response=text,
            response_hash=prompt_hash(text),
            response_embedding=emb,
            duration_seconds=round(duration, 3),
            error=embed_err,
            transport_name=voter_transport,
        )
    except Exception as e:  # noqa: BLE001 -- deliberate, see below
        # Catch EVERYTHING. This function's contract, stated in its own
        # docstring, is that it never raises: one voter failing must degrade to
        # an errored VoterResponse so the other voters' answers still count.
        #
        # The previous tuple (URLError, RuntimeError, JSONDecodeError,
        # TimeoutError) did not hold that contract. Provider clients raise their
        # own types -- httpx.ConnectError, LiteLLM's API exception classes,
        # ssl.SSLError, bare OSError -- and none of those are subclasses of the
        # four listed. Such an exception propagated out of `fut.result()` in
        # dispatch_parallel and aborted the entire synthesis, so a single
        # transient provider hiccup discarded every other voter's work. Provider
        # 404s and timeouts are routine on this stack, so this was not a rare
        # path.
        #
        # Naming provider exception types explicitly is not an option worth
        # taking: it would make this module import-depend on every transport's
        # client library, and the next new provider would silently reintroduce
        # the same bug. A voter boundary is exactly where a broad catch belongs.
        duration = time.perf_counter() - started
        return VoterResponse(
            voter_id=voter["voter_id"],
            model=voter["model"],
            family=voter["family"],
            response="",
            response_hash="",
            response_embedding=None,
            duration_seconds=round(duration, 3),
            error=f"{type(e).__name__}: {e}",
            transport_name=voter_transport,
        )


def dispatch_parallel(
    voter_pool: list[dict], prompt: str, embed_fn=ollama_embed
) -> list[VoterResponse]:
    """Fan out to all voters in parallel via ThreadPoolExecutor.

    For online voters (mode=online, the default) generation is network-bound and
    genuinely parallel. For local Ollama voters (mode=local/mixed) GPU access is
    serialized internally, so parallelism is partial — but submitting together
    still lets Ollama overlap different models better than strict-serial.
    """
    voter_prompt = _build_voter_prompt(prompt)
    responses: list[VoterResponse] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(voter_pool)) as executor:
        futures = {
            executor.submit(_dispatch_voter, v, voter_prompt, embed_fn): v
            for v in voter_pool
        }
        for fut in concurrent.futures.as_completed(futures):
            responses.append(fut.result())
    # Preserve canonical ordering by voter_id for reproducible logs
    responses.sort(key=lambda r: r.voter_id)
    return responses


def _build_voter_prompt(user_prompt: str) -> str:
    """Wrap the user prompt with the voter-role framing."""
    return f"""You are one voter in a multi-model ensemble deliberating a substantive question.
Provide your independent reasoning and answer. You do NOT see other voters' responses.

Disagreement between voters is signal, not failure — answer honestly even if it differs
from what you expect others to say. Be concise but show your reasoning briefly (2-5 sentences).

QUESTION:
{user_prompt}

YOUR REASONING + ANSWER:"""


# ---------------------------------------------------------------------------
# Clustering + Tier classification
# ---------------------------------------------------------------------------


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def pairwise_similarity_matrix(responses: list[VoterResponse]) -> list[list[float]]:
    """Compute N×N cosine similarity. Voters with missing embeddings: 0.0 row/col."""
    n = len(responses)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 1.0
            elif responses[i].response_embedding and responses[j].response_embedding:
                matrix[i][j] = cosine(
                    responses[i].response_embedding, responses[j].response_embedding
                )
    return matrix


def greedy_cluster(
    responses: list[VoterResponse], similarity: list[list[float]], threshold: float
) -> dict[str, int]:
    """Simple greedy single-link clustering for small N.

    Assigns cluster IDs starting from 0. Two voters share a cluster iff their
    pairwise similarity >= threshold OR they're transitively connected through
    such pairs.
    """
    n = len(responses)
    assignments: dict[str, int] = {}
    next_cluster_id = 0

    for i, r in enumerate(responses):
        if r.voter_id in assignments:
            continue
        # Find any earlier voter this one is similar to
        merged_into: Optional[int] = None
        for j in range(i):
            if similarity[i][j] >= threshold:
                earlier = responses[j].voter_id
                if earlier in assignments:
                    merged_into = assignments[earlier]
                    break
        if merged_into is not None:
            assignments[r.voter_id] = merged_into
        else:
            assignments[r.voter_id] = next_cluster_id
            next_cluster_id += 1

    # Optional second pass: merge clusters that have any pair >= threshold
    # (handles transitive cases the single forward pass missed)
    changed = True
    while changed:
        changed = False
        for i in range(n):
            for j in range(i + 1, n):
                if similarity[i][j] < threshold:
                    continue
                ci = assignments[responses[i].voter_id]
                cj = assignments[responses[j].voter_id]
                if ci != cj:
                    # Merge the higher cluster id into the lower
                    target = min(ci, cj)
                    other = max(ci, cj)
                    for v_id, cid in assignments.items():
                        if cid == other:
                            assignments[v_id] = target
                    changed = True
    return assignments


# A response can be present, long, and still contain no position. Two of the
# six voters in the 2026-08-24 campaign were non-functional in every run and
# were counted as converged voters in all of them: one emitted a bare `<think>`
# restatement of the prompt (5/5 runs), the other was truncated mid-sentence
# (5/5, 212-1466 chars against 2000-3200 for peers). The "≥3 provider surfaces /
# ≥4 model families" diversity policy was therefore satisfied on paper by voters
# that produced no positions.
#
# Length alone does not catch this -- the restating voter was the SECOND-LONGEST
# response in one run. These checks are shape-based and deliberately
# conservative: they flag, they do not exclude, because a wrong exclusion loses
# a real vote while a wrong flag costs a line of output.
DEGENERATE_TRUNCATION_RATIO = 0.4
THINK_OPENERS = ("<think>", "<thinking>", "<reasoning>")
SENTENCE_ENDINGS = (".", "!", "?", "`", ")", "]", '"', "'")


def degenerate_voters(responses: list[VoterResponse]) -> dict[str, str]:
    """Name voters whose text is present but carries no position.

    Returns voter_id -> reason. Empty when every response looks substantive.
    """

    scored = [r for r in responses if r.response and not r.error]
    if not scored:
        return {}
    lengths = sorted(len(r.response) for r in scored)
    median = lengths[len(lengths) // 2]

    flagged: dict[str, str] = {}
    for response in scored:
        text = response.response.strip()
        lowered = text.lower()
        if lowered.startswith(THINK_OPENERS) and "</" not in lowered:
            flagged[response.voter_id] = (
                "opens a reasoning block that never closes -- prompt "
                "restatement, not an answer"
            )
            continue
        if not text.endswith(SENTENCE_ENDINGS) and len(text) < median:
            flagged[response.voter_id] = (
                f"ends mid-sentence at {len(text)} chars against a "
                f"{median}-char median -- truncated, not concluded"
            )
    return flagged


def separation_diagnostics(
    similarity: list[list[float]],
    threshold: float,
    embedded: list[bool] | None = None,
) -> dict[str, object]:
    """Report whether the clustering could have separated anything at all.

    A cluster assignment only carries information if the similarity values
    actually straddle the threshold. If every off-diagonal pair is above it, a
    single cluster was the only reachable outcome and ``tier1`` says nothing
    about whether the voters agreed -- it says the metric never looked.

    That is not hypothetical. Every synthesis this repository has produced to
    date reports ``largest_cluster_fraction = 1.0`` with an empty minority set,
    including four prompts written specifically to provoke dissent. The measured
    floor across the whole corpus is 0.791 against a 0.75 threshold.

    Returns a dict rather than a bool so the numbers travel with the verdict and
    a future calibration argument can be made from data instead of from memory.
    """

    def _has_embedding(index: int) -> bool:
        if embedded is None:
            return True
        return index < len(embedded) and bool(embedded[index])

    # ONE TRIANGLE. The matrix is symmetric, so iterating the full off-diagonal
    # visited (i,j) and (j,i) and reported exactly twice the number of distinct
    # pairs -- six for three voters. Those counts are persisted and presented as
    # experimental diagnostics, so they were wrong wherever they were read.
    scored: list[float] = []
    missing_pairs = 0
    for i in range(len(similarity)):
        for j in range(i + 1, len(similarity)):
            value = similarity[i][j]
            # pairwise_similarity_matrix writes 0.0 for a voter with no
            # embedding. A genuine cosine can also be 0.0 or negative, and
            # dropping those as "missing" hid real disagreement: a panel whose
            # only separating pairs were negative reported that every scored
            # pair converged and that separation was impossible, while the
            # clustering used those same negatives and split the voters.
            if _has_embedding(i) and _has_embedding(j):
                scored.append(value)
            else:
                missing_pairs += 1
    if not scored:
        return {
            "discriminative": False,
            "reason": "no scored pairs (missing embeddings)",
            "pair_count": 0,
            "pairs_missing_embeddings": missing_pairs,
            "threshold": threshold,
        }

    low = min(scored)
    high = max(scored)
    below = sum(1 for value in scored if value < threshold)
    # Discriminative means the threshold actually falls inside the observed
    # spread. If it sits below the floor, no pair could ever have been split;
    # if it sits above the ceiling, every voter would be its own cluster and
    # "dissent" would be equally meaningless.
    discriminative = low < threshold <= high

    diagnostics: dict[str, object] = {
        "discriminative": discriminative,
        "pair_count": len(scored),
        "pairs_missing_embeddings": missing_pairs,
        "threshold": threshold,
        "min": round(low, 4),
        "max": round(high, 4),
        "mean": round(sum(scored) / len(scored), 4),
        "pairs_below_threshold": below,
    }
    if not discriminative:
        if low >= threshold:
            diagnostics["reason"] = (
                f"{CONSENSUS_NOT_MEASURED}: every one of {len(scored)} pairs "
                f"scored >= {threshold} (floor {low:.3f}); a single cluster was "
                f"the only reachable outcome, so the tier reflects the metric "
                f"and not the voters"
            )
        else:
            diagnostics["reason"] = (
                f"{CONSENSUS_NOT_MEASURED}: every one of {len(scored)} pairs "
                f"scored < {threshold} (ceiling {high:.3f}); every voter is its "
                f"own cluster, so dissent is equally unmeasured"
            )
    return diagnostics


def classify_tier(
    responses: list[VoterResponse],
    similarity: list[list[float]],
    assignments: dict[str, int],
) -> TierClassification:
    """Tier-1/2/4 from cluster sizes + coherence-guard for minority surfaces."""
    cluster_sizes: dict[int, int] = {}
    for cid in assignments.values():
        cluster_sizes[cid] = cluster_sizes.get(cid, 0) + 1

    total = sum(cluster_sizes.values())
    largest_cid = max(cluster_sizes, key=cluster_sizes.get) if cluster_sizes else 0
    largest_size = cluster_sizes.get(largest_cid, 0)
    largest_fraction = largest_size / total if total else 0.0

    # Tier classification per v0.2 §12.3:
    #   Tier-1: all responses in one cluster
    #   Tier-2: dominant cluster (≥ ⌈N/2⌉) that is the unique largest
    #   Tier-4: roughly equal clusters (incl. an even split like 2/2 or 1/1)
    #           OR small coherent minority
    # Compare cluster COUNTS, not a fraction-with-epsilon: an even split with a
    # genuine plurality (e.g. 4 voters splitting 2/1/1) has largest_fraction
    # exactly 0.5 and must qualify as Tier-2, while a 2/2 tie must not.
    ceil_half = (total + 1) // 2
    unique_largest = (
        sum(1 for size in cluster_sizes.values() if size == largest_size) == 1
    )
    if len(cluster_sizes) == 1:
        tier = "tier1"
        # Overwritten below if the clustering could not have separated anything.
    elif largest_size >= ceil_half and unique_largest:
        tier = "tier2"
    else:
        tier = "tier4"

    # Coherence guard on minority clusters: which dissenters surface verbatim?
    minority_coherent_voters: list[str] = []
    voter_by_id = {r.voter_id: r for r in responses}
    for v_id, cid in assignments.items():
        if cluster_sizes[cid] < largest_size:
            voter = voter_by_id[v_id]
            if voter.is_coherent:
                minority_coherent_voters.append(v_id)

    separation = separation_diagnostics(
        similarity,
        CLUSTER_SIMILARITY_THRESHOLD,
        embedded=[r.response_embedding is not None for r in responses],
    )
    if not separation.get("discriminative", True):
        # ANY tier, not just tier1. The guard was written for the documented
        # all-pairs-above-threshold case and therefore only caught single-cluster
        # runs -- while the equally non-discriminative all-pairs-BELOW case
        # produces many clusters, lands on tier4, and was exported and rendered
        # as measured divergence.
        #
        # separation_diagnostics already reports discriminative=False for both
        # sides. Guarding one of them was reading the diagnostic and then
        # re-deciding the question from the tier.
        #
        # `tier1` is a claim that the voters agreed; `tier4` is a claim that they
        # diverged. A run whose threshold sat outside the observed spread
        # supports neither.
        tier = TIER_UNMEASURED

    return TierClassification(
        tier=tier,
        cluster_assignments=assignments,
        cluster_sizes=cluster_sizes,
        largest_cluster_id=largest_cid,
        largest_cluster_fraction=round(largest_fraction, 3),
        minority_coherent_voters=minority_coherent_voters,
        similarity_matrix=[[round(v, 3) for v in row] for row in similarity],
        separation=separation,
    )


# ---------------------------------------------------------------------------
# Synthesis writeup
# ---------------------------------------------------------------------------


def write_synthesis(
    prompt: str,
    responses: list[VoterResponse],
    tier_class: TierClassification,
    all_responses: list[VoterResponse] | None = None,
) -> str:
    """Produce the human-readable synthesis. Tier-aware formatting.

    `responses` are the voters that produced an embedding and were therefore
    clusterable. `all_responses` is every voter that was dispatched. They differ
    whenever a voter times out, and the difference used to vanish: the header
    printed `len(responses)`, so a file could read "Voters: 5" while its own
    `voter_count` field said 6 and no line anywhere said a voter was lost.
    """
    dispatched = all_responses if all_responses is not None else responses
    voter_by_id = {r.voter_id: r for r in responses}
    largest_cluster_voters = [
        v_id
        for v_id, cid in tier_class.cluster_assignments.items()
        if cid == tier_class.largest_cluster_id
    ]
    minority_voters = [
        v_id
        for v_id in tier_class.cluster_assignments
        if v_id not in largest_cluster_voters
    ]

    lines: list[str] = []
    lines.append(f"# Ensemble synthesis — {tier_class.tier.upper()}")
    if tier_class.tier == TIER_UNMEASURED:
        lines.append("")
        # Same false claim as the body branch had: this asserted the all-above
        # shape for both non-discriminative sides. The header is a sibling of
        # that defect and was written in the same commit.
        lines.append(
            "_(`tier: unmeasured`, not `tier1` or `tier4`. The clustering "
            "threshold sat outside the observed similarity range, so it could "
            "not have separated the voters differently however they answered. "
            "This run makes no claim about agreement OR divergence, and machine "
            "consumers must not read it as either.)_"
        )
    lines.append("")
    lines.append(
        f"**Voters:** {len(responses)} ({', '.join(r.family for r in responses)})"
    )
    lost = [r for r in dispatched if r.voter_id not in voter_by_id]
    if lost:
        lines.append(
            f"**Dispatched but not counted:** {len(lost)} of {len(dispatched)} — "
            + ", ".join(
                f"{r.voter_id} ({r.error or 'no embedding'})" for r in lost
            )
        )
    lines.append(
        f"**Largest cluster:** {len(largest_cluster_voters)}/{len(responses)} "
        f"({100 * tier_class.largest_cluster_fraction:.0f}%)"
    )
    if not tier_class.consensus_was_measurable:
        # Say this above the fold, before any number that looks like agreement.
        # A reader who takes "6/6, 100%" at face value and cites it as
        # multi-model corroboration is making a claim the measurement does not
        # support, and the measurement is the only thing that knows that.
        separation = tier_class.separation
        lines.append("")
        lines.append("> **This run did not measure consensus.**")
        lines.append(">")
        lines.append(f"> {separation.get('reason', CONSENSUS_NOT_MEASURED)}")
        lines.append(">")
        lines.append(
            f"> Observed pairwise similarity: min {separation.get('min')}, "
            f"mean {separation.get('mean')}, max {separation.get('max')} "
            f"across {separation.get('pair_count')} pairs, threshold "
            f"{separation.get('threshold')}. "
            f"{separation.get('pairs_below_threshold')} pairs fell below it."
        )
        lines.append(">")
        lines.append(
            "> Treat the cluster numbers above as diagnostics of the metric, not "
            "as agreement between voters. Do not cite this run as corroboration."
        )
    degenerate = degenerate_voters(responses)
    if degenerate:
        lines.append("")
        lines.append(
            f"> **{len(degenerate)} of {len(responses)} counted voters returned "
            f"no position.**"
        )
        for voter_id, reason in degenerate.items():
            lines.append(f">   - `{voter_id}`: {reason}")
        lines.append(">")
        lines.append(
            "> These were clustered as agreement. A voter that restates the "
            "prompt or stops mid-sentence agrees with nothing; count the "
            "diversity policy against the voters that actually answered."
        )
    lines.append("")

    if tier_class.tier == "tier1":
        if tier_class.consensus_was_measurable:
            lines.append("## Unanimous consensus")
        else:
            lines.append("## Single cluster — consensus not established")
        lines.append("")
        # The "synthesis" of a single cluster is one voter's verbatim text,
        # selected by character count. That is worth stating plainly rather than
        # letting the word "synthesis" imply that anything was combined.
        rep = max(
            (voter_by_id[v] for v in largest_cluster_voters),
            key=lambda r: len(r.response),
        )
        lines.append(f"> {rep.response}")
        lines.append("")
        if tier_class.consensus_was_measurable:
            lines.append(
                f"_(Representative voter: {rep.voter_id} / {rep.family} family. "
                f"All {len(responses)} voters converged.)_"
            )
        else:
            lines.append(
                f"_(Text above is the verbatim response of {rep.voter_id} / "
                f"{rep.family} family, selected as the longest of "
                f"{len(responses)}. Nothing was combined, and the clustering "
                f"could not have placed any voter elsewhere. The other "
                f"{len(responses) - 1} responses are preserved in "
                f"`voter_responses[]` and are the only place a disagreement, if "
                f"there was one, still exists.)_"
            )

    elif tier_class.tier == "tier2":
        lines.append("## Majority consensus (with named dissent)")
        lines.append("")
        rep = max(
            (voter_by_id[v] for v in largest_cluster_voters),
            key=lambda r: len(r.response),
        )
        lines.append(f"> {rep.response}")
        lines.append("")
        lines.append(
            f"_(Representative: {rep.voter_id}. "
            f"{len(largest_cluster_voters)}/{len(responses)} voters in this cluster.)_"
        )
        lines.append("")
        if tier_class.minority_coherent_voters:
            lines.append("## Named dissent (passed coherence guard)")
            for v_id in tier_class.minority_coherent_voters:
                v = voter_by_id[v_id]
                lines.append("")
                lines.append(f"**{v.voter_id} / {v.family}:**")
                lines.append(f"> {v.response}")
        elif minority_voters:
            lines.append(
                f"_(Minority voters {', '.join(minority_voters)} dissented but "
                "their responses failed the coherence guard — "
                "logged to activity log but not surfaced.)_"
            )

    elif tier_class.tier == TIER_UNMEASURED:
        # Its own branch. Reclassifying a single-cluster run to `unmeasured`
        # dropped it into the tier4 `else`, so the artifact said consensus was
        # unmeasured and then, three lines later, claimed "Tier-4 divergence
        # preserved" and "No single cluster carried the majority" -- about a run
        # that had exactly ONE cluster. A reader could believe either half.
        lines.append("## Consensus not measured")
        lines.append("")
        # Read the REASON from the diagnostic instead of assuming the case the
        # branch was written for. Generalising classify_tier to both
        # non-discriminative sides while leaving this prose describing only the
        # all-above one produced an artifact that told an all-below run every
        # voter had landed in one cluster -- when in fact each had its own.
        separation = tier_class.separation or {}
        cluster_count = len(set(tier_class.cluster_assignments.values()))
        if cluster_count <= 1:
            shape = (
                "Every voter landed in one cluster, and the clustering could "
                "not have produced more than one."
            )
        else:
            shape = (
                f"The clustering produced {cluster_count} clusters -- one per "
                f"voter -- because no pair reached the threshold, so it could "
                f"not have produced fewer."
            )
        lines.append(
            f"{shape} That is a property of the metric, not a finding about the "
            f"voters: this run neither established agreement nor observed "
            f"divergence."
        )
        if separation.get("reason"):
            lines.append("")
            lines.append(f"> {separation['reason']}")
        lines.append("")
        lines.append("**The responses are the output. All of them, unranked:**")
        lines.append("")
        for voter_id in tier_class.cluster_assignments:
            voter = voter_by_id.get(voter_id)
            if voter is None:
                continue
            lines.append(f"### {voter.voter_id} ({voter.family})")
            lines.append("")
            lines.append(f"> {voter.response}")
            lines.append("")
        lines.append(
            "_(Nothing was combined and nothing was selected as representative. "
            "Any disagreement between these responses is present above and was "
            "not measured by the clustering.)_"
        )

    else:  # tier4
        lines.append("## Tier-4 divergence preserved")
        lines.append("")
        lines.append("**No single cluster carried the majority. Distinct positions:**")
        lines.append("")
        # Group by cluster
        clusters: dict[int, list[str]] = {}
        for v_id, cid in tier_class.cluster_assignments.items():
            clusters.setdefault(cid, []).append(v_id)
        for cid, members in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
            rep_v = max(
                (voter_by_id[m] for m in members), key=lambda r: len(r.response)
            )
            lines.append(
                f"### Position {cid + 1} — {len(members)} voter(s): "
                f"{', '.join(members)}"
            )
            lines.append("")
            lines.append(f"> {rep_v.response}")
            lines.append("")
        lines.append(
            "_This divergence is preserved as Tier-4 per CFIS v0.3 — it is "
            "high-information, not noise. Per Inline Reasoning Ensemble v0.2 "
            "§12.3 the minority-but-coherent cluster is sometimes correct on "
            "hard questions; the user adjudicates._"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


def synthesize(
    prompt: str, voter_pool: Optional[list[dict]] = None, stage_artifact: bool = True
) -> EnsembleSynthesis:
    """Run the full ensemble: voters → embed → cluster → tier → synthesize.

    When `voter_pool` is None the pool is resolved from FLOSS_ENSEMBLE_VOTER_MODE
    (online-primary by default), so a deliberation no longer depends on local GPU
    headroom. The embedder is resolved once per run (local mxbai preferred, cloud
    fallback) so all voter responses share one vector space.
    """
    if voter_pool is not None:
        pool = voter_pool
    else:
        pool, _mode = transport.resolve_voter_pool()
    if len(pool) < MIN_VOTERS:
        raise ValueError(f"Voter pool too small: {len(pool)} < {MIN_VOTERS}")

    started_iso = utc_iso()
    started_perf = time.perf_counter()
    p_hash = prompt_hash(prompt)

    # Resolve the single embedder for this run (shared vector space required).
    # The local probe is bounded separately from the real embed timeout: see
    # EMBED_PROBE_TIMEOUT_SECONDS. Once resolved, the returned embedder uses the
    # full timeout for actual work.
    _embed_name, embed_fn = transport.resolve_embedder(
        _local_embed_probe,
        local_embed_fn=ollama_embed,
        embed_timeout=EMBED_TIMEOUT_SECONDS,
    )

    # 1-3: dispatch + embed (embed is inside _dispatch_voter)
    responses = dispatch_parallel(pool, prompt, embed_fn)

    # Filter to voters that produced an embedding (others can't be clustered)
    embedded = [r for r in responses if r.response_embedding is not None]
    if len(embedded) < MIN_VOTERS:
        # Degraded — log + return a sentinel
        duration = time.perf_counter() - started_perf
        result = EnsembleSynthesis(
            prompt=prompt,
            prompt_hash=p_hash,
            timestamp=started_iso,
            duration_seconds=round(duration, 3),
            voter_responses=responses,
            tier_classification=TierClassification(
                tier="degraded",
                cluster_assignments={r.voter_id: 0 for r in responses},
                cluster_sizes={0: len(responses)},
                largest_cluster_id=0,
                largest_cluster_fraction=1.0,
                minority_coherent_voters=[],
                similarity_matrix=[],
                separation={
                    "discriminative": False,
                    "reason": (
                        f"{CONSENSUS_NOT_MEASURED}: degraded run, "
                        f"{len(embedded)}/{len(responses)} voters embedded"
                    ),
                    "pair_count": 0,
                    "threshold": CLUSTER_SIMILARITY_THRESHOLD,
                },
            ),
            final_synthesis=(
                f"# Ensemble synthesis — DEGRADED\n\n"
                f"Fewer than {MIN_VOTERS} voters produced embeddings "
                f"({len(embedded)}/{len(responses)}). Cannot run cluster-based Tier "
                f"classification. Raw voter responses follow:\n\n"
                + "\n\n---\n\n".join(
                    f"**{r.voter_id} ({r.family})** "
                    f"{'OK' if not r.error else 'ERR: ' + r.error}\n\n{r.response}"
                    for r in responses
                )
            ),
        )
        _log_synthesis_action(
            result,
            prompt,
            p_hash,
            started_iso,
            success=False,
            error=f"insufficient_voters: {len(embedded)}/{len(responses)}",
        )
        return result

    # 4: cluster
    sim = pairwise_similarity_matrix(embedded)
    assignments = greedy_cluster(embedded, sim, CLUSTER_SIMILARITY_THRESHOLD)

    # 5: tier classification + coherence guard
    tier_class = classify_tier(embedded, sim, assignments)

    # 6: synthesis writeup
    final = write_synthesis(prompt, embedded, tier_class, all_responses=responses)

    # 7: stage artifact
    staging_path: Optional[str] = None
    if stage_artifact:
        ENSEMBLE_STAGING.mkdir(parents=True, exist_ok=True)
        ts_short = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = ENSEMBLE_STAGING / f"{ts_short}_{p_hash}_synthesis.json"
        try:
            out_path.write_text(
                json.dumps(
                    {
                        "prompt": prompt,
                        "prompt_hash": p_hash,
                        "timestamp": started_iso,
                        "tier": tier_class.tier,
                        "voter_count": len(responses),
                        "embedded_voter_count": len(embedded),
                        "cluster_assignments": tier_class.cluster_assignments,
                        "cluster_sizes": tier_class.cluster_sizes,
                        "largest_cluster_fraction": tier_class.largest_cluster_fraction,
                        "minority_coherent_voters": tier_class.minority_coherent_voters,
                        "similarity_matrix": tier_class.similarity_matrix,
                        "separation": tier_class.separation,
                        "degenerate_voters": degenerate_voters(embedded),
                        "voter_responses": [asdict(r) for r in responses],
                        "final_synthesis": final,
                    },
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                ),
                encoding="utf-8",
            )
            staging_path = str(out_path.relative_to(WORKSPACE_ROOT).as_posix())
        except OSError as e:
            print(f"[synthesizer] WARN: failed to stage artifact: {e}", file=sys.stderr)

    duration = time.perf_counter() - started_perf
    result = EnsembleSynthesis(
        prompt=prompt,
        prompt_hash=p_hash,
        timestamp=started_iso,
        duration_seconds=round(duration, 3),
        voter_responses=responses,
        tier_classification=tier_class,
        final_synthesis=final,
        staging_path=staging_path,
    )

    # 8: emit Action to global activity log
    _log_synthesis_action(result, prompt, p_hash, started_iso, success=True)
    return result


def _log_synthesis_action(
    result: EnsembleSynthesis,
    prompt: str,
    p_hash: str,
    started_iso: str,
    success: bool,
    error: Optional[str] = None,
) -> None:
    llm_calls = [
        {
            "model": r.model,
            "provider": _provider_label(r),
            "voter_id": r.voter_id,
            "family": r.family,
            "prompt_hash": p_hash,
            "response_hash": r.response_hash,
            "duration_seconds": r.duration_seconds,
            "error": r.error,
        }
        for r in result.voter_responses
    ]
    action = Action(
        action_id=f"ensemble-{p_hash}",
        kind="ensemble_synthesis",
        harness="reasoning_ensemble/synthesizer.py",
        started_at=started_iso,
        ended_at=utc_iso(),
        duration_seconds=result.duration_seconds,
        success=success,
        inputs={
            "prompt_preview": prompt[:200],
            "voter_count": len(result.voter_responses),
        },
        outputs={
            "tier": result.tier_classification.tier,
            "largest_cluster_fraction": result.tier_classification.largest_cluster_fraction,
            "minority_coherent_count": len(
                result.tier_classification.minority_coherent_voters
            ),
            "synthesis_preview": result.final_synthesis[:400],
        },
        llm_calls=llm_calls,
        staging_paths=[result.staging_path] if result.staging_path else [],
        error=error,
    )
    append_action(action)

    # Also write a top-level row to the reasoning activity log, where the
    # Router's check_tier4_similarity_bias() actually looks. The global Action
    # above is off that scan path, and the Router seeds tier_classification=None
    # on its own row — so without this, a real Tier-4 divergence never biases the
    # adjacent-prompt routing it promises. For Tier-4 we also record the prompt
    # embedding (the field the similarity check requires); best-effort, non-fatal.
    tier = result.tier_classification.tier
    row: dict = {
        "event": "ensemble_synthesis",
        "prompt_hash": p_hash,
        "prompt_preview": prompt[:200],
        "tier_classification": tier,
    }
    if tier == "tier4":
        try:
            row["prompt_embedding"] = ollama_embed(prompt)
        except Exception:  # noqa: BLE001 — embedding is best-effort
            pass
    try:
        REASONING_ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with REASONING_ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("prompt", help="Question for the ensemble to deliberate")
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the synthesis text, not the JSON envelope",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = synthesize(args.prompt)
    if args.summary_only:
        print(result.final_synthesis)
    else:
        print(
            json.dumps(
                {
                    "tier": result.tier_classification.tier,
                    "duration_seconds": result.duration_seconds,
                    "voter_count": len(result.voter_responses),
                    "cluster_sizes": result.tier_classification.cluster_sizes,
                    "largest_cluster_fraction": result.tier_classification.largest_cluster_fraction,
                    "minority_coherent_voters": result.tier_classification.minority_coherent_voters,
                    "staging_path": result.staging_path,
                },
                indent=2,
            )
        )
        print()
        print(result.final_synthesis)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
