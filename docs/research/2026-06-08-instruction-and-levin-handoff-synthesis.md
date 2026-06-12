# 2026-06-08 Instruction + Levin Handoff Synthesis (Canonical Digestion)

```yaml
id: "2026-06-08-instruction-and-levin-handoff-synthesis"
date: "2026-06-08"
type: "research_distillation"
status: "Canonical digestion for ranked queue items 1-3"
source_intake:
  - "FLOSS/docs/research/intake_raw/2026-06-08-root/reports/FLOSSI0ULLK-operating-instructions-v2.md"
  - "FLOSS/docs/research/intake_raw/2026-06-08-root/plans/PLAN-instruction-iteration-and-inventory.md"
  - "FLOSS/docs/research/intake_raw/2026-06-08-root/reports/6-5-2026-6pm_claude_HANDOFF-levin-brief-v0_4.md"
truth_status:
  source_read: "Verified"
  claim_revalidation_against_primary_sources: "Not performed in this digestion"
  implementation_changes_to_instruction_layers: "Not performed in this digestion"
```

## Why this document exists

This is the canonical synthesis for the first three ranked digestions in
`2026-06-08-root-intake-digestion.md`. It consolidates instruction-policy
changes, execution sequencing, and Levin-brief correction directives into one
small artifact to prevent note sprawl.

## Digest A — Operating Instructions v2 (what is load-bearing)

The v2 operating-instructions intake establishes six load-bearing constraints
that should govern downstream instruction surfaces:

1. **Bounded spirit-over-letter**
   - Interpret intent over literalism, except where literal precision is itself
     required (truth claims, dates, page numbers, hard ethical/safety limits).
2. **Priority stack**
   - Accuracy/safety > actionable usefulness > clarity > continuity.
3. **Anti-sycophancy**
   - Explicit disagreement and failure-mode surfacing are defaults, not optional
     style choices.
4. **Assumption discipline**
   - No buried assumptions; costly assumptions require clarification; unresolved
     questions should be carried forward and re-asked.
5. **Doc-discipline gate**
   - Smallest artifact wins; integration must clear evidence gates; the prior
     “integrate everything everywhere” behavior is explicitly rescinded.
6. **Source authority + provenance**
   - Repo/live state outranks memory/conversation; conflicts fail closed; truth
     labels and attribution are mandatory.

## Digest B — Instruction Iteration + Inventory Plan (normalized execution shape)

The planning intake is structurally sound, but it mixes proposal and execution
language. Distilled executable shape:

1. **Inventory-first verification (WS2 step 1)**
   - Verify runtime/tooling stack claims against in-repo and live surfaces
     before editing instruction layers that reference those claims.
2. **Instruction propagation (WS1)**
   - Apply v2 constraints to all instruction surfaces in minimal deltas.
3. **High-friction gate**
   - Kernel-level changes are governance-class and should be ADR/pilot gated.
4. **Reconciliation pass**
   - Any mismatch between verified system state and instruction text fails
     closed and must be corrected before promotion.

### Priority instruction surfaces (from distilled plan)

- Master metaprompt kernel (`FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md`)
- `userPreferences` surface (wherever currently authoritative)
- Perplexity instruction set (CORE + EXTENDED)
- `AGENTS.md`
- Skill manifests / instruction-bearing files in `.agent-surface/` and skills

## Digest C — Levin v0.4 Handoff (actionable correction packet)

Treat the handoff as an edit-and-verification directive for the next Levin brief
update, not as final canon by itself. Distilled mandatory corrections:

1. Chernet & Levin (2013) page range must be `595–607` (remove erroneous `555`).
2. Holochain “Landing Reliability” date must be `31 Dec 2025`; warrants status
   phrasing must remain “functional, not complete.”
3. Xenobot `600+ DEGs` claim cannot be sourced to 2020 PNAS; either re-source
   to the 2025 Communications Biology paper and verify exact count, or keep
   explicitly Unverified.
4. Promote Planarian `K ≈ 21` to Verified per cited Synthese section.
5. Promote Anthrobot DEG count to Verified (`8,992 / 22,518`) per cited paper.
6. Correct provenance attribution drift in the v0.4 packet.

## Synthesis outcome

Across the three inputs, one common operational rule emerges:

- **Verification before proliferation**: validate source authority and evidence
  first, then propagate concise updates through canonical surfaces.

This rule should anchor both instruction-layer refactors and Levin-brief
promotion to avoid repeating document-growth and provenance-drift failures.

## Immediate follow-on artifacts

1. A single inventory verification artifact (update existing state file if one
   exists; otherwise create one canonical inventory doc).
2. A minimal instruction-delta patch set across the listed surfaces.
3. Levin v0.4 canonical brief update with explicit truth labels and corrected
   provenance packet.
