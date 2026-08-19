# ADR-0000: ADR System, Versioning, and Upgrade-Everything
**Status:** Proposed (Generated)  
**Date:** 2026-02-08  
**Deciders:** FLOSSIOULLK stewards + contributors  
**Supersedes:** —  
**Superseded by:** —  

## Context
FLOSSIOULLK explicitly rejects “immutable tablets”: all artifacts (including governance and FLOSSI0ULLK itself) must remain evolvable.
At the same time, a decentralized ecosystem needs a legible decision record and a stable way to resolve conflicts across agents, repos, and time.

We need a consistent ADR format that:
- is machine-navigable and human-readable,
- supports supersession (no frozen stones),
- supports fork visibility (divergence is allowed but must be visible),
- supports “high friction changes” for high-blast-radius decisions.

This ADR defines the ADR system itself.

## Decision
Adopt ADRs as *UpgradableArtifacts*:
- Each ADR is versioned (e.g., ADR-0000@v1.0.0) and may be superseded.
- Supersession is explicit: new ADR references the previous ADR and records rationale + evidence.
- ADRs are normative only when their Status is **Accepted** (or **Deprecated** with explicit migration guidance).
- ADRs MUST include “Upgrade & Rollback” describing how to change, pilot, and revert.

Truth rule:
- An ADR records a decision; it does not guarantee implementation. Implementation claims must be backed by tests/signed results and provenance.

## Consequences
### Positive
- Creates a consistent “decision memory” across humans + multiple AI systems.
- Encodes the “upgrade everything” principle without sacrificing traceability.
- Makes forks/divergence explicit and auditable.

### Negative / Risks
- Adds process overhead.
- Risk of “governance theater” if ADRs are written but not enforced by CI/provenance.

## Alternatives Considered
- No ADRs; rely on informal discussion (rejected: drift).
- Immutable constitution / hard-coded rules (rejected: violates upgrade-everything).
- Blockchain DAO governance as the primary decision log (deferred: high overhead; social contract first).

## Evidence / References
- Project-Spine-FLOSSIOULLK_v0.5.md (precedence chain + upgrade-everything stance)
- flossi0ullk_seed_packet_v1.0.0.md (seed packet as bootstrappable, evolvable kit)

## Upgrade & Rollback
Upgrade path (normal):
1) Draft ADR-NNNN@vX+1 with explicit supersedes link.
2) Run simulation/pilot if blast radius is Medium/High.
3) Require steward quorum proportional to blast radius.
4) Roll out and label old ADR as Deprecated (not deleted).

Rollback:
- Revert to previous ADR version and record rollback ADR with incident summary.



---


# ADR-0001: Carrier Equivalence Principle as a Design Invariant
**Status:** Proposed (Generated)  
**Date:** 2026-02-08  
**Deciders:** FLOSSIOULLK stewards + contributors  
**Supersedes:** —  
**Superseded by:** —  

## Context
FLOSSIOULLK frames “carrier equivalence” as an invariant: meaning should remain transferable across carriers (text/code/graph/tests/artifacts)
without privileging one representation in a way that causes drift or authority capture.

We need to establish carrier equivalence as an explicit architectural decision so that:
- specifications, provenance, code, and social governance can share a common shape,
- multi-agent collaboration can unify across mediums.

## Decision
Adopt Carrier Equivalence as a normative principle:
- All core artifacts (specs/ADRs/schemas/tests/provenance entries) MUST be representable as structured data plus a human-readable rendering.
- No single carrier (e.g., “the chat log” or “the repo README”) is allowed to be the only authoritative representation.
- Transformations between carriers MUST preserve identifiers and provenance links.

## Consequences
### Positive
- Reduces drift between “what we meant” and “what we shipped”.
- Enables a universal provenance graph to connect decisions, code, and outcomes.

### Negative / Risks
- Requires extra tooling (converters, linters, schema discipline).
- Might slow early prototyping if enforced too hard.

## Alternatives Considered
- Treat code as the only truth (rejected: loses rationale, human meaning).
- Treat narrative docs as the only truth (rejected: non-executable, ambiguous).

## Evidence / References
- Project-Spine-FLOSSIOULLK_v0.5.md (explicit precedence and “provable” stance)
- kb-index-winwings_v1.0.0.md (research index supporting carrier equivalence as core)

## Upgrade & Rollback
Changes to the definition of Carrier Equivalence are High blast radius:
- Require longer review window + red-team pass.
- Require migration tooling for existing artifacts.
Rollback: restore previous definition + provide compatibility adapters.



---


