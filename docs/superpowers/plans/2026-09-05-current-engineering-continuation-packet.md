# FLOSSI0ULLK Current Engineering Continuation Packet
## Evidence-driven implementation alignment — 2026-09-05
## Packet version: v1.1

**Status:** Specified — execution-control / context-continuation packet (v1.1 amendments applied)
**Purpose:** Restore current engineering intent, reconcile the active implementation plans, select the highest-information next work, and prevent stale plans from silently becoming current architecture.
**Intended location:** `FLOSS/docs/superpowers/plans/2026-09-05-current-engineering-continuation-packet.md` or the current canonical resumption-plan surface if one already exists.
**Important:** Before creating a new document, apply the repository's doc-budget rule. If an existing canonical resumption/control document serves this role, update that document instead.

---

# 0. Operating decision

## Decision

**+1 ADOPT** this packet as the current task-selection and implementation workflow.

**0 HOLD** the attached implementation plans as evidence, contracts, and task-specific detail.

**-1 REJECT** treating their unchecked tasks as one chronological queue to execute blindly.

The older plans remain valuable, but they were created under different repo states and different uncertainties. Their branch anchors, dirty-file observations, PR states, hashes, blockers, and completion states must be reverified before execution.

The governing engineering objective is now:

> **Preserve maximal ambition in the direction of travel, but permit only the minimum architecture justified by current evidence. Choose each iteration to maximize consequential uncertainty reduction per unit of irreversible complexity.**

Supporting invariant:

> **Structure where correctness requires it. Neural flexibility where interpretation benefits from it. Preserve provenance across both.**

And the established trust-path rule remains:

> **Logic validates; neural assists.**

More operationally:

> **Neural systems may propose, retrieve, rank, interpret, synthesize, or recommend state changes. Deterministic policy decides whether authoritative state changes are accepted.**

---

# 1. Actual project intent

The immediate goal is not to maximize the number of subsystems, documents, protocols, agents, or abstractions.

The engineering goal is to progressively prove a substrate in which independently operating human and machine agents can:

1. retain local agency;
2. coordinate without silent interference;
3. exchange meaningful work across heterogeneous implementations;
4. preserve provenance through transformations;
5. distinguish evidence, interpretation, authority, and decision;
6. use probabilistic/neural capabilities without granting them implicit authority;
7. make consequential state transitions through explicit deterministic/governed boundaries;
8. inspect and replay why the system reached its current state;
9. evolve components without forcing universal internal implementation or ontology;
10. eventually support distributed human/AI/other-intelligence symbiosis without prematurely building the entire final architecture.

The current implementation program should therefore optimize for **credible proofs of these properties**, not architectural completeness.

---

# 2. Truth and maturity discipline

Do not conflate claim truth with implementation maturity.

Use the repository's truth labels:

- **Verified** — supported by traceable evidence.
- **Specified** — deliberately defined but not necessarily implemented or demonstrated.
- **Aspirational** — desired direction without sufficient implementation evidence.
- **Unverified** — insufficient evidence.

Separately reason about implementation maturity:

`Idea → Specified → Prototype → Tested → Operational → Canonical`

Example:

`Truth status: Verified`
`Implementation maturity: Specified`

is valid.

A plan saying that something was implemented, green, blocked, dirty, open, or closed on an earlier date does **not** establish the current state.

For this packet:

> **Plan evidence is historical evidence until reread against the current workspace.**

---

# 3. Source-plan reconciliation

## 3.1 Coordination Room — 2026-08-30

### Historical evidence

The plan's goal was a loopback MCP file-claim room preventing two agents from silently sharing a path, with an append-only event log.

Its architecture was explicitly:

- router, not controller;
- loopback only;
- file claims only;
- conflict represented structurally rather than inferred from chat;
- JSONL event log as durable mutation.

The plan states that the operator executed it inline on 2026-08-30.

### Current disposition

**+1 KEEP as established prior work, subject to current verification.**

Do not restart this plan from Task 1.

The newer Coordination v1 plan explicitly says to keep `packages/coordination_room/` unchanged and reports 17 tests green at its review point.

Treat the room as a prior implementation whose useful lessons are:

- path identity must be structural;
- coordination conflicts must not depend on natural-language interpretation;
- router ≠ controller;
- durable event history is useful;
- daemon dependence should not be required for fundamental coordination truth.

---

## 3.2 Coordination v1 — 2026-09-02

## Intent

Replace:

- manually maintained work-board status; and
- daemon-dependent claim truth

with:

- status derived from Git;
- atomic Git-REF claims;
- CAS-based exclusivity;
- separate fail-closed enforcement.

This is strongly aligned with the current engineering doctrine.

### Strong parts to preserve

**+1 KEEP**

