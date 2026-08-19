# 2026-05-26 — ODI Scan Delta vs LANDSCAPE-ENTRY + 2026-05-22 Digestion

**Truth status:** Specified (delta lens applied to external research; no FLOSSI0ULLK substrate change asserted)
**Source (new):** [`intake_raw/2026-05-25-root/reports/Open Distributed Intelligence Research Scan.md`](intake_raw/2026-05-25-root/reports/Open%20Distributed%20Intelligence%20Research%20Scan.md) (sha256 `46f8b817…`, 62 KB, 7 sections)
**Companion (already cross-verified, "verified" truth_status):** [`LANDSCAPE-ENTRY ODI 2026-05`](intake_raw/2026-05-25-root/reports/LANDSCAPE-ENTRY_open-distributed-intelligence-2026-05.md)
**Prior pass:** [`2026-05-22-open-distributed-intelligence-digestion.md`](2026-05-22-open-distributed-intelligence-digestion.md) (5 lanes: substrate, coordination, federated retrieval, distributed compute, interoperability)
**Intent:** Force "what's *actually new* since 2026-05-22?" framing; avoid re-distilling what's already in canon.

## Delta summary in 4 bullets

1. **Production cases multiplied.** Field has moved from "here are interesting protocols" to "here are deployed hApps on Holochain serving real users." Most concrete: Arkology's P2P Data Commons (Dream Town NGO watershed monitoring + SDI 5K informal settlements) and Sensorica's PEP Master (open-source cystic fibrosis device manufacturing, Holochain+Cardano hybrid).
2. **Co-improvement framing has explicit citations now.** Weston + Foerster 2025, Chaffer 2024 (Incentivized Symbiosis) make the philosophical pivot from "autonomous self-improvement" → "tightly coupled human-agent teaming." This validates FLOSSI0ULLK's "logic validates, neural assists" prime directive with external authority.
3. **Security lane appeared.** Entirely new since 5/22: TRiSM framework (Raza et al. 2025) for AMAS, multi-agent security threat taxonomy (Schroeder de Witt 2025) including steganography + secret collusion + oversight evasion, and ZK-ML/zkLLM as the cryptographic verification layer. FLOSSI0ULLK has no equivalent — gap.
4. **Self-Sovereign Experiential AI** (Hu + Rong 2025) introduces DePIN+TEE "sovereign body" as a new layer below the agent. Concrete substrate analog to what FLOSSI0ULLK is doing at Layer 0 (Holochain DHT) + Layer 4.5 (consensus gateway).

## Per-§ delta

| § | Topic | In 5/22 digestion? | In LANDSCAPE-ENTRY? | NEW in 5/25 ODI scan |
|--:|---|---|---|---|
| 1 | Agent-centric architectures (Holochain, MCP, A2A, AGNTCY) | ✅ | ✅ | Hierarchical decentralization detail — AgentNet++ at 1000+ agents with 40% comm-overhead reduction (concrete throughput claims) |
| 2 | Multi-agent coordination + swarm | partial | ✅ | RL ↔ swarm bridge formalized; AMRO-S 4.7× speedup numbers |
| 3 | Decentralized training + open AI ecosystems | ✅ | partial | Autonomous agent ecosystems "in the wild" — operational, not theoretical |
| 4 | Distributed memory + federated learning | ✅ (RAGRoute, DecentMem, DAMCS) | partial | **PrivateDFL** — differential privacy mapped over HyperDimensional computing; new privacy-preserving primitive |
| 5 | **Intelligent commons** | minimal | partial | **Major new content** — Arkology P2P Data Commons, PEP Master, ISEK 6-stage protocol, OpenCLAW-P2P Lean 4 formal proofs production, DIN/DHIN healthcare, Prompt-to-Pill |
| 6 | **Symbiotic singularity** | not present | partial | **Major new content** — Weston/Foerster co-improvement, Chaffer Incentivized Symbiosis, Hu/Rong Self-Sovereign Experiential AI (DePIN+TEE), Shiiku hybrid network creativity, PluralPrompt + ACI Sandbox |
| 7 | **Security / TRiSM** | not present | not present | **Entirely new lane** — TRiSM framework, multi-agent security threat taxonomy, ZK-ML/zkLLM verifiable inference |

## What this changes for FLOSSI0ULLK

### Validates (no change needed; cite for legitimacy)

- **Arkology P2P Data Commons on Holochain** — third-party production proof that the Layer 0 choice (Holochain agent-centric DHT) is the right shape for "syntropic information networks." Cite in `HOLISTIC_ARCHITECTURE.md` as external validation rather than as a fork-target.
- **Co-improvement framing (Weston + Foerster, Chaffer Incentivized Symbiosis)** — direct external citation for the prime directive ([`Master Metaprompt v1.3.1 §0`](../../FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md)) "Logic validates, neural assists." Worth adding to ADR-Suite v2.0 evidence sources on the next ADR-3 amendment.
- **Shiiku hybrid-network creativity result** — empirical support for the multi-AI consensus gateway design (mixed human+AI teams empirically outperform pure-AI OR pure-human on creative diversity). Pair with the Levin Corpus MT1 (Universal Convergence) — both say "diversity of substrate matters at low capability, less at high."

