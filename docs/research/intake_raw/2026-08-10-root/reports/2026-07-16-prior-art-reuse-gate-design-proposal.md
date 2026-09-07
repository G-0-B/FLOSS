# Prior-Art and Reuse Gate — Design Proposal (for approval, not implementation)

```yaml
id: "2026-07-16-prior-art-reuse-gate-design-proposal"
kind: "design_proposal"
status: "AWAITING HUMAN APPROVAL — nothing implemented"
created: "2026-07-16"
truth_status: "Specified (design); evidence items individually labeled"
responds_to: "2026-07-16-prior-art-reuse-gate-continuation.md (Codex packet, PR38 salvage session)"
authoring_surface: "claude-fable-5 (Cowork session)"
scope_compliance: "No edits to docs/adr/, integrity zomes, metacoordinator consensus logic, .mcp.json, settings, agent instruction files, canonical status, dirty files, or capsules. Nothing deleted, pushed, or published."
```

## 0. Intent echo

Design — not build — an enforceable gate that forces a serious adopt → extend → compose → build inquiry before infrastructure implementation, without empty bureaucracy. Triggered by PR38: a working bespoke preservation capsule that plausibly duplicates BagIt/OCFL/restic/in-toto territory. Deliverable: 2–3 gate shapes, trade-offs, a recommendation, a PR38 counterfactual, and a stop for approval.

## 1. What already exists (the gate must not be a fourth parallel invention)

The reuse principle already exists in the repo in **three partially-enforced forms**:

1. **spec_gate.py (decision D7, 2026-06-12)** — ✅ Verified live. Fail-closed `--check` over GATED surfaces (`FLOSS/scripts`, `docs/specs`, `docs/adr`); registry at `docs/specs/spec-registry.json`; advisory (never-blocking) runtime path already wired through `hook_post_write.py`. Crucially: intake mouths, research, and continuation artifacts are *definitionally exempt* — the friction lands only where canon status is claimed.
2. **SDD-Master-Spec 0.22 constitutional gates** — ⚠ Specified. "Spec-first and test-first gates," simplicity/anti-abstraction discipline, CI gates as the enforcement idea. Layer 2 explicitly frames the spec graph as "a gate to prevent redundant work."
3. **`before_build_check` (Grand Synthesis v4.0 / NANDA-Omnigent composition doc)** — ⚠ Specified, doc-only. Includes a concrete Reinvention Risk Register ("if you consider building X, check Y first") covering orchestration (Omnigent), routing (OmniRoute), discovery (NANDA), economic tracking (hREA), P2P commons (Arkology), compression (OmniRoute RTK stack), adversarial review (Polly).
4. Supporting precedent: the compliance-check habit already carries "Existing work searched before proposing new" (`pprevious_working_task.md` ~§checklist); ADR-1/RFC-001 history explicitly records that KERI/AD4M/hREA integration was **built too early without demonstrated necessity** — the exact failure mode this gate targets; `whites_resonance` analysis models the staged "adopt rather than reinvent" substitution pattern; `artifactually bridging.md` §8 gives the guiding principles (open standards, gradual adoption, maintained tech, federation, plurality).

**Design conclusion:** the gate should be the *unification and enforcement* of these three, under the existing spec_gate mechanism and the existing `before_build_check` name — not a new document class, registry, or hook.

## 2. Answers to the ten design questions

### 2.1 Trigger — which work requires the gate?

Risk-tiered, reusing spec_gate's surface logic:

- **Tier 0 (never gated):** intake, research notes, continuation packets, docs edits, config, tests, bug fixes in existing components, emergency preservation (see 2.6). Identical to spec_gate's EXEMPT surfaces.
- **Tier 1 (evidence record required):** any *new artifact* on a GATED surface that introduces a capability — new script, new package, new spec. Operationalization: the existing spec-registry stub gains a `reuse` block (see 2.2). No new artifact class.
- **Tier 2 (evidence record + independent reuse review):** architecture-class work — new storage/packaging formats, protocols, security/provenance mechanisms, new `FLOSS/packages/*`, anything that would warrant an ADR. Heuristic: if it needs an ADR, it needs Tier 2.

### 2.2 Evidence — what must a proposer show?

Extend `spec-registry.json` entries (schema addition, not a new registry) with:

```json
"reuse": {
  "capability": "one-sentence capability statement",
  "search_date": "YYYY-MM-DD",
  "evidence_window_days": 90,
  "candidates": [
    {"name": "", "version": "", "license": "", "maintenance": "",
     "platform_fit": "", "probe": "result | not_probed: <reason>",
     "truth_status": "Verified|Specified|Unverified"}
  ],
  "verdict": "adopt|extend|compose|build",
  "irreducible_delta": "what remains custom, stated as capability subtraction",
  "rejected_because": ["requirement-by-candidate gaps, each with truth status"],
  "reviewer": "model-family + surface, distinct from proposer (Tier 2)",
  "expiry_or_retest_date": "YYYY-MM-DD"
}
```

