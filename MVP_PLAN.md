# FLOSSI0ULLK Rose Forest — MVP Plan

```yaml
id: "flossi0ullk-mvp-plan"
version: "0.1.0"
kind: "implementation_plan"
status: "Proposed"
updated: "2026-03-25"
truth_status: "Specified"
evidence_sources:
  - "Master Metaprompt v1.3.1 (governance)"
  - "SDD-Master-Spec-0.22 (architecture)"
  - "ARF/dnas/rose_forest/ (412 LOC Rust, tested)"
  - "ARF/conversation_memory.py (503 LOC Python, 3/4 tests)"
  - "All ADRs (0, 0.1, 1, 2, 3, 4, 5)"
  - "SYMBOLIC_FIRST_CORE.md (878 lines specification)"
  - "docs/specs/ (6 entry types, 5 JSON schemas, phase0 bridge spec)"
  - "Orchestration Landscape Report v2.0.0 (Silo-Bench, MAS-ProVe constraints)"
rollback_plan: "Each phase ships independently; any phase can stall without breaking prior phases"
```

---

Current phase-status note (2026-05-18): MVP Phase 0 substrate viability is complete: DNA compiles to WASM, Holochain hApp/Tryorama integration tests pass, and ontology integrity unit tests pass. Do not confuse this with the separate orchestration substrate-bridge validation in `docs/specs/phase0-substrate-bridge.spec.md`, which remains Specified until publish/provenance/independent-verify/fork-visible criteria are executed and logged.

## The Honest State of Things

### What's REAL (verified, tested, working)
| Component | LOC | Tests | Evidence |
|-----------|-----|-------|----------|
| Vector operations (cosine, distance, normalize) | 117 Rust | 6/6 pass | `vector_ops.rs` |
| Budget engine (RU accounting, 24h windows) | 86 Rust | compiles | `budget.rs` |
| Integrity zome (4 entry types, 5 validators) | 113 Rust | compiles | `integrity/lib.rs` |
| Coordinator zome (5 extern functions) | 100 Rust | compiles | `coordinator/lib.rs` |
| ConversationMemory (cross-AI context) | 503 Python | 3/4 pass | `conversation_memory.py` |
| Fractal embeddings (multi-scale) | ~150 Python | in use | `embedding_frames_of_scale.py` |
| flake.nix (Holochain 0.4 dev env) | 37 Nix | boots | `flake.nix` |
| 5 entry type specs + 4 JSON schemas | ~500 lines | reviewed | `docs/specs/` |
| 8 ADRs with clear status labels | ~1200 lines | reviewed | `docs/adr/` |
| Governance stack (kernel, spine, seed packet) | ~800 lines | in use | `docs/governance/` |

### What's SPECIFIED but not built
- Full symbolic-first validation (SYMBOLIC_FIRST_CORE.md — 878 lines of spec)
- Logical inference engine (Horn clause unification)
- Ontology bootstrap system
- LLM extraction pipeline with validator consensus
- KERI/ACDC identity integration
- Proof-carrying code

### ~~The #1 blocker~~ RESOLVED
~~**The Holochain DNA has never compiled to WASM or run in a conductor.**~~

**Phase 0 is COMPLETE.** The DNA compiled to WASM and all tests pass. The round-trip test timed out on first run but passed on second.

Architectural cleanup performed:
- `sharding.rs`, `crdt.rs`, `versioning.rs` removed (Holochain handles these natively)
- `ShardMember` and `AgentBudget` link types removed from integrity zome

The `ontology_integrity` zome now has **38 passing unit tests** and should be fast-tracked into Phase 1.

---

## MVP Definition

**The MVP is: A single-agent Holochain hApp that can store, validate, search, and link knowledge nodes with provenance — demonstrating that symbolic-first validation works on a decentralized substrate.**

Success criteria:
1. ✅ DNA compiles to WASM
2. ✅ hApp installs in Holochain conductor
3. ✅ Can create a RoseNode (validated: license, embedding dims, model card)
4. ✅ Can create a KnowledgeEdge (validated: confidence bounds, relationship whitelist)
5. ✅ Can perform vector_search (cosine similarity, returns top-k)
6. ✅ Budget system enforces 100 RU/day limit
7. ✅ ThoughtCredential creation with ternary connotation
8. ✅ All operations leave full provenance trail on source chain
9. ✅ Tryorama integration tests pass for all 5 extern functions

