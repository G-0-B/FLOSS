# FLOSSI0ULLK Architecture Specification v0.1

```yaml
id: flossi0ullk-architecture-spec
version: "0.1.1-with-superseded-banners"  # was 0.1.0; 2026-05-18 banners added — see Section 0
kind: architecture_spec
status: Partially Superseded — see Section 0 banner below
truth_status: Mixed — per-component status declared inline; superseded sections marked explicitly
updated: "2026-05-18"  # was 2026-04-17; banners added without rewriting historical content
supersedes: []
superseded_in_part_by:
  - "FLOSS/docs/adr/FLOSSI0ULLK-ADR-Suite-v2.0.md (ADR-10 analog vote model — supersedes §5 step 4, §6.1, §6.2, §9 ternary glossary entry)"
  - "FLOSS/docs/architecture/META_COORDINATION_KERNEL_v4.0.md (operational axis — augments §3 layer taxonomy)"
  - "FLOSS/docs/architecture/HOLISTIC_ARCHITECTURE.md §2.5 (CCES 8-layer teleological axis)"
canonical_path: FLOSS/docs/architecture/FLOSSI0ULLK-Architecture-Spec-v0.1.md
authors:
  - Anthony (human steward)
  - Perplexity synthesis agent
source_docs:
  - INDEX.md (2026-04-14)
  - CLAUDE.md / AGENTS.md (2026-04-14)
  - GEMINI.md
  - 4-4-26-FLOSSI0ULLK-Four-System-Integration-Analysis.md
  - Open-Access Research Landscape (2026-04-14)
  - Integrated Extended Report (2026-04-15 session)
stress_test_applied: "2026-04-17 — seven load-bearing issues addressed per critique"
```

---

## 0. ⚠️ Supersession Banner (added 2026-05-18)

**This document remains valuable as a snapshot of the architecture as understood on 2026-04-17, but the following sections have been formally superseded by later canonical landings:**

| Section in v0.1 | Status | Superseded by |
|---|---|---|
| §5 Control Loop step 4 — "Ternary vote: +1 / 0 / −1" | ⚠️ Superseded | **ADR-10 v2.0 analog vote model `[-1.0, +1.0]`** (FLOSSI0ULLK-ADR-Suite-v2.0.md, hand-verified 2026-04-26). Any "ternary" mention here is historical context, not current behavior. The Layer 4.5 gateway has accepted analog floats since commit `096b058`. |
| §6.1 Ternary consensus | ⚠️ Superseded | ADR-10 v2.0 (same as above). |
| §6.2 Steward-vote carve-outs | ⚠️ Open — governance ADR-13 still pending per ADR-Suite v2.0 §13 governance-gap backlog. Carve-out + analog-vote composition is the v2.0 work-item. |
| §9 Glossary "Ternary Consensus" | ⚠️ Superseded by analog vote model per ADR-10 v2.0. Read as historical only. |
| §3 Layer taxonomy (single 9-layer stack) | ⚠️ Augmented (not contradicted) by **META_COORDINATION_KERNEL_v4.0** (operational axis, 9 layers + RICE overlay + Superalignment Triad + 10 named roles) AND **HOLISTIC_ARCHITECTURE.md §2.5 CCES** (teleological axis, 8 cosmocentric layers). v4.0 §21 names the orthogonal-axis composition rule. |
| §4.5 ADR drift note | ✅ Resolved 2026-04-26 — ADR-Suite v2.0 consolidated ADR-0..11; ADR-MCP-ORCHESTRATOR assigned permanent number ADR-10. |
| §6.3 Claim Truth Model | ✅ Adopted into canonical specs per `project_truth_label_canon` memory; governance ADR canonicalizing the scheme still pending. |
| §7 Orchestration patterns / Seam priorities | ⚠️ Partially advanced — Seam 1 (consensus-gate hook) is the verified Layer 4.5 gateway; Seam 2 (git-worktree isolation) used in practice via `.claude/worktrees/`. Other seams remain aspirational. |
| §10 Phase 0 blocker #3 (ADR-0 Test #4) | ✅ Resolved — Test #4 (Human Coherence) PASSED 2026-03-20 per ADR-0.1 v2.0. Recognition Protocol is **Validated**. |
| §10 Phase 0 blocker #1 (Rose Forest DNA) | ✅ **CORRECTED 2026-05-18 (cross-agent drift fix)** — **MVP Phase 0 is COMPLETE** per `FLOSS/MVP_PLAN.md` line 23 + `FLOSS/pprevious_working_task.md`: DNA compiles to WASM, Holochain hApp/Tryorama integration tests pass, ontology integrity unit tests pass. The "Tryorama suite still the exit gate" framing was a session-drift error this banner originally reproduced. The current gate is **orchestration substrate bridge validation** per `FLOSS/docs/specs/phase0-substrate-bridge.spec.md` (publish → provenance → independent verify → query → fork-visible → no privileged verifier). ADR-Suite v2.0 still carries the older wording — that's pending evidence-reconciliation work, not silent rewriting. |

