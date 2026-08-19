# ADR-16 — Omnigent as Execution/Governance Surface; Gateway + Holochain as Validation Substrate

```yaml
adr: 16
title: "Omnigent (Youmeiagent fork) as execution/governance surface; MCP as the seam"
status: "Proposed"
date: "2026-06-17"
supersedes: []
relates_to: ["ADR-8 (Radicle dev substrate)", "ADR-10 (MCP orchestrator / analog vote model)", "METAHARNESS_OPERATING_MODEL"]
decision: "+1 adopt — scoped to execution + governance; 0 hold on anything touching validation; -1 reject merging into the truth layer"
truth_status:
  upstream_capability: "Verified (read README, dir tree, 10 commits on the fork 2026-06-17)"
  fork_state: "Verified — kalisam/Youmeiagent is a vanilla mirror of omnigent-ai/omnigent; all recent commits are upstream authors via web-flow; README still self-identifies as Omnigent; no FLOSSI0ULLK customization landed"
  integration_seam: "Specified — MCP-tool seam to metacoordinator_mcp is designed here, not yet built or tested"
  fit_for_validation: "Blocked — Omnigent has no symbolic validator; must not be treated as a truth substrate"
```

## Context

`kalisam/Youmeiagent` is a fork of [`omnigent-ai/omnigent`](https://github.com/omnigent-ai/omnigent)
(Apache-2.0, alpha) — a **meta-harness** over Claude Code, Codex, Cursor, Pi, and
custom YAML agents. Verified on 2026-06-17, the fork is a clean upstream mirror (no
local divergence yet). Its capabilities overlap substantially with surfaces we have
specified but only partly built:

- **Polly** — multi-agent orchestrator: delegates to coding sub-agents in parallel git
  worktrees, routes each diff to a reviewer **from a different vendor than authored it**.
  This is our METAHARNESS execution+review composition and the ≥3-provider / ≥4-family
  diversity policy, already implemented.
- **Debby** — two-headed Claude+GPT with `/debate`: a miniature of the analog-vote
  multi-model deliberation.
- **Policies** — approval gates, spend caps, per-tool limits, stacked server/agent/session.
  The governance layer we have **not** built.

## Decision

Adopt Omnigent as the **execution and governance surface**. Keep the local consensus
gateway (`packages/metacoordinator_mcp`) + source chain + (eventually) Holochain
integrity zomes as the **validation substrate**. Wire them through **MCP**: Omnigent
agents already speak MCP tools, so they call the gateway as a tool — Omnigent runs the
agents and enforces governance; the gateway/Holochain remains the Claim sink and the
only thing that establishes truth.

This preserves the prime directive: **logic validates, neural assists.** Omnigent's
"consensus" is cross-vendor *social review* (a different model eyeballs the diff) — a
heuristic, not a validator that cannot be bypassed. Treating it as if it covered
Layers 0–3 would invert the directive.

### Scope boundary (the load-bearing line)
- **+1 adopt:** Layer 4 (agent coordination) execution, Layer 4.6 (harness composition),
  and the governance/policy layer.
- **0 hold:** anything that reads or writes the source chain — only through the gateway's
  Claim/Vote/provenance contract.
- **−1 reject:** Omnigent making or recording truth decisions; the validator stays symbolic.

## Consequences

**Positive:** large execution-surface saving (Polly/Debby/policies exist and are
maintained upstream); a real governance layer we lacked; multi-device/collaboration for
free.

**Costs / failure modes (named):**
- **Alpha + fast drift.** Upstream landed 10+ commits on 2026-06-17 alone. Mitigation:
  keep our additions as **thin overlays** — YAML agents, policy configs, one MCP tool
  pointing at the gateway — never in-tree patches to omnigent core. In-tree divergence on
  a fast fork = merge pain and is the doc/code-explosion failure mode in another guise.
- **Capability conflation.** Risk that "we have a consensus tool now" quietly demotes the
  symbolic validator. Mitigation: this ADR's scope boundary; review at promotion time.
- **Provenance.** Source-authority for "what Omnigent does" is the repo, re-verified, not
  this ADR's prose, which will go stale as upstream moves.

**Licensing:** Apache-2.0, FLOSS-clean and compatible with project posture; `NOTICE`
present — preserve attribution if the fork is renamed past cosmetic.

## Next actions
1. Run `examples/debby` and `examples/polly` against own keys to validate the
   deliberation/review loop before committing architecture.
2. Prototype the MCP seam: register `metacoordinator_mcp` as an Omnigent tool; have a
   Polly review emit a Claim+Vote to the source chain. This is the one build that proves
   the boundary holds.
3. Author one thin overlay agent (YAML) that uses the gateway; do not patch core.

## Open
- Promotion of this ADR from Proposed → Accepted pending the §2 seam prototype.
- INDEX.md not yet updated (advisory-only; no auto-promotion into canon per doc-discipline).
