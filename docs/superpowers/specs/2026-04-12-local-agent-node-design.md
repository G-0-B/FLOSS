# Specification: Local Agent Node — Cell-Scoped Source Chain & Analog Vote Model

**Version:** 1.0  
**Date:** 2026-04-12  
**Status:** Approved — ready for implementation  
**Authors:** kalisam + AI session (multi-model consensus)

---

## 1. Context & Motivation

FLOSSIØULLK's long-term substrate is a Holochain DHT: sovereign agents, no global state, no master orchestrator. Every architectural decision made before Holochain is live must be forward-compatible with Holochain primitives, or it will require full rework at migration time.

This spec defines the **local agent node** — the personal, file-based representation of one sovereign agent — and the **analog vote model** that replaces the legacy ternary consensus gate. Both are designed as direct precursors to Holochain Cells and source chains, requiring no structural rework when Holochain becomes the transport layer.

### Phase 0 Blockers Addressed

- Rose Forest DNA build infra (unblocked by cell-scoped structure)
- `ConversationMemory` / `MultiScaleEmbedding` API mismatch (addressed in §6)
- ADR-0 Test #4 Human Coherence (unblocked by analog vote model)

---

## 2. Core Principles

1. **Agent-centricity**: State belongs to the agent, not the network. The agent directory IS the agent.
2. **No master orchestrator**: The MCP gateway is a router (network switch), not a controller. It routes Claims to peers; it does not command them.
3. **Asymptotic certainty**: Absolute certainty (±1.0) is a property of the Singularity, not a finite agent. `CERTAINTY_LIMIT = 0.999` is the practical bound. No vote may equal ±1.0.
4. **Variance-first tally**: High disagreement between peers is not neutrality — it is conflict. Conflict is a distinct, actionable state.
5. **Canonical serialization**: Hash stability across implementations (Python, Rust, TypeScript) requires a strict wire format.

---

## 3. Storage Substrate — Cell-Scoped Source Chain

### 3.1 Directory Structure

```
~/.floss_agent/
├── identity.json                        # Agent keypair + DID
├── registry.json                        # Known peer agents and their DIDs
└── cells/
    └── <dna_hash>/                      # One directory per network context (DNA)
        ├── head.json                    # Pointer to latest entry hash
        ├── source_chain/
        │   ├── <entry_hash>.json        # Filename IS the SHA256 of canonical content
        │   └── <entry_hash>.json
        └── memory/
            ├── working/                 # Ephemeral session context (cleared per session)
            ├── episodic/                # Rolling conversation history
            └── semantic/               # Embeddings index (per-cell scope)
```

**Key design decisions:**

- No sequential prefixes (`000001_`). Topological ordering is derived exclusively from `previous_hash` links — matching Holochain's source chain model exactly.
- Each `<dna_hash>` directory represents one Cell (agent × DNA combination). An agent participating in multiple networks has distinct, non-conflated chains.
- `memory/` is scoped per-cell to maintain context boundaries across networks.

### 3.2 Entry Schema

Every source chain entry is a JSON object with this shape:

```json
{
  "id": "<uuid-v7>",
  "type": "genesis | claim | vote | decision | memory",
  "author_did": "<did:key:z...>",
  "previous_hash": "<sha256-hex | null for genesis>",
  "timestamp": "<ISO 8601 UTC>",
  "content": { }
}
```

### 3.3 Canonical Serialization (MANDATORY)

All entries MUST be serialized via this procedure before hashing:

1. Recursively normalize all floats: reject non-finite values (NaN, ±Inf), collapse negative zero to positive zero, then round to 6 decimal places.
2. Serialize with `json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=False)`.
3. Encode as UTF-8 bytes (raw, no ASCII escaping).
4. Hash with SHA256 → hex digest → use as filename.

**Why `ensure_ascii=False`:** Python's `ensure_ascii=True` emits `\u2014` for `—`; Rust `serde_json` and most JS runtimes emit raw UTF-8 `—`. Since hash inputs must be byte-identical across languages, raw UTF-8 is the canonical form. Both sides MUST write and read UTF-8.

