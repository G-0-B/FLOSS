---
id: "flossi0ullk-canonical-build-spine"
version: "0.3.0"
kind: "canonical_build_spine"
status: "Proposed"
truth_status: "Specified"
date: "2026-07-16"
supersedes:
  - "FLOSSI0ULLK_CANONICAL_BUILD_SPINE_v0.2.md"
  - "FLOSSI0ULLK / ARF / Symbiotic Singularity — Merged Upgradeable Artifact v1"
  - "Rose Forest Merged Artifact v1 — Adversarial Verification and Corrections"
evidence_sources:
  - "Live repo fetch, G-0-B/FLOSS @ main, 2026-07-16 (CLAUDE.md, README.md, MVP_PLAN.md, SDD-Master-Spec-0.22.md, ARF/docs/arf_sdd_master_spec.md, LICENSE, docs/adr/INDEX.md + all ADR files, docs/specs/phase0-substrate-bridge.spec.md, docs/governance/* full directory, packages/orchestrator/*.py)"
  - "arf_sdd_master_spec.md as uploaded by user this session (byte-identical to ARF/docs/arf_sdd_master_spec.md)"
  - "Claude project-knowledge memory snapshot, this conversation, 2026-07-16"
upgrade_path:
  - "Amend by PR only"
  - "Update source register, contradiction log, and phase gates when evidence changes"
  - "Promote to Accepted after repo-maintainer review"
rollback_plan: "Revert this file and LOADING_ORDER pointer to v0.2; no runtime behavior changes."
friction_tier: "medium"
---

# FLOSSI0ULLK Canonical Build Spine v0.3

## 0. Executive decision

**Decision: +1 proceed — adopt this v0.3 as the current contradiction-resolving execution spine, superseding v0.2. 0 hold on the two items that require Anthony's direct decision (license posture, SDD-spec dual-naming) before any file is actually renamed or a license is actually chosen.**

v0.2 (2026-07-02, authored by a GPT-5.5 Thinking session) already did most of the hard work of reconciling the Phase 0 completion contradiction, the GitHub/Radicle canonical question, and the license risk. That work holds and is preserved below unchanged. This revision adds five new contradictions this session found by reading the live repo directly (`CLAUDE.md`, ADR INDEX, the actual `packages/orchestrator` consensus-gate code, and the LICENSE file byte-for-byte) that v0.2 did not catch, because v0.2 relied on the same repo-local sources without diffing them against each other line-by-line.

**The single most important meta-finding:** most of what looked like "Claude's memory is stale" is actually "a prior session already wrote the correction on 2026-07-02, and it hasn't fully propagated to every doc it should have updated." This is not a memory problem — it's a **propagation** problem. See §5, C6–C10.

One-sentence build spine (unchanged from v0.2):

> Build a local-first, spec-driven, provenance-rich agent memory and knowledge-validation loop; prove it with tests and audit logs; then progressively move only the parts that benefit from decentralization into Holochain and optional sovereignty layers.

---

## 1. Authority and precedence

Unchanged from v0.2. This file is a current-state execution spine. It does **not** outrank the Kernel, Project Spine, SDD master specification, ADRs, contracts, schemas, tests, or signed results.

1. Kernel / mandatory coordination rules
2. Project Spine / governance invariants
3. SDD master specification
4. UpgradableArtifact schema and lints
5. Governance protocols
6. This canonical build spine as current execution synthesis
7. ADRs / RFCs
8. Contracts / Schemas
9. Tests and signed results
10. Code
11. Synthesis / analysis docs

**New note (v0.3):** `CLAUDE.md` is not in this precedence chain at all — it is a repo-navigation aid for agentic readers, not a governance artifact. That is precisely why it was able to drift out of sync with this spine's C2 resolution (see C6 below) without anything formally flagging the conflict. Recommend `LOADING_ORDER.md` add a line noting `CLAUDE.md` is descriptive, not normative, so future readers don't accidentally treat it as tie-breaking authority.

---

## 2. Source register

Unchanged from v0.2 §2, with one addition:

| Source | Role | Current posture |
|---|---|---|
| `docs/adr/INDEX.md` (v2.0.0, updated 2026-05-25) | ADR truth/status surface | **Already resolves** the ADR-numbering conflict that Claude's memory still listed as open. Adds ADR-12 (Consent Gate Protocol, 2026-05-19) — not yet reflected in `CLAUDE.md`. |

---

## 3. Evidence classes

Unchanged from v0.2 §3.

---

## 4. Current reality check

