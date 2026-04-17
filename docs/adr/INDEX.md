# ADR Index — FLOSSI0ULLK / ARF Ecosystem

**Version:** 1.1.0
**Updated:** 2026-04-16
**Truth Status:** Specified

---

## Numbering Convention

ADRs use sequential integers. Sub-ADRs (e.g., ADR-0.1) extend a parent without replacing it. Supersession is explicit via `supersedes` field.

---

## Active ADRs

| ADR | Title | Decision Status | Truth Status | Date | File |
|-----|-------|-----------------|--------------|------|------|
| **ADR-0** | Recognition Protocol | Legacy: Validated | — | 2025-11-01 | `ADR-0-recognition-protocol.md` |
| **ADR-0.1** | Cross-AI Transmission Validation | Legacy: Validated | — | 2025-11-02 | `ADR-0.1-cross-ai-validation.md` |
| **ADR-1** | Carrier Equivalence Principle | Proposed | — | 2026-01-05 | `ADR-1-carrier-equivalence.md` |
| **ADR-2** | Holochain Substrate Decision | Proposed | Specified | 2026-03-05 | `ADR-2-holochain-substrate.md` |
| **ADR-3** | Metaprompt Kernelization | Proposed | — | 2026-01-12 | `ADR-3-metaprompt-kernelization.md` |
| **ADR-4** | Specification-Driven Development | Accepted | — | 2025-12-15 | `ADR-4-spec-driven-development.md` |
| **ADR-5** | Cognitive Virology as Architectural Pattern | Specified | Specified | 2026-03-21 | `ADR-5-cognitive-virology-pattern.md` |
| **ADR-6** | Four-System Meta-Orchestration Integration | Proposed | Specified | 2026-04-04 | `ADR-6-four-system-integration.md` |
| **ADR-7** | Embracing AGPL-3.0 Copyleft Cascade | Accepted | — | 2026-04-15 | `ADR-7-agpl-cascade.md` |
| **ADR-8** | Radicle as Dev-Plane Code Substrate | Accepted | — | 2026-04-16 | `ADR-8-radicle-dev-substrate.md` |
| **ADR-MCP-ORCHESTRATOR** | Local Agent Node | Accepted | — | 2026-04-10 | `ADR-MCP-ORCHESTRATOR.md` |

---

## Numbering History

Previous documents used inconsistent numbering. This index resolves conflicts:

| Old Reference | New Canonical ID | Reason |
|---------------|-----------------|--------|
| `ADR-003` | ADR-3 | Renumbered for consistency |
| `ADR-N` (SDD) | ADR-4 | Assigned permanent number |
| `ADR-N` (IPFS) | Unassigned | Not yet prioritized (LATER) |

---

## Rules

Per Project Spine v0.5 Section 6:
- ADRs document decisions + rationale + supersession chain.
- `Decision Status` captures the ADR lifecycle (`Proposed`, `Accepted`, `Rejected`, `Superseded`). Some legacy ADRs still use a single legacy status label and are marked explicitly until normalized.
- `Truth Status` captures evidence level (`Verified`, `Specified`, `Aspirational`, `Unverified`) when the ADR defines it explicitly.
- ADR changes follow friction tiers (`Low`, `Medium`, `High`).
- New ADRs should reference this index and update it.
