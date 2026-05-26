# Working Todo List — FLOSSI0ULLK

**Last refreshed:** 2026-05-23 (DecentMem/DAMCS memory-harness delta)
**Status:** Living working-memory artifact. Update on every significant work landing or completion.
**Purpose:** Single canonical surface for "what are we tracking right now?" — the answer to "do we have a working list of items we need to remember?"

This is NOT canon; it is operational working-memory. Items here get promoted to ADRs or research docs as they're worked. Items completed get pruned with a brief outcome marker.

---

## Section A — Immediate threads (this session or next)

### A.1 Heartbeat service via Servy

**Status:** ✅ SERVICE INSTALLED / ⚠️ PAUSED 2026-05-19 — service runs as `MSI\kalis`, but `.agent-surface/heartbeat/STOP` is intentionally present after the Groq token-burn diagnosis. Runtime budget now defaults routine polls to `balanced`, skips unchanged slates, caps daily consensus rounds at 40, and backpressures autonomous synthesis when the staging queue is full. See `FLOSS/docs/architecture/RUNTIME_SURFACES.md` and §I.

**Original setup recipe (preserved for reference):**
**Reason previous attempt died:** parent shell terminated on reboot for video-driver update.
**Servy config recommended** (Servy is the maintained NSSM replacement — correct choice):

| Field | Value |
|---|---|
| Service name | `flossi-heartbeat` |
| Display name | `FLOSSI0ULLK Heartbeat Loop` |
| Executable | `C:\Python313\python.exe` |
| Arguments | `C:\~shit\FLOSS\scripts\heartbeat.py --loop --interval-seconds 600` |
| Working directory | **`C:\~shit\`** (workspace root, NOT `scripts/`) |
| Run as | User account (kalis) — NOT LocalSystem/NetworkService |
| Startup type | Automatic (delayed start, ~30s after boot) |
| Restart on failure | Yes; delay 60s; max attempts 3 within 10 min |
| Stop signal | SIGTERM (the script's signal handler does graceful shutdown via the STOP file pattern) |
| Stop timeout | 30 seconds |

**Why workspace root cwd, not scripts/:** The script uses absolute `Path(__file__).resolve()` for its own paths, but it spawns subprocess work items with `cwd=str(WORKSPACE_ROOT)` explicitly. Consistency with that = clean. Running from `scripts/` would technically work but mixes signals.

**Why user account:** The heartbeat needs read access to `C:\~shit\FLOSS\.env` (API keys) and read/write to `~/.floss_agent/` (source chain storage). LocalSystem/NetworkService accounts can't reach user-home paths without privilege gymnastics.

**Halt protocol (already wired in script):** create file `C:\~shit\.agent-surface\heartbeat\STOP` and the loop exits within one tick (~10 minutes max). Delete the file to resume.

**Budget correction (2026-05-19):** do not resume blindly. `daily_state.json` hit `175/40` rounds and synthesis staging had 112 drafts. Confirm `FLOSS/docs/specs/heartbeat-runtime-budget.spec.md` still matches intended spend before deleting STOP.

### A.2 CFIS v0.3 canon promotion

**Status:** ✅ COMPLETED 2026-05-19 via consensus claim `019e3f84-bfd2-7d7e-a310-232ed8f52b39` (APPROVED mean +0.60). See §I for full landing details.

**Original promotion plan (preserved for reference):**
- ✅ Move `CFIS v0.3 — Pre-Pilot Hardened Specification.md` → `FLOSS/docs/architecture/CFIS_v0.3.md`
- ✅ Archive v0.2 + MDASH user-prompt source → `FLOSS/archive/intake_raw/`
- ✅ Add cross-reference to `HOLISTIC_ARCHITECTURE.md` §2.5 CCES section
- ⏸ Update Wave-3 backlog marking 3 items subsumed (deferred — next session)
- ✅ Submit consensus claim validating the canon-promotion move

### A.3 Workspace root intake digestion

**Status:** 2026-05-19 relocation pass complete; 2026-05-22 follow-on open
distributed intelligence report digested with partial live source verification.
49 loose workspace-root intake files plus the extracted `sitegeist/` directory
were moved into dated raw holding buckets. File hashes are recorded at
`.agent-surface/intake/root-intake-moves-2026-05-19.json`; directory tree hash at
`.agent-surface/intake/root-intake-directory-moves-2026-05-19.json`.

| Bucket | Path | Count | Next use |
|---|---:|---:|---|
| Architecture intake | `FLOSS/docs/architecture/FLOSSI0ULLK-Architecture-Spec-v0.1.md` | 1 | Historical evidence with supersession banners; not sole current canon |
| Reports | `FLOSS/docs/research/intake_raw/2026-05-19-root/reports/` | 35 | Distill into research/spec/ADR surfaces when load-bearing |
| Reference | `FLOSS/docs/research/intake_raw/2026-05-19-root/reference/` | 8 | Paper-style intake before use as evidence |
| Bundles | `FLOSS/docs/research/intake_raw/2026-05-19-root/bundles/` | 5 archives + 1 extracted dir | Isolated unpack-and-inspect pass only |

Digestion map: `FLOSS/docs/research/2026-05-19-root-intake-digestion.md`.

2026-05-22 addendum: `Recent Open Distributed Intelligence Research.md` and its
`pERFORM-...` prompt were moved to
`FLOSS/docs/research/intake_raw/2026-05-22-root/`; move log:
`.agent-surface/intake/root-intake-moves-2026-05-22.json`; digestion map:
`FLOSS/docs/research/2026-05-22-root-intake-digestion.md`; first distillation:
`FLOSS/docs/research/2026-05-22-open-distributed-intelligence-digestion.md`.

High-ROI next distillations: sycophancy/audit pair for anti-sycophancy +
ADR-12 hardening; two harness/memory HTML articles for context-daemon and
reasoning-ensemble pressure testing; agentic-security references; isolated
inspection of the code/archive bundles, including `sitegeist_extracted/`. From
the 2026-05-22 research digestion, the RAGRoute-style corpus routing thread
landed in `FLOSS/scripts/context_router.py`, and the DecentMem/DAMCS memory
harness comparison landed in
`FLOSS/docs/research/2026-05-23-decentmem-damcs-memory-harness-delta.md`.
Memory-harness result: next spec candidates are a memory-boundary contract and
selective-sharing gate; no adoption of DecentMem/DAMCS; `agentmemory` remains
Plane A recall/federation infrastructure, while repo canon/source-chain
validation remains the promotion path. For routing, focused tests and policy doc
landed with
`FLOSS/docs/research/2026-05-22-context-router-routing-policy.md`; next router
work should add retrieval-inside-corpus, not a global vector DB.
AD4M fit-check addendum landed in
`FLOSS/docs/research/2026-05-09-ad4m-coasys-audit-delta.md`: target AD4M
Language/Social-DNA integration, use sidecar only as the proof-of-fit spike,
and freeze new `source_chain/`, `packages/memory/`, identity, semantic graph, or
neighbourhood/runtime expansion until that spike records pass/fail evidence.

2026-05-26 addendum: 7 fresh root drops (Levin Corpus 48KB sha256 `766b9d98…`,
Open Distributed Intelligence Research Scan 62KB sha256 `46f8b817…`,
LANDSCAPE-ENTRY ODI 2026-05, info_firehose_ingestion, AD4M-hosting research,
Perplexity ODI-skill transcript, InfoQ Architecting Autonomy II 9MB PDF) moved
to `FLOSS/docs/research/intake_raw/2026-05-25-root/` (`reports/` + `reference/`
buckets). Move log: `.agent-surface/intake/root-intake-moves-2026-05-25.json`.
Digestion map: `FLOSS/docs/research/2026-05-25-root-intake-digestion.md`.
Two HIGH-leverage distillations landed:
- `FLOSS/docs/research/2026-05-26-levin-corpus-cces-implications.md` — maps each
  CCES layer (L0…L7) to Levin meta-themes + names three load-bearing structural
  isomorphisms (Holochain validation ≅ morphogenetic attractor; consensus
  gateway ≅ heterarchical cortical coordination; causal integration as the
  durable metric). Forwards 4 open research questions.
- `FLOSS/docs/research/2026-05-26-odi-scan-delta-vs-landscape.md` — delta lens
  against 2026-05-22 digestion + LANDSCAPE-ENTRY. NEW since 5/22: §5 production
  cases on Holochain (Arkology, Sensorica PEP Master, ISEK 6-stage protocol,
  OpenCLAW-P2P Lean 4 verified, DIN/DHIN healthcare); §6 co-improvement
  framing (Weston+Foerster, Chaffer Incentivized Symbiosis, Hu+Rong
  Self-Sovereign Experiential AI with DePIN+TEE); §7 NEW security lane
  (TRiSM, multi-agent threat taxonomy, ZK-ML/zkLLM verifiable inference) —
  FLOSSI0ULLK has no equivalent, candidate gap. 2 ADR candidates on watchlist
  (TRiSM adversarial robustness; ZK-ML verifiable inference) — both gated by
  Now/Later/Never evidence pass per Master Metaprompt §2.
Cross-distillation pattern: both surface "voter diversity matters LESS at high
capability" as testable hypothesis for reasoning-ensemble pilot data
(working-todo §A.6).
Root drops remaining (not moved): ADR-003-Metaprompt-Kernelization.md (handled
separately: replaced canonical ADR-3 with amended v1.1.0 + archived v1.0.0 in
commit `94dc3de`).

### A.4 SocratiCode install (UNBLOCKED — Docker running post-reboot)

**Status:** Docker server 29.4.3 is now running. SocratiCode install was blocked on Docker availability in prior session. Plugin marketplace already added via `claude plugin marketplace add giancarloerra/socraticode`.

Next: `npx -y socraticode` to install and start indexing. Expected indexing time ~2-5 min for the FLOSS codebase.

### A.6 Inline Reasoning Ensemble — CFIS-in-practice for every substantive prompt

**Status:** Router + synthesizer pre-pilot shipped 2026-05-18 under `FLOSS/packages/reasoning_ensemble/`. Architecture proposal lives at `FLOSS/docs/research/2026-05-17-inline-reasoning-ensemble.md`. Hardware confirmed (RTX 4090 Laptop 16GB). `phi4-mini:latest` is the v0.1 Router default; `gemma3:12b-it-qat` remains fallback via `FLOSS_ROUTER_MODEL`.

**Goal:** Extend the ADR-10 consensus gateway pattern from decision-grade (Claims, source-chain commits) to reasoning-grade (selective multi-model debate per substantive prompt). MDASH-validated approach. CFIS-aligned. User's explicit ask 2026-05-17.

**Selectivity discipline (non-negotiable):** NOT "every prompt." Three modes selected by local Router:
- Pass-through (single cheap call) — trivial lookups, file reads
- Single-strong (current default) — standard reasoning
- Ensemble (≥3 voters in parallel + Router synthesis) — substantive reasoning, decision boundary

**Next-action gates** (per proposal §9):
1. ✅ Confirm hardware (done 2026-05-17 — 4090 Laptop, 16GB VRAM, Ollama installed)
2. ✅ Router model selected/calibrated: `phi4-mini:latest` default; `mxbai-embed-large` embeddings available
3. ✅ Prototype `FLOSS/packages/reasoning_ensemble/router.py` — single-prompt → mode classifier
4. ✅ Partial: `FLOSS/packages/reasoning_ensemble/synthesizer.py` stages ensemble synthesis + emits global `Action`; MCP tool wrapper still TODO
5. ✅ Skill counterpart promoted through shared skill surface — canonical source is now `FLOSS/skill-corpus/reasoning-ensemble/SKILL.md`, materialized to Codex / Claude / Gemini / OpenCode
6. ✅ Activity logs exist: `.agent-surface/reasoning/activity.jsonl` plus global `.agent-surface/activity.jsonl`
7. 7-day pilot — log every Tier-4 divergence, measure course-correction rate
8. ADR-14 promotion decision based on pilot data

**Open questions** (carried from proposal §8):
- Router-as-hook vs Router-as-tool architectural shape (recommendation: tool first, hook later)
- How to wrap internal Claude chain-of-thought (answer: can't — only boundary-crossing calls)
- Voter-frame-mapping for CFIS — needs empirical calibration over weeks of pilot data
- Conductor-style learned topology planning is a promising adapter spike, but not a new authority layer. See `FLOSS/docs/research/2026-05-18-conductor-paper-metaharness-implications.md`; recommended next step is a typed `ConductorPlan` pilot over archived high-risk prompts before any training loop.

### A.7 Metaharness Unification — single Action schema, single activity log, shared Routing convention

**Status:** Sketch landed 2026-05-18 → `FLOSS/docs/research/2026-05-18-metaharness-unification.md`. Architectural reconciliation, NOT new construction. **Reframes user's "overarching metaharness overseer" ask as unification of existing harnesses via shared conventions.**

**The pattern named:** 8+ executable harnesses each invented with different staging dir / activity-log shape / LLM call path / provenance convention. The work is unification of the surrounding scaffolding, not the function of each.

**Three unification abstractions** (per the doc §3):
1. **Atomic interface:** shared `Action` schema — every agentic action emits one record
2. **Holistic surface:** single global `.agent-surface/activity.jsonl`
3. **Routing convention:** every LLM call routes through `router.classify()` first

**Next-action gates** (U-numbered, see doc §8):
1. ✅ U1 `activity_log/schema.py` + `append_action()` helper — DONE 2026-05-18 (`FLOSS/packages/activity_log/`)
2. ✅ U2 Wire global activity log into `synthesizer.py` and `router.py` — DONE 2026-05-18
3. ✅ U3 Wire global activity log into `heartbeat.py`, `harvest_reuse_ledger.py`, `poll_high_roi_actions.py`, `autonomous_synthesis_loop.py` — DONE 2026-05-18; focused tests cover all five tee points
4. ✅ U4 Build `FLOSS/scripts/review_queue.py` roll-up across staging dirs — DONE 2026-05-18; focused tests passing; live roll-up reports 178 queued items (66 harvest drafts + 112 synthesis drafts)
5. ✅ U5 Update `METAHARNESS_OPERATING_MODEL.md` with the unified conventions section — DONE 2026-05-18
6. ⬜ U6 7-day pilot + ADR-14/15 promotion decision

**Atomic Agents fit (2026-05-18 spot-check):** BrainBlend-AI/atomic-agents is the most directly relevant staged harvest candidate for this work-stream. Its typed `BaseIOSchema` + `AtomicAgent[In, Out]` contract maps cleanly onto FLOSSI0ULLK's `Action`, Claim, Vote, and router-decision shapes. Treat it as an adapter/tooling candidate for the atomic side of the metaharness, not as a replacement for ADR-10 consensus or the heartbeat composer.

### A.8 Review Queue — synthesis drafts + staged harvest candidates

**Status:** Active. `python FLOSS/scripts/review_queue.py` now provides the unified read-only roll-up. Latest local count 2026-05-18: 178 queued items = 66 harvest drafts + 112 synthesis drafts; 1 harvest draft already reviewed (`0016_brainblend_ai_atomic_agents`). User cursory inspection 2026-05-18: synthesis drafts look "pretty legit"; high-ROI poll also ranked "Review 111 synthesis drafts pending commit" #1 (mean +0.494). Treat the review queue as likely-valuable backlog, not disposable noise.

**Next actions:**
- Preview synthesis promotion with `python FLOSS/scripts/autonomous_synthesis_loop.py --commit --dry-run`
- Preview all staged review work with `python FLOSS/scripts/review_queue.py --limit 40`
- Sample-review representative drafts, then batch accept / revise / reject / archive
- Prioritize harvest draft `0016_brainblend_ai_atomic_agents_*` for metaharness relevance; promote selectively after renumbering and adapter-spike planning

### A.9 Cross-agent Status Drift — Phase 0 terminology reconciliation

**Status:** Active correction 2026-05-18. User flagged Codex drift: MVP Phase 0 Tryorama tests passed months ago. Confirmed by `MVP_PLAN.md` and `pprevious_working_task.md`. The stale surfaces were `FLOSS/CLAUDE.md`, workspace `CLAUDE.md`/`AGENTS.md`, `README.md`, and several architecture summaries.

**Resolved distinction:**
- **MVP Phase 0 / Rose Forest substrate viability:** ✅ complete — DNA compiles to WASM, hApp/Tryorama tests pass, ontology integrity unit tests pass.
- **Orchestration Phase 0 / substrate bridge validation:** ⚠️ still specified — publish/provenance/independent verify/query/fork-visible/no privileged verifier per `docs/specs/phase0-substrate-bridge.spec.md`.
- **ADR-2 evidence drift:** ⚠️ ADR-Suite v2.0 still carries the older "full round-trip unvalidated" note. Do not treat that stale note as current operational status; update ADR evidence formally before relying on ADR-2 as fully reconciled.

**Next actions:**
- Add `MVP_PLAN.md`, `SDD-Master-Spec-0.22.md`, `INSTRUCTIONS_FOR_CODE.md`, and `phase0-substrate-bridge.spec.md` to the shared context/agent surfaces so cheap reorientation loads the phase-state and discipline sources.
- Regenerate context, skill, and agent projections.
- Later: prepare a proper ADR-2 evidence-update patch rather than silently rewriting the consolidated ADR suite.

### A.5 External FLOSS Harvest — drive the reuse-ledger from inventory to gate-pass

**Status:** Activated 2026-05-16. Reuse-ledger expanded from 10 → 15 entries (entries 0011–0015 added: OpenHuman, agentmemory, holochain-agent-skill, delimit-mcp-server, mycelix). Entry 0013 is now `adopt` with 4/5 gates passed, so the anti-accumulation guard has one concrete gate-pass anchor. Wide harvest staging contains 66 drafts; promote selectively rather than expanding canon indiscriminately.

**Inventory state:**
- ~90 forks under `kalisam` GitHub (`gh repo list kalisam --fork --limit 100`), 2026-04 to 2026-05-16 vintage
- 15 of those are now ledger entries; ~80 are inventory-only
- High-signal staged candidate: `0016_brainblend_ai_atomic_agents_draft.yaml` (MIT, Python 3.12+, current upstream version 2.7.5, GitHub main at `f849087`, 5.9k stars). It is directly relevant to §A.7 metaharness unification because its schema-first agent contracts can prototype FLOSSI0ULLK Action/Claim/Vote adapters.
- Living artifact: `FLOSS/docs/research/reuse-ledger-seed.yaml` (relocated from workspace root 2026-05-16, v0.2-seed-expanded)
- Plan canon: `FLOSS/docs/research/2026-05-13-collaboration-research-plan.md` (relocated from workspace root 2026-05-16)

**Delegation pattern (per §D rule — Gemini CLI is the preferred delegate; Codex is currently flagged for token-burn, see §G):**
- One ledger entry per delegated subprocess invocation
- Structured YAML output matching the entry schema (license_status, gate_status, decision, notes, next_action)
- Append-only to the ledger; human steward gates promotion of any entry from `decision: investigate` → `decision: adopt`
- 5-gate evidence standard from plan §1 (license / adapter_test / provenance / rollback / contact) is non-negotiable

**Operational tool: `FLOSS/scripts/harvest_reuse_ledger.py`** (shipped 2026-05-17)
- Usage: `python FLOSS/scripts/harvest_reuse_ledger.py https://github.com/owner/repo`
- Auto-detects next available ledger id
- Drafts land in `.agent-surface/harvest/staging/<id>_<owner>_<repo>_draft.yaml` for human review
- Provenance JSON co-located; contains upstream metadata snapshot + invocation context
- `--dry-run` prints assembled prompt without burning Gemini quota (use for prompt-tuning)
- Free-tier gemini-2.5-flash, ~50-60s per fork. 50 forks = ~50 min wall-clock, $0 cost

