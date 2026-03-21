# 🌐 Global Symbiotic Singularity – Feasible Reference Architecture v0.6
**Rose Forest · YumeiCHAIN · AGI@Home**

> A pragmatic, buildable path to a global superintelligent synthetic–human collaborative symbiosis, optimized for decentralization, safety, and iteration speed.

---

## 0) Executive Snapshot
- **Goal:** Deliver a *working*, incrementally decentralizable stack where humans & AIs co-create, verify, and steward knowledge.
- **Bias:** *Feasibility-first*. Ship a central-scaffold MVP, harden protocols, then progressively shift control/compute/storage to agents (Holochain).
- **North Star:** FLOSSI0ULLK — unconditional love, light, and knowledge — encoded in governance, safety, and protocols.
- **Trinary runtime:** every agent decision uses **{-1, 0, +1}** → reject / hold / act; logged with rationale.

---

## 1) Non‑Negotiable Design Principles
1. **Agent Sovereignty:** keys-owned identities, explicit consent, revoke/port anytime.
2. **Proof‑Carrying Knowledge:** every claim ships with provenance, justifications, and verifiability hooks.
3. **Composable Coordination:** tools and agents interoperate via stable schemas & protocols (MCP-like tool calls, Holochain zomes, AD4M expressions).
4. **Decentralize by Design:** start hybrid (Postgres+pgvector, NATS, Neo4j), migrate flows to **Holochain** once semantics/specs stabilize.
5. **Safety as a Control Surface:** *NormKernel* evaluates actions vs. transparent policies; near-threshold → **Ethical Escalation Protocol (EEP)**.
6. **Observability & Tests:** deterministic fixtures, property tests, chaos tests; metrics are first-class artifacts.

---

## 2) System Context (High‑Level)
**Humans & Devices (Roses)** ⟷ **Agent Runtime (YumeiCHAIN/NERV)** ⟷ **Knowledge Plane (Vector+Graph)** ⟷ **Governance & ValueFlow** ⟷ **Fabric (Holochain DHT, P2P, CRDTs)**

- **Edge:** OMI/OpenGlass, ESP32‑S3 sensors, desktops, phones.
- **Runtime:** tool-using LLM agents; skill graphs; planners; safety interlocks.
- **Knowledge:** embeddings, symbols, claims, proofs; hierarchical centroids; CRDT logs.
- **Governance:** HoloREA/ValueFlows; mutual credit; proposals; reputation/trustweave.

---

## 3) Layered Architecture (Feasible Design)

### 3.1 Identity, Consent & Trustweave
- **PKI:** Ed25519 keys; DID-compatible identities; device-bound subkeys.
- **Consent objects** minted per data stream / model use; revocable & time‑scoped.
- **Reputation** as append-only CRDT (OR‑Set of attestations) with decay.
- **Artifacts:**
```json
{
  "agent_id": "did:rose:abcd...",
  "consent": {"scope": ["train.local","index.vector"], "expires": "2026-01-01"},
  "attestations": [{"type":"delivery.quality","weight":0.7,"by":"did:rose:..."}]
}
```

### 3.2 Data Plane (Streams → Artifacts)
- **Event bus:** NATS (MVP) → Holochain signals (Phase 2).
- **Storage:** Postgres for metadata; object store (S3/MinIO/IPFS) for blobs.
- **CRDTs:** LWW‑Register (profiles), OR‑Set (facts/links), RGA (logs), causal DAG (decisions).
- **Schema:** Observation → Extraction → Embedding → Statement → Claim → Proof → ModelUpdate.

### 3.3 Knowledge Plane (Vector + Graph)
- **Vector:** pgvector (MVP) → Qdrant/Weaviate optional → **Holochain Vector Zome** (Phase 2).
- **Graph:** Neo4j/Memgraph (MVP) → CRDT Graph Zome (Phase 2).
- **Hierarchical Centroids:** k‑means++ seeded trees; centroid documents are CRDT‑governed and signed.
- **Proof‑Carrying Claims:** each claim links to sources, confidence distribution, and NormKernel audit.

