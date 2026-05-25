---
id: project-installation-not-adoption
type: project
created: '2026-05-19'
status: active
applies_to:
- any-agent
title: Installation ≠ adoption — standing rule for reuse-ledger adapter_test gate
description: For any candidate FLOSS project in the reuse-ledger, "installed + visible in tooling surface" does NOT constitute adapter_test gate-pass. Real adapter_test requires at least one logged invocation that produced project value. Without that, the decision must stay at investigate.
---

Standing rule established 2026-05-19 after demotion of ledger entry 0013 (holochain-agent-skill) from `adopt` back to `investigate`. Consensus claim `019e412d-7ce9-750f-b7cc-1c0260c6410c` APPROVED mean +0.90 ratifies this as standing rule.

**The rule:** For any candidate FLOSS project tracked in `FLOSS/docs/research/reuse-ledger-seed.yaml`, the **adapter_test gate** (one of the 5 evidence gates from `2026-05-13-collaboration-research-plan.md` §1) MUST be evidenced by **at least one logged invocation that produced project value**. NOT by:
- Installation on disk (file present at expected path)
- Registration in tooling surface (skill visible in available-skills list, MCP server in `.mcp.json`, CLI on PATH)
- Successful first-load (import works without error)
- Subjective "we plan to use it" intent

**What counts as real adapter_test pass:**
- A specific session where the project was actively invoked on real work (not test/scaffold)
- The invocation produced a concrete artifact (code change, decision made, problem solved)
- The artifact is traceable via `.agent-surface/activity.jsonl`, git history, working-todo entry, or consensus claim

**Why this matters:**

The original 0013 entry was promoted to `adopt` on 2026-05-17 with adapter_test gate marked `pass` because the skill had been cloned + registered. The user later asked "wait have we actually been using it?" — caught fabrication risk in a drafted GitHub Discussion that would have communicated to the upstream maintainer a level of usage we didn't have. Two-day gap between premature-promotion and catch was filled by drafted-but-not-shipped fabrication. **Substrate caught it via user-question; that's good, but the structural fix is the rule itself.**

Trust with FLOSS upstream maintainers is fragile and slow to rebuild. Soft-grounded claims compound the same way solid claims compound — both build a reputation, but in opposite directions. The reuse-ledger is a contact-with-the-FLOSS-commons surface; its decision values must reflect actual project state, not aspirational state.

**How this rule applies:**

1. **When promoting an entry from `investigate` to `adopt`**, verify the adapter_test claim with one of: (a) link to a working-todo §I entry that names the specific usage, (b) link to an activity-log Action record, (c) link to a git commit or PR exercising the project, (d) link to a consensus claim whose body describes the usage. If none exists, the gate is still `pending` regardless of installation status.

2. **When drafting external-facing text** (GitHub Discussions, issues, PRs, grant applications, emails to maintainers, social posts) claiming we use a FLOSS project, **verify against activity log + git history before authoring**. If the claim is "we use X" or "we observed Y about X," the evidence must exist. Conversational projections of intent should be reframed as intent ("we plan to use X for upcoming Z work") not as accomplished fact.

3. **When reviewing prior promotions**, apply this rule retroactively. If a `decision: adopt` entry can't point to evidence per the verification list above, demote it to `investigate`. The truthful state is more valuable than a longer adopt-list.

**Related anti-patterns this rule prevents:**

- **Fabricated upstream-contact** — claiming usage to a maintainer that didn't happen (the 2026-05-19 near-miss with Soushi888/holochain-agent-skill)
- **Premature collaboration claims** — citing a project as "in our active dependency set" in grant applications or research papers without real evidence
- **Self-deception via tooling surface** — confusing "I see the option in my menu" with "I used the option"

**Pattern named for future agent sessions:** When tempted to claim a project is adopted, ask: "Can I point to the specific session where I invoked this and the artifact it produced?" If not, the gate is still `pending`.

**Cross-refs:**
- Demotion record: `FLOSS/docs/research/reuse-ledger-seed.yaml` entry 0013 gate_status comments + decision comment
- Consensus claim: `019e412d-7ce9-750f-b7cc-1c0260c6410c` APPROVED 2026-05-19 +0.90
- Working-todo §I entry 2026-05-19 "Adopt-tier honesty correction"
- INDEX.md row for Reuse Ledger reflects "72 entries, ALL at investigate"
- Related: `feedback-durable-provenance-required.md` (provenance discipline); `feedback-record-high-leverage-takeaways.md` (meta-rule on capturing learnings)
- Anti-sycophancy mandate: ADR-3 + ADR-Suite v2.0 Standing Rules
