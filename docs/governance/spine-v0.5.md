# Project Spine — FLOSSI0ULLK / ARF Ecosystem
**Version:** 0.5 (consolidated + seed packet + orchestration research binder)  
**Updated:** 2026-02-08  
**Status:** Normative “spine” (enforced invariants + upgrade mechanics)

> The spine is the project’s **minimum non-chaos set**: what must be legible, what must be labeled, and what must be provable—**while still allowing everything to evolve**.

---

## 0) Purpose
The spine exists to:
- prevent “spec ≠ implementation” confusion,
- stop drift across humans + multiple AI systems,
- preserve attribution and fork visibility,
- keep decentralization shippable (circulation > dams),
- enforce truth labels for capability claims,
- enable **upgrade-everything** without collapsing into governance chaos.

---

## 1) Canonical Sources and Precedence
When artifacts disagree, resolve conflicts in this order:

1. **Kernel (mandatory rules)** — the always-on coordination kernel for agents/humans  
2. **Project Spine (this document)** — invariants + enforcement expectations  
3. **Canonical architecture spec (SDD Master Spec)** — requirements, module boundaries, invariants  
4. **UpgradableArtifact schema + lints** — the shared format for “everything evolvable”  
5. **Governance protocols** — steward recognition, consent windows, upgrade procedures  
6. **ADRs / RFCs** — decisions + rationale + supersession chain  
7. **Contracts / Schemas** — machine-checkable constraints  
8. **Tests + signed test results** — what makes ✅ Verified true  
9. **Code** — implementation detail; must conform  
10. **Synthesis / analysis docs** — context only unless triaged + evidence-linked

**Rule:** Anything stated outside the chain must be triaged (✅/⚠️/🔮/❌) before being cited as capability.

---

## 2) Prime Directive (ULLK Substrate)
ULLK is an engineering constraint:

- **Love:** consent-first; reduce coercion; non-retaliation  
- **Light:** transparency; auditability; fork visibility  
- **Knowledge:** reproducible verification; provenance-first; open commons  

**Prime Directive:** Increase sovereignty; reduce coercion; reduce cognitive debt; prefer verifiable coordination over impressive speculation.

---

## 3) “Upgrade Everything” (No Immutable Stones)
Nothing is infinitely frozen—not even FLOSSI0ULLK. We replace “immutability” with:

- **versioning** (semver + supersedes links),
- **fork visibility** (divergence is data),
- **compatibility negotiation** (ranges),
- **friction tiers** (cost-to-change),
- **rollback plans** (reversibility).

### 3.1 UpgradableArtifact minimum contract
Every serious artifact SHOULD be an UpgradableArtifact with:
- `id`, `version`, `kind`, `status`, `supersedes[]`
- `truth_status` (✅/⚠️/🔮/❌)
- `evidence_sources[]` (links to tests/docs/commits)
- `upgrade_path[]` + `rollback_plan`

### 3.2 Friction tiers (cost-to-change)
- **Low:** docs/examples (fast iteration)
- **Medium:** CI thresholds/workflows (review + pilot recommended)
- **High:** identity/provenance/consent semantics (simulate + pilot + quorum + rollback required)

---

## 4) Claim Truth Model (Required Labels)
Every capability claim must carry one label:

| Label | Meaning | Allowed phrasing |
|---|---|---|
| ✅ **Verified** | implemented + tested (or externally validated with attribution) | “is implemented / validated” |
| ⚠️ **Specified** | designed; code may exist; not validated | “is specified / in development” |
| 🔮 **Aspirational** | vision / roadmap / research direction | “we aim / we propose / future work” |
| ❌ **Unverified** | lacks evidence or attribution | “do not cite; triage required” |

**Default:** If unsure → ⚠️ (or ❌).

### Required header for syntheses/overviews
```yaml
capability_truth_model:
  verified: "tests or external validation exist"
  specified: "design documented; code may exist; not validated"
  aspirational: "vision/research; do not claim as current capability"
```

---

## 5) Two-Plane Architecture (Authority Boundary)
### Plane A — Dev Meta-Coordinator
Centralized tooling allowed for speed (plans, ADRs, PRs, CI).  
**Outputs are artifacts, not runtime truth.**

### Plane B — Runtime Meta-Coordinator
Agent-centric runtime truth, enforced by validation:
- per-agent history (source chains or equivalent)
- integrity rules that cannot be bypassed
- eventual consistency + sharded authority

**Bridge rule:** Plane A may publish into Plane B, but **cannot bypass** Plane B validation.

