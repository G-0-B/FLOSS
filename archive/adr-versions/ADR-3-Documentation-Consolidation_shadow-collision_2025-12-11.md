# ADR-3: Documentation Consolidation

**Status**: ACCEPTED
**Date**: 2025-12-11
**Deciders**: Claude Opus 4, Anthony (kalisam)

---

## Intent Echo

Resolve documentation conflicts, duplicates, and confusing version schemes across the FLOSS/ARF codebase to establish clear, unambiguous documentation hierarchy.

---

## Problem Statement

An analysis of the codebase revealed the following documentation issues:

1. **ADR-1 Numbering Conflict**: Two completely different ADR-1 documents existed:
   - `ARF/ADR-1.md` - Python Module Extraction and Validation Strategy
   - `docs/ADRs/ADR-1-Holochain-Integration-Stack.md` - Holochain Integration Stack (KERI, AD4M, hREA)

2. **Duplicate README**: `README (2).md` in root was actually an IPFS integration overview incorrectly named

3. **Executive Summary Conflict**:
   - `EXECUTIVE-SUMMARY-AND-ACTION-PLAN.md` contained git merge conflict markers
   - `IPFS Integration_11-11-2025_EXECUTIVE-SUMMARY-AND-ACTION-PLAN.md` was a dated duplicate

4. **Confusing Specification Versions**: Four specification files with unclear versioning:
   - `arf_flossi_0_ullk_sdd_master_specification_v_0.md`
   - `arf_flossi_0_ullk_sdd_master_specification_v_00.md`
   - `arf_flossi_0_ullk_sdd_master_specification_v_000.md`
   - `arf_flossi_0_ullk_sdd_master_specification_v_01.md`

---

## Multi-Lens Snapshot

### Practical/Engineering Lens
- Multiple conflicting documents create confusion for contributors
- New AI conversations may load wrong ADR-1 and make incorrect decisions
- Merge conflicts left in committed files indicate incomplete merges

### Critical/Red-Team Lens
- ADR numbering conflict could cause citing wrong decision
- Unclear canonical specification could lead to implementing against outdated version
- Technical debt compounds over time if not addressed

### Values (Love-Light-Knowledge) Lens
- **Light**: Transparency requires clear, unambiguous documentation
- **Knowledge**: Confusing docs create cognitive debt for all contributors
- **Love**: Respect for contributors' time requires organized materials

### Systems/Governance Lens
- Clear documentation hierarchy enables better AI-human collaboration
- Provenance tracking requires stable document identifiers
- Future ADRs need unique numbers to function as memory substrate

---

## Decision

**[+1 Proceed]** with the following consolidation actions:

### 1. ADR Renumbering
- Renamed `docs/ADRs/ADR-1-Holochain-Integration-Stack.md` to `ADR-2-Holochain-Integration-Stack.md`
- Added note explaining the renumbering for historical context
- `ARF/ADR-1.md` remains unchanged (it was chronologically first)

### 2. Duplicate README Resolution
- Renamed `README (2).md` to `docs/IPFS-INTEGRATION-README.md`
- This correctly reflects its content as an IPFS integration navigation document

### 3. Executive Summary Cleanup
- Fixed merge conflict markers in `EXECUTIVE-SUMMARY-AND-ACTION-PLAN.md`
- Deleted dated duplicate `IPFS Integration_11-11-2025_EXECUTIVE-SUMMARY-AND-ACTION-PLAN.md`

### 4. Specification Consolidation
- Created `ARF/docs/archive/` directory for historical versions
- Moved `v_0`, `v_00`, `v_000` to archive
- Renamed `v_01` to `arf_flossi_0_ullk_sdd_master_specification.md` (canonical)
- Added `archive/README.md` explaining the archive contents

---

## Consequences

### Positive
- Clear ADR numbering sequence (0, 0.1, 1, 2, 3...)
- Single authoritative specification file
- No duplicate or conflicting documents
- Merge conflicts resolved
- Historical versions preserved in archive

### Negative
- Any external references to old file paths will need updating
- ADR-2 references must be used for Holochain Integration Stack

### Neutral
- Archive directory adds small organizational overhead
- Document renames may appear in git history

---

## Files Changed

| Action | Old Path | New Path |
|--------|----------|----------|
| Rename | `docs/ADRs/ADR-1-Holochain-Integration-Stack.md` | `docs/ADRs/ADR-2-Holochain-Integration-Stack.md` |
| Rename | `README (2).md` | `docs/IPFS-INTEGRATION-README.md` |
| Edit | `EXECUTIVE-SUMMARY-AND-ACTION-PLAN.md` | (fixed merge conflict) |
| Delete | `IPFS Integration_11-11-2025_EXECUTIVE-SUMMARY-AND-ACTION-PLAN.md` | - |
| Archive | `ARF/docs/arf_flossi_0_ullk_sdd_master_specification_v_0.md` | `ARF/docs/archive/...` |
| Archive | `ARF/docs/arf_flossi_0_ullk_sdd_master_specification_v_00.md` | `ARF/docs/archive/...` |
| Archive | `ARF/docs/arf_flossi_0_ullk_sdd_master_specification_v_000.md` | `ARF/docs/archive/...` |
| Rename | `ARF/docs/arf_flossi_0_ullk_sdd_master_specification_v_01.md` | `ARF/docs/arf_flossi_0_ullk_sdd_master_specification.md` |
| Create | - | `ARF/docs/archive/README.md` |

---

## Validation Criteria

- [ ] No duplicate ADR numbers exist
- [ ] Only one master specification exists (not in archive)
- [ ] No merge conflict markers in committed files
- [ ] All documentation files have appropriate names reflecting their content

---

## Related Documents

- `ARF/ADR-0-recognition-protocol.md` - Meta-protocol establishing ADR system
- `ARF/ADR-1.md` - Python Module Extraction (retained)
- `docs/ADRs/ADR-2-Holochain-Integration-Stack.md` - Holochain Integration (renumbered)
- `ARF/docs/arf_flossi_0_ullk_sdd_master_specification.md` - Canonical specification

---

## Lessons Learned

1. **Version Control**: Use semantic versioning (e.g., v0.1, v0.2) instead of confusing schemes (v_0, v_00, v_000)
2. **ADR Coordination**: Check existing ADRs before assigning numbers
3. **Merge Hygiene**: Resolve merge conflicts before committing
4. **File Naming**: Avoid spaces and dates in filenames; use descriptive, stable names

---

**Compliance**: This ADR follows the FLOSSI0ULLK Operating Instructions methodology:
- Intent Echo present
- Multi-Lens analysis performed
- Clear decision with rationale
- Concrete actions with evidence
