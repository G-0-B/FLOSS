# Work-Board Reconciliation Design — Proposed Delta

```yaml
id: flossi0ullk-work-board-reconciliation-delta
version: 0.1.0
date: 2026-09-05
status: Proposed; operator review required; does not edit the target
truth_status: Specified
target: docs/superpowers/specs/2026-09-05-work-board-reconciliation-design.md
target_version: 0.1.1
target_head_observed: f114dde1f81adfc3933d2c6c437c29df422c48fd
author: Hermes (single reviewer; independent audit filed alongside)
audit_record: docs/reviews/2026-09-05-work-board-reconciliation-design/RESULT.md
```

This delta is a critic's patch list, not an edit. It applies the findings of the
independent audit (`audit_record` above) plus the five accepted ROI improvements
to the target design. The target's documentation-only scope, file scope (§7),
and review gate (§9) are unchanged by every item below. Apply by hand or by
patch; then run the apply-and-verify checklist at the end.

## D1 — Re-anchor two stale source hashes; freeze all six sources at execution (audit F1 + ROI #2 half)

Location: §9 hash table + §6A first bullet.

Problem: the table binds coordination plan `4a041d…` and coordination design
`e62e28…`, but `3f9e1ab` edited both files afterward. Current bytes at
`f114dde` are `60f98e805a043f1a8bc57b8d02974415444b71108203cd0a6d685c3ee1daa15d`
(plan) and `08b6ca20c2506a6e1df51e71dc120e13d6f8c8683caec3fd4162008ece226ee5`
(design). The other four rows re-verify clean. Recompute both rows at apply
time (values above are expected-as-of-`f114dde`, not promises), and annotate the
table: "anchors as of `<commit>`; §6A re-anchors before use."

Change §6A first bullet from freezing "board bytes/hash, local HEAD and
worktree/index state" to freezing "board bytes/hash, the six §9 source
bytes/hashes, local HEAD and worktree/index state." Rationale: without the
sources in the freeze list, a diligent executor fails closed on the first
verification step — this exact drift already happened once inside the design
itself.

## D2 — §6A step zero: shared-precondition snapshot (ROI #1)

Insert as the first work unit of §6A, before per-item inventory:

> Capture once, cite everywhere: `git worktree list --porcelain`, remote merge
> topology (`git branch -r --merged` / `--no-merged` against the tracked
> default), one time-bounded port-7334 connect check (record TCP result and any
> banner; no writes, no restarts), and the frozen board hash — into the receipt
> directory. Per-item branch/commit/service checks in §6B become lookups
> against this snapshot, not fresh discovery.

Suggested commands (bash; quote paths; record stdout verbatim, interpret later):

```bash
B="C:/~shit/FLOSS/docs/research/2026-05-15-working-todo-list.md"
R="C:/~shit/FLOSS/docs/reviews/2026-09-05-work-board-reconciliation"
git -C C:/~shit/FLOSS worktree list --porcelain > "$R/worktrees.txt"
git -C C:/~shit/FLOSS branch -r --merged origin/HEAD > "$R/branches-merged.txt"
git -C C:/~shit/FLOSS branch -r --no-merged origin/HEAD > "$R/branches-unmerged.txt"
curl -s -m 5 -o /dev/null -w "port7334_http=%{http_code} curl_rc=$?\n" http://127.0.0.1:7334/ > "$R/port-7334.txt" 2>&1
sha256sum "$B" > "$R/board-hash.txt"
```

Rationale: the board names 66 SHAs and the checkout holds 15+ worktrees;
per-item branch/commit resolution is the dominant §6B cost, and nearly all of
it reduces to these shared facts. Grounding counts (verified 2026-09-05 at
`f114dde`): 0 checkboxes, 23 `###`/`####` subsections, 101 status-keyword
hits, 66 unique SHAs, 0 port refs in the board.

## D3 — Machine-generate the inventory candidate index (ROI #3 + audit F4 mitigation)

Append to §6A inventory bullet: before human disposition, emit a numbered
candidate index from the frozen board bytes and dispose candidates instead of
discovering obligations by eye:

```bash
B="C:/~shit/FLOSS/docs/research/2026-05-15-working-todo-list.md"
grep -n -e "^#\{1,4\} " -e "OPEN" -e "DONE" -e "MERGED" -e "BLOCKED" -e "DEFERRED" -e "superseded" -e "SUPERSEDED" "$B" > candidates.txt
grep -n -o -E "[0-9a-f]{7,40}" "$B" | sort -t: -k2 -u > candidate-shas.txt
```