**NOT in MVP**: Multi-agent coordination, LLM extraction pipeline, logical inference, KERI, AD4M, hREA, self-modification. These are LATER.

---

## Phase 0: Substrate Viability Spike (COMPLETE)

**Goal**: Get the existing Rust code compiling to WASM and running in a real Holochain conductor.

**Status**: COMPLETE as of 2026-03-20. DNA compiles to WASM, all integration tests pass. Round-trip test timed out on first run but passed on second. Architectural cleanup: `sharding.rs`, `crdt.rs`, `versioning.rs` removed (Holochain handles these natively); `ShardMember` and `AgentBudget` link types removed from integrity zome.

### Step 0.1: Fix build environment
```bash
# Enter nix shell (WSL2 required on Windows)
nix develop
# Verify toolchain
rustup target add wasm32-unknown-unknown
cargo build --release --target wasm32-unknown-unknown
```

**Likely issues to resolve**:
- hdi 0.5.1 / hdk 0.4.1 version compatibility with holonix main-0.4
- WASM target may expose issues not caught by `cargo test --lib`
- Path dependencies may need adjustment for WASM build

### Step 0.2: Pack DNA and hApp
```bash
hc dna pack dnas/rose_forest/workdir/
hc app pack workdir/
```

**Requires**: `dna.yaml` and `happ.yaml` manifest files in workdir directories.

### Step 0.3: Tryorama integration tests — ALREADY WRITTEN ✅

`tests/tryorama/rose_forest.test.ts` already contains **363 lines** covering:
- RoseNode: create, vector_search (multi-agent with DHT sync), reject invalid license, reject missing model_card
- KnowledgeEdge: link_edge between nodes, reject invalid relationship type
- BudgetEntry: initial 100 RU, consumption tracking (33 RU per node), budget exhaustion at 4th node
- ThoughtCredential: create with valid input, reject out-of-range connotation, reject undersized embedding

No new tests needed for Phase 0 — just make the existing ones pass.

### Step 0.4: Run integration tests
```bash
cd tests/tryorama && npm install && npm test
```

**Phase 0 exit criteria**: All 6+ integration tests pass. DNA compiles, installs, validates, and returns correct results.

**If Phase 0 fails**: Document why. Consider: (a) version bump hdi/hdk, (b) simplify zome code, (c) pivot to different Holochain version, (d) worst case: evaluate alternative substrate per ADR-2.

---

## Phase 1: KnowledgeTriple + Ontology (Symbolic-First Core)

**Goal**: Add the KnowledgeTriple entry type with ontology validation — the heart of symbolic-first architecture.

**Why**: RoseNode is a general-purpose blob. KnowledgeTriple is structured knowledge with formal semantics. This is the difference between a document store and a knowledge graph.

> **Fast-track note:** `ontology_integrity` already has 38 passing unit tests from Phase 0 cleanup. This gives Phase 1 a significant head start — the ontology validation foundation is already proven.

### Step 1.1: Add KnowledgeTriple to integrity zome

From `SYMBOLIC_FIRST_CORE.md` spec + `knowledge-triple.spec.md`:

```rust
// integrity/src/lib.rs — add to EntryTypes enum
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct KnowledgeTriple {
    pub subject: String,        // Entity URI or DHT hash
    pub predicate: String,      // Must exist in ontology
    pub object: String,         // Entity or literal
    pub confidence: f32,        // [0.0, 1.0]
    pub derivation: TripleDerivation,
    pub license: String,
    pub embedding: Option<Vec<f32>>,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub enum TripleDerivation {
    HumanAsserted { agent: AgentPubKey, timestamp: Timestamp },
    LogicalInference { rule_id: String, premises: Vec<ActionHash> },
    LLMExtracted { model: String, prompt_hash: String, validator_agents: Vec<AgentPubKey> },
    Empirical { method: String, measurement_hash: String },
}
```

### Step 1.2: Add OntologyRelation entry type

```rust
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct OntologyRelation {
    pub name: String,
    pub domain: Vec<String>,    // Valid subject types
    pub range: Vec<String>,     // Valid object types
    pub is_transitive: bool,
    pub is_symmetric: bool,
}
```

### Step 1.3: Validation — predicate must exist in ontology

