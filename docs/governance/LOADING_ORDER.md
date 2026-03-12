# FLOSSIOULLK Governance Document Loading Order

When onboarding a new agent (human or AI) to the FLOSSIOULLK project, load documents in this order:

## 1. Kernel v1.2 (Mandatory Rules)

**File:** `kernel-v1.2.md`
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

## 4. Relevant ADRs (Decisions)

**Directory:** `../adr/`
**Index:** `../adr/INDEX.md`
**Purpose:** Specific architectural decisions with rationale and supersession chains.
**Load order within ADRs:** Start with ADR-0 (Recognition Protocol), then ADR-1 (Carrier Equivalence), then task-relevant ADRs.

## 5. Seed Packet v1.0.0 (Bootstrapping)

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
6. ADRs / RFCs
7. Contracts / Schemas
8. Tests + signed results
9. Code
10. Synthesis / analysis docs