# ADR-0002: Two-Plane Architecture: Dev Meta-Coordinator vs Runtime Validation Plane
**Status:** Proposed (Generated)  
**Date:** 2026-02-08  
**Deciders:** FLOSSIOULLK stewards + contributors  
**Supersedes:** —  
**Superseded by:** —  

## Context
The project differentiates between:
- Plane A: fast iteration space (planning, drafting, CI, synthesis),
- Plane B: runtime truth (agent-centric validation, provenance, integrity rules).

We need a crisp boundary so that centralized convenience does not become a de facto authority capture.

## Decision
Adopt a Two-Plane Architecture:
- Plane A may produce artifacts (plans, patches, ADR drafts, CI results).
- Plane B validates and records runtime truth; Plane A cannot bypass Plane B validation.
- Cross-plane bridges MUST be explicit adapters that emit provenance packets including hashes and signatures.

## Consequences
### Positive
- Allows speed without sacrificing decentralization.
- Clarifies what is “planning output” versus “validated runtime truth”.

### Negative / Risks
- Requires bridge tooling and explicit provenance logging.
- Adds complexity to developer workflows.

## Alternatives Considered
- Fully centralized coordination (rejected: centralization risk).
- Fully decentralized everything from day 1 (risky: slower; tooling maturity).

## Evidence / References
- Project-Spine-FLOSSIOULLK_v0.5.md section on Two-Plane Architecture and bridge rule

## Upgrade & Rollback
Upgrade path:
- Bridge changes are Medium/High blast radius depending on scope.
- Any change that weakens Plane B validation requirements requires steward quorum + pilot network test.

Rollback:
- Revert bridge adapter versions; keep Plane B validators strict.



---


# ADR-0003: Kernelization: Always-on Coordination Kernel for Agents and Humans
**Status:** Proposed (Generated)  
**Date:** 2026-02-08  
**Deciders:** FLOSSIOULLK stewards + contributors  
**Supersedes:** —  
**Superseded by:** —  

## Context
Multi-agent + human collaboration drifts when coordination rules are implicit or scattered.
A “kernel” is needed to provide always-on invariants: truth labeling, provenance expectations, safety boundaries, and escalation norms.

This is not an immutable constitution; it is an evolvable kernel module.

## Decision
Adopt a Coordination Kernel (the FLOSSI0ULLK Kernel):
- Defines minimum rules for artifact labeling (✅/⚠️/🔮/❌), provenance packet format, and escalation.
- Agents MUST treat kernel rules as mandatory when interacting in the ecosystem.
- Kernel is versioned and upgradeable via ADR-0000 mechanisms.

## Consequences
### Positive
- Reduces fragmentation across multiple AIs/tools.
- Makes “what counts” explicit (evidence, provenance).

### Negative / Risks
- If too strict, can stifle creative exploration.
- Requires clear separation between “kernel rules” and “context/proposals”.

## Alternatives Considered
- Rely on ad-hoc prompt discipline (rejected: doesn’t scale).
- Hard-code all rules in runtime (rejected: violates upgrade-everything).

## Evidence / References
- Project-Spine-FLOSSIOULLK_v0.5.md precedence chain (Kernel is top of normative order)

## Upgrade & Rollback
Kernel changes:
- Medium blast radius by default; High if modifying consent/non-retaliation or trust rules.
- Require simulation/pilot and explicit backward compatibility notes.

Rollback:
- Revert kernel version; preserve provenance logs of the change.



---


# ADR-0004: Synthesis Integration Triage and Truth Labels
**Status:** Proposed (Generated)  
**Date:** 2026-02-08  
**Deciders:** FLOSSIOULLK stewards + contributors  
**Supersedes:** —  
**Superseded by:** —  

## Context
The ecosystem includes many artifact types: research reports, drafts, code, test results, and agent outputs.
To prevent “analysis masquerading as capability,” every claim needs a truth status.

We need standardized triage labels and what qualifies as “Verified”.

## Decision
Adopt standard claim triage:
- ✅ Verified: backed by tests/signed results/provenance
- ⚠️ Plausible: supported by evidence but not yet validated in this stack
- 🔮 Proposal: design intent; not implemented
- ❌ False/Deprecated: known invalid or superseded

All artifacts that include capability claims MUST include triage status + evidence pointers.

## Consequences
### Positive
- Reduces confusion and overclaiming.
- Enables automation (linters can fail builds on unlabeled claims).

### Negative / Risks
- Extra authoring burden.
- Risk of bikeshedding about labels.

## Alternatives Considered
- No labels; rely on reader judgment (rejected: too error-prone).

## Evidence / References
- Project-Spine-FLOSSIOULLK_v0.5.md truth-label rule and precedence chain

