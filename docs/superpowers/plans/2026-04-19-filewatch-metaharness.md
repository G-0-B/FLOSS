# Filewatch Metaharness Plan

```yaml
id: "flossi0ullk-filewatch-metaharness-plan"
version: "0.1.0"
kind: "implementation_plan"
status: "Active"
updated: "2026-04-19"
truth_status: "Specified"
evidence_sources:
  - "docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md"
  - "docs/architecture/METAHARNESS_OPERATING_MODEL.md"
  - "shared-context-surface.json"
  - "shared-agent-surface.json"
```

## Goal
Add a minimal filewatch and consolidation seam that can tell every active agent
what changed without letting every agent write canon directly.

This is not the full context daemon. It is the smallest useful observer/event
bus skeleton that lets intake, routing, and curation happen with explicit
concurrency boundaries.

## Problem
Right now new root intake docs, fork notes, traces, and shared-surface edits are
noticed socially or manually. That creates three predictable failures:

- important new material lands in `C:\~shit` and only one agent sees it
- multiple agents update adjacent shared surfaces without a shared queue
- generated context and orientation drift behind the latest intake

## Constraints
- watchers do not write canon directly
- observers may be many, canonical writers must be one-per-surface
- normalized events are append-only
- consolidation must be reversible and inspectable
- generated projections remain generated; canon remains the source of truth
- shadow logs and sidecar memories are non-canonical until explicitly promoted
- clock-driven memory sidecars must emit events, not direct mutations

## Pipeline Shape

| Layer | Responsibility | Writes |
|-------|----------------|--------|
| Observation | Detect file changes and normalize them into events | `.agent-surface/events/incoming/*.json` |
| Interpretation | Classify events into root-intake / canon / traces / shared-surface | `.agent-surface/events/processed/*.json` |
| Projection | Rebuild cheap views when safe and needed | generated context / skill / agent surfaces |
| Curation | Propose updates to orient/shared-surface skills, pointers, and docs | canonical manifests and skill corpus |
| Promotion | Move durable learnings into ADRs/specs/canon | canonical docs only |

## Concurrency Model

### Rule 1: Many observers, one writer per target
- many watcher processes may emit events
- only one consolidator writes a given canonical surface at a time
- generated outputs are also single-writer per target

### Rule 2: Claim work by rename, not by shared memory
- event files start in `incoming/`
- a worker claims an event by atomically moving it into `processing/`
- completed events move to `processed/`
- failed events move to `failed/`

### Rule 3: Lock by surface, not by whole system
Expected lock names:
- `shared-context-surface.lock`
- `shared-skill-surface.lock`
- `shared-agent-surface.lock`
- `summary.lock`
- `watch-state.lock`

### Rule 4: Reserve subtrees before importing new sidecars
Reserved runtime subtrees under `.agent-surface/`:
- `events/` for queue state
- `context/` for generated context views
- `skills/` for generated indexes
- `hooks/` for generated hook indexes
- `shadows/` for future append-only file shadow artifacts

Anything writing under these roots must be explicitly excluded from watcher
intake unless it is itself the queue source of truth.

## Walking Skeleton

### 1. Event format
Use `docs/specs/intake-event.schema.json` as the normalized queue contract.

### 2. Observer script
`scripts/watch_intake.py`

Responsibilities:
- scan configured roots
- detect created / modified / deleted files
- hash and debounce changed files
- emit one normalized event per meaningful change
- lock watcher state before rewriting `watch-state.json`
- ignore reserved runtime subtrees and future shadow logs so sidecars do not
  self-trigger recursive churn

### 3. Consolidator script
`scripts/process_intake_events.py`

Responsibilities:
- claim pending events
- classify them into domains
- compute recommended follow-up actions
- write queue summaries for humans and agents
- hold lock discipline for future projection steps

### 4. Output queue
Runtime queue root:
- `.agent-surface/events/incoming/`
- `.agent-surface/events/processing/`
- `.agent-surface/events/processed/`
- `.agent-surface/events/failed/`
- `.agent-surface/events/locks/`

### 5. First actions emitted by the skeleton
- `review_root_intake`
- `refresh_context_views`
- `refresh_shared_skills`
- `refresh_shared_agent_surface`
- `review_trace_drift`
- `consider_canon_promotion`

## Guardrails

- `consider_canon_promotion` is advisory only and must never auto-promote
  artifacts into canon
- append-only shadow logs are not ADRs and must not silently become decision
  truth
- projections such as `CONTEXT_L0.md` and `CONTEXT_L1.md` must never write back
  into canonical docs
- diagnostic imports and external probes run in isolated workspaces, never
  against live source-chain state

## Phase Boundary

### Included now
- polling-based filewatch skeleton
- normalized event queue
- processing claim-by-rename
- lock scaffolding
- queue summaries for shared agent awareness

### Deferred
- continuous daemonized watchers
- semantic indexing
- graph storage
- CRDT working state
- automatic canon promotion
- automatic multi-agent task assignment

## Success Criteria
- a new root intake file becomes a normalized event without manual narration
- multiple agents can read the same queue without stomping each other
- one consolidator can summarize what changed and what needs updating
- orient/shared-surface maintenance becomes an explicit follow-up action instead of a guess

## Immediate Follow-Ons
1. Add event-driven regeneration for `CONTEXT_L0.md` / `CONTEXT_L1.md` behind a lock.
2. Add event-driven skill refresh for `flossi0ullk-orient` and `flossi0ullk-shared-surface`.
3. Add root-fork intake heuristics so new GitHub forks become first-class intake events.
4. Expose the queue summary through a future `flossi0ullk-context` MCP surface.
5. Add append-only file shadow rollups under `.agent-surface/shadows/` with explicit
   watcher exclusion.
