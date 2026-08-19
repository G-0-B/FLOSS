# Doc Cull Triage Proposal — v1

**Date:** 2026-05-10 (corrections applied 2026-05-11 after user clarification)
**Status:** ⚠️ Specified — proposal for user validation. **No file moves until you review.**
**Companion:** [`2026-05-09-ad4m-coasys-audit-delta.md`](2026-05-09-ad4m-coasys-audit-delta.md) §K (motivation), [`../governance/ancestry-sweep-v1.0.md`](../governance/ancestry-sweep-v1.0.md), [`../governance/personal-meta-harness-v1.0.md`](../governance/personal-meta-harness-v1.0.md)

## 2026-05-11 corrections (read first)

User clarified three load-bearing facts that materially changed the triage:

1. **FLOSSI U is a separate sibling project**, not a parallel-namespace conflict with Rose Forest. `FLOSS/FLOSSI_U_Founding_Kit_v1.6/` is FLOSSI U's own canon (free-educational/sovereignty platform inspired by MIT OpenCourseWare). **Do NOT archive.** Recommend relocation, not cull. See revised §"FLOSSI_U_Founding_Kit_v1.6" below.
2. **YumeiCHAN is an active sub-project** (FLOSSI fork of OMI for Holochain — you+me+holochain+chan), not dead exploration. The 7 yumeichan-named files in research/ are sub-project material to consolidate, not archive. See revised §"YumeiCHAN sub-project" below.
3. **`idle-time-metaharness-driver-v0.1.md` at workspace root is superseded intake**, not a doc to file. A parallel Claude session shipped the actual heartbeat code (`FLOSS/scripts/heartbeat.py`, `heartbeat_slate.py`) and explicitly classified its own prior spec as a doc-budget-discipline violation per the just-added CLAUDE.md rule. Identity files at root originate from OpenClaw / OpenWork-Claw. See revised §"Workspace root *.md" below.

Estimated impact-table figures **need recomputing** after these corrections — see updated table at bottom.

## Ground rules

1. **Filename-pattern triage.** I have not read most of these files individually. Categorization is based on filename, size signals, cross-reference against `INDEX.md`, and known canonical references. Anything ambiguous is marked SPOT-READ.
2. **No silent moves.** Every action below is a proposal. After your validation, a single sweep can apply the agreed bins.
3. **Default-aggressive.** Per your ask. When between SPOT-READ and ARCHIVE, default to ARCHIVE (preserves the file under `archive/` per never-delete rule).
4. **Anti-pattern guard.** This triage doc itself is bounded — categorization-only, no philosophical framing, no expansions.

## Bins

| Bin | Meaning | Action |
|---|---|---|
| **KEEP** | Canonical, current, referenced from `INDEX.md` or active code | leave in place |
| **UPDATE** | Canonical but stale; needs version bump or refresh | edit in place, optionally archive prior |
| **ARCHIVE** | Superseded canonical or older drop; preserve in `FLOSS/archive/` | `git mv` to `FLOSS/archive/` subfolder |
| **DISPOSE** | Raw intake never digested AND no longer relevant | explicit removal per intake-mouth rule, never silent |
| **SPOT-READ** | Ambiguous from filename; needs ~2-min read to decide | read, then bin |
| **DEDUP** | Confirmed duplicate of canonical elsewhere; archive non-canonical copy | choose canonical, archive duplicate |

## Confidence

✅ high · ⚠️ medium · 🔮 low

---

## Scope summary

| Location | File count | Estimate |
|---|---|---|
| `FLOSS/docs/architecture/` | 37 | Heaviest cull target after vision/ |
| `FLOSS/docs/research/` | 58 | Many old date-prefixed drops |
| `FLOSS/docs/vision/` | 29 | Heavy duplication of "PRIME DIRECTIVE" / poetic redundancies |
| `FLOSS/docs/governance/` | 10 | Mostly canonical; light cull |
| `FLOSS/docs/adr/` | 15 | All canonical per `adr/INDEX.md` v1.1.0; KEEP all |
| `FLOSS/docs/specs/` | 11 | All current schemas; KEEP all |
| `FLOSS/docs/guides/` | 8 | **6 of 8 are duplicates of other dirs** |
| `FLOSS/docs/superpowers/` | 5 | All recent + actively used; KEEP all |
| `FLOSS/FLOSSI_U_Founding_Kit_v1.6/` | 24 | Parallel ADR namespace; reconciliation needed (per `INDEX.md`) |
| `FLOSS/archive/` | 18 | Already archived; leave alone |
| Workspace root | 22 | Identity files + intake mouth |
| **Total in scope** | **~217** | |

