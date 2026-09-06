# External review handoff — FLOSSI0ULLK PR #41

**Repository:** `G-0-B/FLOSS`
**Branch:** `reconcile/pr38-salvage-20260817`
**Range under review:** `2a55711` … `303b1f9` (seven commits)
**Status:** committed, **not pushed**. Nothing in this range is on the remote.

## What I want from you

Adversarial review, not a sanity check. The question is:

> **Which of these fixes introduces a defect the next review round will find?**

Not rhetorical. On this PR, across roughly sixty findings, the large majority
were defects in fixes made earlier in the same session — including four of the
five findings the final commit here addresses. The prior is that this range
contains at least one more, and that it is in a fix rather than in untouched
code.

Priorities:

1. **Control-flow equivalence.** Two fixes restructure dispatch: a PowerShell
   if/elseif/else chain, and an exception path that used to be a return value.
   Enumerate input combinations; check nothing changed that was not meant to.
2. **Contract changes.** One function went from total to partial (returned
   None, now raises). Check every caller, including any running under a
   `--check` mode that must not fail.
3. **Half-wiring.** Several fixes span two files — a manifest and its reader.
   Check that what one end writes is what the other end reads. A defect of
   exactly this shape is already recorded in the final commit message.
4. **Tests that cannot fail.** Every new test was run against the unfixed code
   first; the ones that passed anyway are labelled as complements. Check that
   labelling is honest, and that no test asserts an outcome identical under
   both implementations.

## Files

This packet lives at `docs/reviews/2026-09-05-pr41-fix-sweep/`, per the
convention in [`../README.md`](../README.md).

| File | Contents |
|---|---|
| `PACKET.md` | this document |
| `source-changes.patch` | production changes only, one section per commit |
| `test-changes.patch` | test changes only, same commits |
| `<reviewer>.md` / `.json` | external reviewer outputs, as they arrive |
| `RESULT.md` | dispositions and the operator's decision |

The split is deliberate: read the source patch first, form your own view of
what the tests should say, then read the test patch and see whether they say it.

## Commits, in order

| Commit | Subject |
|---|---|
| `2a55711` | six PR41 backlog findings, and one the tests refused |
| `29feb91` | three defects the pre-push review found in the previous commit |
| `222d27b` | second review pass, including the duplicate the helper was added to remove |
| `05f60e0` | headers were dropped by three projections, not one |
| `172a70b` | three review findings on the header projection, and one of mine |
| `216e3ff` | five findings, four of them defects in this session's own fixes |
| `303b1f9` | the review pass on those five, and one finding I disagreed with |

**Not mine, but present on the branch:** `616deaa` and `e2d02af`, authored by a
parallel session sharing this worktree (they sit between `172a70b` and
`216e3ff`). Excluded from both patch files. If you
review the branch directly rather than these patches you will see them; they
are not part of this handoff and I have not reviewed them.

## What the changes do

Twelve distinct defects across five areas.

**Multi-model voting independence** — `packages/metacoordinator_mcp/voters.py`,
`packages/reasoning_ensemble/transport.py`, `.../synthesizer.py`. The gateway
requires a poll to span at least 3 provider surfaces and 4 model families
before calling the result consensus. Three ways that bar was not enforced:
unclassified models each counted as their own family, so four routes to one
model cleared a four-family bar; mixed mode judged the online subset before
adding local voters, refusing rosters that are independent once combined; and
the survivor recheck exempted mixed mode, so a provider outage could reduce an
independent ensemble to a correlated subset still reported as normal consensus.

**Daemon slot claiming** — `packages/mcp_daemon.py`,
`scripts/start_mcp_daemons.ps1`. Two ways a failed start reported success: a
PowerShell branch whose own comment said "fall through and let the slot claim
decide" while structurally guaranteeing the slot claim could never run, and an
exception path returning the same value as "slot occupied", which the launcher
reads as a healthy daemon.

**Agent-surface materialization** — `scripts/materialize_shared_agent_surface.py`,
`scripts/materialize_shared_skill_surface.py`. HTTP MCP servers authenticated by
header were projected without them by three of four targets; withdrawn skills
kept their installed projection indefinitely while `--check` reported no drift;
and an unreadable Hermes `gateway.pid` was read as "no gateway running",
authorising a config write a live gateway overwrites on shutdown.

**Provenance attribution** — `hooks/hook_post_write.py`,
`shared-hook-surface.json`. Codex and Claude register the same hook with an
identical matcher and command, so no payload heuristic separates them; every
Codex edit was labelled `claude-code` in the signed packet's `source_systems`.
Each registration now declares its own surface via a flag.

