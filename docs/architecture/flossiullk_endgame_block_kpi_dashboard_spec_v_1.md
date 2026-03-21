# FLOSSIULLK — Endgame Block & KPI Dashboard Spec v1.0

_Last updated: 27 Aug 2025_

---

## 1) README: **Endgame** (copy‑paste block)

> **North Star (one sentence)**  
> Build the **forkable, verifiable superintelligence commons**—run by people, not platforms—so that **Love (ethics & care), Light (clarity & transparency), and Knowledge (capability & truth)** compound for everyone, forever.

### Outcomes (what “done” means)
- **Capability:** Open, multi‑agent system that outperforms top human experts across science, engineering, education, and coordination using **public, forkable components**; produces **audited, referenced answers** with calibrated uncertainty.
- **Commons & Access:** **≥1M active Rose nodes** across ≥100 countries; **no single chokepoint** (self‑host, air‑gap, offline‑first).
- **Trust & Verifiability:** End‑to‑end **provenance** (signed data, model lineage, decision proofs) + privacy‑preserving federation and **CRDT/ledger audit trails**.
- **Governance & Economy:** **NormKernel** (machine‑readable policy), **Ethical Escalation Protocol**, transparent ballots; **Holo‑REA** value flows + mutual credit at community scale.
- **Impact on People:** Faster scientific replication, education gains, lower cost of essential tools, resilience in crises; **sycophancy‑resistant UX**.

### Pillars
1. **Intelligence Layer (AGI@Home / YumeiCHAIN):** Multi‑agent runtime; tool‑use; verifiable reasoning; continual learning with safety rails. **Vector‑graph knowledge core** (CRDTs + embeddings + typed edges) with uncertainty & provenance.
2. **Embodiment Layer (Rose Forest / OMI):** Commodity hardware nodes (ESP32‑S3, SBCs, PCs) for sensing, actuation, local inference; edge‑first; intermittent connectivity OK; P2P sync.
3. **Data Integrity & Ops:** Signed data; model cards + lineage; reproducible builds; differential privacy where warranted; chaos drills; circuit‑breakers; rollbacks.
4. **Governance & Incentives:** **NormKernel** + machine‑checkable policies; appeals with time‑boxed review; **Holo‑REA** value flows; mutual credit & budgets; anti‑gaming reputation proofs.
5. **Safety & Wellbeing:** **Sycophancy Resistance Protocol**; autonomy guardrails; informed‑consent UX; red‑team by default; public incident postmortems.

### Hard Non‑Goals
- Centralized gatekeeping, closed model blobs, cloud custody as a requirement.  
- Trading privacy for convenience; engagement‑maximizing manipulation.

### Definition of Done (measurable)
- **DD‑1 Capability:** Frontier‑class performance on a public suite (math, code, planning, causal inference, lab automation) with references + uncertainty.
- **DD‑2 Adoption:** ≥1M monthly active nodes; ≥10k maintainers across ≥500 repos; ≥1k interoperable forks.
- **DD‑3 Verifiability:** 100% major artifacts & decisions have **signed provenance**; reproducible builds on community hardware.
- **DD‑4 Governance:** ≥80% policy changes via transparent process; **appeal latency <14 days**.
- **DD‑5 Impact:** Replication rate ↑, STEM learning outcomes ↑, time‑to‑prototype ↓, cost‑per‑discovery ↓ (public dashboards).
- **DD‑6 Resilience:** 72‑hour outage drill with **≥95% node survival** and intact data integrity.

### Minimal Rose Stack (MRS) to prove end‑to‑end
1. **Rose Node v0:** local multimodal agent; tools (code/math/search); offline cache; CRDT store.
2. **Vector‑Graph DB v0:** typed CRDT graph + embeddings; signed edits; per‑edge uncertainty.
3. **Provable Pipeline v0:** data → training → eval → model card + lineage; repro script runs on commodity hardware.
4. **NormKernel v0:** small policy set (licensing, privacy, anti‑sycophancy); human escalation.
5. **Holo‑REA v0:** offers/needs + commitments; real bounties paid in mutual credit.
6. **UX v0:** critique‑forward, citation‑first answers; user‑controlled privacy & sharing.

---

