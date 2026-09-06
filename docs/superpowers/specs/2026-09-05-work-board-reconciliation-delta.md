# Work-Board Reconciliation Design — Proposed Delta

```yaml
id: flossi0ullk-work-board-reconciliation-delta
version: 0.1.1
date: 2026-09-05
status: Proposed; operator review required; does not edit the target
truth_status: Specified
target: docs/superpowers/specs/2026-09-05-work-board-reconciliation-design.md
target_version: 0.1.1
head_observed: 2528e77a988630b9f4a1c7fcddd4becea39a8b39
author: Hermes (single reviewer; independent audit filed alongside)
audit_record: docs/reviews/2026-09-05-work-board-reconciliation-design/RESULT.md
external_review: docs/reviews/2026-09-05-work-board-reconciliation-design/astra-light-review.md
adjudication: docs/reviews/2026-09-05-work-board-reconciliation-design/adjudication.md
```

v0.1.1 adjudicates the external review (`external_review`, dispositions in
`adjudication`): D1/D2 adopted with limits, D3 substantially revised, D4
rephrased, D5–D7 safeguards added, D8/D10 conceded and restated, D2 curl
defect fixed. This delta is a critic's patch list, not an edit. The target's
documentation-only scope, file scope (§7), and review gate (§9) are unchanged
by every item below.

## Observed hash history (dated, not expectations)

Anchors are observations bound to a commit, never promises. At execution,
capture fresh hashes for every source actually used and record them alongside
the historical rows — never overwrite history with current bytes.

| Source | Design table (v0.1.1) | Audit (HEAD `f114dde`) | Adjudication (HEAD `2528e77`) |
|---|---|---|---|
| Board | `6d187e55…` | `6d187e55…` ✅ | `6d187e55…` ✅ unchanged |
| Coord plan | `4a041d…` | `60f98e…` (stale) | `d48d78ce…` (changed again) |
| Coord design | `e62e28…` | `08b6ca…` (stale) | `08b6ca…` ✅ stable |
| Polyglot / reminder / room-v0 | as tabled | all match ✅ | re-verify at execution |

Three distinct plan hashes in one day is the live argument for D1: any table
frozen at authoring time is stale by execution time.

## D1 — Freeze all sources at execution (adopted, reframed)

Location: §9 hash table + §6A first bullet.

Change §6A first bullet from freezing "board bytes/hash, local HEAD and
worktree/index state" to freezing "board bytes/hash, the §9 source
bytes/hashes *as actually used*, local HEAD and worktree/index state." The
receipt records a two-column row per source: historical anchor (from the
table above, with its commit) and execution hash (freshly computed). A
mismatch between them is routine drift to note, not a failure — the
execution hash governs, the anchor explains.

## D2 — §6A step zero: timestamped shared-precondition snapshot (adopted with limits)

Insert as the first work unit of §6A, before per-item inventory:

> Capture once, cite everywhere, refresh on change: `git worktree list
> --porcelain`, remote merge topology, one time-bounded port-7334 connect
> check, and the frozen board hash — timestamped, into the already-planned
> receipt directory (no new output files beyond §7 scope). Per-item
> branch/commit/service checks in §6B become lookups against this snapshot.
> Refresh the snapshot when relevant state changes (new commits on the
> branch, new worktrees, service restarts); stale snapshots are labeled
> with their capture time, not silently reused.

Limits (verified 2026-09-05: `FETCH_HEAD` mtime 2026-09-03 vs session
2026-09-05 — remote-tracking refs were 2 days stale): `git branch -r`
output is **last-fetch state** and cannot establish live PR status. Live
merge/landing assertions require a refetch or the separately gated
`--online` path; until then they stay `unverified (last-fetch <timestamp>)`.

Corrected commands (bash; quote paths; record stdout verbatim — the v0.1.0
`curl_rc=$?` inside `-w` expanded *before* curl ran and printed `0` on a
real exit 7; reproduced live, fixed below):

```bash
B="C:/~shit/FLOSS/docs/research/2026-05-15-working-todo-list.md"
R="C:/~shit/FLOSS/docs/reviews/2026-09-05-work-board-reconciliation"
git -C C:/~shit/FLOSS worktree list --porcelain > "$R/worktrees.txt"
git -C C:/~shit/FLOSS branch -r --merged origin/HEAD > "$R/branches-merged.txt"
git -C C:/~shit/FLOSS branch -r --no-merged origin/HEAD > "$R/branches-unmerged.txt"
curl -s -m 5 -o /dev/null -w "port7334_http=%{http_code}\n" http://127.0.0.1:7334/ > "$R/port-7334.txt" 2>&1; echo "curl_rc=$?" >> "$R/port-7334.txt"
sha256sum "$B" > "$R/board-hash.txt"
date -u +"%Y-%m-%dT%H:%M:%SZ" > "$R/snapshot-time.txt"
```

Grounding counts (verified at `f114dde`): 23 `###`/`####` subsections, 66
hex-token hits (see D3 — raw pattern output, not a SHA list), 0 port refs.

## D3 — Structural candidate index; accounting separated from completeness (substantially revised)

The v0.1.0 keyword filter is withdrawn: reproduced live, it misses board
lines 715 (ARF deep-dig), 716 (Yumeichan consolidation), 722
(ConversationMemory↔MultiScaleEmbedding) — all table rows whose
`Not started`/`Open`/`Partial` statuses never match case-sensitive keywords
— plus every other obligation expressed as a table row. Replacement, verified
live (373 candidates; lines 715/716/722 all INDEXED):

