# 2026-07-07 Root Intake Digestion Map

```yaml
id: "2026-07-07-root-intake-digestion"
status: "Relocation completed 2026-07-08 (14 files moved, sha256 verified); distillation pending"
truth_status:
  relocation: "Verified (2026-07-08 — 14 files moved with pre/post sha256 checkpoints; 1 dedup-skip)"
  classification: "Specified (single-agent read pass, 2026-07-07)"
  canon_promotion: "Not performed"
move_log: ".agent-surface/intake/root-intake-moves-2026-07-07.json"
raw_holding_area: "FLOSS/docs/research/intake_raw/2026-07-07-root/{reports,reference}/"
companion_record: "Supersedes 2026-06-12 pass as latest intake map; 06-12 map retained as template"
previous_passes:
  - "2026-05-19"
  - "2026-05-22"
  - "2026-06-08"
  - "2026-06-12 (template: 2026-06-12-root-intake-digestion.md)"
```

## What changed

A read-only root-intake digestion pass classified 13 new undigested items (7
markdown files + 6 PDFs) that landed at the workspace root (and one subdir)
since the 2026-06-12 digestion pass. **No files were moved, renamed, or
modified** — Anthony is AFK and file moves require provenance recording and
sha256 checkpoints per project discipline. This pass reads, classifies, and
recommends destinations only.

The intake falls into four clusters:
- **Lovable synthesis cluster** (2026-06-13): grand synthesis + ROI matrix + UTN v0.3 spec + Carse deep reading — a four-document critical distillation of the FLOSSIOULLK corpus
- **Agent coordination cluster** (2026-06-13 → 06-20): continuation packet + OpenHuman outreach brief + Yumeichan implementation packet — the OpenHuman/Omi/Yumeichan thread and its local implementation handoff
- **Memory infrastructure** (2026-06-18): agentmemory/SiYuan/Khoj/mem0 stack mapping
- **External research PDFs** (2026-06-18 → 06-19): three arXiv papers + two Anthropic system cards + one business sustainability chapter

## Classification verdicts