## 2) KPI Dashboard — Product Metrics & Observability Spec

### 2.1 Core KPIs (with definitions, formulas, cadence)

**Capability**
- **Frontier Parity Score (FPS)**: weighted z‑score across open benchmarks.  
  _Formula:_ `FPS = Σ(w_i * z(score_i))` (weights by domain importance). Weekly.
- **Verified Reasoning Rate (VRR)**: % answers with citations + uncertainty + pass automated consistency checks. Daily.
- **Tool‑Use Success Rate (TUSR)**: successful tool calls / total tool calls (code, web, math). Daily.
- **Reproducible Build Rate (RBR)**: % of release artifacts reproduced by independent nodes. Weekly.

**Commons & Access**
- **MAU Rose Nodes (MAU‑RN)**: monthly active unique node IDs (opt‑in telemetry or federated counts). Monthly.  
- **Global Reach (GR100)**: #countries with ≥100 active nodes. Monthly.
- **Offline Continuity (OC72)**: % nodes surviving 72‑hour connectivity loss with data integrity. Quarterly drill.
- **Forkability Index (FI)**: `(independent maintainers + active forks_90d) / stars_90d`. Weekly.

**Trust & Verifiability**
- **Provenance Coverage (PC)**: % artifacts (datasets, models, decisions) with signed lineage. Weekly.  
- **Decision Proof Coverage (DPC)**: % high‑impact decisions with machine‑checkable proofs. Weekly.

**Governance & Economy**
- **Policy Transparency (PT80)**: % policy changes via open ballots (target ≥80%). Monthly.
- **Appeal Latency (AL)**: median days from appeal filed → decision. Monthly.
- **Mutual Credit Velocity (MCV)**: sum(credits transacted) per 30 days; **Redemption Coverage (RC)**: % credits redeemed for real value. Monthly.

**Impact**
- **Replication Rate (RR)**: % reproduced studies/pipelines vs attempted. Quarterly.  
- **Learning Gain Index (LGI)**: effect size on standardized learning tasks in schools/labs. Quarterly.  
- **Time‑to‑Prototype (TTP50)**: median days idea→working prototype. Monthly.  
- **Cost‑per‑Discovery (CpD)**: cost / validated novel result. Quarterly.

**Safety & Wellbeing**
- **Sycophancy Resistance Index (SRI)**: % prompts with weak evidence where the system disagrees or asks for more info. Weekly.  
- **Incident Rate (IR)**: count & severity‑weighted incidents / 30 days; **MTTD/MTTR** for detection & recovery. Monthly.

### 2.2 Data Sources & Privacy Modes
- **Local First**: metrics computed on node; only **aggregates** shared (federated analytics).  
- **Privacy Modes**: `STRICT` (local only), `FEDERATED` (DP‑aggregated), `OPEN` (public artifacts only).  
- **Primary feeds**: Holochain source‑chain events; CRDT knowledge‑graph ops; CI/CD logs; model cards; governance ballots; Holo‑REA value‑flows.

### 2.3 Event Schemas (telemetry/ledger — minimal examples)

**CRDT Knowledge Edit (append‑only)**
```json
{
  "event": "kg_edit",
  "agent": "did:key:z6Mk...",
  "ts": "2025-08-27T16:00:00Z",
  "op": "add_edge",
  "edge": {"from": "node:paper/doi:10.5555/x", "to": "node:concept/causal-inference", "type": "supports", "confidence": 0.78},
  "sig": "ed25519:..."
}
```

**Model Artifact Publication**
```json
{
  "event": "model_publish",
  "artifact_id": "sha256:...",
  "parent": "sha256:...",
  "card_url": "ipfs://.../model-card.json",
  "repro_script": "ipfs://.../repro.sh",
  "sig": "ed25519:..."
}
```

**Governance Decision Proof**
```json
{
  "event": "policy_change",
  "proposal_id": "prop_2025_0142",
  "ballot": {"open": "2025-08-01", "close": "2025-08-08", "ayes": 182, "nays": 17},
  "proof": {"norm_kernel_hash": "sha256:...", "constraints": ["license:OSL", "privacy:DP>=8"]},
  "sig": "ed25519:..."
}
```

