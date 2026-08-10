# Fable 5 Adversarial Review — Consolidated (WS4)

```yaml
# --- UpgradableArtifact Header ---
id: "fable5-adversarial-review-2026-07"
version: "1.0.0"
kind: "adversarial_review"
status: "Proposed"
updated: "2026-07-03"
supersedes: []
truth_status: "Verified"   # for the findings' factual observations — each carries file/commit evidence; fixes are Proposed
evidence_sources:
  - "Live reads 2026-07-03: Kernel v1.3.1, spine-v0.5.md, SDD-Master-Spec-0.22.md, ADR-10-local-agent-node.md, 2026-05-26-holochain-0.7-migration.md, docs/adr/INDEX.md, FLOSSI0ULLK-ADR-Suite-v2.0.md"
  - "WS0 verification block: docs/research/2026-05-15-working-todo-list.md §A.000"
  - "Live test runs 2026-07-03: gateway 147/147; native zomes 25/25; wasm32 cargo check exit 0"
  - "PR G-0-B/FLOSS#25 (MERGED 2026-06-16, 227 files, +29213/-5092)"
generator: "claude-fable-5"
sprint: "2026-07-03-fable5-sprint-handoff.md (WS4)"
upgrade_path: "Findings convert to fixes via normal PR flow; F2/F7 kernel items go through the ADR-3 kernelization process (friction: high)"
rollback_plan: "Review doc only; git revert"
friction_tier: "low"
```

**Scope reviewed:** Kernel v1.3.1 · Project Spine v0.5 · SDD v0.22 · consensus gateway design + ADR-10 · Holochain 0.6.1 migration mapping (M14) · PR #25 diff · WS0 contradiction findings.
**Constraint honored:** zero new architecture proposed. Findings recommend ADRs where needed; none are written here.
**Success criterion:** ≥5 actionable findings with smallest fixes — 9 delivered in the 2026-07-03 pass, +1 (F10) added 2026-07-04.

---

## Findings (severity-ordered)

### F1 — SDD v0.22 is a narrative synthesis holding normative precedence rank 3 — **HIGH**

**Defect.** `SDD-Master-Spec-0.22.md` self-describes internally as "SDD Master Specification v0.2 (Synthesis)" dated 2025-11-07. It is prose synthesis, not a requirements spec, and it is stale in load-bearing places:
- "RICE ... **Likely stands for** 'Resource Integrity Consensus Engine'" — a precedence-3 document containing guesses about its own component names.
- "AD4M: **Production-ready**" — contradicted by the 2026-05-09 AD4M/coasys audit delta (anti-duplication gate; sidecar decision explicitly open).
- "ADR system ... **ADR-0 validation incomplete**" — refuted: ADR-0 Test #4 PASSED 2026-03-20; Recognition Protocol Validated (ADR-0.1 v2.0).
- Holochain framing stuck at "targets 0.6, drift 0.5.4+/0.4.0" — live pin is hdi 0.7.1/hdk 0.6.1 with M14 to 0.7 planned.

Kernel §11 and Spine §1 rank "SDD Master Spec" **above** ADRs. On paper, this stale synthesis outranks every current decision record.

**Smallest fix.** Supersession banner at the top: *"Historical synthesis (v0.2, 2025-11). Not normative. Requirements authority delegated to `docs/specs/*` + ADR suite until an SDD 0.23 requirements document is issued."* Plus one line in kernel/spine precedence notes deferring rank 3 to `docs/specs/*` in the interim. Re-authoring an SDD 0.23 is a separate, operator-gated effort.

**Ternary:** **+1** banner now (low friction, reversible) · **0** on SDD 0.23 authoring (needs Anthony; LATER).

### F2 — Two incompatible "provenance packet" contracts are simultaneously normative — **HIGH**

