# ADR Index — FLOSSI0ULLK / ARF Ecosystem

**Version:** 2.0.0
**Updated:** 2026-05-25
**Truth Status:** Specified
**Canonical reference:** `FLOSSI0ULLK-ADR-Suite-v2.0.md` (compiled 2026-04-26) is the consolidated narrative source. This index is the pointer surface kept in sync with the suite plus any post-suite additions (ADR-12).

---

## Numbering Convention

ADRs use sequential integers. Sub-ADRs (e.g., ADR-0.1) extend a parent without replacing it. Supersession is explicit via `supersedes` field.

Permanent numbers assigned in v2.0:
- `ADR-MCP-ORCHESTRATOR` → **ADR-10** (file kept under historical name to avoid breaking inbound links; cross-reference both).
- `ADR-N` (IPFS) → **ADR-11** (file kept under historical name pending a rename pass; cross-reference both).

---

## Active ADRs

| ADR | Title | Decision Status | Truth Status | Friction | Date | File |
|-----|-------|-----------------|--------------|----------|------|------|
| **ADR-0** | Recognition Protocol | Validated | Verified | — | 2025-11-01 | `ADR-0-recognition-protocol.md` |
| **ADR-0.1** | Cross-AI Transmission Validation | Validated | Verified | — | 2025-11-02 | `ADR-0.1-cross-ai-validation.md` |
| **ADR-1** | Carrier Equivalence Principle | Accepted | Specified | Low | 2026-01-05 | `ADR-1-carrier-equivalence.md` |
| **ADR-2** | Holochain as Runtime Substrate | Accepted | Specified (evidence patch pending) | High | 2026-03-05 | `ADR-2-holochain-substrate.md` |
| **ADR-3** | Metaprompt Kernelization | Accepted | Verified | Low | 2026-01-12 | `ADR-3-metaprompt-kernelization.md` |
| **ADR-4** | Specification-Driven Development | Accepted | Specified (CI pending) | Low | 2025-12-15 | `ADR-4-spec-driven-development.md` |
| **ADR-5** | Cognitive Virology as Architectural Pattern | Accepted | Specified (consent gate now backed by ADR-12) | High | 2026-03-21 | `ADR-5-cognitive-virology-pattern.md` |
| **ADR-6** | Four-System Meta-Orchestration Integration | Accepted | Specified (Seam 1 partial) | Medium | 2026-04-04 | `ADR-6-four-system-integration.md` |
| **ADR-7** | Embracing AGPL-3.0 Copyleft Cascade | Accepted | Specified | Low | 2026-04-15 | `ADR-7-agpl-cascade.md` |
| **ADR-8** | Radicle as Dev-Plane Code Substrate | Accepted | Specified (bridge unproven) | Medium | 2026-04-16 | `ADR-8-radicle-dev-substrate.md` |
| **ADR-9** | Self-Perceptual Evolution (n+1) | Accepted | Specified | Medium | 2026-04-17 | `ADR-9-self-perceptual-evolution.md` |
| **ADR-10** | Local Agent Node (Passive-Router MCP Consensus Gateway) | Accepted | Verified | Medium | 2026-04-10 | `ADR-MCP-ORCHESTRATOR.md` |
| **ADR-11** | IPFS Large File Integration for VVS-Compliant Git | Accepted | Specified | Medium | 2025-11-11 | `ADR-N-IPFS-Integration-VVS.md` |
| **ADR-12** | Consent Gate Protocol | Draft (implementation-backed) | Specified (substrate verified locally; action-time gating + DID hardening + cross-frame validation pending) | High (OVERRIDE FORBIDDEN; APPROVE ≥ 0.85) | 2026-05-19 | `ADR-12-consent-gate-protocol.md` |

---

## Numbering History

Previous documents used inconsistent numbering. This index resolves conflicts:

| Old Reference | New Canonical ID | Reason |
|---------------|-----------------|--------|
| `ADR-003` | ADR-3 | Renumbered for consistency |
| `ADR-N` (SDD) | ADR-4 | Assigned permanent number |
| `ADR-N` (IPFS) | **ADR-11** | Promoted to permanent in v2.0 suite |
| `ADR-MCP-ORCHESTRATOR` | **ADR-10** | Promoted to permanent in v2.0 suite |

Pending file renames (cosmetic, follow-up):
- `ADR-MCP-ORCHESTRATOR.md` → `ADR-10-local-agent-node.md` (with inbound-link redirects)
- `ADR-N-IPFS-Integration-VVS.md` → `ADR-11-ipfs-large-file-integration.md` (with inbound-link redirects)

---

## Rules

Per Project Spine v0.5 §6 plus ADR-Suite v2.0:
- ADRs document decisions + rationale + supersession chain.
- `Decision Status` captures the ADR lifecycle (`Proposed`, `Accepted`, `Validated`, `Rejected`, `Superseded`, `Draft (implementation-backed)`).
- `Truth Status` captures evidence level (`Verified`, `Specified`, `Aspirational`, `Unverified`) on every load-bearing claim — no claim presented as `Verified` without traceable repo artifacts.
- `Friction Tier` captures change cost (`Low`, `Medium`, `High`). Substrate-touching ADRs (e.g. ADR-12) carry override-forbidden semantics and elevated APPROVE thresholds.
- New ADRs reference this index and update it; if the ADR is consolidated into a future suite (v2.1, v3.0, …), update the canonical-reference banner above.
