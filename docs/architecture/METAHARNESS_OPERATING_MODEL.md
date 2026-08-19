# FLOSSI0ULLK Metaharness Operating Model

```yaml
id: "flossi0ullk-metaharness-operating-model"
version: "0.2.0"
kind: "architecture_reference"
status: "Active"
updated: "2026-05-18"
truth_status: "Specified"
evidence_sources:
  - "docs/architecture/AGENTIC_OPERATING_MODEL.md"
  - "docs/research/2026-05-18-metaharness-unification.md"
  - "docs/superpowers/specs/2026-04-12-local-agent-node-design.md"
  - "shared-agent-surface.json"
  - "shared-context-surface.json"
  - "shared-hook-surface.json"
  - "shared-skill-surface.json"
  - "packages/activity_log/schema.py"
  - "scripts/context_router.py"
  - "scripts/review_queue.py"
  - "scripts/hook_post_write.py"
  - "packages/metacoordinator_mcp/hashline.py"
  - "packages/metacoordinator_mcp/voters.py"
```

## Purpose
This document defines the meta for using all active FLOSSI0ULLK code harnesses together.

The metaharness is not another super-agent. It is the policy layer that composes:

- shared canon
- shared context
- shared skills
- shared hooks
- execution agents
- cheap consensus loops
- durable provenance

Its job is to keep all of those surfaces aligned while minimizing waste.

## Meta
The metaharness should optimize for:

1. one canonical source per concern
2. one primary writer per task
3. many cheap critics in parallel
4. full traces on disk, selective context in memory
5. promotion of durable learnings back into canon only after evidence

In short:

- manifests are canonical
- materializers project into agent-native config
- one executor lands edits
- background loops review and vote
- provenance captures the result
- stable learnings become docs, skills, or policy

## Active Harnesses

### 1. Canon Harness
Purpose: hold the shared source of truth.

Current surfaces:
- `shared-agent-surface.json`
- `shared-context-surface.json`
- `shared-hook-surface.json`
- `shared-skill-surface.json`
- ADRs, specs, and architecture docs

Rule:
- never hand-edit the generated agent views when the canonical manifest is the real source

### 2. Context Harness
Purpose: load only the right context for the current task.

Current pieces:
- `scripts/context_router.py`
- `.agent-surface/context/context-registry.json`
- `.agent-surface/context/CONTEXT_L0.md`
- `.agent-surface/context/CONTEXT_L1.md`
- Serena project memories
- portable skills pointing back into canon

Rule:
- route corpus first, then retrieve inside the chosen corpus

### 3. Execution Harness
Purpose: do the real work.

Default roles:
- `Claude Code` or `Codex`: primary editor / integrator
- `OpenCode`: secondary executor when useful
- `Serena`: code understanding substrate, not the decider

Rule:
- only one primary writer owns a concrete change set at a time

### 4. Consensus Harness
Purpose: review substantive edits cheaply and preserve disagreement.

Current pieces:
- `hook_pre_write.py`
- `hook_post_write.py`
- `hook_bg_round.py`
- `packages/metacoordinator_mcp/hashline.py`
- `packages/metacoordinator_mcp/`
- `packages/source_chain/`
- Groq, Cerebras, Flowith-backed voter rosters

Rule:
- use cheap heterogeneous review first
- escalate to premium synthesis only when blast radius justifies it
- derive exact post-images from pre-write checkpoints when possible so stale landings fail closed
- avoid correlated cheap-voter swarms; strategic polls should span provider surfaces and model families

### 5. Reflection Harness
Purpose: turn traces into better routing, better prompts, and better policy.

Current pieces:
- `~/.floss_agent/hook.log`
- `~/.floss_agent/traces/consensus/`
- skill and context surfaces

Near-term additions:
- Boulder-style task notes
- nightly consolidation
- skill distillation

Rule:
- optimize the harnesses, not the model weights

### 6. Publish Harness
Purpose: move accepted work onto the collaboration and provenance substrates.

Target flow:
- `Radicle` first for dev-plane collaboration
- `GitHub` second as mirror / interoperability
- `Holochain` later as runtime provenance and validation

Rule:
- dev-plane collaboration never bypasses runtime-plane truth

## Unified Conventions

Truth status: Specified with partial implementation evidence as of 2026-05-18.

The metaharness is atomic and holistic by convention, not by one central
controller. The current convergence target has three shared surfaces:

1. **Atomic interface:** every agentic action SHOULD be representable as one
   `Action` record from `packages/activity_log/schema.py`.
2. **Holistic activity surface:** every harness SHOULD tee durable work into the
   global append-only `.agent-surface/activity.jsonl` while preserving any
   useful subsystem logs.
3. **Review queue surface:** staged artifacts SHOULD remain in their native
   staging directories, while `scripts/review_queue.py` rolls them up into one
   read-only queue for human review.