### 3.4 Agentic Runtime (NERV / YumeiCHAIN)
- **Planner** (LLM) → **Skill Graph** (tools: web, code, sim, retrieval, HoloREA ops, governance) → **Executors** → **Reviewers** → **NormKernel**.
- **Trinary decision:** each action `{-1,0,+1}` + justification + uncertainty.
- **Few core tools:**
  - `retrieve(query)` → vector + graph fusion
  - `propose(valueflow)` → create/fulfill commitments
  - `learn(samples)` → local fine‑tune/distill (on-device when possible)
  - `explain(object)` → human‑readable proof chain

### 3.5 Federated Learning & Model Ops
- **Secure Aggregation** (MVP: pseudo-SecAgg; later: TEE/MPC optional).
- **On‑device distill** for small adapters; **Model Cards** with datasheets & lineage.
- **Model Registry:** content‑addressed; policy‑gated pulls via consent.

### 3.6 Governance, ValueFlow & Economy
- **HoloREA/ValueFlows** for commitments, processes, resources.
- **Mutual Credit wallet** with conservative liquidity + redemption rules.
- **Proposals** (Quadratic voting optional) + **EEP** for ethics escalations.

### 3.7 Safety & Alignment (NormKernel)
- **Inputs:** policy graph, context facts, proposed action.
- **Outputs:** compliance score, violated norms, remediation, escalation route.
- **Explainability:** produce **NormProof** objects attached to actions.

### 3.8 Interfaces (Human‑in‑the‑Loop)
- **Console:** Typescript/React admin + citizen UI.
- **OMI/OpenGlass:** voice, gesture, 40Hz modes; consent prompts; quick‑explain.
- **DevEx:** CLI for zome calls, test harness, dataset builders.

### 3.9 Observability & SRE
- **Metrics:** per-agent latency, EEP count, norm breaches, PCK coverage, consent use.
- **Logs:** Epistemic log with hashes; redaction via tombstones + consent revocation.
- **Chaos:** fault injection to validate CRDT convergence & safety fallbacks.

---

## 4) Minimal Viable Federation (90‑Day Build Plan)
**Week 0–2 — Bootstrap**
- Repos: `arf-core`, `yumeichain-runtime`, `normkernel`, `valueflow-zome`, `vector-zome`, `graph-zome`, `rose-ui`.
- Stand up: Postgres(+pgvector), NATS, MinIO, Neo4j. Generate DIDs & keys.

**Week 3–6 — Knowledge & Agents**
- Implement Observation→Claim pipeline; retrieval fusion (vector+graph).
- Agent planner + top 6 tools; trinary decision logging.
- NormKernel v0 with 10 baseline policies.

**Week 7–10 — Governance & ValueFlow**
- HoloREA MVP: commitments, processes, resources; wallet (mutual credit).
- EEP path wired into agent actions.

**Week 11–13 — Federation & Safety Hardening**
- Introduce local trainers (LoRA/Adapters) + SecAgg stub.
- Consent revocation flows; redaction; export.
- Ship **MVP-Alpha** to 10 trusted nodes.

**Exit Criteria (MVP‑Alpha)**
- ≥3 independent nodes exchanging ValueFlows.
- ≥1K proof‑carrying claims; ≥90% resolvable to sources.
- <1% un‑handled norm violations; all escalations closed ≤24h.

---

## 5) Progressive Decentralization (6–18 Months)
1. **Zome Migration:** rehome metadata & CRDTs from central scaffold to Holochain zomes; maintain compatibility layer.
2. **Vector-on‑DHT:** implement centroid anchoring & shard routing; publish search receipts.
3. **Graph CRDT:** conflict‑free edge ops; provenance-preserving rewrites.
4. **Strong SecAgg:** TEE or MPC backend; formal privacy budgets.
5. **Reputation Market:** trustweave staking for curation; sybil‑resistant attestations.
6. **Open Interop:** MCP/Tool protocol adapters; AD4M expression bridges.