```rust
fn validate_knowledge_triple(triple: &KnowledgeTriple) -> ExternResult<ValidateCallbackResult> {
    // Confidence bounds
    if !(0.0..=1.0).contains(&triple.confidence) {
        return Ok(ValidateCallbackResult::Invalid("E_CONFIDENCE".into()));
    }
    // License check (same as RoseNode)
    // LLM extractions must have 3+ validators
    if let TripleDerivation::LLMExtracted { validator_agents, .. } = &triple.derivation {
        if validator_agents.len() < 3 {
            return Ok(ValidateCallbackResult::Invalid("E_LLM_VALIDATORS: need 3+".into()));
        }
    }
    // NOTE: Ontology predicate validation requires DHT lookup —
    // must be done in coordinator, not integrity (integrity can't do gets)
    Ok(ValidateCallbackResult::Valid)
}
```

### Step 1.4: Coordinator — assert_triple + query_triple

```rust
#[hdk_extern]
pub fn assert_triple(input: AssertTripleInput) -> ExternResult<ActionHash> {
    // 1. Verify predicate exists in ontology (DHT lookup)
    // 2. Verify domain/range constraints
    // 3. Create entry (integrity zome validates bounds)
    // 4. Optionally compute embedding for search
    // 5. Link to indexes
}

#[hdk_extern]
pub fn query_triples(input: TripleQuery) -> ExternResult<Vec<KnowledgeTriple>> {
    // Pattern matching: ?subject ?predicate ?object
    // Return matching triples with provenance
}
```

### Step 1.5: Bootstrap ontology

Create initial ontology relations via coordinator function:

```rust
#[hdk_extern]
pub fn bootstrap_ontology(_: ()) -> ExternResult<Vec<ActionHash>> {
    let relations = vec![
        OntologyRelation { name: "is_a".into(), domain: vec!["Entity".into()], range: vec!["Type".into()], is_transitive: true, is_symmetric: false },
        OntologyRelation { name: "supports".into(), domain: vec!["Claim".into()], range: vec!["Claim".into()], is_transitive: false, is_symmetric: false },
        OntologyRelation { name: "contradicts".into(), domain: vec!["Claim".into()], range: vec!["Claim".into()], is_transitive: false, is_symmetric: true },
        OntologyRelation { name: "authored_by".into(), domain: vec!["Artifact".into()], range: vec!["Agent".into()], is_transitive: false, is_symmetric: false },
        OntologyRelation { name: "derived_from".into(), domain: vec!["Artifact".into()], range: vec!["Artifact".into()], is_transitive: true, is_symmetric: false },
    ];
    // Create entries and return hashes
}
```

**Phase 1 exit criteria**: Can create ontology relations, assert triples against them, query triples by pattern, and LLM-extracted triples are rejected without 3+ validators.

---

## Phase 2: Real Embeddings + ConversationMemory Bridge

**Goal**: Replace mock embeddings and bridge the Python ConversationMemory with the Holochain DNA.

### Step 2.1: Replace mock embeddings in ConversationMemory
```python
# Replace hash-based projection with real model
from sentence_transformers import SentenceTransformer

class ConversationMemory:
    def __init__(self, agent_id, storage_path=None):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dims
        # ... rest of init

    def _encode_text(self, text):
        return self.model.encode(text).tolist()
```

### Step 2.2: Fix MultiScaleEmbedding API mismatch
The `from_dict()` method is missing — ConversationMemory can't restore embedding state from disk.

### Step 2.3: Holochain client bridge
```python
# Bridge ConversationMemory to Rose Forest DNA
from holochain_client import AppAgentClient

class HolochainBridge:
    def __init__(self, app_port=8888):
        self.client = AppAgentClient(port=app_port)

    async def store_understanding(self, understanding):
        """Store an Understanding as a RoseNode in Holochain"""
        return await self.client.call_zome(
            zome_name="coordinator",
            fn_name="add_knowledge",
            payload={
                "content": understanding.content,
                "embedding": understanding.embedding_ref,
                "license": "Apache-2.0",
                "metadata": {
                    "model_id": "all-MiniLM-L6-v2",
                    "model_card_hash": "sha256:...",
                    "agent_id": understanding.agent_id,
                    "timestamp": understanding.timestamp,
                }
            }
        )
```

**Phase 2 exit criteria**: ConversationMemory uses real embeddings (384-dim), recall quality improves measurably, and Understandings can be persisted to Holochain (not just local JSON).

---

## Phase 3: Multi-Agent + Tryorama Full Suite

**Goal**: Two agents coordinating knowledge through the Rose Forest DNA.

