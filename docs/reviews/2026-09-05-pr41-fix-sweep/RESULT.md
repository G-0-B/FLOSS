# RESULT — PR41 fix-sweep review

**Packet:** [`PACKET.md`](PACKET.md), range `2a55711` … `303b1f9`
**External review:** independent audit, 2026-09-18 —
[`external-audit-2026-09-18/REVIEW.md`](external-audit-2026-09-18/REVIEW.md)
**Audit recommendation:** request changes, on two reproduced findings
**Author response:** `e747a75` — both findings fixed, two residuals fixed, one deferred

## Operator decision

**PENDING.** This file records the author's dispositions. It is not the
operator's decision, and the audit states explicitly that it is not one either.
Whether the range is accepted, and whether the deferred item below is accepted
as deferred, is for the operator to write here.

## Dispositions

| Item | Audit | Author disposition |
|---|---|---|
| **F1** — survivor independence read raw model ids, admission read transport-aware routes | P1, reproduced | **Fixed** in `e747a75`. Survivors now go through the same `_independence_route`, keyed on each response's `transport_name`. Regression drives `synthesize()` with the shipped local pool and two failed online voters, and requires `degraded` plus an unsuccessful audit record. |
| **F2** — `hermes_gateway_alive` raising reached one caller of two | P2, reproduced | **Fixed** in `e747a75`. The hook materializer's path translates the refusal to a local `GatewayStateUnknown` and reports `REFUSED`. Tested through the YAML target, the standalone hook materializer, and the parent `materialize()` running the real hook sub-step. |
| Malformed `gateway.pid` shapes (`[]`, `null`, invalid UTF-8) escaped as unhandled types | residual, reproduced | **Fixed** in `e747a75`. All shapes, plus bare strings, numbers and `true`, now raise the handled type. |
| Stale-skill pruner checked a marker's existence, not its owner | residual, dry-run reproduced | **Fixed** in `e747a75`. Removal requires the marker's `source_path` to resolve under this workspace; anything that cannot prove ownership is left alone. A join test ties the marker writer to the reader. |
| Survivor helper treats an exception from the independence checker as `None` | residual, pre-existing | **Deferred — needs an operator decision.** It predates this range and a test pins it deliberately: a checker that cannot run currently must not abort a run. Changing that trades availability for correctness and is a policy choice, not a defect fix. |
| Linux behaviour, installed Antigravity/Hermes header support, real harness invocation, authenticated MCP delivery, daemon readiness | unverified | **Remain unverified.** Nothing in this sweep closes them. |

## Internal review of the response

`e747a75` was reviewed by a subagent before this file was written. It returned
a bare "no issues" rather than the per-area report requested, which is weaker
evidence than a structured clean result, so the question it was most likely to
get wrong was checked directly: whether any skill's source lives outside the
workspace root, which would make this workspace's *own* projections
unprunable under the new ownership rule. Against the real workspace
(`C:/~shit`), all 27 manifest skills resolve under the root; none are outside
and none are unresolvable.

That check surfaced one pre-existing behaviour worth recording, not changed
here: `WORKSPACE_ROOT` is `REPO_ROOT.parent`, so a materializer run from a
worktree under `FLOSS/.worktrees/` resolves against `.worktrees/` rather than
the workspace. It fails loudly — every skill becomes unresolvable before any
pruning — so it cannot cause a silent deletion, but it means the skill
materializer should be run from the main checkout.

### What that review found and did not report

After the above was written, the reviewer's reasoning showed it *had* examined
the PID shapes the prompt listed: zero and negative ids reach `_pid_alive`,
which fails closed, so the write is refused — but the refusal then reads
"gateway PID 0 is live; stop it and re-run", which is false, and for 0 (or 4
on Windows, the System process) directs an operator to kill a system process.
It judged this safe and not introduced by the commit, and so did not report it,
because the prompt asked only for introduced defects. The fault is the prompt.

Fixed in the commit after this file first landed: any id outside
`0 < pid < 2**32` is now reported as an unknown gateway state. **Not fixed:**
a *possible* PID that belongs to some other process — 4 on Windows, or any
reused id from a stale `gateway.pid` — still reads as a live gateway.
Existence is not identity; the daemon side solved that with process-start
tokens, and Hermes' pid file carries none. Recorded as open.

The prompting rule this taught is in [`../README.md`](../README.md).

## Where the audit corrected the packet

The packet made claims the audit tested. Four did not hold as stated:

- **"ruff reports 9 errors."** It is **8** code diagnostics under ruff 0.15.11.
  The packet was wrong. (Carrying the auditor's scripts into this directory adds
  5 more to a repo-wide `ruff check .`, since the repository has no ruff
  config and CI does not lint. Report code-only counts in future packets:
  `ruff check packages scripts tests hooks`.)
- **"`--check` must survive whatever it finds on disk"**, asserted in `303b1f9`.
  False when written: `[]`, `null` and invalid UTF-8 all escaped. Fixed in
  `e747a75`.
- **"1054 passed."** True on the author's machine. The audit's run was
  1051 passed with 3 environment failures (sandboxed `tasklist`, an archive
  without a Git index), each shown to pass outside that environment. Not one
  all-green run in a second environment.
- **A test that proved nothing.** `test_a_corrupt_pid_file_is_reported_not_
  raised_through_materialize` grepped the source for a `try` and an `except`
  around one call site. It could not see the second caller where the defect
  was. Removed in `e747a75` and replaced by the three behavioural tests above.

And two uncertainties it closed in the packet's favour:

- **The Codex `http_headers` key** is confirmed by a Codex CLI readback and the
  official documentation. This closes the key-name question only — not
  authenticated delivery over the network.
- **The PowerShell dispatch** was executed for all 12 combinations of verdict,
  path existence and reservation status, and every one matches the intended
  dispatch. The author's pushback on the double-message finding is supported.

## Test discrimination

The audit ran the 45 new test functions against pre-sweep production code:
36 failed, 9 passed. The 9 largely pin unchanged behaviour and were labelled
as complements. It also noted that several failures only show a new name is
missing, which is weaker evidence than observing the old wrong behaviour.

`e747a75` was red-checked differently from the rest of the sweep: every test
was written and run red **before** its fix. Earlier commits in this range
red-checked with `git stash push` / `pop`, and the stash stack in this
repository is shared with other sessions' worktrees — so those checks could
have popped another session's entry. That practice is retired.

## Evidence

`external-audit-2026-09-18/` carries the review and every evidence file it
links to, content-identical to the auditor's output and checked for
credentials before commit. Not byte-identical: the repository's line-ending
rules normalize four of them on commit (three to LF, the PowerShell harness to
CRLF) -- the same effect the audit itself recorded when comparing its exported
`.ps1` against Git. The originals are unchanged at `_audit/` if byte equality
matters (the header probe used `X-Audit: nonsecret` against
`example.invalid`). Every relative link in `REVIEW.md` resolves inside the
repository.

Not carried, and still at `_audit/pr41-fix-sweep-20260918/` in the workspace:
the 273 MB exported snapshot of `303b1f9`, the 219 MB dependency cache, the
pytest temporary directories and the probe fixtures. They reproduce the
evidence rather than being it.