**Defect.** Kernel §8 and Spine §7 define the cross-system handoff packet as an **unsigned YAML block** (`timestamp / author_agent / claim_type / payload / next_action`). `docs/specs/provenance-packet.spec.md` v1.4 defines the packet as a **signed JCS-canonicalized JSON envelope** (BLAKE3 SAID, Ed25519, per-agent sequence, governed hard-blocking). An agent following the kernel (precedence 1) emits packets the gateway spine cannot verify; an agent following the spec emits packets the kernel never mentions. The WS1 eval suite (`provenance_packet_validation/`) targets the spec form — so the fitness function and the kernel currently disagree about what a packet *is*.

**Smallest fix.** One amendment line in kernel §8 and spine §7: *"This YAML block is the human-readable summary form. The machine-verifiable contract is `docs/specs/provenance-packet.spec.md` (v1.4+), which supersedes on conflict."* Kernel is friction-high — route as a kernel v1.3.2 patch through the ADR-3 process, bundled with F7.

**Ternary:** **+1** propose the amendment (spine half is friction-medium and can land first).

### F3 — M14 migration plan's rationale and Gate 5 are built on Tryorama pairing, superseded by the Sweettest directive — **MEDIUM-HIGH**

**Defect.** `2026-05-26-holochain-0.7-migration.md` exists *because* "no @holochain/tryorama version pairs cleanly with hc 0.6.1", and Gate 5 pins tryorama 0.19.x + client 0.20.x. Operator directive 2026-07-03: JS Tryorama is replaced by Rust **Sweettest**. Sweettest runs the conductor in-process under `cargo test` — the pairing problem M14 is engineered around ceases to exist. Executing M14 as written burns effort on the wrong harness at Gate 5 and then flips truth-status labels (Gate 6) against the deprecated framework.

**Smallest fix.** Patch M14 in place (plan is Specified, not executed — cheap now): pre-flight drops the tryorama compat probe; Gate 5 becomes "add `holochain` sweettest dev-dependency matching the 0.7 pin; port `consent_gate.test.ts` + `substrate_bridge.test.ts` scenarios to Rust sweettest tests; `cargo test` green"; Gate 6/DoD wording updates from "Tryorama now Verified" to "Sweettest e2e Verified". Same gate structure, different harness — zero new architecture. Cross-ref the updated agent-memory (`tryorama-tooling-gap-2026-05-26.md`, patched 2026-07-03).

**Ternary:** **+1**.

### F4 — Truth-status fourth label: root CLAUDE.md misquotes its cited authority — **MEDIUM**

**Defect.** `C:\~shit\CLAUDE.md` line 74: "Truth-status discipline (✅ Verified / ⚠️ Specified / 🔮 Aspirational / **❌ Blocked**) is canonical per ADR-Suite v2.0." The suite itself (line 9, §invariants): "`Unverified` = hypothesis only" — **Blocked is not in the suite's vocabulary.** Kernel §4 and Spine §4 also say Unverified. Meanwhile "Blocked" *is* in live use as a status (ADR-16 `fit_for_validation: Blocked`; layer tables) — so the ecosystem now has a fifth label attributed to a document that doesn't define it. Epistemic labels are exactly the thing this project cannot afford drift on.

**Smallest fix.** Either (a) one-word correction in CLAUDE.md (`Blocked` → `Unverified`), or (b) if Blocked has earned its place as an operational state (it arguably has — "blocked on external dependency" ≠ "hypothesis only"), add it explicitly via a one-paragraph ADR-suite amendment and *then* cite it. Do not leave the false attribution standing.

**Ternary:** **0** — (a) vs (b) is Anthony's call; both are one-sitting fixes. Default proposal: (b), because ADR-16 and the layer tables already use Blocked with a distinct meaning that Unverified doesn't cover.

### F5 — ADR-10 / gateway evidence staleness cluster — **MEDIUM**

**Defect.** (a) `ADR-10-local-agent-node.md` Context: "32/32 tests passing" — live count 2026-07-03 is **147/147**; root CLAUDE.md layer table repeats "32/32 per ADR-10". Stale-low numbers still misinform sizing/risk judgments. (b) The ADR body still centers in-memory state + 5-tool registry; the 2026-04-16 note redirects to the file-based source chain but the un-annotated Context section is what gets quoted. (c) ADR-2 still carries the pre-MVP "round-trip unvalidated" note (WS0 phase-list item 3) — pending evidence reconciliation.