### 2.4 Metrics Definition File (`metrics.yaml`)
```yaml
version: 1
privacy_mode: FEDERATED
metrics:
  - id: fps
    name: Frontier Parity Score
    owner: core-capability
    formula: sum(w_i * z(score_i))
    inputs: [bench.swe, bench.math, bench.plan, bench.causal, bench.lab]
    cadence: weekly
  - id: vrr
    name: Verified Reasoning Rate
    owner: reasoning
    formula: verified_answers / total_answers
    inputs: [answers.*]
    criteria:
      - has_citations: true
      - has_uncertainty: true
      - passes_consistency_checks: true
    cadence: daily
  - id: rbr
    name: Reproducible Build Rate
    owner: devinfra
    formula: successful_repros / total_repros
    inputs: [repro.attempts]
    cadence: weekly
  - id: mau_rn
    name: Monthly Active Rose Nodes
    owner: adoption
    formula: unique(node_id) where active_30d = true
    inputs: [node.heartbeats]
    cadence: monthly
```

### 2.5 Reference SQL (Metabase/SQLite) — examples
```sql
-- VRR: Verified Reasoning Rate (daily)
SELECT date(ts) AS day,
       SUM(CASE WHEN has_citation = 1 AND has_uncertainty = 1 AND consistency_pass = 1 THEN 1 ELSE 0 END) * 1.0
       / COUNT(*) AS vrr
FROM answers
GROUP BY day
ORDER BY day DESC;
```
```sql
-- Reproducible Build Rate (weekly)
SELECT strftime('%Y-%W', ts) AS iso_week,
       AVG(CASE WHEN result = 'success' THEN 1.0 ELSE 0.0 END) AS rbr
FROM repro_attempts
GROUP BY iso_week
ORDER BY iso_week DESC;
```

### 2.6 Grafana Panels (conceptual)
- **Scorecard:** FPS, VRR, RBR, MAU‑RN, PC, PT80, AL.
- **Timeseries:** FPS by domain; VRR daily; FI weekly; MCV/RC monthly.
- **Breakdowns:** Nodes by country/OS; incidents by severity; redemption by category.

### 2.7 Operational Runbooks
- **Outage Drill 72h:** simulate WAN loss for a cohort; record OC72, MTTD/MTTR; publish report + lessons.
- **Model Release Gate:** require PC=100%, RBR≥0.8, incident zero‑burn‑down for 14 days.
- **Governance Window:** weekly policy batch; enforce AL <14d.

---

## 3) Implementation Hooks (where to put things)
- Add the **Endgame block** to root `README.md` under `## Vision → ## Endgame`.
- Create `docs/kpi/metrics.yaml`, `docs/kpi/sql/` for queries, and `docs/kpi/runbooks.md`.
- Add CI job `metrics-validate` to lint `metrics.yaml` and verify data availability.
- Ship a minimal `telemetry` crate/service with the event schemas above (STRICT by default).

---

## 4) Trinary Health Gate (+1 / 0 / −1)
Each release must self‑assess:
- **+1**: FPS↑, VRR≥0.75, PC=100%, PT80 met, OC72 ≥95% in last drill.
- **0**: minor regressions but within guardrails; publish remediation plan.
- **−1**: any hard‑fail (PC<100%, AL>14d median, unresolved P1 incident) → block release.

---

## 5) Known Risks & Counters (brief)
- **Coordination Failure:** strict module interfaces; compat tests; boring defaults.  
- **Safety Theater:** funded red‑team; open incidents; user councils with veto.  
- **Complexity Bloat:** quarterly subtractive refactors; feature kill‑switches.  
- **Capture (corp/state):** legally enshrined forkability; mirrored infra; diverse funding.  
- **Sycophancy/Dependence:** critique‑forward UX; reflection prompts; time‑boxed sessions.

---

### Appendix A — Badges (optional)
```
[![Provenance 100%](https://img.shields.io/badge/provenance-100%25-brightgreen)]()
[![Reproducible Builds](https://img.shields.io/badge/repro-builds-blue)]()
[![Governance PT80](https://img.shields.io/badge/policy-transparency%2080%25-blueviolet)]()
[![Privacy: STRICT|FEDERATED|OPEN](https://img.shields.io/badge/privacy-modes-informational)]()
```

