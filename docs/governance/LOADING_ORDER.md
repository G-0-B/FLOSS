# FLOSSIOULLK Governance Document Loading Order

When onboarding a new agent (human or AI) to the FLOSSIOULLK project, load documents in this order:

## 1. Kernel v1.3.1 (Mandatory Rules)

**File:** `FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md` (root level)
**Purpose:** Always-on coordination rules. Non-negotiable constraints.
**Key content:** Identity, prime directive, response modes, evidence gate (Now/Later/Never), symbolic-first validation, provenance packet schema.

## 2. Context Compression Packet v1.1 (Rationale)

**File:** `context-compression-v1.1.md`
**Purpose:** Explains *why* the project is built this way. Design rationale.
**Key content:** Isomorphism map, transmutation dictionary (Love=Interoperability, Light=Observability, Knowledge=Verifiable State), immediate vector (blocking items), compliance guardrails.

## 3. Project Spine v0.5 (Governance + Enforcement)

**File:** `spine-v0.5.md`
**Purpose:** Invariants, truth labels, upgrade mechanics, enforcement expectations.
**Key content:** Canonical source precedence, prime directive, upgrade-everything policy, claim truth model (labels), two-plane architecture, voluntary convergence, provenance packets, substrate-first gating, agent orchestration.

## 4. Canonical Build Spine v0.2 (Current Execution Synthesis)

**File:** `FLOSSI0ULLK_CANONICAL_BUILD_SPINE_v0.2.md`
**Purpose:** Current build order and contradiction-resolving execution spine. This document does not override the Kernel, Spine, or SDD spec; it translates them into the present repo state.
**Key content:** Source register, evidence classes, current reality check, contradiction log, phase gates, NOW/LATER/NEVER backlog, issue backlog draft.

## 5. Relevant ADRs (Decisions)

**Directory:** `../adr/`
**Index:** `../adr/INDEX.md`
**Purpose:** Specific architectural decisions with rationale and supersession chains.
**Load order within ADRs:** Start with ADR-0 (Recognition Protocol), then ADR-1 (Carrier Equivalence), then task-relevant ADRs.

## 6. Seed Packet v1.0.0 (Bootstrapping)

**File:** `seed-packet-v1.0.0.md`
**Purpose:** Complete system genesis kit. How to bootstrap a new instance.
**Key content:** DNA (minimal genetic blueprint), Nutrients (starter bundle), Protective coat (safety primitives), Planting instructions (Phase 0-4), Growth conditions.

---

## Quick Reference: Precedence (from Spine v0.5 Section 1)

When artifacts disagree, resolve in this order:
1. Kernel (mandatory rules)
2. Spine (invariants + enforcement)
3. SDD Master Spec (architecture)
4. UpgradableArtifact schema + lints
5. Governance protocols
6. Current Build Spine (execution synthesis; contradiction resolver)
7. ADRs / RFCs
8. Contracts / Schemas
9. Tests + signed results
10. Code
11. Synthesis / analysis docs