- derive state instead of manually duplicating it;
- stdlib-only/offline probe path;
- `git update-ref` CAS for atomic exclusivity;
- one canonical path normalization mechanism;
- explicit claim identity;
- no raw identifier interpolation into refs;
- corruption fails closed;
- enforcement separate from provenance classification;
- whole semantic objects rather than ambiguous text conventions;
- workspace-level audit;
- worktree isolation;
- tests against races rather than assuming exclusivity;
- `--online` as explicit opt-in rather than hidden network dependency;
- reject signals Git cannot actually derive instead of manufacturing fake state;
- do not silently swallow module-load failures.

## Current blocker

The plan records that its governed `System + SpecChange` decision requires a valid provenance packet containing a real ADR-12 `consent_ref.decision_action_hash`.

At the plan's 2026-09-03 verification point, that anchor was unresolved.

Therefore:

> **Do not implement governed Coordination v1 changes by inventing an anchor, substituting a commit SHA/session ID, or weakening validation.**

## Resolve plan contradiction

One early global constraint mentions proceeding after approval **or a written operator waiver**.

Later Task 0 explicitly states:

> **No waiver path.**

The final handoff also states that operator LGTM or a waiver is insufficient while ADR-12's consent anchor is unresolved.

### Current rule

Use the stricter interpretation:

> **No waiver substitutes for the governed consent anchor unless the current canonical governance mechanism explicitly establishes a legitimate waiver path.**

Do not infer one from the earlier sentence.

---

## 3.3 Local A2A Harness Mesh — 2026-08-29

## Intent

Prove basic A2A interoperability without replacing the MCP/tool/context plane or turning A2A into a controller.

This separation remains sound:

- **MCP:** tools/context plane.
- **A2A:** discovery / peer task exchange.
- **Claim/Vote layer:** governance/coordination router.
- **A2A never bypasses governed validation.**

## Current disposition

**+1 KEEP the bounded experiment.**

But change its success criterion.

The original loopback Hello World proves protocol interoperability. That is useful but insufficient to justify architectural expansion.

The revised sequence is:

1. prove the local pair if it is not already proven;
2. prove the invariant that A2A does not become the MCP/tool bus;
3. prove one native Hermes peer if still relevant;
4. then **STOP** until there is a real peer-delegation use case.

Do not add:

- OCC wrappers;
- a2abridge;
- A2A voter semantics;
- A2A-to-consent mappings;
- extra discovery infrastructure

merely because interoperability works.

### Promotion criterion

Additional A2A architecture requires a concrete task where native peer delegation demonstrably improves something over the existing MCP/harness path.

---

## 3.4 PR #38 Contract / Shared-Skill Closure — 2026-07-29

This plan contains several highly reusable engineering contracts:

- failing regression before production modification;
- symbolic evaluation contract separated from runtime prompt formatting;
- validated evidence-DAG traversal belongs in provenance infrastructure;
- bounded/sanitized neural presentation belongs at the neural boundary;
- referenced non-packet contents are not silently imported;
- cycle and depth failures do not weaken validation;
- generated projections are derived from canonical bytes;
- exact review before remote mutation.

These patterns remain **+1 KEEP**.

However, the plan contains old frozen-base assumptions, exact hashes, PR-thread IDs, branch names, and remote-state expectations.

### Current disposition

Treat this as a **defect-contract reference**, not an executable script until current repo/PR state is reread.

Do not blindly recreate its historical frozen branch.

First determine:

- whether the four original defects remain;
- whether the canonical orientation skill is already promoted;
- whether its hash contract remains current;
- whether PR #38 still exists in the expected state;
- whether later work superseded any implementation detail.

If the defects remain, preserve their tests/invariants and repair them against current code.

If they are already closed:

**+1 VERIFY AND RETIRE.**

Do not reimplement solved work.

---

## 3.5 Phases 2/3/4 Resumption Packet — 2026-05-25

This packet is valuable historical context but should no longer act as a priority queue.

## Reclassification

### P2.4/P2.5 research distillations

**0 LATER**

Do them when they answer a live architectural question.

Do not produce research summaries merely because they remain unchecked.

### P3 zome README work

**0 LATER**

Documentation should follow verified current code.

Do not spend implementation cycles documenting stale zome surfaces before confirming they remain active.

### P4 autonomy / heartbeat resumption

**0 HOLD — hard preference**

Do not restart autonomous activity simply because the old packet says it is pending.

Resume only after:

- current runtime budget matches implementation;
- governance boundaries are functional;
- coordination truth is reliable enough;
- review backlog is under control;
- first ticks can be inspected without creating uncontrolled work.

### P5 root `git init`

**0 HOLD / REASSESS**

Do not perform this simply because an older plan proposed it.

The workspace topology, `.agent-surface`, nested repositories, worktrees, and Coordination v1 assumptions have evolved.

Require a current concrete problem that root Git solves before committing to this topology.

### `hc` CLI + Tryorama end-to-end follow-up

**+1 HIGH-VALUE CANDIDATE**

