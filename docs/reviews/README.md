# Review records

Durable records of multi-model reviews run under
[`../governance/manual-review-protocol-v1.0.md`](../governance/manual-review-protocol-v1.0.md).

One directory per review, named `YYYY-MM-DD-<subject>`, containing:

| File | Contents |
|---|---|
| `PACKET.md` | The packet sent verbatim to every Lane A reviewer, plus the reviewer assignment table |
| `a1.json` … | Lane A reviewer outputs, in the protocol's schema |
| `b1.json` … | Lane B adversarial-cascade outputs |
| `merge.json` | Optional operator equivalence map for findings worded differently by different reviewers |
| `adjudication.json` | Lane C dispositions, plus `missed_by_all` filled in retrospectively |
| `RESULT.md` | `review_independence.py` output and the operator's decision |

## Why this directory exists rather than `.agent-surface/`

ADR-18's reuse gate requires `reuse.reviewer.record` to be a repository-relative
path to a real file, and `_record_problems` in `spec_gate.py` checks that the file
exists, is inside the repository, and is a regular file.

`.agent-surface/` sits at the **workspace root, one level above this repository**,
and `.agent-surface/reasoning/ensemble/` is additionally gitignored
(`.gitignore:75`). So a record pointing there is unresolvable twice over: it
escapes the repository containment check, and it is absent from any clone.

**Fixed instance, 2026-08-24 / 2026-08-26.**
`FLOSS/docs/adr/ADR-20-provenance-validator-reconciliation.md` recorded its
reviewer as
`.agent-surface/reasoning/ensemble/20260824T023542Z_97e6b32c78072e8b_synthesis.json`.
The synthesis was copied to
[`2026-08-24-adr20-adversarial-audit/synthesis.json`](2026-08-24-adr20-adversarial-audit/synthesis.json)
byte-identically, the ADR and registry were repointed, and the original was
removed so two copies cannot drift.

**Why nobody noticed.** The record was never checked. `_reviewer_problems` — and
therefore the record-resolution check inside it — runs only for `tier == 2`
(`spec_gate.py:581`), and that entry is tier 1. Its `reviewer` field was freeform
prose that happened to mention a path. Confirmed by running `_reviewer_problems`
directly against the old value: it returns *"does not exist — an unresolvable
record is not evidence"*. The gate would have caught this the moment it applied,
and it never applied.

That is worth generalising: **a tier-1 entry's reuse block is recorded but not
validated.** Any evidence claim living in a tier-1 block is unchecked prose, and
should be read that way until the entry is promoted.

Review records are evidence. Evidence that only the author can resolve is not
evidence.