**Net read of this doc as of 2026-05-18:** historical context of how the architecture was understood pre-v4.0-kernel, pre-CFIS-v0.3, pre-MDASH-transfer, pre-Reasoning-Ensemble-proposal. **NOT good for:** ground truth on vote model, operational stack, or Phase 0 status. For current-state ground truth, read in order:

1. `FLOSS/docs/adr/FLOSSI0ULLK-ADR-Suite-v2.0.md` (canonical decisions)
2. `FLOSS/docs/architecture/META_COORDINATION_KERNEL_v4.0.md` (operational axis)
3. `FLOSS/docs/architecture/HOLISTIC_ARCHITECTURE.md` (teleological axis + §2.5 CCES)
4. `FLOSS/docs/research/2026-05-15-working-todo-list.md` (live operational state)
5. `FLOSS/docs/research/2026-05-16-mdash-cfis-architectural-transfer.md` + `2026-05-17-inline-reasoning-ensemble.md` (architectural proposals in flight)

The original §1–§10 content follows unchanged below for historical preservation.

---

> **Reading guide — truth-status labels used throughout:**
> - ✅ **Verified** — running, tested, confirmed
> - ⚠️ **Specified** — designed and documented; not yet built or validated
> - 🔮 **Aspirational** — intended direction; no spec or implementation
> - ❌ **Unverified / Blocked** — claimed elsewhere but contradicted or not buildable yet

---

## 1. Identity

FLOSSI0ULLK (**F**ree **L**ibre **O**pen **S**ource **S**ingularity of **I**nfinite **O**verflowing **U**nconditional **L**ove, **L**ight, and **K**nowledge) is a decentralized knowledge commons and biomimetic distributed intelligence platform.

**Design intent:** an agent-centric, Holochain-grounded, symbolic-first orchestration architecture in which decentralized agents collaborate through cryptographically signed Claims, governance Votes, ADR memory, and semantic knowledge structures, while a passive local agent node routes execution, a hookable multi-agent harness scales work, and a full-trace optimization loop improves the harness over time under consent-based governance.

**Current honest one-liner:** A well-specified architecture with a running coordination gateway and a governance framework. The cryptographic substrate is not yet compiled. Most claims in the design remain Specified or Aspirational rather than Verified.

---

## 2. Prime Directive

> **Logic validates, neural assists — never the reverse.**

| Layer | Expression | Status |
|-------|-----------|--------|
| Integrity zomes (Rust) | Enforce formal logic, type systems, ontology rules — non-bypassable | ❌ **Blocked** — Rose Forest DNA has not compiled; build infra missing |
| Coordinator zomes (Rust) | APIs and complex coordination logic | ❌ **Blocked** — same blocker as integrity layer |
| Neural models (LLMs) | Formatting engines and natural language interfaces only | ✅ **Verified** — in active use |
| Knowledge graphs | Primary storage; embeddings for indexing/search only | ⚠️ **Specified** — schema designed, not deployed |

