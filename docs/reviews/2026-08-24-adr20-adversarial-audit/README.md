# ADR-20 adversarial ensemble audit — 2026-08-24

Retroactive review record. This poll predates
[`manual-review-protocol-v1.0.md`](../../governance/manual-review-protocol-v1.0.md)
and does not conform to it — it is preserved because ADR-18's reuse gate cites it
as `reuse.reviewer.record` for `FLOSS/docs/adr/ADR-20-provenance-validator-reconciliation.md`.

| | |
|---|---|
| File | `synthesis.json` |
| SHA-256 | `94f419aa3ca545885c21f33da151ad475dc0067e39274b9cc09994034bd05c93` |
| Size | 200,104 bytes |
| Synthesis timestamp | `2026-08-24T02:35:15.906096+00:00` |
| `prompt_hash` | `97e6b32c78072e8b` |
| Voters | 6 (5 provider surfaces, 6 model families) |
| Prompt | "Critical adversarial audit of a proposed ADR (ADR-20, FLOSSI0ULLK provenance spine). Attack it. Do not summarize or agree — find what is wrong, missing, or dangerous." |

ADR-20 refers to this as "the 2026-08-23 ensemble audit". The synthesis timestamp
is 2026-08-24 UTC; both refer to this file.

## Why it was copied here

It previously lived only at
`.agent-surface/reasoning/ensemble/20260824T023542Z_97e6b32c78072e8b_synthesis.json`
— the workspace root, one level above this repository, in a gitignored directory
(`.gitignore:75`). That path was unresolvable from here twice over: outside the
repository, and absent from any clone.

It went unnoticed because it was never checked. The record-resolution guard runs
only for `tier == 2` entries (`spec_gate.py:581`) and ADR-20 is tier 1, so its
`reviewer` field was freeform prose that happened to contain a path. Running
`_reviewer_problems` against the old value directly returns *"does not exist — an
unresolvable record is not evidence"*: the gate would have caught it the moment
it applied, and it never applied.

Evidence only the author can resolve is not evidence.

Copied verbatim — byte-identical, hash above — and the original was removed so
there is one copy that cannot drift from the other.

## What this record does NOT support

Read the file, not its headline. The synthesis is labelled
`tier1 / largest_cluster_fraction 1.0 / "Unanimous consensus"` and that label is
false. Established in `docs/research/2026-08-25-provenance-failure-mode-register.md`
(CF-4) and in ADR-20's own "Correction to the Q1 tally (2026-08-26)":

- The clustering never measured consensus. Minimum off-diagonal cosine
  similarity in this file is 0.844 against a 0.75 threshold, so no pair could
  have been separated and a single cluster was the only reachable outcome.
- **Two of the six voters produced no position.** `groq-qwen3-27b` returned a
  bare unclosed `<think>` restatement of the prompt (2,291 chars);
  `groq-gpt-oss-120b` was truncated mid-sentence at 359 chars. Both were counted
  as converged voters, so the "5 provider surfaces / 6 model families" figure was
  satisfied on paper by voters that did not vote.
- The Q1 tally derived from it was wrong in ADR-20's first draft and is corrected
  in that ADR. `mistral-devstral-small` opened
  `**1. BLAST RADIUS: Substrate (0.85, override forbidden).**` and was filed on
  the System side.

The value of this file is the raw `voter_responses[]`, which is what made the
correction possible. Its top-level cluster metrics should not be cited.
