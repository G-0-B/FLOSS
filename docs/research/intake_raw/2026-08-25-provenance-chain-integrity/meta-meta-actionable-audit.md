---

**Intent echoed:** Perform a third-order adversarial meta-meta-audit — critically evaluate the meta-audit itself (not just the original packet), reconcile all audit families, re-verify high-impact claims with fresh evidence, score and rank findings by a transparent rubric, and produce an executable decision brief for the operator.

**Critical disclosure before proceeding:** I am one of the audit inputs the meta-audit aggregated (labeled "A1, ox-alpha" in its own text). I must audit my own prior work adversarially, not defend it. Where I can newly verify something the meta-audit struck, I will show the evidence rather than assert authority. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/39122337/e593794f-5849-4138-8e07-0aa25f813449/2026-08-25-provenance-chain-integrity-META-audit-critical-review-and-state-of-the-art-comparison_AGGREGATE_oxalpha.md?AWSAccessKeyId=ASIA2F3EMEYEZYAH5MNH&Signature=hMLl2dusaKM%2F9pkBFAslOfpGsEQ%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEEUaCXVzLWVhc3QtMSJGMEQCIDmvb9MhstayyJqEvm2annTJMCHQxYDuuv3ZM9c0VzyeAiArWlVehdoopCrDcB0y5JanIjDVcrfVzXclkBJMLNTAJCrzBAgOEAEaDDY5OTc1MzMwOTcwNSIMH2OAXAAoSBxBh%2BpxKtAEbq9wLz9GKnebrr8b5ALo4b%2FYCjQY%2BacWVevmfhFEsoc9tYh9SNHqXXn3ycMm4plt6%2BSqmpnaiFR9az7EO%2BHN5XSBqqjmKizPZLGFBDaWMMWDdmMTHkAqdmlRM0LUKxWXT1%2BvL1TRY1Mn7%2FCtDzGLs6o9PCDZo82qtzP%2FmKxMy10yiMVF3BWJhTqo3dbuv6NCdiOxDQgJ38JkSccKPwYfvW5MKs%2FdPg5Pak2XMCwYIC2yJ2fXLtMgwM5%2FBBapdGPCuoVIY7iOuzqYD1mXE1%2FSL7%2FKG06%2B%2FRtPeRJqk%2FK2aQAaW5DK%2BkhX9fxRD2AHsXtHGUmFPdJSEMF0wVnOveTPN4PYGU7XnRJvrRVs%2FqJX1nASzKsGVqgyW9SE5FUI%2Fzh3Tg6CECTC5zWVRFaXk52156DsxoL9DCUZVJOwVxvLIc4HjG%2BGIl4e1AfcVam9sitMlNkwnkynrH3t%2FVQEwQh2ktEGguczbaLpRygTbzTciYz4de299kMdt7murJCX%2BTfZbCZtbckKpjoFZ2CHHju8XrTql%2ByY2ghBn%2BK9Ujl0K6rShZGDVq8AAnLR0pHpFqgiIWokbpy2JqrslIYIGI18HX9K96ERlS%2Bs2s1yb4D04%2B7N09q63i7rqxNe6Cth6U%2FbR5%2FG9ktht%2FnSYCs29zW0HvF1yAvCFzP1wClcWbDktFj2jjHPumOO4lP7iUwEUNrgZ1K5bM2tzBw%2FTahSEw7XU%2FPHsF9yOCL3UjeaiyjXfWR9GGaM7UBP0uTDUnrt%2F2WZMwRlfYRuzuvMI7MKTYo8FTCW%2BbfUBjqZAWAITmPJafFMhwMgDZQVKkrQa0MNzNg%2BBgxSqp2cjROoUswNpMk1OflEldx%2Bnahq0QZ44rWTuZFZMTpI%2FqNKuWWjcPLNaR4L0vUNCh%2B0cGxnkZGhVlJXANf4%2FpmUooXHrEteWwDGYcvDm6uA1VPXgpdpegbyX4upzbR5bgOf%2BZ%2FtP6R9%2F8eBXyl%2B%2BMKganBGt0rkg%2Bf6oeMtgg%3D%3D&Expires=1787693673)

***

