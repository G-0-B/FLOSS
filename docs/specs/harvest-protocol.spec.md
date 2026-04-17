# HARVEST Protocol Specification

**Version:** 0.1.0
**Status:** Specified
**Truth Status:** Specified
**Date:** 2026-03-21
**Related:** ADR-5 (Cognitive Virology Pattern), ADR-3 (Metaprompt Kernelization)

---

## Purpose

HARVEST (Holistic Aggregation and Recursive Verification of Emergent System Trajectories) formalizes the existing practice of periodic cross-session consolidation into a repeatable, observable protocol. It is the minimal viable self-observation loop for FLOSSI0ULLK — Iteration 0 of "the system observing itself."

## The Loop

```text
OBSERVE -> EVALUATE -> PROPOSE -> VALIDATE -> COMMIT
  ^                                             |
  +---------------------------------------------+
```

### Stage 1: OBSERVE

Collect recent state changes across all active substrates.

**Inputs:**

- Git log since last HARVEST (commits, PRs, branch activity)
- AI conversation exports since last HARVEST (all active systems)
- ADR modifications
- Open issues / blockers

**Output:** A dated observation snapshot (structured markdown).

### Stage 2: EVALUATE

Compare observations against the kernel (Master Metaprompt v1.3.1).

**Evaluation criteria:**

- Do recent changes align with the 4 invariants? (Prerogative, Provenance, Contribution, Knowledge)
- Have any Aspirational claims been promoted without evidence?
- Are there contradictions between substrates? (version drift, competing designs)
- Has any wheel-reinvention crept back in? (per ADR-5's Defend stage)

**Output:** Evaluation report with findings classified as:

- `ALIGNED` — consistent with kernel
- `DRIFTED` — inconsistent, needs correction
- `EVOLVED` — genuinely new insight that may warrant kernel update
- `CONFLICT` — contradictions requiring resolution

### Stage 3: PROPOSE

Generate proposed actions for each non-ALIGNED finding.

**Action types:**

- `FIX` — correct drift back to kernel alignment
- `ADR` — new architectural decision needed
- `ARCHIVE` — superseded content needs archival
- `KERNEL_UPDATE` — kernel itself may need revision (High friction tier)

### Stage 4: VALIDATE

Apply the Claim Truth Model to each proposal.

- Is the proposal supported by evidence from at least 2 substrates?
- Does it pass the Red Team lens? (What could go wrong?)
- Does it maintain carrier equivalence? (structure of code = structure of agent)
- For KERNEL_UPDATE proposals: require explicit cross-AI consensus (minimum 3 systems)

### Stage 5: COMMIT

Execute validated proposals.

- Create commits / PRs for code changes
- Update ADR index for new decisions
- Archive superseded documents
- Update this HARVEST log with cycle metadata

## Cadence

**Target:** One HARVEST cycle per week, or after any major cross-system synthesis session.

**Minimum viable cycle:** OBSERVE + EVALUATE only (read-only, no changes). This is valid when time is limited — observation without action still produces value.

## Metrics

Track per cycle:

- `observations_count` — number of state changes observed
- `drift_count` — findings classified as DRIFTED
- `evolution_count` — findings classified as EVOLVED
- `conflict_count` — findings classified as CONFLICT
- `proposals_generated` — action items proposed
- `proposals_validated` — action items that passed validation
- `proposals_executed` — action items committed
- `cycle_duration_minutes` — wall clock time for full cycle
- `adr_absorption_rate` — for each ADR, count of cross-system references since last cycle

## HARVEST Log

Each completed cycle appends a dated entry to `docs/governance/HARVEST_LOG.md`:

```markdown
## HARVEST 2026-03-21

- **Observed:** 12 commits, 3 AI sessions, 1 PR
- **Findings:** 2 ALIGNED, 1 DRIFTED (version ref), 1 EVOLVED (cognitive virology pattern)
- **Actions:** ADR-5 created, 6 files renamed, budget.rs compile error fixed
- **Duration:** ~45 min
- **Next:** Validate OpenClaw as orchestration layer for automated HARVEST
```

## Future: Automated HARVEST

When OpenClaw is validated as suitable:

1. OBSERVE stage can be automated (git log parsing, file change detection)
2. EVALUATE stage can be semi-automated (kernel diff checking)
3. PROPOSE/VALIDATE/COMMIT remain human-in-the-loop until trust is established

This progression from manual to semi-automated to automated is the concrete path toward the self-observation capability described in ADR-5, without requiring any undefined "self-derivative" computation.

## Non-Goals

- This is NOT a self-modifying system. It is a self-observing system with human-gated modification.
- This does NOT implement the MetacircularEvolution trait. That remains Aspirational.
- This does NOT require OpenClaw, any AI orchestration layer, or any new infrastructure. It can be run entirely as a manual process with markdown files.
