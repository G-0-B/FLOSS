# Reuse Map — v0.4 Continuation Bundle

The bundle's `00_README_CONTINUE_HERE.md` names this as the first safe task:
search the repo for existing contracts, produce a reuse / extend / supersede /
reject map. Its `09_CONTRADICTION_OPEN_QUESTIONS.md` C4 marks the same question
"must be validated by repo reuse map". This is that map.

| | |
|---|---|
| Subject | `.toilet/flossi0ullk_v0_4_continuation_package/` (24 files) |
| Bundle version | `flossi0ullk-v0.4-continuation-bundle` 0.1.0, Proposed / Specified |
| Reviewer | Claude Opus 5, single reviewer — **not protocol-conformant**, see RESULT.md |
| Date | 2026-09-04 |
| Repo state | branch `feat/coordination-room` |
| Governed by | ADR-18 prior-art & reuse gate |

**Bundle integrity ✅ Verified:** all 24 files in `handoff_manifest.json` hash
byte-exact. Nothing drifted between authoring and this review.

## Verdicts

| Bundle schema | Existing repo counterpart | Verdict |
|---|---|---|
| `evidence-ref` | `packages/orchestrator/claim_schema.EvidenceRef` + the 10-value enum in `provenance-packet.schema.json` | **reuse** |
| `claim` | `claim_schema.Claim` — **same name, different concept** | **extend + rename** |
| `admission-decision` | adjacent to `claim_schema.Vote` / `Decision` / `Outcome` | **extend + re-notate** |
| `task-contract` | `risk_tier` duplicates `claim_schema.BlastRadius` | **extend + reuse BlastRadius** |
| `ledger-entry` | none | **extend** |
| `shared-gist` | none | **extend** |
| `capability-descriptor` | none | **extend** |
| `private-memory-piece` | none | **extend (LATER)** |

Nothing is **supersede** and nothing is **reject**. The bundle proposes no
artifact that a current repo contract already fully provides, and it removes
nothing. Four of eight need changes before implementation; four are new
surface with no counterpart.

## The four that need changing

### 1. `evidence-ref` — reuse, do not ship a second one

`type` is declared as an unconstrained string carrying the reconciliation rule
in its description: *"Evidence class. Map to current canonical repo allowlists
before implementation."*

The intent is right and this is the only one of eight schemas deliberately left
without an enum. But a JSON Schema validates strings, not descriptions. The repo
enforces a closed ten-value vocabulary — `spec`, `test`, `adr`, `url`, `commit`,
`provenance_packet`, `file`, `log`, `activity`, `source_chain` — through
`claim_schema.EVIDENCE_TYPES`, which ADR-20 D-A1 established as the **single**
authority after four competing allow-lists drifted apart and produced a 100%
claim-rejection rate for weeks.

Shipping this schema as written adds a fifth surface that accepts any string.
That is ADR-20 Defect A exactly, one iteration later.

**Action:** carry the enum, not a note about the enum.

### 2. `claim` — extend, and rename

Two different things now share the name `Claim`:

| | repo `claim_schema.Claim` | bundle `claim.schema.json` |
|---|---|---|
| What it is | a **governance proposal** to the consensus gate | a **task-runtime epistemic assertion** |
| Key fields | `proposer`, `proposal_type`, `blast_radius`, `truth_status` | `task_id`, `claim_type`, `producer_agent`, `status`, `confidence` |
| Lifecycle | submitted, voted, decided | proposed, contested, admitted, rejected, superseded |
| Governed by | consensus-gate spec, ADR-10 | this bundle |

The bundle's C4 *identifies* this distinction correctly and then leaves both
called `Claim`. The concepts are genuinely different, so the answer is not to
merge them — it is to stop them sharing a name in one codebase.

**Action:** rename the bundle's to `RuntimeClaim`. Same for its `status`
vocabulary, which is unrelated to `Outcome`.

### 3. `admission-decision` — extend, but drop the ternary notation

`decision` is an integer enum `[-1, 0, 1]`.