---

## 6) Voluntary Convergence (Federation Without Coercion)
- Integration is voluntary.
- Forks are first-class and must remain visible.
- Coherence emerges by **protocol resonance**, not forced synchrony.

Practical rule: if two groups disagree, the system must support:
- a forked artifact line (new `id` or divergent `supersedes` chain),
- explicit compatibility ranges,
- a measured comparison (metrics, outcomes), not hidden struggle.

---

## 7) Provenance Packet (Cross‑AI + Cross‑System Handoff)
Any cross-system handoff SHOULD include a provenance packet:

```yaml
timestamp: ISO8601
author_agent: string
human_collision_node: string
source_systems: [list]
claim_type: ["observed_fact","repo_assumption","proposal","target"]
payload:
  summary: "≤15 lines"
  evidence: ["ADR","file","commit","log","test-result"]
  risks: ["-1 items"]
  benefits: ["+1 items"]
next_action: "one clear ask"
```

Rule of thumb: **no provenance packet → treat as context**, not an actionable artifact.

---

## 8) Seed Packets (Bootstrapping + Reproduction)
A **seed packet** is an UpgradableArtifact bundle meant to bootstrap a new instance of the ecosystem.

### 8.1 Canonical seed artifacts (current set)
- `flossi0ullk_seed_packet_manifest.md` (conceptual “genesis kit” synthesis)
- `flossi0ullk-seed-packet@1.0.0` (normative bootstrapping instructions + bundle template)
- `research-report-agent-orchestration@1.0.0` (technical grounding + substrate-first roadmap)
- `kb-index-winwings@1.0.0` (evidence binder / citation index)

### 8.2 Seed packet invariant
A seed packet **must** include:
- a Project Spine reference,
- a substrate-first viability test (Phase 0),
- truth-labeling rules,
- an upgrade path + rollback plan.

---

## 9) Substrate-First Gating (Phase 0 is a hard gate)
Before building orchestration logic or agent autonomy, validate the substrate bridge:

**Goal:** prove “code substrate ↔ provenance substrate” linkage is verifiable by any peer.

Minimal loop:
1) publish an ADR/decision artifact to the code substrate,  
2) emit a provenance entry referencing its hash + signatures,  
3) verify independently from another node.

**Pass criteria (pragmatic):**
- convergence after quiescence across ≥3 nodes,
- conflict produces visible fork (not silent overwrite),
- verification requires no privileged access.

If Phase 0 fails, **pivot substrate**.

---

## 10) Automated Agent Orchestration (What we build now)
### 10.1 Task allocation (decentralized)
Prefer decentralized task allocation patterns:
- tasks are entries with requirements + blast radius tier,
- agents bid with capacity + evidence,
- assignment is recorded in provenance and mirrored into code collaboration artifacts.

### 10.2 Autonomy budgets (ACI)
Agents may:
- read/search/run tests,
- create branches + patches,
- open review artifacts,
- **but not merge high-risk changes** without approvals + CI proof.

### 10.3 CI is the spine’s nervous system
Agent autonomy scales only as CI reliability scales:
- reproducible environments,
- signed test results,
- policy gates for sensitive areas.

---

## 11) Traceability (Tenants → Artifacts → Tests)
Every new module must declare:
- which tenant(s) it serves,
- where it lives in the spec,
- what schemas/contracts it satisfies,
- what tests verify it,
- its truth status (✅/⚠️/🔮/❌).

---

## 12) Enforcement (What makes the spine real)
Minimum enforcement set:
- CI gates that fail builds when contracts/tests/spec alignment breaks
- Truth labels required on overview/synthesis docs
- Provenance packet required for cross-AI handoffs and major syntheses
- High-friction changes require simulate/pilot/rollback plan
- Seed packets must include Phase 0 substrate test and MVC bootstrapping steps

---

## Appendix A — Active artifacts added in this refresh
- Automated-Agent-Orchestration-Report_v1.0.0.md  
- kb-index-winwings_v1.0.0.md  
- flossi0ullk_seed_packet_manifest.md  
- flossi0ullk_seed_packet_v1.0.0.md  

---

## Appendix B — “Paste me” manifest snippet (starter)
```yaml
- id: "flossi0ullk-seed-packet"
  version: "1.0.0"
  kind: "seed_packet"

- id: "research-report-agent-orchestration"
  version: "1.0.0"
  kind: "technical_report"

- id: "kb-index-winwings"
  version: "1.0.0"
  kind: "research_index"
```
