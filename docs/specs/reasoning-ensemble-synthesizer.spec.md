# Reasoning-Ensemble Synthesizer Spec

**Status:** ⚠️ Specified (post-hoc retrofit 2026-05-19 from existing implementation)
**Truth status:** Reflects current `FLOSS/packages/reasoning_ensemble/synthesizer.py` v0.1 behavior; promotion to Verified gated on cluster-classification accuracy data over real Tier-4 events
**Version:** 0.1.0
**Blast radius:** Module
**SDD discipline note:** Retrofit, same caveat as `reasoning-ensemble-router.spec.md` §0 — future changes MUST follow proper SDD order.

---

## 0. What this is

Partner to the Router. When the Router decides `mode=ensemble`, the Synthesizer dispatches parallel calls to ≥3 diverse voter models, embeds each response, clusters them by semantic similarity, classifies into Tier-1 (unanimous) / Tier-2 (majority + dissent) / Tier-4 (preserved divergence), applies a coherence-threshold guard against amplifying incoherent dissent, and produces a synthesized response with named tensions.

The Synthesizer makes CFIS v0.3 Tier-1/2/4 distinction operational at the reasoning-step layer.

---

## 1. Interface

### 1.1 Library function

```python
from FLOSS.packages.reasoning_ensemble.synthesizer import synthesize

result: dict = synthesize(prompt: str, voter_pool: Optional[list[dict]] = None) -> dict
```

### 1.2 CLI

```bash
python FLOSS/packages/reasoning_ensemble/synthesizer.py "<prompt>"
```

### 1.3 MCP tool (via `mcp_server.py`)

`deliberate(prompt, force_mode?)` — routes via Router; if mode=ensemble, invokes Synthesizer; otherwise returns Router decision with caller-handles-it note.

### 1.4 Result schema

```python
{
    "prompt": str,
    "prompt_hash": str,                       # 16-char SHA-256 prefix
    "timestamp": str,                         # ISO 8601 UTC
    "tier": Literal["tier1", "tier2", "tier4"],
    "voter_count": int,                       # how many voters were dispatched
    "embedded_voter_count": int,              # how many produced embeddable responses
    "cluster_assignments": dict[str, int],    # voter_id -> cluster_id
    "cluster_sizes": dict[str, int],          # cluster_id -> count
    "largest_cluster_fraction": float,        # |dominant cluster| / N
    "minority_coherent_voters": list[str],    # voters in small but coherent clusters
    "similarity_matrix": list[list[float]],   # N×N cosine matrix
    "voter_responses": list[dict],            # per-voter: voter_id, model, response, coherence_score
    "final_synthesis": str,                   # human-readable digest
    "synthesis_path": str,                    # path to durable JSON draft
}
```

---

## 2. Behavior (formal contract)

### 2.1 Voter pool resolution

Default voter pool (`DEFAULT_VOTER_POOL` constant): 4 local Ollama models spanning distinct families per ADR-Suite v2.0 voter-diversity policy.

```yaml
- voter_id: phi4-mini         model: phi4-mini:latest               family: phi
- voter_id: llama3.2-3b       model: llama3.2:3b-instruct-q4_K_S    family: llama
- voter_id: granite-code-3b   model: granite-code:3b-instruct-128k-q4_K_S    family: granite
- voter_id: qwen2.5-coder-3b  model: hf.co/.../Qwen2.5-Coder-3B-Instruct-128K-GGUF:F16    family: qwen
```

Voter pool can be overridden via `voter_pool` parameter or `FLOSS_ENSEMBLE_VOTER_POOL` env (future; not yet wired).

### 2.2 Minimum voters

`MIN_VOTERS = 3`. If fewer voters respond successfully than this threshold, the Synthesizer MUST degrade to single-strong behavior (use the most-coherent single response) and flag in the result with `tier="tier_degraded"`.

### 2.3 Parallel dispatch

All voter calls dispatched in parallel via `concurrent.futures.ThreadPoolExecutor`. Total latency ≈ slowest voter call. Per-voter timeout = `VOTER_TIMEOUT_SECONDS` (default 180).

### 2.4 Embedding