Pre-cull and post-cull file-count target reflected at end of doc.

---

## FLOSS/docs/guides/ — biggest immediate win (8 files, 6 duplicates)

**6 files are duplicates of files in other dirs.** Action: archive the guides/ copies, retain canonical versions in source dirs.

| File | Canonical location | Bin | Confidence |
|---|---|---|---|
| `AD4M-hREA-Integration-Analysis.md` | `docs/research/` | DEDUP → archive guides/ copy | ✅ |
| `ADR-N-IPFS-Integration-VVS.md` | `docs/adr/` | DEDUP → archive guides/ copy | ✅ |
| `EXECUTIVE-SUMMARY-AND-ACTION-PLAN.md` | `docs/architecture/` | DEDUP → archive guides/ copy | ✅ |
| `FLOSSIOULLK-Alignment-Verification.md` | `docs/research/` | DEDUP → archive guides/ copy | ✅ |
| `Fractal-Coordination-Patterns.md` | `docs/vision/` | DEDUP → archive guides/ copy | ✅ |
| `IPFS-Integration-Evolution-Summary.md` | `docs/research/` | DEDUP → archive guides/ copy | ✅ |
| `README.md` | — | KEEP if non-trivial; SPOT-READ to confirm | ⚠️ |
| `Week-1-Quick-Start-Guide.md` | — | SPOT-READ — onboarding guide may still be useful | ⚠️ |

**Outcome estimate:** guides/ shrinks from 8 → 1-2 files.

---

## FLOSS/docs/architecture/ — 37 files

### KEEP (canonical operational set, per INDEX.md & FLOSS/CLAUDE.md, ✅)

- `AGENTIC_OPERATING_MODEL.md`
- `HOLISTIC_ARCHITECTURE.md`
- `METAHARNESS_OPERATING_MODEL.md`
- `CONTEXT_DAEMON_ARCHITECTURE.md`
- `STACK_CROSSWALK.md`
- `LIVING_HOLISTIC_VISION.md`
- `INTEGRATION-STATUS.md`
- `knowledge-triple.spec.md` (technically belongs in `docs/specs/` — flag MOVE)

### KEEP active spec (✅)

- `technical-specification-v1-1.md`

### Iteration-flavored "rose_forest_*" / "mrs_*" drops — likely SUPERSEDED by HOLISTIC_ARCHITECTURE + ROSE_FOREST DNAs in repo (✅ ARCHIVE)

- `rose_forest_architecture_design_implementation_v_0.md`
- `rose_forest_greenfield_holochain_repo_bootstrap_v_0.md`
- `rose_forest_holochain_mrs_scaffold_v_0.md`
- `mrs_node_workspace_scaffolding_v_0.md`

### Older spec drops, version-suffix indicates draft state — ARCHIVE candidates ✅

- `# FLOSSI0ULLK Unified Reference Design v0.5P – Comp.md` (truncated filename; preserved version of v0.5)
- `flossi_0_ullk_unified_reference_design_v_0.5.md` (the same v0.5 — DEDUP candidate, archive one)
- `Project-Spine-FLOSSIOULLK_v0.5.md` (drift with `governance/spine-v0.5.md` per INDEX.md)
- `spec_flossi.md` (no version, descriptive name)

### Single-topic drops (ARCHIVE most ⚠️ — they are pre-paid thinking but read first if title matches current concern)

