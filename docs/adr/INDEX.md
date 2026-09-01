# ADR Index — FLOSSI0ULLK / ARF Ecosystem

**Version:** 2.2.0
**Updated:** 2026-07-16
**Truth Status:** Specified
**Canonical reference:** `FLOSSI0ULLK-ADR-Suite-v2.0.md` (compiled 2026-04-26) is the consolidated narrative source. This index is the pointer surface kept in sync with the suite plus any post-suite additions (ADR-12..18).

---

## Numbering Convention

ADRs use sequential integers. Sub-ADRs (e.g., ADR-0.1) extend a parent without replacing it. Supersession is explicit via `supersedes` field.

Permanent numbers assigned in v2.0:
- `ADR-MCP-ORCHESTRATOR` → **ADR-10**, file `ADR-10-local-agent-node.md`. The rename has happened; the old
  filename no longer exists. Prose that cites the historical identifier alongside the number is accurate and
  intentional, but any *link* to `ADR-MCP-ORCHESTRATOR.md` is dead and should be repointed.
- `ADR-N` (IPFS) → **ADR-11**, file `ADR-11-ipfs-large-file-integration.md`. Same: renamed, old filename gone.

These two lines previously claimed the files were "kept under historical name to avoid breaking inbound links".
That stopped being true when the files were renamed, and the stale claim outlived the rename in
`docs/specs/spec-registry.json`, which carried duplicate entries for both old paths until 2026-08-24.

**Namespace separation — FLOSSI U curriculum ADRs:** the FLOSSI U Founding Kit defines a *separate* curriculum-ADR series using the zero-padded `001`–`019` namespace (containing-scope / curriculum layer). These do **not** share numbering with the repo's integer `ADR-0 … ADR-N` engineering ADRs indexed below; the two series are intentionally distinct and must not be cross-numbered.

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
| **ADR-7** | Embracing AGPL-3.0 Copyleft Cascade | Accepted | Verified | Low | 2026-04-15 | `ADR-7-agpl-cascade.md` |
| **ADR-8** | Radicle as Dev-Plane Code Substrate | Accepted | Specified (bridge unproven) | Medium | 2026-04-16 | `ADR-8-radicle-dev-substrate.md` |
| **ADR-9** | Self-Perceptual Evolution (n+1) | Proposed | Specified | Medium | 2026-04-17 | `ADR-9-self-perceptual-evolution.md` |
| **ADR-10** | Local Agent Node (Passive-Router MCP Consensus Gateway) | Accepted | Verified | Medium | 2026-04-10 | `ADR-10-local-agent-node.md` |
| **ADR-11** | IPFS Large File Integration for VVS-Compliant Git | Accepted | Specified | Medium | 2025-11-11 | `ADR-11-ipfs-large-file-integration.md` |
| **ADR-12** | Consent Gate Protocol | Draft (implementation-backed) | Specified (substrate verified locally; action-time gating + DID hardening + cross-frame validation pending) | High (OVERRIDE FORBIDDEN; APPROVE ≥ 0.85) | 2026-05-19 | `ADR-12-consent-gate-protocol.md` |
| **ADR-13** | Yumeichan Watch Architecture (Affective Edge Node) | Accepted | Specified | High | 2026-06-13 | `ADR-13-yumeichan-watch-architecture.md` |
| **ADR-14** | ObjectGraph Projection over Corpus | Accepted | Specified → Verified on landing | Low | 2026-06-13 | `ADR-14-objectgraph-projection.md` |
| **ADR-15** | Enforce Author–Provenance Binding in Integrity Zome | Accepted (impl P1) | Specified | High (security / core invariant) | 2026-06-13 | `ADR-15-provenance-validation-enforcement.md` |
| **ADR-16** | Omnigent as Execution/Governance Surface; Gateway + Holochain as Validation Substrate | Proposed | Specified (upstream capability + fork state Verified; integration seam Specified; validation fit Blocked) | High (execution/governance seam) | 2026-06-17 | `ADR-16-omnigent-execution-surface.md` |
| **ADR-17** | KnowledgeTriple Contract Reconciliation (signed-gradient confidence; enum-now/URI-later predicates) | Proposed | Specified (divergence Verified; D1/D2 pending gate acceptance) | High (Phase 1 primary-deliverable contract) | 2026-07-04 | `ADR-17-knowledge-triple-contract-reconciliation.md` |
| **ADR-18** | Prior-Art & Reuse Gate (before_build_check enforced via spec_gate + reuse-review voters) | Accepted (operator 2026-07-16) | Specified (--check enforcement Verified on landing) | Low (T1) / Medium (T2 review) | 2026-07-16 | `ADR-18-prior-art-reuse-gate.md` |
| **ADR-19** | OmniRoute Inference Plane + MCP Daemon Migration | Accepted (operator-consented 2026-07-17; consensus-pending) | Verified (Stages 0–3.5 implemented + tested; equivalence run closed 2026-07-26 — see ADR evidence for two disclosed caveats) | Medium (System blast radius; transport-plane change) | 2026-07-17 | `ADR-19-omniroute-inference-plane.md` |
| **ADR-20** | Provenance Validator Reconciliation (evidence-vocabulary drift, p-ancestor over-validation, unbuilt supersession view) | Accepted (operator 2026-08-24; D-A1 + D-B3 landed, D-B1 unbuilt) | Verified (defects reproduced then fixed; 267 tests; hook lands claims end-to-end) / Specified (D-B1 unimplemented) | **Substrate** (reclassified 2026-08-25 by external meta-audit; override forbidden) | 2026-08-23 | `ADR-20-provenance-validator-reconciliation.md` |

