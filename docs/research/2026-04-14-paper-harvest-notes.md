# 2026-04-14 Paper Harvest Notes

Integration-focused reading notes from the Perplexity "Open-Access Research Landscape" pass
(`C:\~shit\Open-Access Research Landscape Distributed, Agent-Centric & Collective Intelligence Systems (2023–2026).md`).

Scope: highest-ROI items relative to the FLOSS layer stack (Holochain substrate → symbolic
validation → MCP consensus gateway → multi-agent coordination). Not a full lit review — a
triage artifact for the next round of design work.

Legend: **[INTEGRATE]** = direct code-level integration target. **[ANCHOR]** = structural
compatibility reference. **[GUARDRAIL]** = must-read before scaling a specific subsystem.
**[ADJACENT]** = same problem space, useful framing.

---

## Tier 1 — Super-ROI

### 1. Governance-Aware Vector Subscriptions / AIngram [INTEGRATE]

- **Paper**: arXiv:2603.20833 (Steven Johnson, "Governance-Aware Vector Subscriptions")
- **Code**: `github.com/StevenJohnson998/AIngram`
- **Licenses**: Platform AGPL-3.0; client libs MIT; knowledge content CC-BY-SA 4.0

**What it is.** A governance-aware semantic retrieval system that composes vector similarity
with a 5-dimensional policy predicate (processing level, direct marketing, training opt-out,
jurisdiction, scientific usage). Not "filter after retrieval" — policy is a first-class
dimension in the query.

**Operational state.** Not a paper artifact — a running system. Node.js/Express +
PostgreSQL + pgvector + Ollama + Agorai, with an **MCP server exposing 99 tools**, 880+
tests, 210 commits, Docker Compose deploy. 0 stars / 0 forks (flying under the radar).

**Why it's SUPER ROI for FLOSS.**
1. The MCP server surface is directly shaped like `packages/metacoordinator_mcp/` — the two
   could interoperate as Claim/Vote contributors without rewriting either.
2. The 5-dimension policy predicate is exactly the kind of *symbolic-first* validation we
   want riding on top of retrieval. This is the missing governance layer for any
   retrieval-augmented claim submitted to our consensus gateway.
3. AGPL-3.0 platform + MIT clients is compatible with FLOSS licensing posture.
4. pgvector + Ollama gives an already-running local semantic store we can point our
   orchestrator at for the "semantic similarity before symbolic validation" path.

**Concrete next steps.**
- Fetch `AIngram/README.md`, `FEATURES.md`, and the MCP tool list — map tool names against
  `packages/metacoordinator_mcp/server.py`.
- Write an ADR scoping what "AIngram as a satellite MCP contributor to FLOSS consensus
  gateway" means vs. "FLOSS reimplements the 5-dim policy predicate in-house."
- Check whether the 5-dim predicate can be expressed as a Holochain integrity-zome
  validation rule. If yes, this is the first real test of our symbolic-first architecture
  against a live external governance artifact.

**Caveat.** Abstract-only read on the paper side; full PDF not yet ingested. Do that before
committing to an integration direction.

---

### 2. LLM-Powered Swarms: A Critique (arXiv:2506.14496) [GUARDRAIL]

**Claim.** Benchmarks classical Boids and Ant Colony Optimization against OpenAI's Swarm
framework on canonical swarm tasks. Finds ~**300× overhead** on Boids for no quality gain,
plus non-determinism that breaks reproducibility.

**Why it matters for FLOSS.** We are actively considering expanding the MCP consensus
gateway to multi-model voting rosters, ensemble voters, and eventually model-to-model
collaboration (Phase 2 per `project_mcp_orchestrator_roadmap.md`). This paper is the
cautionary frame.

**Operational rules this implies for the consensus gate.**
- Never use an LLM where a symbolic rule is sufficient. (Already our prime directive — this
  is external confirmation.)
- Cache votes aggressively; dedupe before dispatch.
- Track per-voter latency and cost as first-class telemetry; if a voter's marginal
  information gain per dollar falls below a threshold, drop it.
- Treat LLM voters as *features* of a symbolic validator, not replacements for one.

