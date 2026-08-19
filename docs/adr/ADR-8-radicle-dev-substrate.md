# ADR-8: Radicle as the Canonical Dev-Plane Code Substrate

## Status
Accepted (2026-04-16)

## Context
FLOSSI0ULLK's core architectural commitments are agent sovereignty, provenance-first coordination, fork visibility, and the elimination of unnecessary central control points. The current code collaboration reality does not fully reflect those commitments. GitHub is still the practical forge for the repository, but GitHub is a centralized platform and therefore a mismatch for the project's long-term dev-plane posture.

Existing research already identified the better substrate. `docs/research/Automated-Agent-Orchestration-Report_v1.0.0.md` established the recommended composition pattern as:

- `Holochain` for identity, provenance, validation, and warrants
- `Radicle` for code hosting, patches, and review/social artifacts
- `IPFS/libp2p` for artifact distribution and event streams
- an orchestrator bounded by policy and CI

Recent synthesis work tightened the operational picture further:

- `deep-flossi0ullkreport.md` argues for layered architectures rather than a monolith
- `oh-my-meta.md` argues for multiple specialized meta-harnesses instead of one giant context-hungry agent loop
- the open-access survey (`Open-Access Research Landscape Distributed, Agent-Centric & Collective Intelligence Systems (2023–2026).md`) reinforces that sovereign identity, federated retrieval, and governance-aware semantics are converging production patterns

Meanwhile, the local agent node under `packages/` already implements an immediate bridge substrate:

- `packages/source_chain/` for file-based per-cell source chains
- `packages/metacoordinator_mcp/` for claim/vote/decision routing
- `.claude/settings.json` + `scripts/hook_post_write.py` for cheap automatic submission of substantive edits

That local bridge is not a replacement for the dev-plane forge. It is the provenance and coordination seam that must connect the forge to the runtime substrate.

## Decision
We adopt `Radicle` as the canonical dev-plane code substrate for FLOSSI0ULLK.

1. **Radicle is primary for code collaboration.**
   The normative dev-plane model is Radicle repos, Radicle patches, and Radicle collaborative objects (COBs) for issues/discussions/review artifacts.

2. **GitHub is a mirror, not the architectural center.**
   GitHub may continue to be used as a pragmatic mirror, distribution channel, or interoperability surface, but it is no longer the canonical source in architectural descriptions.

3. **The local source chain remains the immediate coordination bridge.**
   The file-based cell source chain and MCP gateway remain the active Phase 0 implementation seam. Their job is to record claims, votes, decisions, and eventually provenance links to Radicle artifacts until Holochain is the runtime substrate.

4. **The hard gate is the substrate handshake.**
   Before scaling autonomous merge behavior or complex orchestration, the project must prove a `Radicle -> provenance substrate` handshake:
   - create or update an ADR / patch as a Radicle artifact
   - emit a provenance entry referencing the Radicle object hash and delegate signatures
   - verify independently from another peer that the linkage is fetchable and valid

5. **High-risk merge autonomy will map to Radicle delegate policy.**
   The delegate and threshold semantics in Radicle become the policy gate for high-risk code updates on Plane A. Agents may propose patches and supporting evidence, but they do not bypass delegate threshold rules.

6. **The multi-harness operating model will treat Radicle artifacts as first-class context.**
   Execution, memory, retrieval, and optimization harnesses must all be able to ingest and reference Radicle patches/COBs as durable dev-plane evidence.

## Consequences

### Positive
- Aligns the dev-plane substrate with the project's anti-centralization commitments.
- Gives the architecture a legible split: `Radicle` for code-plane, `source_chain/MCP` for immediate provenance and coordination, `Holochain` for runtime truth.
- Makes fork visibility and delegate-threshold policy native rather than bolted on.
- Reduces future architectural drift by making the code substrate explicit in canonical docs instead of leaving it hidden in research notes.

### Negative
- Adds onboarding and tooling burden while the team still relies on GitHub and local git habits.
- Requires a bridge spike before it delivers concrete value to the existing code flow.
- Some surrounding tools and external contributors will continue to assume GitHub-first workflows, so a mirror strategy remains necessary in the near term.

### Risks
- Treating Radicle as canonical without proving the bridge could create policy theater.
- Over-rotating into forge migration before trace, memory, and routing discipline mature would slow velocity.
- If delegate threshold policy is too heavy for routine work, contributors will bypass it informally.

## Mitigations
- Keep GitHub as a mirror while the bridge is proven.
- Limit initial Radicle integration to the substrate handshake and patch/ADR provenance flow.
- Apply blast-radius discipline: routine work stays cheap, only higher-risk work touches stricter delegate policy.

## References
- `docs/research/Automated-Agent-Orchestration-Report_v1.0.0.md`
- `docs/architecture/HOLISTIC_ARCHITECTURE.md`
- `docs/superpowers/specs/2026-04-12-local-agent-node-design.md`
- `docs/superpowers/plans/2026-04-16-forward-momentum-radicle-meta-harnesses.md`
- `deep-flossi0ullkreport.md`
- `oh-my-meta.md`
