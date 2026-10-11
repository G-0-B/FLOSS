# Driver for the plan's Deployment section, run 2026-10-11 at the operator's request.
# The blocks are the plan's, in the plan's order. The one difference: the plan
# says "one PowerShell session"; here the session is split in two processes at
# the point just before the real start, so the previews can be read first. The
# settled seq is carried across as a parameter.
param(
    [Parameter(Mandatory)][ValidateSet('A', 'B')][string]$Stage,
    [int]$Settled = -1
)
$ErrorActionPreference = 'Stop'
$repo = 'C:\~shit\FLOSS'
$deployCommit = '9cbe61cd3e2bb143b1ed3b380f0b631e056eb90c'
$serve = "$repo\.worktrees\room-serve-$($deployCommit.Substring(0, 8))"
"== $(Get-Date -Format o) stage $Stage, deploy commit $deployCommit"

if ($Stage -eq 'A') {
    "== step 0: pinned checkout"
    . "$repo\.worktrees\coordination-room-rebased\packages\coordination_room\deploy.ps1"   # for New-PinnedCheckout
    New-PinnedCheckout $repo $deployCommit $serve
    . "$serve\packages\coordination_room\deploy.ps1"                                        # the helpers of the commit being deployed
    "log: $log"
    "agent dir: $agent"
    "python: $py"

    "== step 1: record what is running (the room is down, so no room_state)"
    Get-Content (Join-Path $agent 'coordination_room.pid') -ErrorAction SilentlyContinue

    "== step 2: stop only the room (preview, then real)"
    $preview = Invoke-DaemonScript $serve 'stop_mcp_daemons.ps1' @('-Only', 'room', '-DryRun')
    Assert-OnlyAction $preview 'WOULD_STOP' 'coordination_room.pid'
    Invoke-DaemonScript $serve 'stop_mcp_daemons.ps1' @('-Only', 'room') | Out-Null

    "== step 3: slot and port free, settled log"
    Assert-PortFree 7334 'coordination_room.pid'
    $settled = Get-SettledSeq
    "settled seq: $settled"

    "== step 4 (preview only): start only the room"
    $preview = Invoke-DaemonScript $serve 'start_mcp_daemons.ps1' @('-Only', 'room', '-DryRun')
    Assert-OnlyAction $preview 'WOULD_START' 'packages.coordination_room.server'
    Assert-PinnedLog $preview
    "STAGE A COMPLETE settled=$settled"
}

if ($Stage -eq 'B') {
    if ($Settled -lt 0) { throw 'Stage B needs -Settled from stage A.' }
    . "$serve\packages\coordination_room\deploy.ps1"
    "log: $log"
    $settled = $Settled

    "== step 4 (real): start only the room"
    Invoke-DaemonScript $serve 'start_mcp_daemons.ps1' @('-Only', 'room') | Out-Null

    "== step 5: assert the bus before any post"
    $state = Invoke-Room $serve 'room_state'
    $state | ConvertTo-Json -Depth 5
    Assert-RoomState $state $serve $settled

    "== step 6: smoke"
    $marker = New-SmokeMarker
    $reply = Invoke-Room $serve 'room_broadcast' @{
        agent_id = 'deploy-smoke'
        text = "deployed $deployCommit $marker"
        topic = 'announcements'
        evidence_refs = @('file:docs/specs/coordination-room.spec.md')
    }
    $reply | ConvertTo-Json -Depth 5
    if ($reply.evidence_status -cne 'resolved') { throw "Evidence lookup said '$($reply.evidence_status)'. Roll back." }
    Assert-SmokeEvent $reply.seq 'deploy-smoke' $marker
    $after = Invoke-Room $serve 'room_state'
    if ($after.board_last_error) { throw "The board is not being written: $($after.board_last_error)" }
    "deployed; smoke post is seq $($reply.seq); board as of $($after.board_as_of)"
    "STAGE B COMPLETE"
}