**Implication:** The prime directive is currently aspirational by enforcement. It is operational by convention — agents are instructed to honor it, but no zome-level gate can reject a violation while the substrate is uncompiled. Every design decision should preserve the prime directive in anticipation of the gate becoming real.

---

## 3. Layer Taxonomy (canonical)

The authoritative stack is five layers. The "four planes" framing used in the previous synthesis is deprecated — it conflated operational substrate with a proposed optimization loop that does not yet exist. Planes are not used in this document.

| Layer | Name | Technology | Location | Status |
|-------|------|-----------|----------|--------|
| 0 | Storage substrate | Holochain agent-centric DHT | `ARF/dnas/rose_forest/` | ❌ **Blocked** — DNA uncompiled |
| 1 | Persistent memory | ADR system + ConversationMemory | `ARF/conversation_memory.py`, `docs/adr/` | ⚠️ **Specified** — API mismatch with MultiScaleEmbedding; ADR index drift |
| 2 | Semantic layer | Semantic CRDTs + embeddings | `ARF/embedding_frames_of_scale.py` | ⚠️ **Specified** |
| 3 | Symbolic validation | Formal logic in Rust integrity zome | `ARF/dnas/*/zomes/integrity/` | ❌ **Blocked** — Layer 0 blocker applies |
| 4 | Agent coordination | RSA swarm + LLM committee | `ARF/pwnies/`, `ARF/validation/` | ⚠️ **Specified** |
| 4.5 | Local agent node | File-based source chain + consensus gateway | `FLOSS/packages/` | ✅ **Verified** — landed commit 096b058 |

**Layer 4.5 note:** The local agent node is a **pre-substrate bridge**, not a parallel implementation of Holochain. It is structurally analogous to a single Holochain cell's source chain — append-only, hash-linked, agent-signed — but it cannot replicate DHT validation, cryptographic header chaining across agents, or cross-cell consensus. When Layer 0 is operational, Layer 4.5 either migrates into it or becomes a local development shim. Calling it "1:1 with Holochain cell structure" was overfit; the honest characterization is **structurally analogous, pre-substrate**.

---

## 4. Key Components

### 4.1 Rose Forest DNA ❌ Blocked

The primary Holochain DNA implementing the knowledge graph. Contains integrity and coordinator zomes for entry type validation, link validation, and graph traversal.

- **Blockers:** Build infra missing; DNA has not compiled. `ConversationMemory` has an API mismatch with `MultiScaleEmbedding`.
- **Test gap:** ADR-0 Test #4 (Human Coherence) has not been run.
- **Phase gate:** Rose Forest compiling and passing `cargo test` is the exit criterion for Phase 0.

### 4.2 ARF (Autonomous Resonance Framework) ⚠️ Specified

The high-level Python coordination and memory layer. Provides the `arf` CLI (`memory transmit`, `swarm query`, `ontology validate`). Integrates ConversationMemory, semantic embedding frames, and the RSA protocol.

- **Active gap:** `conversation_memory.py` API mismatch with `MultiScaleEmbedding` is a known blocker.
- **Entry point:** `FLOSS/ARF/`

### 4.3 Local Agent Node (Consensus Gateway) ✅ Verified

A passive-router multi-model consensus gateway under `FLOSS/packages/`. Three sub-packages:

| Package | Role |
|---------|------|
| `metacoordinator_mcp` | MCP passive-router gateway — receives Claims and Votes via MCP protocol |
| `orchestrator` | Claim schema, consensus gate, serialization |
| `source_chain` | File-based append-only source chain (pre-substrate analog) |

**Invariant:** The gateway **does not decide outcomes and does not command voters.** It accepts Claims and Votes from any agent — human, model, ensemble — and appends to disk. Decision authority stays with the agents and the governance rules, not the router.

### 4.4 RSA (Recursive Self-Aggregation) ⚠️ Specified

