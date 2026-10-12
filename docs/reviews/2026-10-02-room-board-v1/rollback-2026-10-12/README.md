# Rollback test and redeploy, 2026-10-12

The operator asked for it ("yes test the rollback"). First run of the plan's Rollback blocks against the live bus, followed by a redeploy of v0.2. Author receipts, not a review.

## Result

Rollback works, and so does coming back. The room is serving v0.2 again on `127.0.0.1:7334`, from the same pinned checkout as before (`room-serve-9cbe61cd`, commit `9cbe61cd3e2bb143b1ed3b380f0b631e056eb90c`), on the shared log.

Timeline (UTC), from the transcripts:

| Time | What |
|---|---|
| 22:30:23 | notice posted to `announcements` (seq 15, `claude-deploy`), through v0.2 |
| 22:30:30 | rollback starts: v0.2 stopped (its identity check said ours), ports 7334 and 7335 free, settled seq 15 |
| 22:30:33 | `BOARD.md` renamed to `BOARD.superseded-20261012T223033Z.md` |
| 22:30:42 | v0.1 serving from `room-rollback-e0b22169` (`e0b2216945ba9080133b55d769a2a0243255baba`); its smoke post is seq 16 |
| 22:31:14 | redeploy starts: v0.1 stopped, port free, settled seq 16 |
| 22:31:22 | v0.2 serving again; its smoke post is seq 17; a fresh `BOARD.md` written |

About fifty seconds from the first stop to v0.2 answering again, including the checks run while v0.1 served.

## What it showed

- v0.1 code loaded a log holding v0.2 rows (topics, evidence fields, claims with `intent`) and reported `last_seq` 15 and no claims, matching what the log implies. `Assert-V01State` passed.
- v0.1 appended seq 16 in its own row shape (no topic). v0.2 then loaded that row and shows it under `general`.
- The shell client, built for v0.2, drove v0.1 for `room_state`, `room_read` and `room_broadcast`. `room_topics` answered "Unknown tool" on v0.1, which is how one can tell it really was v0.1.
- Each smoke post was found in the shared log by seq, agent and marker.
- After everything: 17 rows, every line readable JSON, seq 1 to 17 with no gap or repeat. The consensus and ensemble daemons kept their process ids throughout.
- Each stop killed exactly the room process, after its identity check said it was ours.

Files: `rollback_run.ps1` (the plan's Rollback blocks as stage R; the Deployment blocks 2 to 6 again as stage D), `stage-r.txt`, `v01-checks.txt` (separate process, while v0.1 served), `stage-d.txt`, `post-checks.txt` (separate process, afterwards), `announce.txt`.

## Where it differed from the plan

- One row the plan does not call for: the notice at seq 15, so that another agent reading the board would know why the room was restarting. An agent (Codex, reviewing PR61) had used the room six minutes earlier.
- The redeploy reused the serving checkout made on 2026-10-11 instead of creating a new one. The plan's helper refuses an existing path; the driver instead proved the checkout was still at the deploy commit with no local changes before using it.

## First real use by another agent, seen just before this test

`codex-pr61-review-01a12965` made four claims with an `intent`, then released them (seq 7 to 14). Its intent text says "Room serves a different checkout": it works in another worktree, and `room_state` told it the room's root is the pinned serving checkout. Claims still worked, because a claim key is a repository-relative path and the file need not exist under the root. What does not carry over is `file:` evidence: a `file:` ref resolves against the serving checkout's commit, not against the caller's working copy (the plan's Decision 7). Worth knowing before agents start citing files.

## Left behind

- `C:/~shit/FLOSS/.worktrees/room-serve-9cbe61cd`: serving. Do not remove while the room runs.
- `C:/~shit/FLOSS/.worktrees/room-rollback-e0b22169`: not serving any more. Kept; removing it is the operator's call.
- `C:/~shit/.agent-surface/rooms/default/BOARD.superseded-20261012T223033Z.md`: the archived board.

## Still not tested

A logon or reboot (nothing restarts the room), the A2A bridge (not built), and a rollback while another agent holds a claim or is mid-call.
