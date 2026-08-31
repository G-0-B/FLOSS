# What thirty-two review rounds taught, 2026-08-31

**Truth status:** ✅ Verified — every claim here is traceable to a commit on
`reconcile/pr38-salvage-20260817` (PR #41), a review thread on that PR, or a
test in the tree. Nothing is inferred.

**Scope.** One continuous session: 32 commits from `08619f0` to `a8afdf5`,
25 files, +5,732/−351 lines, test suite 908 → 959. Roughly 35 review findings
from two independent reviewers plus 7 from a cold read. Every finding was
valid; none was rejected as wrong.

**Relationship to existing docs.** This EXTENDS
`2026-08-25-provenance-failure-mode-register.md`, which holds FM-1..FM-8 and
CF-1..CF-10. New failure modes continue that numbering from FM-9 and CF-11.
Skill-level observations 1..11 live in the operator's observation log
(`skill-observations/log.md`).

---

## 1. The headline number

**Of ~35 findings, 29 were defects in fixes made earlier in the same session.**

Nine consecutive rounds found nothing but consequences of the previous round.
The rate did not fall as the work went on. It fell only when a reviewer moved
one level down the stack — see FM-9.

That number is the reason this document exists. A green suite, a clean linter
and a passing spec-gate were true at every one of those 32 commits.

---

## 2. New failure modes

### FM-9 — The fix aimed at the wrong layer

The clearest case is the file lock, which took **seven rounds**:

| Round | What changed | Layer |
|-------|--------------|-------|
| 1 | Added a lock at all | mechanism (absent) |
| 2 | Stale reclamation by age | policy |
| 3 | Reclamation gated on owner liveness | policy |
| 4 | Liveness gated on process-creation token | policy |
| 5 | Stale window parameterised per caller | policy |
| 6 | Reclamation made atomic (rename, not unlink) | **mechanism** |
| 7 | Rollback made non-destructive (O_EXCL, not rename) | **recovery** |

Rounds 2-5 each fixed the failure the previous round caused, because they all
adjusted *when a holder is considered dead* while the operation underneath --
"delete whatever is at this path" -- was unsound the whole time. No amount of
better policy repairs a non-atomic primitive.

**Rule.** When round N+1 finds a defect in round N's fix, do not fix round N's
fix. Ask which of three layers the change touched, and whether the defect lives
one below:

- **Mechanism** -- what operation is performed (is it atomic? can it lose?)
- **Policy** -- when the operation is allowed
- **Recovery** -- what happens when the operation loses a race

Two consecutive findings at the policy layer is the signal to go down a level.

### FM-10 — Extending a function's domain silently re-scopes every branch in it

`_reclaim_claim_if_unchanged()` was written for pid files, then also used for
identity sidecars. Its `ImportError` fallback -- an unconditional `unlink()` --
had been correct for the original domain and became a data-destroying path in
the new one. **Nothing about the fallback changed.**

Same shape: `load_anchor()` returning `None` was widened to cover "corrupt" as
well as "absent", and every caller branching on `None` silently acquired a
wrong branch -- most damagingly `_publish`, where `None` meant "safe to start a
fresh genesis over a store with no predecessor".

**Rule.** When a function gains a caller of a different kind, or a sentinel
gains a second meaning, re-read every branch and error path against the new
domain. The branches that do not change are the dangerous ones, because nothing
in the diff points at them.

### FM-11 — Guarding on what a file says instead of what it can prove

Three instances in `anchor.py`, each found separately:

1. A **count** used where a **set** was meant (`ANCHOR_STALE` compared lengths).
2. A **locator** used where a **digest** was meant -- position, then path, then
   count: the same defect renamed twice by its own fixes.
3. A **version string** trusted where a **signature** was available. Editing `v`
   to garbage made `publish` discard the predecessor and sign a fresh genesis
   over a truncated store, laundering the loss with no `--force`. Reproduced.

In all three the proof was already in the same document; the guard asked the
cheaper question.

**Rule.** For any guard on operator- or attacker-writable data, ask what in the
artefact cannot be forged and guard on that. `v` is a field; the signature over
`v` is proof.

### FM-12 — Constants that agree by coincidence, not by coupling

`VOTER_CALL_TIMEOUT_SECONDS = 60` and the OmniRoute client's `timeout=60.0`
default matched, so the OmniRoute path *looked* correct while forwarding
nothing. litellm -- the DEFAULT backend -- forwarded nothing and had no default
at all, so a stalled provider ran past the budget the client timeout was
derived from. A review note asserting OmniRoute "already forwards it" was
wrong, and checking rather than accepting it is what found the second half.

**Rule.** If a budget is asserted anywhere, the code that spends it must
receive it explicitly. Two constants with the same value are not a coupling.

### FM-13 — Deriving a value instead of reading its source

Three instances, each shipped as the fix for the previous one:

- `MAX_ROSTER_FOR_BUDGET = 4` typed by hand, in a commit whose own comment read
  *"a config that has to clear a budget must READ the budget"*. The registry
  offers profiles of 6, 8 and 12; a valid 12-voter round cost 720s against a
  projection derived from 4.
- `WORST_CASE_RUN_SECONDS` summed by hand as probe + generate + embed = 275.
  The real path includes a second embed in the logging step: 365. The test
  meant to catch this **re-derived the same wrong sum and agreed with itself**.
- `EMBED_MODEL` derived independently in three modules, so a vector could be
  produced by one model and labelled with another -- and two fixes to the
  downstream copies could not work, because the source that produced the label
  was the third.

**Rule.** A test that recomputes a value independently proves only that two
derivations agree. Read the source of truth; have the test read the same one.

### FM-14 — Output describing a state the code did not achieve

An extension of FM-2 (*naming the conclusion instead of showing the work*),
moved from probes into user-facing output and comments. Six instances:

- `stop_mcp_daemons.ps1` printed "All daemons stopped. PID files cleaned."
  unconditionally, including from six branches that deliberately left things
  running.
- `start_mcp_daemons.ps1` printed "OmniRoute started" on the line after
  "Stopped the unrecorded OmniRoute".
- The degraded ensemble writeup always said "Fewer than 3 voters produced
  embeddings", including when three did and the survivors' *independence* was
  the failure -- sending an operator to hunt for dead voters that were fine.
- `_store_lock`'s docstring accurately described a lock the packet writers did
  not take. Accuracy is what made it worse; see CF-13.
- `_series_order`'s comment promised a filename tie-break the tuple omitted.
- `lock_file` documented its `timeout_seconds` as "accepted for call-site
  compatibility" -- a comment excusing a silently ignored argument.

**Rule.** A summary line is a claim. If any branch above it can decline to act,
the summary must be conditional on what happened and the exit code must match.

### FM-15 — Importing a small primitive through a heavyweight module

`watch_intake.py` had been standard-library-only. Reusing the file lock by
importing it *from `provenance`* pulled in blake3, jcs and PyNaCl -- present
only in `requirements-ci.txt` -- and broke `watch_intake.py --help` outright on
a lean install.

`packages/activity_log/__init__.py` already keeps `provenance` lazily imported
and its docstring says exactly why. **The file documented the constraint and
the import was added anyway.**

**Rule.** "Reuse, don't reimplement" is about the implementation, not the
import path. Importing a small primitive through a heavy module is a dependency
decision wearing a code-sharing costume. Extract the primitive.

---

## 3. Tests that could not fail

**Ten instances in one session.** This is the highest-yield section here,
because every one of them was counted as coverage and none of them could have
caught the defect it was written for.

| # | The test | Why it could not fail |
|---|----------|----------------------|
| 1 | Duplicate-root resolution | Sorted-glob order happened to give the right answer for that fixture |
| 2 | Pointer staging name | Asserted no leftover `.tmp` remained -- true either way, the rename consumes it |
| 3 | Retention race | Simulated a *collision*, which the old code already handled, not the *race* |
| 4 | Legacy voter pool | Checked `DEFAULT_VOTER_POOL[0]`, the one slash-free entry of four |
| 5 | Embedder identity | Used `is` across a module reload, comparing test artefacts |
| 6 | Declared transport | Asserted a docstring exists and a string contains a slash |
| 7 | Broken-history block | Asserted only that its own fixture committed to some leaves |
| 8 | Reservation ordering | Exercised the helper when the change was in the caller's ordering |
| 9 | Summary guard (x2) | Matched the prose of the comment explaining the code, not the code |
| 10 | Sidecar ordering | Encoded an *ordering* that later legitimately changed |

### The five shapes

1. **Assert the aftermath.** The observable end state is identical under both
   implementations (#2). Assert the operation, not its residue.
2. **Assert the fixture.** The test verifies its own inputs (#7).
3. **Assert the wrong unit.** The change is in the caller; the test drives the
   callee (#8), or vice versa.
4. **Match prose, not code.** `text.find("Daemons started")` hits the comment
   that explains the summary, not the `Write-Host` that emits it (#9). Anchor
   on the emitting statement.
5. **Encode ordering, not invariant.** Correct until the order legitimately
   changes, then wrong (#10). Assert what must hold under any order.

### The meta-finding

**Naming the pattern did not stop it.** A fake test (#6) was written *minutes
after* describing this exact habit in a commit message. The only reliable
counter was mechanical: run the test against the unfixed code, every time,
without exception.

**Rule.** Red-green verifies the FIXTURE, not just the fix. A test that passes
red is not "unverified" -- it is misleading, because it is counted. The correct
response is to change the input until it discriminates, never to accept green.
Ask explicitly: *for this exact fixture, what answer would the old code give?*

---

## 4. Coordination and process findings

### CF-11 — A notification is not a description of state

The PR monitor relayed "1 new review comment"; the source held **three new
threads** and nine open. On another occasion it relayed six comments that
carried no findings at all -- stale bot summaries for commits already merged --
while thirteen real threads sat unresolved. Acting on the notification alone
would have produced nothing and reported "nothing to do" accurately about the
message and wrongly about the pull request.

Worse, and separately: **the open-thread count was misreported four times in a
row** (as "2" when it was 7) by carrying a remembered number forward instead of
re-querying. The correction only came from running the query.

**Rule.** A notification says something changed, never what is true. Any claim
about what remains outstanding must come from the system of record, at the
moment of the claim. Do not carry a count across turns.

### CF-12 — Two reviewers, three non-overlapping lenses

| Lens | Found |
|------|-------|
| Codex (deep single-file reasoning) | Guard logic, race conditions, one-path-of-two |
| CodeRabbit (diff-wide) | Value provenance, message truthfulness, dependency coupling |
| Cold read (whole-function, unchanged code) | Unswept siblings in code the diff never touched |

**None subsumes the others.** CodeRabbit found four defects the cold read had
walked past in a file it had just read twice. The cold read found seven that
neither reviewer could see, because those lines were not in any diff. Codex
found the two P1s.

**Rule.** Treat "the reviewer is green" as evidence about one lens only. A cold
read of the whole function is the only thing that inspects code the diff did
not touch, and it is exactly where "the guard covers one path of two" lives.

### CF-13 — Candour about a gap substitutes for closing it

`_store_lock` shipped with a docstring stating plainly that packet writers do
not take it, so it "narrows rather than closes" the window. That was true,
written specifically to avoid overclaiming -- and it functioned as a
replacement for the fix. The thread was replied to and resolved; the defect
stayed. The next reviewer's strongest evidence was the honest comment itself.
The real fix (atomic writes plus a two-agreeing-scans snapshot) was small and
had been available the whole time.

**Rule.** An accurate description of a limitation is not a resolution of it.
"Narrows but does not close", "best-effort", "advisory", "known limitation" in
code being offered as a fix -- stop and ask whether the real fix is out of
reach or merely less convenient. If it is reachable, the honest comment is a
way of feeling rigorous while shipping the gap.

### CF-14 — The rule stated in the same commit that violates it

Three times, a commit message or code comment articulated the correct principle
and the code beside it did the opposite:

- *"a config that has to clear a budget must READ the budget"* -- then
  hardcoded 4 (FM-13).
- *"never publish a record before the thing it cites exists"* -- then moved the
  proof above the pointer and not above `_retain_series`, one of two writers.
- `_series_order`'s comment promised a filename tie-break; the tuple had none.

**Rule.** Writing the rule down is not applying it. After stating a principle
in a commit, grep the diff for every site the principle governs before pushing.

---

## 5. The single dominant pattern

Across ~35 findings, one shape accounts for most of them:

> **A correct mechanism attached to the wrong scope.**

Right function, wrong caller. Right lock, wrong duration. Right guard, wrong
side of the `try`. Right check, wrong moment. Right constant, wrong module.

It presents as "one path of two" because a fix is applied to the path in view
and not to its sibling. Concrete sightings this session:

- The bound added to the anchor scan and not to the chain walk that expands the
  same field.
- The bound added to one branch of the chain walk and not the branch beside it
  reaching the same expansion.
- The stale-claim recovery added to `claim_singleton`, which the OmniRoute path
  never calls.
- Absent-vs-unreadable taught to `publish` and not to `verify`.
- Signer pinning added to `publish` and not to `verify`.
- Scan stabilisation added to the build and not to the preflight that depends
  on it.
- The summary guard added to `stop` and not to `start`.
- The proof written before the pointer and not before the retained copy.
- `mkdir` moved inside the guard, then moved back outside inside a new helper.

**Rule (the sweep).** After any fix, before reporting it:

1. **Siblings** -- find every other reader and writer of the structure changed.
2. **Scope** -- is the guard local while the property is general?
3. **Consumers** -- does the fix change what downstream readers now see?
   (A value that was intermittently absent and is now reliably present is a new
   input to every reader.)
4. **Property test** -- assert the property, not the reported instance.

Steps 1 and 3 found real, worse second defects on their first uses.

---

## 6. What the green suite was worth

At all 32 commits: tests passed, ruff was clean, `spec_gate --check` was green.
Those signals were true and did not discriminate. Specifically:

- The suite grew 908 → 959 while containing, at various points, ten tests that
  could not fail.
- One commit's honest accounting was **"+0 tests"** because it replaced two
  tests rather than adding any -- the previous count had included one that
  could never fail.
- The most damaging defects (a signed anchor over a truncated store; two
  writers in the sequence critical section) were invisible to every automated
  gate in the repo.

**Rule.** A green gate is a floor, not evidence. The things that caught real
defects this session were: an independent reviewer, a cold read of unchanged
code, and running each new test against the unfixed code.

---

## 7. What none of this fixed

- **The rate did not fall.** Nine consecutive rounds of self-inflicted defects,
  with the pattern named explicitly in commit messages throughout. Naming is
  not mitigation.
- **The `mcp_daemon` / `filelock` area had eleven passes** and is the least
  trustworthy code in the branch despite -- or because of -- the attention.
- **Seven review threads have been open all session**, untouched: three in
  `materialize_shared_agent_surface.py`, one each in
  `materialize_shared_skill_surface.py`, `hook_post_write.py`,
  `autonomous_synthesis_loop.py`, plus two marked outdated. The materializer's
  POSIX path break still breaks Linux CI.
- **`a8afdf5` is unreviewed.** Both reviewers were exhausted when it landed.
- **The six agent-surface projections were never regenerated**, so the
  consensus (780s) and ensemble (420s) timeouts exist only in
  `shared-agent-surface.json` and no harness sees them.

---

## 8. Cross-references

- Failure modes FM-1..FM-8, CF-1..CF-10:
  `docs/research/2026-08-25-provenance-failure-mode-register.md`
- Cross-audit learnings: `docs/research/2026-08-29-cross-audit-learnings.md`
- Ensemble aggregation prior art:
  `docs/research/2026-08-26-ensemble-aggregation-prior-art.md`
- Manual multi-model review protocol:
  `docs/governance/manual-review-protocol-v1.0.md`
- Skill-level observations 1..11 (agent behaviour rather than code):
  `~/.claude/projects/C---shit/skill-observations/log.md`