Multi-agent synthesis and coordination protocol. Coordinates agent ensembles toward convergent outputs through recursive self-referencing rounds. Not yet implemented against the live consensus gateway.

### 4.5 ADR System ✅ Verified (with drift)

Architecture Decision Records in `FLOSS/docs/adr/`. Currently ADR-0 through ADR-7 plus unnumbered ADR-MCP-ORCHESTRATOR. Known drift:
- ADR INDEX shows 8 entries; actual count is 10+.
- ~~`FLOSSI_U_Founding_Kit_v1.6/` uses a parallel ADR-001..019 namespace. Relationship to main ADR set is **unresolved** — needs a reconciliation ADR before either set is treated as canonical.~~ **RESOLVED 2026-05-11**: FLOSSI U is a separate sibling project (Free YOU-niversity), relocated to `C:\~shit\FLOSSI_U/` at workspace top-level. Its ADR-001..019 namespace is its own canon, not a conflict with Rose Forest's ADR-0..11.
- ADR-7 (AGPL-3.0 Copyleft Cascade) formally embraces copyleft licensing, unblocking AIngram integration paths B (Python port) and C (Rust integrity zomes).

---

## 5. Control Loop

The normative work cycle with explicit actor assignment. **Automation of ADR promotion is not default** — promotion by an agent is permissible only under an explicit standing governance rule (quorum + claim-truth Verified threshold). Without that rule, promotion is a human action.

```
Step                     Actor                   Gate / Trigger
──────────────────────────────────────────────────────────────────────────
1. Clarify intent        Human OR agent (Socratic  Anti-sycophancy mandate;
                         deep-interview pattern)   ambiguity → Decision 0, stop
2. Spec / plan           Designated planner agent  Spec (.spec.md + .schema.json)
                         + human review            produced before code
3. Symbolic pre-check    Symbolic validator agent  AST / schema validation;
                         (tool-guard hook)         hard-fail → return to step 2
                         [currently: convention;
                         gate unenforceable until
                         Layer 0 compiles]
4. Consensus gate        Consensus gateway         Ternary vote: +1 / 0 / −1
                         (Layer 4.5)               0 → clarify; −1 → reject
                         + human or ensemble       Recorded as Claim on source chain
5. Execute               Worker agents in          Git-worktree isolation
                         isolated contexts         (pattern: candidate, not required)
6. Collect Claims/Votes  Consensus gateway         Append-only, hash-linked
7. Promote to ADR        Human steward             NOT automated by default;
                         (or agent under explicit  requires explicit governance rule
                         standing rule)            with quorum + Verified threshold
──────────────────────────────────────────────────────────────────────────
```

**Human bottleneck:** Steps 1, 7, and the −1 veto in Step 4 are intentional human gates, not bottlenecks to be automated away. The system's safety model depends on them. Steps 3 and 4 are candidates for partial automation once Layer 0 is operational and governance rules are codified.

---

## 6. Consensus and Governance

### 6.1 Ternary consensus

All structural decisions use a **+1 / 0 / −1** vote scheme rather than binary approval.

| Vote | Meaning | Effect |
|------|---------|--------|
| +1 | Approve | Counts toward quorum |
| 0 | Abstain / insufficient information | Does not count toward quorum; triggers additional review if majority |
| −1 | Reject | Blocks the decision; requires re-plan or escalation |

**Quorum rule (unresolved — pending governance ADR):** The specific quorum threshold (e.g., majority +1, no −1) is not yet codified. Until it is, a single human −1 is an effective veto. This gap must be closed before automated loops can be trusted to run unsupervised.

### 6.2 Steward-vote carve-outs (ADR-7)

ADR-7's humanitarian / medical / educational carve-outs are referenced in the system's governance model but not yet composed with the ternary consensus mechanism. The open questions:

- Does a steward carve-out override a −1 vote?
- Does it lower quorum for that category?
- What prevents carve-out scope creep?

These are **unresolved**. No implementation should assume an answer until a dedicated governance ADR lands.

### 6.3 Claim Truth Model