**Synthesis loop** — `scripts/autonomous_synthesis_loop.py`. An unreadable file
returned a plain error string carrying neither not-processed marker, so it was
staged as that file's extracted semantics and `--commit` recorded an unread
file as a completed distillation.

## How to verify

From the repository root:

    python -m pytest -q packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded
    python scripts/spec_gate.py --check
    python -m ruff check .

Expected: **1054 passed, 7 skipped, 1 deselected**. spec_gate reports OK with
one non-fatal stale entry. ruff reports 9 errors, all predating this range:
E402 import placement in two test files and in autonomous_synthesis_loop.py,
E722 a bare except in that same file. No new lint error is introduced.

The deselected test is a known-red supersession classification, tracked in CI
config rather than fixed here, and untouched by this range.

## What I could not verify

Stated plainly so you can aim at it.

- **`http_headers` is the right Codex key.** It comes from a review comment
  citing Codex's config reference. Not verified against a live Codex install.
  If the key is wrong the credentials are still dropped and the failure is
  still silent — the fix would look correct and do nothing.
- ~~`--surface` survives the round trip through every target's config format.~~
  **Verified after this document was first drafted.** Rendering each target
  through `build_target_payload` shows the flag intact for all four —
  `codex`, `claude_user`, `hermes_user` (YAML, flat entry shape) and `gemini`
  (alongside its existing `--stdout-json`) — with the interpreter and script
  path quoted and the flag outside the quotes. Pinned by
  `test_the_declaration_survives_materialization_for_every_target`, which is
  red against the pre-manifest state. What remains unverified is the step
  after that: whether each agent actually *invokes* the command as written.
- **The PowerShell control flow** is covered by a source-text guard, not by
  execution — I cannot run the daemon scripts here. The restructured chain is
  the single change I would most like checked by hand.
- **Codex TOML entry ordering.** One test pins the rendered output and passes
  against the unfixed code too, because the pinned tomlkit re-orders on render.
  It is labelled a complement rather than counted as coverage. Whether the
  underlying ordering discipline is now correct is a judgement I want checked.
- **Cross-platform.** Everything ran on Windows. Three separate defects this
  session were visible only on Linux — ext4 inode reuse, %LOCALAPPDATA%
  expansion, mandatory versus advisory file locks — so a Linux run is worth
  more here than usual.
- **Reviewer diversity was thin.** Reviewed by one subagent throughout and, for
  two commits, two models via a routing gateway; five other model surfaces were
  unreachable (two sunset, one end-of-life, one credential mismatch, one
  timeout). That is the main reason I want outside eyes.

## What the internal review already found

Every commit here was reviewed by a subagent before this handoff, and that
review is not a substitute for yours — it found defects in four of the six
commits, which is the point. Recorded so you do not spend time re-deriving it:

- **`29feb91`, `222d27b`** — three defects in `2a55711`, then two more in
  `29feb91`, including a helper introduced to remove a duplicate predicate that
  was wired into only one of the two sites it existed for.
- **`172a70b`** — three defects in `05f60e0`: an override could strand a
  credential table on an entry whose transport had flipped; overrides were
  applied after tables, which is the ordering hazard that file documents; and
  one new test asserted the same refusal twice instead of covering the second
  target.
- **`303b1f9`** — two defects in `216e3ff`: a raise that escaped into
  `materialize()` and crashed `--check`, and an unvalidated `--surface` value
  that could stamp an uninterpretable label into signed provenance.

One finding I pushed back on rather than implementing, so you can judge it
yourself: the review called the PowerShell restructure a bug because UNKNOWN
plus a *fresh* reservation now prints twice and ends in "already claimed by
another launcher". I hold that the behaviour is correct — a fresh reservation
means a launcher is mid-flight, refusing is right, and the `$skipped` entry it
now records is the half that was missing. I changed the wording so the two
lines read as diagnosis and outcome rather than as competing verdicts. If you
think the refusal itself is wrong, say so.

## Conventions you may not expect

- Comments are long and explain **why a previous version was wrong**. House
  style, not padding. A comment that merely restates the code is a defect here.
- Truth-status discipline: no claim is marked verified without a traceable
  artifact. A comment asserting something you cannot check is worth raising.
- Fail-closed beats degrade-silently. A refusal that blocks work is preferred
  to a write that loses data — several of these fixes convert a silent fallback
  into a loud error on purpose.
