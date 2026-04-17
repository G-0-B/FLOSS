# Forward Momentum Plan: Radicle, Multi-Harnesses, and Cheap-Loop Utilization

```yaml
id: "plan-forward-momentum-radicle-meta-harnesses"
version: "0.1.0"
kind: "plan"
status: "Active"
updated: "2026-04-17"
truth_status: "Specified"
evidence_sources:
  - "docs/adr/ADR-8-radicle-dev-substrate.md"
  - "docs/architecture/AGENTIC_OPERATING_MODEL.md"
  - "deep-flossi0ullkreport.md"
  - "oh-my-meta.md"
  - "docs/research/Automated-Agent-Orchestration-Report_v1.0.0.md"
```

## Goal
Maximize forward momentum with the least energy cost by:

- canonicalizing the right substrates
- pushing repetitive work onto cheap/free inference
- keeping high-value judgment with Claude Code and Gemini
- building multiple small harnesses instead of one giant token burner

## Working Thesis
The cheapest path forward is not new model training, framework migration, or a Holochain rewrite. The cheapest path forward is harness improvement:

1. make the dev-plane substrate explicit
2. preserve full traces on disk
3. route work to the cheapest adequate model
4. keep governance and provenance in the loop

## Priority Order

### Phase 0: Canonicalize the Stack
**Why first:** if the active docs forget the real stack, every future session re-argues fundamentals.

Deliverables:
- ADR for `Radicle` as canonical dev-plane code substrate
- operating model doc for harnesses and model allocation
- architecture/index/orientation updates

Effort: low  
Payoff: immediate reduction in architectural drift

### Phase 1: Exploit the Free Inference Stack Hard
**Why second:** the throughput already exists; not using it is wasted leverage.

Required actions:
- keep `Groq` and `Cerebras` as default reviewers/voters/trace triagers
- reserve `Claude Code` for proposer/integrator/high-risk edits
- reserve `Gemini` for multimodal, design, research digestion, and dissent
- formalize that allocation in docs and future harness config

Success criteria:
- background review loops do not require premium models
- premium models are only used when a task has real blast radius or synthesis value

Effort: low  
Payoff: immediate drop in token burn and context fatigue

### Phase 2: Build the Radicle Bridge Spike
**Why third:** the orchestration report identified this as the hard gate before deeper autonomy.

Minimal test:
1. create/update an ADR or equivalent change as a Radicle artifact
2. emit a provenance record linking that artifact into the local source chain
3. verify from another peer that the artifact and linkage are fetchable and valid

Success criteria:
- bridge is independently verifiable
- fork visibility is explicit
- failure semantics are legible

Effort: medium  
Payoff: converts Radicle from architecture policy into working substrate

### Phase 3: Upgrade the Memory Harness
**Why fourth:** work stoppage is currently more likely to come from context collapse than from missing raw compute.

Required structure:
- lightweight index
- topic files
- raw traces
- Boulder-style task notepads
- nightly or periodic consolidation pass

Concrete outputs:
- task-local `learnings`, `decisions`, `issues`, `verification`, `problems`
- truth labels on learnings
- a deterministic place for interrupted work to resume from

Effort: medium  
Payoff: less restart cost, less token waste, more continuity

### Phase 4: Upgrade the Execution Harness
**Why fifth:** once memory and substrate are stable, execution can become more autonomous safely.

Required features:
- consensus hook for structural changes
- Hashline-style edit verification with pre-write checkpoints
  Current state: post-write verification spike is landed; next step is widening it into stronger structural policy gates.
- explicit blast-radius handling
- policy gates before higher-risk merges or patch publication

Effort: medium  
Payoff: better reliability and lower corruption risk

### Phase 5: Upgrade the Retrieval Harness
**Why sixth:** retrieval needs corpus routing, not just bigger indexes.

Required features:
- route across active specs, ADRs, code, source-chain entries, research, `_reference/`
- only then run vector or semantic retrieval inside the chosen corpus
- later ingest Radicle COBs and patches as first-class retrievable artifacts

Effort: medium  
Payoff: lower context waste, better evidence quality

### Phase 6: Start the Optimization Harness
**Why last:** MetaHarness-style optimization only pays off once traces, routing, and memory are real.

Optimize:
- routing tables
- prompt variants
- hook settings
- retrieval policies
- continuation rules

Rule:
- archive every optimization cycle as a candidate
- never discard the full traces

Effort: high  
Payoff: compounding improvement once the rest of the stack is stable

## Immediate Work Queue

### Cheapest high-gain tasks
1. Finish canonical docs updates.
2. Add a provider-role matrix to active architecture/orientation docs.
3. Define the Radicle bridge spike as the next hard-gate engineering task.
4. Define the memory harness filesystem layout before coding it.
5. Define consensus-hook inputs/outputs before touching hook code.

### First engineering tasks after docs
1. Radicle bridge proof-of-concept.
2. Boulder/KAIROS memory directory and index design.
3. Consensus hook prototype for structural package edits.
4. Widen checkpointed Hashline verification into structural policy gates.

## Model Budget Policy
- `Groq/Cerebras` first for repetitive or parallelizable work.
- `Claude Code` when code changes must actually land.
- `Gemini` for multimodal interpretation, independent dissent, and document/design synthesis.
- No new premium review loop is allowed unless the cheap-loop failure mode is documented.

## Kill Criteria
Stop or delay a phase if:
- it increases centralization instead of reducing it
- it requires premium-model dependence for routine loops
- it adds orchestration complexity without improving traceability
- it cannot be explained in one paragraph to a future collaborator

## Definition of Momentum
Momentum means:
- fewer architectural arguments repeated across sessions
- more work recoverable after interruption
- more background review done on free inference
- more durable provenance per unit of effort
- less reliance on one model, one context window, or one central platform
