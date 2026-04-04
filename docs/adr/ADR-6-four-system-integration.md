# ADR-6: Four-System Meta-Orchestration Integration

**Status:** Proposed
**Date:** 2026-04-04
**Truth Status:** Specified (integration seams identified, not yet implemented)
**Friction Tier:** Medium (adds integration layer, does not modify core substrate)

---

## Context

The meta-orchestration space has converged on a shared problem: the LLM is frozen, all intelligence lives in the surrounding code (the "harness"), and optimizing that harness is the highest-leverage engineering work. Four systems attack this from four different angles:

| System | Strength | Gap |
|---|---|---|
| **Meta Harness** (Stanford IRIS + MIT) | Automated harness optimization via 10M-token full-trace inspection | Runtime orchestration, governance, multi-agent coordination |
| **omo (oh-my-openagent)** | 11 specialized agents, 48 hooks, Hashline, Boulder persistence | Git-based isolation, automated optimization, provenance/governance |
| **OMX/OMC (oh-my-codex/claudecode)** | Git worktree agent isolation, mixed-provider teams, portable orchestration | Deep agent specialization, symbolic validation, governance |
| **FLOSSI0ULLK MetaCoordinator** | Ternary consensus, ADR governance, symbolic-first, Claim Truth Model | Production hook system, background parallelism, git-based isolation |

None of these systems solves the full problem alone. Together they cover the full surface.

### Source Material

- Four-System Integration Analysis (`docs/research/4-4-26-FLOSSI0ULLK-Four-System-Integration-Analysis.md`)
- Meta Harness paper (arXiv:2603.28052, Stanford IRIS + MIT, 2026-03-30)
- oh-my-openagent (github.com/code-yeongyu, 47.5k stars)
- oh-my-codex / oh-my-claudecode (github.com/Yeachan-Heo)
- ADR-5 (Cognitive Virology Pattern) — FLOSSI0ULLK is itself a harness
- ADR-3 (Metaprompt Kernelization) — the kernel IS an optimized harness pre-configuration

## Problem Statement

FLOSSI0ULLK's MetaCoordinator is the governance layer of a meta-orchestration stack, but runs without:

1. A production hook system (omo has 48 production-tested hooks)
2. Git-based agent isolation (OMX has worktree-per-worker since v0.10.0)
3. Automated harness optimization (Meta Harness has formal framework + 10M-token traces)
4. Three-layer persistent memory (Claude Code KAIROS pattern)

Building all four from scratch would duplicate work that is already open-source. Picking one vendor lock-in kills FLOSSI0ULLK's "ride every model, every substrate" principle.

The integration question: can FLOSSI0ULLK adopt patterns from all three external systems, contribute governance back to them, and let Meta Harness optimize the combined system automatically?

## Decision

Integrate FLOSSI0ULLK with the three other systems via **five discrete, independently-reversible seams**. Each seam is small enough to validate in isolation. None requires modifying the core substrate (Holochain DNA, integrity zomes, or ADR format).

### The Five Seams

| # | Seam | Contribution Direction | Dependencies |
|---|------|----------------------|-------------|
| 1 | **Consensus-Gate Hook** | FLOSSI0ULLK contributes ternary consensus → omo hook system | OpenClaw running (done) |
| 2 | **Git Worktree Isolation** | OMX contributes worktree-per-agent → MetaCoordinator | Git repo structure |
| 3 | **Harness Optimization of LiteLLM Routing** | Meta Harness optimizes FLOSSI0ULLK's routing table | Full-trace storage (Seam 2 needed) |
| 4 | **KAIROS Three-Layer Memory** | Claude Code pattern → MetaCoordinator context management | ADR system (exists) |
| 5 | **OpenClaw Gateway Events** | OMX + OpenClaw route FLOSSI0ULLK events cross-system | OpenClaw + OMX installed |

### Stack Composition

```
Meta Harness          — optimizes the harness
  OMX/omo             — orchestrates the agents
    OpenClaw/LiteLLM  — routes and executes
      FLOSSI0ULLK     — governs, validates, records
```

Each layer is replaceable. Each seam is independently reversible. No layer is trusted to be correct without governance from the layer below it.

### Seam 1 Detail (Implemented First)