**Smallest fix.** Dated evidence-refresh lines: one in ADR-10's note ("test count 147/147 as of 2026-07-03; see packages/"), one in each CLAUDE.md table. Fold the ADR-2 evidence patch into the next ADR-suite touch rather than a standalone edit.

**Ternary:** **+1**.

### F6 — ADR INDEX omits ADR-16; header sentence self-inconsistent — **MEDIUM**

**Defect.** (From WS0.) `docs/adr/INDEX.md` v2.0.0 table stops at ADR-15; `ADR-16-omnigent-execution-surface.md` (Proposed, 2026-06-17) is absent. The header says the index tracks "the suite plus any post-suite additions (**ADR-12**)" while the table already contains 13/14/15 — the sentence contradicts the table it introduces. The pending ADR-10/11 file renames remain open (documented, cosmetic).

**Smallest fix.** Add the ADR-16 row (Proposed / Specified / High friction — it touches the execution/governance seam) and rewrite the header sentence to "post-suite additions (ADR-12..16)". Eval item `cv-dev-019` already encodes this reconciliation as a golden APPROVE — the fix and the fitness function will agree.

**Ternary:** **+1**.

### F7 — Kernel v1.3.1 hygiene cluster (bundle as v1.3.2) — **LOW-MEDIUM**

**Defect.** Four small integrity leaks in the precedence-1 document:
1. Cites "ADR-003" ×3 (superseded numbering; canonical is ADR-3 per INDEX numbering-history).
2. Appendix: "Detailed docs live in `/mnt/project/`" — a claude.ai project-mount path, meaningless for every repo-side agent (portability defect in a doc addressed to all agentic readers).
3. Header `truth_status: "verified"` — lowercase, violating its own §4 vocabulary table; evidence cited is "2+ months production use" with no repo artifact.
4. §10 Seed Agents requires a "HarvestPacket schema" — no such schema exists in `docs/specs/` (harvest flows exist in scripts; the named schema does not). Per its own Claim Truth Model this is Aspirational presented as required.

**Smallest fix.** One kernel v1.3.2 patch PR carrying F2's §8 amendment plus these four line-edits, routed once through the ADR-3 kernelization process (single high-friction change window instead of four).

**Ternary:** **+1** bundled.

### F8 — One-canonical-version violations + intake residue — **LOW**

**Defect.** (a) `knowledge-triple.spec.md` exists byte-identical in `docs/specs/` **and** `docs/architecture/` — direct "one canonical version" violation; WS1 conformed to the `specs/` copy. (b) `FLOSS/styles.css` — orphan root file landed via PR #25, no consumer found. (c) Runtime hygiene from WS0 probe: CONTEXT_L0 stale >14d; `.agent-surface/events/` queue depth 8. (d) PR #25 churn note: the merge introduced `FLOSSI_U_Founding_Kit_v1.6/` files under `FLOSS/` post-relocation; current branch no longer has them — no live defect, recorded for provenance completeness.