**Next gate-passes by priority** (closing entries before adding more):

| Rank | Entry | Target gate | Action | Owner |
|---|---|---|---|---|
| 1 | 0013 holochain-agent-skill | license + adapter_test | Install in `.claude/skills/`, test against `ARF/dnas/rose_forest/` | Tony (highest leverage, lowest friction) |
| 2 | staged 0016 atomic-agents | adapter_test + provenance | Promote/renumber selectively, then spike a typed Claim/Vote or Action wrapper using `AtomicAgent[In, Out]` | Tony or Gemini CLI delegate |
| 3 | 0010 sentence-transformers | adapter_test + provenance | Already designated `proceed`; pilot per plan §5 | Tony |
| 4 | 0012 agentmemory | MCP tool call + contact | Root surface indexed, license/server health verified, MCP registered behind JanuScope; REST remember/search and REST cross-session recall passed. Next session must execute real MCP `memory_smart_search`, then file upstream contact. | Tony or next MCP-aware agent |
| 5 | 0011 OpenHuman | adapter/data-model check | License gate passed 2026-05-21; map Memory Tree + agentmemory fields to ConversationMemory + MultiScaleEmbedding and decide test depth | Tony |
| 6 | 0014 delimit-mcp-server | adapter_test (claim schema compare) | Diff against `packages/orchestrator/consensus_gate.py` wire format | Tony |
| 7 | 0015 mycelix | contact + governance compare | Read DNA arch, map to CFIS frames + CCES layers | Tony |

**Anti-pattern guard active** (from plan §9):
- "Architectural resonance ≠ working interoperability" — no ledger entry promoted to `adopt` based on alignment vibes alone
- "Vision accumulation" — do not add ledger entries faster than existing entries close gates
- "Treating philosophical alignment as integration proof" — same project, different worded reminder

