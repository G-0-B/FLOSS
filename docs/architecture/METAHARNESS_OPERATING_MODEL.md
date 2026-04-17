# FLOSSI0ULLK Metaharness Operating Model

```yaml
id: "flossi0ullk-metaharness-operating-model"
version: "0.1.0"
kind: "architecture_reference"
status: "Active"
updated: "2026-04-17"
truth_status: "Specified"
evidence_sources:
  - "docs/architecture/AGENTIC_OPERATING_MODEL.md"
  - "docs/superpowers/specs/2026-04-12-local-agent-node-design.md"
  - "shared-agent-surface.json"
  - "shared-context-surface.json"
  - "shared-hook-surface.json"
  - "shared-skill-surface.json"
  - "scripts/context_router.py"
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

## Default Metaharness Loop
1. Route the task with the context harness.
2. Load the smallest relevant skill or canon surface.
3. Choose one primary executor.
4. Use Serena and cheap helpers for understanding, not authority.
5. Land edits through an agent-native client whose config was materialized from canon.
6. Trigger shared hooks on substantive mutations.
7. Run cheap consensus and write claims, votes, and traces.
8. Promote only durable learnings into manifests, skills, ADRs, or plans.
9. Publish accepted work to the dev-plane substrate.

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
- `2026-04-16-forward-momentum-radicle-meta-harnesses.md` sequences near-term work
- `shared-hook-surface.json` is the current canonical hook-policy source