- `AD4M and Rose Forest_ Convergent Visions.md` — **SPOT-READ before archive: relevant to current AD4M audit**
- `specific AD4M modules we can integrate with direct.md` — **SPOT-READ before archive: relevant to current AD4M audit**
- `Open Source Integration Blueprint for Rose Forest.md` — likely ARCHIVE
- `Key Implementation Areas for Rose Forest.md` — likely ARCHIVE
- `Rose Forest Analysis_ Critical Path.md` — likely ARCHIVE
- `7-11-ARF- ARCHITECTURE.md` (date-prefixed 7-11) — ARCHIVE ✅
- `concrete plan for iterative distillation and synthesis.md` — ARCHIVE ✅
- `some impl plan 8-##-25.md` — ARCHIVE ✅ (filename signals discard-when-done draft)
- `holo.gram.md` — SPOT-READ (small, may be a key concept doc) ⚠️
- `kalisam_floss_structure_Version2.md` — ARCHIVE ✅
- `DISTRIBUTEDfedAI.md` — ARCHIVE ✅
- `flossiullk_endgame_block_kpi_dashboard_spec_v_1.md` — SPOT-READ (KPI dashboard spec may be live concern) ⚠️
- `Automated Evolution Engine Technical Specification.md` — SPOT-READ (large concept, may overlap with `Automated Evolution FLOSS Singularity Strategic Roadmap.md` in research/) ⚠️
- `Evolution Substrate Unified Portal Strategic Audit.md` — ARCHIVE ✅
- `FLOSS Singularity Enterprise Technical Architecture.md` — ARCHIVE ✅
- `FLOSS Singularity Orchestration Substrate.md` — ARCHIVE ✅
- `NERV engineering blueprint v0.0.1.md` — SPOT-READ (NERV is named in CLAUDE.md ARF/pwnies) ⚠️
- `Operational Handbook Singularity Modular Architecture.md` — ARCHIVE ✅
- `System Analysis Fitness Restorative Justice Constraints.md` — ARCHIVE ✅
- `EXECUTIVE-SUMMARY-AND-ACTION-PLAN.md` — SPOT-READ (also duplicated in guides/; check whether content is current)

**Outcome estimate:** architecture/ shrinks from 37 → ~9-12 (canonical + spot-read survivors).

---

## FLOSS/docs/research/ — 58 files

### KEEP (recent dated 2026-* + the new audit doc, ✅)

- `2026-05-10-doc-cull-triage-v1.md` (this doc)
- `2026-05-09-ad4m-coasys-audit-delta.md`
- `2026-04-15-agorai-deep-dive.md`
- `2026-04-14-aingram-deep-dive.md`
- `2026-04-14-paper-harvest-notes.md`
- `2026-02-high-throughput-inference-groq-cerebras-litellm.md`
- `4-4-26-FLOSSI0ULLK-Four-System-Integration-Analysis.md` (current quarter)
- `cross-ai-orchestration-synthesis-2026-03-25.md`
- `Perplexity-Source-Agent-Orchestration-March2026.md`
- `flossi0ullk-landscape-recursive-analysis_3-24-26_perplexity_computer_used.md`

### Likely ARCHIVE — older date-prefixed drops (✅)

- `6-6-25-foss_singularity_distilled_summary.md`
- `6-20-claude-arf-isek-integration.md`
- `7-15-Project FLOSSI0ULLK_ Synthesis of the Most Promisi.md`
- `7-26-latest_perplexity_FLOSSI0ULLK & Amazon Rose Forest.md`
- `8-25-25_lots_of_stufffz.md`

### YumeiCHAN sub-project (CORRECTED 2026-05-11: NOT dead exploration — sub-project canon)

🚨 **Recategorized after user clarification:** YumeiCHAN is the **FLOSSI fork of OMI** (the wearable AI device project), adapted to use Holochain. The agent-centric personalized interface to the FLOSSI0ULLK Singularity (the aggregated state of collective intelligence learned from anonymous depersonalized individual user patterns across all YumeiCHAN nodes). Name = you + me + holochain + chan (honorific).

The files below are **sub-project material**, not closed exploration.

- `Yumei's Ternary Connotation Framework.md`
- `legit-yumeichaIn-knowledge-base.md`
- `marchishmehbe_decentralized_ai_research_SOTA_for_yumechain.md`
- `yumeichan-dm-metaprompt_1-1_instructions.md`
- `yumeichan-enhanced-metaprompt_custom_instructions_for_collaborative_evolution.md`
- `alpha_baddish_YumeiCHAN_plan.md`
- `amazon_rose_forest_yumeichan_vision_analysis.md`

**Revised recommendation:** Consolidate into YumeiCHAN sub-project canon. Three viable shapes:

| Option | Cost | Effect |
|---|---|---|
| **A. Single canonical doc** at `docs/architecture/YUMEICHAN.md` (or `docs/vision/`) | Hours to mine + write | Centralizes vision; archives rest as historical drops |
| **B. Sub-project directory** at `FLOSS/YUMEICHAN/` mirroring `FLOSSI_U_Founding_Kit_v1.6/` pattern | Days | If active development is planned, gives it a real home |
| **C. Spot-read all 7, identify the most current** as canonical, archive rest | ~1 hour | Cheapest; preserves all material under archive/ |