**Kill criteria for the harvest task itself:**
- If after 4 weeks no ledger entry has passed ≥3 gates, the harvest is producing inventory not integration — re-scope before continuing
- If reuse-ledger.yaml grows past 25 entries without any reaching `decision: adopt`, freeze additions per the plan's anti-pattern §9.

---

## Section B — Voter-prioritized Wave-3 backlog

Per consensus discrimination round (claim `019e2384`, 2026-05-13):

| Rank | Item | Votes | CFIS subsumption | Action notes |
|---|---|---|---|---|
| 🥇 1 | ADR-PHASE-0-SUBSTRATE-VIABILITY-TEST | 8/13 | No | MVP Tryorama proof is done; remaining gate is substrate-bridge provenance + independent verification + ADR-2 evidence update |
| 🥈 2 | ADR-THREAT-MODEL | 7/13 | No | Mostly documentation; high tractability |
| 🥉 3 | LOAD-TEST-HARNESS | 6/13 | No | Scalability at 10M+ triples |
| 4 | SORTITION-DESIGN | 5/13 | No | Voter sampling beyond static 14-voter roster |
| 5 | TRANSLATION-ENTROPY-MEASUREMENT | 3/13 | **YES** (CFIS Phase 0 task 4) | Defer to CFIS pilot |
| 6 | ADR-AGENT-LIFECYCLE (newest #19) | n/a | No | Agent death/decay/permanent voter loss |
| — | ADR-PLURALISTIC-EPISTEMOLOGY (#10) | n/a | **YES** (CFIS Phase 0 task 1) | Defer to CFIS pilot |
| — | ADR-CONFLICT-RESOLUTION (#6) | n/a | **YES** (CFIS catuskoti + LSM-Override) | Defer to CFIS pilot |
| — | KERI-BINDING-INTEGRATION (#3) | n/a | No | Identity substrate |
| — | VALIDATOR-REWARD-MODEL (#9) | n/a | No | hREA + UNYT wiring |
| — | PILOT-HOLON-SPRINT (#8) | n/a | No | Per v4.0 §11 |
| — | KERI/hREA/UNYT/Neighbourhoods audit (#11) | n/a | No | Wave-4 |
| — | META-KERNEL-CCES-ALIGNMENT-v4.1 (#12) | n/a | No | v4.0 §21.4 divergences |
| — | FUNDING-MODEL-SUSTAINABILITY-ANALYSIS (#13) | n/a | No | Structural |
| — | ECON-MODEL-PROTOCOL-VS-ORG (#14) | n/a | No | Three-layer economic stratification |
| — | SORTITION-DESIGN (#16) | 5 (same as #4) | No | Duplicate? Audit |
| — | PROVENANCE-UX-LAYER (#17) | n/a | No | UX design |
| — | CURATION-TRANSPARENCY-AUDIT (#18) | n/a | No | AD4M Language trust paths |

**3 items are now subsumed by CFIS** — should be marked in `2026-05-13-multi-lens-critique-exchange.md` §5 as deferred-to-CFIS rather than active Wave-3.

---

## Section C — CFIS Phase 0 — 8-week parallel implementation

**The Phase 0 timeline IS the implementation surface for 3 subsumed Wave-3 items.** Tracking here as the operational thread.

| Week | Task | Owner | Critical? | Blocking issue |
|---|---|---|---|---|
| 1-2 | T1: Frame Registry hardening | Frame-community reps | **YES** (Gate input) | Requires `[auth:trained]` reps confirmed |
| 1-2 | T2: Independence matrix | CFIS participant | NO | None — computation |
| 1-4 | T3: Authority tier assignment | Frame communities | NO | Social process |
| 1-4 | T4: Divergence schema deployment (SDNA DivergenceShape SHACL) | Technical team | NO | Requires AD4M SDNA fluency |
| 3-6 | **T5: Frame recruitment** | Rose Forest governance | NO | **HIGHEST risk — social, not technical. Start NOW.** |
| 3-6 | T6: AI constraint deployment (LSM-Override) | Technical team | NO | Holochain integrity zome callback |
| 3-6 | T7: Test claim walkthrough | Cross-frame team | NO | Requires reps for each frame |
| 5-8 | T8: Pilot governance documentation | Governance committee | NO | Community ratification |

**Frame Sufficiency Gate** (Phase 0 → Phase 1 boundary):
- Requirement 1: ≥1 frame pair disagrees on ALL 5 CLC axes (provisional analysis says F1 vs F3 PASSES)
- Requirement 2: No CLC axis unanimously agreed (requires verification on observer_world + unit axes)

---

## Section D — Delegation-ready (not yet started)

| Thread | Description | Why delegated | Estimated cost |
|---|---|---|---|
| **A: Wave 2 ancestry sweep** | Sweep remaining 70+ forks via Gemini CLI subprocess; one fork at a time; structured YAML output; aggregate into Wave 2 delta doc | Per-fork pattern-extraction work; ~0 Opus tokens, free Gemini quota | ~5K Opus tokens for synthesis |

---

## Section E — Older open threads (lower priority, flagged for awareness)

| Thread | Status | Notes |
|---|---|---|
| ARF folder deep-dig | Not started | User flagged ARF has same doc-explosion pattern internally |
| Yumeichan consolidation | Not started | User mentioned 3 consolidation shape options (A/B/C) — open question |
| Universal-flourishing drops consolidation | Not started | n+1, n+3, substantiate, maximizing drops at root |
| Worktree quirky-mcnulty cleanup | Not started | `.claude/worktrees/quirky-mcnulty/` |
| Flowith catalog audit | Partial | `flowith-claude-sonnet-4`, `flowith-gpt-4o` voter wiring still erroring despite `data=` fix; `flowith-deepseek-chat` works |
| Consolidation pass for ~2yrs disparate research | Not started | Per `project_consolidation_pending.md` memory |
| PR #25 merge (ADR-5, ADR-6, consensus gate, ADR-0 propagation) | Open | Pre-FLOSSI_U-relocation context; needs re-plan per `META_COORDINATION_KERNEL_v4.0.md` §21 changes |
| ConversationMemory ↔ MultiScaleEmbedding API reconciliation | Partial fix landed (193729c); underlying API gap remains | Per Tuesday session_summary §B2 |
| Identity files SPOT-READ outcome | Not started | OpenClaw / OpenWork-Claw origin questions |

---

## Section F — Recent intake (transcripts updated)

User noted "extremely fab transcripts" recently saved to `_reference/transcripts/`. High-signal items by author/topic:
- Yann LeCun — "Mathematical Obstacles on the Way to Human-Level AI" + "Special Lecture on AI and World Models"
- Leonard Susskind — "Why Empty Space Is Not Empty" + "Why Nature Is Not Real"
- Chase Hughes — "Why You Can't Relax - Emotional DEBT"
- Emil Eifrem (Neo4j CEO) — "How to turn Documents into Knowledge Graphs in Modern AI"
- Prof Jiang Xueqin — "Why Grinding Hard Won't Make You Rich"
- Tom Scryleus — "You Don't Need a Job To Make Money"
- Skeptic — "Why the Same Childhood Doesn't Affect Everyone the Same Way"

These are intake for synthesis pass — not action items per se, but signal for thematic threads we're tracking.

---

## Section G — Heartbeat / consensus gateway health

| Item | Status |
|---|---|
| Heartbeat process | ✅ Active via Servy as `MSI\kalis`; latest resumption surface 2026-05-18 shows 25 ticks and 120/240 daily consensus rounds dispatched. |
| Docker daemon | ✅ Running (Server 29.4.3) — unblocks SocratiCode |
| Consensus gateway tests | ✅ 32/32 passing as of last verified state |
| MCP server: serena | Active (JanuScope-wrapped per `.mcp.json`) |
| MCP server: flossiullk-consensus | Active (JanuScope-wrapped) |
| JanuScope audit sinks | `.agent-surface/heartbeat/janus-{consensus,serena}-audit.jsonl` |
| 14-voter diverse-max roster | Verified working last session: 13/16 fire successfully (3 Flowith voters still erroring) |
| omo + omo-momus voters | Wired and approved as canon |

---

## Section H — Pruning protocol

When an item completes:
1. Remove from this doc
2. Add a brief outcome line to a new "Recently completed" section at the bottom
3. If the work produced a research doc / ADR / memory file, link it
4. Recently-completed section auto-purges after 30 days (becomes recoverable via git history)

When an item is reframed or merged:
- Mark with strikethrough + note where it moved
- Don't delete until 7 days later (recovery window)

---

## Section I — Recently completed (rolling 30-day window)

- **2026-05-25** Cross-harness AI roster + OpenWork update packet shipped — added `FLOSS/shared-ai-roster-surface.json` and `FLOSS/scripts/materialize_shared_ai_roster.py` to aggregate OpenWork/OpenCode provider imports, model lists, MCP servers, instruction files, agent surfaces, and shared memory targets into `.agent-surface/harness/ai-roster.json`, `.agent-surface/harness/AI_ROSTER.md`, and `.agent-surface/harness/HARNESS_UPDATE_PACKET.md`. Extended `materialize_shared_agent_surface.py` so the shared-surface generation now refreshes the roster and projects the OpenWork default agent instructions at `opworkers/.opencode/agents/openwork.md`. Durable memory entry: `project-cross-harness-ai-roster`. Boundary preserved: `agentmemory` REST health/search verified 2026-05-25, but MCP tool-use remains the remaining adapter gate; repo canon still wins and load-bearing System/Substrate handoffs still require provenance packet evidence.
- **2026-05-22** RAGRoute-style context-router prototype shipped — upgraded `FLOSS/scripts/context_router.py` from keyword+priority ranking to corpus-first routing with weighted `route_intents`, route labels, route policies, and intent evidence in markdown/JSON output. `FLOSS/shared-context-surface.json` v0.3.0 now labels canon, architecture, code, source-chain, agent-memory, serena-memory, research, reference, skills, and traces before retrieval. Policy doc: `FLOSS/docs/research/2026-05-22-context-router-routing-policy.md`. Focused tests: `FLOSS/scripts/tests/test_context_router.py` verifies source-chain intent beating generic canon priority, real lane selection for research/code/memory/reference, and rendered route rationale. Boundary preserved: no global vector DB, no embeddings, and no retrieval output becomes canon without normal validation.
- **2026-05-21** OpenHuman harvest gate update — corrected the workstream to local-first before new remote analysis. Prior state was already canonical as reuse-ledger entry 0011, not a fresh candidate: adapter-only, federate through `memory.backend = "agentmemory"`, and keep P5 routing concerns out of core adoption. GPL-3.0 license gate now marked pass for adapter/federation use under ADR-7 + GPLv3/AGPLv3 section-13 compatibility; next gate is data-model/adapter depth, not another license pass. Same pass repaired 57 malformed promoted-entry `candidate_project` lines in the ledger so YAML parsing works again.
- **2026-05-21** OpenHuman local install wired for FLOSSI0ULLK — configured user profile `6a08d8d252d6337c9871ac1d` to use `memory.backend = "agentmemory"` at `http://localhost:3111`, Memory Tree local Ollama embeddings via `mxbai-embed-large:latest` (1024 dims verified), local extraction/summarisation via `phi4-mini:latest` + `gemma3:12b-it-qat`, and four JanuScope-backed MCP client entries (`agentmemory`, `flossiullk-consensus`, `flossiullk-reasoning-ensemble`, `serena`). OpenHuman's local-AI bootstrap panel is intentionally disabled (`runtime_enabled = false`, `opt_in_confirmed = false`) because current upstream probes `POST /api/tags` and falsely marks this Ollama runner broken even though direct generation/embeddings work. This is config-level wiring only; do not mark entry 0011 adapter_test/adoption passed until a real OpenHuman memory store/recall smoke test succeeds.
- **2026-05-19** agentmemory REST adapter-test PASSED — server verified healthy at `localhost:3111` (uptime 3.6h, 257 iii functions registered, worker version 0.11.6, viewer 200 OK at `:3113`); MCP wiring already in place at root + FLOSS `.mcp.json` behind JanuScope lens (`.mcp/lenses/agentmemory.yaml` with audit sink + invariants subordinating agentmemory to repository canon). **REST round-trip closed the partial adapter_test gate**: `POST /agentmemory/remember` wrote substrate-migration memory id `mem_mpebqux9_d9ae5dbe18e4`; `POST /agentmemory/smart-search` for "holochain substrate migration HDI 0.7" recalled the same obsId on first query with BM25 score 0.016. **2026-05-20 Codex recheck:** the same REST smart-search recalled `mem_mpebqux9_d9ae5dbe18e4` again, so REST-level cross-session recall is now verified. **Reuse-ledger entry 0012 gate flip**: adapter_test partial → pass; decision still `investigate` pending (a) MCP tool round-trip via `memory_smart_search`, (b) contact gate via GH Discussion to rohitg00 acknowledging FLOSSI0ULLK use-case + JanuScope wrapping. Two gates pending = no ADOPT yet, but the protocol-level federation is live and high-signal substrate-migration evidence now lives in a queryable cross-model memory store. **Honest scope**: this is a *successful Plane A integration*, not a *canon shift* — canonical FLOSSI0ULLK memory remains repository-owned under `FLOSS/docs/agent-memory/` and materialized outward via `materialize_shared_agent_memory.py` to `~/.claude/projects/C---shit/memory/`. agentmemory adds a third memory surface (alongside repo canon + Claude MEMORY.md projection) optimized for semantic search / cross-tool federation. Standing rule (from lens): recalled memories from agentmemory are *evidence candidates*, promoted through normal markdown/spec/ADR/Claim path if load-bearing.
- **2026-05-19** Substrate migration holochain-0.4 → holochain-0.6 EXECUTED — user-explicit directive ("def worth it now rather than later we dont have substantial codebase yert so get to it") drove the substrate-line decision from pending pressure-surface to landed work in a single session. **Consensus claim `019e4220-d40c-7c41-b8d6-af8dc9304d58` System-class APPROVED mean +0.72 variance 0.024** (threshold 0.60 cleared by 0.12; cerebras +0.80, gpt-oss-20b +0.85 strongest yet on a migration, qwen3-32b +0.50 with positive technical merits despite future-dated-claim heuristic firing). Workspace pins now `hdi = "=0.7.1"` + `hdk = "=0.6.1"` + `holochain_serialized_bytes = "=0.0.57"`; `flake.nix` `holonix?ref=main-0.6`; new `ARF/.cargo/config.toml` with `rustflags = ['--cfg', 'getrandom_backend="wasm_js"']` for wasm32 (HDI 0.7 transitive getrandom 0.3.x requirement). Per-zome Cargo.toml: integrity pair gets direct `holochain_serialized_bytes` dep (HDI 0.7 macro requirement), all 4 active zomes get `[target.cfg(target_arch="wasm32").dependencies] getrandom = features=["wasm_js"]`. Source migrations: `agent_latest_pubkey → agent_initial_pubkey` (5 sites), `GetLinksInputBuilder::try_new(...).build() → LinkQuery::try_new(...)?` (4 sites), `get_links(input) → get_links(query, GetStrategy::default())` (4 sites). **Verification on Windows host**: cargo check both integrity zomes → clean; cargo check both coordinators → clean; `cargo test -p consent_integrity` → **10/10 pass on HDI 0.7.1** (same suite that passed on 0.5.1 — confirms zero entry-shape semantic drift); release WASM build all 4 zomes → 37.65s, 4 wasms produced (rose_forest_integrity 2.05 MB, consent_integrity 2.03 MB, rose_forest 3.47 MB, consent 3.29 MB). **Stale-artifact discipline**: 0.4-line `rose_forest.dna` and `rose_forest.happ` deleted (must re-pack in WSL on main-0.6 nix shell). Tryorama `@holochain/client ^0.18.0 → ^0.20.0` and `@holochain/tryorama ^0.17.0 → ^0.19.0` to track the 0.6 line. **Out-of-scope**: orphan zomes (hrea_*, identity_*, memory_coordinator, ontology_integrity) NOT migrated — they pin `hdk = "0.5"` / `hdi = "0.5"` directly but are not in workspace members and not in dna.yaml; they remain dev artifacts on the 0.4 line until they re-enter the active substrate. **Substrate-class ratification gates** unchanged by this migration (still pending: action-time enforcement, DID/header binding, cross-frame validation, counter-frame resolvability). Migration cost-benefit (qualitative): less than expected — most breaking changes are mechanical renames, the existing `op.flattened` dispatch already followed 0.6 conventions, only the entry-helper macro lookup + getrandom wasm flag required new infrastructure. Workspace now aligns with `holochain-agent-skill` canonical reference, closing the version-skew finding originally surfaced as Pitfall #1 in the 2026-05-19 full-force HDK session.
- **2026-05-19** Holochain runtime version-line skew tracked durably — user flagged that Codex's WSL pack/Tryorama success was real substrate work but "still using old version of hdi n stuff." Verified from disk: workspace pins `hdi = "=0.5.1"` / `hdk = "=0.4.1"`, `ARF/flake.lock` pins holonix `main-0.4` + holochain `0.4.4`. `holochain-agent-skill` canonical reference is `hdi=0.7.1` / `hdk=0.6.1` (holochain `0.6.x`, holonix `main-0.6`) per skill `Quick Reference`. Substrate is **two minor versions behind** what the skill teaches — same gap originally surfaced as Pitfall-finding #1 in 2026-05-19 full-force HDK session, unresolved across two subsequent Codex parallel runs (consent_coordinator + WSL pack/Tryorama). Migration cost is breaking-change work across all 8 existing zomes + the new `consent_*` pair: `delete_link(hash)` → `delete_link(hash, GetOptions::default())`, `GetLinksInputBuilder` → `LinkQuery::try_new()`, `op.to_type()` → `op.flattened::<EntryTypes, LinkTypes>()`, `GetStrategy::Local`/`Network` split, plus flake input ref `main-0.4` → `main-0.6` and holochain ref `0.4.4` → `0.6.x`. **Captured durably** at `FLOSS/docs/specs/consent-payload.spec.md` validation-status table with a new `Holochain runtime version line` row so the gap surfaces every time anyone reads that spec, **not just** in working-todo §I where it would scroll off. Flagged as **separate substrate-line decision pending pressure surface**, NOT a Module-class follow-up and NOT a blocker for the current Substrate-class ratification critical path (action-time gating + DID/header binding + cross-frame validation + counter-frame resolvability). Future option: substrate-line-decision Claim at System or Substrate blast radius asking voter pool whether the migration is worth the 8-zome rewrite cost, or whether 0.4 is acceptable for current substrate work given that 0.4 is still in active holonix maintenance. Decision NOT yet submitted; this is decision-pending surface, not decided work.
- **2026-05-19** Workspace root intake relocation pass — 49 loose root files plus the extracted `sitegeist/` directory moved out of the shared intake mouth into durable dated holding areas: architecture spec to `FLOSS/docs/architecture/FLOSSI0ULLK-Architecture-Spec-v0.1.md`, 35 reports to `FLOSS/docs/research/intake_raw/2026-05-19-root/reports/`, 8 PDFs/DOCX to `.../reference/`, 5 ZIP/TAR artifacts plus `sitegeist_extracted/` to `.../bundles/`. Move logs: `.agent-surface/intake/root-intake-moves-2026-05-19.json` and `.agent-surface/intake/root-intake-directory-moves-2026-05-19.json`. New digestion map: `FLOSS/docs/research/2026-05-19-root-intake-digestion.md`. Shared memory entry: `project-root-intake-2026-05-19`. This was relocation/provenance, not canon promotion; raw files still require distillation/spec/ADR/consensus before becoming load-bearing.
- **2026-05-19** WSL Tryorama pass — consensus closed — ran balanced voter round on Codex's status claim `019e41ef-d1ed-70b1-aeef-0c2fb5048300` covering the WSL/Nix `hc dna pack` + `hc app pack` + `npx vitest run consent_gate.test.ts` 2/2 pass. **APPROVED mean +0.60 variance 0.02** — same three voters as the implementation-slice round, same tight signal (cerebras +0.80, gpt-oss-20b +0.50, qwen3-32b +0.50). qwen3-32b specifically called out incremental progress with clear remaining-gates documentation, validating the spec-table honesty discipline. Module threshold 0.50 cleared. **Substrate gain summary across the two consensus rounds**: implementation slice landed (consent_integrity + consent_coordinator + DNA wiring + 10 cargo unit tests + 4 wiring tests + release WASMs) AND hApp packaging landed (rose_forest.dna 2.08 MB + rose_forest.happ 2.08 MB) AND Tryorama scenario passed (2/2 via vitest). Three Substrate-class ratification gates remain: action-time governed-pattern enforcement, DID ↔ action-header binding, cross-frame validation via `[auth:trained]` frame reps (CFIS Phase 0 §T5). Counter-frame resolvability also pending. Separately tracked: holochain-runtime version line (0.4 vs 0.6) — see entry above.
- **2026-05-19** Consent gate substrate slice — consensus closed + WSL Tryorama verified — ran balanced voter round on Codex's claim `019e41d3-0672-75a9-a266-f3b4f631aac5` (the Module-class status claim Codex left unvoted to conserve tokens after the heartbeat budget fix). **APPROVED mean +0.60 variance 0.02** — cerebras-llama3.1-8b +0.80 (thorough implementation, voter-round-skip noted as concern), groq-gpt-oss-20b +0.50 (clear concrete deliverables, no apparent conflicts), groq-qwen3-32b +0.50 (pragmatic scope to substrate slice, acknowledges pending Substrate-class ratification gates honestly). Module threshold 0.50 cleared. Low variance (0.02) signals tight inter-voter agreement on what was actually shipped — the spec/ADR honest-status updates ("⚠️ Partially verified" not "✅ Verified") were specifically validated. **Polycentric pattern loop closed**: user flagged ADR-12 §847 gap → Claude landed schema/stub/zome-skeleton → Codex executed substrate slice (consent_coordinator + DNA wiring + Tryorama scenario + 10 cargo unit tests + release WASMs + honest-status spec updates) → Claude voted via gateway → user reminded Codex that Holochain CLI lives in WSL → Codex packed and executed the consent hApp test in the WSL/Nix shell. Open boundaries preserved durably: action-time governed-pattern enforcement still pending; DID/header binding still pending; counter-frame resolvability still pending; Substrate-class ratification (0.85) still gated on those.
- **2026-05-19** ADR-12 Consent Gate substrate slice wired — continued Claude's schema/stub work with a focused implementation pass: `consent_integrity` now has Rust unit tests for deterministic ConsentPayload/ConsentDecision validation; `workdir/dna.yaml` packages `consent_integrity`; a separate `consent` coordinator zome exposes create/get/list calls and enforces `scope_granted ⊆ consent_scope`. The separate zome is intentional: linking both integrity crates into the existing `rose_forest` coordinator produced duplicate Holochain export symbols. Added static wiring tests and authored Tryorama coverage at `ARF/tests/tryorama/consent_gate.test.ts`; fixed the hApp path to `../../workdir/rose_forest.happ`. Verified locally: wiring tests `4 passed`, `cargo test -p consent_integrity` `10 passed`, `cargo check -p consent -p rose_forest --target wasm32-unknown-unknown`, release WASM build for all four zomes, WSL/Nix `hc dna pack` + `hc app pack`, and WSL/Nix `npx vitest run consent_gate.test.ts` `2 passed`. Source-chain status claims: implementation slice `019e41d3-0672-75a9-a266-f3b4f631aac5`; WSL Tryorama pass `019e41ef-d1ed-70b1-aeef-0c2fb5048300`. Boundary preserved: full Substrate-class ratification still waits on action-time gating, DID/header binding, counter-frame resolvability, and cross-frame validation.
- **2026-05-19** Operator primer + reasoning ensemble MCP registration shipped — added `FLOSS/docs/architecture/OPERATOR_PRIMER.md` as the human-first "what is this / how do I use it" guide covering current phase status, runtime planes, start-of-session flow, emergency controls, SDD discipline, and current best next moves. Wired it into `INDEX.md`, `FLOSS/shared-context-surface.json`, `FLOSS/shared-agent-surface.json`, `FLOSS/docs/architecture/RUNTIME_SURFACES.md`, generated `CONTEXT_L0`, `CONTEXT_POINTERS`, and Vibe startup. Resumed after Claude's SDD retrofit: all three reasoning ensemble specs (`router`, `synthesizer`, `mcp`) are present, and `flossiullk-reasoning-ensemble` is now registered in root `.mcp.json`, mirrored to `FLOSS/.mcp.json`, wrapped by `.mcp/lenses/flossiullk-reasoning-ensemble.yaml`, and projected to Gemini/OpenCode/Vibe configs with longer cold-start budget. Verification: shared-agent-surface tests `5 passed`, materializer `--check` OK, JSON validation OK, and `packages.reasoning_ensemble.mcp_server` imports with `route_prompt` + `deliberate` available. Boundary preserved: reasoning ensemble is Plane A reasoning-grade tooling; decision-grade Claims still go through `flossiullk-consensus`.
- **2026-05-19** Mistral Vibe alignment surface shipped — `Vibe.txt` showed Vibe still leaning toward stale Phase 0/Tryorama-style framing. Updated the canonical Vibe target in `FLOSS/shared-agent-surface.json`, extended `FLOSS/scripts/materialize_shared_agent_surface.py`, and added `scripts/tests/test_shared_agent_surface.py`. Generated outputs now include `.vibe/config.toml` with `default_agent = "flossi0ullk-align"`, `.vibe/agents/flossi0ullk-align.toml`, `.agent-surface/VIBE_STARTUP.md`, and `vibe-floss.ps1` startup-prompt injection for blank interactive sessions. The startup prompt directs Vibe through `CONTEXT_L0`, `RESUMPTION`, shared memory, runtime budget, substrate-bridge spec, and this working todo before proposing work. Also updated `FLOSS/docs/superpowers/plans/2026-04-16-external-adoption-and-shared-surface.md` and shared memory `project-vibe-alignment`. Verification: shared-agent-surface tests + memory + heartbeat tests `13 passed`; materializer `--check` all OK; `vibe-floss.ps1 --help` and `--version` both return cleanly.
- **2026-05-19** Heartbeat runtime budget correction shipped — user identified that heartbeat was burning Groq quota by running high-ROI polling with excessive diversity even when nothing changed. Diagnosis: `.agent-surface/heartbeat/daily_state.json` already showed `175/40` rounds for the day; old `heartbeat` voter alias resolved to `diverse-max`; `poll_high_roi_actions.py` defaulted hotter than routine should; `heartbeat.py` counted profile-qualified poll names as zero rounds; no slate-signature skip had actually been implemented; autonomous synthesis could still run Groq while 112 staged drafts were waiting. Fixes landed spec-first/TDD: `FLOSS/docs/specs/heartbeat-runtime-budget.{spec.md,schema.json}`, `FLOSS/scripts/tests/test_heartbeat_budget.py`, `heartbeat.py` daily cap + slate-signature + 72-tick wide-sweep + synthesis staging cap, `poll_high_roi_actions.py` default `balanced`, `voter_registry.json` alias `heartbeat -> balanced`, operator guide `FLOSS/docs/architecture/RUNTIME_SURFACES.md`, shared context/agent surfaces, and shared memory `project-heartbeat-running`. STOP remains intentionally present until human resumes.
- **2026-05-17** Heartbeat Servy fix VERIFIED working — service restart at 03:20 UTC ran first real tick at 03:21 UTC: `poll_high_roi_actions 95.14s rounds=+5` (was <1s pre-fix, meaning voters were silently failing inside). Subsequent ticks 03:34 (89.11s) and 03:46 (94.99s) confirm sustained real voter latency. The "today: 95 rounds" pre-fix was indeed fake — heartbeat is now generating real consensus traffic again.
- **2026-05-17** holochain-agent-skill INSTALLED — ledger entry 0013 promoted from `investigate` → `adopt` with 4/5 gates pass (license: Apache-2.0 verified, adapter_test: skill registered in Claude Code available-skills list, provenance: this todo + ledger update, rollback: trivial). Cloned upstream Soushi888/holochain-agent-skill into `C:/~shit/.claude/skills/holochain-agent-skill/`. Contact gate (file GH Discussion to introduce FLOSSI0ULLK use-case) deadline 2026-05-24. Directly serves Wave-3 priority #1 (Phase-0-Substrate-Viability-Test, 8/13 votes) — Tryorama work now has a structured-knowledge surface inside Claude Code.
- **2026-05-17** Model version correction caught by user — was using gemini-2.5-pro when 3.1 Pro has been GA since 2026-02-19. Verified working model ID on gemini-cli v0.38.2 is `gemini-3.1-pro-preview` (the GA name `gemini-3.1-pro` 404s — CLI predates rename). Script default upgraded to 3.1-pro-preview; env-var override for when CLI updates. The 8 existing 2.5-pro drafts in staging are sound (AIOS spot-check confirmed quality) — re-harvest with 3.1 is optional, not blocking.
- **2026-05-18** Metaharness Unification sketch landed — `FLOSS/docs/research/2026-05-18-metaharness-unification.md`. Reframes user's "overarching metaharness overseer" ask: **unification of existing 8 harnesses via shared conventions, NOT new orchestrator construction**. Three abstractions: (a) shared `Action` schema, (b) global `.agent-surface/activity.jsonl`, (c) every LLM call routes through Router first. 10-step refactor migration path; anti-vision-accumulation guards explicit. New §A.7 work-stream tracking 6 U-numbered next-actions. Companion ADR-14 candidate to the Inline Reasoning Ensemble proposal.
- **2026-05-19** Full-force HDK session — REAL adapter_test for holochain-agent-skill + ConsentPayload Rust integrity-zome landed. After demoting 0013 to investigate earlier in the session (anti-fabrication catch), invoked the holochain-agent-skill via Skill tool, read its Patterns.md + Pitfalls Checklist, examined existing rose_forest zome structure, then wrote `ARF/dnas/rose_forest/zomes/consent_integrity/{Cargo.toml,src/lib.rs}` (300+ LOC Rust HDI 0.5.1 implementing ConsentPayload + ConsentDecision entry types per ADR-12 + consent-payload.spec.md). **Compiled cleanly via `cargo check -p consent_integrity --target wasm32-unknown-unknown` in 36.36s.** Skill patterns explicitly applied: no action-header fields as entry fields, `#[serde(default)]` on optional fields, deterministic validate() with no DHT reads, `op.flattened::<EntryTypes, LinkTypes>()` dispatch. **Skill surfaced 3 real findings on first invocation:** (i) workspace HDI/HDK is two minor versions behind what skill teaches (0.5.1/0.4.1 vs 0.7.1/0.6.1), (ii) only rose_forest_integrity is wired into dna.yaml — hrea/identity/ontology integrity zomes exist as code but are unused dev artifacts, (iii) existing zomes carry `created_at`+`agent_pub_key` as entry fields in violation of the timeless invariant. **Ledger entry 0013 re-promoted from `investigate` → `adopt`** with 4/5 gates pass legitimately. The demotion-then-promotion cycle within hours produced more value than the original sloppy promotion: forced honest evaluation, exercised the skill on real work, advanced ADR-12 §8 next-action #4 simultaneously. Workspace Cargo.toml updated to include the new zome member. Contact gate (5/5) still pending — Discussion to Soushi888 will be drafted from the 3 real findings + compile-clean evidence, NOT from yesterday's fabricated draft.
- **2026-05-19** Adopt-tier honesty correction — user prompt "wait have we actually been using it?" caught a fabrication risk in a drafted GitHub Discussion to Soushi888/holochain-agent-skill. My draft claimed "caught a drift in our zomes we'd been carrying" + "would have saved us a Tryorama debugging hour" + "~15 distinct sessions of HDK 0.6 work driven by the skill" — none of which were true. Actual state: skill installed 2026-05-17, registered in available-skills list, but ZERO substantive Rust HDK invocations since install (all work was Python/markdown). MVP Phase 0 Tryorama work that this skill would have applied to passed months ago (pre-install). **Demoted entry 0013 from `adopt` → `investigate`** in reuse-ledger-seed.yaml. Honest gate count: 2/5 pass (license + rollback) + 1 thin-pass (provenance: installation-only) + 2 pending (adapter_test demoted, contact pending). INDEX.md updated to reflect: **72 entries, ALL at `investigate`** — no entries at adopt is the truthful state. Future promotion: gated on real Rust HDK session exercising the skill (most likely catalyst: ConsentPayload Holochain entry-type implementation per ADR-12 §8 #4). The substrate caught the drift before the fabricated Discussion shipped — user-question was the gate. Pattern named for future agent sessions: **installation ≠ adoption; visibility in available-skills list does not constitute adapter_test pass; document concrete patterns-applied before claiming adopter status to external maintainers.**
- **2026-05-19** Pressure-restore correction — user named anti-accumulation throttling guard as wrong default. Memory `feedback-pressure-helps-drop-throttling-guards.md` had internal contradiction (canon-protected ledger vs unrestricted-staging); user correction sharpened it to **adopt-tier-canon vs investigate-tier-inventory** distinction — even within canonical ledger file, investigate-tier rows accumulate freely as pressure surface. Memory refined to remove the ambiguity. Reuse-ledger header rewritten (v0.4 → v0.5-pressure-restored). **44-entry promotion batch** of all eligible remaining staging drafts (license ∈ {pass, pending} AND decision ≠ reject) → entries 0029-0072. Ledger 28 → 72 canonical entries; staging 55 → 11. The 11 skipped are genuine reject/license-fail including gemini-harvested cip-org/full-stack-alignment self-downgrading on empty-README (harvester self-regulates without my throttle). Consensus claim `019e40f8-fa14-755b-a330-318da4fe79e5` **APPROVED mean +0.88 variance 0.004** — unanimous-by-statistics (cerebras +0.80, gpt-oss-20b +0.90, qwen3-32b +0.95). Best signal yet; substrate confirms the correction is right.
- **2026-05-18** Activity-log unification primitive shipped — `FLOSS/packages/activity_log/{__init__.py,schema.py}` (140 LOC). Defines `Action` dataclass with `schema_version: "0.1-experimental"` for forward-compat iteration. `append_action()` best-effort write to `.agent-surface/activity.jsonl`; never raises; backpressure-safe. `tail_actions(n, kind_filter)` for log readers. Closes §A.7 U1.
- **2026-05-18** Reasoning Ensemble Synthesizer v0.1 shipped — `FLOSS/packages/reasoning_ensemble/synthesizer.py` (450 LOC). Partner to `router.py`. Implements full Upgrade B from v0.2 proposal: parallel voter dispatch (ThreadPoolExecutor, 4 local Ollama models default — phi4-mini + gemma3:12b + llama3.1 + qwen2.5-coder-3b for ≥3 providers + ≥4 model families diversity), mxbai-embed-large embedding per response, pairwise cosine similarity matrix, greedy single-link clustering with transitive merge pass, Tier-1/2/4 classification per cluster sizes, coherence-threshold guard (≥100 chars + ≥2 sentences) gating minority dissent surfacing per v0.2 §12.5. Stages full artifact to `.agent-surface/reasoning/ensemble/<id>_synthesis.json` for human review; emits one Action to the global activity log via the new `activity_log` package. CLI works as both library and standalone. Closes §A.6 step #4 partial + §A.7 U2.
- **2026-05-19** SDD retrofit on reasoning_ensemble (closing yesterday's code-first debt) — three spec docs authored post-hoc from existing implementation: `FLOSS/docs/specs/reasoning-ensemble-{router,synthesizer,mcp}.spec.md`. Each spec carries formal contract (interface, behavior, configuration, performance, calibration evidence, open questions, binding SDD discipline for future changes). Bidirectional citation chain: inline docstrings (updated prior turn) point to specs; specs cite the code. Consensus claim `019e40f0-c88c-7370-ace0-e8170760b08b` **APPROVED mean +0.68 variance 0.017** — three honest votes (cerebras +0.80 with retrofit-quality reservations, gpt-oss-20b +0.50 acknowledging retrofit limitations, qwen3-32b +0.75 with bidirectional-citation praise). The +0.50 from gpt-oss-20b is calibrated signal — retrofit IS lower-quality than spec-first; voters are honestly weighing the tradeoff rather than rubber-stamping. Closes SDD violation debt explicitly named in prior consensus claim 019e40c0 §"Honest acknowledgement."
- **2026-05-19** Cross-agent alignment loop completed — user flagged Groq TPD bleed + SDD violations + missing operator docs at ~10am UTC. **Codex executed in parallel** in two runs (17m heartbeat budget fix + 8m Mistral Vibe alignment). I read Codex's artifacts and added the inline-SDD-discipline gap Codex skipped: top-of-file docstrings on `router.py` + `synthesizer.py` + `mcp_server.py` now have WHAT / WHY / HOW / specs-and-refs sections cross-linking to architecture proposal + MDASH transfer + CFIS_v0.3 + ADR-12 + RUNTIME_SURFACES + metaharness-unification + heartbeat-runtime-budget spec + shared skill surface. Consensus claim `019e40c0-e24b-73f7-8c1f-6858718cbd5c` **APPROVED mean +0.85 variance 0.012** — **all three voters fired** (cerebras +0.80, groq-gpt-oss-20b +0.999 *no longer rate-limited because Codex's heartbeat STOP is letting Groq TPD breathe*, groq-qwen3-32b +0.75 with notes on un-retrofitted reasoning_ensemble + persistent STOP). The voter pool empirically validates Codex's fix: lower-pressure substrate produced higher-quality consensus (variance 0.012 vs 0.13-0.19 in earlier rate-limited rounds). **Polycentric pattern proof-of-life**: user flags → Codex executes → Claude reads + adds gaps → consensus publishes shared contextual state → drift surfaces named explicitly in voter rationales. Emergency state preserved (STOP file, 175/40 rounds, 112 staging) — STOP stays until UTC-midnight daily_state reset + staging drains below 25.
- **2026-05-18** Metaharness global Action wiring shipped — `router.py`, `heartbeat.py`, `harvest_reuse_ledger.py`, `poll_high_roi_actions.py`, and `autonomous_synthesis_loop.py` now tee terminal work into `.agent-surface/activity.jsonl` while preserving subsystem logs/staging. Focused tests in `scripts/tests/test_global_activity_wiring.py` cover all five tee points. Closes §A.7 U2/U3.
- **2026-05-18** Harvest drafts kalisam_fork backfill — `FLOSS/scripts/backfill_kalisam_fork.py` (110 LOC). Fetches kalisam fork list via `gh api`, builds parent→fork map, rewrites 65/66 staging drafts in place with the missing URL. 1 unmatched (`w3c/cogai` — kalisam fork exists per inventory but didn't surface in the 200-result page; manual patch trivial). Closes the user's spot-check finding 2026-05-18.
- **2026-05-18** Phi4-mini Router full 11-case calibration — **10/11 = 91%** at ~10s warm-call. Single miss: case #5 "Explain what this regex matches" → phi4 said pass_through, test label was single_strong; defensible borderline. **All ensemble cases hit correctly**. Miss-bias is in pass_through↔single_strong (cheap end of spectrum). Phi4-mini confirmed as v0.1 Router default; gemma3:12b-it-qat available as fallback via `FLOSS_ROUTER_MODEL` env. Activity log now has 35+ entries from prototype + calibration testing.
- **2026-05-19** All-engines burst (consensus claim `019e3f98-a755-7ce9-9ff4-f038e047ed85` **APPROVED mean +0.60 variance 0.19**) — five coordinated artifacts in one turn: (1) **ConsentPayload JSON schema + spec** at `FLOSS/docs/specs/consent-payload.{schema.json,spec.md}` — eight pattern types, four scope levels, four outcome modes matching ADR-12 §4 refusal semantics, ten integrity-zome validation rules. Unblocks ADR-12 §8 next gate (Holochain entry-type implementation). (2) **Reasoning Ensemble MCP server** at `FLOSS/packages/reasoning_ensemble/mcp_server.py` — FastMCP with four tools (route_prompt / deliberate / get_recent_decisions / get_ensemble_drafts). Closes working-todo §A.6 v0.2 gate #4. Any MCP-aware client can now invoke Router + Synthesizer as first-class tools. (3) **NLnet grant application v0.1 draft** at `FLOSS/docs/research/2026-05-19-nlnet-grant-application-draft.md` — three €27,500 deliverables (Consent Gate Holochain impl + CFIS Phase 0 frame-rep recruitment + Polis deliberation adapter), cites four consensus claims as substrate-evidence, deadline 2026-06-01 12:00 CEST, blocked on US-eligibility verification + tone calibration before submission. (4) **Wave-3 backlog cleanup** — `2026-05-13-multi-lens-critique-exchange.md` §5 four items formally marked SUBSUMED with strikethrough + cross-refs: ADR-PHASE-0-SUBSTRATE-VIABILITY-TEST (MVP Phase 0 complete), ADR-CONFLICT-RESOLUTION + ADR-PLURALISTIC-EPISTEMOLOGY + TRANSLATION-ENTROPY-MEASUREMENT (all → CFIS v0.3 mechanisms). (5) **INDEX.md refresh** — CFIS v0.3 + ADR-12 promotion rows added with consensus-claim hashes inline as durable references.
- **2026-05-19** CFIS v0.3 promoted to canon — `CFIS v0.3 — Pre-Pilot Hardened Specification.md` (41KB) moved from workspace root → `FLOSS/docs/architecture/CFIS_v0.3.md`. v0.2 + MDASH-thread user-prompt source archived to `FLOSS/archive/intake_raw/2026-05-14_CFIS_v0_2_source.md` + `_mdash_cfis_user_prompt_source.md`. HOLISTIC_ARCHITECTURE.md §2.5 augmented with CFIS epistemic-substrate cross-reference (CFIS Tier-1/2/4 IS the formal realization of CCES L5 Collective Intelligence; Part VII isomorphism-map cross-references P1-P5 kernel). Consensus claim `019e3f84-bfd2-7d7e-a310-232ed8f52b39` **APPROVED mean +0.60 variance 0.19** (cerebras-llama3.1-8b +0.80 with scope-implications reservations, groq-qwen3-32b +0.999 strong support, groq-gpt-oss-20b 0.0 rate-limited). Three Wave-3 items now formally subsumed: PLURALISTIC-EPISTEMOLOGY + TRANSLATION-ENTROPY-MEASUREMENT + CONFLICT-RESOLUTION → all map to CFIS v0.3 mechanisms.
- **2026-05-19** ADR-12 Consent Gate Protocol stub landed — `FLOSS/docs/adr/ADR-12-consent-gate-protocol.md` (Draft, Substrate-class). Fills the gap explicitly named in ADR-Suite v2.0 §13/§847 as the most-important-unresolved item. Body includes: concrete ConsentPayload + ConsentDecision entry-type schema sketch, ambient-vs-governed distinction table (8 surface classes), four refusal modes (reject / bounded_accept / tourist_observe / counter_propose — last three operationalize CFIS authority tiers + Tier-4 divergence), cross-ADR implications across ADR-1/3/5/6/9/10/11/13, 6 open questions, 7-step ratification gate. Substrate-class ratification (0.85 threshold) requires JSON schema + Holochain entry-type implementation + frame-rep cross-validation. Module-class stub-acceptance consensus `019e3f85-25fd-700c-9b25-4cbfede6aed3` **APPROVED mean +0.52 variance 0.13** (cerebras +0.80, qwen3-32b +0.75 with notes on open implementation Qs, gpt-oss-20b 0.0 rate-limited). Citation anchor from Positive Alignment paper §"The Paternalism Problem" (consented guidance vs technocratic imposition distinction); the stub is FLOSSI0ULLK's substrate-layer answer to the paper's conceptual framing.
- **2026-05-19** Harvest promotion batch 2 — 5 more drafts promoted as canonical entries **0024-0028** with focus on domain-gap filling: polis (compdemocracy/polis — democratic-deliberation, Positive Alignment paper cite), llamafile (mozilla-ai — local-inference-execution), openclaw-self-healing (Ramsbaby — service-resilience-watchdog), jan (janhq — offline-first-AI-alternative, compare with 0011 OpenHuman), vouch (mitchellh — developer-trust-management). Ledger version 0.3 → 0.4-promoted-2026-05-19. Now **28 canonical entries, 1 at adopt** (0013 holochain-agent-skill). Staging remaining: 55 drafts. Anti-accumulation guard now AT the soft threshold; next batch blocked until ≥2 more close to adopt.
- **2026-05-18** Polycentric round-trip exercised — published shared contextual state through the substrate (per user direction "find consensus and where there is not, publish shared contextual states for mutual enrichment and shared flourishing"): (a) submitted Module-class Claim `019e3e2c-e4a4-71a6-a487-956661a6ccb3` validating Positive Alignment alignment-map, (b) ran consensus round with active voter roster, (c) **APPROVED mean +0.55 variance 0.15** — cerebras-llama3.1-8b +0.80 with reservations on critique strength, groq-qwen3-32b +0.85 strongly on all three sub-assertions, groq-gpt-oss-20b 0.0 (rate-limited on TPD). Below the polarization threshold (0.15 < 0.25). Decision durable on source chain. Downstream: (d) HOLISTIC_ARCHITECTURE.md §2.5 CCES section got a "External cross-validation (2026-05 onwards)" footnote citing Laukkonen et al. + Full-Stack Alignment + Global Flourishing Study + CCAI, with reference to the alignment-map + consensus-claim hash, (e) 2 candidate harvest entries staged via existing pipeline: 0074 Polis (compdemocracy/polis — democratic deliberation infrastructure, 8000-char README pulled, gemini-3.1-pro-preview) + 0075 Full-Stack Alignment (cip-org/full-stack-alignment — empty README at the GitHub URL, decision downgraded accordingly). Deep DIVE dataset entry deferred — not on GitHub. 60 drafts now in staging.
- **2026-05-18** Positive Alignment paper intake — distilled `Positive Alignment AI for Human Flourishing — Deep Research Report.md` (Laukkonen et al., arXiv:2605.10310, May 2026, 16 authors across Oxford / DeepMind / OpenAI / Anthropic / Stanford / Tufts / UCLA) → `FLOSS/docs/research/2026-05-18-positive-alignment-flossi0ullk-map.md`. Mapping shows the paper proposes the paradigm FLOSSI0ULLK has been operating from for 14+ months: pluralistic, polycentric, user-authored, ecological-flourishing-positive, harness-over-prompt-engineering. Direct alignment with: CCES 8-layer telos, CFIS v0.3 cross-frame invariance, P5 (no central routing), ADR-7 AGPL cascade, ADR-0 Recognition Protocol, anti-sycophancy standing rule, consensus gateway analog vote, voter diversity policy, source chain immutability. **Independent contribution gap (what FLOSSI0ULLK has that the paper lacks):** Holochain substrate, symbolic-first validation in integrity zomes (cannot be bypassed by LLMs), working multi-model consensus mechanism, MDASH-validated harness architecture, cluster-based Tier classification via mxbai embeddings, unified Action schema + activity log. Source archived to `archive/intake_raw/2026-05-18_positive-alignment-deep-research-report.md`. **This is the SECOND external-academic-validation event in 7 days** (MDASH 2026-05-12 + this 2026-05-18) — pattern named in §7 of the new doc. Mainstream research field is converging on the answer space FLOSSI0ULLK reached from first principles; substrate + working implementation is the durable moat. Multiple downstream implications flagged: HOLISTIC_ARCHITECTURE.md §2.5 footnote, CFIS v0.3 canon promotion vocabulary, ADR-12 Consent Gate citation anchor, 3 candidate reuse-ledger entries (Full-Stack Alignment / TMV, Polis platform, Deep DIVE dataset), NLnet grant application citation.
- **2026-05-18** Cross-agent drift fix — corrected my prior session work that still referenced "Tryorama suite still the exit gate" as the Phase 0 blocker. **MVP Phase 0 is COMPLETE** per `FLOSS/MVP_PLAN.md` line 23 + cross-agent synthesis (ChatGPT correction, integrated into `FLOSS/CLAUDE.md` + workspace CLAUDE.md): DNA compiles to WASM, hApp/Tryorama integration tests pass, ontology integrity unit tests pass. Current gate is **Orchestration Substrate Bridge validation** per `FLOSS/docs/specs/phase0-substrate-bridge.spec.md` (publish → provenance → independent verify → query → fork-visible → no privileged verifier). ADR-Suite v2.0 still carries older wording → pending evidence reconciliation (not silent rewriting). Updated my Architecture-Spec v0.1 §0 banner table accordingly.
- **2026-05-18** Harvest promotion batch landed — 8 drafts promoted from staging to canonical reuse-ledger-seed.yaml as entries **0016-0023** (agentsid-scanner, caveman, agit, WildClawBench, NeMo-Agent-Toolkit, atomic-agents, OpenViking, nanobot). Selection criteria: license_gate=pass + decision=investigate + domain diversity. User spot-checked all 66 drafts 2026-05-18; backfill_kalisam_fork.py already fixed the missing fork URLs in the gap. Staging dir now has 58 remaining drafts; 8 preserved at `.agent-surface/harvest/promoted/` with paired _provenance.json. Ledger version bumped 0.2-seed-expanded → 0.3-promoted-2026-05-18. Now 23 canonical entries with 1 at `adopt` (0013) — approaching but not exceeding the 25-entry-with-none-at-adopt kill criterion.
- **2026-05-18** Shared agent memory surface v0.1 shipped — `FLOSS/shared-agent-memory-surface.json` + `FLOSS/scripts/materialize_shared_agent_memory.py` + `FLOSS/docs/agent-memory/`. Migrated 33 legacy Claude memory files into repository-owned canonical markdown with YAML frontmatter, backed up the original Claude memory directory to `.agent-surface/memory/legacy-claude-backup-20260518T175013`, and regenerated projections for `.agent-surface/memory/AGENT_MEMORY.md`, `FLOSS/docs/agent-memory/MEMORY.md`, `CHATGPT_MEMORY_EXPORT.md`, and Claude native memory. Added `scripts/tests/test_shared_agent_memory.py`; focused suite reports 9/9 passing and all materializer `--check` commands report no drift. This executes the 2026-05-18 proposal in `FLOSS/docs/research/2026-05-18-agent-memory-as-shared-surface.md`.
- **2026-05-18** Reasoning Ensemble skill promoted to shared surface — canonical source is now `FLOSS/skill-corpus/reasoning-ensemble/SKILL.md`, registered in `FLOSS/shared-skill-surface.json`, and materialized to `~/.codex/skills`, `.claude/skills`, `.gemini/skills`, and `opworkers/.opencode/skills`. This closes the Claude-only skill drift from the earlier landing.
- **2026-05-18** Conductor paper intake — read `C:\~shit\_reference\ai-ml\2512.04388v5.pdf` ("Learning to Orchestrate Agents in Natural Language with the Conductor", ICLR 2026) and distilled project implications to `FLOSS/docs/research/2026-05-18-conductor-paper-metaharness-implications.md`. Main takeaway: supports selective learned topology/planner layer above Router/Synthesizer, but FLOSSI0ULLK gates must remain external: ADR/source-chain/Holochain/consensus validation, not Conductor authority.
- **2026-05-18** Architecture-shared-context reconciliation — INDEX.md updated to 2026-05-18 with all 2026-05 landings (ADR-Suite v2.0, working-todo pointer, reuse-ledger, CFIS v0.3 pre-canon, MDASH transfer, Inline Reasoning Ensemble proposal, JanuScope, harvest staging dir). `FLOSSI0ULLK-Architecture-Spec-v0.1.md` got a §0 supersession banner explicitly flagging the ternary-vote sections (§5/§6.1/§6.2/§9) as superseded by ADR-10 v2.0 analog model; layer-taxonomy §3 noted as augmented by v4.0 kernel + CCES orthogonal-axis pair. Phase 0 blocker statuses brought to current (Test #4 PASSED, DNA compiles, holochain-agent-skill installed). Version bumped to "0.1.1-with-superseded-banners" — historical content preserved unchanged below the banner.
- **2026-05-18** Reasoning Ensemble Router v0.1 prototype landed — `FLOSS/packages/reasoning_ensemble/router.py` (530 lines). Implements three-mode classifier (pass_through/single_strong/ensemble) via Ollama HTTP API. Upgrade A wired: prompt embeddings via mxbai-embed-large → cosine similarity against last 10 activity-log entries → forced ensemble bias on Tier-4 adjacency >0.7. Conservative fallback to single_strong on any classifier failure. Activity log at `.agent-surface/reasoning/activity.jsonl` (JSONL one-line-per-event with prompt_hash + embedding + decision). Two patches during smoke testing: (1) timeout budget bumped 30s→90s for embed cold-start, (2) **OLLAMA_BASE_URL switched localhost→127.0.0.1** — Python urllib tries IPv6 first on Windows but Ollama is IPv4-only, was hanging until socket timeout. Calibration: **gemma3:12b-it-qat = 11/11 correct (100%) at 39-87s/call**, **phi4-mini = 4/4 correct (100%) at ~10s warm-call** — phi4-mini chosen as v0.1 default due to 4-5x latency win at equivalent accuracy and lighter VRAM footprint (2.5GB vs 8.9GB, fits cleanly alongside mxbai). Activity log has 19 entries from prototype testing — Tier-4 frame-cousin detection will accumulate signal over coming days. CFIS-frame-cousin per Upgrade E starts working empirically once log hits ~50 ensemble calls.
- **2026-05-17** Inline Reasoning Ensemble v0.2 upgrade — `2026-05-17-inline-reasoning-ensemble.md` §12 added (integrates external Perplexity review with two new papers: Multi-Stream LLMs Max Planck / ETH Zurich 2026-05-12 + Multi-Model Consensus Reasoning Engine arXiv Jan 2026). Five concrete upgrades: (A) Router uses cosine-similarity to past activity log for ensemble-bias on adjacent disagreement, (B) **cluster-based Tier classification via embedded responses + agglomerative clustering** (replaces vote-counting; minority-but-coherent cluster is high-signal), (C) multi-stream parallel auditing as third complementary mechanism (Later, requires fine-tuneable local model), (D) anti-sycophancy override gains reasoning-quality threshold guard (≥0.6 for verbatim surfacing), (E) frame-cousin detection emerges empirically from activity log via persistent co-cluster frequency. Revised next-action sequence (10 gates now, was 8). Hardware confirmed RTX 4090 16GB, gemma3:12b-it-qat picked as v0.1 Router. Source artifact archived: `FLOSS/archive/intake_raw/2026-05-17_inline-ensemble-perplexity-review.md`.
- **2026-05-17** Inline Reasoning Ensemble v0.1 architecture proposed — `FLOSS/docs/research/2026-05-17-inline-reasoning-ensemble.md` (CFIS-in-practice extension of ADR-10 consensus gateway from decision-grade to reasoning-grade; three-mode local Router + ensemble synthesis with Tier-1/2/4 classification; full MDASH/CFIS cross-mapping; honest pushback against literal "every prompt"; 8 next-action gates; ADR-14 promotion path). Working-todo §A.6 added. Hardware confirmed: RTX 4090 Laptop 16GB VRAM, Ollama 0.9.6 installed, **gemma3:12b-it-qat + gemma3:27b-it-qat + Qwen3-32B-Q4_K_XL + phi4-mini + others ALREADY PULLED**. First Router test run (gemma3:12b-it-qat, 5-file OAuth refactor prompt): returned valid JSON in 64s cold-start (subsequent calls expect ~2s warm); classification was `single_strong` when correct answer was `ensemble` — Router needs better few-shot prompting or step up to gemma3:27b (latter requires CPU offload at 18GB > 16GB VRAM, slower). Memory saved: `project_local_hardware_4090_laptop.md`.
- **2026-05-17** Strategic 8-fork harvest batch landed in staging (gemini-2.5-pro, user's Pro subscription) — ~60s/each, ~8 min total wall-clock. Targets: openwork (different-ai), agno (agno-agi), hermes-agent (NousResearch), AIOS (agiresearch), atomic-agents (BrainBlend-AI), ironclaw (nearai), OpenViking (volcengine), NeMo-Agent-Toolkit (NVIDIA). All drafts at `.agent-surface/harvest/staging/`. Quality spot-check (AIOS): Gemini correctly identified the central "Agent Hub Machine" as a P5 violation without being prompted to look for it, flagged NOASSERTION license as blocking, defaulted to `investigate` (no over-claiming). Sharp edge logged + patched: initial run gave all 8 drafts id=0016 because `next_available_id()` only scanned canonical ledger. Patched in v0.1.1 to scan staging dir too. Existing drafts need renumbering 0017-0024 at human promotion.
- **2026-05-17** Harvest retry batch COMPLETE — 23/23 succeeded, 0 failed in ~13 min wall-clock (17:19-17:33 UTC). Perms-issue + cwd-workaround + duration-bug + exit-code-propagation all proven fixed. Activity log now records `duration_seconds: 25.81` style real values. **Final harvest state: 66 drafts in staging (with 66 matching provenance JSON sidecars)**, 80/80 effective success rate after retry. License breakdown of 57 activity-logged drafts: 29 MIT + 8 AGPL-3.0 + 6 Apache-2.0 + 1 GPL-3.0 = **44 license-gate-eligible**; 8 NOASSERTION + 5 None = **13 blocked at license gate** (upstream clarification needed). Next action: human triage + selective promotion to canonical reuse-ledger-seed.yaml. Anti-accumulation guard active — only 1 of 16 canonical entries currently at `adopt` (0013 holochain-agent-skill), so promote selectively.
- **2026-05-17** Wide harvest batch — 59 targets, gemini-3.1-pro-preview, batch ran 13:38-14:54 UTC (~76 min). **34/59 succeeded, 23 failed, 2 indeterminate**. All 23 failures shared root cause: gemini-cli libuv crash (`Assertion failed: !(handle->flags & UV_HANDLE_CLOSING)`) when scanning `C:\~shit\_pr25fix\.pytest_cache` — directory ACL-locked under `.\floss` account (stale from pre-Servy-fix). Cannot remove without elevated admin PowerShell. **Workaround patched into harvest_reuse_ledger.py v0.1.2**: gemini subprocess now runs with `cwd=tempfile.TemporaryDirectory(prefix='floss_harvest_')` so it never scans `C:\~shit`. Also patched two other bugs: (a) batch_runner exit-code propagation (was reporting `0 fail` despite failures — `tail -3` pipe was swallowing the real rc; now captures rc before piping), (b) duration_seconds was always 0.0 (was computing end - end; now uses invocation_started captured at function entry). Retry queue persisted as durable artifact at `.agent-surface/harvest/retry_queue.txt` (23 URLs). Retry deferred: Gemini account-wide quota hit (all model tiers — pro, flash, flash-lite — slow/throttled); waiting for quota reset. **43 total drafts now in staging.**
- **2026-05-17** Two feedback memories saved: `feedback_pressure_helps_drop_throttling_guards.md` (user is procrastinator+analysis-paralysis; pressure helps; anti-accumulation guards apply to canon not staging) + `feedback_durable_provenance_required.md` (response-trail is not enough; activity.jsonl + working-todo §I + memory + ledger + provenance sidecars for every meaningful action). MEMORY.md index updated.
- **2026-05-17** All ADRs read — v2.0 consolidated suite ingested end-to-end + ADR-5 + ADR-9 individual files for depth. Key facts captured to working memory at the time: ADR-0 Validated; ADR-10 Verified 32/32 with analog vote `[-1.0, +1.0]` canonical; ADR-2 text still said Phase 0 Tryorama required; ADR-7 AGPL cascade; ADR-8 Radicle bridge unproven; ADR-9 ContinuityPayload wraps Claim wire format. **2026-05-18 correction:** MVP Phase 0 Tryorama pass is confirmed by `MVP_PLAN.md` / cross-agent synthesis; the remaining ADR-2 work is evidence reconciliation and the separate substrate-bridge validation, not redoing the old Tryorama gate. Standing rules internalized (blast-radius, Now/Later/Never, anti-sycophancy, truth-status, explicit-supersession, fork-ability). Critical gaps named in suite §13: ADR-12 Consent Gate Protocol (most important unresolved), ADR-13 Steward Vote Protocol, ADR-8.1 Radicle↔Holochain identity bridge. Tensions held: replication-fitness-vs-consent, Plane-A-vs-Plane-B premature graduation.
- **2026-05-17** Gemini CLI delegation primer SHIPPED + VALIDATED — `FLOSS/scripts/harvest_reuse_ledger.py` (v0.1.0 → v0.1.1) takes a fork URL, fetches upstream metadata + README via `gh api`, assembles a structured prompt with full FLOSSI0ULLK governance constraints (license-cascade per ADR-7, anti-pattern guards, P5 obstruction taxonomy reference), invokes gemini via stdin (workaround for Windows cmd.exe 8KB cmdline cap), validates field-name coverage, writes drafts + provenance to `.agent-surface/harvest/staging/`. End-to-end test against `khoj-ai/khoj` produced clean draft in 53s. Drafts require human review before integration to canonical ledger — Plane A only, no auto-promotion. Patches during dev: (1) shutil.which for Windows `gemini.cmd` shim, (2) stdin-fed prompt for cmdline cap, (3) v0.1.1 next-id scans staging dir to avoid batch-id-collision. Validator permissive (field-name check, not field-value match) to handle variable model quoting. Model is env-configurable via `FLOSS_HARVEST_GEMINI_MODEL`; default `gemini-2.5-flash`, batch run used `gemini-2.5-pro`.
- **2026-05-16** Heartbeat Servy account fix diagnosed — service was running as `.\floss` (LocalSystem-class) instead of `MSI\kalis`; user-site litellm + FLOSS/.env + ~/.floss_agent invisible to that account. Fix recipe: services.msc → Log On → MSI\kalis, OR `sc.exe config "flossioullk heart" obj= "MSI\kalis" password= "..."`. Also flagged: poll_high_roi_actions hardcodes `rounds=+5` regardless of actual voter execution, so the 02:00-03:00 UTC "today: 95 rounds" was likely fake — verify post-fix.
- **2026-05-16** Reuse-ledger seed activated + expanded — relocated `FLOSSIULLK_collaboration_research_plan.md` + `reuse-ledger-seed.yaml` from workspace root to `FLOSS/docs/research/`. Plan file renamed to `2026-05-13-collaboration-research-plan.md` per research-folder convention. Ledger expanded from v0.1-seed (10 entries) to v0.2-seed-expanded (15 entries) by adding the 5 highest-relevance forks from kalisam's ~90-fork GitHub inventory: OpenHuman (0011), agentmemory (0012), holochain-agent-skill (0013), delimit-mcp-server (0014), mycelix (0015). New working-todo §A.5 activates the harvest task with gate-pass priority + anti-accumulation guard.
- **2026-05-16** MDASH intake ingested — Microsoft's 2026-05-12 multi-model agentic scanning harness announcement (88.45% CyberGym, 16 Windows CVEs, Team Atlanta lineage) distilled into `2026-05-16-mdash-cfis-architectural-transfer.md` with 6 concrete CFIS v0.4 upgrade candidates (DST-A, Auditor/Debater/Prover triad, Prove Gate, Frame Context Plugin, Model Invariant Layer, Now-readiness designation). Source archived. Carries forward the A2A/MCP unified-entity-card ADR candidate from the IBM "After Mythos" continuation packet.
- **2026-05-13** Multi-lens critique exchange (3 consensus rounds) — `2026-05-13-multi-lens-critique-exchange.md`. Outcome: 55-60% recalibrated viability validated; 6th blindspot (Agent Lifecycle/Death/Decay) consensus-named; voter-counted Wave-3 priority.
- **2026-05-13** META_COORDINATION_KERNEL_v4.0 landed as canon — `META_COORDINATION_KERNEL_v4.0.md` + INDEX.md + FLOSS/CLAUDE.md updates. Consensus claim `019e2293` APPROVED mean +0.717.
- **2026-05-13** JanuScope wired in front of both MCPs — `.mcp/lenses/{flossiullk-consensus,serena}.yaml`. Activates on next session start.
- **2026-05-13** oh-my-openagent installed + omo-momus persona voter wired — `voter_registry.json` diverse-max profile + `voters.py` make_omo_momus_voter. Consensus-validated.
- **2026-05-12** Heartbeat loop launched (subsequently died on reboot; service setup pending).
- **2026-05-11** FLOSSI_U relocated to workspace root + guides/ duplicates culled — `INDEX.md` + `FLOSS/CLAUDE.md` updates.
- **2026-05-10** Doc-cull triage (Wave 1 of consolidation) — major reorg.
- **2026-05-09** AD4M / Coasys audit delta — `2026-05-09-ad4m-coasys-audit-delta.md`.
