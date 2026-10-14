# Restore the coordination room durably, 2026-10-14, at the operator's request
# ("restore the room durably").
#
# The room deployed on 2026-10-12 was started from inside a Claude desktop
# session and died when the app restarted (no reboot, no crash event). This
# registers a separate logon task that starts only the room, from the pinned
# serving checkout, and starts the room now through that task, so the daemon is
# a child of Task Scheduler, not of any agent harness.
#
# Why a new task and not an edit of FLOSS-MCP-Daemons: that task runs the
# primary checkout's script, which starts consensus and ensemble from the
# primary's code. Pointing it at the serving checkout would change the code
# those daemons run as well.
#
# The deployment checks are the plan's (Deployment steps 2 to 6); only the
# launcher differs: Start-ScheduledTask instead of Invoke-DaemonScript.
$ErrorActionPreference = 'Stop'
$repo = 'C:\~shit\FLOSS'
$deployCommit = '9cbe61cd3e2bb143b1ed3b380f0b631e056eb90c'
$serve = "$repo\.worktrees\room-serve-$($deployCommit.Substring(0, 8))"
$taskName = 'FLOSS-Coordination-Room'
$model = 'FLOSS-MCP-Daemons'
. "$serve\packages\coordination_room\deploy.ps1"
"== $(Get-Date -Format o)"
"log: $log"

"== 0: the serving checkout is still exactly the deploy commit"
$head = "$(git -C $serve rev-parse HEAD)".Trim()
if ($head -ne $deployCommit) { throw "The serving checkout is at $head, not $deployCommit. Stop here." }
if ("$(git -C $serve status --porcelain)") { throw "The serving checkout has local changes. Stop here." }
"serving checkout: $serve at $head, clean"
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    throw "A task named $taskName already exists. Not overwriting it; look at it first."
}

"== 2: stop only the room (it is down; this clears its stale record)"
$preview = Invoke-DaemonScript $serve 'stop_mcp_daemons.ps1' @('-Only', 'room', '-DryRun')
Assert-OnlyAction $preview 'WOULD_STOP' 'coordination_room.pid'
Invoke-DaemonScript $serve 'stop_mcp_daemons.ps1' @('-Only', 'room') | Out-Null

"== 3: slot and port free, settled log"
Assert-PortFree 7334 'coordination_room.pid'
$settled = Get-SettledSeq
"settled seq: $settled"

"== 4: preview the start, then register the task and start the room through it"
$preview = Invoke-DaemonScript $serve 'start_mcp_daemons.ps1' @('-Only', 'room', '-DryRun')
Assert-OnlyAction $preview 'WOULD_START' 'packages.coordination_room.server'
Assert-PinnedLog $preview

$existing = Get-ScheduledTask -TaskName $model
$action = New-ScheduledTaskAction -Execute 'powershell' -Argument "-WindowStyle Hidden -File $serve\scripts\start_mcp_daemons.ps1 -Only room"
$description = "Starts only the FLOSS coordination room (v0.2) at logon, from the pinned serving checkout $serve (commit $deployCommit). " +
    "Registered 2026-10-14 at the operator's request; see docs/reviews/2026-10-02-room-board-v1/restore-2026-10-14/ on feat/coordination-room-rebased. " +
    "A redeploy of a different commit must update this action. Principal and settings copied from $model; the trigger is this user's logon " +
    "(that task's any-user logon trigger needs administrator rights to register)."
# The model task's trigger fires at any user's logon, which only an administrator
# may register. This user's own logon is the same event for this machine's one user.
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
Register-ScheduledTask -TaskName $taskName -Description $description -Action $action `
    -Trigger $trigger -Principal $existing.Principal -Settings $existing.Settings | Out-Null
$registered = Get-ScheduledTask -TaskName $taskName
"registered: $($registered.TaskPath)$($registered.TaskName)"
"  action: $($registered.Actions[0].Execute) $($registered.Actions[0].Arguments)"
"  trigger: $($registered.Triggers[0].CimClass.CimClassName); principal: $($registered.Principal.UserId) $($registered.Principal.LogonType) $($registered.Principal.RunLevel)"
"  settings: timelimit=$($registered.Settings.ExecutionTimeLimit) multiple=$($registered.Settings.MultipleInstances) battery=$($registered.Settings.DisallowStartIfOnBatteries)/$($registered.Settings.StopIfGoingOnBatteries)"

$before = (Get-ScheduledTaskInfo -TaskName $taskName).LastRunTime
Start-ScheduledTask -TaskName $taskName
$deadline = (Get-Date).AddSeconds(60)
do {
    Start-Sleep -Seconds 2
    $info = Get-ScheduledTaskInfo -TaskName $taskName
    $task = Get-ScheduledTask -TaskName $taskName
} while (((Get-Date) -lt $deadline) -and (($info.LastRunTime -eq $before) -or ($task.State -eq 'Running')))
"task run: last run $($info.LastRunTime), result $($info.LastTaskResult), state $($task.State)"
if ($info.LastTaskResult -ne 0) { throw "The task's start script did not exit 0 ($($info.LastTaskResult)). Stop here." }

"== 5: assert the bus before any post"
$state = Invoke-Room $serve 'room_state'
$state | ConvertTo-Json -Depth 5
Assert-RoomState $state $serve $settled

"== the daemon's ancestry: it must not descend from an agent harness"
$listener = Get-NetTCPConnection -State Listen -LocalPort 7334
$daemon = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
"daemon pid $($daemon.ProcessId): $($daemon.CommandLine)"
$walk = $daemon.ParentProcessId
for ($i = 0; $i -lt 8 -and $walk; $i++) {
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$walk" -ErrorAction SilentlyContinue
    if (-not $p) { "  ancestor pid ${walk}: gone"; break }
    "  ancestor pid $($p.ProcessId): $($p.Name)"
    if ($p.Name -match '^(claude|Claude|codex|Code|node)(\.exe)?$') { throw "The daemon descends from $($p.Name). It would die with it. Stop here." }
    $walk = $p.ParentProcessId
}

"== 6: smoke"
$marker = New-SmokeMarker
$reply = Invoke-Room $serve 'room_broadcast' @{
    agent_id = 'deploy-smoke'
    text = "deployed $deployCommit via logon task $taskName $marker"
    topic = 'announcements'
    evidence_refs = @('file:docs/specs/coordination-room.spec.md')
}
$reply | ConvertTo-Json -Depth 5
if ($reply.evidence_status -cne 'resolved') { throw "Evidence lookup said '$($reply.evidence_status)'." }
Assert-SmokeEvent $reply.seq 'deploy-smoke' $marker
$after = Invoke-Room $serve 'room_state'
if ($after.board_last_error) { throw "The board is not being written: $($after.board_last_error)" }
"restored; smoke post is seq $($reply.seq); board as of $($after.board_as_of)"
"RESTORE COMPLETE"
