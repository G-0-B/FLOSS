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
path to a real file, and `spec_gate.py` checks that the file exists.

`.agent-surface/reasoning/ensemble/` is gitignored (`.gitignore:75`). A reuse
block pointing there passes the gate on the machine that ran the poll and points
at nothing in a fresh clone — the record exists for the author and not for the
auditor, which is the opposite of what a review record is for.

**Known instance:** `FLOSS/docs/adr/ADR-20-provenance-validator-reconciliation.md`
currently records its reviewer as
`.agent-surface/reasoning/ensemble/20260824T023542Z_97e6b32c78072e8b_synthesis.json`.
That file exists locally and is not tracked. Not fixed here — flagged, because
re-pointing an ADR's evidence is an operator decision, and because the honest fix
is to copy the synthesis into a tracked record rather than to quietly change the
path.

Review records are evidence. Evidence that only the author can resolve is not
evidence.
