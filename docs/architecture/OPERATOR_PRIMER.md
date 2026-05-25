# FLOSSI0ULLK Operator Primer

```yaml
id: "flossi0ullk-operator-primer"
version: "0.1.0"
kind: "operator_primer"
status: "Active"
updated: "2026-05-19"
truth_status: "Specified with verified runtime anchors"
evidence_sources:
  - "INDEX.md"
  - "FLOSS/docs/architecture/RUNTIME_SURFACES.md"
  - "FLOSS/docs/architecture/HOLISTIC_ARCHITECTURE.md"
  - "FLOSS/docs/architecture/METAHARNESS_OPERATING_MODEL.md"
  - "FLOSS/docs/specs/heartbeat-runtime-budget.spec.md"
  - "FLOSS/docs/specs/phase0-substrate-bridge.spec.md"
  - "FLOSS/docs/specs/reasoning-ensemble-router.spec.md"
  - "FLOSS/docs/specs/reasoning-ensemble-synthesizer.spec.md"
  - "FLOSS/docs/specs/reasoning-ensemble-mcp.spec.md"
  - "FLOSS/docs/specs/consent-payload.spec.md"
  - "FLOSS/docs/adr/ADR-12-consent-gate-protocol.md"
  - "FLOSS/docs/research/2026-05-15-working-todo-list.md"
```

## What This Is

FLOSSI0ULLK is a decentralized knowledge commons and coordination substrate.
The short practical version:

- Holochain is the intended truth/provenance substrate.
- Rust integrity zomes and schemas validate load-bearing claims.
- LLMs assist with search, synthesis, formatting, critique, and proposal work.
- Multi-model consensus records decisions, but does not become an authority.
- Shared context, memory, skills, hooks, and MCP servers keep agents aligned.

The project is not "an AI chat app." It is an attempt to make multi-agent,
human-authored, consent-aware coordination durable enough that humans and models
can build on the same state without constantly rediscovering the same context.

## Current State

Use this as the default phase correction:

| Area | Status | Meaning |
|---|---|---|
| MVP Phase 0 substrate viability | Verified complete | DNA/WASM/Tryorama and ontology integrity passed per `FLOSS/MVP_PLAN.md`; do not restart this as the current gate. |
| Orchestration substrate bridge | Specified | Current proof gate: publish, provenance, independent verify, query, fork-visible conflict, no privileged verifier. |
| Local consensus gateway | Verified at module level | ADR-10 / `ADR-MCP-ORCHESTRATOR`; analog votes, source-chain append, passive router. |
| Heartbeat automation | Stopped intentionally | `C:\~shit\.agent-surface\heartbeat\STOP` is present after the 2026-05-19 Groq token-budget fix. |
| Reasoning ensemble | Specified prototype | Router, Synthesizer, and MCP wrapper exist; specs were retrofitted after code and now bind future changes. |
| Consent gate | Implementation-backed draft | ADR-12 stub, JSON schema, Holochain entry types, consent coordinator, DNA wiring, Rust unit tests, static wiring tests, release WASMs, hApp packing, and consent Tryorama scenarios exist; action-time gating remains pending before Substrate-class ratification. |

If another file says "Phase 0 Tryorama is still the blocker," treat it as
evidence drift unless it explicitly distinguishes the separate orchestration
substrate-bridge validation.

## Mental Model

There are four operational planes:

| Plane | What belongs there | Examples |
|---|---|---|
| Canon | Human-reviewable project truth | `INDEX.md`, ADRs, specs, architecture docs, shared manifests |
| Runtime | Local automation and traces | `.agent-surface/`, heartbeat logs, poll drafts, activity log |
| Source chain | Durable decision evidence | claims, votes, decisions under `~/.floss_agent/.../source_chain/` |
| Reference | External background material | `_reference/`, external papers, fork harvest drafts |

Do not promote runtime output into canon just because a model produced it. Canon
changes need an explicit doc/spec/ADR update and, when load-bearing, a consensus
claim or other provenance pointer.

## How To Start A Session