This old item is different from the documentation backlog because it can produce new empirical evidence.

The historical packet reports:

- active zomes built;
- consent-integrity native tests passed;
- vector tests passed;
- full Tryorama round-trip remained blocked on missing `hc`.

Current state must be reverified.

If still true, this is a high-information experiment because it advances the project from component-level tests toward actual Holochain end-to-end substrate evidence.

Do **not** claim that passing Tryorama automatically resolves the ADR-12 decision-action anchor.

Determine whether the consent-anchor problem actually requires a functioning source-chain execution path. If yes, connect these work items. If not, keep them separate.

---

# 4. Current central uncertainty

The most consequential current uncertainty appears to be the **governance authorization anchor**:

> **Can the system produce and consume a real ADR-12 `decision_action_hash` through its intended substrate, without placeholders or authority shortcuts?**

This is not the same problem as outsider-verifiable historical-integrity witnessing. Do not collapse them under the word **anchor**. See the next subsection.

Why the governance-authorization uncertainty matters:

- Coordination v1 is blocked on it.
- The governance/provenance architecture claims that consequential state changes require it.
- Solving around it would invalidate the architecture's own trust assumptions.
- If the intended consent mechanism cannot actually produce the required `decision_action_hash`, that is more important to discover than building additional coordination UI or documentation.

Therefore the first high-ROI investigation — after P0 security reverification — should reduce this uncertainty.

---

## Two non-collapsible anchor problems

### Governance authorization anchor

`ADR-12 consent decision → source-chain action → decision_action_hash`

Purpose:

**prove that a governed action received the required consent/authorization.**

### Historical-integrity witness

`provenance state → external commitment/witness`

Purpose:

**make deletion/truncation of historical provenance detectable outside the store being protected.**

These solve different problems.

A valid ADR-12 action hash does not prove provenance-history completeness.

An external provenance witness does not establish consent for a governed decision.

Never allow the word **anchor** to collapse them.

---

# 5. Current four-lane execution model

Do not let one blocked governed path freeze all independent empirical work.

Use four lanes. Lane S may interrupt the others when a currently live credential or destructive footgun is confirmed.

---

## Lane S — Security and irreversible-risk containment

**Priority: P0 REVERIFY IMMEDIATELY**

Historical evidence from the 2026-08-30 re-orientation identified three credential-exposure classes:

1. committed Supabase credential material, with a secondary reproduction into an inventory artifact;
2. an OpenWork-style bearer token in local configuration;
3. six provider credentials in Hermes planning artifacts.

These are historical findings, not assertions about current state.

### Outcome

Determine whether each exposure remains live and contain any that does.

### Invariants

1. Never reproduce secret values into reports, context packets, logs, generated inventories, prompts, or shared surfaces.
2. Rotation/revocation state must be verified by readback rather than assumed from an attempted mutation.
3. Committed-secret remediation distinguishes credential revocation from Git-history remediation; they are separate decisions.

### Procedure

- Verify whether each historical exposure still exists.
- If live, revoke/rotate through the appropriate operator-controlled mechanism.
- Decide separately whether committed history must be purged or exposure accepted after revocation.
- Perform a repository/workspace secret scan using an established tool before designing another scanner.
- Verify that generated inventory/materializer paths redact likely credentials.
- Record only redacted identifiers and status.

Security containment may interrupt other lanes when a currently live credential or destructive footgun is confirmed.

---

## Lane A — Governance / trust-path unblock

**Priority: NOW**

### Outcome

Establish whether a real ADR-12-compatible `decision_action_hash` (governance authorization anchor) can be produced under the current implementation.

### Invariants

1. No placeholder, commit hash, session ID, or chat approval substitutes for the required governance authorization anchor.
2. Provenance validation remains deterministic.
3. Neural consensus cannot manufacture authority missing from the deterministic trust path.

### Central uncertainty

Does a functioning source-chain path currently exist that can produce the required consent decision artifact (`decision_action_hash`)?

### First experiment

Inspect current code and tests for:

- `ConsentPayload`;
- `ConsentDecision`;
- decision recording externs;
- source-chain action creation;
- the consumer expecting `decision_action_hash`;
- any existing tests or fixtures producing a real action hash.

Determine the shortest executable path from:

`consent proposal → consent decision → committed source-chain action → action hash → provenance packet → governed submit_claim`

### Falsification condition

If the repository contains no executable route from consent decision to a real `decision_action_hash`, then the assumption that Coordination v1 can merely "obtain an anchor" is false.

In that case:

**do not continue Coordination v1.**

The next implementation item becomes:

> **Build the smallest real consent path that produces a governance authorization `decision_action_hash`.**

Not a workaround. Do not substitute an external historical-integrity witness for this path.

### Connection to Holochain end-to-end proof

If running that path requires the missing `hc`/Tryorama substrate:

