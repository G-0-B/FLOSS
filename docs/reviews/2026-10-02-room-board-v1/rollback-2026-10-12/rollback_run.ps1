# Driver for the plan's Rollback blocks (stage R) and for the redeploy that
# follows (stage D: the Deployment blocks 2 to 6 again, reusing the pinned
# serving checkout after proving it is still the deploy commit, unmodified).
# Run 2026-10-12 at the operator's request ("yes test the rollback").
param([Parameter(Mandatory)][ValidateSet('R', 'D')][string]$Stage)
$ErrorActionPreference = 'Stop'
$repo = 'C:\~shit\FLOSS'
$deployCommit = '9cbe61cd3e2bb143b1ed3b380f0b631e056eb90c'
$serve = "$repo\.worktrees\room-serve-$($deployCommit.Substring(0, 8))"
. "$serve\packages\coordination_room\deploy.ps1"
"== $(Get-Date -Format o) stage $Stage"
"log: $log"

if ($Stage -eq 'R') {
    "== rollback 1: stop the bridge if it runs, stop the room, prove both ports free, read the settled log"
    if (Test-Path (Join-Path $agent 'a2a_room_bridge.pid')) {
        Invoke-DaemonScript $serve 'stop_mcp_daemons.ps1' @('-Only', 'bridge') | Out-Null
    }
    Assert-PortFree 7335 'a2a_room_bridge.pid'
    $preview = Invoke-DaemonScript $serve 'stop_mcp_daemons.ps1' @('-Only', 'room', '-DryRun')
    Assert-OnlyAction $preview 'WOULD_STOP' 'coordination_room.pid'
    Invoke-DaemonScript $serve 'stop_mcp_daemons.ps1' @('-Only', 'room') | Out-Null
    Assert-PortFree 7334 'coordination_room.pid'
    $settled = Get-SettledSeq
    "settled seq: $settled"

    "== rollback 2: archive the board, never delete it"
    $board = Join-Path (Split-Path $log) 'BOARD.md'
    if (Test-Path $board) {
        Rename-Item $board ("BOARD.superseded-{0}.md" -f (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'))
    }
    Get-ChildItem (Split-Path $log) | ForEach-Object { "  $($_.Name)  $($_.Length)" }

    "== rollback 3: check out the rollback point and serve v0.1 from it, room only"
    $rollbackCommit = 'e0b2216945ba9080133b55d769a2a0243255baba'
    $rollback = "$repo\.worktrees\room-rollback-$($rollbackCommit.Substring(0, 8))"
    New-PinnedCheckout $repo $rollbackCommit $rollback
    $preview = Invoke-DaemonScript $rollback 'start_mcp_daemons.ps1' @('-Only', 'room', '-DryRun')
    Assert-OnlyAction $preview 'WOULD_START' 'packages.coordination_room.server'
    Assert-PinnedLog $preview
    Invoke-DaemonScript $rollback 'start_mcp_daemons.ps1' @('-Only', 'room') | Out-Null

    "== rollback 4: accept v0.1 by what it can report, then prove a post of ours is in the shared log"
    $state = Invoke-Room $serve 'room_state'
    $state | ConvertTo-Json -Depth 5
    Assert-V01State $state $settled
    $marker = New-SmokeMarker
    $reply = Invoke-Room $serve 'room_broadcast' @{ agent_id = 'deploy-smoke'; text = "rolled back to v0.1 $marker" }
    $reply | ConvertTo-Json -Depth 5
    Assert-SmokeEvent $reply.seq 'deploy-smoke' $marker
    "rolled back; smoke post is seq $($reply.seq)"
    "STAGE R COMPLETE"
}

if ($Stage -eq 'D') {
    "== redeploy 0: the pinned serving checkout from 2026-10-11 is reused only if it is still that commit, unmodified"
    $head = "$(git -C $serve rev-parse HEAD)".Trim()
    if ($head -ne $deployCommit) { throw "The serving checkout is at $head, not $deployCommit. Stop here." }
    if ("$(git -C $serve status --porcelain)") { throw "The serving checkout has local changes. Stop here." }
    "serving checkout: $serve at $head, clean"

    "== redeploy 2: stop only the room (v0.1 is serving)"
    $preview = Invoke-DaemonScript $serve 'stop_mcp_daemons.ps1' @('-Only', 'room', '-DryRun')
    Assert-OnlyAction $preview 'WOULD_STOP' 'coordination_room.pid'
    Invoke-DaemonScript $serve 'stop_mcp_daemons.ps1' @('-Only', 'room') | Out-Null

    "== redeploy 3: slot and port free, settled log"
    Assert-PortFree 7334 'coordination_room.pid'
    $settled = Get-SettledSeq
    "settled seq: $settled"

    "== redeploy 4: start only the room"
    $preview = Invoke-DaemonScript $serve 'start_mcp_daemons.ps1' @('-Only', 'room', '-DryRun')
    Assert-OnlyAction $preview 'WOULD_START' 'packages.coordination_room.server'
    Assert-PinnedLog $preview
    Invoke-DaemonScript $serve 'start_mcp_daemons.ps1' @('-Only', 'room') | Out-Null

    "== redeploy 5: assert the bus before any post"
    $state = Invoke-Room $serve 'room_state'
    $state | ConvertTo-Json -Depth 5
    Assert-RoomState $state $serve $settled

    "== redeploy 6: smoke"
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
    "STAGE D COMPLETE"
}