```bash
B="C:/~shit/FLOSS/docs/research/2026-05-15-working-todo-list.md"
grep -n -e "^#\{1,4\} " -e "^|" -e "^- " -e "^[0-9][0-9]*\. " "$B" > candidates.txt
```

Rule: review headings, table rows, bullets, numbered items, and prose —
the machine proposes structural candidates only; humans dispose. Candidate
accounting (dispositions ÷ frozen index lines) is reported separately from
any completeness claim; the index itself is frozen and reviewable, which is
what makes the denominator honest.

SHA-locator step: raw hex-pattern output is *not* a SHA list (live sample:
66 tokens, **0** full-length SHAs — mostly claim-ID fragments split on
dashes). Extract tokens, then verify each against the object store; keep
only what resolves:

```bash
grep -n -o -E "[0-9a-f]{7,40}" "$B" > sha-tokens.txt
# per token T: git -C C:/~shit/FLOSS cat-file -t "$T"  (verified discriminating:
# 193729c -> commit; 019e41d3 / 20260519 -> "Not a valid object name")
```

Cost honesty: the structural queue (~373) is ~5× the keyword queue (~69).
That is the true price of not missing Section E. Mitigations: D5 ordering,
per-item note cap, §6A parallelization.

## D4 — Revision table with exact decision scope (rephrased)

Freeze one revision table in the receipt and cite it everywhere M1 scope
arises:

```bash
P="docs/superpowers/specs/2026-09-02-coordination-v1-design.md docs/superpowers/plans/2026-09-02-coordination-v1.md"
git -C C:/~shit/FLOSS log --oneline c1a08f1e528dc29fa885c2d71b04908b4f90f345..HEAD -- $P
git -C C:/~shit/FLOSS diff c1a08f1e528dc29fa885c2d71b04908b4f90f345 HEAD --stat -- $P
```

Scope wording (corrected from v0.1.0): the M1 DEFERRED **stands for the
submitted revision** (`c1a08f1`+`ff1f5c0`); the table identifies what changed
since. Later edits neither erase that decision nor inherit approval.
Known content (re-verify at execution): four post-submission commits touch
those paths — `35cb173`, `f07b1f5`, `08b377e`, `3f9e1ab`.

## D5 — Filter pass before verification pass (with safeguard)

Prepend to §6B: dispose `retained-context` items first (judgment only, no
commit/branch/service checks) to shrink the queue before expensive evidence
checks. Safeguard: intent-level obligations must not disappear as "context"
— retained-context items keep full source linkage and enter the D6
cross-source reconciliation like any other disposition.

## D6 — §6A parallelizable by source; merge pass stays central (with safeguard)

Add to §6A: "Inventory tranches are independent by §3 source row; the merge
key is the receipt-local ID (original ID + heading/line + frozen board
hash)." Per-item locator is source path + source hash + locator — the board
hash anchors board-origin items only, never every source. The
cross-source duplicate/supersession reconciliation is explicitly a central,
single-threaded pass over the merged tranches — parallelize discovery,
never the merge.

## D7 — External sources: label + vendor bounded excerpts (adopted)

Replace the three `../../../../.toilet/…` links (two atlas entrypoints, one
v0.4 bundle README — all resolving into gitignored outer-workspace scratch)
with non-link citations: path + SHA-256 + snapshot commit + an explicit
`external scratch, not in this repo` label. Availability fix (beyond
rendering): the receipt vendors verbatim **only the bounded excerpts
actually relied upon**, cited to their source packet. Excerpts live in the
receipt, never copied as requirements into the board.

## D8 — Landing-commit annotation (defect withdrawn)

v0.1.0's "revision_base trails its landing" is withdrawn as a defect: a
revision's base normally precedes its landing. Optional one-line addition if
useful: `landed_in: <commit>` in the header. Nothing demanded.

## D9 — Reviewer coverage duty (reframed)

Add to the §6D checklist: "dispose review against the frozen D3 candidate
index; hunt specifically for structurally indexed lines with no disposition;
record indexed-but-undisposed lines as gaps, not silent non-items." The
two-section sample is retained only as a smoke check and labeled as such —
sampling cannot prove exhaustive coverage; the frozen, reviewable index is
the actual control.

## D10 — Purge policy (gate item withdrawn, restated as scope note)

No extra approval is needed to *not* purge inside an already-selected
lossless pass — that is entailed scope, not an override. Restatement: "This
pass performs no Section-H purges; the purge policy itself is unchanged and
no policy decision is implied. Permanently changing the purge policy would
be a separate decision." §6C keeps its "do not run timed-purging" line under
this reading.

## Non-changes (deliberately out)

- No automation of dispositions or state derivation (would smuggle
  unapproved derived-view machinery through the back door).
- No coverage-percentage target above the D9 index control (a bigger number
  incentivizes under-inventorying).
- No atlas refresh (both packets checksum-clean; refresh is a separate dated
  packet or nothing).
- No runtime derived status, agent assignments, additional output files, or
  permanent policy changes — each needs separate authorization.

## Apply-and-verify checklist

1. Apply D1–D10 to the target; keep the diff to that file (scoped commit per
   project Rule 12a; never bare-commit in the shared checkout).
2. Recompute all §9 hashes at the apply commit; record historical + fresh
   side by side per D1.
3. Re-run `python FLOSS/scripts/spec_gate.py --check` (real exit via
   `${PIPESTATUS[0]}`); no new finding attributable to these edits.
4. Run the D2/D3/D4 commands verbatim in bash on the operator host; all
   must exit 0 and the D3 membership spot-checks (715/716/722 INDEXED)
   must pass before the execution plan references them.
5. Operator review gate (§9 target) still blocks execution planning; this
   delta does not satisfy it.
