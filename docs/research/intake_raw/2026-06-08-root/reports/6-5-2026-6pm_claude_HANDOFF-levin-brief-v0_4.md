# HANDOFF — Levin Corpus Brief v0.4 (resume packet)

```yaml
id: "handoff-levin-brief-v0_4"
version: "1.0.0"
kind: "cold_resume_handoff"
status: "Active"
plane: "A"
created: "2026-06-05"
author_agent: "Claude (Opus 4.x), this session"
human: "Anthony (kalisam)"
purpose: "Let a fresh thread finish the corrected v0.4 brief WITHOUT re-deriving the verification."
truth_status: "Corrections below are Verified (primary-source checked this session)"
```

## State (one paragraph)
v0.3 of the Levin Corpus Integration Brief exists in **two forms**: a prose-essay version (`V0_3`, capital) and a **structured version (`v0_3`, lowercase) — this lowercase one is canonical** (YAML header, provenance chain, Claim Index §17, References). All 12 externally-checkable claims were independently verified this session against primary sources (Synthese, DMM, Oncotarget, PNAS, Advanced Science, arXiv, PMLR, Holochain blog). Result: **10 confirmed, 1 contradicted, 1 partially confirmed.** The full ledger is the session output "Independent Verification Ledger" — pull it forward as the evidence base.

## v0.4 = lowercase v0.3 + these exact edits

**Hard corrections (Verified — do these):**
1. **Chernet & Levin 2013** page range is **595–607**. Delete the erroneous "555" wherever it appears.
2. **Holochain "Landing Reliability" post**: date is **31 Dec 2025** (not 30). And the **Warrants / "immune system" is *functional*, NOT complete** — membrane-proof enforcement during handshaking is still pending. Reword any "Warrants completed in 2025" to "functional (not complete)."
3. **Xenobot "600+ differentially expressed genes"**: this figure is **NOT in the 2020 PNAS paper** (that's a design-pipeline paper). Either re-source to the 2025 *Communications Biology* xenobot-transcriptomics paper (s42003-025-08086-9) and verify the exact number there, or keep it flagged **Unverified**. Do **not** let it inherit the PNAS citation.

**Clear these UNVERIFIED flags (both checked out — upgrade to Verified):**
4. **Planarian K ≈ 21** — confirmed verbatim, Synthese §6.2 (log₁₀(6×10²⁷/3.2×10⁶) ≈ 21, ~70 bits).
5. **Anthrobot ~9,000 DEGs** — confirmed: "8,992 of 22,518 transcripts" (anthrobot life-cycle paper, PMC12376695).

**Provenance fix:**
6. The v0.3 provenance chain **mislabeled contributions** — it credited Gemini/Perplexity for structural work Claude did, because Claude was forgotten in the rotation and tags got crossed when briefs were passed between systems. Correct the attribution in v0.4's provenance packet.

## Open question to resolve in v0.4 (carried forward)
v0.3 ballooned to ~5,000 words from the **92-line v0.1**. Doc-discipline says smallest-artifact-that-does-the-job. **Decide before writing v0.4:** keep the long structured essay, or cut back to a lean brief + separate evidence appendix? (Anthony's call.)

## First action in the fresh thread
Load lowercase v0.3 + the verification ledger → apply edits 1–6 → emit v0.4 → present.
```