move the Holochain #28 follow-up into this lane.

Otherwise treat Tryorama as a parallel substrate proof.

---

## Lane B — Independent interoperability experiment

**Priority: NOW if not already proven**

### Outcome

Demonstrate that two real peer processes can discover and exchange a task using A2A while the existing MCP/tool plane remains untouched.

### Invariants

1. A2A is not the controller.
2. A2A is not inserted into `.mcp.json` as an MCP server.
3. A peer task result is information/evidence, not authoritative system state.
4. Governed decisions continue through the existing trust path.

### Minimum proof

`peer A → agent-card discovery → peer B → task/message → result → peer A`

Then one Hermes-native peer if relevant.

### Stop condition

Once this works:

**STOP adding A2A infrastructure.**

The next A2A work waits for a concrete real task.

### Falsification condition

If native A2A adds no useful capability compared with current harness/MCP interaction for an actual peer task, do not generalize it further.

---

## Lane C — Existing contract closure / cleanup

**Priority: PARALLEL / CHEAP REVERIFICATION**

Lane C does not block Lane A, Lane B, or Lane S unless reverification reveals a shared dependency or active hazard.

Use PR #38 and similar older plans as regression-contract inventories.

For each old task:

`current failure? → yes: repair`
`already solved? → verify + retire`
`superseded? → archive`
`cannot establish? → Unverified`

Do not rebuild old branch history to satisfy an old plan.

---

# 6. Coordination v1 after governance unlock

Only enter this sequence after:

1. the current governance requirement is established;
2. the required decision is legitimately approved;
3. the dirty/shared-file pre-task state is reconciled;
4. the implementation base is reverified.

Then preserve the broad sequence:

## M1 — Derived coordination status

Build the read-only derived view first.

Why:

- highest reach;
- no daemon needed for truth;
- eliminates stale manually maintained status;
- increases observability before adding enforcement.

Success means current worktree/branch/claim conditions are derived from authoritative sources rather than duplicated text.

Do not add fake signals the underlying substrate cannot derive.

---

## M2 — Git-REF atomic claims

Implement the minimal CAS primitive.

Critical invariants:

- canonical normalized ID;
- safe injective ref encoding;
- `git check-ref-format` authoritative;
- exclusive create against ZERO;
- refresh by same holder through CAS;
- no stealing before expiry policy;
- malformed claim data fails closed;
- distinct actor vs holder;
- every forced mutation audited;
- missing agent identity fails closed.

### Central experiment

Two independent contenders attempt the same claim using the same expected old state.

Exactly one must win.

This is more important than feature breadth.

---

## M3 — Enforcement

Only after M2 is empirically credible.

Enforcement must:

- consume the same canonicalization logic;
- remain separate from `is_substantive`;
- fail closed on claim subsystem errors;
- produce explicit machine-readable denial;
- avoid weakening provenance semantics.

---

## M4 — Optional online projection / manual-board retirement

Only after the derived offline core is working.

Network access remains explicit.

Retire manual status only where authoritative derived status actually covers it.

Do not delete manual information merely because the new system resembles it.

---

# 7. North-star vertical walking skeleton

This is an **integration milestone**, not the next coding task.

The smallest meaningful cross-system proof should eventually demonstrate:

1. two independently running agent surfaces;
2. unique session identity;
3. observable shared workspace/repository state;
4. atomic claim of one real path or work unit;
5. competing claim deterministically rejected;
6. one peer delegates a bounded task to another;
7. peer result returns as evidence, not authority;
8. evidence receives provenance;
9. bounded structured evidence reaches the reasoning/consensus layer;
10. neural systems may assess/propose;
11. deterministic policy validates acceptance;
12. a governed consent action is committed through the intended substrate;
13. the resulting decision/action identifier is retained;
14. another observer can reconstruct the important sequence from derived state + provenance/audit artifacts.

Conceptually:

```text
Agent A
  │
  ├─ observe derived state
  │
  ├─ CAS claim work/path ────────────────┐
  │                                      │
Agent B                                  │
  ├─ competing claim → deterministic deny
  │
  └─ optional A2A peer task
            │
            ▼
       result/evidence
            │
            ▼
      provenance packet
            │
            ▼
   deterministic validation
            │
            ▼
    neural assessment/vote
            │
            ▼
    governed decision gate
            │
            ▼
 Holochain/source-chain action
            │
            ▼
       action hash
            │
            ▼
 replayable status/provenance
```

Do not attempt to implement this entire diagram in one branch.

Each iteration should attack one uncertainty required for this proof.

---

# 8. Mandatory per-iteration workflow

Every implementation slice starts with this template.

## 8.0 Pre-Action Gate

Before consequential mutations, proportionately evaluate:

