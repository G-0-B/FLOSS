# FLOSSI0ULLK Context Daemon Architecture

```yaml
id: "flossi0ullk-context-daemon-architecture"
version: "0.1.0"
kind: "architecture_reference"
status: "Active"
updated: "2026-04-17"
truth_status: "Specified"
evidence_sources:
  - "root intake: FLOSSI0ULLK_Context_Daemon_Architecture.md"
  - "root intake: The Living Context Daemon_ Architecture for a Cont.md"
  - "shared-context-surface.json"
  - "scripts/context_router.py"
  - "scripts/materialize_shared_context_surface.py"
  - "docs/architecture/AGENTIC_OPERATING_MODEL.md"
  - "docs/architecture/METAHARNESS_OPERATING_MODEL.md"
  - "packages/source_chain/"
  - "packages/metacoordinator_mcp/"
```

## Purpose
This document promotes the context-daemon design into canon.

The goal is to stop treating shared context as a session-start ritual and start
treating it as infrastructure: observable, routed, compressed for loading, and
traceable back to richer source material.

## Problem
Static context files decay quickly in a multi-agent workspace:

- architecture changes while agents are still working from older snapshots
- claims, votes, and decisions move between epistemic states over time
- traces accumulate faster than humans or agents can reread them end to end
- token budgets punish naive "load everything" behavior

The answer is not to flatten the canon into shorter canon. The answer is to keep
rich canonical artifacts, then generate cheaper projections for loading.

## Canonical Shape
The living context daemon is a five-layer architecture served through a single
shared context interface:

1. **Observer layer**
   - file changes, hook outputs, and provenance events become normalized deltas
2. **Semantic index layer**
   - incremental indexing and retrieval over docs, code, claims, and traces
3. **Bi-temporal graph layer**
   - facts, ADRs, artifacts, and agents linked with validity windows
4. **CRDT working-state layer**
   - conflict-free shared task and session state for active collaboration
5. **Curator layer**
   - scheduled or triggered consolidation, contradiction handling, and pruning

The current FLOSSI0ULLK implementation is only a walking skeleton of this
architecture, but the shape is now canonical.

## Current Walking Skeleton
What is live now:

- `shared-context-surface.json` defines corpora, route order, and operating rules
- `scripts/context_router.py` chooses corpora before deeper retrieval
- `scripts/materialize_shared_context_surface.py` generates additive context views
- `scripts/watch_intake.py` emits normalized intake events into a queue skeleton
- `scripts/process_intake_events.py` claims and classifies queued events for consolidation follow-up
- `.agent-surface/context/CONTEXT_BOOTSTRAP.md` exposes the corpus map
- `.agent-surface/context/CONTEXT_L0.md` and `CONTEXT_L1.md` provide cheap
  loading projections
- `packages/source_chain/` and `packages/metacoordinator_mcp/` already produce
  provenance and trace surfaces that the future daemon should ingest
- `FLOSS/.serena/memories/` provides a durable code-understanding sidecar

What is not live yet:

- a continuous file-watch event daemon
- incremental semantic indexing over the whole workspace
- a bi-temporal claim / ADR / artifact graph
- CRDT-backed shared working state
- an automated curator loop for contradiction handling and nightly consolidation
- a dedicated `flossi0ullk-context` MCP gateway

## Compression Doctrine
Compression is additive. Canon remains human-readable and editable.

Rules:

- rich docs stay canonical
- generated compressed views are projections, not source of truth
- route corpus first, then load `L0`, then `L1`, then `L2`
- `_reference/` is a published research library and book corpus, not the live canon
- full traces remain on disk even when condensed views are generated for loading

This is where `caveman`-style compression is useful: as a projection strategy for
always-loaded context, not as a rewrite policy for the canon itself.

## Generated Context Views
The shared context surface now owns two generated views:

- `CONTEXT_L0.md`
  - very cheap briefing for fast re-orientation
  - one compressed line per canonical source
- `CONTEXT_L1.md`
  - richer but still selective briefing with summaries, headings, and key bullets

These views are deterministic artifacts generated from selected canonical docs.
They are intended to reduce startup token burn while keeping the canonical
documents intact.

## Near-Term Build Order
1. Harden the current generated `L0/L1` views and keep them aligned with canon.
2. Harden the observer/event queue for doc, code, and source-chain changes.
3. Add incremental semantic indexing over active corpora.
4. Represent claims, ADRs, artifacts, and agents in a graph structure.
5. Add CRDT-backed working memory for active collaboration state.
6. Add a curator loop for consolidation, contradiction handling, and pruning.
7. Expose the whole stack through a single `flossi0ullk-context` MCP surface.

## Relationship To Other Canonical Docs
- `AGENTIC_OPERATING_MODEL.md` defines harness roles and immediate execution policy.
- `METAHARNESS_OPERATING_MODEL.md` explains how shared surfaces compose.
- `HOLISTIC_ARCHITECTURE.md` places the daemon in the full project stack.
- `shared-context-surface.json` is the canonical routing and context-source manifest.

The root intake daemon reports remain valuable source material, but this file is
the canonical architectural reference going forward.