Unchanged from v0.2 §4.1–4.2. Still accurate as of this revision — nothing in this session's fetch contradicted it.

---

## 5. Contradiction log

**C1–C5 unchanged from v0.2** (Phase 0 completion language, GitHub-vs-Radicle-canonical, spec-first vs retroactive implementation, vision language vs acceptance criteria, license/funding contradiction). See v0.2 for full text. C5 is **extended**, not replaced, by C7 below — the picture is worse than v0.2 knew.

### C6 — `CLAUDE.md` still claims Radicle-canonical; this spine already resolved that as GitHub-canonical

**Conflict:** `CLAUDE.md`'s "Current Operating Stack" section states: *"Canonical dev-plane code substrate: Radicle... GitHub remains a pragmatic mirror, not the architectural center."* This directly restates ADR-8's proposal as settled fact. But this spine's own §C2 (2026-07-02, two weeks more recent than `CLAUDE.md`'s last visible update) already resolved this the other way: *"Current: GitHub canonical... Radicle-canonical remains a sovereignty target, not current fact."*

Two committed, simultaneously-live documents assert opposite answers to "what is the canonical dev substrate right now." Anyone loading `CLAUDE.md` first (which `LOADING_ORDER.md` does not actually route them to before this spine — but `shared-context-surface.json`'s `canon` corpus lists both at similar priority) gets the wrong current-state answer.

**Resolution:** This spine's C2 resolution stands — it is the more recent, and it is the file whose explicit job is contradiction resolution. `CLAUDE.md` should be patched to read Radicle as the *target*, not the *current* substrate. See the companion patch note delivered alongside this file.

**Decision:** +1 patch `CLAUDE.md` (low friction, docs-only, no runtime change).

### C7 — Three-way license conflict (extends C5)

**Conflict:** v0.2's C5 flagged that README says "Compassion Clause + Apache-2.0/GPL-compatible" and that this may create OSI/FSF funding friction. This session found the conflict is worse than a two-way tension between README wording and funder expectations — it is a **three-way disagreement between three different files, all currently committed**:

1. Root `/LICENSE` — plain **GNU GPLv3** text, verbatim FSF boilerplate. No AGPL network clause. No Compassion Clause rider present as a file.
2. `FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md` header + `README.md` footer — **"Compassion Clause + Apache-2.0/GPL-compatible."**
3. `docs/adr/ADR-7-agpl-cascade.md` ("Embracing AGPL-3.0 Copyleft Cascade," Accepted, 2026-04-15) + `docs/governance/LEGAL_DEFINITIONS.md` ("Carrier Equivalence Addendum") — **AGPL-3.0-or-later** governs, with the addendum explicitly subordinate to it.

None of these three matches either of the other two. The root `LICENSE` file — the one that is legally operative regardless of what any markdown file says — is GPLv3, not AGPL and not Apache-dual. ADR-7 postdates the current `LICENSE` file's apparent content and was never applied to it.

**Resolution:** This cannot be resolved by an AI reading docs — it requires Anthony to state which license is actually intended, then one PR that makes `LICENSE`, the Kernel header, `README.md`, and `LEGAL_DEFINITIONS.md` agree. Until then, **do not cite any of the three as "the license"** in any external-facing context (funding applications, npm/crates.io metadata, GitHub Pages footer) — cite "license posture under active reconciliation, see C7."

**Decision:** 0 HOLD — escalated to NOW backlog (§8) as a direct question, not resolved here.

### C8 — Two documents both claim to be "the SDD Master Spec"

**Conflict:** `ARF/docs/arf_sdd_master_spec.md` (v0.1, no date header, FR/AC/contract-heavy, defines Feature 000 "SDD Tooling" and Feature 001 "Identity & Membership" complete with JSON Schemas and a working Rust skeleton) and root `SDD-Master-Spec-0.22.md` (v0.2-rc1/"Synthesis," dated 2025-11-07, narrative prose describing a 7-layer architecture — RICE, NormKernel, MetaLoop, YumeiCHAIN — that does not appear anywhere in v0.1) are **structurally unrelated documents that happen to share a name and a rough version lineage**. `CLAUDE.md`'s directory map lists both but its "Key Entry Points" section names only the root one as *the* SDD spec.

This is a direct, in-repo violation of the project's own stated convention: *"One canonical version per document — duplicates are the enemy"* (`CLAUDE.md`, Conventions).

Neither document should simply be deleted:
- v0.1 is the only place in the repo with an actual FR→AC→contract→test→code chain for the SDD tooling itself (`/new_feature`, `/generate_plan`) — work explicitly still open per this spine's own NOW backlog item 4 ("Implement or expose SDD CLI scaffolds").
- v0.22 is the only place holding the higher-level architectural narrative (7-layer stack, NormKernel, RICE) that other docs (Kernel appendix, `context-compression-v1.1.md`) point to.

**Resolution (recommended, not yet applied):** Rename v0.1 out of the "Master Spec" naming collision — e.g. `docs/specs/sdd-tooling-and-identity-feature-spec-v0.1.md` — add a one-line cross-reference header pointing to `SDD-Master-Spec-0.22.md` for the architectural frame, and update `CLAUDE.md`'s directory map + Key Entry Points to list both with their now-disambiguated roles. This is a rename + cross-link, not a content deletion.

**Decision:** +1 rename/cross-link (low friction — file move + two doc edits, no content lost) once Anthony confirms the target filename.

### C9 — Kernel's ternary decision model vs. the live consensus-gate code's analog model

**Conflict:** Kernel v1.3.1 §5 and this spine's own Phase 2 gate (§7) describe decisions as discrete `{-1, 0, +1}`. The actual, tested implementation in `packages/orchestrator/claim_schema.py` and `consensus_gate.py` explicitly **forbids** integer ternary votes — its own docstring states *"Ternary {-1, 0, +1} integer values are forbidden"* — and instead tallies continuous float votes in `[-0.999, 0.999]` via per-blast-radius mean/variance thresholds into **five** outcomes: `APPROVED / REJECTED / DEFERRED / CONFLICT / OVERRIDDEN`. The code's own comment explains the reasoning: *"The old ternary model allowed a single -1 to veto substrate changes. The analog model requires quorum=3 AND mean < θ_reject..."* — this is a deliberate, documented architectural upgrade, not a bug.

ADR-6 ("Four-System Meta-Orchestration Integration"), which should own this decision, is still marked `Truth Status: Specified (Seam 1 partial)` per `docs/adr/INDEX.md` — meaning even the ADR record hasn't formally caught up to what the code already does.

This matters beyond pedantry: Claude's own operating contract with Anthony (`userPreferences`) uses the Kernel's ternary framing for every substantive reply's Decision line. That framing is fine as a *human-facing* heuristic and does not need to match the machine gate's internal math — but the gap should be documented, not silently divergent, so a future reader of ADR-6 isn't misled into thinking the gate is still ternary.

**Resolution:** Do not change the Kernel's human-facing ternary contract (no NOW pain motivates that). Do add one sentence to ADR-6 (or a short addendum) noting the analog gate exists in `packages/orchestrator` and is the actual mechanism when that package is invoked.

**Decision:** 0 hold on Kernel change; +1 NOW on the one-sentence ADR-6 note.

### C10 — Phase 0 substrate-bridge spec references a Holochain line that no longer exists

**Conflict:** `docs/specs/phase0-substrate-bridge.spec.md` (2026-03-25, still `Specified`, all Definition-of-Done boxes unchecked) lists its prerequisite as *"Holochain conductor running (holonix main-0.4)."* The active substrate migrated to `hdi 0.7.1 / hdk 0.6.1` (holonix `main-0.6`) on 2026-05-19 (commit `7e6d4e5`), confirmed independently by `CLAUDE.md`, `MVP_PLAN.md`, and this spine's own C1. This spec — which this spine's own Issue 5 names as the next concrete gate to close — will send whoever executes it hunting for a Holochain version that predates the current workspace `Cargo.toml`.

**Resolution:** One-line edit: `holonix main-0.4` → `holonix main-0.6` (or better, remove the pinned version reference entirely and point at the workspace `Cargo.toml`, so this doesn't go stale again on the next substrate bump).

**Decision:** +1 NOW — trivial, prevents wasted debugging time on the next attempt to run this spec.

### Minor items (not full contradiction-log entries, low friction, batch with the above)

- `docs/adr/INDEX.md` lists **ADR-12** (Consent Gate Protocol, `Draft (implementation-backed)`, high friction, `OVERRIDE FORBIDDEN`) as active; `CLAUDE.md`'s ADR summary line still says *"current set per v2.0 suite is ADR-0, 0.1, 1–11"* — one-word fix, add "12."
- `docs/governance/context-compression-v1.1.md`'s own precedence header still names "Kernel v1.2" as the authoritative rules file it companions, but `LOADING_ORDER.md` has moved to Kernel v1.3.1. Low priority — the packet's content (the Love/Light/Knowledge transmutation dictionary) is not itself stale, only its self-referential pointer.

---

## 6. The canonical build spine

Unchanged from v0.2 §6.

```text
Human intent / project memory
  -> SDD feature spec
  -> contracts and tests
  -> local ConversationMemory + source register
  -> minimal policy/provenance gate
  -> Holochain substrate compile/pack/install proof
  -> KnowledgeTriple / ontology Phase 1
  -> agent orchestration via MCP/local router
  -> optional sovereignty modules only after measured need
```

---

## 7. Phase gates

Unchanged from v0.2 §7 (Phase -1 through Phase 3). No new evidence this session changed any gate's pass/fail status. Phase -1 ("Canonicalization gate") is **still open** — C6–C10 are exactly the kind of contradictory project state it was meant to stop from multiplying, and they multiplied between v0.2 (2026-07-02) and this fetch (2026-07-16) simply because nothing re-ran the sweep in the interim.

---

## 8. NOW / LATER / NEVER backlog

### NOW (v0.2's list, unchanged, plus five new items)

1. Create and link this canonical build spine. *(v0.2 — carry forward: link v0.3, not v0.2, from `LOADING_ORDER.md`.)*
2. Reconcile README phase wording with `MVP_PLAN.md`. *(v0.2 — still open; not checked by this session.)*
3. Fix or document `ConversationMemory` / `MultiScaleEmbedding` API mismatch. *(v0.2 — still open.)*
4. Implement or expose SDD CLI scaffolds. *(v0.2 — still open; note C8 renames the spec this depends on.)*
5. Make one Holochain substrate test path reproducible. *(v0.2 — still open; C10 is a sub-blocker.)*
6. Create `SOURCE_REGISTER.md` and `EVIDENCE_LEDGER.md` if not already present. *(v0.2 — not verified present or absent this session; check before creating, to avoid C8-style duplication.)*
7. Add a contradiction-log update process to PR template or governance docs. *(v0.2 — still open.)*
8. **(new, C6)** Patch `CLAUDE.md`'s "Canonical dev-plane code substrate" line to match this spine's GitHub-canonical resolution.
9. **(new, C7)** Get Anthony's explicit license decision; then align `LICENSE`, Kernel header, `README.md`, `LEGAL_DEFINITIONS.md` in one PR.
10. **(new, C8)** Confirm rename target for `ARF/docs/arf_sdd_master_spec.md`; execute rename + cross-link + `CLAUDE.md` update.
11. **(new, C9)** Add one-sentence analog-gate note to ADR-6.
12. **(new, C10)** Fix `holonix main-0.4` → `main-0.6` in `phase0-substrate-bridge.spec.md`.

### LATER / NEVER

Unchanged from v0.2 §8.

---

## 9. Issue backlog draft

v0.2's Issues 1–6 unchanged and still open. Add:

### Issue 7 — Patch CLAUDE.md dev-substrate claim (C6)

**Decision:** +1 NOW

Acceptance criteria:
- `CLAUDE.md`'s "Canonical dev-plane code substrate" line reads Radicle as target/aspirational (ADR-8, Specified), GitHub as current canonical, cross-referencing this spine §C6.

### Issue 8 — License reconciliation PR (C7)

**Decision:** 0 HOLD until Anthony decides

Acceptance criteria:
- One PR makes `LICENSE`, Kernel v1.3.1 header, `README.md`, and `LEGAL_DEFINITIONS.md` state the same license.
- If the license carries a values rider (Compassion Clause / Carrier Equivalence Addendum), it is clearly scoped as non-binding-on-license-terms per the existing `LEGAL_DEFINITIONS.md` pattern, to preserve OSI/FSF-compatibility for funding purposes.

### Issue 9 — SDD spec disambiguation (C8)

**Decision:** +1 NOW, pending filename confirmation

Acceptance criteria:
- `ARF/docs/arf_sdd_master_spec.md` renamed out of "Master Spec" collision.
- Both specs cross-link each other with a one-line role statement.
- `CLAUDE.md` directory map and Key Entry Points updated to list both.

### Issue 10 — ADR-6 analog-gate note (C9)

**Decision:** +1 NOW

Acceptance criteria:
- ADR-6 (or a short addendum file it links) states in one paragraph that the implemented consensus gate (`packages/orchestrator`) is an analog float model with five outcomes, not the Kernel's ternary heuristic, and that the two serve different layers (human dialogue vs. machine tally).

### Issue 11 — Phase0 bridge spec version fix (C10)

**Decision:** +1 NOW

Acceptance criteria:
- `docs/specs/phase0-substrate-bridge.spec.md` prerequisite line references the current substrate (`holonix main-0.6` / workspace `Cargo.toml`), not `main-0.4`.

---

## 10. Handoff packet

```yaml
timestamp: "2026-07-16"
author_agent: "Claude (Sonnet 5, claude.ai)"
human_collision_node: "Tony / kalisam / G-0-B FLOSS"
source_systems:
  - "G-0-B/FLOSS GitHub repo (live fetch, main branch)"
  - "arf_sdd_master_spec.md as uploaded by user this session"
  - "Claude project-knowledge memory (this conversation)"
claim_type:
  - "observed_fact"
  - "repo_assumption"
  - "proposal"
payload:
  summary:
    - "v0.2's reconciliation work (C1-C5) holds and is preserved."
    - "Five new contradictions found by diffing CLAUDE.md, ADR INDEX, LICENSE, and packages/orchestrator against each other and against v0.2."
    - "Most apparent 'stale memory' turned out to be a propagation gap: v0.2 already resolved several things that other docs (CLAUDE.md) never absorbed."
    - "Two items (license, SDD-spec rename) need Anthony's explicit decision before any file changes; three items (CLAUDE.md patch, ADR-6 note, phase0 spec version fix) are low-friction and ready to apply now."
  evidence:
    - "CLAUDE.md (live fetch)"
    - "docs/adr/INDEX.md (live fetch, v2.0.0, 2026-05-25)"
    - "LICENSE (live fetch, plain GPLv3)"
    - "docs/adr/ADR-7-agpl-cascade.md, docs/governance/LEGAL_DEFINITIONS.md"
    - "packages/orchestrator/claim_schema.py, consensus_gate.py, test_consensus_gate.py"
    - "docs/specs/phase0-substrate-bridge.spec.md"
  risks:
    - "If this v0.3 is merged without Anthony's license decision, C7 remains open and unresolvable by further doc-writing alone."
    - "Renaming ARF/docs/arf_sdd_master_spec.md without confirming no other doc links to its current path could silently break a cross-reference this session did not check (docs/architecture, docs/superpowers, and docs/research were not exhaustively grepped)."
  benefits:
    - "Closes the propagation gap between this spine and CLAUDE.md."
    - "Makes the license conflict visible and specific enough to act on, rather than a vague funding risk."
    - "Removes a version-mismatch trap from the next attempt to run the Phase 0 substrate-bridge test."
next_action: "Anthony reviews C7 (license) and C8 (SDD spec rename) and gives a decision; Issues 7, 10, 11 (CLAUDE.md patch, ADR-6 note, phase0 spec fix) can be applied immediately as low-friction PRs regardless."
```

---

## 11. Changelog

### v0.3.0 — 2026-07-16

- Added C6: `CLAUDE.md` Radicle-canonical claim vs. this spine's own GitHub-canonical resolution (C2) — a propagation gap between two governance-adjacent docs.
- Added C7: extended C5 into a confirmed **three-way** license conflict (root `LICENSE`=GPLv3 plain vs. Kernel/README="Compassion Clause + Apache/GPL" vs. ADR-7+LEGAL_DEFINITIONS="AGPL-3.0-or-later").
- Added C8: `ARF/docs/arf_sdd_master_spec.md` (v0.1, FR/AC/contract-heavy) and root `SDD-Master-Spec-0.22.md` (narrative synthesis) are unrelated documents sharing a name, violating the project's own "one canonical version" rule.
- Added C9: Kernel's ternary `{-1,0,+1}` decision model vs. the live, tested `packages/orchestrator` consensus gate, which explicitly forbids ternary integers and uses a five-outcome analog float model instead.
- Added C10: `docs/specs/phase0-substrate-bridge.spec.md` still references `holonix main-0.4`, superseded by the 2026-05-19 migration to `main-0.6`.
- Added Issues 7–11 and NOW backlog items 8–12 corresponding to C6–C10.
- Noted `CLAUDE.md` is outside this spine's formal precedence chain (§1) — flagged as the structural reason C6 was able to happen silently.

### v0.2.0 — 2026-07-02

- Created canonical execution synthesis from uploaded corpus and current `G-0-B/FLOSS` repo state.
- Reconciled Phase 0 completion conflict into "partially verified substrate; e2e integration still gated."
- Made GitHub-canonical / Radicle-later explicit.
- Demoted KERI, AD4M, hREA, ZK, and VVS autonomy to LATER unless evidence changes.
- Added NOW/LATER/NEVER backlog and issue backlog draft.
