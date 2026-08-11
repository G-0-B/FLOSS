# 2026-08-10 Root Intake Digestion Map

```yaml
id: "2026-08-10-root-intake-digestion"
status: "Classification complete; NO FILES MOVED. Awaiting operator approval of the destination column before relocation."
truth_status:
  relocation: "Not performed (this pass classifies only)"
  classification: "Specified (single-agent read pass, 2026-08-09/10, with hash and git verification where stated)"
  canon_promotion: "Not performed"
move_log: ".agent-surface/intake/root-intake-moves-2026-08-10.json (not yet written)"
raw_holding_area: "FLOSS/docs/research/intake_raw/2026-08-10-root/{reports,reference,bundles}/ (not yet created)"
companion_record: "Supersedes 2026-07-07 pass as latest intake map; 07-07 map retained as template"
authorized_by: "Operator instruction 2026-08-09 — 'ingest and document ... start with the root shit, consolidating plans and things affecting the same parts into a single plan'"
plan_file: ".toilet/root-consolidation-plan-2026-08-09.md"
previous_passes:
  - "2026-05-19"
  - "2026-05-22"
  - "2026-05-25"
  - "2026-06-08"
  - "2026-06-12"
  - "2026-07-07 (template)"
```

## What changed

Unlike prior passes, this one is **consolidation-first**, not intake-first. The root has accumulated competing *plans for the same subsystem* written weeks apart, not merely undigested research. The pass therefore adds a **Consolidation verdicts** section (§3) that names exactly one authoritative destination per cluster; §2 remains the familiar per-file classification.

Scope: 55 root-level files. 27 were untracked at pass start; the rest are tracked orientation canon or accumulated cruft.

### Pre-pass baseline (recorded per verification discipline)

| Check | Result at pass start |
|---|---|
| `python FLOSS/scripts/spec_gate.py --check` | **FAIL** — 6 unregistered artifacts |
| `python FLOSS/scripts/refresh_agent_surfaces.py --check` | **PASS** — all 6 steps clean |
| root repo `git status --porcelain \| wc -l` | 137 |
| FLOSS `git status --porcelain \| wc -l` | 137 |
| FLOSS vs `origin/main` | **6 behind, 94 ahead**; `wip/salvage-20260804` has no upstream. Merge-base `877589d` (2026-06-15). |

Snapshots taken before any write: `.toilet/snap-root-20260809.bundle` (56,658,573 B), `.toilet/snap-floss-20260809.bundle` (206,658,894 B), and `.toilet/snap-root-untracked-20260809/` (27 files + `_SHA256SUMS.txt`; hash-set comparison source vs copy identical).

---

## 1. Clusters

- **Provenance** (5 files, 2026-07-30 → 08-04) — one repo spec plus a delta, a verification report, a sidecar carrying a *newer* correction than the report it wraps, and a superseded external draft.
- **Coordination trio + bundle** (2026-08-04) — `CONTEXT.yaml` / `HANDOFF.md` / `RESEARCH-REGISTER.md`, plus `files.zip` which is exactly those three plus two provenance files.
- **Ember seed pack** (6 files + zip, 2026-06-09) — superseded continuation lineage.
- **Process artifacts** (3 live layers) — kernel, operating instructions, UOP. See §3.
- **Build spine / patch notes** (2026-07-16 → 07-21).
- **Context daemon / memory spine** (2026-07-21 → 08-01).
- **Adversarial critiques** (2026-07-08, 08-01) — two substantial audits, both undigested.
- **Undigested research** (2026-07-10 → 07-29).
- **Orientation canon** (tracked; stays).
- **Cruft and runtime artifacts.**

---

## 2. Classification verdicts

Truth: **V**erified / **S**pecified / **A**spirational / **U**nverified.