Every claim propagating through the system should carry one of four truth-status labels:

| Label | Meaning |
|-------|---------|
| ✅ Verified | Confirmed by independent evidence or symbolic gate |
| ⚠️ Specified | Designed; not yet built or tested |
| 🔮 Aspirational | Intended direction; no spec or implementation |
| ❌ Unverified | Asserted elsewhere but contradicted or untestable |

**Outstanding:** A dedicated governance ADR is required to canonicalize the scheme (Spine v0.5 defines it; a "Context Continuation Artifact v0.2.0" variant also exists but is not on disk). The ADR should resolve the outstanding critique flagged by another model before the scheme is treated as binding.

---

## 7. Orchestration Patterns — Candidate Adoptions

The following patterns from the four-system integration analysis are **ROI-ranked candidates**, not default requirements. None should be treated as canonical until an ADR records the adoption decision.

| Priority | Pattern | Source | Rationale | Status |
|----------|---------|--------|-----------|--------|
| 1 | Consensus-gate hook (Seam 1) | FLOSSI0ULLK design | Establishes MCP channel all other seams depend on | ⚠️ Specified — first seam to build |
| 2 | Full-trace storage infra | Meta Harness | Cannot begin harness optimization without it | ⚠️ Specified |
| 3 | Hashline deterministic edit verification | omo | Verifies spec intent landed in file; 6.7%→68.3% success rate documented | 🔮 Aspirational — strong ROI signal |
| 4 | Git worktree agent isolation (Seam 2) | OMX | Enables multi-PC deployment; parallel workers without file contention | 🔮 Aspirational |
| 5 | Three-layer memory (Seam 4) | Claude Code leak | Replaces ad-hoc context; maps to Claim Truth Model promotion cycle | 🔮 Aspirational |
| 6 | OMX OpenClaw gateway events (Seam 5) | OMX | Connects OMX ecosystem to FLOSSI0ULLK | 🔮 Aspirational |
| 7 | Dual-prompt agents | omo | Eliminates Claude/GPT prompt-model mismatch | 🔮 Aspirational |
| 8 | Meta Harness routing optimization (Seam 3) | Meta Harness | Automates routing table improvement; depends on Seams 1+2 | 🔮 Aspirational |

**The optimization loop** (Meta Harness integrate–propose–evaluate–iterate) is entirely aspirational. It is architecturally sound and directionally correct, but it depends on full-trace storage (Priority 2), which depends on the consensus-gate hook (Priority 1), which depends on the Layer 4.5 gateway being stable (✅ landed). There is no "optimization plane" running today.

---

## 8. Governance of This Document

- **ADR gate:** Any section moving from ⚠️ Specified to ✅ Verified requires a corresponding ADR or test record.
- **No premature canonicalization:** Patterns listed in Section 7 must not be referenced as "requirements" in implementation tickets until promoted via ADR.
- **Tense discipline:** Past tense for historical decisions, present tense for running components only, future/conditional for everything else.
- **Version bump trigger:** Any substantive change to Sections 3, 4, 5, or 6 bumps the minor version and creates an archive copy.

---

## 9. Glossary

