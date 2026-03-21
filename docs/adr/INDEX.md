# ADR Index — FLOSSIOULLK / ARF Ecosystem

**Version:** 1.0.0
**Updated:** 2026-03-05
**Truth Status:** Specified

---

## Numbering Convention

ADRs use sequential integers. Sub-ADRs (e.g., ADR-0.1) extend a parent without replacing it. Supersession is explicit via `supersedes` field.

---

## Active ADRs

| ADR | Title | Status | Date | File |
|-----|-------|--------|------|------|
| **ADR-0** | Recognition Protocol | Accepted | 2025-11-01 | `ADR-0-recognition-protocol.md` |
| **ADR-0.1** | Cross-AI Transmission Validation | Validated | 2025-11-02 | `ADR-0.1-cross-ai-validation.md` |
| **ADR-1** | Carrier Equivalence Principle | Proposed | 2026-01-05 | `ADR-1-carrier-equivalence.md` |
| **ADR-2** | Holochain Substrate Decision | Proposed | 2026-03-05 | `ADR-2-holochain-substrate.md` |
| **ADR-3** | Metaprompt Kernelization | Proposed | 2026-01-12 | `ADR-3-metaprompt-kernelization.md` |
| **ADR-4** | Specification-Driven Development | Accepted | 2025-12-15 | `ADR-4-spec-driven-development.md` |

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
- ADRs document decisions + rationale + supersession chain
- Every ADR must carry a truth status label (Verified/Specified/Aspirational/Unverified)
- ADR changes follow friction tiers (Low/Medium/High)
- New ADRs should reference this index and update it
