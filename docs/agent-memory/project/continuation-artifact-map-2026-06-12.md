---
id: project-continuation-artifact-map-2026-06-12
type: project
created: '2026-06-12'
status: active
applies_to:
- any-agent
title: Continuation-artifact map after the 2026-06-12 alignment pass — what is live, what was consumed, what was resolved
---

## Live continuation artifacts (intentionally at workspace root)

- **Ember Seed Pack v1.0.0** — `00_MASTER_SEED.md` + files 01/02/03/05 + `ember_seed_pack_v1_0_0.zip` + `SHA256SUMS`. Install order: Step 1 (orient bootstrap) ✅ consumed 2026-06-11; Step 2 (file 01 repo reconciliation) ✅ done 2026-06-12; Step 3 (N-queue) **N1–N4 ✅ closed 2026-06-12**, N5 (spec-gate D7) + N6 (ObjectGraph spike go) still need Anthony; Step 4 — files 02 (TAME) and 03 (atomic-data hold) remain gated on their stated conditions.
- **`FLOSSI0ULLK_Context_Continuation_Packet_2026-06-09.md`** — active packet; supersede at next session boundary per its own upgrade path. Its open questions are now mostly resolved (see below).

## Consumed / relocated (do not search root for these)

The 2026-06-12 root-intake pass moved 17 files + the `mcps/` schema snapshot into `FLOSS/docs/research/intake_raw/2026-06-12-root/{reports,reference,vision}/` with sha256 ledger `.agent-surface/intake/root-intake-moves-2026-06-12.json` and digestion map `FLOSS/docs/research/2026-06-12-root-intake-digestion.md` (which also carries the N-queue closure record §4). Notables: the consumed orient-handoff twin (`context_continuation_orient_skill_handoff_v1_0_0.md`, sha `aba69142…`), the OVCA report (rejected per file-01 D1 — read that verdict before ever re-evaluating it), and `FLOSSIOULLK_ADRs_ALL_v1.0.0.md` (hallucinated reconstruction; never resolve ADR numbers against it).

## Resolutions worth not re-deriving

- **T0/T1 (repo-of-record):** local `FLOSS/` origin = `https://github.com/G-0-B/FLOSS.git`; G-0-B is Anthony's org; `kalisam/FLOSS` is the fork; the PR #21/#25 ledger lives upstream. Confirmed in-repo by the NLnet draft's applicant line.
- **T2 (Phase-0 README):** local README on `working/2026-05-25-stabilize-canon` already says "MVP Phase 0 Complete" — the stale public README is an **unpushed-branch** problem, not a content problem. Push needs Anthony (outward action, NLnet-visible).
- **NLnet:** US-individual eligibility ✅ **VERIFIED (Anthony, 2026-06-12)**. The 2026-06-01 call passed unsubmitted; current target deadline **2026-08-01**. Draft: `FLOSS/docs/research/2026-05-19-nlnet-grant-application-draft.md`.
- **N3:** `poll_high_roi_actions.py` CLI default is now `diverse`; `balanced` (2 surfaces/3 families) fails the diversity policy and is reserved for heartbeat routine polls, which pin `--profile` explicitly.
- **N4:** review-queue triage merged → `review_queue.py --triage`; `triage_review_queue.py` is a shim.
- **CONTEXT_L0/L1** are script-generated projections of `FLOSS/shared-context-surface.json` — regenerate with `python FLOSS/scripts/materialize_shared_context_surface.py`; never hand-edit them; a no-op run does not bump mtime (probe staleness is mtime-based, materializer drift-check is content-based — they can disagree).

**Why:** Multiple agents across harnesses (claude.ai web, Claude Code, Codex, Warp, Gemini) deposit continuation artifacts at root in different formats; without one map, each new session re-derives the lineage at T3 cost or — worse — re-evaluates already-rejected material.

**How to apply:** On re-entry, run the orient probe, then read the working todo list §A.00 and the latest dated digestion map before touching anything at root. Treat root drops newer than 2026-06-12 as fresh intake; everything older has a recorded verdict.