---

## Numbering History

Previous documents used inconsistent numbering. This index resolves conflicts:

| Old Reference | New Canonical ID | Reason |
|---------------|-----------------|--------|
| `ADR-003` | ADR-3 | Renumbered for consistency |
| `ADR-N` (SDD) | ADR-4 | Assigned permanent number |
| `ADR-N` (IPFS) | **ADR-11** | Promoted to permanent in v2.0 suite |
| `ADR-MCP-ORCHESTRATOR` | **ADR-10** | Promoted to permanent in v2.0 suite |
| `docs/ADRs/ADR-2-Holochain-Integration-Stack.md` | *(none — archived)* | **Shadow-directory collision, resolved 2026-08-12.** Self-declared SUPERSEDED by `ADR-2-holochain-substrate.md`; retained only as a record of a methodology violation. Archived to `archive/adr-versions/…_shadow-collision_2025-11-17.md`. |
| `docs/ADRs/ADR-3-Documentation-Consolidation.md` | *(none — archived)* | **Shadow-directory collision, resolved 2026-08-12.** Number already held by `ADR-3-metaprompt-kernelization.md`. Its subject (doc consolidation, 2025-12-11) has been superseded by the 2026-05 doc-cull triage and the 2026-08 consolidation passes. Archived to `archive/adr-versions/…_shadow-collision_2025-12-11.md`. |

**`docs/ADRs/` and `docs/specifications/` no longer exist.** They were unindexed, ungated shadows of `docs/adr/` and `docs/specs/`. The Codex repository atlas classified both shadow ADRs as `canon-governance` at read-priority **L1**, meaning any agent trusting that map would have loaded them as governance material without any signal that both numbers were already taken. `docs/specifications/keri-identity-bridge.yaml` (marked RETROACTIVE, no `docs/specs/` counterpart) was archived alongside them to `archive/spec-versions/`.

**Rule going forward:** ADRs live in `docs/adr/` and specs in `docs/specs/` — the two surfaces `spec_gate.py` actually walks. A document outside a gated surface is invisible to `--check` and will drift silently, which is exactly how these two survived a numbering reconciliation.

Pending file renames (cosmetic, follow-up):
- `ADR-10-local-agent-node.md` → `ADR-10-local-agent-node.md` (with inbound-link redirects)
- `ADR-11-ipfs-large-file-integration.md` → `ADR-11-ipfs-large-file-integration.md` (with inbound-link redirects)

---

## Rules

Per Project Spine v0.5 §6 plus ADR-Suite v2.0:
- ADRs document decisions + rationale + supersession chain.
- `Decision Status` captures the ADR lifecycle (`Proposed`, `Accepted`, `Validated`, `Rejected`, `Superseded`, `Draft (implementation-backed)`).
- `Truth Status` captures evidence level (`Verified`, `Specified`, `Aspirational`, `Unverified`) on every load-bearing claim — no claim presented as `Verified` without traceable repo artifacts.
- `Friction Tier` captures change cost (`Low`, `Medium`, `High`). Substrate-touching ADRs (e.g. ADR-12) carry override-forbidden semantics and elevated APPROVE thresholds.
- New ADRs reference this index and update it; if the ADR is consolidated into a future suite (v2.1, v3.0, …), update the canonical-reference banner above.
