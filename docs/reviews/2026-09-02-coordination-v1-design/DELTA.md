# Delta — `2026-09-02-coordination-v1-design.md`

**Target:** `docs/superpowers/specs/2026-09-02-coordination-v1-design.md` @ `7421dee`
**Reviewer:** Claude Opus 5, Claude Code session, 2026-09-02
**Kind:** applicable delta, not a rewrite. Nine changes; everything not listed here stands.
**Why a delta and not a revision:** four fixes were written twice in this repo inside 48 hours
because two agents worked the same finding without seeing each other. Rewriting a doc its author
is mid-flight in is the same mistake with a larger blast radius.

**Truth labels:** ✅ Verified (command given) / ⚠️ Specified / ❌ Blocked.

---

## Keep as written — do not change

Listed first so the delta is not mistaken for a teardown.

- **§0's CAS proof.** The claim primitive is settled empirically, not argued. 8-way `Popen`,
  1 win / 7 blocked, repeated twice, `git 2.54.0.windows.1` on NTFS, with
  `is at <sha> but expected <old>` and `Unable to create '*.lock'` recorded as distinct errors.
  This is better evidence than the reviewing session had; it closes the open Windows-CAS question
  that the external audit raised.
- **§0's finding that Grok's `packages/coordination_room/` diff is 0 lines.** Confirms the room
  code never diverged — only its wiring did. Reframes the fork as parallel substrate evolution
  rather than a conflict needing resolution. ✅ independently re-verified.
- **§4.2 in full.** Namespace, `hash-object -w` value, delete-with-expected-old, TTL, `2×ttl`
  force-drop with audit. More complete than the reviewing session's sketch.
- **§6's retry-with-jitter on AV/indexer lock contention.** A real Windows failure mode the
  reviewing session had not accounted for.
- **§8's testing plan** and **§9's M1 = derived view only**. Two sessions reached that sequencing
  independently, which is itself evidence for it.
- **§0's falsifier.** Keep the discipline.

---

## D1 — §4.1: extend `orient_probe.py`; do not build a new entry point

**Change:** replace `coord_status.py` / `hermes status` as the primary surface with a sibling
module that `scripts/orient_probe.py` imports and renders as additional sections.

**Why.** §7's ADR-18 check is thorough on git *primitives* and misses reuse of an *entry point*.
`scripts/orient_probe.py` already:

- emits a deterministic markdown packet (`## Section` + pipe tables),
- is stdlib-only, no-network, no-mutation, 322 lines,
- and is **the mandatory Step 0 of the `flossi0ullk-orient` skill** — agents already run it.

That last property is the one that matters. The coordination room and Work Board §0 did not fail
on design; they failed on adoption and liveness. A new command has to earn adoption from zero.
The probe has it already. On the adopt → extend → compose → build ladder this is **extend**, not
**build** — one rung, but the rung that decides whether anyone reads the output.

**Also drop `hermes status` as the primary alias.** It names a universal view after one of six
harnesses, and not the busiest one (see D5). Reach is the entire argument for the derived view.

**Suggested shape:** `scripts/coord_status.py` exists as a module with a `render_sections()`
returning markdown, imported by `orient_probe.py`, and runnable standalone for `--json`. Same
adoption, better isolation, and the probe stays under ~500 lines.

## D2 — §4.1.3: the divergence filter as written produces an unusable panel

**Change:** replace *"flag if `base age > 24h` or `behind > N`"* with a two-part filter:

1. **Active branches only** — a branch with a commit in the last 7 days.
2. **Both sides must have modified the same file** — `git diff --name-only <merge-base> <A>`
   intersected with the same for `<B>`; empty intersection means forked but disjoint, which
   carries no stranding risk.

**Evidence.** ✅ Both variants were run against this repo on 2026-09-02:

| filter | rows |
|---|---|
| naive (any two branches with unique commits both ways) | **45+, output truncated before it finished** |
| active-only (7d) — cuts 28 branches to 8 | 8 pairs |
| active-only **and** shared files, with D3 applied | **4 rows** |

The naive count is not a tuning problem. Every abandoned branch is technically a fork of every
other, so the row count grows with the *dead* branch count, which is the opposite of what the
panel is for.

**The filtered version independently rediscovered both known stranded fixes** —
`chore/digestion-actions` ↔ `reconcile/pr38-salvage-20260817`, 3 files on both sides:
`scripts/start_mcp_daemons.ps1`, `scripts/stop_mcp_daemons.ps1`, and
`docs/agent-memory/project/commitment-built-witness-improvised.md`. Those are the launcher fix and
the frontmatter fix, both of which cost manual archaeology to find by hand. That is the panel
earning its place.

## D3 — §4.1: collapse hotspot files

**Change:** when one file appears on both sides of three or more fork pairs, emit it once as a
`HOTSPOT` row instead of once per pair.

**Evidence.** ✅ `docs/specs/spec-registry.json` appeared on both sides of **5 of the 8** surviving
pairs. It is one contention hotspot, not five findings, and left uncollapsed it is most of the
panel.

## D4 — §4.1.1: report exceptions, not inventory — and pre-filter for cost

