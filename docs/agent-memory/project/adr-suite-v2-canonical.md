---
id: project-adr-suite-v2-canonical
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_adr_suite_v2_canonical.md
title: ADR-Suite v2.0 is hand-verified canonical
legacy_description: FLOSSI0ULLK-ADR-Suite-v2.0.md (2026-04-26, Perplexity synthesis,
  hand-verified by user) is the consolidated authoritative ADR registry — supersedes
  ad-hoc ADR INDEX drift
origin_session_id: 567c823f-3cba-4d75-866d-600bd4286e6f
---

`FLOSS/docs/adr/FLOSSI0ULLK-ADR-Suite-v2.0.md` (compiled 2026-04-26, Perplexity AI synthesis, hand-verified and approved by Anthony) is the consolidated authoritative ADR registry. Treat it as canon when it conflicts with older `docs/adr/INDEX.md` content.

**Why:** Earlier I flagged this as suspicious because of the prior hallucinated-ADR-suite incident. User confirmed: "the latest adr suite is factual and hand verified approved by me." The body has been reviewed and is not synthetic.

**Permanent ADR numbering established:**
- ADR-0 (Recognition Protocol) — **Validated** ✅ all 4 criteria passed including Test #4 Coherence on 2026-03-20
- ADR-0.1 (Cross-AI Transmission Validation) — Validated ✅
- ADR-1 (Carrier Equivalence Principle) — Accepted, Specified
- ADR-2 (Holochain as Runtime Substrate) — **Accepted** (upgraded from Proposed); DNA compiles, full Tryorama suite unvalidated
- ADR-3 (Metaprompt Kernelization) — Accepted, Verified
- ADR-4 (Specification-Driven Development) — Accepted, Specified (CI enforcement pending)
- ADR-5 (Cognitive Virology) — Accepted, Mixed truth-status; consent gate is LATER
- ADR-6 (Four-System Meta-Orchestration) — Accepted, Specified; Seam 1 partial
- ADR-7 (AGPL-3.0 Copyleft Cascade) — Accepted, Specified
- ADR-8 (Radicle Dev-Plane Substrate) — Accepted, Specified; **bridge unproven** (highest-priority NOW item gated by this ADR)
- ADR-9 (Self-Perceptual Evolution / n+1 ContinuityPayload) — Proposed, Specified; uses existing Claim wire format, not new top-level type
- **ADR-10** (MCP Server Consensus Hub) — formerly ADR-MCP-ORCHESTRATOR — Accepted, Verified (32/32 tests)
- **ADR-11** (IPFS Large-File / VVS) — formerly ADR-N — Accepted, Specified

**Standing rules canonicalized in v2.0:**
1. Blast-radius discipline (Low/Medium/High friction tiers; High requires unanimous +1)
2. Now/Later/Never discipline (no LATER built as NOW)
3. **Anti-sycophancy mandate** (every AI joining must internalize this — non-negotiable)
4. Truth Status on every claim (✅/⚠️/🔮/❌)
5. Supersession is explicit (no silent replacement)
6. Fork-ability is a design constraint

**Vote model is analog (float in [-1.0, +1.0])**, not ternary, per ADR-10 v2.0. The original ternary description is formally superseded; all dependent specs (ADR-6 Seam 1, ADR-9 ContinuityClaim, `consensus-gate.schema.json`) must use analog.

**Proposed gaps (future ADR-12, ADR-13):**
- ADR-12: Consent Gate Protocol (resolves ADR-5/ADR-1 tension; the most important unresolved item in the suite)
- ADR-13: Steward Vote Protocol (resolves ADR-7 carve-out mechanism)

**How to apply:**
- When ADR INDEX.md and the v2.0 suite disagree, prefer the v2.0 suite.
- When citing ADR-MCP-ORCHESTRATOR, also note it as ADR-10. Same for ADR-N → ADR-11.
- When proposing votes, use analog [-1, +1], not ternary.
- When working on dev-plane code substrate work, the Radicle bridge spike is the gating NOW item.
- Do not silently start work on the consent gate (ADR-12) — it requires HARVEST Protocol ≥3 cycles first per ADR-5.
