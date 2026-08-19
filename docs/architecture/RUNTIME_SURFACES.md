# FLOSSI0ULLK Runtime Surfaces

```yaml
id: "flossi0ullk-runtime-surfaces"
version: "0.1.0"
kind: "operator_guide"
status: "Active"
updated: "2026-05-24"
truth_status: "Specified with partial implementation evidence"
evidence_sources:
  - "FLOSS/docs/architecture/METAHARNESS_OPERATING_MODEL.md"
  - "FLOSS/docs/specs/heartbeat-runtime-budget.spec.md"
  - "FLOSS/scripts/heartbeat.py"
  - "FLOSS/scripts/poll_high_roi_actions.py"
  - "FLOSS/scripts/heartbeat_slate.py"
  - "FLOSS/scripts/review_queue.py"
  - "FLOSS/packages/metacoordinator_mcp/"
  - "FLOSS/packages/activity_log/schema.py"
  - "FLOSS/packages/activity_log/provenance.py"
  - "FLOSS/docs/specs/provenance-packet.spec.md"
```

## What This Is

This is the operator map for the local FLOSSI0ULLK metaharness: the scripts,
MCP surfaces, logs, and generated projections that run around the project.

If you need the shortest human-first overview before operating anything, start
with `FLOSS/docs/architecture/OPERATOR_PRIMER.md`, then come back here for
commands and runtime inventory.

The short version:

- Canon lives in docs, specs, ADRs, and shared manifests.
- Runtime traces live under `.agent-surface/` and `~/.floss_agent/`.
- Heartbeat is a local composer, not an authority.
- Consensus gateway records claims/votes/decisions, but does not decide truth by itself.
- Provenance packets sign cross-agent handoffs before governed claims can bind.
- Generated projections are disposable; canonical sources are not.

## Emergency Controls

### Stop Heartbeat

Create:

```powershell
New-Item -Path C:\~shit\.agent-surface\heartbeat\STOP -Force
```

Heartbeat checks this file before every tick and between work items.

### Resume Heartbeat

Delete:

```powershell
Remove-Item -LiteralPath C:\~shit\.agent-surface\heartbeat\STOP
```

Only resume after `FLOSS/docs/specs/heartbeat-runtime-budget.spec.md` still
matches the intended budget posture.

### Inspect Current State

```powershell
Get-Content C:\~shit\.agent-surface\context\RESUMPTION.md
Get-Content C:\~shit\.agent-surface\heartbeat\daily_state.json
Get-Content C:\~shit\.agent-surface\heartbeat\poll_state.json
Get-Content C:\~shit\.agent-surface\heartbeat\ticks.log -Tail 40
Get-Content C:\~shit\.agent-surface\activity.jsonl -Tail 20
python C:\~shit\FLOSS\scripts\audit_provenance_packets.py
```

## Runtime Inventory

| Surface | Entry Point | Cost | Output | Canonical Spec / Doc |
|---|---|---:|---|---|
| Heartbeat composer | `FLOSS/scripts/heartbeat.py` | Mixed | `.agent-surface/heartbeat/`, `.agent-surface/context/RESUMPTION.md` | `docs/specs/heartbeat-runtime-budget.spec.md` |
| Dynamic poll slate | `FLOSS/scripts/heartbeat_slate.py` | Local | `.agent-surface/heartbeat/next_slate.json` | `docs/architecture/METAHARNESS_OPERATING_MODEL.md` |
| High-ROI poll | `FLOSS/scripts/poll_high_roi_actions.py` | Voter calls | `.agent-surface/polls/`, source-chain claims | `docs/specs/heartbeat-runtime-budget.spec.md`, ADR-10 |
| Consensus gateway | `FLOSS/packages/metacoordinator_mcp/` | Voter calls | `~/.floss_agent/cells/.../source_chain/` | ADR-10 / `ADR-MCP-ORCHESTRATOR` |
| Reasoning ensemble | `FLOSS/packages/reasoning_ensemble/` + `flossiullk-reasoning-ensemble` MCP | Local/LLM calls | `.agent-surface/reasoning/` | `docs/specs/reasoning-ensemble-{router,synthesizer,mcp}.spec.md` |
| Activity log | `FLOSS/packages/activity_log/schema.py` | Local | `.agent-surface/activity.jsonl` | `docs/research/2026-05-18-metaharness-unification.md` |
| Provenance packets | `FLOSS/packages/activity_log/provenance.py`, `FLOSS/scripts/audit_provenance_packets.py` | Local | `.agent-surface/provenance/` | `docs/specs/provenance-packet.spec.md` |
| Review queue | `FLOSS/scripts/review_queue.py` | Local | read-only rollup | `docs/architecture/METAHARNESS_OPERATING_MODEL.md` |
| Shared context | `FLOSS/scripts/materialize_shared_context_surface.py` | Local | `.agent-surface/context/CONTEXT_L0.md`, `CONTEXT_L1.md` | `shared-context-surface.json` |
| Shared skills | `FLOSS/scripts/materialize_shared_skill_surface.py` | Local | Codex/Claude/Gemini/OpenCode skills | `shared-skill-surface.json` |
| Shared memory | `FLOSS/scripts/materialize_shared_agent_memory.py` | Local | `FLOSS/docs/agent-memory/`, `.agent-surface/memory/` | `shared-agent-memory-surface.json` |
| AI/harness roster | `FLOSS/scripts/materialize_shared_ai_roster.py` | Local | `.agent-surface/harness/AI_ROSTER.md`, `ai-roster.json`, `HARNESS_UPDATE_PACKET.md` | `shared-ai-roster-surface.json` |

