# Adjudication — astra-light review of delta v0.1.0

```yaml
adjudicator: Hermes (delta author; single reviewer)
date: 2026-09-05
head_at_adjudication: 2528e77a988630b9f4a1c7fcddd4becea39a8b39
review_record: astra-light-review.md
delta_before: docs/superpowers/specs/2026-09-05-work-board-reconciliation-delta.md v0.1.0 (committed 990e2bc)
delta_after: v0.1.1 (this adjudication applied)
```

Standing rule: every finding dispositioned — fix, defer with reason, or rebut
with falsifying evidence. A rebuttal without evidence is just disagreement.

Ambient drift observed during adjudication: HEAD moved `f114dde` → `990e2bc`
(this audit's scoped commit) → `2528e77` (another hand; content unexamined
here). Board hash `6d187e55…` recomputed unchanged at `2528e77` — reviewer's
"board's hash is unchanged" confirmed. Coordination plan hash moved
`60f98e…` → `d48d78ce…` — reviewer's "changed again" confirmed.

## Verdicts

| # | Reviewer position | Reproduction / evidence | Verdict | Delta disposition |
|---|---|---|---|---|
| D1 | Accept; preserve historical + capture fresh; plan changed again | Confirmed: plan now `d48d78ce…` (was `60f98e…` at audit). Three distinct plan hashes in one day | **ADOPT** (strengthens D1) | Reframed: anchor table becomes dated observations, never expectations; execution captures fresh hashes for every source used |
| D2 | Accept with limits: timestamp/reuse/refresh; remote-refs ≠ live PR status; embed in existing receipt | Confirmed: `FETCH_HEAD` mtime 2026-09-03 vs session 2026-09-05 — remote-tracking refs 2 days stale; `origin/feat/coordination-room` (`2eff97c`, 09-03) trails local HEAD | **ADOPT** all limits | Snapshot gains timestamps + refresh triggers; `branch -r` labeled last-fetch state, live PR status needs `gh`/`--online` (separately gated); outputs land in the already-planned receipt dir |
| D2-curl | `$?` expands before curl runs; printed `curl_rc=0` on exit 7 | **Reproduced live**: `actual_rc=7`, file says `curl_rc=0`. Author error, no defense | **CONFESS + FIX** | Command rewritten (`; echo "curl_rc=$?"` after); author notes Rule-11 failure — a checked command shipped unrun |
| D3 | Keyword filter misses lines 715/716/722; SHA pattern over-captures; sample ≠ proof | **Reproduced live**: all three MISSED by v0.1.0 filter. 715 = ARF deep-dig, 716 = Yumeichan consolidation, 722 = ConversationMemory↔MultiScaleEmbedding — all table rows (`Not started`/`Open`/`Partial` never match case-sensitive keywords). SHA output: 66 tokens, **0 full-length SHAs** — mostly claim-ID fragments (`019e41d3` etc.) | **SUBSTANTIALLY REVISE** as demanded | Structural-element index (`^#{1,4}`, `^\|`, `^- `, numbered items) replaces keywords — verified: 373 candidates, all three lines INDEXED. SHA step becomes extract + `git cat-file -t` per token (verified discriminating: `193729c`→commit; `019e41d3`,`20260519`→not objects). Coverage redefined as dispositions ÷ frozen structural index, with the index reviewable; sample check kept but labeled smoke-check, not proof |
| D4 | Keep table; reject "binds none of the current text"; edits neither erase decision nor inherit approval | Reviewer's formulation is strictly more correct and compatible with the design's own "not extend that decision to unreviewed text" | **ADOPT correction** | Rephrased: M1 DEFERRED stands for submitted revision `c1a08f1`+`ff1f5c0`; table shows per-commit delta; nothing later is covered, nothing earlier is erased |
| D5/D6 | Safeguards: context items keep linkage; locator = source path + hash + locator; merge pass stays central | Valid gaps in v0.1.0: filter-first risked context items escaping reconciliation; D6 never named the merge step | **ADOPT** | Retained-context items carry source linkage and enter cross-source reconciliation; receipt-local ID clarified as the *merge key*, per-item locator as source path + source hash + locator; cross-source duplicate/supersession pass explicitly single-threaded/central |
| D7 | Plain-text citations don't fix availability; vendor bounded excerpts, label external | Correct: delinking solves rendering, not availability | **ADOPT** | Receipt vendors verbatim only the excerpts relied upon (bounded, cited); sources labeled external/scratch |
| D8 | No defect: base normally precedes landing | Conceded — F3 was the audit's weakest item ([low] by its own label); convention reading is correct | **CONCEDE** (withdraw defect) | D8 replaced: optional `landed_in` annotation, no bump demanded |
| D10 | No extra approval to *not* purge inside an already-selected lossless pass | Conceded — suspension during a lossless pass is entailed by selected scope, not an override; only permanent policy change needs a decision | **CONCEDE** (withdraw gate item) | Restated as scope note: this pass performs no purges; policy unchanged, no decision implied |

## What the reviewer got wrong or overstated — nothing material

The "SHA pattern captures dates" example is imprecise as stated (dashed
dates like `2026-05-15` cannot match `[0-9a-f]{7,40}`; the actual pollutants
are compact timestamps and claim-ID fragments), but the over-capture
conclusion is correct and the fix (per-token `cat-file` verification) covers
all three pollutant classes. Noted here so the record is exact; no rebuttal —
the disposition is identical either way.

## Cost honesty on the revised D3

Structural index yields 373 candidates vs the keyword filter's 69. The queue
is ~5× larger — that is the true price of not missing Section E. Mitigations
retained: D5 filter-first ordering, per-item note cap, §6A parallelization.
Coverage is now well-defined (denominator frozen and reviewable) at the cost
of a larger numerator. Recommended as worth it: a missed Yumeichan-class
obligation is exactly the failure this reconciliation exists to prevent.
