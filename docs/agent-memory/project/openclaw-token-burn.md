---
id: project-openclaw-token-burn
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_openclaw_token_burn.md
title: OpenClaw consumed the OpenAI token budget, not Codex
legacy_description: Project state correction — the rapid OpenAI token consumption
  flagged in 2026-05-16 session was caused by OpenClaw, NOT by Codex CLI. Codex remains
  a viable delegation target. Investigate OpenClaw's loop/configuration before re-enabling
  it against an OpenAI key.
origin_session_id: a04c9df9-7bf3-4c48-8305-871bc29b680d
---

The OpenAI usage spike that caused the prior session's "ran out of usage insanely fast" symptom was caused by **OpenClaw**, not Codex. Confirmed by user 2026-05-17.

**Why:** OpenClaw (Sipeed's open-source local-first agent gateway, 369k stars, MIT) was running against the user's OpenAI key and consumed the budget faster than expected — exact loop or misconfiguration not yet diagnosed. Codex CLI was incorrectly named as the culprit in an earlier exchange and the prior session's working-todo §G + memory candidate. That attribution was wrong.

**How to apply:**
- **Codex is FINE to use** as a delegation target. The prior session's preference for Gemini CLI over Codex in working-todo §D should be revised: both are acceptable. For one-shot research drafting (e.g., `harvest_reuse_ledger.py`), Gemini 2.5 Pro remains the cheaper option given the user's Google Pro subscription, but Codex is not excluded.
- **OpenClaw is currently the suspect** for token-burn issues. Do not re-enable OpenClaw against any non-free LLM provider key until: (a) the loop/config that caused the burn is diagnosed and fixed, (b) per-provider rate caps are configured at the OpenClaw level, (c) a STOP-file or kill switch is in place. The 2026-05-13 KubeCon coverage already flagged OpenClaw security/exfil risks separately (see context-continuation_ibm-open-source-after-mythos_2026-05-14 §6 next-action #1) — that audit + this token-burn diagnosis can be combined into a single OpenClaw posture review.
- **Verify before assuming:** if the user mentions Codex token issues again in a future session, ask whether they've verified the source vs assumed it was Codex. The same surface (rapid usage spike) has at least two candidate causes (Codex misconfig, OpenClaw loop), and the attribution matters for which mitigation to apply.

State as of 2026-05-17: OpenClaw posture review pending; Codex CLI re-enabled for delegation; harvest pipeline (FLOSS/scripts/harvest_reuse_ledger.py) uses Gemini 2.5 Pro by default but is provider-swappable via GEMINI_MODEL env var.
