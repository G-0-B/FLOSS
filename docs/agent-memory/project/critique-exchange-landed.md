---
id: project-critique-exchange-landed
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_critique_exchange_landed.md
title: Multi-lens critique exchange landed as canon + Wave-3 backlog prioritized
legacy_description: External LLM 8-lens critique (33% verdict) → Claude rebuttal →
  critic recalibration to 55-60% → 3 consensus-gateway rounds (balanced APPROVED +0.683,
  diverse-max DEFERRED +0.466, discrimination round APPROVED +0.524 with substantive
  rationales). 6th blindspot consensus-named (Agent Lifecycle/Death/Decay) added as
  backlog item
origin_session_id: e871691c-2013-4bde-b604-e6c52730ed65
---

## Artifact

`FLOSS/docs/research/2026-05-13-multi-lens-critique-exchange.md` — 8-part doc preserving both critic rounds, both Claude rebuttals, three consensus-gateway validation passes, and the consolidated 19-item Wave-3 backlog with voter-counted prioritization.

## Consensus rounds

| Claim | Profile | Outcome | Mean | Variance | Notes |
|---|---|---|---|---|---|
| `019e2374` | balanced (3v) | APPROVED | +0.683 | 0.017 | Validated 55-60% recalibration + 18-item backlog + doc-budget call. groq-gpt-oss-20b at exactly +0.50 flagged "some risk remains" unspecified |
| `019e237c` | diverse-max (14v) | DEFERRED | +0.466 | 0.150 | groq-qwen3-32b -0.50 with rationale truncated at "(e..." — about to name a 6th blindspot |
| `019e2384` | diverse-max, max_tokens=4000 | APPROVED | +0.524 | 0.135 | Discrimination round with longer rationales — surfaced the 6th blindspot consensus + backlog priority |

## The 6th blindspot — consensus-named

**Agent lifecycle / death / decay.** Four voters independently named the same dimension using overlapping language ("agent death/decay," "agent lifecycle and decay," "temporal alignment of consensus," "asynchronous temporal coordination drift"). qwen3-32b's truncated "(e..." was almost certainly "epochs" or "expiry."

The gap: no explicit mechanisms for permanent voter loss, state migration, async coordination drift, staleness thresholds for replay attacks on votes, or adaptive quorum dynamics under temporal heterogeneity.

Added as backlog item #19 (ADR-AGENT-LIFECYCLE) in research doc §8.D.

## Backlog prioritization — voter-counted

| Rank | Item | Votes (of 13 working) |
|---|---|---|
| 🥇 | ADR-PHASE-0-SUBSTRATE-VIABILITY-TEST | 8 |
| 🥈 | ADR-THREAT-MODEL | 7 |
| 🥉 | LOAD-TEST-HARNESS | 6 |
| 4 | SORTITION-DESIGN | 5 |
| 5 | TRANSLATION-ENTROPY-MEASUREMENT | 3 |

**Not prioritized by any voter** (slip to Wave-4): hREA/UNYT wiring, validator-reward-model, pilot-holon-sprint, meta-kernel-CCES-v4.1, funding-model-sustainability, curation-transparency-audit, provenance-UX-layer, KERI-binding.

## Methodological lessons preserved

- **flowith-deepseek-chat -0.25** rejected the dual-question form ("ambiguous evaluation criteria") then answered both substantively. Form-dissent + substantive contribution = right voter behavior.
- **Future claims**: keep questions atomic where possible. If combining is necessary for token economy, label dimensions explicitly so voters can grade them separately.
- **max_tokens=4000** override via `voter_factory` kwarg was the path to retrieve full rationales. The MCP-launched gateway uses defaults (2000); direct-Python invocation with custom voter construction is the override pattern.
- **3 Flowith voters still error** (`flowith-claude-sonnet-4`, `flowith-gpt-4o`) — model-identifier catalog mismatch persists despite `data=` JSON fix from earlier session. `flowith-deepseek-chat` works.

## How to apply

- When working Wave-3, take items in voter-priority order unless overriding for specific reason
- ADR-PHASE-0-SUBSTRATE-VIABILITY-TEST is the next concrete unblock-anything-else action
- The Agent Lifecycle blindspot should land in any ADR or design that touches voter rosters, identity binding, or consensus timing
- For future discrimination rounds: atomic questions + max_tokens raise + voter_factory override
