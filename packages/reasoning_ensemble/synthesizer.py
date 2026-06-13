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
- Decision-grade peer: `docs/adr/ADR-MCP-ORCHESTRATOR.md` (ADR-10
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

v0.1 voter pool: local Ollama models only (gemma3:12b-it-qat, phi4-mini,
qwen2.5-coder-3b, llama3.1, llama3.2) for $0 cost and no rate limits. Cloud
voters via LiteLLM are Later — same shape, different transport.

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
from dataclasses import dataclass, field, asdict
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

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
ENSEMBLE_STAGING = WORKSPACE_ROOT / ".agent-surface" / "reasoning" / "ensemble"

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.environ.get("FLOSS_EMBED_MODEL", "mxbai-embed-large")

# v0.1 default voter pool. All local. ~$0 cost. Each is a distinct family,
# satisfying the ≥3 providers / ≥4 model families diversity policy (where
# "provider" is the model family lineage, not the inference host).
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

# Cluster-similarity threshold for grouping voter responses into the same cluster.
# Cosine similarity > THRESHOLD → same cluster.
# Calibrated based on mxbai-embed-large semantic similarity for related-but-distinct
# answers. 0.75 = "saying basically the same thing"; 0.85 = "near-paraphrase."
CLUSTER_SIMILARITY_THRESHOLD = 0.75

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


def ollama_embed(text: str) -> list[float]:
    """Get a 1024-d mxbai embedding for text. Raises on failure."""
    response = _ollama_request(
        "/api/embeddings",
        {"model": EMBED_MODEL, "prompt": text},
        timeout=EMBED_TIMEOUT_SECONDS,
    )
    emb = response.get("embedding", [])
    if not emb:
        raise RuntimeError(f"Empty embedding from {EMBED_MODEL}")
    return emb


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


def _dispatch_voter(voter: dict, prompt: str) -> VoterResponse:
    """Call one voter. Wraps errors into the response. Never raises."""
    started = time.perf_counter()
    try:
        text = ollama_generate(voter["model"], prompt)
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
            )
        # Embed in this voter's thread to keep things parallel-friendly
        try:
            emb = ollama_embed(text)
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
        )
    except (
        urllib.error.URLError,
        RuntimeError,
        json.JSONDecodeError,
        TimeoutError,
    ) as e:
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
        )


def dispatch_parallel(voter_pool: list[dict], prompt: str) -> list[VoterResponse]:
    """Fan out to all voters in parallel via ThreadPoolExecutor.

    Ollama serializes GPU access internally (single-model loading + queuing),
    so true parallelism is partial. But submitting all calls simultaneously
    lets Ollama overlap embed + generate for different models, which is
    better than strict-serial.
    """
    voter_prompt = _build_voter_prompt(prompt)
    responses: list[VoterResponse] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(voter_pool)) as executor:
        futures = {
            executor.submit(_dispatch_voter, v, voter_prompt): v for v in voter_pool
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
    voter_to_idx = {r.voter_id: i for i, r in enumerate(responses)}

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

    return TierClassification(
        tier=tier,
        cluster_assignments=assignments,
        cluster_sizes=cluster_sizes,
        largest_cluster_id=largest_cid,
        largest_cluster_fraction=round(largest_fraction, 3),
        minority_coherent_voters=minority_coherent_voters,
        similarity_matrix=[[round(v, 3) for v in row] for row in similarity],
    )


# ---------------------------------------------------------------------------
# Synthesis writeup
# ---------------------------------------------------------------------------


def write_synthesis(
    prompt: str, responses: list[VoterResponse], tier_class: TierClassification
) -> str:
    """Produce the human-readable synthesis. Tier-aware formatting."""
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
    lines.append("")
    lines.append(
        f"**Voters:** {len(responses)} ({', '.join(r.family for r in responses)})"
    )
    lines.append(
        f"**Largest cluster:** {len(largest_cluster_voters)}/{len(responses)} "
        f"({100 * tier_class.largest_cluster_fraction:.0f}%)"
    )
    lines.append("")

    if tier_class.tier == "tier1":
        lines.append("## Unanimous consensus")
        lines.append("")
        # Pick the most coherent / longest response from the cluster as the synthesis
        rep = max(
            (voter_by_id[v] for v in largest_cluster_voters),
            key=lambda r: len(r.response),
        )
        lines.append(f"> {rep.response}")
        lines.append("")
        lines.append(
            f"_(Representative voter: {rep.voter_id} / {rep.family} family. "
            f"All {len(responses)} voters converged.)_"
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
                lines.append(f"")
                lines.append(f"**{v.voter_id} / {v.family}:**")
                lines.append(f"> {v.response}")
        elif minority_voters:
            lines.append(
                f"_(Minority voters {', '.join(minority_voters)} dissented but "
                "their responses failed the coherence guard — "
                "logged to activity log but not surfaced.)_"
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
    """Run the full ensemble: voters → embed → cluster → tier → synthesize."""
    pool = voter_pool or DEFAULT_VOTER_POOL
    if len(pool) < MIN_VOTERS:
        raise ValueError(f"Voter pool too small: {len(pool)} < {MIN_VOTERS}")

    started_iso = utc_iso()
    started_perf = time.perf_counter()
    p_hash = prompt_hash(prompt)

    # 1-3: dispatch + embed (embed is inside _dispatch_voter)
    responses = dispatch_parallel(pool, prompt)

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
    final = write_synthesis(prompt, embedded, tier_class)

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
            "provider": "ollama-local",
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