1. Read `.agent-surface/context/CONTEXT_L0.md`.
2. Read `.agent-surface/context/RESUMPTION.md`.
3. Read `.agent-surface/memory/AGENT_MEMORY.md` if the task has project history.
4. If the task touches runtime, read `FLOSS/docs/architecture/RUNTIME_SURFACES.md`.
5. If the task changes behavior, read the relevant spec in `FLOSS/docs/specs/`.
6. If there is no relevant spec, write the spec before changing behavior.

For routed context:

```powershell
python C:\~shit\FLOSS\scripts\context_router.py "what I am about to do" --format markdown --limit 4
```

## How To Use The System

Use the cheapest surface that can do the job:

| Need | Use |
|---|---|
| Current status | `.agent-surface/context/RESUMPTION.md`, working todo |
| Human-readable runtime map | `FLOSS/docs/architecture/RUNTIME_SURFACES.md` |
| Project architecture | `FLOSS/docs/architecture/HOLISTIC_ARCHITECTURE.md` |
| Operating model | `FLOSS/docs/architecture/METAHARNESS_OPERATING_MODEL.md` |
| Decision history | `FLOSS/docs/adr/INDEX.md`, ADR-Suite v2.0 |
| Shared memory | `FLOSS/docs/agent-memory/MEMORY.md` |
| Agent-native projections | generated from shared manifests, not edited directly |
| Consensus decisions | `flossiullk-consensus` MCP / source-chain files |
| Reasoning debate | `flossiullk-reasoning-ensemble` MCP or reasoning-ensemble skill |

The heartbeat is a composer, not a manager. The consensus gateway is a router,
not a judge. The reasoning ensemble is a thinking aid, not a canonicalizer.

## Emergency Controls

Heartbeat stop file:

```powershell
New-Item -Path C:\~shit\.agent-surface\heartbeat\STOP -Force
```

Resume only when the budget posture is intentional:

```powershell
Remove-Item -LiteralPath C:\~shit\.agent-surface\heartbeat\STOP
python C:\~shit\FLOSS\scripts\heartbeat.py --once
```

Inspect current runtime state:

```powershell
Get-Content C:\~shit\.agent-surface\context\RESUMPTION.md
Get-Content C:\~shit\.agent-surface\heartbeat\daily_state.json
Get-Content C:\~shit\.agent-surface\heartbeat\poll_state.json
Get-Content C:\~shit\.agent-surface\activity.jsonl -Tail 20
```

Routine heartbeat consensus should use `balanced`. `diverse-max` is intentional
spend for important checks, not a default health pulse.

## Change Discipline

For runtime or architecture behavior:

1. Update or create the spec.
2. Add a failing test when code behavior is involved.
3. Implement the smallest scoped change.
4. Run focused tests.
5. Regenerate shared projections if manifests changed.
6. Log provenance in the working todo or activity log.
7. Update `INDEX.md` when a canonical entry point changes.

Retrofitted specs are acceptable as debt repayment, but future changes should
not repeat the code-first sequence unless explicitly marked as emergency work.

## What Not To Do

- Do not restart old MVP Phase 0 Tryorama work as if it is the active gate.
- Do not remove the heartbeat STOP file just to see what happens.
- Do not run `diverse-max` repeatedly from heartbeat without a changed slate.
- Do not edit generated projections when a canonical manifest can be changed.
- Do not treat model agreement as truth without schema, substrate, or provenance.
- Do not promote fork harvest drafts just to make the ledger bigger.
- Do not rewrite ADR evidence drift silently; reconcile it explicitly.

## Current Best Next Moves

As of 2026-05-19, high-leverage work is:

1. Implement ADR-12 action-time governed-pattern enforcement, then harden DID/header binding.
2. Run the orchestration substrate-bridge validation from `phase0-substrate-bridge.spec.md`.
3. Register and pilot the reasoning ensemble MCP under real agent use.
4. Reconcile ADR-2 evidence drift against the verified MVP Phase 0 state.
5. Keep heartbeat budgeted until staged synthesis drafts and daily round state are under control.

When in doubt, slow down at the canon boundary. Fast iteration belongs in Plane A;
promotion belongs behind specs, tests, provenance, and consent.