1. **Intent** — what outcome was requested? Is the input an instruction or a report that something already occurred?
2. **State** — what cheap observation could show that the action is already complete, unnecessary, stale, or aimed at the wrong target?
3. **Necessity** — does this action actually advance the outcome?
4. **Consequences** — what scarce resources, external effects, irreversible changes, or failure modes are involved?
5. **Decision** — proceed, challenge the premise, select a safer action, or stop.
6. **Readback** — verify the result.

Rules:

> Authorization is not evidence of necessity.

> An interrupted mutation has unknown outcome until read back.

> Never blindly retry a consequential mutation.

This is a reasoning obligation, not a requirement to emit a six-item checklist before ordinary actions.

---

## 8.1 Observable outcome

What capability will exist after this slice that does not exist now?

One sentence.

---

## 8.2 Invariants

Maximum three.

If more than three are needed, shrink the slice.

---

## 8.3 Central uncertainty

What consequential thing do we currently not know?

---

## 8.4 Falsification condition

What result would cause us to reject or materially revise the approach?

Write this **before implementation**.

---

## 8.5 Five-way review lens

Before introducing representations or identities, inspect:

- **Content** — what information exists?
- **Occurrence** — what specific event/version/instance produced it?
- **Semantics** — what does it mean or relate to?
- **Authority** — who/what is allowed to assert/change it?
- **Provenance** — where did it come from and how was it transformed?

This is a review lens.

Do **not** automatically turn these five distinctions into five tables, classes, protocols, IDs, or repository-wide canonical rules.

Promote a distinction into implementation only if collapsing it causes a demonstrated problem.

---

## 8.6 Now / Later / Never

Every proposed abstraction must have an evidential sponsor.

Valid sponsors:

1. invariant enforcement;
2. observed failure;
3. measurement;
4. interoperability;
5. security/governance requirement.

No sponsor → do not implement.

---

## 8.7 Trust allocation

Explicitly write:

**Deterministic authority:**
What code/rule decides system acceptance?

**Neural/probabilistic assistance:**
What may models suggest, interpret, rank, retrieve, or synthesize?

Never leave this implicit at a consequential boundary.

---

## 8.8 Narrow typed boundary

Document:

`input → parse → validate → typed representation → bounded transformation → serialization → consumer`

Do not permit a validated structured object to quietly become ambiguous delimiter text at a downstream neural boundary.

---

## 8.9 Walking skeleton

Build the narrowest end-to-end path that attacks the central uncertainty.

Prefer a slightly larger experiment that answers the real question over a tiny demo that proves nothing consequential.

---

## 8.10 Adversarial cases

Test the boundary, not merely business examples.

Common representation cases:

- quotes;
- delimiters;
- fake metadata;
- newline/tab/control whitespace;
- Unicode;
- duplicate IDs;
- malformed fields;
- stale state;
- oversized values;
- conflicting provenance;
- reorderings;
- corruption;
- concurrent writers.

---

## 8.11 Degradation

If bounded information must be omitted:

> **Drop whole semantic units and declare the omission.**

Do not character-truncate structures into ambiguous partial representations.

---

## 8.12 Baseline

Name the simpler alternative.

Examples:

- manual status table;
- ordinary Git branch inspection;
- existing MCP invocation;
- direct function call;
- vector retrieval + metadata;
- single-agent execution.

New architecture should earn its complexity against something.

---

## 8.13 Measurements

Choose only measurements that could affect a decision.

Examples:

- conflict detection correctness;
- race winner count;
- false accept / false deny;
- provenance retained;
- cross-peer success;
- human intervention;
- context size;
- latency;
- failure recovery;
- implementation complexity.

---

## 8.14 Adoption gate

Finish every slice with:

### `+1 ADOPT`
Evidence supports keeping it.

### `0 HOLD`
Potentially useful, evidence insufficient.

### `-1 REMOVE`
Complexity does not justify itself.

Deletion and retirement are valid successful outcomes.

---

## 8.15 Update operational memory

Record only useful forward state:

- open questions;
- open intentions;
- open hypotheses;
- blockers;
- next experiment.

Do not convert every iteration into another narrative document.

---

## 8.16 Workflow retrospective

`KEEP` — what generated information?
`KILL` — what generated work but no decision?
`COMPRESS` — what can become an invariant/test/helper?
`AUTOMATE` — what repeated mechanical work should become code?

---

## 8.17 Evidence rules

### Validate, do not coerce

Do not transform an untrusted value into the expected type and then call the transformation validation.

Validate original type and shape before parsing/coercion.

### Positive evidence, not absence of bad markers

A gate claiming evidence exists must require a substantive positive witness.

`not obviously bad` does not imply `verified`.

### One authority or an executable equivalence contract

When schema, specification, runtime constants, registries, and validators describe the same vocabulary:

- derive them from one authority where practical; or
- maintain an executable test asserting their general equivalence.

Tests should assert the general property, not merely enumerate the last fields that happened to break.

---

## 8.18 Multi-model review policy