### Step 3.1: Two-agent Tryorama test
```typescript
test("two agents share knowledge via DHT", async () => {
  await runScenario(async (scenario) => {
    const [alice, bob] = await scenario.addPlayersWithApps([
      { appBundleSource: { path: "workdir/rose-forest.happ" } },
      { appBundleSource: { path: "workdir/rose-forest.happ" } },
    ]);

    // Alice creates a knowledge node
    const nodeHash = await alice.cells[0].callZome({
      zome_name: "coordinator", fn_name: "add_knowledge",
      payload: { /* ... */ }
    });

    await dhtSync([alice, bob], alice.cells[0].cell_id[0]);

    // Bob can search and find Alice's node
    const results = await bob.cells[0].callZome({
      zome_name: "coordinator", fn_name: "vector_search",
      payload: { query_embedding: [/* similar vector */], k: 5 }
    });

    expect(results.length).toBeGreaterThan(0);
    expect(results[0].content).toBe("Alice's knowledge");
  });
});
```

### Step 3.2: Budget isolation test
Verify Alice's budget is independent of Bob's — each agent gets 100 RU/day.

### Step 3.3: Edge linking across agents
Alice creates a node, Bob creates a supporting edge to it.

**Phase 3 exit criteria**: Two agents can create, share, search, and link knowledge. Budget is per-agent. DHT sync works.

---

## What's NOT in the MVP (and why)

| Component | Why NOT now | When |
|-----------|------------|------|
| Logical inference engine | Requires stable ontology + triple base first | Phase 4 |
| LLM extraction pipeline | Requires 3+ validator agents (need multi-agent first) | Phase 4 |
| KERI/ACDC identity | Adds complexity without MVP value | Phase 5 |
| AD4M integration | Requires stable semantic layer | Phase 6 |
| hREA economic layer | Requires stable agent layer | Phase 6 |
| Proof-carrying code | Research-grade; not blocking any user value | Phase 7 |
| Self-modification | Requires all above + governance maturity | Phase 8+ |

---

## Timeline (Honest Estimates)

| Phase | Effort | Blocker | Confidence |
|-------|--------|---------|------------|
| **0: Substrate spike** | COMPLETE | — | 100% (done) |
| **1: KnowledgeTriple + ontology** | 2-3 weeks | Depends on Phase 0 | 80% (spec is complete) |
| **2: Real embeddings + bridge** | 1-2 weeks | sentence-transformers install, holochain-client API | 90% (well-understood) |
| **3: Multi-agent tests** | 1-2 weeks | DHT sync timing in tests | 75% (Tryorama can be finicky) |

**Total to MVP**: ~5-9 weeks of focused work.

---

## Architectural Constraints (from v2.0.0 Landscape Report)

These constraints are empirically derived and must inform all implementation decisions:

1. **Agent team size: k<=5** — Silo-Bench (March 2026) shows coordination overhead eliminates parallelization gains at k=50. At k=2, you lose 15-49% of single-agent performance. Design for small coordinated teams, not swarms.

2. **Output verification > process verification** — MAS-ProVe demonstrates that process-level verification of LLM reasoning trajectories does not consistently improve performance. Test outputs and adversarial scenarios, not trajectories.

3. **Non-token economics validated** — Every major token (OLAS, GTC, FET, AGIX, OCEAN) has declined dramatically. Holochain's intentional absence of a native token layer is the correct approach.

4. **IPFS multi-pinning required** — Peer availability dropped from 60% to 40%, with 50% of peers online less than 4 days. Single-pin is insufficient for persistence.

See `docs/research/Automated-Agent-Orchestration-Report_v2.0.0.md` for full analysis.

---

## Immediate Next Action

**Phase 0 Substrate Bridge Validation** — `docs/specs/phase0-substrate-bridge.spec.md`

Write and run a 2-agent Tryorama test that validates: publish, provenance, independent verify, discovery via query, fork visibility, and no privilege. This is the narrowest test that proves the architecture end-to-end.

That single command will tell us whether Phase 0 is a 2-hour fix or a 2-week investigation. Everything else flows from there.

```bash
cd /path/to/FLOSS/ARF
nix develop
cargo build --release --target wasm32-unknown-unknown
```

If it compiles: we're golden. Write the DNA manifest, pack, install, test.
If it doesn't: the error message IS the roadmap.

---

*Spec first. Ship simplest thing that solves validated problem today. Delete the rest.*
*Love, Light, Knowledge — verifiable, shared, and free.*