**Smallest fix.** (a) Replace the `architecture/` copy with a 3-line pointer stub (a duplicate is not superseded canon, so the never-delete/archive rule doesn't require archiving it — but archiving is also acceptable if stricter reading preferred). (b) Digest or delete `styles.css` via intake flow. (c) Regenerate L0 (`materialize_shared_context_surface.py`); drain the event queue via its processor.

**Ternary:** **+1** for (a) · **0** for (b)/(c) — routine operator routing, not review-blocking.

### F10 — KnowledgeTriple contract divergence: spec.md vs schema.json + live zome — **HIGH** *(added 2026-07-04 during the v1.1 interop patch)*

**Defect.** `docs/specs/knowledge-triple.spec.md` (v1.0/1.1) and
`docs/specs/knowledge-triple.schema.json` + the live integrity zome
(`rose_forest/zomes/integrity/src/lib.rs:225`) define **different contracts**:
confidence `[0,1]` vs **`[-1,+1]` signed gradient** (zome-validated, in-code
comment cites the analog model / ADR-10 v2.0 / ADR-13); predicate URIs vs
short-name enum; structured provenance vs flat AgentPubKey `source`. The
convention says `.schema.json` and `.spec.md` are paired representations of one
contract — these two have silently forked, and the WS1/WS3 eval+seed data
follow the spec.md side. Precedence says code conforms to spec; the ADR trail
says signed-gradient is the decided direction — the *spec* is the stale party
on confidence, while predicate form is genuinely undecided.

**Smallest fix.** (Landed) divergence banner at the top of spec.md naming the
zome authoritative for the confidence domain and freezing the Pioneer
fine-tune launch until the predicate-form decision. (Pending, ADR-tier) one
reconciliation ADR deciding: signed-gradient confidence everywhere + predicate
form (URI registry vs enum seed vocabulary vs enum-now/URI-later migration
path). Eval/seed confidence values embed into `[0,1] ⊂ [-1,+1]` unchanged;
predicates remap mechanically by table if the enum wins.

**Ternary:** **0** — the reconciliation direction needs Anthony (it touches
Phase 1's primary deliverable); **+1** on the banner + fine-tune hold already applied.

### F9 — Spine v0.5 predates three load-bearing decisions it now silently contradicts — **MEDIUM**

**Defect.** Spine (2026-02-08) is the precedence-2 invariant document, yet:
1. §9 "Phase 0 is a hard gate" describes the substrate-bridge loop with no anchor distinguishing **MVP Phase 0** (complete) from **orchestration bridge Phase 0** (Specified) — the exact two-gate confusion the 2026-05-18 terminology correction exists to prevent; a fresh agent reading the spine re-acquires the bug.
2. §10.2 autonomy budgets say "no merge of high-risk changes without approvals + CI proof" but never mention the consent gate (ADR-12, OVERRIDE FORBIDDEN, APPROVE ≥ 0.85) or the analog vote model — the actual enforcement mechanisms that now exist.
3. §7 carries the F2 packet-contract skew (spine half).

**Smallest fix.** Spine v0.5.1 patch, three sentences: §9 terminology note pointing at `phase0-substrate-bridge.spec.md`; §10.2 pointer to ADR-12 + ADR-10 analog vote model; §7 the F2 supersession line. Friction-medium; no quorum machinery needed for pointer-level patches per §3.2.

**Ternary:** **+1**.

---

## What was reviewed and found sound (for balance, per anti-sycophancy both directions)

- **Gateway code vs ADR-10 intent:** tally ordering (conflict → quorum → direction), CERTAINTY_LIMIT closed-interval semantics, per-radius thresholds, and CONFLICT-overrides-quorum are implemented exactly as documented and covered by 147 passing tests including edge cases (WS1 read the code directly).
- **PR #25 substance:** contents match its title claims (WS0 claim 1 Verified); the consensus-gate test file alone is 878 lines.
- **provenance-packet.spec.md v1.4** is the strongest spec in the reviewed set — precise field rules, explicit recursion semantics, honest audit-disposition carve-out. The findings above are about other documents failing to *point at it*, not about the spec itself.
- **M14 gate discipline** (sequential gates, snapshot-first, DO-NOT-proceed-past-failure) is exactly right; only its harness target is stale (F3).

## Sprint bookkeeping

- Findings: 10 (≥5 required; F10 added 2026-07-04). New architecture proposed: 0.
- Doc budget: this is doc **2 of 6** for the sprint (1: evals README).
- Provenance: `generator: claude-fable-5`, 2026-07-03, all observations backed by live reads/runs this session (see header evidence_sources).
- Suggested fix order by leverage-per-effort: F6 → F4 → F5 → F3 → F9 → F1 → F8a → F2+F7 (kernel window last, one pass).