**Why explicit negative-zero normalization:** Python `json.dumps` serializes `-0.0` as `"-0.0"`. Rust `serde_json` normalizes `-0.0` to `"0.0"`. These produce different SHA256 digests, silently forking the chain at the first abstain-weighted vote. The `(x + 0.0)` trick collapses the IEEE 754 sign bit before serialization.

**Reference implementation (Python):**

```python
import json, math, hashlib

FLOAT_PRECISION = 6

def normalize_float(x: float) -> float:
    """Reject non-finite values; collapse -0.0 to 0.0; round to fixed precision."""
    if not math.isfinite(x):
        raise ValueError(f"Non-finite float forbidden in source chain entries: {x!r}")
    return round(x + 0.0, FLOAT_PRECISION)  # (x + 0.0) forces positive zero in IEEE 754

def normalize_val(obj):
    if isinstance(obj, float):
        return normalize_float(obj)
    if isinstance(obj, dict):
        return {k: normalize_val(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize_val(x) for x in obj]
    return obj

def canonical_serialize(data: dict) -> bytes:
    return json.dumps(
        normalize_val(data),
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,  # raw UTF-8 — do NOT escape non-ASCII as \uXXXX
        allow_nan=False,     # NaN/Inf must be caught by normalize_float before this
    ).encode('utf-8')

def entry_hash(data: dict) -> str:
    return hashlib.sha256(canonical_serialize(data)).hexdigest()
```

**Cross-language invariants — any Rust/TypeScript implementation MUST:**

