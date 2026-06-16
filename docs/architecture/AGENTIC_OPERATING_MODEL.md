# FLOSSI0ULLK Agentic Operating Model

```yaml
id: "flossi0ullk-agentic-operating-model"
version: "0.1.0"
kind: "architecture_reference"
status: "Active"
updated: "2026-04-17"
truth_status: "Specified"
evidence_sources:
  - "docs/adr/ADR-8-radicle-dev-substrate.md"
  - "docs/research/Automated-Agent-Orchestration-Report_v1.0.0.md"
  - "docs/superpowers/specs/2026-04-12-local-agent-node-design.md"
  - "deep-flossi0ullkreport.md"
  - "oh-my-meta.md"
  - "packages/source_chain/cell.py"
  - "packages/metacoordinator_mcp/voters.py"
  - "packages/metacoordinator_mcp/hashline.py"
  - "scripts/hook_post_write.py"
```

## Purpose
This document defines the current operating structure for FLOSSI0ULLK's agentic collaboration stack. It is the shortest path from recent research synthesis to day-to-day execution.

The goal is not to build one giant agent. The goal is to compose a low-friction, high-traceability stack that:

- preserves sovereignty and fork visibility
- minimizes premium-token burn
- converts individual work into collective memory
- remains forward-compatible with Holochain runtime truth

## Canonical Stack

### Plane A: Dev-Plane Code and Collaboration
- `Radicle` is the canonical code substrate.
- `GitHub` is a mirror and interoperability surface, not the architectural center.
- `packages/source_chain/` is the immediate local provenance bridge.
- `packages/metacoordinator_mcp/` is the immediate routing and consensus bridge.

### Plane B: Runtime Truth and Validation
- `Holochain` remains the runtime substrate.
- Runtime truth lives in agent-centric source chains and DHT validation, not in dev-plane tooling.
- Plane A artifacts may publish into Plane B, but they do not bypass Plane B validation.

### Artifact and Event Distribution
- `IPFS/libp2p` remains the intended distribution/event layer for larger artifacts and broadcast streams when needed.
- Until that layer is built, the local source chain and repo filesystem are the active storage surfaces for traces and evidence.

## Four Harnesses

### 1. Execution Harness
Purpose: route tasks, spawn workers, run reviews, and submit claims/votes/decisions.

Current pieces:
- Claude `PreToolUse` checkpoint hook
- Claude `PostToolUse` hook
- Gemini `BeforeTool` checkpoint hook
- Gemini `AfterTool` hook
- local claim submission
- background consensus rounds
- Hashline-style checkpointed post-write verification
- file-based source chain

Near-term additions:
- consensus hook for structural edits
- Radicle patch / COB bridge

### 2. Memory Harness
Purpose: preserve actionable continuity without overloading the live context window.

Required shape:
- lightweight index always loadable
- topic files on-demand
- raw traces only grepped or selectively loaded
- generated `L0/L1` context projections derived from canon, not hand-maintained summaries

Near-term additions:
- Boulder-style task notepads
- KAIROS-style nightly consolidation
- Claim Truth Model labels on learnings

### 3. Retrieval Harness
Purpose: choose the right corpus before retrieval, instead of querying everything.

Canonical corpus order:
1. active specs and ADRs
2. project architecture and governance docs
3. current code and tests
4. local source-chain claims / votes / decisions
5. research docs
6. `_reference/`
7. later: Radicle COBs / patches

Rule: prefer corpus routing first, vector retrieval second. Centralized single-store RAG is not the target architecture.

The current canonical reference for this layer is
`docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md`.

### 4. Optimization Harness
Purpose: optimize the surrounding harnesses rather than model weights.

Target variables:
- routing tables
- prompt variants
- hook thresholds
- continuation policies
- retrieval policies
- memory distillation rules

Rule: full traces on disk, selective retrieval into context. No optimization loop may discard the raw evidence needed to debug long-horizon failures.

## Model Allocation Matrix

| Provider / Surface | Default role | Why |
|---|---|---|
| `Groq` | cheap critics, explorers, reviewers, dissenters, batch trace triage | high free throughput; good for many small loops |
| `Cerebras` | cheap parallel voters, background reviewers, large-context inspection where available | high free throughput and large windows |
| `Claude Code` | proposer, integrator, high-risk executor, final technical synthesis | best current coding workflow and operator-aligned execution surface |
| `Gemini` | multimodal analysis, research digestion, writing, design review, independent dissent | strong multimodal and complementary reasoning style |

### Practical routing rules
- Do not spend Claude turns on bulk background review when Groq/Cerebras can do it.
- Use Claude for edits with real blast radius, integration, and final judgment.
- Use Gemini when the task depends on image/PDF/UI interpretation or when a high-value dissenting view is needed.
- Use heterogeneous cheap voters before escalating to a premium synthesis pass.

## Token Discipline
- Store full traces; do not stuff full traces into every context.
- Keep premium models out of repetitive reviewer loops.
- Use cheap models to shortlist relevant traces and corpora before expensive synthesis.
- Design around 60-70% of any claimed maximum context window.
- Prefer additive bootstrap context over ever-more-complex loop logic.

## Operational Defaults
- Cheap loops are background by default.
- High-risk merges remain policy-gated.
- Claims default to `Unverified` until promoted by evidence.
- Disagreement is signal. Variance-driven conflict is not treated as neutrality.
- Any new automation must specify which harness it belongs to.

## Immediate High-Gain Moves
1. Prove the `Radicle -> provenance substrate` handshake.
2. Add Boulder/KAIROS-style memory structure on top of the local source chain.
3. Implement a consensus hook for structural changes.
4. Widen checkpointed Hashline verification into stronger structural policy gates.
5. Add a lightweight corpus router before any heavier retrieval work.
6. Archive every optimization cycle as a full-trace candidate for later MetaLoop work.

## Non-Goals for Now
- replacing the local source chain before the bridge is proven
- building one monolithic orchestration framework
- spending premium model budget on reviewer swarms
- pretending Holochain runtime truth already exists end-to-end

## Relationship to Other Canonical Docs
- `HOLISTIC_ARCHITECTURE.md` explains the project at macro scale
- `METAHARNESS_OPERATING_MODEL.md` defines how the shared code harnesses compose in practice
- `CONTEXT_DAEMON_ARCHITECTURE.md` defines the living context infrastructure and generated context views
- `ADR-8-radicle-dev-substrate.md` records the dev-plane substrate decision
- `2026-04-16-forward-momentum-radicle-meta-harnesses.md` sequences the work