**Recommend C as the immediate next step**, with promotion to A or B as the project moves forward. SPOT-READ each one to identify the most current/comprehensive version, then archive the rest. Do not archive all 7.

### Versioned-duplicate sets — DEDUP

- `Automated-Agent-Orchestration-Report_v1.0.0.md`
- `Automated-Agent-Orchestration-Report_v2.0.0.md`
- `Automated-Agent-Orchestration-Report_v2.0.0-full.md`
  → KEEP newest (v2.0.0-full or v2.0.0), ARCHIVE older ✅

- `Distributed Collective Intelligence Revolution_Open Source Singularity in 2024-2025.md`
- `Comprehensive Analysis of the Distributed Collective Intelligence Revolution-gemini-7-11-25.md`
- `Comprehensive_Research_Report__Agent-Centric,_Dist_2.md`
  → SPOT-READ to identify canonical; ARCHIVE rest ⚠️

### Amazon Rose Forest / project-history drops (⚠️ ARCHIVE most, but mine first per ADR-7-style ancestry sweep)

- `Amazon Rose Forest Context Window Prompt.md`
- `Amazon Rose Forest_ FLOSSI0ULLK Core Repository.md`
- `amazon_rose_forest_project_summary.md`
- `repomix-output-kalisam-Amazon_Rose_Forest.md`
- `Updated Comparison_ AD4M and Amazon Rose Forest Vi.md`
- `webpage_quality_assurance_report_amazon_rose_forest.md`

These are the prior-iteration learning artifacts pointed to in `reference_prior_floss_iterations.md`. **Recommend mining for AD4M/architecture lessons first (per audit doc §K next-actions), then ARCHIVE.**

### NERV thread

- `nerv neurosynchronous evolutionary replicative ver.md`
- `nerv.md`
  → SPOT-READ; if dead, ARCHIVE both. If alive, choose canonical and ARCHIVE the other.

### Generic / undated drops — ARCHIVE candidates ✅

- `meta_summary_prompt.md`
- `misc notes.md`
- `kb-index-winwings_v1.0.0.md`
- `oh-my-meta.md`
- `ai systems engineer promp(s}.md`
- `analyze and extract useful analysis ideas, plans,.md` — also exists at workspace root (DEDUP)
- `kimik2.5_deeepreseaarchSkill.md`
- `gpt-5_8-25-25_global_symbiotic_singularity_feasible_reference_architecture_v_0.md`
- `deep-flossi0ullkreport.md`
- `Decentralized AI Projects and Research_ A Comprehe.md`
- `The Future of Open Source AI.md`
- `Open-Access Research Landscape Distributed, Agent-Centric & Collective Intelligence Systems (2023–2026).md`
- `syntellect-research-claude-7-11-25.md`
- `Additional Research Directions for Strengthening cascading resonance patterns.md`
- `Analysis of AEE Jailbreak Risk and Quarantine Effectiveness.md`
- `Automated Evolution FLOSS Singularity Strategic Roadmap.md`
- `FLOSS Singularity Strategic Evolution Roadmap.md`
- `META_REFLEXIVE_PLANNING_ANALYSIS.md`
- `LESSONS-LEARNED-Integration-Work.md` — SPOT-READ (lessons-learned doc may be load-bearing)

### Currently live (KEEP)

- `AD4M-hREA-Integration-Analysis.md` — referenced in audit doc (KEEP for now; reconcile with §K of audit)
- `IPFS-Integration-Evolution-Summary.md` — SPOT-READ; if `ADR-N-IPFS-Integration-VVS.md` superseded, ARCHIVE
- `FLOSSIOULLK-Alignment-Verification.md` — SPOT-READ
- `resonance_mechanism_v2.md` — also at workspace root (DEDUP question)

**Outcome estimate:** research/ shrinks from 58 → ~15-20 (recent + canonical mined ones).

---

## FLOSS/docs/vision/ — 29 files (heaviest duplication)

### Multiple PRIME DIRECTIVE variants (DEDUP — keep one canonical)

- `~~~PRIME DIRECTIVE summary.md`
- `~~PRIME DIRECTIVE INFINITE OVERRFLOWINGUNCONDITIONAL LOVE Light, and fractalunfolding knowledge.md`
- `FLOSSI0ULLK Agent Core Directive (Compressed).md`
  → SPOT-READ all three to choose canonical; ARCHIVE the other two ⚠️