- Reject NaN and ±Inf before serialization (return an error, never serialize them).
- Normalize `-0.0` to `0.0` before serialization.
- Round floats to exactly 6 decimal places using round-half-to-even (banker's rounding).
- Emit raw UTF-8 strings — do NOT escape non-ASCII code points as `\uXXXX`.
- Sort all object keys lexicographically (byte order of UTF-8 encoded key strings).

Float serialization divergence on any of these points breaks chain integrity permanently.

### 3.4 Concurrency Control

Multiple agents (Claude, Gemini, Ollama) may attempt to append to the same cell simultaneously.

**Lock protocol:**

- Before any append, acquire `cells/<dna_hash>/.lock` via atomic file creation (`O_CREAT | O_EXCL`).
- Write the new entry, update `head.json`.
- Release lock (delete `.lock`).
- Lock timeout: 5 seconds. If expired, stale lock is overwritten with warning logged.

---

## 4. Analog Vote Model

### 4.1 Weight Constraints

```
CERTAINTY_LIMIT = 0.999
valid weight w: -CERTAINTY_LIMIT ≤ w ≤ CERTAINTY_LIMIT
```

Absolute ±1.0 MUST NOT appear in any vote. It represents a limit approached asymptotically, not a reachable value. The validation layer rejects any weight outside `[-CERTAINTY_LIMIT, CERTAINTY_LIMIT]`.

### 4.2 Tally Algorithm

Given weights `W = [w₁, w₂, … wₙ]` and blast-radius thresholds:

```
μ = mean(W)
σ² = variance(W)   # population variance; 0.0 if n=1

Step 1 — Conflict check (variance, runs regardless of quorum):
  if σ² > θ_polarization[blast_radius]:
      return CONFLICT          # early conflict detection — do not wait for more votes

Step 2 — Quorum check (only if no conflict):
  if n < QUORUM_MIN[blast_radius]:
      return DEFERRED          # insufficient participants, not a decision

Step 3 — Direction check:
  if μ > θ_approve[blast_radius]:
      return APPROVED
  if μ < θ_reject[blast_radius]:
      return REJECTED
  return DEFERRED
```

**Why CONFLICT overrides quorum:** If two agents vote `[0.9, -0.9]`, a third agent breaking quorum doesn't resolve the fight — it determines a winner. Human intervention is needed before more votes are collected, not after. CONFLICT is always actionable; DEFERRED is always passive.

**Why variance before quorum:** A single dissenting agent (`n=1, weight=-0.999`) has `σ²=0.0`, so it cannot trigger CONFLICT — it produces REJECTED if below `θ_reject` or DEFERRED otherwise. The quorum gate then prevents SUBSTRATE/SYSTEM rejections from a single voice.

### 4.3 Thresholds

**Quorum minimums** (minimum votes before any direction-based decision):

| Blast Radius | Min Quorum |
|---|---|
| LOCAL | 1 |
| MODULE | 2 |
| SYSTEM | 3 |
| SUBSTRATE | 3 |

**Decision thresholds:**

| Blast Radius | θ_approve | θ_reject | θ_polarization | Override |
|---|---|---|---|---|
| LOCAL | 0.30 | -0.30 | 0.60 | yes |
| MODULE | 0.50 | -0.40 | 0.50 | yes |
| SYSTEM | 0.60 | -0.50 | 0.40 | yes |
| SUBSTRATE | 0.85 | -0.85 | 0.25 | no |

**Note on SUBSTRATE `θ_reject`:** Changed from `-0.30` to `-0.85` to mirror the approve threshold. A single agent can no longer unilaterally reject a substrate-level change by casting any weight below `-0.30`. Rejection now requires the same collective signal strength as approval (`mean < -0.85` with quorum ≥ 3).

### 4.4 Outcomes

| Outcome | Meaning | Next action |
|---|---|---|
| `APPROVED` | Consensus above threshold | Proceed, record ADR |
| `REJECTED` | Mean below reject threshold | Block, record ADR |
| `DEFERRED` | Insufficient signal | Collect more votes |
| `CONFLICT` | High variance — deep disagreement | Route to human |
| `OVERRIDDEN` | Human override of DEFERRED | Proceed with human rationale |

### 4.5 Migrating from Ternary Tests

Legacy ternary values map as follows for test rewriting:

| Old | New |
|-----|-----|
| `+1` | `+CERTAINTY_LIMIT` (`+0.999`) |
| `0` | `0.0` |
| `-1` | `-CERTAINTY_LIMIT` (`-0.999`) |

No test may use exact `1.0` or `-1.0`.

---

## 5. MCP Gateway — Router, Not Controller

### 5.1 Role

The MCP gateway is a **network switch**. It:

- Accepts Claims from any agent (Claude Code hooks, CLI, OpenCode)
- Reads the cell source chain to provide context to voters
- Notifies registered voters (Claude, Gemini, Ollama) that a Claim awaits
- Appends votes to the source chain as they arrive
- Triggers tally when quorum is reached or timeout expires

It does NOT:

- Decide outcomes
- Command voters
- Prioritize one model over another
- Hold state outside the cell directory

### 5.2 MCP Tools Exposed

| Tool | Description |
|---|---|
| `submit_claim` | Append a Claim entry to the source chain |
| `cast_vote` | Append a Vote entry for a given claim_id |
| `get_chain_context` | Return recent source chain entries (bounded by token budget) |
| `get_decision` | Return the Decision for a given claim_id |
| `list_pending` | List Claims with no Decision yet |

### 5.3 Claude Code Hook Integration

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "agent",
        "prompt": "Inspect the changed file. If the change is structural (modifies DNA, integrity zome, ADR, or spec), submit a Claim to the MCP consensus gateway with the appropriate blast_radius. For LOCAL changes, submit silently and continue.",
        "model": "claude-haiku-4-5-20251001",
        "timeout": 30,
        "async": true
      }]
    }]
  }
}
```

Blast radius auto-detection heuristic:

- `ARF/dnas/*/zomes/integrity/` → SUBSTRATE
- `ARF/dnas/*/` → SYSTEM  
- `docs/adr/` or `docs/specs/` → MODULE
- Everything else → LOCAL

---

## 6. Phase 0 Blocker: ConversationMemory API Mismatch

**Root cause:** `conversation_memory.py` references `DEFAULT_EMBEDDING_LEVEL` without defining it.

**Fix (one line, in `conversation_memory.py` near other constants):**

```python
DEFAULT_EMBEDDING_LEVEL = 'default'
```

This unblocks `MultiScaleEmbedding.add()` calls. No other API changes required — `MultiScaleEmbedding.add(key, vector: np.ndarray, level, metadata)` already accepts the numpy arrays that `SentenceTransformer.encode()` returns.

---

## 7. PR #25 Hygiene — Blocking Items

> **Relocation note (2026-05-11):** The `FLOSSI_U_Founding_Kit_v1.6/` directory has been relocated to `C:\~shit\FLOSSI_U/` at workspace top-level — it is a separate sibling project (Free YOU-niversity), not part of the FLOSS / Rose Forest repo. The PR #25 plan below assumed co-location; references below now point to the new location. Whether ADR-017 and LICENSE are still PR #25 blockers depends on whether PR #25 needs FLOSSI U artifacts at all, given the project separation. **Re-plan needed before proceeding.**

### ADR-017 (`../FLOSSI_U/ADR-017_SELF_TRANSCENDENCE_OPERATOR.md`)

Current file is a 10-line stub. Missing required sections: Context, Consequences, Validation Criteria. Must be expanded to full ADR template before merge. **Note:** now lives in FLOSSI U's separate canon; FLOSS PR #25 may no longer require it.

### LICENSE (`../FLOSSI_U/LICENSE`)

Current: `AGPL-3.0 + Carrier Equivalence` (not a valid SPDX identifier).  
Fix:

- `LICENSE` → `SPDX-License-Identifier: AGPL-3.0-or-later`
- Create `LEGAL_DEFINITIONS.md` → Carrier Equivalence addendum text

---

## 8. Implementation Sequence

Phase 0 uses a Fast-Path / Core-Logic / Physical three-track pipeline. The Fast-Path tracks are parallel; the Core-Logic and Physical tracks are strictly sequential with hard gates between them.

### Fast-Path (run in parallel, no dependencies between tracks)

| Step | Task | Time |
|------|------|------|
| F1 | **Fix `DEFAULT_EMBEDDING_LEVEL`** in `conversation_memory.py` — unblocks ConversationMemory | 30 min |
| F2 | **Implement `canonical_serialize` + `entry_hash`** in `packages/orchestrator/` per §3.3 | 2h |
| F3 | **Fix PR #25 hygiene** — ADR-017 full template + LICENSE SPDX fix | 1h |

F1, F2, and F3 have no shared state. Start all three simultaneously. F2 must fully implement the negative-zero normalization, NaN/Inf rejection, and `ensure_ascii=False` rules in §3.3 before it is considered complete.

### Core-Logic Path (strictly sequential — each step is a hard gate for the next)

| Step | Task | Gate condition | Time |
|------|------|----------------|------|
| C1 | **Refactor `claim_schema.py`** — replace `vote: int` with `weight: float`, add CONFLICT to `Outcome` enum | F2 complete | 3h |
| C2 | **Rewrite 16 tests** — replace ternary values with analog weights, add CONFLICT and variance-boundary test vectors | C1 complete | 2h |

C2 is a hard gate: all 16 tests (plus new CONFLICT vectors) must pass before the Physical Path begins. Rationale: the cell directory writer (P1) writes entries whose hashes are computed by `canonical_serialize`. If the analog schema or tally math is wrong at C2, every entry written in P1 will have a corrupt or incorrect hash. There is no recovery path for a poisoned source chain.

### Physical Path (strictly sequential — each step gates the next)

| Step | Task | Gate condition | Time |
|------|------|----------------|------|
| P1 | **Implement cell directory writer** — `packages/source_chain/` | C2 passing | 3h |
| P2 | **Build MCP gateway** — `packages/metacoordinator_mcp/` | P1 complete | 4h |
| P3 | **Wire Claude Code hooks** — `.claude/settings.json` | P2 complete | 1h |

---

## 9. What This Is NOT

- Not a master orchestrator
- Not a daemon that must be running for the agent to exist
- Not a vendor lock-in (every voter is a peer, any model can be swapped)
- Not final — when Holochain is live, each file becomes a source chain action with zero structural rework