## Upgrade & Rollback
Upgrade: extend label taxonomy only with backwards-compatible mapping.
Rollback: keep old labels supported; provide mapping table in kernel.



---


# ADR-0005: Universal Provenance Substrate on Agent-Centric Validation
**Status:** Proposed (Generated)  
**Date:** 2026-02-08  
**Deciders:** FLOSSIOULLK stewards + contributors  
**Supersedes:** —  
**Superseded by:** —  

## Context
FLOSSIOULLK requires a substrate that supports:
- agent sovereignty,
- cryptographic provenance,
- validation rules (including warrants/misbehavior signaling),
- eventual consistency without a single global ledger.

The architecture references an agent-centric approach (e.g., Holochain-style validation).

## Decision
Adopt an agent-centric provenance substrate as the runtime truth plane:
- Per-agent append-only history (source chains or equivalent)
- Sharded, validating DHT for shared entries
- Application-specific validation rules for accepting/denying entries
- Misbehavior signaling (warrants) that can be gossiped and acted upon

All high-impact actions (governance changes, merges, consent changes) MUST emit provenance events.

## Consequences
### Positive
- Enables verifiable audit trail without centralization.
- Supports consent and revocation as protocol events.

### Negative / Risks
- Higher complexity than centralized DB.
- Validation rules must be carefully designed to avoid deadlocks and false positives.

## Alternatives Considered
- Blockchain ledger for everything (deferred: overhead, global consensus).
- Central database with signatures (rejected: centralization risk).

## Evidence / References
- Automated-Agent-Orchestration-Report_v1.0.0.md (validated patterns: agent-centric trust substrate + provenance)
- Project-Spine-FLOSSIOULLK_v0.5.md (provenance packet requirement)

## Upgrade & Rollback
Upgrades require:
- Migration plan for existing entries,
- Compatibility adapters for old event schemas,
- Network pilot across multiple nodes.

Rollback:
- Maintain ability to read old schemas; revert validators if upgrade causes partition.



---


# ADR-0006: Radicle as Sovereign Code Collaboration Substrate and Bridge to Provenance
**Status:** Proposed (Generated)  
**Date:** 2026-02-08  
**Deciders:** FLOSSIOULLK stewards + contributors  
**Supersedes:** —  
**Superseded by:** —  

## Context
Decentralized open-source development needs a code collaboration substrate without reliance on a central forge.
The orchestration research highlights Radicle as a local-first, P2P Git collaboration and governance layer.

We also require a verifiable bridge from code artifacts (commits/patches/ADRs stored with code) into the provenance substrate.

## Decision
Adopt Radicle-style P2P Git as the code collaboration substrate (initially for core repos):
- Repos replicated via P2P gossip; commits and patches signed.
- Delegates + signature thresholds define canonical head for a repo.
- Issues/reviews represented as replicated collaborative objects where appropriate.

Bridge rule:
- Any governance-relevant code event MUST be mirrored into the provenance substrate
  by storing commit/patch identifiers + delegate signatures inside a provenance packet.

## Consequences
### Positive
- Removes single-forge dependency for core coordination.
- Provides threshold-based governance primitives at the repo level.

### Negative / Risks
- Bridge complexity: identity mapping, latency, conflict semantics.
- Operational burden: running relays/peers for discoverability.

## Alternatives Considered
- GitHub/GitLab as canonical forge (rejected: centralization).
- Pure provenance substrate for code storage (possible pivot if bridge fails).

## Evidence / References
- Automated-Agent-Orchestration-Report_v1.0.0.md (Radicle governance + P2P code collaboration)
- Project-Spine-FLOSSIOULLK_v0.5.md (Phase-0 bridge validation gate)

## Upgrade & Rollback
Phase-0 gate:
- Prove “publish ADR/patch → provenance entry → independent verification” across ≥3 nodes.
If gate fails: pivot to alternative code substrate.

Rollback:
- Keep Radicle as mirror only; preserve provenance as canonical truth until bridge stabilizes.



---


# ADR-0007: Seed Packets for Bootstrapping New Instances
**Status:** Proposed (Generated)  
**Date:** 2026-02-08  
**Deciders:** FLOSSIOULLK stewards + contributors  
**Supersedes:** —  
**Superseded by:** —  

## Context
FLOSSIOULLK intends to be instantiable: the system should be able to “reproduce” into new environments without losing alignment.
A seed packet is a curated bundle of the minimum artifacts required to bootstrap a new instance.

