# FLOSSI0ULLK Stack Crosswalk

```yaml
id: "flossi0ullk-stack-crosswalk"
version: "0.1.0"
kind: "architecture_reference"
status: "Proposed"
updated: "2026-04-18"
truth_status: "Specified"
evidence_sources:
  - "FLOSS/CLAUDE.md (layer stack A0..4.6)"
  - "docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md (Observer..Curator service plane)"
  - "docs/architecture/AGENTIC_OPERATING_MODEL.md"
  - "docs/architecture/METAHARNESS_OPERATING_MODEL.md"
  - "FLOSSI0ULLK_Context_Daemon_Architecture.md (root intake)"
  - "FLOSS/docs/architecture/FLOSSI0ULLK-Architecture-Spec-v0.1.md (historical intake with supersession banners)"
supersedes: []
reconciles:
  - "label collision between two 'five-layer' framings circulating under the same project name"
```

## Purpose

Two architectural stacks are described in FLOSSI0ULLK documents as "five-layer
architectures." They are not peers. This document makes the distinction explicit
and provides the crosswalk between them so that future synthesis work can
reference the right object.

## Problem

The phrase *"five-layer model"* appears in at least two contexts:

1. The **parent stack** — the vertical substrate architecture from the Master
   Metaprompt v1.3.1 (Holochain DHT → ADR memory → Semantic CRDTs → Symbolic
   validation → RSA agent coordination). This framing predates the in-flight
   local agent node and harness optimization work.
2. The **Context Daemon stack** — Observer → Semantic Index → Bi-temporal graph
   → CRDT working-state → Curator, per the canonical
   `docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md`.

Treated as peer architectures, these collide. They are not peers. One is a
vertical substrate stack; the other is a horizontal service plane that reads
from, and serves, the substrate.

## The Parent Stack (actually 8 layers, not 5)

The canonical current framing, per `FLOSS/CLAUDE.md`, is *eight* layers:

| Layer | Role | Location / evidence |
|---|---|---|
| A0 | Dev substrate (Radicle patches / COBs) | `docs/adr/ADR-8-radicle-dev-substrate.md` |
| 0 | Storage substrate (Holochain agent-centric DHT) | `ARF/dnas/rose_forest/` |
| 1 | Persistent memory (ADR + ConversationMemory) | `ARF/conversation_memory.py`, `docs/adr/` |
| 2 | Semantic layer (CRDTs + embeddings) | `ARF/embedding_frames_of_scale.py` |
| 3 | Symbolic validation (Rust integrity zomes) | `ARF/dnas/*/zomes/integrity/` |
| 4 | Agent coordination (RSA swarm + LLM committee) | `ARF/pwnies/`, `ARF/validation/` |
| 4.5 | Local agent node (MCP passive-router consensus gateway) | `packages/` (landed in `096b058`) |
| 4.6 | Harness optimization (multi-harness routing, memory, retrieval, optimization) | `docs/architecture/AGENTIC_OPERATING_MODEL.md` |

**Recommendation:** retire the "five-layer" label for this stack. It no longer
matches the canonical layer count. Refer to it as *the parent stack* or *the
A0..4.6 substrate stack*.

## The Context Daemon Service Plane

Per canonical `docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md`:

| Layer | Role |
|---|---|
| Observer | Normalized deltas from file changes, hook outputs, provenance events |
| Semantic index | Incremental indexing/retrieval over docs, code, claims, traces |
| Bi-temporal graph | Facts, ADRs, artifacts, agents linked with validity windows |
| CRDT working-state | Conflict-free shared task/session state for active collaboration |
| Curator | Scheduled or triggered consolidation, contradiction handling, pruning |

This is a **horizontal service plane**, not a vertical substrate stack. It
reads from substrate layers and produces projections (the L0/L1 views already
live on disk at `.agent-surface/context/`) plus graph/state surfaces that other
layers consume.

## The Crosswalk

Which substrate layers the Context Daemon *reads from* (input), *overlaps*
(shared concern), and *serves* (output):

| Parent layer | Daemon relationship | Direction |
|---|---|---|
| A0 (Radicle) | Observer ingests commit / patch events | substrate → daemon |
| 0 (Holochain DHT) | Bi-temporal graph draws claim validity windows from DHT state (not live as daemon input yet; gated on substrate-bridge replication, not the old MVP Tryorama gate) | substrate → daemon |
| 1 (ADR + ConversationMemory) | ADRs feed the bi-temporal graph; ConversationMemory informs Curator's working history | substrate → daemon |
| 2 (Semantic CRDTs + embeddings) | **Overlap / potential duplication with Daemon Semantic Index — see "Unresolved Conflict" below** | ↔ |
| 3 (Integrity zomes) | Curator respects symbolic verdicts over LLM consolidation (symbolic-first); Observer watches zome source changes | substrate → daemon |
| 4 (RSA + LLM committee) | Consumes Daemon's `CONTEXT_L0`/`L1`/`L2` projections and graph queries for context-budget-aware loading | daemon → substrate |
| 4.5 (Local agent node / MCP passive-router) | Observer ingests `packages/source_chain/` provenance and `packages/metacoordinator_mcp/` traces (explicit in canon) | substrate → daemon |
| 4.6 (Harness optimization) | Consumes Daemon's full-trace archive for self-optimization | daemon → substrate |

## Unresolved Conflict (one, genuine)

Parent Layer 2 (**Semantic CRDTs + embeddings**) and the Daemon's **Semantic
Index** both do embedding-backed retrieval. Canon does not decide which is
canonical. Two reconciliations are coherent:

1. **Layer 2 is canonical, Daemon indexes project from it.** Semantic Index
   becomes a cache / projection layer that reads from Layer 2's embedding
   store. The daemon owns indexing strategy and retrieval policy but not the
   embedding store itself.
2. **Daemon owns embeddings, Layer 2 becomes symbolic-only.** Layer 2's role
   contracts to Semantic CRDTs (structural composition), and embeddings move
   entirely into the Daemon's service plane.

Either reconciliation is implementable; picking one is the next architectural
decision and should be captured as a new ADR.

## Label Drift to Fix

- Recent pasted summaries have referred to the Daemon layers as *"Knowledge
  Graph"* and *"CRDT State"*. The canonical names in
  `docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md` are **Bi-temporal graph
  layer** and **CRDT working-state layer**. Drift between derivative summaries
  and canon should be corrected in any downstream synthesis.
- The *"five-layer model"* phrase should no longer be used without qualifier;
  specify *Context Daemon service plane* or *parent A0..4.6 stack*.

## Relationship To Other Canonical Docs

- `AGENTIC_OPERATING_MODEL.md` defines harness roles; the daemon serves those
  harnesses their context.
- `METAHARNESS_OPERATING_MODEL.md` explains how shared surfaces compose; the
  daemon's generated views live on that compositional seam.
- `HOLISTIC_ARCHITECTURE.md` places both the substrate stack and the daemon
  service plane in the full project picture.
- `shared-context-surface.json` is the canonical routing manifest the daemon
  operates against.

## Status Transitions

Current status: **Proposed**. Promote to *Active* only after:

1. Human or multi-agent review confirms the crosswalk is accurate.
2. The Layer-2 / Semantic-Index reconciliation is decided (new ADR).
3. `docs/adr/INDEX.md` is updated to reference this document.