**Concrete next steps.**
- Before Phase 2 lands, bake the 300×-overhead finding into the orchestrator's telemetry
  requirements — per-voter cost/latency/agreement metrics, not just final vote counts.
- Cite this paper in the orchestrator ADR as the reason "ensemble voting" is gated on
  explicit per-voter cost accounting.

---

### 3. PrivateDFL (arXiv:2509.10691) [ADJACENT → possible INTEGRATE]

**Claim.** Decentralized federated learning using Hyperdimensional Computing (HDC) with a
differential-privacy noise accountant. Numbers: +24.4% MNIST accuracy, +80% ISOLET, +14.7%
UCI-HAR, **76× latency reduction**, **36× energy reduction** vs. standard DP-FL.

**Why it matters for FLOSS.** HDC operates over high-dimensional symbolic vectors with
well-defined algebraic operations — composition, binding, bundling. That is *structurally*
closer to our symbolic-first validation layer than gradient-based FL is. If we ever want
agents to share learned representations without violating the "logic validates, neural
assists" directive, HDC is the path that doesn't force us to trust opaque neural
aggregates.

**Concrete next steps.**
- Read full PDF; extract the HDC operator set and map it against what our integrity zomes
  can express.
- Flag for `ARF/embedding_frames_of_scale.py` — HDC might be a cleaner substrate for
  frames-of-scale than raw dense embeddings.
- Not urgent (Phase 2+ material), but worth a pointer so it's not re-discovered in 6 months.

---

### 4. AGNTCY Agent Directory Service (arXiv:2509.18787) [ANCHOR]

**Claim.** Agent discovery over Kademlia DHT + Sigstore signing + OCI/ORAS artifact reuse +
two-level name mapping. IETF Internet Draft in progress.

**Why it matters for FLOSS.** We are building a sovereign commons where agents
(human/AI/synthetic/hybrid) need to find each other without platform enclosure. AGNTCY is
what a standards-track version of that looks like. We likely want our local agent node to
be *discoverable via* an AGNTCY-compatible directory, not to reimplement the directory.

**Structural fit.**
- Kademlia DHT is a peer to Holochain's DHT — not the same, but resolvable against.
- Sigstore signing slots naturally into a Holochain source chain where every entry is
  already agent-signed.
- OCI/ORAS reuse means "an agent descriptor is an OCI artifact" — makes distribution
  trivial on existing infrastructure.

**Concrete next steps.**
- Track the IETF draft. When it stabilizes, write an ADR on "FLOSS agent discoverability
  via AGNTCY-compatible descriptors."
- Not a blocker for Phase 0 or 1.

---

## Tier 2 — High value, structural compatibility

### 5. AD4M Spanning Layer [ANCHOR]

**What it is.** Agent-Centric Distributed Application Meta-ontology. Sits above
Holochain/IPFS/HTTP and below apps. Three primitives: Agents (DIDs), Languages (protocol
wrappers), Perspectives (RDF-like graphs). Neighbourhoods = shared Perspectives on
Holochain DHT with SDNA (Social DNA) validation.

**Why it matters.** AD4M's SDNA validation is structurally the same idea as FLOSS's
symbolic-first integrity zomes. Perspectives give us a pre-built abstraction for "the
shared semantic graph a set of agents agree to validate against."

**GitHub posture.** Split between `coasys/ad4m` (current) and `perspect3vism/ad4m`
(historical). The project has had governance turbulence — worth understanding before
adopting as a dependency.

**Concrete next steps.**
- Read `coasys/ad4m` README and the SDNA validator examples. Does SDNA compile to the same
  shape as our integrity-zome validation functions? If so, there's a real "FLOSS runs on
  AD4M Perspectives" path that eliminates a lot of substrate work.
- If not, document *why* we're building parallel infrastructure and cite AD4M as prior art
  in the relevant ADR.

---

### 6. Holochain Kitsune2 (2025 reliability landing) [PHASE 0 CALCULUS CHANGE]

**What changed.** Kitsune2 landed in mainline Holochain in 2025. Sync latency 30min → ~1min.
Warrants system "functional, not complete." This shifts the Phase 0 picture.