## Token-Budget Rules

The heartbeat bug fixed on 2026-05-19 was simple: high-diversity polls ran too
often even when the slate had not changed.

Current rules:

- routine heartbeat polls use `balanced`;
- `heartbeat` voter-profile alias resolves to `balanced`;
- `poll_high_roi_actions.py` defaults to `balanced`;
- `diverse-max` is opt-in or slow periodic confirmation only;
- unchanged high-ROI slates are skipped until `FLOSS_HEARTBEAT_CONFIRM_INTERVAL_TICKS` elapses;
- poll round accounting parses actual ranked results when possible.
- autonomous synthesis is skipped when staged drafts already meet
  `FLOSS_SYNTHESIS_STAGING_CAP`.

Useful overrides:

```powershell
$env:FLOSS_HEARTBEAT_DISABLE_POLLS = "1"
$env:FLOSS_HEARTBEAT_PROFILE = "balanced"
$env:FLOSS_HEARTBEAT_WIDE_PROFILE = "diverse-max"
$env:FLOSS_HEARTBEAT_WIDE_INTERVAL_TICKS = "72"
$env:FLOSS_HEARTBEAT_CONFIRM_INTERVAL_TICKS = "72"
$env:FLOSS_DAILY_ROUND_CAP = "40"
$env:FLOSS_HEARTBEAT_DISABLE_SYNTHESIS = "1"
$env:FLOSS_SYNTHESIS_STAGING_CAP = "25"
```

## SDD Discipline

When changing a runtime surface:

1. Write or update a spec in `FLOSS/docs/specs/`.
2. Add a failing test for the behavior.
3. Change the runtime code.
4. Run focused tests first, then the relevant broader slice.
5. Append durable provenance to `.agent-surface/activity.jsonl` or the working todo.
6. Update this guide if an operator would need to know the change exists.

## Common Commands

Read the operator primer:

```powershell
Get-Content C:\~shit\FLOSS\docs\architecture\OPERATOR_PRIMER.md
```

Run heartbeat once without doing work if STOP is present:

```powershell
python C:\~shit\FLOSS\scripts\heartbeat.py --once
```

Preview the current review queue:

```powershell
python C:\~shit\FLOSS\scripts\review_queue.py --limit 20
```

Audit provenance packets:

```powershell
python C:\~shit\FLOSS\scripts\audit_provenance_packets.py
python C:\~shit\FLOSS\scripts\audit_provenance_packets.py --json
```

Check shared projections:

```powershell
python C:\~shit\FLOSS\scripts\materialize_shared_context_surface.py --workspace-root C:\~shit --check
python C:\~shit\FLOSS\scripts\materialize_shared_skill_surface.py --workspace-root C:\~shit --check
python C:\~shit\FLOSS\scripts\materialize_shared_agent_memory.py --workspace-root C:\~shit --check
python C:\~shit\FLOSS\scripts\materialize_shared_ai_roster.py --workspace-root C:\~shit --check
python C:\~shit\FLOSS\scripts\materialize_shared_agent_surface.py --workspace-root C:\~shit --check
```

Run the token-budget tests:

```powershell
cd C:\~shit\FLOSS
python -m pytest scripts\tests\test_heartbeat_budget.py packages\metacoordinator_mcp\tests\test_voters.py -q
```

## Promotion Boundary

Runtime output is not canon by default.

- `.agent-surface/heartbeat/` is operational state.
- `.agent-surface/polls/` is evidence and review material.
- `.agent-surface/activity.jsonl` is durable provenance.
- `.agent-surface/provenance/` is signed Plane A packet evidence.
- `~/.floss_agent/.../source_chain/` is local source-chain evidence.
- Canon changes still require doc/spec/ADR updates and, when load-bearing, consensus claims.
