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

## Second packet type: fix-sweep handoffs

The table above describes a **protocol review** — one question put to several
reviewers in parallel, whose outputs are scored for independence by
`review_independence.py`.

A **fix-sweep handoff** is a different shape and gets its own directory under
the same naming scheme:

| File | Contents |
|---|---|
| `PACKET.md` | The handoff: range under review, what changed and why, how to verify, what the author could not verify, and what the internal review already found |
| `source-changes.patch` | Production changes only, one section per commit |
| `test-changes.patch` | Test changes only, same commits |
| `<reviewer>.md` / `.json` | External reviewer outputs, as they arrive |
| `internal-reviews.md` | Every internal review of the author's responses: prompt and return, verbatim |
| `RESULT.md` | Dispositions and the operator's decision |

First instance: [`2026-09-05-pr41-fix-sweep/`](2026-09-05-pr41-fix-sweep/).
A later round that responds to an audit is a new packet, so it gets its own
directory rather than editing the first one's `PACKET.md`:
[`2026-09-29-pr41-audit-response/`](2026-09-29-pr41-audit-response/).

### Why the two patches are split

So a reviewer reads the production change, forms their own view of what the
tests *should* assert, and only then reads what they do assert. Handed a single
diff, a reviewer reads the test as documentation of the fix and inherits the
author's blind spot — which is how a test that cannot fail survives review.

### What a fix-sweep packet must contain

Four things, all of them learned by their absence:

1. **The internal review's own findings, disclosed.** Every commit in the first
   packet had already been through a subagent review that found defects in four
   of six commits. Withholding that would have bought a flattering external
   report and spent the reviewer's attention re-deriving known results.
2. **An explicit unverified ledger.** Not "let me know if you spot anything" —
   a list of the specific claims the author could not check, and what goes
   wrong if each is false. A reviewer aims at stated uncertainty; they cannot
   aim at unstated confidence.
3. **Disagreements, recorded rather than dropped.** Where the author pushed back
   on an internal finding, the packet says so and states the reasoning, so the
   external reviewer can overrule it. A rejected finding that leaves no trace
   is indistinguishable from one that was never raised.
4. **Provenance of every commit in range.** If a branch carries commits by
   another author or another session, they are named and excluded. Handing
   someone else's work to a reviewer as your own wastes the review and
   misattributes the result.

### After the review comes back

Learned on the first round-trip:

- **The packet is not edited after it is sent.** It is the record of what the
  reviewer was given. Where the review shows a packet claim was wrong, the
  correction goes in `RESULT.md` beside it, naming the claim. Rewriting the
  packet would erase exactly the evidence of what the author believed.
- **Carry the reviewer's evidence into the directory**, content-identical,
  and check it for credentials first. Not byte-identical: the repository's
  line-ending rules normalize text files on commit, so say "content-identical"
  and keep the originals where byte equality might matter. A review whose evidence lives only on the
  reviewer's disk is not resolvable by anyone else — the same rule this README
  opens with. Large reproduction artefacts (exported snapshots, dependency
  caches) can stay behind; they reproduce the evidence rather than being it.
- **`RESULT.md` records the author's dispositions, and leaves the operator's
  decision as an explicit PENDING** until the operator writes it. The author
  answering their own review is not a decision.
- **Report lint counts over code paths only**
  (`ruff check packages scripts tests hooks`). The repository has no ruff
  configuration and CI does not lint, so a repo-wide `ruff check .` also counts
  any reviewer scripts carried into `docs/reviews/`.
- **Carry internal reviews verbatim, in `internal-reviews.md`:** the prompt as
  sent and the return as received, nothing edited but the harness's wrapper.
  A `RESULT.md` that only summarizes them asks the next reviewer to trust the
  author's reading of them. The second audit of the first packet said exactly
  that: summaries cannot be certified.
- **Recount before correcting a count.** A correction is a claim too. The
  first `RESULT.md` said four evidence files were normalized on commit; a byte
  comparison of the committed blobs showed two.

### Prompting a reviewer

Learned from a reviewer that found a real problem and did not report it.

The prompt for the internal review of `e747a75` said, in effect, *every fix on
this PR has introduced a defect; find the one this commit introduced.* The
reviewer checked zero, negative and out-of-range PIDs exactly as asked, found
they produce a false "gateway PID 0 is live" message, reasoned that this was
safe and not *introduced* by the commit, weighed whether to mention it — and
followed the prompt. It returned a bare "No issues." The observation existed
only in its reasoning.

- **A prior is a direction to look, not a filter on what to report.** "Find
  the defect this fix introduced" is a good hypothesis to aim with. As a
  reporting rule it silently discards everything else the reviewer notices,
  and the reviewer is the only one who noticed it.
- **Ask for three buckets, every time.** (1) Defects. (2) Observations below
  that bar — pre-existing issues, risks, untested cases, anything misleading
  even if safe. (3) What was checked and found clean, with the evidence. The
  operator decides scope after seeing all three; the reviewer's judgment about
  scope must never be the filter.
- **A bare "no issues" is not a result.** It collapses bucket 3, which is the
  only thing that distinguishes a thorough review from a skipped one. Ask
  again for the structured report before treating it as clean.
