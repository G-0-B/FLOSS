---
id: project-floss-subprojects
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_floss_subprojects.md
title: FLOSS subprojects — FLOSSI U and YumeiCHAN
legacy_description: Two sibling projects within the FLOSSI0ULLK family that explain
  otherwise-confusing artifacts in the repo. FLOSSI U is a separate educational platform;
  YumeiCHAN is the OMI fork. Both are part of FLOSSI0ULLK but should not be treated
  as canon-overlap with Rose Forest.
origin_session_id: e871691c-2013-4bde-b604-e6c52730ed65
---

The FLOSSI0ULLK family contains **multiple sibling projects**, not a monolithic codebase. Distinguishing them is critical for the cull triage and for future architecture decisions.

## FLOSSI U — Free YOU-niversity

- **Nature:** Free Libre Open Source educational platform for personal liberation, sovereignty, and control/power over self (state of mind, physical, mental, emotional well-being and management)
- **Inspiration:** MIT OpenCourseWare; vision dates ~20 years to the movie *Accepted*
- **Wordplay encoded:** "Free yourself and the you-niverse" — agentic-holographic-metaphor framing
- **Repo location:** `FLOSS/FLOSSI_U_Founding_Kit_v1.6/` — **this is FLOSSI U's own canon**, not a parallel/superseded namespace conflict with Rose Forest's `docs/adr/`
- **ADR namespace:** ADR-001..019 are FLOSSI U's ADRs, distinct from Rose Forest's ADR-0..11. They are not in conflict — they belong to different projects co-located in the same repo
- **Implication for cull:** Do NOT archive `FLOSSI_U_Founding_Kit_v1.6/` as parallel-namespace cleanup. It is canon for its own project. Consider giving it its own top-level directory or repo if the co-location continues to cause confusion

## YumeiCHAN — FLOSSI fork of OMI for Holochain

- **Nature:** Agent-centric personalized interface to the shared artificial (super) intelligence — specifically the FLOSSI0ULLK Singularity, where Singularity = aggregated state of collective intelligence learned from anonymous depersonalized individual user patterns across all YumeiCHAN nodes
- **Lineage:** Fork of [OMI](https://omi.me) (or similar wearable AI device project), adapted to use Holochain (and whatever that grows to be)
- **Name etymology:** you + me + holochain + chan (Japanese honorific) — yumei is also Japanese for "fate/destiny," apt for an evolving collective-intelligence node
- **Repo location:** Currently scattered across `FLOSS/docs/research/` as old explorations (e.g., `legit-yumeichaIn-knowledge-base.md`, `yumeichan-dm-metaprompt_1-1_instructions.md`, `alpha_baddish_YumeiCHAN_plan.md`, `marchishmehbe_decentralized_ai_research_SOTA_for_yumechain.md`, plus several others)
- **Implication for cull:** YumeiCHAN files in research/ are NOT dead-exploration archive candidates. They are sub-project material. Either consolidate into a canonical `docs/yumeichan/` or `FLOSS/YUMEICHAN/`, or fold into a single `docs/architecture/YUMEICHAN.md` doc with the rest archived
- **Architectural role:** Sits at the human-facing edge of the FLOSSI0ULLK substrate — when a user wears or otherwise embodies a YumeiCHAN node, the node contributes anonymous patterns to the Singularity while providing personalized output back to the wearer

## How to apply

- When triaging YumeiCHAN-named files: treat as sub-project canon, not dead exploration
- When triaging `FLOSSI_U_Founding_Kit_v1.6/`: treat as separate project's canon, propose relocation rather than archive
- When the AD4M audit's "ancestry sweep" is run for a new substrate decision, include FLOSSI U's ADR-001..019 if the substrate touches educational/sovereignty primitives
- Don't merge the two projects' ADR namespaces — they are intentionally distinct