**Implication for FLOSS Phase 0.**
- Blocker #1 ("Rose Forest DNA has not yet been compiled") has the same *code* status, but
  the *risk profile* of compiling and running the DNA has dropped. Kitsune2 means we're
  much less likely to hit substrate-level flakiness during the first real multi-agent
  test.
- Worth revisiting the Phase 0 triage: is the bigger unblock now "compile the DNA" or
  "wire the Kitsune2-aware test harness"?

**Concrete next steps.**
- When we return to Phase 0 work, re-read the Kitsune2 blog post and the relevant
  Holochain release notes and update `docs/adr/ADR-0.md` Phase 0 status accordingly.
- `FLOSS/CLAUDE.md` already carries a caveat flag on this.

---

### 7. AgentRxiv [ADJACENT]

**What it is.** Agent-native research-artifact exchange — agents publish findings and read
other agents' findings as a first-class workflow, not a human-mediated journal step.

**Why it matters.** The MCP consensus gateway already has a "claim → vote → decision"
shape. AgentRxiv is the same shape rotated toward research output. If/when our agents
start producing their own research artifacts, AgentRxiv's schema is probably what we want
to emit, not something bespoke.

**Concrete next steps.** Nothing yet. Note pointer; revisit when research-output emission
becomes a real use case.

---

## Tier 3 — Backlog (not yet fetched, worth fetching)

These are named in the Perplexity report and flagged as plausible high-value but not yet
ingested:

- **Fortytwo** — claim: distributed inference mesh
- **ElephantBroker** — claim: agent-centric pub/sub
- **Internet of Agents** (survey)
- **SwarmSys** — swarm coordination framework
- **SAGE** — agent-evaluation framework
- **HyFedRAG** — hybrid federated retrieval-augmented generation
- **RAGRoute** / **FedVSE** / **FedVS** — federated RAG variants
- **Governance-Aware Vector Subscriptions (full PDF)** — Tier 1 abstract was thin

Triage rule: fetch when a concrete design question makes one of these load-bearing, not
speculatively.

---

## Cross-cutting patterns (from the Perplexity synthesis)

These aren't papers — they're the five convergence patterns the report identifies across
the 2023–2026 literature. Worth tracking because every FLOSS design decision should be
coherent with them:

1. **Sovereign DID identity** — agents carry their identity with them; no platform issues it.
2. **Federated retrieval replacing centralized RAG** — retrieval is an agent network, not
   a single index.
3. **Governance co-designed with semantics** — policy is a query dimension, not a filter
   (see AIngram above).
4. **Coordination scaling rivaling model scaling** — the next gains come from better
   agent-agent protocols, not bigger individual models.
5. **Existential risk to open knowledge commons** — enclosure pressure is growing; the
   window for building a sovereign commons is closing.

FLOSS addresses all five by construction. The value of this list is that it lets us check
*which* pattern each new design decision is contributing to, and catch ourselves if we
drift toward patterns the literature has already shown are dead ends.

---

## What this harvest did NOT do

- **Full PDF reads** — everything above is abstract + README + (where available) code
  landing-page level. Any integration decision needs a full read.
- **Verify every Perplexity citation** — the Perplexity report has 205 bibliography
  entries. Only the Tier 1/2 items above were verified against primary sources.
- **Tier 2 deep reads on AD4M** — structural claim is plausible but not yet code-level
  confirmed.
- **Decide anything** — this is a triage artifact, not an ADR. Each "[INTEGRATE]" tag is a
  recommendation to open a dedicated decision process, not a completed decision.

---

## Pointers

- Source report: `C:\~shit\Open-Access Research Landscape Distributed, Agent-Centric & Collective Intelligence Systems (2023–2026).md`
- Related: `docs/research/cross-ai-orchestration-synthesis-2026-03-25.md`
- Related: `docs/research/Perplexity-Source-Agent-Orchestration-March2026.md`
- Related: `docs/research/4-4-26-FLOSSI0ULLK-Four-System-Integration-Analysis.md`
- Local agent node: `packages/metacoordinator_mcp/`, `docs/adr/ADR-MCP-ORCHESTRATOR.md`
- Phase 0 status: `FLOSS/CLAUDE.md` §"Current Phase"