| # | File | Size | Kind | Vintage | Truth | Summary | Recommended destination | Flags |
|---|---|---|---|---|---|---|---|---|
| 1 | `provenance-packet-v1.5-delta.md` | 12,819 B | spec delta | 2026-08-04 | S | Edit-set D1–D6 against the repo's v1.4 spec. Self-describes: *"This is an edit-set against the repo's v1.4 spec, not a replacement. v1.4 is authoritative."* | Merge D2/D3 into `docs/specs/provenance-packet.spec.md`, then `intake_raw/reports/` | **D1 blocked on ADR-12** per `CONTEXT.yaml.consent_gate_defect.do_not`. Only live proposal in the cluster. |
| 2 | `provenance-packet.spec.md` | 13,756 B | spec (external draft) | 2026-07-30 | U | External v1.4 draft, same version number as the repo spec but 421 diff lines apart. | `intake_raw/reference/` | **SUPERSEDED.** `HANDOFF.md` §6: *"SUPERSEDED by repo. Diff-source only."* Its SAID algorithm is **wrong** (computed `v` with `sigs=[]`). Ledger note must say so. |
| 3 | `provenance-packet.schema.json` | 5,086 B | schema | 2026-07-30 | U | Companion to #2, 190 diff lines from the repo twin. | `intake_raw/reference/` | Superseded with its parent. |
| 4 | `provenance-spine-v1.4-verification-report.md` | 29,722 B | report | 2026-07-30 | V/mixed | Adversarial verification of v1.4 against keripy / RFC 8785 / repo. `status: Accepted`. | Merge #5 in, then `intake_raw/reports/` | Own `upgrade_path` unmet: *"Supersede when PR #38 is retrieved under authenticated access."* |
| 5 | `verification-report-sidecar.md` | 9,598 B | report sidecar | 2026-08-04 | V | Detachable header + signable packet skeleton for #4 — **but carries the newest fact in the cluster**: `CORRECTION 2026-08-04: the spine is on origin/main via PR #36 (merged 2026-06-16), NOT merely a working branch; PR #38 is docs-only.` | **Merge into #4 before moving** | This is the `parallel_correction` failure mode `CONTEXT.yaml` names. Corrections edit the original. |
| 6 | `CONTEXT.yaml` | 17,543 B | context artifact v0.4.0 | 2026-08-04 | S | Single loadable continuation artifact; declares supersession of OVCA v0.1, CCA-20260716-001, context@0.3.0/0.2.0. Carries 11 `now` + 4 `later` + 3 `never` + 3 open questions. | **Stays at root; now tracked** | Its own `later` list contains *"Generate CONTEXT.yaml from repo state"* — v0.4.0 is not the terminal form. |
| 7 | `HANDOFF.md` | 13,054 B | handoff v1.1.0 | 2026-08-04 | S | Lane assignments A–D, known-refuted claims, bundle manifest. | **Stays at root; now tracked** | Lane discipline governs Phase 2 git work. |
| 8 | `RESEARCH-REGISTER.md` | 9,541 B | citation register v1.1.0 | 2026-08-04 | V | Corrected external-fact register. | **Stays at root; now tracked** | Supersedes #9. |
| 9 | `flossi0ullk-research-register.md` | 8,831 B | citation register v1.0.0 | 2026-07-30 | V | Same `id:`, one version behind. Diff vs #8 is **18 lines**, entirely the AGPL-3.0-or-later relicense resolution. | `intake_raw/reports/` | mtime (08-01) post-dates its own declared `updated: 2026-07-30` — mtime is not a version signal here. |
| 10 | `files.zip` | 29,554 B | bundle | 2026-08-04 | V | **Verified by reading the archive**: exactly 5 entries — `CONTEXT.yaml`, `HANDOFF.md`, `RESEARCH-REGISTER.md`, `provenance-packet-v1.5-delta.md`, `verification-report-sidecar.md`. | `intake_raw/bundles/` | Redundant with the loose originals; keep as the as-shipped bundle record. |
| 11 | `00_MASTER_SEED.md` | 5,593 B | seed manifest v1.0.0 | 2026-06-09 | S | Read-order manifest for the 5-file Ember Seed Pack; source-authority ladder. | `intake_raw/bundles/ember-seed-pack/` | Its ladder (`repo branch state > CURRENT_STATE > repo docs > uploads > conversation > memory`) is worth porting into the kernel — see §3. |
| 12 | `01_thread_verification_spike_inventory.md` | 10,631 B | seed | 2026-06-09 | S | ObjectGraph spike, 20-script metaharness inventory, spec-gate D7. | `intake_raw/bundles/ember-seed-pack/` | §5 N-queue closed 2026-06-12 per working-todo §A.00. |
| 13 | `02_seed_tame_integration_unblock.md` | 1,544 B | seed | 2026-06-09 | S | Levin/TAME integration brief, 3 gated actions. | `intake_raw/bundles/ember-seed-pack/` | **Harvest open items before moving.** |
| 14 | `03_seed_atomic_data_hold.md` | 1,358 B | seed | 2026-06-09 | S | Atomic Data HOLD decision, 4 gated actions "unexecuted as of 2026-06-09". | `intake_raw/bundles/ember-seed-pack/` | **Harvest open items before moving.** |
| 15 | `05_orient_skill_handoff_v1_0_0_VERBATIM.md` | 36,396 B | handoff | 2026-06-09 | S | orient-skill v0.1.0 → v0.2.0 upgrade packet with embedded payloads + sha256. | `intake_raw/bundles/ember-seed-pack/` | Skill has since moved past v0.2.0; historical. |
| 16 | `ember_seed_pack_v1_0_0.zip` + `SHA256SUMS` | 24,211 + 577 B | bundle | 2026-06-09 | V | **Verified by reading the archive**: exactly items 11–15 plus `SHA256SUMS`. | `intake_raw/bundles/ember-seed-pack/` | Keep `SHA256SUMS` adjacent to the zip it verifies. |
| 17 | `FLOSSI0ULLK_Context_Continuation_Packet_2026-06-09.md` | 19,484 B | continuation packet | 2026-06-09 | V | Session record + contradiction table + 6-doc intake inventory. | `intake_raw/reports/` | **Working-tree edit reverted 2026-08-10**: it retroactively applied the ADR-10/11 rename inside a §4a block headed *"Verified this session (live GitHub fetch, 2026-06-09)"*, which would falsify an accurate historical observation. |
| 18 | `flossi0ullk-uop-v2.1.md` | 5,808 B | process (9-gate loop) | 2026-08-03 | S | Nine-gate execution loop with an enforcement-mechanism column and a cross-verification protocol (negative results must state search scope). | **New `docs/governance/uop-v2.1.md`** | See §3. Alternative: fold into `spine-v0.5.md`. |
| 19 | `FLOSSI0ULLK_CANONICAL_BUILD_SPINE_v0.3.md` | 21,652 B | spec/ADR-class v0.3.0 | 2026-07-16 | S | Contradiction-resolving execution spine, 10 issues + phase gates. Self-declares supersession of v0.2 and two merged artifacts. | **New `docs/governance/FLOSSI0ULLK_CANONICAL_BUILD_SPINE_v0.3.md`**, then original → `intake_raw/reports/` | Status stays **Proposed**. Landing it repairs a live dangling pointer (see #20). |
| 20 | `CLAUDE_md_patch_notes_2026-07-16.md` | 2,485 B | patch set | 2026-07-16 | S | Two unapplied `CLAUDE.md` patches (Radicle-canonical → GitHub-current/Radicle-target; ADR range). | Apply via `shared-agent-surface.json`, then `intake_raw/reports/` | Points at `docs/governance/FLOSSI0ULLK_CANONICAL_BUILD_SPINE_v0.3.md` — **path does not exist until #19 lands**. |
| 21 | `ADR-CONTEXT-DAEMON-ROI-v0.2.md` | 11,859 B | ADR-shaped | 2026-07-21 | S | Living Context Daemon: Sourcechain-as-sole-reservoir, 5-layer projection, ROI framing. | Append as an unratified section to `docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md`, then `intake_raw/reports/` | **No ADR number allocated** (ADRs run 0–19). Operator decided 2026-08-09: fold, do not allocate ADR-20. Its 88.7 % / 70–90 % figures are unsourced — carry as claims. |
| 22 | `Adversarial Verification of the Stratified Cognitive Memory Spine…md` | 23,237 B | adversarial audit | 2026-08-01 | U | Tests the memory-spine novelty claim against NARS / OpenCog / justification logic. Verdict: novel *integration*, not novel components. | `intake_raw/reports/` | **Do not land as a parallel critique doc.** Findings become edits to `AGENTMEMORY.md` or backlog items. Flags a licence conflict now resolved by the AGPL relicense. |
| 23 | `whites_resonance_corrections_critical_analysis.md` | 24,627 B | adversarial audit | 2026-07-08 | U | **Not in any prior inventory.** Adversarial technical audit concluding the *"resonance IS validation, not a metaphor"* claim fails: resonance is continuous/linear/superposable, validation is a boolean `V(D,E)→{accept,reject}`. Also finds 2 of 5 "novel predictions" unimplementable on real Holochain (cross-DNA propagation contradicts per-DNA isolated DHTs; timestamp "phase coherence" contradicts deterministic validation, which blocks time reads). | `intake_raw/reports/` | **Highest-signal undigested item in the pass.** Cites Kuramoto/ONN/Ising prior art as owning priority. Corroborates the Holochain maturity picture. Feeds the ADR-18 reuse gate directly. |
| 24 | `FLOSSIOULLK × Omnigent × OmniRoute × NANDA  Stop Reinventing, Start Composing.md` | 35,659 B | reuse survey | 2026-07-10 | U | Composition survey vs Omnigent, OmniRoute, NANDA, hREA/Arkology. | `intake_raw/reports/` | Targets already landed as ADR-16 + ADR-19; source retained for provenance. |
| 25 | `7_29_2026_perplexity synthesis…md` | 22,694 B | external synthesis | 2026-07-29 | U | Perplexity's academically-framed read of the stack; Love/Light/Knowledge as invariants. | `intake_raw/reports/` | AI-generated; **never auto-promote.** |
| 26 | `2026-07-16-prior-art-reuse-gate-design-proposal.md` | 14,986 B | design proposal | 2026-07-16 | V | Three gate shapes for adopt→extend→compose→build. | `intake_raw/reports/` | **Header `status: "AWAITING HUMAN APPROVAL — nothing implemented"` is STALE** — landed as ADR-18 + `reuse-gate.spec.md`. ADR-18's `design_record:` field must be repointed at the new path or it dangles. |
| 27 | `The_Luck_Factor.pdf` | 145,517 B | external book/paper | 2026-07-20 | U | Pairs with `.toilet/7-20-2026_perplexity_Evidence-Based Mechanisms for Cultivating Luck…md`. | `intake_raw/reference/` | Its `.toilet` companion is a later-phase item; leave a forward pointer. |
| 28 | `agentmemory.env.proposed` | 4,964 B | config proposal | 2026-06-16 | S | Proposed `~/.agentmemory/.env`; SOVEREIGN/SHARED/PLANES-CLEAN dials. | `intake_raw/reference/` | Never applied. Contains a **placeholder** key `__PUT_YOUR_GEMINI_KEY__`, not a live secret. Warns against reintroducing a dead `OPENAI_API_KEY`. |
| 29 | `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.hermes.md`, `INDEX.md`, `README-REPO.md`, `AGENTMEMORY.md` | — | orientation canon | 2026-07-07 → 07-26 | V | Per-harness projections + the canon registry. | **Stay at root** | Generated from `FLOSS/shared-agent-surface.json` — never hand-edit. ADR-10 rename propagated 2026-08-10 (`2006070`). |
| 30 | `IDENTITY.md`, `SOUL.md`, `TOOLS.md`, `USER.md`, `HEARTBEAT.md` | 226–1,806 B | vendor templates | 2026-04-28 | U | Unfilled openclaw templates; every field blank. | **Stay at root, flagged empty** | `README-REPO.md` lists them as root canon this repo versions. Do not move. Filling or removing them is an operator call. |
| 31 | `.claude_consciousness.m8` | 609 B | runtime state | 2026-08-09 | V | smart-tree session state (`session_id`, tokenization rules, empty insights). | **gitignore** | Regenerated per session; `project_name: "unknown"` — not carrying real context. |
| 32 | `nul` | 5,049 B | accident | 2026-07-26 | V | A `git status` capture from a Windows `> nul` redirect that hit a file instead of the null device. | **Delete** (operator call) | Zero informational value beyond a 07-26 tree snapshot. |
| 33 | `.gitignore.qwenpaw-dump-backup` (734 KB), `config.json` (2.3 MB), `lintlang-0.3.1.zip` (167 KB), `.mcp.json.pre-januscope.bak`, `floss_plane_rewritten_bootstrap…cfg`, `refactor_opencode.py`, `vibe-floss.ps1`, `skills-lock.json`, `package.json`/`package-lock.json`, `~shit.code-workspace` | — | cruft / tooling | 2026-04 → 08 | U | Backups, a 2.3 MB config dump, a vendored zip, one-off scripts. | **Classify only; move nothing this pass** | `config.json` and the qwenpaw backup are the two size outliers. Never commit either. |
| 34 | `_pr38_*`, `_codex_pr38_*`, `_reuse_probes`, `_review_artifacts`, `_pr25fix`, `tmp_superpowers`, `lintlang-0.3.1/` | — | working dirs | 2026-07 | V | PR38 salvage capsules, review artifacts, probes. | **Deferred sub-pass, gated on PR #38 merging** | Load-bearing: they are the evidence base for ADR-18's PR38 counterfactual. Eventual home `intake_raw/bundles/`. |
| 35 | `Free Libre Open Source SingYouRarity/` | 0 files | empty dir | — | V | Its one file relocated in the 2026-07-07 pass. | **Removable** | Confirmed empty. |

---

## 3. Consolidation verdicts (the merge audit trail)

One authoritative destination per cluster. **Net new canonical docs: 2** (items C4a, C4c). Every other cluster edits an existing doc — doc-budget discipline.

| Cluster | Single authoritative destination | Absorbed sources | Losers → |
|---|---|---|---|
| **C1 Provenance** | `FLOSS/docs/specs/provenance-packet.spec.md` (existing v1.4) | D2/D3 of #1; sidecar #5 merged into report #4 | #2, #3 → `reference/`; #1, #4+5 → `reports/` |
| **C2 Research register** | `RESEARCH-REGISTER.md` v1.1.0 (root, tracked) | — (v1.1.0 wins outright) | #9 → `reports/` |
| **C3 Context continuation** | `CONTEXT.yaml` v0.4.0 (root, tracked) | — | #11–17 → `bundles/`, `reports/` |
| **C4a Build spine** | **NEW** `docs/governance/FLOSSI0ULLK_CANONICAL_BUILD_SPINE_v0.3.md` | #19 | original → `reports/` |
| **C4b Harness patches** | `FLOSS/shared-agent-surface.json` (source, not the projections) | #20's two patches | #20 → `reports/` |
| **C4c Process stack** | `FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md` (L1) + **NEW** `docs/governance/uop-v2.1.md` (L3) | 6 clauses from the Operating Instructions v2.0 already sitting in `intake_raw/2026-06-08-root/reports/`; #18 lands as L3 | `docs/governance/kernel-v1.2.md` **deleted** |
| **C5 Context daemon** | `docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md` (existing) | #21's ratified commitments as an unratified section | #21, #22 → `reports/` |
| **C6 Reuse gate** | `docs/adr/ADR-18-prior-art-reuse-gate.md` + `docs/specs/reuse-gate.spec.md` (existing, now committed `9f18f07`) | — (fully absorbed) | #26 → `reports/`; repoint ADR-18's `design_record:` |
| **C7 Undigested research** | none — holding area only | — | #23, #24, #25 → `reports/`; #27 → `reference/` |

### C4c detail — three live process layers, one corpse

**`FLOSS/docs/governance/kernel-v1.2.md` is dead.** Verified: md5 `60520d7d815b2170087d88f19a5ff95e`, **byte-identical** to `FLOSS/archive/metaprompt-versions/FLOSSI0ULLK Master Metaprompt v1.2 (Kernel Edition).md`. `INDEX.md:279` carries the original order — *"Diff and forward-port any governance-specific content not already in v1.3.1, then move v1.2 to `archive/metaprompt-versions/`"* — which was **half-executed**: copied to archive, never removed from `governance/`. Deleting it completes an archive that already happened.

Live references to repair: `docs/ARCHITECTURE.md:130` (the only one that actively routes onboarding through it), `INDEX.md:279` (close the order), `INDEX.md:109` and `FLOSS/CLAUDE.md:43` (directory-map lines already tagged `(drift)`). Leave `docs/research/2026-05-10-doc-cull-triage-v1.md:318` alone — its premature `✅` is now honest audit history.

The three live layers are **different layers, not versions of each other**:

| Layer | Artifact | Date |
|---|---|---|
| L1 always-on constraints | `FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md` | 2026-07-16 — **newest** |
| L2 high-level reply contract | `docs/research/intake_raw/2026-06-08-root/reports/FLOSSI0ULLK-operating-instructions-v2.md` | 2026-06-08 |
| L3 execution gate loop | root `flossi0ullk-uop-v2.1.md` | 2026-08-03 |

L2 has been in the holding area since 2026-06-08 and was never promoted; only its rescission clause reached canon, via `docs/research/2026-06-08-instruction-and-levin-handoff-synthesis.md:43`. The kernel already carries §2 Evidence Gate, §4 Claim Truth Model, §11 Precedence, §12 Compliance Self-Check and the anti-sycophancy mandate. **Six L2 clauses are genuinely absent** and are the merge payload:

1. Spirit-over-letter reading rule, with its two non-loosened bounds (literal precision on world-claims; hard limits untradeable).
2. Doc-discipline clause, including the **explicit rescission** of the old "integrate everything everywhere" directive.
3. **Source-authority ladder** — `repo branch state > CURRENT_STATE > repo docs > project-knowledge uploads > conversation history > memory`. A *different* ladder from kernel §11's artifact-precedence list; both are needed. Also stated independently in seed item #11.
4. Re-ask open questions across turns (explicitly supersedes any never-repeat rule).
5. Multi-AI agreement is suspect when models share a training distribution — one primary-source check outweighs LLM consensus.
6. Research guidelines (recency, FLOSS-licensed preference, process **all** attachments).

**Open, not decided here:** the live kernel file is named `…v1_3_1_Kernel.md` but carries `version: "1.3.2"`, and differs from the same-named archive copy — the archive holds true 1.3.1. Merging the six clauses makes it 1.4.0. Renaming ripples through `LOADING_ORDER.md`, both `CLAUDE.md` files, `INDEX.md`, and the context surface. **Operator call.**

`docs/architecture/META_COORDINATION_KERNEL_v4.0.md` is deliberately **out of this cluster** — per agent-memory `project-v4-kernel-landed` it is the orthogonal *operational* axis, not a successor to the metaprompt kernel.

---

## 4. NEVER-list flags (filter at distillation time)

1. **AI-generated synthesis is never auto-promoted to canon** (#22, #23, #25, and the 27 unreviewed drafts in `docs/knowledge_log/staging/`). Standing lesson.
2. **The Perplexity synthesis's self-applied confidence framing** (#25) — its own V/S/A/U tags are not authoritative.
3. **Any NANDA/Omnigent recommendation from #24** not already independently landed as ADR-16 or ADR-19.
4. **The external provenance draft's SAID algorithm** (#2) — it computes `v` with `sigs=[]` and is wrong. Do not resurrect.
5. **`ADR-CONTEXT-DAEMON-ROI` ROI percentages** (88.7 %, 70–90 %) — unsourced vendor-style claims; carry as claims, never as measurements.
6. **`FLOSS/docs/ADRs/` shadow directory** — contains `ADR-2-Holochain-Integration-Stack.md` and `ADR-3-Documentation-Consolidation.md`, which **collide by number** with the real ADR-2/ADR-3 in `docs/adr/`. A future agent reading the shadow dir will assert wrong facts. Unindexed, ungated. Resolution is likely `archive/` — these *are* superseded canonical docs, so archive is correct here, unlike root drops.
7. **Retroactive edits to dated verification records** (#17) — a rename applied inside a "verified on date X" block turns a true observation false.

---

## 5. Priority queue: next highest-value distillations

1. **#23 `whites_resonance_corrections_critical_analysis.md`** — the strongest undigested critique in the tree. Its Holochain findings (per-DNA DHT isolation; determinism blocking time reads in `validate`) are checkable against official docs and bear directly on architecture claims. Distil into an architecture-doc correction, not a new parallel doc.
2. **#22 memory-spine adversarial verification** — same treatment; findings become `AGENTMEMORY.md` edits or backlog items.
3. **Seed items #13/#14** — harvest live unblocks before the pack moves.
4. Carried from the 2026-07-07 queue, still open: permeable-shells reduction test; UTN v0.3 dogfooding; Peony doula MVP; anti-sycophancy/anti-dependence metrics; capability-token coverage audit; Self-Harness paper digestion; Carse → governance vocabulary.

---

## 6. Follow-on constraints

- **Nothing moves until the operator approves the destination column.** Precedent: the 2026-07-07 pass wrote the map, moved nothing, and waited.
- Moves are plain `mv` plus a sha256 pre/post ledger. All root drops are untracked in the root repo, so `git mv` is inapplicable.
- **No root drop may land in `FLOSS/archive/`** — archive is for superseded *canonical* docs only. Every ledger `to:` must be under `intake_raw/2026-08-10-root/`.
- The heartbeat stays stopped for the duration; restarting it schedules `process_intake` + `autonomous_synthesis`, which would race canon promotion. `watch_intake.py`'s `node_modules` leak must be fixed before it restarts.
- Do not use `watch_intake.py` to perform moves — it annotates only, never moves, and has no PDF support. `consider_canon_promotion` is advisory.
- Post-pass acceptance requires: hashes match, nothing unaccounted for, `spec_gate --check` green, `refresh_agent_surfaces --check` still clean, every `INDEX.md` canon path resolves, zero `archive` paths in the ledger, and no dangling pointers to moved files.
