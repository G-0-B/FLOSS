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

- Master metaprompt kernel (`FLOSSI0ULLK_Master_Metaprompt_v1_4_0_Kernel.md`)
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

## Digest D — Navigating the Infinite (queue item #10, digested 2026-08-31)

**Source:** `intake_raw/2026-06-08-root/reports/Navigating the Infinite  Cognitive
Light Cones, Universal Flourishing, and the Geometry of Intelligence.md`
(sha256 `47e5e028d25e71068cebe234d187be48fd0150aac128e20c9f8efc7b2a22adf0`,
33,392 bytes, 219 lines, 6 parts, 13 references).

**Digest target, from the batch map:** separate rhetoric from load-bearing
design claims; map only actionable claims to architecture/governance artifacts.

### D.1 — A definitional drift the report introduces

The report's lead definition (2.1) reads: the cognitive light cone is the
spatiotemporal boundary of everything an agent can *perceive, model, and attempt
to control*.

Levin, asked directly, excludes both of those. In conversation with Lex Fridman
(#486, transcript in `_reference/transcripts/`) he defines it as the scale of the
largest goal state an agent can actively pursue, then rules out sensory reach and
causal reach by name — his example being that the James Webb telescope has vast
sensory reach and a tiny cognitive light cone. The report's own reference stub
for TAME carries the goal formulation (Selves are defined by the spatio-temporal
scale and nature of the types of goals they can pursue), so both versions are
present in the document and the perceptual one is the one it leads with.

This is not a wording preference. The two definitions imply different
measurements: perception points at inputs, goal-scope points at what a system
will work to bring about, and Levin's measurement protocol (interpose a barrier,
measure the ingenuity of the detour) only makes sense under the second.

**Disposition:** record the goal-scope definition as the one this workspace uses,
and treat this report as a secondary source that broadened it. The correction is
written up in
[`2026-05-26-levin-corpus-cces-implications.md`](2026-05-26-levin-corpus-cces-implications.md),
the canonical Levin home. Not asserting this report as the *origin* of the drift
— it is the earliest copy found in-repo, which is weaker than a causal claim.

### D.2 — Load-bearing: the Positive Alignment governance list

The most actionable content is not the light-cone material at all. Section 5.3
enumerates five governance mechanisms from *Positive Alignment* (arXiv
2605.10310, Laukkonen et al. 2026 — **primary PDF already on disk** at
`_reference/ai-ml/2605.10310v2_...pdf`, so cite the paper, not this report).
Mapped against what FLOSSI0ULLK actually has:

| Positive Alignment mechanism | FLOSSI0ULLK status |
|---|---|
| Agent identity, registration, records | **Present** — file-based source chain + Claim/Vote provenance (ADR-10) |
| Versioned, modular model constitutions | **Present** — the ADR suite with truth labels is exactly this |
| Pluralistic alignment frameworks | **Present** — analog votes in [-1,+1] and the >=3 surface / >=4 family diversity policy preserve disagreement rather than collapsing it |
| Collectively authored constitutions | **Absent** — ADRs are authored by whoever is at the keyboard; the consensus gateway ratifies, it does not co-author |
| Role-based normative standards | **Absent** — no context-sensitive normative differentiation by agent role exists |

A grep for `model constitution` / `collectively authored` across `docs/` returns
hits only inside undigested intake, which corroborates the two Absent rows.

That table is this digest's main deliverable: three mechanisms already built
without reference to this literature, and two genuine gaps. Neither gap is
proposed for action here — naming them is the digestion; promoting them needs an
ADR.

### D.3 — Load-bearing: consented guidance vs technocratic imposition

Section 5.2's distinction — a system helping a user reach *their own*
higher-order goals, versus a system deciding what flourishing means on their
behalf — lands on a live thread rather than a hypothetical one:
[`ADR-12-consent-gate-protocol.md`](../adr/ADR-12-consent-gate-protocol.md). The
paper supplies external framing and a named failure mode (6.3: positive alignment
otherwise collapses into paternalism) for a protocol the project already has.
Cross-reference; do not restate.

### D.4 — Load-bearing at a different layer: functional compression

Part III argues that bounded representation is the enabling condition for
actionable intelligence rather than a defect to regret. That is a real constraint
on Layer 2 (semantic/embedding) and on context routing, and the strongest
available justification for `context_router.py` returning a small ranked set
rather than more context.

Caveat limiting how far it can be leaned on: the neuroscience half is solidly
sourced (Science Advances, subiculum manifolds); the ATIC and Rockell material is
unrefereed PhilArchive preprints.

### D.5 — Rhetoric (recorded as read, not promoted)

- **Part IV, Carse's infinite games.** Elegant and consonant, but it yields no
  decision procedure the north-star load-bearing test in `CLAUDE.md` does not
  already provide. Optimise-for-continued-play cannot adjudicate a concrete
  trade-off.
- **Section 6.2, three-angles-on-the-same-thing.** An aesthetic claim, and as
  written unfalsifiable: no observation is specified that would show an infinite
  player and an expanded light cone are *not* the same thing.
- **The conclusion.** Restates 6.1.
- **Section 6.3, multi-AI disagreement.** Speculation about which vendor models
  weight governance versus user agency, offered without evidence. Worth noting
  that this workspace can *test* it: the consensus gateway routes one Claim to
  voters spanning >=4 model families and records analog weights. Converting this
  bullet into a probe is the one thing in Part VI that would produce new
  information rather than restate existing framing.

### D.6 — Provenance defects in the source, recorded so it is not re-cited as-is

The report's strong claims rest on solid sources and its *distinctive framing*
does not:

- Refs 5, 8, 10 are expired AWS presigned URLs to Pieces copilot message exports
  — not durable, not citable. Ref 10 is worse than dead: it points at a
  FLOSSI0ULLK SDD master specification, so the report cites this project as
  external support for its open-ended-evolution claim. Circular.
- Refs 6 and 9 (Rockell) are unrefereed PhilArchive preprints.
- Refs 4 and 5 (Evolution Labs, Cognitive Capoeira) are blog-tier, and they carry
  the report's most quotable lines — exosomatic gap junctions, social organs as
  the gap junctions of civilization, the metacrisis-as-contraction reading. Those
  are the phrases most likely to be repeated and the least sourced.
- Refs 1, 12, 13 (Positive Alignment), 2 and 3 (Levin 2019 Frontiers; TAME), and
  7 (Science Advances) are sound. Every load-bearing item above (D.2, D.3, D.4)
  rests only on these.

**Disposition:** the report stays in `intake_raw/` and is not promoted. Cite the
primaries directly. Queue item #10 is closed by this digest.

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