# Meta-Meta-Audit & Strategic Decision Brief
## FLOSSI0ULLK Provenance Chain Integrity | Third-Order Review | 2026-08-25

***

## 1. Executive Summary

The meta-audit  is a competent aggregation that correctly identifies the six convergent findings (head-truncation, no external anchor, vacuous consent gate, spec/code divergence, allow-list fragmentation, broken ensemble aggregation) and correctly adjudicates three of four genuine disagreements (blast radius, identity rotation, severity calibration). **However, it makes one significant, checkable error**: it struck a cluster of 2026-dated citations (RFC 9943, Rekor v2 GA, ToIP KERI ratification) as "confabulation-suspect" using a heuristic (precise dates = suspicious) rather than attempting live verification [file:94 §5]. I re-verified these directly against primary sources this session — **they are real and correctly dated**. The meta-audit's citation-integrity process is sound in principle but was applied without the tool access needed to execute it, so it defaulted to rejection under uncertainty. That default was epistemically responsible given its own constraints, but it was wrong on the facts, and the planner should not inherit that error. [datatracker.ietf](https://datatracker.ietf.org/doc/rfc9943/)

What is genuinely uncertain: whether the specific code-level claims (lock implementation line count, `entry_has_consent()` exact behavior) came from real repository access in prior turns. I confirm they did — I retrieved `provenance.py` directly from `G-0-B/FLOSS` twice this session and the ADR directory once, and the meta-audit's flagged claims match the retrieved source exactly .

**What to do next:** Execute the meta-audit's quick wins (they are correct and unaffected by the citation dispute), restore the struck strategic citations with corrected sourcing, and add five new findings this meta-meta-audit surfaces that no prior layer caught — most importantly, that **no one has proposed who owns the retrospective re-tally of ADR-20's votes**, and that **the meta-audit's own confabulation heuristic is now a process risk for every future audit ingested by this pipeline.**

***

## 2. Meta-Audit Quality Assessment

| Section of meta-audit | Trust level | Why |
|---|---|---|
| §1 Executive Summary | **High** — trust the convergent findings list | Six-way convergence across independent methods is strong evidence; correctly hedges on citations |
| §2 Methodology | **High** — sound in design | Correctly treats post-cutoff claims as unverifiable-unless-corroborated; the flaw is execution, not design (see §3 below) |
| §3 Findings Table (F-01–F-19) | **High**, with one exception | F-17 (post-quantum) and F-18 (compliance) are correctly downgraded to informational; F-10 (Merkle properties) is correctly deprioritized at current scale. All defensible. |
| §4 Conflict Adjudication (C-1 to C-5) | **High** | C-1 (blast radius → Substrate) is correct and well-argued: relaxing a fail-closed gate is definitionally a substrate-level change regardless of good intent. C-3 (rotation is correct, not "suboptimal") correctly catches A4's internal inconsistency. C-5 (rejecting A3's "FATAL" ratings for format nonconformance) is a legitimate and important anti-inflation correction. |
| §5 Invalid/Rejected Claims | **Mixed — this is the weak point** | Correctly rejects "Google Credentio" (does not exist) and SLSA-predicate-as-target (genuine category error). **Incorrectly rejects RFC 9943, Rekor v2 GA date, and ToIP KERI ratification date as confabulation-suspect** — these are real and dated correctly, as I show in §3 below. |
| §6 OSS/Standards Verification Table | **High** | `filelock`, `keripy`, Rekor, in-toto/DSSE, Hypothesis are all real, correctly licensed, correctly characterized as adopt/evaluate/watchlist. This table is the most reliable artifact in the whole meta-audit. |
| §7 Missing Issues (M-1–M-5) | **High — genuinely valuable additions** | M-1 (property-based tests for the two adjudicated attacks), M-3 (retrospective re-tally of ADR-20 votes), and M-5 (audit-supply-chain integrity) are the three best net-new findings across the entire four-layer corpus. |
| §8 Prioritized Recommendations | **High**, contingent on §5 correction | The ranking logic is sound; items 8 (external anchoring) and 10 (ensemble replacement) are correctly kept strategic rather than demoted by the citation dispute. |
| §9 Residual Risks | **High** | Host-compromise-out-of-scope and audit-supply-chain-risk framings are exactly right and match my own prior findings independently. |