Rule: the machine proposes candidates only; workflow/evidence/authority
dispositions stay human (no script decides item state — that would smuggle in
the unapproved derived-view machinery). The §6D reviewer diffs coverage
against this same index, which closes the circular-coverage concern: 100%
means dispositions ÷ indexed candidates, with the index itself frozen and
reviewable.

## D4 — Revision-relation table, computed once (ROI #2)

Append to §4 (after the M1 bullet): freeze one revision table in the receipt
and cite it everywhere M1 scope arises, instead of re-deriving per item:

```bash
P="docs/superpowers/specs/2026-09-02-coordination-v1-design.md docs/superpowers/plans/2026-09-02-coordination-v1.md"
git -C C:/~shit/FLOSS log --oneline c1a08f1e528dc29fa885c2d71b04908b4f90f345..HEAD -- $P
git -C C:/~shit/FLOSS diff c1a08f1e528dc29fa885c2d71b04908b4f90f345 HEAD --stat -- $P
```

Known content at `f114dde` (re-verify at execution): four post-submission
commits touch those paths — `35cb173`, `f07b1f5`, `08b377e`, `3f9e1ab` — so the
M1 DEFERRED binds none of the current text. Record each commit's one-line
scope alongside.

## D5 — Filter pass before verification pass (ROI #4)

Prepend to §6B: dispose `retained-context` items first (intent-level and
research-context obligations needing judgment only, no commit/branch/service
checks). This shrinks the queue before expensive evidence checks run and
surfaces the true verification workload early enough to re-tranche. No new
disposition value needed — §6A already defines retained context.

## D6 — §6A is parallelizable by source (ROI #5)

Add one sentence to §6A: "Inventory tranches are independent by §3 source row;
the merge key is the receipt-local ID (original ID + heading/line + frozen
board hash)." Rationale: the ID scheme is already partition-friendly; stating
it unlocks delegated/AFK execution of the most labor-intensive phase. §6A is
read-only, so no canon risk.

## D7 — Replace `.toilet` links with hash-anchored prose citations (audit F2)

The three `../../../../.toilet/…` links (two atlas entrypoints, one v0.4 bundle
README) resolve outside the FLOSS repo into gitignored scratch: unresolvable
on fresh clone, unrendered on GitHub, unprotected by version control. Replace
each with a non-link citation of the form `` `.toilet/<packet>/START_HERE.md`
(SHA-256 `<hex>`, snapshot commit `<sha>`, outer-workspace scratch —
not in this repo; see §9 anchors) ``. Require the execution receipt to vendor
verbatim any share-set actually relied upon.

## D8 — Header `revision_base_commit` (audit F3)

Bump to `f114dde` (the commit that landed v0.1.1 content) or annotate:
"v0.1.1 content landed in `f114dde`; anchored against `3f9e1ab`." One line.

## D9 — §6D reviewer completeness sample (audit F4)

Add to the §6D reviewer checklist: "sample two sections against the §6A
candidate index (`candidates.txt`) hunting for un-inventoried obligations;
record the sample result in the receipt." Two lines; converts 100%-coverage
from self-defined to sampled-verified.

## D10 — Section H suspension needs explicit ack (audit F5)

§6C's "do not run Section H's old timed-purging convention" overrides a
standing rule of the artifact being edited. Correct call for a lossless first
pass, but make it an explicit operator-ack checkbox in the review gate rather
than an embedded instruction.

## Non-changes (deliberately out)

- No automation of dispositions or state derivation (would smuggle
  unapproved derived-view machinery through the back door).
- No coverage-percentage target above the D9 sample (a bigger number
  incentivizes under-inventorying).
- No atlas refresh (both packets checksum-clean; refresh is a separate dated
  packet or nothing).

## Apply-and-verify checklist

1. Apply D1–D10 to the target; keep the diff to that file (scoped commit per
   project Rule 12a; never bare-commit in the shared checkout).
2. Recompute all eight §9 hashes at the apply commit; every row must match.
3. Re-run `python FLOSS/scripts/spec_gate.py --check` (real exit via
   `${PIPESTATUS[0]}`); output must equal the §9 baseline plus no new finding
   attributable to these edits.
4. Re-run the D2/D3/D4 commands verbatim in bash; they must exit 0 on the
   operator host before the execution plan references them (a plan citing
   unrun commands repeats the failure in project Rule 11).
5. Operator review gate (§9 target) still blocks execution planning; this
   delta does not satisfy it.