> **Model multiplicity is evidence diversity, not authority multiplication.**

Do not claim model/provider-family count establishes statistical independence.

For consequential review:

1. preserve every raw reviewer artifact;
2. normalize findings into a **union with reviewer attribution**;
3. preserve minority and conflicting findings explicitly;
4. distinguish non-answer/truncation from a vote;
5. inspect raw responses whenever aggregate agreement appears suspiciously high;
6. run at least one less-structured reviewer/control when rigid schemas could suppress unexpected finding classes;
7. allow prose synthesis only as a convenience layer over the attributed finding set, never as its replacement.

Neural consensus remains advisory evidence unless deterministic governance explicitly grants a decision mechanism authority.

---

## 8.19 Post-fix adjacency check

The project has repeatedly produced fixes that create neighboring defects.

After every trust-path or validation fix:

1. rerun the focused regression;
2. rerun the relevant package/contract green set;
3. inspect adjacent uses of the same pattern;
4. ask whether the fix addressed the general property or only the reported instance;
5. run an adversarial review against the changed boundary.

A successful regression test is evidence that one failure was closed, not proof that the class was eliminated.

---


# 9. Immediate execution sequence

A local implementation agent receiving this packet should proceed in this order.

## Step 0 — Reality gate

Do not edit production code yet.

Read the minimum current surfaces:

- `CONTEXT_L0.md`;
- `CONTEXT_L1.md`;
- current working todo/control surface;
- ADR-12;
- current consent-zome code;
- current provenance/gateway contracts;
- current git branch/status/worktrees;
- current coordination implementation;
- current PR #38 state if relevant.

Then classify every candidate as:

`IMPLEMENTED | PENDING | BLOCKED | SUPERSEDED | UNKNOWN`

Do not infer completion from plan checkboxes.

The Reality Gate must explicitly establish:

- Are ADR-18, ADR-19, and ADR-20 present on current canonical `main`, only on another branch, or superseded?
- What is the current PR41/PR43/reconciliation topology?
- Are the historical credential exposures still live?
- Is the `_AUDIT_SINK` audit-path finding still reproducible?
- Is the daemon-stop `$PID` failure still present?
- Is the hook/materializer split-brain still present?
- Does the relevant Tryorama integration test currently execute and pass?
- Does the ADR-12 path currently create a real decision action hash?
- What provenance external-witness mechanism, if any, currently exists?

Every answer must be:

`VERIFIED CURRENT | HISTORICAL ONLY | SUPERSEDED | UNKNOWN`

### Output

A concise current-state delta.

Prefer terminal/session output or the existing operational state surface over creating another document.

---

## Step 1 — Resolve the governance uncertainty

Trace the complete required path for `decision_action_hash`.

Do not start by modifying Coordination v1.

Answer:

> **What exact currently executable operation creates the action whose hash the governance gate expects?**

If one exists:

run the smallest test that proves it.

If it does not:

define the missing minimal vertical slice.

---

## Step 2 — Determine whether Holochain #28 is on the critical path

Reverify:

- active Holochain versions;
- zome build state;
- availability of `hc`;
- Tryorama state.

If the missing CLI/runtime prevents the consent anchor experiment:

**+1 execute the minimum Holochain end-to-end setup now.**

If it is unrelated:

run it only if it remains a high-information substrate proof relative to other work.

---

## Step 3 — Run independent work while governed work is blocked

If A2A is still unproven:

run the local pair + invariant test.

If already proven:

verify it and stop.

If Hermes interoperability remains useful:

prove one native peer.

Do not expand the A2A architecture without a real use case.

---

## Step 4 — Reassess PR #38 defects

Check current code and remote state.

For each original defect:

`still reproduced?`

- **yes** → execute red/green repair;
- **no** → collect proof and retire;
- **superseded** → explicitly record supersession;
- **unclear** → mark Unverified.

Do not mechanically replay the July frozen-base process.

---

## Step 5 — Enter Coordination v1 only after legitimate unblock

Once governance and dirty-worktree conditions genuinely permit it:

1. derived offline status;
2. divergence quality only where useful;
3. atomic Git-REF claims;
4. race tests;
5. fail-closed enforcement;
6. explicit online projection;
7. retire only duplicated manual status actually replaced.

---

## Step 6 — Autonomy remains gated

Do **not** restart the heartbeat merely because other work is complete.

Require a new decision based on:

- coordination reliability;
- governance reliability;
- runtime budget;
- queue size;
- observability;
- first-three-tick inspection strategy.

---

# 10. Current Now / Later / Never map

## NOW

- current workspace/repo reality check, including the Step-0 open questions;
- P0 security reverification of historical credential-exposure classes (Lane S);
- ADR-12 governance-authorization `decision_action_hash` executable-path investigation;
- Holochain end-to-end proof if it lies on that path or remains the strongest substrate uncertainty;
- verify A2A local pair if not already proven;
- cheap parallel contract/PR reverification, including PR #38 defects;
- preserve existing coordination-room tests;
- reconcile dirty/shared files before editing them.

