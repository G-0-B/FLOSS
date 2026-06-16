---
id: project-filewatch-intake-skeleton
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_filewatch_intake_skeleton.md
title: Filewatch metaharness intake skeleton landed
legacy_description: Polling-based watcher + claim-by-rename event queue under .agent-surface/events/
  — observers many, writers one-per-surface
origin_session_id: 567c823f-3cba-4d75-866d-600bd4286e6f
---

A minimal filewatch + consolidation skeleton has landed under `FLOSS/scripts/`:

- `scripts/watch_intake.py` — polling-based observer; hashes/debounces changes; emits normalized events.
- `scripts/process_intake_events.py` — consolidator; classifies events, writes summaries, holds locks.
- `scripts/autonomous_synthesis_loop.py` — sibling automation (sample, don't assume specifics).
- `docs/superpowers/plans/2026-04-19-filewatch-metaharness.md` — the plan.
- `docs/specs/intake-event.schema.json` + `intake-event.spec.md` — the queue contract.

**Concurrency model:**
- Many observers, **one writer per target** (canonical surface or generated output).
- Claim work by rename: `incoming/` → `processing/` → `processed/` (or `failed/`).
- Surface-level locks: `shared-{context,skill,agent}-surface.lock`, `summary.lock`, `watch-state.lock`.
- Reserved subtrees under `.agent-surface/`: `events/`, `context/`, `skills/`, `hooks/`, `shadows/` — watchers must exclude these to avoid recursive churn.

**Guardrails (do not violate):**
- `consider_canon_promotion` is **advisory only** — never auto-promote into canon.
- Append-only shadow logs are not ADRs; they cannot become decision truth silently.
- Generated `CONTEXT_L0/L1.md` projections must never write back into canonical docs.
- Diagnostic imports / external probes run in isolated workspaces, never against live source-chain state.

**Deferred (not yet built, do not assume):**
- Continuous daemonized watchers (current is polling-based).
- Semantic indexing, graph storage, CRDT working state.
- Automatic canon promotion, automatic multi-agent task assignment.

**How to apply:**
- When a new root intake doc lands, the *expected* path is: watcher emits event → consolidator classifies → action like `review_root_intake` is recommended → human or agent acts on it → only durable promotions reach canon.
- Don't write into `.agent-surface/events/processed/` directly; use the rename protocol.
- Don't add a sibling watcher under `.agent-surface/` without explicit exclusion.
