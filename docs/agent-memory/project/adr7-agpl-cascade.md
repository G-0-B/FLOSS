---
id: project-adr7-agpl-cascade
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_adr7_agpl_cascade.md
title: ADR-7 embraces AGPL-3.0 copyleft cascade
legacy_description: Load-bearing licensing decision — FLOSS core adopts AGPL-3.0,
  direct code porting from AIngram/Agorai unblocked
origin_session_id: 7a8fdf1c-cf5f-4d01-a344-82a0dec070b6
---

**ADR-7: Embracing AGPL-3.0 Copyleft Cascade** — at `FLOSS/docs/adr/ADR-7-agpl-cascade.md` (renamed from `ADR-7-agpl-mcp-integration.md`). Accepted 2026-04-15.

**Three decisions:**
1. Core FLOSSI0ULLK (`metacoordinator_mcp`, `ARF`, etc.) licensed AGPL-3.0-or-later
2. Direct code porting from AIngram/Agorai into Python/Rust is now allowed — no more artificial MCP-boundary constraint
3. Stewardship carve-out: dual-licensing exceptions available via formal Steward Vote for humanitarian/medical/educational use cases where strict open-sourcing can't work

**Why:** The earlier "arm's-length via MCP" framing was a defensive posture that contradicted the project's own commons-first philosophy. User's own argument settled it: "FLOSSI0ULLK's name is literally the answer... AGPL is not just fine. It's the only honest choice... the cascade is a feature, not a bug." Ideological integrity trumps adoption breadth.

**How to apply:**
- Integration Paths B (port AIngram domain modules to Python) and C (Rust integrity zomes) are now viable — prefer them when architecturally clean, rather than always defaulting to Path A (satellite MCP).
- `FLOSSI_U_Founding_Kit_v1.6/LICENSE` is now bare `SPDX-License-Identifier: AGPL-3.0-or-later` (previous multi-line content removed).
- Commercial closed-source SaaS on top of FLOSS is intentionally prohibited without dual-license agreement.
- When proposing integration with new AGPL code, default is "port directly if it makes sense"; standalone-bridge is now a pragmatic convenience, not a legal requirement.

**Parallel Gemini rewrote and committed ADR-7 in this form** (commit `9ef2b70` on `lappytop`). User approved the rewrite ("Go.") — this is signed, not unilateral.