## Decision
Adopt “Seed Packet” as a first-class artifact bundle:
- Includes: kernel rules, project spine, key ADRs, manifests, and evidence indexes.
- Includes planting instructions: how to instantiate minimal coordination + provenance + validation.
- Seed packets are versioned and upgradeable like any other artifact.

## Consequences
### Positive
- Supports rapid instantiation of aligned sub-ecosystems.
- Improves onboarding and reduces dependency on undocumented tribal knowledge.

### Negative / Risks
- Requires curation discipline.
- Risk of outdated seed packets; needs upgrade cadence.

## Alternatives Considered
- Ad-hoc onboarding and copying repos (rejected: drift + missing invariants).

## Evidence / References
- flossi0ullk_seed_packet_v1.0.0.md + flossi0ullk_seed_packet_manifest.md

## Upgrade & Rollback
Upgrade:
- New seed packet versions must include a changelog + compatibility notes.
Rollback:
- Revert to prior seed packet and record why.



---


# ADR-0008: Automated Agent Orchestration for Decentralized OSS Development
**Status:** Proposed (Generated)  
**Date:** 2026-02-08  
**Deciders:** FLOSSIOULLK stewards + contributors  
**Supersedes:** —  
**Superseded by:** —  

## Context
We want agent-centric automation to reduce human bottlenecks while preserving sovereignty and governance clarity.
The orchestration report surveys coordination algorithms (auctions/CBBA), governance models, infra patterns (Holochain/IPFS/Radicle), and automation tools.

We need a decision that formalizes the orchestration approach and safety boundaries.

## Decision
Adopt a constrained automation stack:
- Orchestration layer: role-based multi-agent workflows (graph/state-machine preferred for reproducibility).
- Task allocation: decentralized mechanisms (consensus/auction family) for claimable tasks; record assignments in provenance.
- Dev loop automation: CI + dependency bots + review/merge automation for low-risk changes.
- SWE-agents: allowed only in sandboxed ACI with strict budgets, logging, and blast-radius tiers.

All agent actions MUST emit provenance events and remain reviewable.

## Consequences
### Positive
- Increases throughput on routine work while keeping auditability.
- Provides a scalable path from manual to semi-autonomous to constrained autonomy.

### Negative / Risks
- Agent reliability limits; risk of noisy PRs and test overfitting.
- Security risks (supply-chain, sybils) require ongoing hardening.

## Alternatives Considered
- Fully manual development (slow; bottlenecks).
- Fully autonomous agents (unsafe; unreliable today).

## Evidence / References
- Automated-Agent-Orchestration-Report_v1.0.0.md (algorithms, governance patterns, automation tools, limitations)
- Project-Spine-FLOSSIOULLK_v0.5.md (Phase-0 substrate-first gating)

## Upgrade & Rollback
Upgrade:
- Increase autonomy only after metrics and CI gates prove stability.
- Add new orchestration capabilities via pilots; publish benchmark results.

Rollback:
- Disable agent write/merge permissions; revert to suggestions-only mode.



---


# ADR-0009: Steward Recognition and Governance Organs
**Status:** Proposed (Generated)  
**Date:** 2026-02-08  
**Deciders:** FLOSSIOULLK stewards + contributors  
**Supersedes:** —  
**Superseded by:** —  

## Context
To avoid implicit power structures and governance chaos, we need explicit recognition of roles (stewards/organs) and how decisions are made.
Governance must stay evolvable, but legible.

This ADR defines the minimum viable governance model consistent with decentralization and upgrade-everything.

## Decision
Adopt a liberal-contribution model with named stewards per “organ”:
- Identity & Provenance
- Policy & Alignment
- Value Flows & Incentives
- Compute & Infrastructure
- Development Methodology

Steward changes and high-blast-radius decisions require:
- explicit consent window,
- transparent rationale (ADR/provenance),
- non-retaliation constraint (revocation does not punish),
- reversibility/pilot for risky changes.

## Consequences
### Positive
- Makes authority explicit and challengeable.
- Enables coordination without defaulting to token/DAO complexity.

### Negative / Risks
- Requires social maintenance and rotation norms.
- Risk of capture if steward rotation is ignored.

## Alternatives Considered
- BDFL/founder rule (centralization risk).
- Token DAO as primary governance (complex; can become plutocracy).

## Evidence / References
- Project-Spine-FLOSSIOULLK_v0.5.md (governance organs + upgrade mechanics)
- Automated-Agent-Orchestration-Report_v1.0.0.md (OSS governance patterns + start-simple recommendation)

## Upgrade & Rollback
Upgrade:
- Organs can be split/merged; must publish transition plan and map responsibilities.
Rollback:
- Revert organ changes; preserve decision log; run postmortem ADR.



---