**Change, presentation:** show active and anomalous worktrees; collapse the rest to a count.
Anomaly flags: `SHARED-INDEX` (dirty in a checkout another agent is active in), `TEMP-DIR`
(worktree path under a temp directory), `ABANDONED-DIRTY` (uncommitted work, no git activity in
30d), `ORPHAN` (detached, parent merged).

**Change, cost:** ✅ `git status --porcelain` across 20 worktrees is the slow path — it dominated
the probe's runtime. Read `<common-dir>/worktrees/<name>/index` mtime first and only `git status`
worktrees that are recent or already known dirty.

**Evidence.** 20 worktrees render as 6 anomaly rows plus `13 more — idle, clean`. Inventory hides
the signal; exceptions are a decision.

## D5 — §4.3: the hook-coverage claim is wrong, and the correction changes the design

**Change:** *"Today only Gemini wires it"* → **3 of 6 harnesses wire it today.**

✅ Verified 2026-09-02 by grepping each materialized config for `hook_pre_write` / `hook_post_write`:

| config | wired |
|---|---|
| `.gemini/settings.json` | yes |
| `C:/Users/kalis/.claude/settings.json` (user scope) | yes |
| `C:/Users/kalis/AppData/Local/hermes/config.yaml` | yes |
| `.claude/settings.json` (repo) | no |
| `.codex/config.toml` (repo) and `C:/Users/kalis/.codex/config.toml` | no |
| `opencode.jsonc` | no |

**The count is not the point.** **Codex is uncovered**, and Codex is the most active agent in this
repository — it authored the majority of PR41's 248 review threads and owns four `codex/*`
branches. Any enforcement story routed through harness hooks misses the main contender, and §4.3
currently reads as though materialization closes the gap. It does not: it closes Claude and
leaves Codex and OpenCode outside.

**Consequence for the design, not just the prose:** this strengthens §9's M1-first sequencing.
The derived view reaches every agent that can shell `git` — all six. Enforcement reaches at best
four. Reach, not liveness, is the constraint that should drive ordering, and the doc should say so.

## D6 — §0: the evidence is unfindable and untracked

**Change:** move the four cited reports into this directory (or another committed path) and update
§0's citations; commit them.

**Evidence.** ✅ The doc lives in `FLOSS/` and cites `.hermes/plans/*.md`, which resolves to
`FLOSS/.hermes/plans/`. That directory does not exist — `FLOSS/.hermes/` contains only
`desktop-attachments`. The files are actually at `C:/~shit/.hermes/plans/`, in the **workspace root
repo**, and all four are **untracked** there:

```
.hermes/plans/cas-proof-report.md          UNTRACKED
.hermes/plans/ancestor-matrix-report.md    UNTRACKED
.hermes/plans/grok-coord-room-audit.md     UNTRACKED
.hermes/plans/derived-status-sketch.md     UNTRACKED
```

So every `[V]` in §0 currently points at a file a reader cannot resolve and git does not have. The
CAS proof in particular is the doc's strongest evidence and the most expensive to reproduce; it
should not be one `git clean` from gone. This is the two-repository hazard documented in
`docs/reviews/2026-09-01-polyglot-plugin-materializer-spec/HANDOFF.md` §1.

## D7 — §4.1.5: `gh pr list` conflicts with the probe's no-network contract

**Change:** keep v1 fully offline. Move the open-PR section behind an explicit `--online` flag,
and state the contract in the section header.

**Why.** `orient_probe.py`'s docstring commits to *"No mutation. No network. Stdlib only."* Under
D1 the status sections land inside that contract. A cached-60s `gh` call is a reasonable design on
its own, but silently importing network into a probe that promises none breaks a guarantee other
callers rely on. All three panels in D2–D4 are pure-git and need nothing external.

## D8 — add the propagation metric

**Change:** add one line at the top of the status output.

**Evidence.** ✅ Of the **10** commits landed across all refs in the last 24 hours, **10 exist on
exactly 1 of the 8 active branches**. Zero propagation. Suggested rendering:

```
## Coordination                    10 commits/24h, 10 on exactly 1 of 8 active branches
```

That single number is the coordination gap stated as a measurement, it is free to compute
alongside the panel that produces it, and it is the line most likely to be read.

## D9 — §6: add abandoned-dirty as a failure class

**Change:** §6 covers detached and orphan worktrees but not uncommitted work rotting in a worktree
nobody is tracking.

**Evidence.** ✅ Four worktrees hold dirty state abandoned for **18, 48, 80 and 181 days**:
`_codex_pr38_cleanup` (1 file, 0/0), `_codex_pr38_salvage_design` (30 files, +118/−83),
`_pr25fix` (17 files, +24/−24), `quirky-mcnulty` (4 files, −486). None was known to anyone before
2026-09-02. Triage is running as a separate task; the design change is only that the status view
should flag the class so it cannot accumulate silently again.

---

## Applying this

D5, D6 and D7 are corrections — apply regardless of what happens to the rest. D2 and D3 are tested
replacements for an untested rule and carry measured numbers. D1 is the one genuine design
disagreement and the one worth arguing about; if it is rejected, the reason should be written down,
because "we built a new entry point instead of extending the adopted one" is exactly the shape of
the two surfaces that already failed here.