## LATER

- additional A2A adapters;
- elaborate peer directories;
- expanded semantic/cognitive memory machinery;
- research distillations without a live decision question;
- zome README sweep not required by current implementation;
- broad manual-board retirement;
- autonomous heartbeat;
- operation-indexed retrieval contracts unless repeated retrieval leakage justifies them;
- stronger defeat propagation unless actual epistemic conflicts require it.

## NEVER / NOT JUSTIFIED NOW

- A2A as master orchestrator;
- A2A replacing MCP;
- neural model output directly establishing authoritative truth;
- placeholders masquerading as consent anchors;
- widening provenance classification merely to enforce claims;
- fake coordination signals that Git cannot derive;
- arbitrary character truncation of structured semantic input;
- silent failure at trust-critical boundaries;
- hand-editing generated canonical projections;
- implementing abstractions merely because prior plans mention them;
- treating historical plan state as current repo truth.

---

# 11. Commitment budget

Treat durable architectural commitment as a finite resource. Local complexity still costs cognition, tests, and debugging, but the gate is **commitment**, not LOC.

For every implementation slice record the delta:

| Long-lived commitment | Added? |
|---|---|
| authoritative vocabulary | |
| durable state/store | |
| schema/protocol | |
| network service | |
| dependency/runtime | |
| background process | |
| canonical document/surface | |
| irreversible migration | |

For each `yes`, provide:

- evidential sponsor;
- why the existing mechanism is insufficient;
- rollback/removal path;
- acceptance experiment.

The objective is not minimum LOC.

It is minimum **durable architectural commitment** necessary to resolve the current uncertainty.

Prefer reversible decisions while confidence is low.

Examples:

- adapters over rewrites;
- explicit interfaces over deep coupling;
- feature flags over irreversible activation;
- ordinary inspectable data over opaque stores;
- local experiments over global protocol adoption;
- migration-capable schemas over premature universal canonicalization.

> **Irreversibility should increase with evidence.**

---

# 12. Canonical architectural boundaries to preserve

Unless new evidence overturns them:

### Coordination is not command.

Routers coordinate. They do not silently acquire executive authority.

### A2A is not MCP.

Peer discovery/task delegation and tool/context access remain distinct concerns.

### Provenance is not authority.

A perfectly authenticated statement can still be false.

### Authority is not truth.

Permission to assert does not prove an assertion.

### Similarity is not identity.

Neural similarity must not establish canonical identity or silently transfer authority.

### Serialization is not semantic validation.

JSON framing removes some syntactic ambiguity but does not make arbitrary neural input safe.

### Signatures are not prompt-injection defenses.

Cryptographic validity and neural-consumption safety are different layers.

### Memory is not canon.

Recall/federation surfaces may assist retrieval without becoming authoritative project state.

### Specification is not implementation.

A designed component must not be described as operational without repo/runtime evidence.

### Historical plans are not current state.

Plans preserve intent and evidence; the workspace establishes current truth.

### Governance authorization is not historical-integrity witnessing.

An ADR-12 `decision_action_hash` does not prove provenance-history completeness. An external witness does not establish consent.

### Prefer interoperable witnesses over project-specific formats.

When a system needs an outsider-verifiable witness:

> **Prefer adoption of a recognizable interoperable witness/attestation standard over inventing a project-specific witness format.**

The project may need bespoke commitments because its data is bespoke.

The witness exists precisely to be understood by entities that do not already trust the project.

Do not automatically implement any specific supply-chain framework from historical research; apply the reuse/probe gate against current versions and current requirements first.

---

# 13. Current integration milestone acceptance criteria

Do not call the coordination/governance substrate meaningfully integrated until a test can demonstrate most of the following without hidden manual substitution:

- [ ] two independent agent processes/surfaces;
- [ ] unique agent/session identities;
- [ ] derived current coordination status;
- [ ] atomic exclusive claim under contention;
- [ ] deterministic loser denial;
- [ ] safe expiry/recovery behavior;
- [ ] bounded peer task exchange;
- [ ] result treated as evidence rather than authority;
- [ ] provenance survives the task boundary;
- [ ] evidence presented to neural voters as bounded typed structure;
- [ ] deterministic provenance/governance validation remains authoritative;
- [ ] consent decision creates a real substrate action;
- [ ] action hash enters the governed provenance path;
- [ ] no placeholder authority;
- [ ] an independent observer can reconstruct the important sequence.

This is the long-lived proof target.

Individual tasks should implement only the smallest slice necessary to move one unchecked item toward credible evidence.

### Lane ownership of the integration milestone

This table describes dependency ownership, not implementation order.

