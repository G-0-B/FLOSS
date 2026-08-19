# Reasoning-Ensemble Router Spec

**Status:** ⚠️ Specified (post-hoc retrofit 2026-05-19 from existing implementation)
**Truth status:** Reflects current `FLOSS/packages/reasoning_ensemble/router.py` v0.1.1 behavior; promotion to Verified gated on test suite expansion + multi-day pilot data
**Version:** 0.1.0
**Blast radius:** Module (changes affect this package + its MCP wrapper + the skill counterpart; do not affect substrate or canon)
**SDD discipline note:** This spec is a **retrofit** — code preceded spec, in violation of `FLOSS/SDD-Master-Spec-0.22.md`. User flagged this 2026-05-19. The spec is being authored now from the existing code, with the code's behavior frozen as the spec's claim. Future changes to the Router MUST follow the proper SDD order (spec change → failing test → code change → green test).

---

## 0. What this is

A local-model prompt classifier that decides whether each substantive reasoning step in a FLOSSI0ULLK agent session needs `pass_through` / `single_strong` / `ensemble` routing. The Router is the cheap front gate of the Inline Reasoning Ensemble (Reference: `FLOSS/docs/research/2026-05-17-inline-reasoning-ensemble.md`).

The Router does NOT execute the reasoning itself. It produces a structured decision that the caller acts on:
- Caller routes its own work to a single cheap model if `pass_through`
- Caller routes its own work to a single capable model if `single_strong`
- Caller invokes the Synthesizer (`FLOSS/packages/reasoning_ensemble/synthesizer.py`) if `ensemble`

---

## 1. Interface

### 1.1 Library function

```python
from FLOSS.packages.reasoning_ensemble.router import classify, RouterDecision

decision: RouterDecision = classify(
    prompt: str,
    force_mode: Optional[Literal["pass_through", "single_strong", "ensemble"]] = None,
) -> RouterDecision
```

### 1.2 CLI

```bash
python FLOSS/packages/reasoning_ensemble/router.py [--test|--force MODE] [PROMPT]
```

### 1.3 MCP tool (via `mcp_server.py`)

```
route_prompt(prompt: str, force_mode: str | None = None) -> str  # JSON
```

### 1.4 RouterDecision schema

```python
@dataclass
class RouterDecision:
    mode: Literal["pass_through", "single_strong", "ensemble"]
    reason: str                              # ≤400 chars; one-sentence justification
    confidence: float                        # 0.0–1.0; classifier self-assessment
    prompt_hash: str                         # 16-char SHA-256 prefix of prompt
    model: str                               # which Router model produced this decision
    embed_model: str                         # which embedding model was used (or "n/a")
    timestamp: str                           # ISO 8601 UTC
    duration_seconds: float                  # wall-clock from classify() entry
    bias_applied: Optional[str]              # None | "tier4_similarity" | "force_flag" | "fallback_on_error"
    similar_prior_prompt_hash: Optional[str] # if tier4_similarity bias applied
    similar_prior_similarity: Optional[float]# cosine similarity that triggered the bias
    raw_model_output: Optional[str]          # truncated raw Router response for debug
```

---

## 2. Behavior (formal contract)

### 2.1 Mode definitions

| Mode | Trigger condition | Examples |
|---|---|---|
| `pass_through` | Trivial lookup, file read, format conversion, simple recall, status check, acknowledgment | "Read line 47 of foo.py", "Reformat this JSON", "Sum these numbers", "ack" |
| `single_strong` | Standard reasoning, single-file code edit, routine synthesis, explanation, light reasoning | "Explain this regex", "Write a test for parse_url", "Fix the bug on line 142" |
| `ensemble` | Substantive reasoning, multi-file refactor, architectural decision, ADR-class move, anything with rollback cost | "Refactor auth to OAuth2 across 5 files", "Should we switch consensus to weighted analog?", "Propose an ADR for threat model" |

### 2.2 Decision precedence (highest → lowest)

1. **`force_mode` argument** → bypasses classifier; returns immediately with `bias_applied="force_flag"`, confidence=1.0
2. **Tier-4 similarity bias** (Upgrade A) → if `prompt_embedding` is similar to any past activity-log entry with `tier_classification="tier4"` above `TIER4_SIMILARITY_THRESHOLD` (default 0.70), force `ensemble` with `bias_applied="tier4_similarity"`, confidence 0.85
3. **Router model classification** → invoke local Router model (default `phi4-mini:latest`), parse JSON response
4. **Fallback** → if any of (1)-(3) fail, return `single_strong` with confidence 0.3 and `bias_applied="fallback_on_error"`

### 2.3 Required side effects

- Every call MUST append a single JSON line to `.agent-surface/reasoning/activity.jsonl` containing the full RouterDecision + `prompt_preview` (≤200 chars of prompt) + `prompt_embedding` (if obtained).
- Activity log append MUST be best-effort (does not raise on OS error).
- If embedding succeeded, the embedding MUST be included for future Upgrade-A lookups.

### 2.4 Required validation

- `mode` MUST be one of the three valid strings; coerce to `single_strong` if invalid
- `confidence` MUST be a float in [0.0, 1.0]
- `force_mode` MUST be one of the three valid strings if supplied; raises ValueError otherwise

### 2.5 Constraints (Plane A discipline)