| Term | Definition |
|------|-----------|
| **ADR** | Architecture Decision Record — numbered, immutable, status-tracked record of a significant design decision. Lives in `FLOSS/docs/adr/`. |
| **ARF** | Autonomous Resonance Framework — the Python coordination and memory layer wrapping Holochain DNA and the RSA protocol. |
| **Claim** | A typed assertion submitted to the consensus gateway, carrying a truth-status label, agent identity, and timestamp. |
| **Claim Truth Model** | The four-label (Verified / Specified / Aspirational / Unverified) system for status-tagging all asserted facts. |
| **ConversationMemory** | Python module in `ARF/conversation_memory.py` that persists agent conversation state across sessions. Currently has an API mismatch with `MultiScaleEmbedding`. |
| **Harness** | In the Meta Harness sense: the stateful program wrapping a frozen LLM that determines what context it sees. Optimizing the harness is the highest-leverage engineering lever per arXiv:2603.28052. |
| **Hashline** | omo pattern: tags each file line with a content hash (`LINE#ID content`). Edit rejected if hash doesn't match current file state. Prevents stale-read corruption. |
| **Integration Seams** | Five numbered integration points between the four systems (omo, OMX, Meta Harness, FLOSSI0ULLK) defined in the four-system analysis. Seam 1 is consensus-gate hook; Seam 2 is git-worktree isolation; Seam 3 is Meta Harness routing optimization; Seam 4 is three-layer memory; Seam 5 is OMX/OpenClaw gateway events. |
| **Integrity Zome** | The Rust layer inside a Holochain DNA that defines validation rules — the non-bypassable "law" of a Holochain application. |
| **Layer 4.5** | Informal label for the local agent node — a pre-substrate bridge that runs today and will migrate into or be replaced by Holochain Layer 0 when the DNA compiles. |
| **Local Agent Node** | The running consensus gateway under `FLOSS/packages/`. A router that appends Claims/Votes to a file-based source chain. Not a controller. |
| **MCP** | Model Context Protocol — the transport layer over which agents submit Claims and receive routing from the metacoordinator. |
| **Meta Harness** | Stanford IRIS + MIT system (arXiv:2603.28052) that optimizes complete harness implementations using ~10M-token full-trace file access per iteration. Optimization objective: `H* = argmax_H E_{x~X}[r(τ, x)]`. |
| **MetaCoordinator** | FLOSSI0ULLK's coordination layer — currently instantiated as the MCP passive-router gateway. |
| **OMX / oh-my-codex** | Yeachan-Heo's portable orchestration wrapper for Codex CLI and Claude Code. Key contribution: git-worktree agent isolation, mixed-provider team execution, `ralplan` consensus planning, `deep-interview` Socratic clarification. |
| **omo / oh-my-openagent** | code-yeongyu's OpenCode plugin. Key contributions: 11 specialized agents in 4 personality groups, 48-hook lifecycle system, Hashline verification, Boulder persistence. |
| **Rose Forest** | The primary Holochain DNA implementing the knowledge graph. Currently uncompiled — the central Phase 0 blocker. |
| **RSA** | Recursive Self-Aggregation — the multi-agent synthesis protocol for converging ensemble outputs through recursive rounds. |
| **Source Chain** | In Holochain: each agent's local, append-only, cryptographically signed record of their own actions. In Layer 4.5: a file-based analog providing the same append-only guarantee without DHT validation. |
| **Ternary Consensus** | +1 / 0 / −1 vote scheme. 0 (abstain) captures genuine uncertainty that binary systems collapse to false approval. −1 (reject) blocks. Quorum threshold TBD via governance ADR. |

---

## 10. Phase Status and Exit Criteria

| Phase | Name | Exit Criterion | Status |
|-------|------|---------------|--------|
| Foundation | Docs, ADRs, spec complete | Master Metaprompt v1.3.1, ADRs 0–7, SDD spec done | ✅ Complete |
| Phase 0 | Substrate viability | Rose Forest compiles + passes `cargo test`; ConversationMemory API mismatch resolved; ADR-0 Test #4 run | ❌ Active — 3 open blockers |
| Phase 1 | MVC | Layer 4.5 gateway + ARF + one working end-to-end claim round-trip | ⚠️ Partially in flight (Layer 4.5 ✅, ARF ⚠️) |
| Phase 2+ | Distributed network | Kitsune2-based DHT sync; multi-node deployment | 🔮 Aspirational |

**Phase 0 blocker detail:**
1. Rose Forest DNA has not compiled — build infra missing.
2. `ConversationMemory` has an API mismatch with `MultiScaleEmbedding`.
3. ADR-0 Test #4 (Human Coherence) has not been run.

---

*Simplicity now. Seams for later. Delete the rest.*
*Love, Light, Knowledge — verifiable, shared, and free.*
*The protocol is the conversation. The system builds itself.*
