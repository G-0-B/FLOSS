# Result — polyglot plugin/materializer spec review, 2026-09-01

## Scope and status

| | |
|---|---|
| Subject | `docs/superpowers/specs/2026-09-01-polyglot-evolving-plugin-materializer-design.md` v0.1.0 |
| Base commit | `a15f5f3` |
| Branch | `feat/coordination-room` |
| Reviewer | Claude Opus 5 (Claude Code session `1af99060`), single reviewer |
| Operator | Anthony / kalisam |
| Outcome | 6 findings against a sound topology; spec not edited, no code written from it |

## This record is NOT protocol-conformant — read it as one reviewer's output

`../manual-review-protocol-v1.0.md` and this directory's [`README.md`](../README.md)
describe a review as Lane A (multiple independent reviewers, `a1.json`…),
Lane B (adversarial cascade), and Lane C (adjudication). **None of that ran here.**

- One reviewer, one model family, one surface. No `a*.json`, no `b*.json`, no
  `adjudication.json`, no `merge.json`.
- `review_independence.py` was not run and would not pass: `spec_gate.py`'s
  `_reviewer_problems` requires distinct reviewer surfaces and families, and
  there is one of each.
- **This record therefore MUST NOT be cited as `reuse.reviewer.record` for any
  tier-2 entry.** It is a single-reviewer spec read, filed here because the
  findings are durable evidence, not because it satisfies the protocol.

`PACKET.md` is the review itself, not a packet issued to reviewers. The filename
follows the directory convention so the layout stays uniform; the content does
not match the convention's definition, and that difference is the point of this
section.

## What was verified rather than asserted

Reproduced independently at `a15f5f3`:

- All six probe SHA-256 values in the spec's Design provenance table match
  byte-exact against `.toilet/polyglot-plugin-validator-probe-2026-09-01/`.
- Base commit exists; fixture retained; nothing drifted.
- The spec's two hardest claims (dialect precedence, hook trust) are correctly
  labelled ❌ Blocked rather than hand-waved.

The topology decision — one physical polyglot directory carrying both dialects —
holds up. The six findings are defects inside a sound design.

## Findings

See [`PACKET.md`](PACKET.md). Summary:

| # | Finding | Spec lines |
|---|---|---|
| 1 | "the existing three materializers" undercounts by four (seven exist, six with `--check`) | 219–220, 113–120 |
| 2 | No error-aggregation contract; first-failure abort under-reports blindness | 237–244 |
| 3 | Lock section specifies identity *content*, not transition atomicity — the shape already corrected on the PR41 lineage | 251–256 |
| 4 | "atomic where the host filesystem supports it" leaves the Windows same-volume constraint unstated | 258–259 |
| 5 | `apply` is not bound to the diff hash a `plan` produced | 237–244, 281 |
| 6 | The spec's own governing gate (ADR-18) never fired on it — `py-filelock` 3.18.0 was installed and undeclared while the lock was hand-written | `governed_by` |

## Finding 6 generalised — and it was already found here, one ring smaller

[`GATE-ADOPTION-AUDIT.md`](GATE-ADOPTION-AUDIT.md) measures why the gate did not
fire: ADR-18's reuse gate is correctly implemented at `spec_gate.py:206` and
reaches **9 of 109 registered artifacts (8%)**, because an omitted `tier` is an
exemption rather than a default. `ADR-18-prior-art-reuse-gate.md` is itself
registered untiered.

**Credit where it is due: this directory's own README got there first.** The
2026-08-24 ADR-20 record generalised the same defect one ring smaller —

> *a tier-1 entry's reuse block is recorded but not validated* … *The gate would
> have caught this the moment it applied, and it never applied.*

The audit here is the next ring out: tier-1 blocks are recorded-but-unvalidated,
**and** 100 of 109 entries carry no tier at all, so they never even record a
block. Two independent sightings, one week apart, of the same failure shape.
That the earlier one was written in this very directory and did not prevent the
later one is itself evidence for the standing rule below.

## Correction to Finding 6, 2026-09-02 — the decision was made, then lost

Finding 6 and the audit both said ADR-18's gate "never fired" on the lock
capability. True, and too kind. **The reuse decision was reached by another
route and dropped.**

[`ADR-20`](../../adr/ADR-20-provenance-validator-reconciliation.md):589, under
*Accepted but not implemented here*, operator-accepted 2026-08-25 after a
four-auditor external meta-audit, lists **`filelock` adoption** alongside
external anchoring and the ADR-12 consent gate. Accepted — not proposed, not
deferred, not rejected. Eight days later the hand-rolled lock was still being
reviewed round after round while py-filelock 3.18.0 sat installed on the machine.

Same ADR, same sweep: the chain defects at identity `DkuYPguG98HM2nyR` are
attributed to "the `_acquire_lock` stale-reclamation bug and the daemon
singleton races." The lock work and the provenance work were one sweep, the
reuse verdict was produced there, and it did not travel.

That makes **three** ungated classes, not one:

| Class | Why the gate misses it |
|---|---|
| Unregistered artifacts | No registry entry; the gate cannot see them |
| Untiered entries | Registered, but an omitted tier is an exemption — 100/109 |
| **Accepted-but-not-implemented** | **A decision reached and recorded in canon, with nothing checking it was carried out** |

The third is invisible to every gate by construction. `spec_gate` validates that
evidence exists for artifacts that were *built*; nothing validates that
artifacts get built for decisions that were *accepted*. ADR-20 carries six such
promises with no gate behind them.

**R6** (new): read accepted ADRs for their accepted-but-not-implemented lists
and report the open count. Same shape as R1 — an existing unmeasured boundary
turned into a number that prints. No new surface; the items are already
enumerated in ADR text.

## Standing rule adopted

**Measure gate coverage, not just gate verdict.** A gate that reports pass/fail
must also report the size of the set it examined against the set it could have
examined. A gate with no coverage number is an unfalsifiable claim of compliance.

Corollary: **the remedy for a forgotten surface is never an additional surface.**
No skill, hook, agent, or checklist was created by this review.

Recorded at [`docs/agent-memory/project/gates-exempt-by-default.md`](../../agent-memory/project/gates-exempt-by-default.md) (commit `2deb8c9`).

## Disposition

| Remedy | State |
|---|---|
| **R1** — `spec_gate --check` prints coverage | ✅ **Implemented** this session, TDD, 4 new tests in `scripts/tests/test_spec_gate_reuse_contract.py` |
| R2 — untiered stops meaning exempt for new entries | ⚠️ Proposed; convention-establishing, needs explicit operator consent |
| R3 — aggregate materializers report all failures | ⚠️ Proposed |
| R4 — register the lock capability under ADR-18 with per-surface verdicts | ⚠️ Proposed |
| R5 — add no new surface | ✅ Honoured |

R1's output on this branch at time of writing:

```
SPEC-GATE COVERAGE: reuse gate active on 9/109 registered artifact(s) (8%); 100 untiered, of which 57 not grandfathered
```

## Known-red, not caused by this work

- `spec_gate --check` exits 1: `hooks/grok_pretool_st.py` and
  `hooks/grok_session_register.py` unregistered, `scripts/research_log.py` stale.
- `scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded`
  fails. Confirmed pre-existing by stashing this session's change and re-running.
- `black --check scripts/spec_gate.py` wants a reformat at line ~434, in
  pre-existing code. Left alone rather than swept into this commit.