The `expiry_or_retest_date` field deliberately mirrors the ADR-17 open-review fields (`valid_context`/`known_failures`/`expiry_or_retest_date`) so the two conventions converge rather than fork.

### 2.3 Decision model — adopt/extend/compose/build without VC framing

A burden-of-proof ladder, not a cost-benefit spreadsheet: **adopt** is the default verdict; each step rightward (extend → compose → build) requires the proposer to show, with per-candidate truth status, why the previous rung fails a *stated requirement* (not a preference). Alignment with `artifactually bridging.md` §8 principles is the tiebreaker (open standards, maintained, federated, plural) — not time-to-market or differentiation language.

### 2.4 Irreducible delta

Stated as subtraction: requirements matrix rows minus best-composition coverage. The delta must be (a) expressible in ≤5 sentences, (b) testable, (c) consistent with the packet §6 hypothesis form. If the delta can't be stated as a failing test against a probed candidate, the verdict cannot be `build`.

### 2.5 Enforcement surface — least invasive effective composition

**Recommended: Shape B+C hybrid (see §3), implemented entirely on existing machinery:**

- Audit path: `spec_gate.py --check` extended to fail closed when a Tier-1+ artifact lacks a `reuse` block. One schema field + one validation branch in an existing script.
- Runtime path: the *already-wired* advisory `hook_post_write` note gains the reuse reminder. Advisory only; never blocks — unchanged behavior contract.
- Tier-2 review: routed through the existing consensus gateway voter roster (cheap heterogeneous critics first, per the metaharness allocation policy), with the reviewer drawn from a **different model family than the proposer** — the Polly pattern, which is already the repo's anti-sycophancy invariant. The reviewer's task is adversarial: *attempt to replace the proposal with existing systems.*
- Explicitly rejected: new CI infrastructure (nothing to run it on yet), a standalone checklist doc (Shape A — gameable), a new hook (duplicates hook_post_write), prompt-only enforcement (violates the data-centric-policy lesson from Omnigent).

### 2.6 Emergency exception

Preserve-first action is always permitted when delay risks data loss (PR38's actual situation). The exception is recorded as `"emergency": true` in the registry entry, and the gate then fires at **generalization/promotion time**: no emergency artifact may be productized, promoted toward canon, or reused as a dependency until a retrospective reuse audit completes. This cleanly separates "the capsule run was right" from "salvage_spine as infrastructure needs the gate."

### 2.7 Anti-gaming

- **Probe-or-justify:** Tier-2 `build`/`compose` verdicts require at least one *direct probe* (candidate actually executed against a real requirement) — docs-reading alone cannot reject a candidate. Untested incompatibility claims are marked ⚠ Specified and cannot justify `build` on their own.
- **Freshness:** evidence older than `evidence_window_days` fails `--check` for new dependents.
- **No post-hoc self-justification:** if code exists before its reuse record, the record must be authored by a different surface/model family than the code's author, and say so.
- **ACON-style guideline loop (operator-endorsed 2026-07-16):** the gate's search protocol and evidence requirements live in one guideline doc. Every discovered *gate miss* (duplication found after the fact — PR38 is retroactively the first case) becomes a failure trace that refines the guidelines, exactly as ACON refines compression guidelines from failure analysis: natural-language-space optimization, no weights, near-zero cost. The Reinvention Risk Register from the NANDA/Omnigent doc is the guideline seed.

### 2.8 Truth status

Per-candidate and per-claim labels are mandatory in the `reuse` block (schema above). A capability may only be cited as covered/not-covered at ✅ Verified after a probe; everything else is ⚠ Specified or ❌ Unverified. This inherits the ADR-Suite v2.0 discipline unchanged.

### 2.9 Lifecycle

`expiry_or_retest_date` plus re-scan triggers: dependency major-version change, standard revision (e.g., OCFL v2 landing), platform change, or requirement change. Re-scan is a registry update, not a new document.

### 2.10 Salvage disposition (recommendation, gated on probes)

**Decompose toward standards; retain the semantic layer; convert tests to acceptance tests.** Specifically — all ⚠ Specified until probed:

- **Retain as FLOSSI0ULLK-specific (packet §6 hypothesis, provisionally supported):** semantic evidence planes; index/tracked/untracked/ignored distinctions; disposition vocabulary (copied/metadata-only/redacted/excluded/opaque); private-preservation vs. publication separation; fail-closed projection gates. Live check today confirms none of BagIt/OCFL/restic/in-toto express these.
- **Migrate candidates:** payload packaging/fixity → BagIt (RFC 8493) or OCFL 1.1 object layout; snapshot storage/dedup/encryption → restic **after a Windows probe** — restic's own FAQ carries "Why does restic perform so poorly on Windows?" (verified live 2026-07-16, docs v0.19.1), so Windows performance is exactly the untested incompatibility the gate forbids assuming in either direction; step attestation/authorized-steps → in-toto layouts + link metadata (verified live: layout/functionary/artifact-rule model maps directly onto capture→seal→verify→restore steps and onto Claim-shaped provenance).
- **Convert:** salvage_spine's validation suite becomes the interoperability acceptance test set that any composed replacement must pass (packet §7.10's best option).
- **Do not** rewrite the working capsule now — it is emergency-tier output. The gate fires if/when salvage_spine is generalized.