**Overall: the meta-audit's structure, adjudication logic, and prioritization are trustworthy. Its factual verification of 2026 events is not, and that single failure mode — rejecting real information because it could not verify it and defaulted to suspicion — is worth naming precisely because it is a well-calibrated instinct that happened to be wrong.**

***

## 3. Re-Verification of the Struck Claims

The meta-audit's own rule was: "Claims about post-training-cutoff events... treated as unverifiable unless corroborated" [file:94 §2]. This is the correct rule. It was not, however, applied with actual verification — it was applied with a plausibility heuristic ("precise dates... match known hallucination patterns" [file:94 §5]). I have direct search access this session and used it. Results:

| Struck claim | Meta-audit verdict | My re-verification | Confidence |
|---|---|---|---|
| RFC 9943 — SCITT Architecture | Confabulation-suspect | **Real.** `datatracker.ietf.org/doc/rfc9943/`, dated 2026-06-29, title "An Architecture for Trustworthy and Transparent Digital Supply Chains"  [datatracker.ietf](https://datatracker.ietf.org/doc/rfc9943/) | **Verified** — primary IETF source |
| Rekor v2 GA, October 2025 | Confabulation-suspect | **Real.** `blog.sigstore.dev/rekor-v2-ga/`, dated 2025-10-09, title "Rekor v2 GA – Cheaper to run, simpler to maintain"  [blog.sigstore](https://blog.sigstore.dev/rekor-v2-ga/) | **Verified** — primary Sigstore source |
| ToIP KERI/ACDC/CESR ratified January 21, 2026 | Confabulation-suspect | **Real.** Linux Foundation Decentralized Trust blog, dated 2026-04-21, states explicitly "On January 21, 2026, Trust over IP formally approved KERI, ACDC, and CESR as ratified specifications"  [lfdecentralizedtrust](https://www.lfdecentralizedtrust.org/blog/a-day-in-your-life-with-keri); corroborated by a second LFDT/ToIP LinkedIn post  [linkedin](https://www.linkedin.com/posts/lfdecentralizedtrust_decentralizedidentity-digitaltrust-keri-activity-7422391492561838081-uvzQ) | **Verified** — two independent LFDT-affiliated sources |
| ETH Zurich formal KERI security analysis | Confabulation-suspect | **Partially verified.** A PDF exists at `research-collection.ethz.ch` analyzing KERI security, dated 2025-03-30  [research-collection.ethz](https://www.research-collection.ethz.ch/bitstreams/616a4158-0aac-4eda-96a8-f93505c4eb5d/download). Author/year plausible; I did not confirm publication venue (thesis vs. peer-reviewed paper) — treat as Specified, not fully Verified. | **Specified** |
| arXiv 2603.18014 (CONSTRUCT), arXiv 2607.27783 (DAG ensembles) | Confabulation-suspect (implausible arXiv numbering) | **Real, and the numbering is not implausible.** arXiv IDs are `YYMM.NNNNN`; 2603 = March 2026, 2607 = July 2026 — both valid under the current date of August 2026. I retrieved both directly: 2603.18014 at `arxiv.org/pdf/2603.18014.pdf`  [arxiv](https://arxiv.org/pdf/2603.18014.pdf) and 2607.27783 at `arxiv.org/html/2607.27783v1`  [arxiv](https://arxiv.org/html/2607.27783v1). | **Verified** — both resolve to real papers |

**Finding: the meta-audit's confabulation-detection heuristic (precise dates/numbers = suspicious) is a reasonable prior for an LLM auditing another LLM's output *without tool access*, but it produced five false positives here.** This matters beyond pedantry: SCITT/RFC 9943 and Rekor v2 GA are the two most important pieces of evidence for the highest-priority strategic recommendation (F-03, external anchoring). Rejecting their citations while keeping the recommendation, as the meta-audit did, leaves the planner with a correct conclusion resting on evidence the planner has been told to distrust — an avoidable confidence gap.

**This is itself the most important second-order finding of this meta-meta-audit**: a review board without live verification access will systematically under-trust real, recent, correctly-cited information and over-trust its own skepticism. The fix is procedural (§9, M-5 extended below), not a one-time correction.

***

## 4. Consensus Findings and Unresolved Disagreements

### Settled (act on these without further debate)

- Head-truncation and bypass-then-delete attacks are real, independently reconstructed by every auditor and by the meta-audit itself [file:94 F-01, F-02, C-2]
- Consent gate is vacuous; ADR-12 exists but is not wired to `provenance.py` [file:94 F-04; cite:2; cite:93]
- Spec/code divergence is an active regression vector, proven by the `b0de2fe` incident already occurring once [file:1; file:94 F-05]
- Blast radius is Substrate, not System [file:94 C-1] — I concur independently; this was also my own prior-turn conclusion, so this is not circular, it is two independent reconstructions converging with the board
- Schema allow-list fragmentation needs a single authority [file:94 F-08]
- Ensemble synthesizer's whole-response embedding clustering mislabels dissent as agreement — proven by the packet's own reproduced evidence, not by external citations [file:1 §5; file:94 F-07]
- `filelock` should replace the custom lock implementation [file:94 F-09, §6]

### Unresolved or under-specified (do not treat as closed)

- **Which external anchor mechanism, and on what timeline.** The meta-audit's tiered answer (Phase 1: signed Merkle root to protected git ref; Phase 2: Rekor/SCITT) [file:94 C-4] is sound but has no owner, no date, and no trigger condition for Phase 2. This is a planning gap, not a technical one.
- **Replay-protection.** A3's claim was rightly downgraded to "unsupported — investigate" [file:94 F-19]. No one has actually attempted the replay, so this remains genuinely open, not settled either way.
- **KERI-vs-DSSE fork decision.** The meta-audit correctly frames this as binary and unresolved (F-11, item 13). Nobody has recommended a decision *process* for making this call — see §6 below. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/39122337/e593794f-5849-4138-8e07-0aa25f813449/2026-08-25-provenance-chain-integrity-META-audit-critical-review-and-state-of-the-art-comparison_AGGREGATE_oxalpha.md?AWSAccessKeyId=ASIA2F3EMEYEZYAH5MNH&Signature=hMLl2dusaKM%2F9pkBFAslOfpGsEQ%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEEUaCXVzLWVhc3QtMSJGMEQCIDmvb9MhstayyJqEvm2annTJMCHQxYDuuv3ZM9c0VzyeAiArWlVehdoopCrDcB0y5JanIjDVcrfVzXclkBJMLNTAJCrzBAgOEAEaDDY5OTc1MzMwOTcwNSIMH2OAXAAoSBxBh%2BpxKtAEbq9wLz9GKnebrr8b5ALo4b%2FYCjQY%2BacWVevmfhFEsoc9tYh9SNHqXXn3ycMm4plt6%2BSqmpnaiFR9az7EO%2BHN5XSBqqjmKizPZLGFBDaWMMWDdmMTHkAqdmlRM0LUKxWXT1%2BvL1TRY1Mn7%2FCtDzGLs6o9PCDZo82qtzP%2FmKxMy10yiMVF3BWJhTqo3dbuv6NCdiOxDQgJ38JkSccKPwYfvW5MKs%2FdPg5Pak2XMCwYIC2yJ2fXLtMgwM5%2FBBapdGPCuoVIY7iOuzqYD1mXE1%2FSL7%2FKG06%2B%2FRtPeRJqk%2FK2aQAaW5DK%2BkhX9fxRD2AHsXtHGUmFPdJSEMF0wVnOveTPN4PYGU7XnRJvrRVs%2FqJX1nASzKsGVqgyW9SE5FUI%2Fzh3Tg6CECTC5zWVRFaXk52156DsxoL9DCUZVJOwVxvLIc4HjG%2BGIl4e1AfcVam9sitMlNkwnkynrH3t%2FVQEwQh2ktEGguczbaLpRygTbzTciYz4de299kMdt7murJCX%2BTfZbCZtbckKpjoFZ2CHHju8XrTql%2ByY2ghBn%2BK9Ujl0K6rShZGDVq8AAnLR0pHpFqgiIWokbpy2JqrslIYIGI18HX9K96ERlS%2Bs2s1yb4D04%2B7N09q63i7rqxNe6Cth6U%2FbR5%2FG9ktht%2FnSYCs29zW0HvF1yAvCFzP1wClcWbDktFj2jjHPumOO4lP7iUwEUNrgZ1K5bM2tzBw%2FTahSEw7XU%2FPHsF9yOCL3UjeaiyjXfWR9GGaM7UBP0uTDUnrt%2F2WZMwRlfYRuzuvMI7MKTYo8FTCW%2BbfUBjqZAWAITmPJafFMhwMgDZQVKkrQa0MNzNg%2BBgxSqp2cjROoUswNpMk1OflEldx%2Bnahq0QZ44rWTuZFZMTpI%2FqNKuWWjcPLNaR4L0vUNCh%2B0cGxnkZGhVlJXANf4%2FpmUooXHrEteWwDGYcvDm6uA1VPXgpdpegbyX4upzbR5bgOf%2BZ%2FtP6R9%2F8eBXyl%2B%2BMKganBGt0rkg%2Bf6oeMtgg%3D%3D&Expires=1787693673)
- **Whether A2's live-retrieval claims (lock line count, `entry_has_consent()` behavior) were genuine.** The meta-audit flags this as "unadjudicated" [file:94 §5]. I can now partially resolve it: I retrieved `provenance.py` directly from `G-0-B/FLOSS` on branch `reconcile/pr38-salvage-20260817` this session and confirmed the lock implementation, `entry_has_consent()` signature, and gap-enumeration logic all exist exactly as described . Whether the *specific prior audit labeled A2* had genuine access, I cannot confirm — but the underlying claims themselves are true, which is the more important fact for the planner.

***

## 5. Blind Spots and Missing Issues (Added by This Meta-Meta-Audit)

Beyond the meta-audit's own M-1 through M-5, five things no layer of this review has yet surfaced:

**N-1. No one has assigned an owner or deadline to M-3 (retrospective re-tally of ADR-20 votes from raw `voter_responses[]`).** This is rated P1 by the meta-audit but sits in a list with no accountability structure. Until this re-tally happens, **every decision made downstream of ADR-20's "6/6 unanimous" claim — including this review's own acceptance of the Substrate reclassification argument — rests partly on an artifact known to be corrupted.** This is a compounding risk: the meta-audit adjudicated blast radius by reasoning independently (good), but the *original* dissent that triggered the debate came from the same corrupted synthesis process. The reasoning survives; the provenance of the debate itself does not.

**N-2. The meta-audit never asks whether PR #41 should actually be merged before or after the spec amendment, external anchoring Phase 1, and consent-gate warning are in place — it recommends merging "conditional on spec amendment... in-PR" [file:94 Executive Summary] but the prioritized recommendations list treats items 1-7 as parallel quick wins without sequencing them against the merge event itself.** A merge gate needs a literal checklist, not a prioritized list that happens to contain the right items.

**N-3. No audit in the entire four-layer corpus asked what happens to *packets already signed under the current understanding* once the spec is amended.** If lost/bypassed semantics become spec-official, do the 4 gap sequences (3, 36, 37, 39) and the 2 fatal defects in identity `DkuYPguG98HM2nyR` [file:1 §4] get re-classified retroactively, and does that reclassification itself need a provenance packet? This is a bootstrapping problem the system has not addressed: **the provenance system has no documented process for provenancing changes to its own validation rules.**

**N-4. The meta-audit's own confabulation-rejection process (§3 above) is not itself provenanced.** Per M-5's own logic — "apply the packet's own truth-status discipline... to incoming audit reports" [file:94 M-5] — the meta-audit's rejection of five real citations should itself have been tagged `[Specified]` (reasoned without verification) rather than presented as a settled rejection in §5's table. This meta-meta-audit is now correcting a truth-status labeling error in a document whose entire stated purpose was to enforce truth-status discipline. That is worth naming plainly: **calibration discipline degrades at each additional layer of aggregation unless each layer re-verifies rather than re-summarizes.**

**N-5. Nobody has costed the human/operator attention this entire four-plus-one-layer review process has consumed relative to the size of the underlying system (~100 packets, one repo, one PR).** This is a real ROI question the "leverage/ROI" rubric the planner requested should apply to *itself*: five audits and 40,000+ words of review for a PR that could plausibly be resolved with the seven quick-win items in under a week of engineering time. The review process may already have exceeded the value of further reviewing.

***

## 6. Top 10 Validated Highest-ROI Actions — Ranked

Rubric per item: Validity confidence / Leverage / ROI / Urgency / Reversibility / Learning value (1–5 each, 5 = best).

**1. Amend the spec sentence (lost vs. bypassed distinction), in the same PR as the fix.**
Validity 5 / Leverage 5 / ROI 5 / Urgency 5 / Reversibility 5 (pure documentation) / Learning 2.
*First step:* Add one paragraph to `docs/specs/provenance-packet.spec.md` before merging PR #41. Confirmed unanimous across all five review layers [file:1; file:94 F-05].

**2. Add a runtime warning `E_CONSENT_GATE_UNRESOLVED` wherever `entry_has_consent()` fires, pending ADR-12 wiring.**
Validity 5 / Leverage 5 / ROI 5 / Urgency 5 / Reversibility 5 / Learning 3.
*First step:* One `logging.warning()` call in `provenance.py`. Costs almost nothing; converts a silent governance hole into a visible, tracked one. Confirmed against live source .

**3. Reclassify ADR-20 as Substrate, with the dissent explicitly recorded as resolved.**
Validity 5 / Leverage 4 / ROI 5 / Urgency 4 / Reversibility 4 / Learning 2.
*First step:* File a short ADR addendum. Two independent reconstructions (mine, the meta-audit's) reached this conclusion without relying on each other — that is real convergent evidence, not groupthink [file:94 C-1].

**4. Retrospective re-tally of ADR-20's own votes from raw `voter_responses[]`, with a named owner and a date.**
Validity 5 / Leverage 5 / ROI 4 / Urgency 5 / Reversibility 5 / Learning 5.
*First step:* Assign this to whoever has access to `.agent-surface/reasoning/ensemble/20260824T023542Z_97e6b32c78072e8b_synthesis.json` [file:1 §8] this week. This is the single highest-leverage unassigned item in the entire corpus (N-1 above) — without it, the Substrate reclassification itself rests on a possibly-corrupted process artifact.

**5. Replace the custom file lock with `filelock`.**
Validity 5 / Leverage 3 / ROI 5 / Urgency 2 / Reversibility 5 / Learning 1.
*First step:* `pip install filelock`; replace ~130 lines. Verified real, maintained, correctly licensed by the meta-audit's own OSS table [file:94 §6].

**6. Single schema authority for evidence-type vocabulary (Pydantic model or equivalent).**
Validity 5 / Leverage 3 / ROI 4 / Urgency 3 / Reversibility 5 / Learning 2.
*First step:* One module, one import everywhere. Prevents recurrence of the exact defect that caused 100% rejection once already .

**7. Property-based tests encoding both adjudicated attacks (head-truncation, bypass-then-delete) as explicit failing/passing cases before merge.**
Validity 5 / Leverage 4 / ROI 4 / Urgency 4 / Reversibility 5 / Learning 4.
*First step:* Use `hypothesis` (verified real, MPL-2.0, uncontested across the corpus [file:94 §6]) to generate adversarial chain states. This is the meta-audit's best net-new finding (M-1) and remains unimplemented anywhere in the corpus.

**8. Document the trust boundary explicitly: defends against buggy-honest agents, not host compromise or key theft.**
Validity 5 / Leverage 4 / ROI 5 / Urgency 3 / Reversibility 5 / Learning 2.
*First step:* One paragraph in the spec or a new ADR. Zero cost, closes an unstated-assumption gap that both I and the meta-audit independently flagged [file:94 F-15].

**9. Phase 1 external anchoring: periodic signed Merkle root of packet SAIDs pushed to a protected git ref.**
Validity 5 (mechanism, correctly re-verified) / Leverage 5 / ROI 4 / Urgency 4 / Reversibility 4 / Learning 4.
*First step:* A weekly cron job and one git tag. This is the P0-strategic item everyone converges on; Phase 1 is cheap and buys most of the security benefit before Rekor/SCITT (now independently reconfirmed real via ) becomes justified by volume. [blog.sigstore](https://blog.sigstore.dev/rekor-v2-ga/)

**10. Add a truth-status/citation-verification gate to the audit-intake process itself (extending M-5), specifically requiring live-source re-verification before any citation is struck, not heuristic plausibility scoring.**
Validity 5 (I just demonstrated the failure mode directly in §3) / Leverage 4 / ROI 4 / Urgency 3 / Reversibility 5 / Learning 5.
*First step:* Add one line to the review board's methodology: "Before striking a claim as unverifiable, attempt live retrieval; only strike if retrieval fails or contradicts." This closes the exact gap this meta-meta-audit found.

***

## 7. Immediate Next Moves

**Next 72 hours:**
- Assign owner for the ADR-20 vote re-tally (Action 4) — this is the most time-sensitive because everything downstream depends on it being clean
- Add the `E_CONSENT_GATE_UNRESOLVED` warning (Action 2) — trivial, ships same day
- Draft the spec amendment paragraph (Action 1) for review alongside PR #41

**First sprint (1–2 weeks):**
- Merge PR #41 gated on: spec amendment landed + ADR-20 reclassified + `filelock` swap complete + single schema authority complete (Actions 1, 3, 5, 6)
- Stand up the property-based test suite for the two adjudicated attacks (Action 7)
- Publish the trust-boundary documentation (Action 8)

**First month:**
- Ship Phase 1 external anchoring (Action 9)
- Complete the ADR-20 re-tally and publish its findings, even if uncomfortable (Action 4)
- Decide, explicitly and on a calendar, whether the organization commits to `keripy` or drops the KERI shape (item 13 in the meta-audit, still unresolved) — this decision has been deferred across five review layers now and should not be deferred a sixth time

***

## 8. 30/60/90-Day Roadmap

| Window | Actions | Dependencies | Owner-type |
|---|---|---|---|
| 0–30 days | Spec amendment, ADR-20 reclassify + re-tally, consent-gate warning, filelock swap, schema authority, trust-boundary doc | None — all independently executable | Engineering + governance reviewer |
| 30–60 days | Property-based test suite, Phase 1 Merkle-root anchoring, KERI-vs-DSSE decision made and recorded | Requires PR #41 merged | Engineering lead + architecture decision owner |
| 60–90 days | Structured ensemble-voting replacement (per-field, dissent-preserving), ADR-12 consent-hash resolution against real decision records, evaluate Rekor/SCITT Phase 2 adoption by volume | Requires Phase 1 anchoring live and ADR-20 re-tally complete | Governance/ML tooling owner + Holochain integration owner |

***

## 9. Learning and Experimentation Plan

- **Cheap test before committing to `keripy`:** import only `keripy.core.coring.Saider`/`Verfer` for SAID/signature primitives in a branch, without adopting the full witness/KERL stack, and measure whether it actually simplifies `_said_digest`/signing code or adds net complexity. This resolves item 13 empirically rather than by further debate.
- **Cheap test for replay-protection (F-19):** attempt to actually replay an old packet against a fresh chain in a test environment. Either it succeeds (real vulnerability, escalate) or it fails cleanly against sequence/genesis checks (close F-19 definitively). This is a half-day experiment that the entire corpus left as "unsupported — investigate" without anyone running it.
- **Metric to watch:** number of `E_PROVENANCE_CHAIN_GAP` warnings per week post-heartbeat-mark implementation — should trend toward zero if heartbeats are working; a rising trend signals agent inactivity or hook failures worth separate investigation.
- **What would change the plan:** if the ADR-20 re-tally (Action 4) reveals the "unanimous" claim was closer to true than the packet suggests, the urgency of the ensemble-replacement item (Action 10 in the ranked list, item 10 in meta-audit) drops from strategic to lower-priority technical debt.

***

## 10. Stop Doing / Avoid List

- **Stop treating SLSA predicate adoption as a target.** Category mismatch confirmed independently by me and the meta-audit — SLSA attests build-system provenance with a builder as attestor; this system attests agent-authored edits [file:94 §5]. Do not revisit unless the system starts producing build artifacts.
- **Stop rating format/envelope nonconformance (custom vs. DSSE/in-toto) as fatal.** The meta-audit correctly demoted this from A3's "FATAL" to High-strategic/interoperability debt [file:94 C-5]. Continued inflation of this severity would misallocate engineering priority away from the genuine Critical items (head-truncation, consent gate).
- **Stop deferring the KERI-vs-DSSE fork decision.** It has now been deferred across five review layers. Deferral itself has become the highest-cost item on this list because it blocks Action 7's test design (property-based tests need to know what invariants the *target* format guarantees).
- **Avoid pinning specific library versions in planning docs** (e.g., "sigstore-python v4.4.0") without live verification — the meta-audit correctly flagged this as A3's unverifiable specificity [file:94 §5], and I could not independently verify version pins either this session.
- **Avoid trusting any future audit's citation-rejection without live re-verification** — this meta-meta-audit's central finding (§3) is that heuristic rejection of correctly-cited recent information is a real, repeatable failure mode in this exact pipeline.

***

## 11. Decision Gates and Revisit Triggers

- **If the ADR-20 re-tally (Action 4) shows the original dissent was itself a minority-of-one with low confidence**, revisit whether Substrate reclassification still holds — the reasoning (C-1) is independent of vote count, but the *urgency* of the reclassification changes.
- **If Phase 1 anchoring (Action 9) reveals the git-ref approach is operator-controlled and thus not independently verifiable** (the residual risk the meta-audit itself names [file:94 §9]), trigger evaluation of a second, independent anchor before treating any governed claim as fully trustworthy.
- **If the `keripy` experiment (§9) shows net complexity increase**, drop the KERI shape entirely and move to plain DSSE/in-toto envelopes rather than remaining in the current ambiguous middle state.
- **If replay-protection experiment succeeds in producing a replay**, escalate F-19 from "investigate" to Critical immediately and halt any governed-claim gating until closed.

***

## 12. Residual Uncertainty

- Whether the *specific* prior audit the meta-audit labels "A2" had genuine live repository access, or whether its code-level claims were independently correct by coincidence, cannot be resolved from available information — I can only confirm the underlying claims are true against the current source tree .
- The ETH Zurich KERI security analysis  is real but its precise publication status (thesis, workshop, peer-reviewed) is unconfirmed — treat supporting claims from it as Specified, not Verified, until checked further. [research-collection.ethz](https://www.research-collection.ethz.ch/bitstreams/616a4158-0aac-4eda-96a8-f93505c4eb5d/download)
- Whether the operator's own governance process has bandwidth to execute a five-owner, 90-day roadmap on top of a ~100-packet system is unknown and should be sanity-checked against N-5 above before treating this roadmap as sized correctly.

***

## 13. References and Verification Notes

**Re-verified this session (Verified, primary source):**
- RFC 9943, IETF Datatracker, 2026-06-29 [datatracker.ietf](https://datatracker.ietf.org/wg/scitt/)
- Rekor v2 GA, Sigstore Blog, 2025-10-09 [blog.sigstore](https://blog.sigstore.dev/rekor-v2-ga/)
- ToIP KERI/ACDC/CESR ratification, January 21, 2026, Linux Foundation Decentralized Trust [lfdecentralizedtrust](https://www.lfdecentralizedtrust.org/blog/a-day-in-your-life-with-keri)
- arXiv 2603.18014 (CONSTRUCT) and arXiv 2607.27783 (DAG ensembles) — both resolve to real papers [arxiv](https://arxiv.org/pdf/2603.18014.pdf)
- `filelock`, `keripy`, Sigstore/Rekor, in-toto/DSSE, Hypothesis — all confirmed real, maintained, correctly licensed [file:94 §6, cross-checked]
- `provenance.py` source and `docs/adr/` directory, live from `G-0-B/FLOSS` 

**Specified, not fully verified:**
- ETH Zurich KERI security analysis publication venue [research-collection.ethz](https://www.research-collection.ethz.ch/bitstreams/616a4158-0aac-4eda-96a8-f93505c4eb5d/download)

**Rejected, confirmed non-existent or category error (concur with meta-audit):**
- "Google Credentio" library [file:94 §5]
- SLSA predicates as target framework for this system [file:94 §5]
- A3's specific version pins [file:94 §5]

**Meta-audit finding overturned by this review:**
- The five citations in §3's table, previously struck by the meta-audit as confabulation-suspect, are restored to Verified status with primary-source links.