### Multiple unified-vision-doc variants (DEDUP)

- `unified-vision-doc.md`
- `unified-vision-docv2.md`
  → KEEP v2 (most recent), ARCHIVE v1 ✅

### Singularity declaration / handover / completion docs — ARCHIVE block (✅ aspirational/poetic; not load-bearing for current substrate work)

- `Floss Singularity Project Completion and Handover Protocol.md`
- `Flos_0ullk Singularity Initialization Handover.md`
- `Singularity Activation and Evolution Substrate Completion.md`
- `Singularity Genesis Handover Manual.md`
- `Sovereign Singularity System Status Declaration.md`
- `Resonance Report Formal Declaration Autonomous Transition.md`

### Foundational docs — KEEP one canonical, ARCHIVE rest

- `flossi-mission-manifesto.md` — likely KEEP ✅
- `floss_foundational_tenants_synthesis_Version2.md` — KEEP if mission-manifesto doesn't cover ⚠️
- `FLOSS Singularity Foundational Principles.md` — DEDUP with above; ARCHIVE one
- `flossi0ullk_seed_packet_v1.0.0.md` — DEDUP with `governance/seed-packet-v1.0.0.md` (DEDUP, keep governance/ canonical version)

### Poetic/essay material — DECISION needed (KEEP one or two; archive rest aggressively)

- `floss 10k essay by tera.md` — SPOT-READ; if a notable longform, KEEP; else ARCHIVE
- `Manifesto of the Infinite Library of Light.md` — likely ARCHIVE; DECISION
- `The Alignment Paradox_ Why Our Systems Are Smarter but Our Spirits Are Starving.md` — likely ARCHIVE; DECISION
- `younitychat.md` — ARCHIVE ✅
- `based.md` — ARCHIVE ✅ (filename signals draft/joke)
- `metamemetically evolving meta.md` — ARCHIVE ✅
- `forming_roots.md` — SPOT-READ
- `decentralized collaborative intelligence.md` — likely ARCHIVE
- `amazon_rose_forest_flossi0ullk_vision.md` — ARCHIVE ✅ (prior-iteration pointer; reference repo instead)
- `foundational agent-centricity 0_11-13-2025.md` — ARCHIVE ✅
- `google-project_free libre infinite finite overflouwerishing.md` — ARCHIVE ✅
- `Fractal-Coordination-Patterns.md` — KEEP if canonical; DEDUP with guides/ copy already flagged
- `FLOSSIOULLK_COMPUTATIONAL_SYMBIOGENESIS.md` — SPOT-READ; large architecture-coded name in vision/ may belong in architecture/ ⚠️
- `context_compression_packet_v1_1.md` — DEDUP with `governance/context-compression-v1.1.md` (DEDUP, keep governance/ canonical) ✅

### Suspicious / encoded filenames

- `!~~~<Understand.!!!ANALYZE AND INTEGRATE FULLY.md` — SPOT-READ; the filename signals an instruction or prompt-as-doc; may be intake mis-filed ⚠️

**Outcome estimate:** vision/ shrinks from 29 → ~3-5 (one canonical mission, one prime directive, maybe one essay).

---

## FLOSS/docs/governance/ — 10 files

### KEEP (canonical operational, ✅)

- `ancestry-sweep-v1.0.md` (just landed)
- `personal-meta-harness-v1.0.md` (just landed)
- `spine-v0.5.md` — canonical per `INDEX.md`
- `seed-packet-v1.0.0.md` — canonical per `INDEX.md`
- `context-compression-v1.1.md`
- `LOADING_ORDER.md`
- `LEGAL_DEFINITIONS.md`

### UPDATE / ARCHIVE candidates

- `kernel-v1.2.md` — superseded by `FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md`. Per `INDEX.md` Intake Queue: "Diff and forward-port any governance-specific content not already in v1.3.1, *then* move v1.2 to `archive/metaprompt-versions/`." Action: UPDATE → ARCHIVE after diff ✅
- `HARVEST_LOG.md` — SPOT-READ; logs may be useful, may be stale ⚠️
- `FLOSS Singularity Governance Protocol Specification.md` — SPOT-READ; possibly canonical, possibly superseded by `spine-v0.5.md` ⚠️