## 3. The three gate shapes, compared

| | A. Checklist doc | B. Machine-readable evidence + spec_gate | C. Independent reuse review |
|---|---|---|---|
| Cost per use | ~0 | Low (one JSON block) | Medium (one adversarial review) |
| Gameable? | Trivially | Partially (fields can be shallow) | Hard (reviewer tries to replace the work) |
| New machinery | None | One schema field + validation branch | None (existing voter roster) |
| Blocks? | Never | Fail-closed at `--check`, advisory at runtime | Blocks Tier-2 promotion only |
| Failure mode | Ignored | Checkbox compliance | Cost creep, review theater |

**Recommendation: B as the floor for Tier 1, B+C for Tier 2.** A alone is rejected (the repo's own history shows principles-without-enforcement didn't stop PR38-style duplication). C alone is rejected as too expensive for routine work. B+C reuses spec_gate, hook_post_write, the consensus gateway, and the diversity policy — zero new components, which is itself this gate passing its own test.

## 4. PR38 counterfactual (acceptance criterion §9.2)

With the gate live: the emergency capture proceeds untouched (2.6). At the moment "capsule" became a *designed system* (manifest format, fixity, sealing, cleanroom restore — i.e., Tier 2 architecture-class work), `--check` fails closed without a `reuse` block. The evidence record would have surfaced BagIt/OCFL/restic/in-toto within one search round (all are first-page results for their capability statements). Probable honest verdict: **compose** — standard payload packaging + in-toto-shaped attestations + custom semantic-plane/disposition/projection layer. Estimated effect: the custom surface shrinks to roughly the packet §6 list, and the unresolved `mtime_ns` race lands in maintained upstream code's problem domain (restic's change detection) rather than ours. This is a counterfactual estimate, ⚠ Specified — the point is the sequence change, not the exact LOC saved.

## 5. Falsifiers for the gate itself (acceptance criterion §9.7)

The gate should be **retired to a plain checklist** if, after ~6 months of operation:

1. It fires on fewer than ~5 proposals total (not enough infrastructure work to justify machinery), or
2. Its verdicts never differ from what the proposer intended anyway (measure: verdict-changed rate ≈ 0), or
3. Median time spent per Tier-1 record exceeds ~10% of implementation effort (bureaucracy exceeds value), or
4. Hook-log evidence shows agents already reliably search-first without it.

Additionally, if the gate itself required new infrastructure to build, that would be self-refuting; the recommended shape requires none.

## 6. What implementation would touch (for scoping only — NOT authorized)

One guideline doc (seeded from the Reinvention Risk Register), a `reuse` schema addition to `spec-registry.json`, ~30 lines in `spec_gate.py`, one advisory-string change in `hook_post_write.py`, one Tier-2 review prompt for the voter roster. No ADR edits, no integrity-zome, no consensus-logic changes. An ADR *recording the gate decision* would be appropriate at approval time — that is a human-gated step per convention.

## 7. Open questions carried forward (answer piecemeal as convenient)

1. Approve shape B+C as recommended, or Tier-1-only (B) to start?
2. Should the Tier-2 reviewer requirement wait until the voter-roster prompt exists, with human review as interim?
3. Is 90 days the right evidence window?
4. Restic-on-Windows probe: authorize as the first gate-driven probe (it also de-risks the 9 GB-copy problem the packet flags)?

## 8. Self-audit

Sources actually read: continuation packet (uploaded), NANDA/Omnigent composition doc (uploaded), packet §4 sources at the cited line ranges, `spec_gate.py` (read-only), SDD-0.22 gate sections (grep), PR38 task-10 operator report (head). Live primary sources fetched 2026-07-16: restic stable docs, ocfl.io, in-toto getting-started. Not refreshed: BagIt RFC 8493 (stable informational RFC, low drift risk), RO-Crate, DataLad, Borg, Archivematica, Software Heritage, Guix — **must be refreshed before any implementation verdict relies on them.** No hard-stop surface touched; nothing deleted, pushed, or published; no implementation begun.

**Stopping here for approval per packet §2 and §11.8.**