**Goal:** Expose FLOSSI0ULLK's ternary consensus to omo agents as a pre-execution gate.

**Mechanism:**
1. When an agent proposes a structural change (AST diff > threshold), omo's hook system fires a `consensus-requested` event
2. Hook serializes proposed change as a Claim with `truth_status: "Unverified"`
3. Claim is sent to MetaCoordinator via MCP context sync
4. Execution blocks until ternary vote received (+1/+1/+1 unanimous, or +1/+1/0 with human override)
5. Decision recorded as ADR with provenance

**Why first:** Establishes the MCP communication channel that Seams 2-5 also depend on. Smallest blast radius. Fastest validation loop.

## Implementation Strategy

### Phase A — Seam 1 Prototype (NOW)

1. Create `packages/orchestrator/consensus_gate.py` — MCP hook handler
2. Create `docs/specs/consensus-gate.spec.md` — hook contract (Claim schema, vote schema, ADR output format)
3. Create `packages/orchestrator/claim_schema.py` — Pydantic models for Claim/Vote/Decision
4. Write unit tests with 3 mock voters (no real LLM calls)
5. Document integration with omo's `createConsensusGateHook()` factory pattern

### Phase B — Seams 2 & 4 (LATER)

- Seam 2: Adopt OMX worktree pattern after Phase A validates MCP channel
- Seam 4: KAIROS three-layer memory after ADR volume justifies it (>20 ADRs)

### Phase C — Seams 3 & 5 (LATER)

- Seam 3: Meta Harness optimization requires full-trace storage infrastructure
- Seam 5: Gateway events require OpenClaw and OMX both running in integration environment

## Validation Criteria

This ADR moves from Proposed → Accepted when:

1. **Seam 1 operational:** Consensus-gate hook accepts a Claim, routes to 3 mock voters, returns decision, writes ADR stub
2. **Reversibility proven:** Hook can be disabled without breaking the hosting agent (omo continues running without MetaCoordinator)
3. **Symbolic validation:** Each Claim validates against `claim-schema.json` before vote routing
4. **Provenance preserved:** Decision ADR records voter identities, votes, and rationale

This ADR moves from Accepted → Validated when:

1. At least 1 real structural change has been gated through the hook in a working agent session
2. A Claim has been rejected (returned -1 from at least one voter) and execution blocked
3. Human override path has been exercised on a +1/+1/0 decision

## Consequences

### Immediate (NOW)

- Seam 1 spec + schema + prototype in `packages/orchestrator/`
- No modifications to Holochain DNA, integrity zomes, or existing ADRs
- FLOSSI0ULLK governance becomes invocable from any system speaking MCP

### Deferred (LATER)

- Full five-seam integration requires OMX, OpenClaw, and omo all running
- Meta Harness optimization requires full-trace infrastructure (~10M tokens/iteration)
- Multi-PC deployment depends on Seam 2 (worktree isolation) being operational

### Trade-offs Accepted

- **Dependency surface:** Each seam adds a system FLOSSI0ULLK can fail with. Mitigated by independent reversibility.
- **Integration lag:** External systems evolve at their own pace. Mitigated by versioning each seam independently.
- **Governance overhead:** Ternary consensus is slower than binary approval. Accepted — speed is not the goal; correctness is.

## Related Documents

- `docs/research/4-4-26-FLOSSI0ULLK-Four-System-Integration-Analysis.md` — full comparative analysis
- `docs/adr/ADR-3-metaprompt-kernelization.md` — Metaprompt as harness pre-configuration
- `docs/adr/ADR-4-spec-driven-development.md` — spec-first applies to seam contracts
- `docs/adr/ADR-5-cognitive-virology-pattern.md` — FLOSSI0ULLK IS a harness
- `docs/specs/consensus-gate.spec.md` — Seam 1 contract (to be created)

### External References

- Lee, Khattab, Finn et al. "Meta-Harness: End-to-End Optimization of Model Harnesses." arXiv:2603.28052.
- code-yeongyu. "oh-my-openagent." github.com/code-yeongyu/oh-my-openagent.
- Yeachan-Heo. "oh-my-codex." github.com/Yeachan-Heo/oh-my-codex.