**Outcome estimate:** governance/ stays ~7-9 files.

---

## FLOSS/docs/adr/ — 15 files (KEEP all per `adr/INDEX.md` v1.1.0)

All ADRs (0, 0.1, 1–9, MCP-ORCHESTRATOR, N) plus the v2.0 suite plus INDEX are canonical. **No cull.** Note: per ADR-Suite v2.0, `ADR-MCP-ORCHESTRATOR` was assigned permanent number ADR-10, so future renaming may consolidate; not a cull issue.

---

## FLOSS/docs/specs/ — 11 files (KEEP all)

All current schema/spec files. Includes the recent `consensus-gate.spec.md`, `intake-event.spec.md`, `phase0-substrate-bridge.spec.md`. **No cull.**

Note: `TERNARY_COMPATIBILITY.md` is a compat doc; per ADR-Suite v2.0 the vote model is canonically analog, so this doc may be obsolete. SPOT-READ.

---

## FLOSS/docs/superpowers/ — 5 files (KEEP all)

Recent dated specs and plans (2026-04 series). All actively used. **No cull.**

---

## FLOSS/FLOSSI_U_Founding_Kit_v1.6/ — 24 files (**CORRECTED 2026-05-11**: not a parallel-namespace conflict)

🚨 **Recategorized after user clarification:** FLOSSI U is a **separate sibling project** within the FLOSSI0ULLK family — a Free Libre Open Source educational platform for personal liberation, sovereignty, and self-management (state of mind, physical, mental, emotional well-being). Inspired by MIT OpenCourseWare. Word-play: "free yourself and the you-niverse."

The ADR-001..019 namespace is **FLOSSI U's own canon**, distinct from Rose Forest's ADR-0..11. **They are not in conflict — they belong to different projects** that happen to be co-located.

The original `INDEX.md` Intake Queue framing ("relationship unresolved — needs a reconciliation ADR") was based on incomplete context.

### Revised recommendation