4. **AI/harness roster surface:** provider/model imports, agent instruction
   files, MCP servers, and startup packets SHOULD roll up through
   `shared-ai-roster-surface.json` into `.agent-surface/harness/`. The JSON
   roster is the comprehensive machine inventory; the markdown roster and
   update packet are compact operator/harness entry points.

Current implementation evidence:

- Verified: `packages/activity_log/schema.py` defines `Action`, `append_action()`, and
  helper functions for the global activity log.
- Verified: `packages/reasoning_ensemble/synthesizer.py` emits unified
  `ensemble_synthesis` actions.
- Verified: `packages/reasoning_ensemble/router.py` preserves the reasoning
  subsystem log and tees each `router_decision` into the global Action log.
- Verified: `scripts/review_queue.py` rolls up `.agent-surface/harvest/staging/` and
  `docs/knowledge_log/staging/` without mutating staged files.
- Verified: `heartbeat.py`, `harvest_reuse_ledger.py`,
  `poll_high_roi_actions.py`, and `autonomous_synthesis_loop.py` emit global
  Actions for heartbeat work items, harvest terminal events, high-ROI polls,
  and staged synthesis drafts.

### Runtime Budget Discipline

Truth status: Specified with test coverage as of 2026-05-19.

Heartbeat may run cheap local work frequently, but voter-backed polls must pass
the runtime budget policy in `docs/specs/heartbeat-runtime-budget.spec.md`.
The current policy is:

- routine heartbeat polls use the `balanced` voter profile;
- `diverse-max` is reserved for explicit high-diversity checks or slow
  confirmation sweeps;
- unchanged high-ROI slates are skipped instead of repeatedly spending Groq and
  other provider token budgets;
- `poll_high_roi_actions.py` defaults to `balanced`;
- the `heartbeat` voter profile alias resolves to `balanced`;
- actual poll round counts are parsed when possible so daily caps remain honest.

Operator-facing details live in `docs/architecture/RUNTIME_SURFACES.md`.

The review queue is intentionally a roll-up, not a new staging convention.
Existing staging locations stay intact so each harness can preserve its local
debugging shape; the global queue gives agents and humans one place to see what
needs review.

## Default Metaharness Loop
1. Route the task with the context harness.
2. Load the smallest relevant generated `L0/L1` view, skill, or canon surface.
3. Choose one primary executor.
4. Use Serena and cheap helpers for understanding, not authority.
5. Land edits through an agent-native client whose config was materialized from canon.
6. Trigger shared hooks on substantive mutations.
7. Run cheap consensus and write claims, votes, and traces.
8. Emit or tee a unified `Action` record for durable work.
9. Roll up staged outputs with `scripts/review_queue.py` before promotion.
10. Refresh the AI/harness roster when provider imports, agent instructions, or
    shared startup invariants change.
11. Promote only durable learnings into manifests, skills, ADRs, or plans.
12. Publish accepted work to the dev-plane substrate.

## Allocation Policy

### Premium surfaces
- `Claude Code` and other premium interactive coding surfaces should be used for:
  - integration
  - high-risk edits
  - final synthesis
  - architectural judgment

### Cheap surfaces
- `Groq`, `Cerebras`, `Flowith`, and similar free or low-cost providers should be used for:
  - critics
  - reviewers
  - dissenters
  - trace triage
  - repetitive consensus passes

### Diversity policy
- nontrivial planning polls should prefer at least three provider surfaces and four model families
- do not mistake multiple endpoints of the same family for genuine independence
- preserve dissent and variance as signal; do not optimize them away

### Cross-check surfaces
- `Gemini` should be used for:
  - multimodal review
  - independent dissent
  - document and design synthesis
  - alternative reasoning style on important plans

## What To Materialize
The metaharness should converge agent-native surfaces only where overlap is real:

- MCP servers
- shared hooks
- shared skills
- shared context pointers

Do not force fake portability for surfaces that are not actually shared yet.

## What Not To Do
- do not build one giant omni-agent that tries to carry every context
- do not spend premium tokens on reviewer swarms
- do not hand-edit generated client config when a manifest exists
- do not flatten disagreement into fake consensus
- do not promote every transient insight into canon
- do not treat same-family reviewer bundles as a substitute for provider diversity

## Success Metrics
- less drift across Claude, Gemini, Codex, and OpenCode
- lower premium-token burn per accepted change
- faster recovery after context loss
- more claims, votes, and traces per substantive decision
- more durable skills and docs extracted from repeated work

## Relationship to Other Canonical Docs
- `AGENTIC_OPERATING_MODEL.md` defines the broader stack and harness roles
- `HOLISTIC_ARCHITECTURE.md` explains the project at macro scale
- `CONTEXT_DAEMON_ARCHITECTURE.md` defines the living context stack and compression doctrine
- `docs/research/2026-05-18-metaharness-unification.md` records the migration plan for unified Action/activity/review conventions
- `2026-04-16-forward-momentum-radicle-meta-harnesses.md` sequences near-term work
- `shared-hook-surface.json` is the current canonical hook-policy source
