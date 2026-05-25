---
name: recent-open-distributed-intelligence-research
description: Use when the user asks for recent, current, latest, or open-access research on distributed intelligence, agent-centric architectures, decentralized multi-agent systems, federated learning, distributed vector databases, agent interoperability protocols, or FLOSSI0ULLK-adjacent open knowledge commons. Always use this skill for "recent open distributed intelligence research" prompts, even if the user only names a seed report or asks for a quick update.
---

# Recent Open Distributed Intelligence Research

Use this skill to produce current, source-grounded research scans for work
adjacent to FLOSSI0ULLK's agent-centric, privacy-preserving, decentralized
knowledge commons architecture.

## Workflow

1. Establish the time window and evidence boundary.
   - Default to the last 2-3 years unless the user specifies another window.
   - Treat any repo-local seed report as a lead list, not current evidence.
   - Use live source lookup for current claims, versions, releases, and "latest"
     status.
2. Prioritize primary sources.
   - Papers: arXiv, OpenReview, conference pages, DOI/publisher pages.
   - Projects: official docs, GitHub/GitLab repositories, release notes.
   - Protocols: official specifications, standards pages, or maintainer docs.
3. Cover the core lanes.
   - Agent-centric substrates: Holochain, AD4M/ADAM, local-first/P2P runtimes.
   - Decentralized multi-agent coordination: peer-to-peer LLM agents,
     non-central orchestrators, emergent graph/topology methods, agent memory.
   - Privacy-preserving learning: federated, decentralized, differential
     privacy, secure aggregation, data-sovereignty systems.
   - Distributed retrieval and memory: federated RAG, distributed vector
     databases, knowledge graphs, semantic CRDTs.
   - Open training and inference infrastructure: distributed RL/training,
     permissionless compute, open model routing, verification protocols.
   - Agent interoperability: MCP, A2A, AGNTCY/ACP, NANDA, and adjacent open
     agent protocol work.
   - Human-AI collective intelligence: deliberation, evaluation commons,
     co-improvement, governance, and open knowledge commons.
4. Apply FLOSSI0ULLK relevance filters.
   - Mark whether each item supports symbolic-first validation, agent
     sovereignty, anti-enclosure, privacy, provenance, or multi-agent consensus.
   - Separate verified facts from architectural implications.
   - Do not upgrade FLOSSI0ULLK truth status from external research alone.
5. Report in a compact, actionable structure.

## Output Format

Use this structure unless the user requests another format:

```markdown
# Recent Open Distributed Intelligence Research

## Executive Summary

## High-Signal Findings

| Item | Source Type | Date | Openness | Why It Matters |
|---|---|---:|---|---|

## FLOSSI0ULLK Implications

## Watchlist / Verification Gaps

## Sources
```

## Source Quality Rules

- Include links for every source used.
- Prefer primary sources over commentary.
- Flag unverified or secondary-only claims explicitly.
- For fast-moving tools and protocols, include the date checked.
- Do not cite raw intake files as current evidence unless the answer is about
  historical intake provenance.

## Repo Seed

If useful, use this raw intake as a seed list only:

- `FLOSS/docs/research/intake_raw/2026-05-22-root/reports/Recent Open Distributed Intelligence Research.md`