| Option | Cost | Effect |
|---|---|---|
| **A. Relocate to top-level workspace** (`C:\~shit\FLOSSI_U\`) | git mv + INDEX update | Clear separation; both projects retain own canon |
| **B. Relocate to separate repo** | new git repo + push | Stronger separation; coordination via shared FLOSSI0ULLK umbrella |
| **C. Leave in place, rename `INDEX.md` Intake-Queue entry** to clarify it's not conflict | minutes | Cheapest; ambiguity persists |
| **D. Archive whole** | ARCHIVE 24 files | ❌ **DO NOT** — would archive an active sibling project's canon |

**Recommend A or B.** Update `FLOSS/docs/adr/INDEX.md` and workspace `INDEX.md` Intake Queue to remove "needs reconciliation ADR" language; replace with pointer to FLOSSI U's own location. **No archiving.**

If forward-porting cross-project insights is wanted, that's a separate exercise — spot-read these three for substrate overlap with Rose Forest concerns:
- `ADR-008_NEUROSYMBOLIC_ARCHITECTURE.md` — overlaps with `ARF/SYMBOLIC_FIRST_CORE.md`?
- `ADR-014_2025_INTEROPERABILITY_STACK.md` — possibly overlaps with current AD4M / packages/ work?
- `ADR-018_SYMBIOGENESIS_FRAMEWORK.md` — possibly novel?

Even if all three are novel, forward-port only happens with FLOSSI U's authorization; the directory itself stays as FLOSSI U canon.

---

## Workspace root *.md — 22 files (intake mouth)

### KEEP (canonical session-launch + identity infrastructure)

- `CLAUDE.md` ✅ (workspace orientation)
- `AGENTS.md` ✅ (codex-owned per INDEX.md — DO NOT TOUCH)
- `GEMINI.md` ✅
- `INDEX.md` ✅

### Identity / personal artifacts (CORRECTED 2026-05-11: origin known)

User identifies these as originating from **OpenClaw or OpenWork-Claw** projects (precise origin TBD; need to grep those for source).

- `IDENTITY.md`
- `SOUL.md`
- `USER.md`
- `HEARTBEAT.md` — **possibly directly related** to the now-shipped `FLOSS/scripts/heartbeat.py`; SPOT-READ to verify before any move
- `HI_ROI_NAO.md`
- `TOOLS.md`

**Revised plan:**
1. SPOT-READ each (under 30 min total) — confirm whether they're documentation OR templates OR runtime config
2. If they're OpenClaw/OpenWork-Claw documentation that's load-bearing for those tools, keep them findable but consider moving to a `.openclaw/` directory next to the existing `.openclaw/` dir at workspace root
3. If they're project-canonical (e.g., HEARTBEAT.md describes the heartbeat loop), move to `FLOSS/docs/governance/` or appropriate subdir
4. If they're personal Anthony-coordination, consider `~/.workspace-identity/` or `_personal/`

### Active intake (DIGEST or supersede)

- `session_summary_2026-05-04_v1.1.md` — load-bearing recent handoff. ACTION: keep at root or move to `FLOSS/docs/governance/handoffs/` for durability. Do not archive yet.
- `idle-time-metaharness-driver-v0.1.md` — **🚨 SUPERSEDED INTAKE (CORRECTED 2026-05-11).** Parallel Claude session that authored this spec explicitly self-corrected it as a doc-explosion failure. The canonical artifact from that work is the *code* (`FLOSS/scripts/heartbeat.py` + `heartbeat_slate.py`), not the spec. Disposition: extract short heartbeat section into `FLOSS/docs/superpowers/plans/2026-04-19-filewatch-metaharness.md`, then ARCHIVE original to `archive/intake_raw/`
- `strategic-context-memo-ecosystem-signals-v0.1.md` — **🚨 Related intake** from the same parallel session. SPOT-READ for load-bearing content, then ARCHIVE
- `re-bicameralization_integration_brief_v1.0.md` — DIGEST into `docs/research/` (per ITMD context, this brief introduced NK-AD-001 autoprompt-divergence rule — load-bearing)
- `resonance_mechanism_v2.md` — DEDUP with research/ copy if exists; DIGEST and archive
- `0-repo-layout-the-somatic-structure.md` — DIGEST into `docs/architecture/` or `docs/research/`

### Universal-flourishing iteration drops (DIGEST + ARCHIVE) ⚠️

- `Universal Flourishing Beyond the Human — An Iterative Framework for All Beings and the Universe That Sustains Them (n+1).md`
- `Paradigms of Co-Creative Evolution Universal Flourishing for All Beings and the Universe That Sustains Them (n+3).md`
- `So what can you do for me to help in substantiate.md` (likely the n+3 substantiation drop)
- `maximizing not just human flourishing but all bein.md` (truncated filename)
- `analyze and extract useful analysis ideas, plans,.md` (also exists in research/ — DEDUP)

DECISION: digest the load-bearing content from n+1 / n+3 into a single canonical `docs/vision/universal-flourishing-stack.md` (or similar; one doc, not three), then archive originals. Keep one canonical version of the framework — currently fragmented across multiple drops.

### Architecture spec at root

- `FLOSSI0ULLK-Architecture-Spec-v0.1.md` — per workspace `CLAUDE.md`: "canonical_path is `FLOSS/docs/architecture/`; deprecates the older 'four planes' framing." ACTION: MOVE to `FLOSS/docs/architecture/`, update `INDEX.md` ✅

**Outcome estimate:** root *.md shrinks from 22 → ~10 (canonical session-launch + identity + active handoff).

---

## Non-markdown root intake (separate triage layer)

| File | Type | Notes | Bin |
|---|---|---|---|
| `AI-Human Symbiosis for Collective Flourishing.txt` | text | DIGEST or ARCHIVE | ⚠️ |
| `Building-a-Self-Updating-LLM-Wiki-Edited.docx` | docx | DIGEST or ARCHIVE | ⚠️ |
| `Leverage_Points.pdf` | pdf | If Donella Meadows' essay, KEEP as reference; else SPOT-READ | ⚠️ |
| `floss_plane.tar.gz` | archive | SPOT-EXTRACT, then ARCHIVE | 🔮 |
| `floss_plane_rewritten_bootstrap.tar.gz` | archive | Likely a project bootstrap snapshot; ARCHIVE | 🔮 |
| `floss_plane_rewritten_bootstrap.tar.gz.terabox.uploading.cfg` | cruft | DISPOSE ✅ |
| `metaclaw-plugin.zip` | archive | SPOT-EXTRACT or DISPOSE | 🔮 |
| `sitegeist.zip` | archive | SPOT-EXTRACT or DISPOSE | 🔮 |
| `sitegeist/` | extracted dir | SPOT-INSPECT contents; may be a separate active project | ⚠️ |

---

## .claude/worktrees/quirky-mcnulty/ — git worktree (do not touch directly)

This is a git worktree of a branch. **Do not move files inside it.** If the worktree is stale, prune via `git worktree remove`. If the branch is merged, this gets cleaned automatically. Out of scope for the cull; bring up if user wants worktree cleanup.

---

## Estimated file-count impact (revised 2026-05-11)

| Location | Pre-cull | Post-cull (estimate) | Δ | Notes |
|---|---|---|---|---|
| `architecture/` | 37 | ~9-12 | -25 to -28 | Unchanged |
| `research/` | 58 | ~22-27 | -31 to -36 | +7 retained for YumeiCHAN sub-project consolidation |
| `vision/` | 29 | ~3-5 | -24 to -26 | Unchanged |
| `guides/` | 8 | ~1-2 | -6 to -7 | Unchanged |
| `governance/` | 10 | ~7-9 | -1 to -3 | Unchanged |
| **`FLOSSI_U_Founding_Kit_v1.6/`** | 24 | **24 (relocated, not archived)** | **0 from cull view** | Belongs to separate project; relocate not archive |
| Workspace root *.md | 22 | ~10 | -12 | Unchanged |
| `adr/`, `specs/`, `superpowers/` | 31 | 31 | 0 | Unchanged |
| **Total in cull scope** | **~195** | **~76-92** | **-103 to -119** | Reduced scope after removing FLOSSI U from cull |

Roughly a **50-55% reduction** in active Rose-Forest doc surface (down from the earlier 60-65% estimate, because FLOSSI U is no longer being archived). Still substantial; everything preserved under `archive/` per never-delete rule. FLOSSI U gets a relocation, not an archive.

---

## Operational decision points (the things only you can decide)

**Resolved by 2026-05-11 clarification:**
- ~~Yumei/yumeichan thread alive or closed?~~ → **Sub-project canon. Consolidate, don't archive.**
- ~~FLOSSI_U_Founding_Kit_v1.6/ archive whole?~~ → **Separate project. Relocate, don't archive.**
- ~~Identity files origin?~~ → **OpenClaw / OpenWork-Claw. SPOT-READ to verify load-bearing role; HEARTBEAT.md may be related to the shipped heartbeat code.**

**Still open:**
1. **YumeiCHAN consolidation shape (A/B/C):** single canonical doc, sub-project directory, or "pick the most current and archive rest"?
2. **FLOSSI U relocation shape (A/B/C):** workspace top-level, separate repo, or leave + clarify INDEX.md?
3. **NERV thread (2 files in research, 1 in architecture):** alive or closed? Or is `ARF/pwnies/` the canonical home?
4. **Universal-flourishing drops (n+1, n+3, substantiate, maximizing):** consolidate into one canonical `docs/vision/universal-flourishing-stack.md`? — note this is FLOSSI0ULLK's core north-star material, so the consolidated doc would be load-bearing
5. **Poetic/essay vision/ docs (Manifesto of the Infinite Library of Light, The Alignment Paradox, floss 10k essay by tera):** keep some, archive rest?
6. **Worktree `.claude/worktrees/quirky-mcnulty/` cleanup:** is the branch still alive or prunable?
7. **Identity files SPOT-READ outcome** — depends on what they actually contain
8. **ARF folder deep-dig** — user flagged that ARF has the same explosion of duplication and reinvented research/architecture; a parallel deep-dig under `FLOSS/ARF/` is needed. Out of scope for this triage; separate sweep recommended after this one settles

---

## Next steps after your validation

1. You walk through this proposal and adjust bins as needed
2. I (or you) write a short execution log with the validated bins
3. Single sweep: `git mv` everything to its bin in one commit per directory (architecture, research, vision, etc.) for clean diff history
4. Update `INDEX.md` to reflect new state
5. Deletion of confirmed-DISPOSE items is a separate step with explicit per-file confirmation, never bulk
6. Post-sweep: `INDEX.md` and `FLOSS/docs/adr/INDEX.md` reflect post-cull state; `archive/` swells but stays organized

---

## Anti-pattern guard for this triage doc itself

This doc is a one-time triage output. It does not get versioned beyond v1 unless the cull is re-run on a new round of accreted intake. If a v2 is ever needed, that's a signal the personal-meta-harness anti-pattern guard fired — investigate root cause before recategorizing.