Each successful voter response embedded via mxbai-embed-large (per Router's embed model). Failed embeddings drop the voter from cluster analysis but retain the response in `voter_responses` with `coherence_score=null`.

### 2.5 Clustering (greedy, no sklearn dependency)

Pairwise cosine similarity matrix computed. Clusters formed greedily:
- Start with each voter as its own cluster
- Merge clusters when any cross-pair similarity > `CLUSTER_SIMILARITY_THRESHOLD` (default 0.75)
- Iterate until stable

### 2.6 Tier classification

| Cluster shape | Tier |
|---|---|
| All voters in one cluster | `tier1` (unanimous consensus) |
| Dominant cluster ≥ ⌈N/2⌉ voters, with dissent | `tier2` (majority + named dissent) |
| Two roughly-equal clusters OR small minority-but-coherent cluster passing the coherence guard | `tier4` (preserved divergence — highest-information event per CFIS v0.3) |

### 2.7 Coherence guard (Upgrade D from 2026-05-17 §12.5)

For Tier-4 minority clusters: surface the dissent verbatim ONLY if each voter's internal coherence proxy ≥ `COHERENCE_THRESHOLD` (default 0.6 on a 0-1 scale). Below threshold, the dissent is logged but NOT amplified in the final synthesis. *"The minority is right sometimes; the minority that can't explain itself is not."*

Coherence proxy v0.1 implementation: response length normalized + within-cluster variance check (placeholder; v0.2 will use a dedicated verifier model).

### 2.8 Required side effects

- One durable draft JSON written to `.agent-surface/reasoning/ensemble/<utc_ts>_<prompt_hash>_synthesis.json`
- One global `Action` appended to `.agent-surface/activity.jsonl` (per unified Action schema)
- Activity log entry tagged with `tier_classification` so Router's Tier-4-similarity bias can find it

### 2.9 Constraints (Plane A discipline)

- Synthesizer MUST NOT write outside `.agent-surface/reasoning/`
- Synthesizer MUST NOT auto-promote ensemble drafts to canon
- Synthesizer MUST NOT modify the prompt or voter responses
- Synthesizer MUST NOT route through the consensus gateway (that's decision-grade; ensemble is reasoning-grade)

---

## 3. Configuration

### 3.1 Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Shared with Router |
| `FLOSS_EMBED_MODEL` | `mxbai-embed-large` | Shared with Router |

### 3.2 Module-level constants

| Constant | Value | Purpose |
|---|---|---|
| `MIN_VOTERS` | 3 | Below this → degrade to single-strong |
| `VOTER_TIMEOUT_SECONDS` | 180 | Per-voter wall-clock budget |
| `EMBED_TIMEOUT_SECONDS` | 90 | Embedding call budget |
| `CLUSTER_SIMILARITY_THRESHOLD` | 0.75 | Greedy clustering join threshold |
| `COHERENCE_THRESHOLD` | 0.6 | Tier-4 dissent surfacing guard |

---

## 4. Performance contract

- **Warm-call target:** 30-90s wall-clock (slowest-voter-dominated)
- **VRAM budget:** 4 small models simultaneously loaded = ~6-8GB; mxbai-embed-large = ~1.2GB; total ~8GB. Fits comfortably in 16GB VRAM.
- **Failure mode:** if >half voters time out, return `tier_degraded` not a fake tier1

---

## 5. Activity-log integration

Every Synthesizer call appends an Action with:
- `action_id`: `ensemble-synthesis-<prompt_hash>-<ts>`
- `kind`: `reasoning_ensemble_synthesis`
- `harness`: `synthesizer.py`
- `success`: `tier != "tier_degraded"`
- `outputs.tier`: the classification
- `outputs.synthesis_path`: the durable draft location

Per `FLOSS/docs/research/2026-05-18-metaharness-unification.md` Action schema.

---

## 6. Open questions (deferred for v0.2)

1. **Graph Attention Network meta-model** for cluster-based Tier classification (per `2026-05-17` §12.3) — current greedy clustering is the v0.1 approximation. GAT requires labeled training data from accumulated activity log (~50+ Tier-4 events expected by ~end-of-v0.2).
2. **Real coherence verifier model.** v0.1 coherence proxy is length+variance heuristic; v0.2 should use a dedicated verifier prompt scored by the local Router model.
3. **Cloud voter integration via LiteLLM.** Currently local-only for cost reasons. Cloud voters would expand the voter pool but require token-budget discipline per `heartbeat-runtime-budget.spec.md`.
4. **Frame-cousin detection** (per `2026-05-17` §12.6) — voters that always co-cluster over many prompts should be flagged as frame-cousins (sharing hidden meta-assumption). Implementation in v0.2 once activity log has ≥50 ensemble calls.

---

## 7. SDD discipline going forward

Same as `reasoning-ensemble-router.spec.md` §7: spec change → failing test → code change → green test → activity-log provenance → operator-guide update.

---

## 8. Cross-refs

- **Code:** `FLOSS/packages/reasoning_ensemble/synthesizer.py`
- **Sibling spec:** `FLOSS/docs/specs/reasoning-ensemble-router.spec.md`
- **MCP wrapper spec:** `FLOSS/docs/specs/reasoning-ensemble-mcp.spec.md`
- **Architecture proposal:** `FLOSS/docs/research/2026-05-17-inline-reasoning-ensemble.md` (especially §12 v0.2 upgrades)
- **CFIS Tier-1/2/4 semantics:** `FLOSS/docs/architecture/CFIS_v0.3.md`
- **MDASH harness-over-model validation:** `FLOSS/docs/research/2026-05-16-mdash-cfis-architectural-transfer.md`
- **Consent governance:** `FLOSS/docs/adr/ADR-12-consent-gate-protocol.md`
- **Activity log schema:** `FLOSS/packages/activity_log/schema.py`
- **Operator guide:** `FLOSS/docs/architecture/RUNTIME_SURFACES.md`
- **Decision-grade peer:** `FLOSS/docs/adr/ADR-MCP-ORCHESTRATOR.md` (ADR-10)