| # | File (current location) | Size | Kind | Vintage | Truth | One-line summary | Recommended destination | Dependencies / flags |
|---|---|---|---|---|---|---|---|---|
| 1 | `yumeichan-heartbeat-bridge-local-implementation-packet-2026-06-20.md` (root) | 9,643 B / 371 lines | handoff packet | 2026-06-20 | U | Implementation handoff for Yumeichan v0.1 — read-only heartbeat/STOP/repo state inspector with `state.json` schema, safety rules, and 6-step build plan; "Yumeichan coordinates momentum; FLOSSI0ULLK governs authority; Anthony remains the consent root." | `architecture/` | **Not canon** — handoff packet, repo wins on conflict. References PR #38 and ADR-15 PR-A which may have progressed since. Defines `.agent-surface/yumeichan/state.json` schema v0.1. STOP-file discipline aligns with workspace convention. |
| 2 | `FLOSSIOULLK_grand_synthesis_by_lovable_6-13-2026.md` (root) | 21,795 B / 247 lines | synthesis | 2026-06-13 | U | Lovable-produced critical distillation across 6 source documents (Carse, Furr UTN, permeable-shells seed, Flourishing Protocol, PRIME-DIRECTIVE chat, substantiate doc); identifies 4 load-bearing ideas, 5 high-ROI plays, cross-document motif map, truth-status audit, deduplicated glossary, 8 open questions. | `research/` | **AI-generated synthesis** — its self-applied V/S/A/U tags are useful but not authoritative. Companion to item 3 (ROI matrix). PDF twin exists (item 2b). Notes FLOSSIOULLK acronym is never defined in the corpus — known gap. |
| 2b | `FLOSSIOULLK_grand_synthesis_by_lovable_6-13-2026.pdf` (root) | 261,588 B / 9 pages | PDF (synthesis) | 2026-06-13 | U | PDF render of item 2 — byte-identical content, headless Chrome output. | `research/` (with item 2) | **Duplicate flag**: `FLOSSIOULLK_grand_synthesis.pdf` (same size, 3 min earlier mtime) also exists at root — likely an earlier render of the same document. Deduplicate at move time (keep the `_by_lovable_6-13-2026` named version). |
| 3 | `FLOSSIOULLK_roi_matrix_by_lovable_6-13-2026.md` (root) | 9,103 B / 39 lines | ROI matrix | 2026-06-13 | U | Companion to item 2: 25 distinct ideas from the 6-doc corpus scored by payoff÷effort. Top 5 = reduction test for permeable shells (#1), dogfood UTN loop (#4), Peony doula MVP definition (#7), falsifiable anti-sycophancy/anti-dependence (#8), capability-token coverage audit (#14). | `research/` (with item 2) | **Companion to item 2** — read together. Types: write/build/research/govern/product. Kill criteria specified per item. |
| 4 | `FLOSSI0ULLK_Context_Continuation_Packet_2026-06-13_for-cowork.md` (root) | 8,987 B / 167 lines | continuation packet | 2026-06-13 | U | Claude Code → Claude Cowork handoff: 06-12→06-13 code/canon changes (root-intake digestion, spec-gate D7, ObjectGraph spike N6, NLnet status), Fable-access doctrine change, OpenHuman/Omi/Yumeichan outreach thread state, repo/branch state, 5 open questions for Anthony. | `research/` | **Live continuity artifact, not canon.** **OBSOLETE-FLAG**: §2 "Fable access pulled" is superseded — Hermes now runs Fable-5 via Pioneer.ai API (durable, per workspace skill inference posture). References PR #36 (may be merged by now). Filename uses `FLOSSI0ULLK` (zero), not `FLOSSIOULLK` (O). |
| 5 | `agentmemory, openhuman, siyuan an more, flossioullk weavings.md` (root) | 6,331 B / 103 lines | tooling survey (Perplexity) | 2026-06-18 | U | Perplexity export mapping agentmemory/mem0/Khoj/SiYuan stack; recommends activation order (SiYuan MCP first, then Khoj, then evaluate mem0); 3-layer memory architecture (episodic/structured-KB/semantic-search); notes SiYuan kernel HTTP API at localhost:6806. | `research/` | **External source** (Perplexity) — benchmark claims (95.2% recall) are vendor-cited, not independently verified. FLOSS stack framing relevant to OpenHuman outreach. SiYuan MCP server (`@porkll/siyuan-mcp`) is a concrete actionable. |
| 6 | `Free Libre Open Source SingYouRarity/openhuman-outreach-brief.md` (subdir) | 10,026 B / 130 lines | outreach brief | 2026-06-13 | U | Conversation brief for OpenHuman/TinyHumans.ai Discord outreach: shared DNA framing, Holochain in plain language, Omi sensing layer, Yumeichan meaning layer, 5-layer integration vision (Omi→OpenHuman→Holochain→FLOSSI0ULLK→Yumeichan), honest privacy tension, likely Q&A, soft ask. | `research/` | **Live outreach artifact** — referenced by item 4 (continuation packet §3). Yumeichan section (§4) is intentionally thin — flagged as repo gap. Pre-call checklist includes tightening Yumeichan specifics. In subdir `Free Libre Open Source SingYouRarity/`. |
| 7 | `meta_flossioulllk_utn_3-.md` (root) | 2,163 B / 43 lines | spec | 2026-06-13 | S | UTN v0.3 specification: Uncertainty Runtime built on Furr & Furr 2022. Four-stage loop (Reframe→Prime→Do→Sustain), exit criteria per stage, balancer registry (identity/relationship/resource), key primitives (transilience, Don't Force Machinery, frontier operation, infinite-game lens), concrete logging schema. Truth-status tags applied. | `architecture/` | **Most spec-complete document in the corpus** (per item 2 synthesis). Provenance: Furr & Furr 2022 (Verified). Integration mapping to FLOSSI0ULLK/TAME/Carse = Specified. Flourishing extension = Aspirational. One of the 6 source docs the synthesis covers. Typo in filename (`flossioulllk` — triple-l). |
| 8 | `Finite and Infinite Games — James P. Carse  A Deep Reading.md` (root) | 26,736 B / 264 lines | source-text analysis | 2026-05-26 | V | Deep reading of Carse (1986): all key distinctions (finite/infinite, self-veiling, seriousness/playfulness, titles/names, power/strength, training/education, machine/garden, society/culture, explanation/narrative, evil as termination of infinite play). Includes FLOSSI0ULLK resonance mapping and 5-box compliance check. | `research/` | **V** — claims are direct quotations from the 1986 published book. Philosophical chassis for the entire corpus. One of the 6 source docs the synthesis covers. Double-space in filename. S3 URL in references is time-limited (expires). |
| 9 | `From AGI to ASI-with-annotations.pdf` (root) | 600,164 B / 57 pages | research paper (PDF) | 2026-06-19 | V | Google DeepMind (Genewein et al.) — "From AGI to ASI." arXiv paper on the AGI→ASI transition trajectory, safety considerations, capability scaling. | `reference/` | **External research** — V (published arXiv paper, DeepMind authors). Relevant to ASI safety/alignment discussions and metaharness design. Annotated version (user annotations embedded). |
| 10 | `Self-Harness Harnesses That Improve Themselves-with-annotations.pdf` (root) | 4,228,303 B / 19 pages | research paper (PDF) | 2026-06-19 | V | Shanghai AI Lab (Zhang et al.) — "Self-Harness: Harnesses That Improve Themselves." LLM-based agent harnesses that self-improve; harness = scaffolding mediating model-environment interaction. | `reference/` | **External research** — V (arXiv paper). **Directly relevant** to FLOSSI0ULLK metaharness/self-improving agent architecture. Annotated version. 4.2 MB — note size for future move considerations. |
| 11 | `Sustainability as a megatrend in business.pdf` (root) | 310,089 B / 11 pages | book chapter (PDF) | 2024-05-02 | V | Kowalska & Syrda — "Sustainability as a megatrend in business" (book chapter, Adobe InDesign). Business sustainability overview. | `reference/` | **External** — V (published). **Tangential** to FLOSSI0ULLK core; may inform governance/sustainability framing or NLnet grant narrative but no direct architectural dependency. |
| 12 | `Claude Fable 5 & Claude Mythos 5 System Card.pdf` (root) | 26,957,495 B / 317 pages | system card (PDF) | 2026-06-09 | V | Anthropic system card for Claude Fable 5 & Claude Mythos 5 (June 9, 2026). Model capabilities, safety posture, evaluation results. | `reference/` | **Reference material** — Fable 5 is the current Hermes inference surface (per workspace skill). 27 MB — large file, note for future move. |
| 13 | `Claude Mythos Preview System Card (3).pdf` (root) | 23,749,047 B / 245 pages | system card (PDF) | 2026-04-07 | V | Anthropic system card for Claude Mythos Preview (April 7, 2026). Earlier model preview. | `reference/` | **Reference material** — companion to item 12. `(3)` in filename suggests download iteration. 24 MB — large file. |

## NEVER-list flags (filter at distillation time)

1. **Lovable grand synthesis (items 2, 2b, 3)** — AI-generated synthesis; its self-applied truth-status tags and ROI scoring are useful orientation but not human-verified canon. Do not promote its recommendations into ADRs/specs without independent verification. The synthesis itself notes FLOSSIOULLK is undefined as an acronym — do not invent a definition.
2. **Continuation packet (item 4) §2** — "Fable access pulled" doctrine is **OBSOLETE**. Hermes now runs Fable-5 via Pioneer.ai API (durable, independent of Anthropic subscription windows, per workspace skill). Do not re-propagate the "Fable access on hold" claim.
3. **Yumeichan (items 1, 6)** — Yumeichan is thin/absent in repo canon. Items 1 and 6 describe Yumeichan at the vision/handoff level; do not treat either as a Yumeichan spec. A real spec needs to be authored, not improvised from these packets.
4. **agentmemory weavings (item 5)** — Perplexity export with vendor-cited benchmark numbers (95.2% recall at top-5). Treat performance claims as Unverified until independently tested. The SiYuan MCP server recommendation is concrete and actionable, though.

None of these block holding the documents; all block uncritical distillation.

## Priority queue: next highest-value distillations

1. **Reduction test for "permeable shells"** (synthesis item 2 → ROI matrix #1) — one-session thinking exercise: does the shell concept collapse to `holarchy + Holochain membranes + capability tokens + TAME light-cone`? Cheapest move that could prevent the most wasted spec effort. Output: one page, yes/no with named remainder.
2. **UTN v0.3 dogfooding** (item 7 → ROI matrix #4) — run the Reframe→Prime→Do→Sustain loop on one real FLOSSI0ULLK decision per week using the logging schema. The spec is complete; there is nothing to design. If the loop doesn't change decisions, it's decorative.
3. **Peony doula MVP definition** (synthesis → ROI matrix #7) — is it just `pony swarm + consent zomes + values-reflection prompt contract`? Read the 4 cited psych papers (Harber 2005, Schnall 2008, Pennebaker & Harber, Jussim & Harber 2005), write a one-page design note. Do not build yet.
4. **Falsifiable anti-sycophancy + anti-dependence metrics** (synthesis → ROI matrix #8) — define one measurable per invariant for any agent touching inner-shell data. Without these, "doula" is unprotected branding.
5. **Capability-token coverage audit** (synthesis → ROI matrix #14) — list every cross-shell read/write in current code; verify each goes through a capability check. "Permeability without capability gates is just a hole."
6. **Self-Harness paper digestion** (item 10 → metaharness architecture) — the Zhang et al. paper on self-improving harnesses is directly relevant to the FLOSSI0ULLK metaharness design. Extract the harness-improvement mechanism and cross-reference against existing metaharness operating model.
7. **Carse → governance vocabulary** (item 8 → governance docs) — the training/education, strength/power, machine/garden, and evil-as-silence distinctions are already referenced across the corpus; consolidate into one canonical citation home rather than scattering.

Per doc-budget discipline, items 1–5 land in EXISTING docs; items 6–7 may warrant a new reference note each.

## Follow-on constraints

- Treat all items as non-canonical until distillation lands in existing canon
  and load-bearing claims are promoted through ADR/spec pathways.
- **No files were moved in this pass.** When Anthony returns, moves require
  sha256 pre/post checkpoints and a move ledger (per 2026-06-12 precedent).
  Large PDFs (items 10, 12, 13 at 4–27 MB each) should be checked against the
  root repo `.gitignore` exclusion patterns before any relocation.
- The `FLOSSIOULLK_grand_synthesis.pdf` (no `_by_lovable` suffix, same byte
  size, 3-min-earlier mtime) is a likely duplicate of item 2b — deduplicate
  at move time.
- The continuation packet (item 4) Fable-access doctrine is obsolete; do not
  re-propagate. Check workspace skill `inference posture` for current truth.
- The Yumeichan implementation packet (item 1) and outreach brief (item 6)
  describe Yumeichan at vision/handoff level only — a real Yumeichan spec
  is a missing canon artifact, not something to reconstruct from these.
- Items 2, 3, 7, 8 form a tight cluster (the 6-source-document synthesis and
  two of its primary sources) — distill together for cross-reference fidelity.