Repo canon is explicit that the **analog** vote model superseded the ternary
framing (ADR-10 v2.0; `claim_schema.py:95` sets `CERTAINTY_LIMIT = 0.999` and
the module docstring at line 50 reads "analog vote model"). An admission verdict
is arguably not a vote weight, so this is not necessarily a semantic conflict —
but the notation is indistinguishable from the superseded model, in a repo whose
own `packages/orchestrator/__init__.py:8` still carries a stale "ternary
{-1, 0, +1} voting" line. A reader cannot tell the two apart by looking.

**Action:** make it a string enum — `["admit", "abstain", "reject"]`. Costs
nothing and cannot be misread as a vote weight.

### 4. `task-contract` — extend, but reuse the existing risk vocabulary

`risk_tier` is `["R0", "R1", "R2", "R3"]`. The repo already has a four-level
scope-of-impact vocabulary that drives quorum and override rules:
`BlastRadius` = `Local` / `Module` / `System` / `Substrate`, with per-level
thresholds in `QUORUM_MIN`.

Two four-level risk scales in one system is the drift defect this repo keeps
paying for. `R0..R3` also collides visually with the `R1`/`R2` rule numbering
already used in `docs/specs/integrity-provenance-validation.spec.md`.

**Action:** use `BlastRadius` values. If a task-level risk notion genuinely
differs from blast radius, say how in the spec — do not introduce a second
opaque scale.

## The four with no counterpart

`ledger-entry`, `shared-gist`, `capability-descriptor` and
`private-memory-piece` return nothing in `docs/specs/` or `packages/`. They are
genuinely new surface, so the fork risk the bundle worries about in C4 is
concentrated entirely in the four above — which is a better result than C4
feared.

Two constraints still apply to all four:

- Every one of them carries `evidence_refs`. Those must be the reused
  `EvidenceRef`, not a local variant, or the fifth-allow-list defect returns
  through the back door.
- `private-memory-piece` is on the bundle's own **LATER** list
  ("DECENTMEM-style private exploit/explore memory after repeated
  persistent-agent usage exists"). Specifying it now is fine; implementing it
  now contradicts the bundle's own sequencing.

## What the bundle got right, recorded because it is unusual

- **24/24 manifest hashes verify.** Byte-exact, nothing missing.
- **Lettered candidates (A, B, C, D…) rather than ADR numbers.** ADR-13..20 are
  live; a bundle proposing "ADR-21" would have collided with whatever lands
  next. Deferring numbering to ratification is the correct move.
- **Every repo contract it names exists** — `provenance-packet.spec.md`,
  `consensus-gate.spec.md`, `packages/activity_log/provenance.py`.
- **Seven of eight schemas carry enums.** The one that does not is the one that
  overlaps existing canon, and it says so.
- **Its NEVER list includes** *"treating signatures, hashes, log inclusion, or
  provenance as proof of semantic truth"* — which is ADR-20's trust-boundary
  finding, reached independently.
- **`rollback_plan` on every artifact.** "Delete this bundle; it changes no
  runtime state" is a checkable claim, and it is true.

## Staleness, not a defect

The bundle was authored without the 2026-09-02 gate changes: it does not know
about reuse-coverage reporting, `tier_exempt`, `deferred_promises`, or
`docs/specs/file-locking.spec.md`. Parallel authoring, not an error. But it
changes the bundle's own first task: **registering any of these schemas now
requires a tier decision**, because an omitted tier stopped being an exemption
on 2026-09-02. See `docs/reviews/2026-09-01-polyglot-plugin-materializer-spec/`.

## Sequencing

1. Apply the four changes above **to the bundle source**, so the corrected
   version is what any later agent loads. Done — see RESULT.md.
2. Register the design spec at **tier 1** with this map as its reuse evidence.
   Tier 1 and not tier 2 because tier 2 requires an independent reuse review
   across at least three provider surfaces and four model families, and this
   review is one reviewer on one surface. **A tier-1 reuse block is recorded
   but not validated** — see `../README.md`.
3. Promote to tier 2 with a real adversarial review **before** any of these
   schemas is implemented. The consensus gateway was unreachable
   (`ConnectionRefused` on `127.0.0.1:7334`) throughout this review.
