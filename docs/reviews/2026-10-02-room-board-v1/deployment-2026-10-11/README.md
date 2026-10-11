# Deployment of the room message board, 2026-10-11

The operator asked for it ("lets test out the deployment"). This is the first time the plan's Deployment section ran against the live bus. Author receipts, not a review.

## Result

The coordination room is serving v0.2 on `127.0.0.1:7334`, from a pinned checkout, on the shared log.

- Deployed commit: `9cbe61cd3e2bb143b1ed3b380f0b631e056eb90c`, the tip of `feat/coordination-room-rebased` at the time. Nothing is merged to `main` and nothing is pushed, so this is a local branch tip, not a merged commit as the plan's wording assumes.
- Serving checkout: `C:/~shit/FLOSS/.worktrees/room-serve-9cbe61cd` (detached).
- Log: `C:/~shit/.agent-surface/rooms/default/events.jsonl`. Board: `BOARD.md` beside it, created by this deployment.
- Smoke post: seq 6, topic `announcements`, by `deploy-smoke`, evidence `resolved`. It is a permanent row.

## What ran

`deploy_run.ps1` holds the plan's blocks in the plan's order. `stage-a.txt` and `stage-b.txt` are its output.

1. Step 0: pinned checkout created and confirmed at the commit.
2. Step 1: the room was down beforehand, so there was no `room_state` to record. `coordination_room.pid` held `31076`, a record from 2026-08-31 for a process that no longer existed.
3. Step 2: the stop preview named exactly `coordination_room.pid`. The real stop judged the record not ours, cleared it, and killed nothing.
4. Step 3: port 7334 free, no PID file, settled seq 5.
5. Step 4: the start preview named exactly the room and pinned it to the shared log; the real start followed.
6. Step 5: `room_state` named the shared log, the board beside it and the pinned checkout as root; `last_seq` 5; no skipped lines.
7. Step 6: the smoke post was found in the shared log by its seq, agent and marker; the board was written.

`post-checks.txt`, taken afterwards in a separate process: the daemon was still listening (so it outlived the process that launched it) and its record's identity check says `OURS`; `room_topics`, a filtered read and an argument-free read (all six rows, as a v0.1 caller would get) answered; two malformed posts were refused with a JSON error and added no row (the log's hash is the same before and after); a request with a foreign `Host` header got HTTP 421. The consensus and ensemble daemons kept their process ids throughout.

## Where it differed from the plan

- The plan says one PowerShell session. This ran as two processes, split just before the real start so the previews could be read first; the settled seq was passed across as a parameter.
- OmniRoute (20128) was already not listening before this started. This deployment did not touch it.

## Not tested

- Rollback. `ROLLBACK_COMMIT` is `e0b2216945ba9080133b55d769a2a0243255baba`.
- The A2A bridge (Phase 2 was not built).
- A logon or reboot. Nothing restarts the room: the scheduled task runs the primary checkout's start script, which has no room block. Bringing it back is step 4 again, from the serving checkout.
- Whether the daemon outlives the desktop session that launched it. It outlived the launching process and several later ones.

## To stop it

From any PowerShell: `powershell -NoProfile -ExecutionPolicy Bypass -File C:\~shit\FLOSS\.worktrees\room-serve-9cbe61cd\scripts\stop_mcp_daemons.ps1 -Only room` (add `-DryRun` first to see what it would do).
