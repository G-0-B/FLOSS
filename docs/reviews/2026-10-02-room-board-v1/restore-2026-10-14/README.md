# The room died with the app; restored under Task Scheduler, 2026-10-14

Author receipts, not a review.

## What happened

The v0.2 room redeployed on 2026-10-12 (pid 5524) was gone by 2026-10-14 01:55 local time. The log's last row was the redeploy's smoke post (seq 17); nothing after it was lost. There had been no reboot (last boot 2026-10-06 21:19) and no Python crash event in the Application log. The Claude desktop app had restarted on 2026-10-13 at 15:03.

Most likely cause, not proven: the room had been started from a shell that the Claude desktop app launched, and it was ended along with the app's processes. The consensus and ensemble daemons, started by the logon task `FLOSS-MCP-Daemons` on 2026-10-06, survived the same restart.

So the deployment of 2026-10-11 and the redeploy of 2026-10-12 proved the procedure, not durability: a room started from inside an agent harness does not outlive that harness.

## What was done

At the operator's request ("restore the room durably"), `restore_run.ps1`:

1. Confirmed the serving checkout `room-serve-9cbe61cd` is still exactly `9cbe61cd3e2bb143b1ed3b380f0b631e056eb90c` with no local changes.
2. Ran the plan's stop (preview, then real). It judged the record for pid 5524 not ours, cleared it, and killed nothing.
3. Proved port 7334 and the slot free; settled seq 17. Previewed the start: exactly the room, pinned to the shared log.
4. Registered a new logon task, `\FLOSS-Coordination-Room`, and started the room through it:
   - action: `powershell -WindowStyle Hidden -File C:\~shit\FLOSS\.worktrees\room-serve-9cbe61cd\scripts\start_mcp_daemons.ps1 -Only room`
   - trigger: logon of this user; principal (kalis, interactive, limited) and settings copied from `FLOSS-MCP-Daemons`, including its battery rules (it does not start on battery power).
   - The first attempt copied that task's trigger too and was refused (`Access is denied`): its trigger fires at any user's logon, which only an administrator may register. Nothing was registered by that attempt (`restore-attempt1-access-denied.txt`).
5. Task result 0. `room_state` named the shared log, the board beside it and the serving checkout; seq 17; no skipped lines. Smoke post seq 18, found in the shared log by seq, agent and marker.

`durability-check.txt`: the room daemon, this shell and the consensus daemon all report being in a job object, so job membership does not tell them apart. What does: the room now has the same launcher as the consensus daemon (Task Scheduler, then the start script, then a hidden child process), and that daemon survived the app restart.

## Why a separate task

`FLOSS-MCP-Daemons` runs the primary checkout's start script, which starts consensus, ensemble and OmniRoute from the primary's code and has no room block. Pointing it at the serving checkout would have changed the code those daemons run. The new task starts only the room.

## Not verified

- That the room survives a Claude desktop restart. That needs a restart this session cannot perform from inside the app.
- A logon. The task fires at the next one.

## To keep in mind

- A redeploy of another commit must update the task's action (it names the serving checkout path).
- To stop the room: `scripts\stop_mcp_daemons.ps1 -Only room` from the serving checkout. To stop it starting at logon: disable or unregister `\FLOSS-Coordination-Room`.