| Integration proof | Owning lane |
|---|---|
| independent surfaces / session identity | Coordination / Lane A after governance unblock |
| derived workspace state | Coordination |
| atomic claim + deterministic contention denial | Coordination |
| peer task delegation | Lane B |
| result as non-authoritative evidence | Lane B + trust boundary |
| provenance creation/validation | Lane A |
| bounded neural review | Lane A |
| governed consent decision | Lane A |
| real consent action hash | Lane A |
| external historical-integrity witness | Provenance subtrack of Lane A, distinct from ADR-12 |
| replay / reconstruction | integration acceptance across lanes |
| credential containment | Lane S prerequisite where affected |

---

# 14. Context-continuation protocol

A new agent/session receiving this packet should not begin by proposing architecture.

It should:

1. load minimal context;
2. inspect current executable/repository state;
3. compare state against this packet;
4. identify the highest-consequence unresolved uncertainty;
5. select one bounded experiment;
6. state outcome/invariants/falsification criterion;
7. run red/green or equivalent empirical test;
8. measure against the simpler baseline;
9. decide `+1 / 0 / -1`;
10. update only the necessary canonical/operational surfaces;
11. leave explicit open questions and next experiment.

If current evidence contradicts this packet:

> **evidence wins.**

Update or supersede the packet instead of bending implementation to preserve it.

---

# 15. First prompt for the local implementation agent

Use the following intent when resuming:

> Reload the current FLOSSI0ULLK workspace with this continuation packet as the task-selection policy, but treat all dated state in it and its source plans as historical until verified. Do not begin production edits. First run the Reality Gate, including P0 security reverification of historical credential-exposure classes. Establish current branch/worktree/dirty state, current Coordination Room/Coordination v1 status, current ADR-12 governance-authorization path (`decision_action_hash`), whether any provenance external-witness mechanism exists as a *separate* problem, Holochain end-to-end test status, A2A proof status, and whether the PR #38 contract defects remain. Classify candidate work as IMPLEMENTED, PENDING, BLOCKED, SUPERSEDED, or UNKNOWN with traceable evidence. Answer every Step-0 open question as `VERIFIED CURRENT | HISTORICAL ONLY | SUPERSEDED | UNKNOWN`.
>
> Then choose the single next implementation slice that removes the most consequential uncertainty while introducing the least unjustified durable commitment and irreversible risk. State its observable outcome, maximum three invariants, central uncertainty, falsification condition, deterministic-vs-neural authority boundary, simpler baseline, commitment-budget delta, and acceptance test before editing code.
>
> Preserve these constraints: logic validates; neural assists; provenance is distinct from authority and truth; the governance authorization anchor is distinct from any historical-integrity witness; A2A does not replace MCP or become a controller; governed decisions may not use placeholder consent hashes; structured validated data must not become syntactically ambiguous at neural boundaries; omission/truncation operates on whole semantic units; trust-critical failure is explicit and normally fail-closed; historical plans do not override current repo evidence; never reproduce secret values into reports or shared surfaces.
>
> Prefer a real vertical proof over additional architectural documentation. Do not introduce a new abstraction without an evidential sponsor. After the slice, return `+1 ADOPT`, `0 HOLD`, or `-1 REMOVE`, followed by KEEP / KILL / COMPRESS / AUTOMATE and the next unresolved experiment.

---

# 16. Current default recommendation

Absent contradictory current evidence:

1. **Run the Reality Gate, including P0 security reverification.**
2. **Contain any currently live security exposure or destructive operational footgun.**
3. **Resolve the ADR-12 executable consent-action path uncertainty.**
4. **Determine whether Holochain/Tryorama is on that critical path.**
5. **Run bounded A2A proof only if still empirically unresolved.**
6. **Perform cheap parallel contract/PR reverification.**
7. **Enter Coordination v1 only after legitimate governance unblock.**
8. **Keep external provenance witnessing distinct from the consent-authorization work.**
9. **Reissue task ordering whenever an invalidation trigger fires.**

The selection criterion is not age of backlog.

It is:

> **Choose the experiment that removes the most consequential uncertainty while introducing the least unjustified durable commitment and irreversible risk.**

---

# 17. Self-staleness / invalidation triggers

This continuation packet becomes **STALE FOR TASK SELECTION** when any of these occur:

1. the ADR-12 consent-authorization uncertainty resolves in either direction;
2. current canonical branch/PR topology materially changes;
3. ADR-18/19/20 governance status or location changes;
4. Coordination v1 M1/M2/M3 lands or is rejected;
5. the security lane discovers or closes a P0 exposure;
6. A2A crosses its stated stop condition into a real production use case;
7. a governing ADR supersedes one of this packet's invariants;
8. a reality-gate observation materially contradicts its lane ordering.

On trigger:

> **re-run the Reality Gate and update this packet in place.**

Do not continue executing the old lane order by inertia.

A timestamp alone does not establish freshness; freshness is tied to changes in the facts the packet depends upon.