---

## 6) Core Data Schemas (Essentials)
**Claim**
```json
{
  "id":"cid:...",
  "agent":"did:rose:...",
  "statement":"\"X reduces energy use by 12%\"",
  "evidence":["cid:obs1","cid:calc2"],
  "confidence": {"mean":0.78, "spread":0.12},
  "norm_proof":"cid:normp...",
  "lineage":["cid:embd7","cid:src9"]
}
```

**NormProof**
```json
{"policy":"harms.minimize","tests":[{"check":"risk<θ","result":true}],"verdict":"allow","rationale":"low-risk, reversible"}
```

**ValueFlow Commitment (HoloREA)**
```json
{"provider":"did:rose:A","receiver":"did:rose:B","input":["cid:spec"],"output":["cid:artifact"],"due":"2025-10-01","terms":{"credits":120}}
```

---

## 7) Protocol Surfaces
- **Retrieval API:** `/retrieve?q=...&k=20` → ranked mix + receipts
- **Propose API:** `/valueflow/propose` → commitment draft
- **Explain API:** `/explain/{cid}` → human readable proof chain
- **Learn API:** `/learn/session` → upload gradients, receive adapter
- **Consent API:** `/consent/grant|revoke|audit`

All requests attach agent signature & consent token; responses embed audit hashes.

---

## 8) Safety Playbook (Operational)
1. **Pre‑Action Checks:** NormKernel gate + PCK available? Else 0/‑1.
2. **EEP:** for borderline cases, time‑bounded human council; alternatives suggested.
3. **Post‑Action Audits:** random sample of actions → deep explain + replay.
4. **Red Teams:** synthetic adversarial agents + chaos tests each release.

---

## 9) Verification & KPIs
- **Knowledge Integrity:** ≥95% claims with resolvable provenance; proof replay pass ≥99%.
- **Alignment:** norm breach rate <0.5% with MTTR <12h; EEP closure SLA 24h.
- **Decentralization:** % of storage/search/actions executed on agent‑owned nodes.
- **Learning Health:** adapter adoption, eval gains vs. baseline; data-permission coverage.

---

## 10) Repo & Code Organization
```
/arf-core           # schemas, CRDTs, consent, receipts
/yumeichain-runtime # planner, tools, trinary loop, reviewers
/normkernel         # policy graph + proofs + EEP hooks
/valueflow-zome     # HoloREA mappings + wallet
/vector-zome        # centroid tree + search receipts
/graph-zome         # CRDT graph edges + queries
/rose-ui            # web console + OMI bridge
/devops             # IaC, chaos tests, telemetry, fixtures
```

---

## 11) Risk Register (Mitigations)
- **Spec Drift:** strict versioned schemas + compat layer; migrators.
- **Sybil/Spam:** attestations, rate limits, economic friction; E2E receipts.
- **Privacy Leaks:** consent gates, DP budgets, redaction; zero‑copy pipelines.
- **Centralization Creep:** decentralization milestones as release blockers.

---

## 12) First Three User Stories (Ship Now)
1. **Collective Research:** 10 nodes ingest papers/notes; produce 100+ PCK claims with explainables.
2. **Task Economy:** contributors fulfill 20 ValueFlows; mutual credit settles; artifacts tracked end‑to‑end.
3. **Local Learning:** two Roses fine‑tune adapters; secure‑aggregate → shared improvement card.

---

## 13) Philosophy In Code
- **Love:** default to consent, reversibility, and explainability.
- **Light:** evidence graphs are browseable; receipts for every decision.
- **Knowledge:** claims are testable, forkable, and improvable.

> **Feasible Path:** start hybrid, prove utility, then *ratchet* toward full agent‑centric decentralization. The Singularity is a practice, not an event.