- Router MUST NOT write outside `.agent-surface/reasoning/`
- Router MUST NOT invoke any cloud API in the routing decision path (Ollama HTTP only)
- Router MUST NOT depend on the consensus gateway being available
- Router MUST NOT alter canonical documents
- Router MUST NOT modify the prompt before classification

---

## 3. Configuration

### 3.1 Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama HTTP endpoint. **Must use `127.0.0.1` not `localhost`** on Windows (Python urllib IPv6-first quirk) |
| `FLOSS_ROUTER_MODEL` | `phi4-mini:latest` | Router model name as known to Ollama. Set `gemma3:12b-it-qat` for stronger but slower fallback |
| `FLOSS_EMBED_MODEL` | `mxbai-embed-large` | Embedding model for prompt similarity (Upgrade A) |

### 3.2 Module-level constants (require code change to override)

| Constant | Value | Purpose |
|---|---|---|
| `ACTIVITY_LOOKBACK` | 10 | How many past activity-log entries to scan for Tier-4 similarity bias |
| `TIER4_SIMILARITY_THRESHOLD` | 0.70 | Cosine similarity above which adjacent Tier-4 forces ensemble mode |
| `ROUTER_TIMEOUT_SECONDS` | 120 | Wall-clock budget for Router model call (cold-start tolerance) |
| `EMBED_TIMEOUT_SECONDS` | 90 | Wall-clock budget for embedding call |

---

## 4. Performance contract

- **Warm-call target:** ≤10s on RTX 4090 Laptop (16GB VRAM) with phi4-mini resident in VRAM
- **Cold-start tolerance:** ≤60s for first call after Ollama server start
- **No-bias path:** classifier-only, ~10s warm
- **Bias path:** embedding + similarity scan + (early-return ensemble), ~5-15s warm (no Router call)
- **Failure path:** fallback to single_strong, <2s

If sustained warm-call latency exceeds 15s, the operator should consider switching Router model (env var `FLOSS_ROUTER_MODEL`) or ensure Ollama keeps the model resident (Ollama default keep-alive is 5min idle).

---

## 5. Calibration evidence

Per multi-day calibration runs documented in working-todo §A.6 + §I:

| Router model | Sample | Accuracy | Latency (warm) |
|---|---|---|---|
| `gemma3:12b-it-qat` | 11 cases | 11/11 = 100% | 40-87s (CPU/GPU split due to 16GB VRAM tightness) |
| `phi4-mini:latest` | 11 cases | 10/11 = 91% | ~10s |

Single miss for phi4-mini: borderline pass_through↔single_strong case (regex explanation). All ensemble cases correctly identified. Phi4-mini chosen as v0.1 default for latency.

---

## 6. Open questions (deferred for v0.2)

1. **Cluster-based Tier classification in the Router itself.** Currently Router only classifies the prompt; the Synthesizer does Tier-1/2/4 cluster classification on voter responses. Should the Router pre-classify the prompt by "type of question" (factual / architectural / ethical / etc.) to inform Synthesizer behavior? Per `2026-05-17-inline-reasoning-ensemble.md` §12.3, the Synthesizer's cluster-based Tier classification is the load-bearing v0.2 upgrade — the Router stays simple.
2. **Multi-stream parallel auditing** (Upgrade C / `2026-05-17` §12.4) — Router would not know if a within-model audit-stream was active. Out of scope for v0.1.
3. **Persistent VRAM keep-alive** — current Ollama default 5-minute keep-alive sometimes evicts the Router model during quiet sessions, forcing cold-start re-load. Consider env-var configurable keep-alive longer than expected idle.

---

## 7. SDD discipline going forward (binding for future Router changes)

Any change to Router behavior MUST:

1. Update this spec FIRST (new section or revised contract clause)
2. Write a failing test under `FLOSS/packages/reasoning_ensemble/tests/test_router.py` against the new spec
3. Change `router.py` to make the test pass
4. Run `pytest FLOSS/packages/reasoning_ensemble/tests/ -q` and confirm green
5. Append durable provenance to `.agent-surface/activity.jsonl`
6. Update `FLOSS/docs/architecture/RUNTIME_SURFACES.md` if operator-visible behavior changed

---

## 8. Cross-refs

- **Code:** `FLOSS/packages/reasoning_ensemble/router.py`
- **Sibling spec:** `FLOSS/docs/specs/reasoning-ensemble-synthesizer.spec.md`
- **MCP wrapper spec:** `FLOSS/docs/specs/reasoning-ensemble-mcp.spec.md`
- **Architecture proposal:** `FLOSS/docs/research/2026-05-17-inline-reasoning-ensemble.md`
- **Empirical validation:** `FLOSS/docs/research/2026-05-16-mdash-cfis-architectural-transfer.md`
- **Epistemic substrate:** `FLOSS/docs/architecture/CFIS_v0.3.md`
- **Consent governance:** `FLOSS/docs/adr/ADR-12-consent-gate-protocol.md`
- **Operator guide:** `FLOSS/docs/architecture/RUNTIME_SURFACES.md`
- **SDD master spec:** `FLOSS/SDD-Master-Spec-0.22.md` (the doctrine this retrofit honors)
- **Unification context:** `FLOSS/docs/research/2026-05-18-metaharness-unification.md`
- **Token-budget peer:** `FLOSS/docs/specs/heartbeat-runtime-budget.spec.md`