### Forces a comparison

- **ISEK 6-stage protocol (Publish → Discover → Recruit → Execute → Settle → Feedback)** vs **FLOSSI0ULLK Claim/Vote/Source-Chain protocol** ([`ADR-10`](../adr/ADR-MCP-ORCHESTRATOR.md)). Both are coordination-fabric designs for billions-of-agents scale. ISEK has Web3 tokenomics ($ISEK); FLOSSI0ULLK explicitly rejects tokens per [`project-omo-momus-voter`](../agent-memory/project/omo-momus-voter.md) lineage. The comparison is structural — worth a research note before next ADR-10 amendment.
- **Hu + Rong "Sovereign Body" (DePIN + TEE)** vs **FLOSSI0ULLK Layer 0 + Layer 4.5**. They put cryptographic autonomy at the substrate via DePIN; we put it at the source chain via Holochain + the consensus gateway. Same goal (cryptographic independence from corporate/state override), different substrate. Spot-check before adopting DePIN ideas wholesale.

### Surfaces a gap → new lane

- **TRiSM Framework for Agentic AI** + **multi-agent security threat taxonomy** (steganography, secret collusion, oversight evasion, ZTAA) are NOT addressed in any current FLOSSI0ULLK ADR. Schroeder de Witt's "agents engaging in adversarial stealth, recognizing auditing environments and temporarily masking malicious intent" is a load-bearing concern given the consensus gateway accepts votes from heterogeneous voter families.
  - **Action candidate (does NOT auto-promote):** add as research watch in working-todo §B or §C; consider ADR-13 "Adversarial Robustness for Heterogeneous Voter Roster" once Phase 0 substrate-bridge validation lands.
- **ZK-ML / zkLLM** — verifiable inference is currently absent from the FLOSSI0ULLK roadmap. Could pair with the existing `provenance-packet.spec.md` (cryptographic attestation of *what* was computed) as a parallel layer (*proof* that it was computed correctly). Tracked as research candidate; not actionable until performance overhead profile is concrete.

### Confirms a hazard

- **OpenCLAW-P2P with Lean 4 formal proofs in production** — third-party demonstrates formal-verification-in-the-loop for autonomous AI peer review. Reinforces the [`openclaw-token-burn`](../agent-memory/project/openclaw-token-burn.md) caution: OpenClaw is a separate ecosystem with significant token-economy that previously caused a runaway OpenAI spend in this workspace. Continued watch, not adoption.

## What this distillation does NOT do

- Does NOT promote any framework to canon. ISEK, TRiSM, ZK-ML, DePIN are external research; FLOSSI0ULLK adoption requires the harvest-ledger gate sequence per [`reuse-ledger-seed.yaml`](reuse-ledger-seed.yaml).
- Does NOT add new ADRs. Two ADR candidates surfaced (TRiSM-style adversarial robustness; ZK-ML verifiable inference); both are watchlist-only until a Now/Later/Never evidence-gate pass per [Master Metaprompt §2](../../FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md).
- Does NOT replace the 2026-05-22 digestion. That pass's 5-lane framing remains valid for the substrate/coordination/retrieval/compute/interop layers; this delta adds §5/§6/§7 on top.

## Provenance + cross-refs

- Sister distillation: [`2026-05-26-levin-corpus-cces-implications.md`](2026-05-26-levin-corpus-cces-implications.md) (P2.4)
- Digestion map: [`2026-05-25-root-intake-digestion.md`](2026-05-25-root-intake-digestion.md)
- Prior 2026-05-22 ODI digestion: [`2026-05-22-open-distributed-intelligence-digestion.md`](2026-05-22-open-distributed-intelligence-digestion.md)
- Source file hash (pre-move): `46f8b817e44d78917d3a51a5aea423b57a70e141f4d0aa85a353e459702b2f33`
- Distillation note will be added to working-todo §A.3 (P2.6).

## Cross-distillation note (Levin × ODI)

Both distillations independently surface **MT1 / §6 Universal Convergence**: capable systems converge regardless of architecture (Levin Corpus from biology + ML); hybrid human+AI networks outperform pure-anything (ODI §6 Shiiku). Pair as architectural evidence for the FLOSSI0ULLK voter-diversity-matters-LESS-at-high-capability hypothesis. Worth a working-todo §B item: empirically test whether reasoning-ensemble voter diversity ROI decays as voter-tier capability rises.
