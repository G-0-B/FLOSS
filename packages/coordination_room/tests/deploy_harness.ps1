# Inert checks of ..\deploy.ps1, run by test_deploy_helpers.py under each
# installed PowerShell: fake checkouts, a scratch port, a scratch log, a scratch
# git repository, and (when -RoomUrl is given) a scratch room the test started.
# No real daemon, PID file or port 7334/7335 is touched. Prints one JSON object
# of named checks; every value must be true.
param([string]$Work, [string]$Python, [int]$Port, [string]$RoomUrl, [string]$RoomLog, [string]$RoomRoot)
$ErrorActionPreference = 'Stop'
$py = $Python
. (Join-Path (Split-Path -Parent $PSScriptRoot) 'deploy.ps1')
$agent = Join-Path $Work 'agent'; New-Item -ItemType Directory -Force $agent | Out-Null
$log = Join-Path $Work 'events.jsonl'
$results = [ordered]@{}

function Make-Checkout([string]$Name, [string]$Body) {
    $dir = Join-Path $Work $Name
    New-Item -ItemType Directory -Force (Join-Path $dir 'scripts') | Out-Null
    Set-Content -Path (Join-Path $dir 'scripts\stop_mcp_daemons.ps1') -Value $Body -Encoding ascii
    return $dir
}
$ok   = Make-Checkout 'ok'   'Write-Host "[FLOSS MCP] WOULD_STOP coordination_room.pid (x)"; exit 0'
$fail = Make-Checkout 'fail' 'Write-Host "[FLOSS MCP] SHUTDOWN INCOMPLETE"; exit 1'
$two  = Make-Checkout 'two'  'Write-Host "[FLOSS MCP] WOULD_STOP coordination_room.pid"; Write-Host "[FLOSS MCP] WOULD_STOP consensus.pid"; exit 0'

$out = Invoke-DaemonScript $ok 'stop_mcp_daemons.ps1' @('-Only', 'room', '-DryRun')
Assert-OnlyAction $out 'WOULD_STOP' 'coordination_room.pid'
$results['success-returns-output'] = $true

try { Invoke-DaemonScript $fail 'stop_mcp_daemons.ps1' @('-Only', 'room') | Out-Null; $results['failure-throws'] = $false }
catch { $results['failure-throws'] = ($_.Exception.Message -match 'exited 1') }

$out = Invoke-DaemonScript $two 'stop_mcp_daemons.ps1' @('-DryRun')
try { Assert-OnlyAction $out 'WOULD_STOP' 'coordination_room.pid'; $results['extra-action-throws'] = $false }
catch { $results['extra-action-throws'] = $true }

# Review round 4, R4-03: the target must match exactly, not by prefix.
try { Assert-OnlyAction '[FLOSS MCP] WOULD_START packages.coordination_room.server_other (wrong)' 'WOULD_START' 'packages.coordination_room.server'; $results['prefixed-module-throws'] = $false }
catch { $results['prefixed-module-throws'] = $true }
try { Assert-OnlyAction '[FLOSS MCP] WOULD_STOP coordination_room.pid.bak (x)' 'WOULD_STOP' 'coordination_room.pid'; $results['suffixed-pid-throws'] = $false }
catch { $results['suffixed-pid-throws'] = $true }
Assert-OnlyAction '[FLOSS MCP] WOULD_START packages.coordination_room.server (coordination room (:7334))' 'WOULD_START' 'packages.coordination_room.server'
$results['exact-module-passes'] = $true

Assert-PortFree $Port 'none.pid'
$results['free-port-passes'] = $true

$holderFile = Join-Path $Work 'hold_port.py'
Set-Content $holderFile -Encoding ascii -Value "import socket, time`ns = socket.socket()`ns.bind(('127.0.0.1', $Port))`ns.listen()`ntime.sleep(20)"
$holder = Start-Process -PassThru -WindowStyle Hidden -FilePath $py -ArgumentList "`"$holderFile`""
Start-Sleep -Milliseconds 1500
$results['holder-running'] = -not $holder.HasExited
try { Assert-PortFree $Port 'none.pid'; $results['bound-port-throws'] = $false }
catch { $results['bound-port-throws'] = ($_.Exception.Message -match 'still bound') }
Stop-Process -Id $holder.Id -Force -ErrorAction SilentlyContinue

Set-Content (Join-Path $agent 'coordination_room.pid') '4242'
try { Assert-PortFree $Port 'coordination_room.pid'; $results['leftover-pid-throws'] = $false }
catch { $results['leftover-pid-throws'] = ($_.Exception.Message -match 'still present') }

Set-Content $log -Value '{"seq": 1}', '{"seq": 7, "type": "broadcast"}' -Encoding utf8
$results['settled-seq'] = (Get-SettledSeq) -eq 7

# Review round 4, R4-01: prove the smoke post itself is in the shared log.
function Write-Log([string[]]$Rows) {
    # As the room writes it: UTF-8, no BOM, one JSON object per line.
    [IO.File]::WriteAllLines($log, $Rows, (New-Object System.Text.UTF8Encoding($false)))
}
$marker = New-SmokeMarker
$results['marker-shape'] = ($marker -cmatch '^deploy-smoke-[0-9a-f]{32}$') -and ($marker -ne (New-SmokeMarker))
$settledRow = '{"seq": 1, "type": "broadcast", "agent_id": "a", "text": "settled"}'
$smokeRow = '{"seq": 2, "type": "broadcast", "agent_id": "deploy-smoke", "text": "rolled back to v0.1 ' + $marker + '"}'

# Wrong bus: the room that answered returned seq 2, but in the shared log
# seq 2 is another agent's post. The tail moved by one; the post is not there.
Write-Log @($settledRow, '{"seq": 2, "type": "broadcast", "agent_id": "peer", "text": "unrelated"}')
$results['tail-moved-by-one-on-wrong-bus'] = (Get-SettledSeq) -eq 2
try { Assert-SmokeEvent 2 'deploy-smoke' $marker; $results['wrong-bus-throws'] = $false }
catch { $results['wrong-bus-throws'] = ($_.Exception.Message -match 'not the smoke post') }

# Correct bus with a peer posting right after: must pass although the tail is now 3.
Write-Log @($settledRow, $smokeRow, ('{"seq": 3, "type": "broadcast", "agent_id": "peer", "text": "a' + [char]0x2028 + 'b"}'))
Assert-SmokeEvent 2 'deploy-smoke' $marker
$results['interleaved-peer-passes'] = (Get-SettledSeq) -eq 3

try { Assert-SmokeEvent 2 'someone-else' $marker; $results['wrong-agent-throws'] = $false }
catch { $results['wrong-agent-throws'] = $true }
try { Assert-SmokeEvent 2 'deploy-smoke' (New-SmokeMarker); $results['wrong-marker-throws'] = $false }
catch { $results['wrong-marker-throws'] = $true }
try { Assert-SmokeEvent 9 'deploy-smoke' $marker; $results['missing-seq-throws'] = $false }
catch { $results['missing-seq-throws'] = ($_.Exception.Message -match 'appears 0 times') }
# Review round 5 (Codex's characterisation cases): only a generated marker is
# accepted, and it is matched literally and case-sensitively.
foreach ($pair in @(@('empty-marker-throws', ''), @('wildcard-marker-throws', '*'), @('uppercase-marker-throws', $marker.ToUpper()))) {
    try { Assert-SmokeEvent 2 'deploy-smoke' $pair[1]; $results[$pair[0]] = $false }
    catch { $results[$pair[0]] = ($_.Exception.Message -match 'not a marker from New-SmokeMarker') }
}
Write-Log @($settledRow, $smokeRow, $smokeRow)
try { Assert-SmokeEvent 2 'deploy-smoke' $marker; $results['duplicate-seq-throws'] = $false }
catch { $results['duplicate-seq-throws'] = ($_.Exception.Message -match 'appears 2 times') }
Write-Log @($settledRow)
$results['log-row-readback'] = (Get-LogRow 1).agent_id -ceq 'a'

# Review round 6 (Grok), M2: the room skips a line it cannot read; a deployment must not.
Write-Log @($settledRow, '{"seq": 2, "type": "broadcast", "agent_id": "a", "te')
try { Get-SettledSeq | Out-Null; $results['torn-log-stops-deployment'] = $false }
catch { $results['torn-log-stops-deployment'] = ($_.Exception.Message -match 'Line 2 .* not readable JSON') }
Write-Log @('{"seq": 1, "type": "claim", "agent_id": "a", "path": "x.py"}', '{"seq": 2, "type": "claim", "agent_id": "b", "path": "y.py"}', '{"seq": 3, "type": "release", "agent_id": "a", "path": "x.py"}')
$results['log-claims'] = ((Get-LogClaims) -join '|') -ceq 'y.py=b'
$v01 = '{"claims": {"y.py": "b"}, "last_seq": 3, "speakers": ["a", "b"]}' | ConvertFrom-Json
Assert-V01State $v01 3
$results['v01-state-accepted'] = $true
try { Assert-V01State ('{"claims": {"y.py": "someone"}, "last_seq": 3, "speakers": []}' | ConvertFrom-Json) 3; $results['v01-wrong-claims-throws'] = $false }
catch { $results['v01-wrong-claims-throws'] = $true }
try { Assert-V01State $v01 4; $results['v01-behind-settled-throws'] = $false }
catch { $results['v01-behind-settled-throws'] = $true }

$preview = "[FLOSS MCP] coordination room log: $log (root C:\x)"
Assert-PinnedLog $preview
$results['pinned-log-passes'] = $true
try { Assert-PinnedLog "[FLOSS MCP] coordination room log: C:\elsewhere\events.jsonl (root C:\x)"; $results['shadow-log-throws'] = $false }
catch { $results['shadow-log-throws'] = $true }

# Rollback checkout against a scratch repository.
$repo = Join-Path $Work 'repo'
New-Item -ItemType Directory -Force $repo | Out-Null
$previous = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
git -C $repo init -q 2>&1 | Out-Null
git -C $repo -c user.name=t -c user.email=t@t commit -q --allow-empty -m one 2>&1 | Out-Null
$commit = "$(git -C $repo rev-parse HEAD)".Trim()
$ErrorActionPreference = $previous

try { New-PinnedCheckout $repo $commit.Substring(0, 7) (Join-Path $Work 'rb-short'); $results['short-commit-throws'] = $false }
catch { $results['short-commit-throws'] = ($_.Exception.Message -match '40-character') }

New-Item -ItemType Directory -Force (Join-Path $Work 'rb-exists') | Out-Null
try { New-PinnedCheckout $repo $commit (Join-Path $Work 'rb-exists'); $results['existing-path-throws'] = $false }
catch { $results['existing-path-throws'] = ($_.Exception.Message -match 'already exists') }

try { New-PinnedCheckout $repo ('0' * 40) (Join-Path $Work 'rb-missing'); $results['unknown-commit-throws'] = $false }
catch { $results['unknown-commit-throws'] = ($_.Exception.Message -match 'exited') }

New-PinnedCheckout $repo $commit (Join-Path $Work 'rb-good')
$results['good-checkout-passes'] = ("$(git -C (Join-Path $Work 'rb-good') rev-parse HEAD)".Trim() -eq $commit)

# A real scratch room, started by the test, reached through the room's own client.
if ($RoomUrl) {
    $roomUrl = $RoomUrl
    $log = $RoomLog
    $checkout = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
    $settled = Get-SettledSeq
    $state = Invoke-Room $checkout 'room_state'
    Assert-RoomState $state $RoomRoot $settled
    $results['live-state-accepted'] = $true
    try { Assert-RoomState $state (Join-Path $Work 'elsewhere') $settled; $results['live-wrong-root-throws'] = $false }
    catch { $results['live-wrong-root-throws'] = ($_.Exception.Message -match 'root is') }
    try { Assert-RoomState $state $RoomRoot ($settled + 5); $results['live-behind-settled-throws'] = $false }
    catch { $results['live-behind-settled-throws'] = ($_.Exception.Message -match 'below the settled') }

    $marker = New-SmokeMarker
    $reply = Invoke-Room $checkout 'room_broadcast' @{ agent_id = 'deploy-smoke'; text = $marker; topic = 'announcements' }
    Assert-SmokeEvent $reply.seq 'deploy-smoke' $marker
    $results['live-smoke-correlated'] = ([int]$reply.seq -eq $settled + 1)

    try { Invoke-Room $checkout 'room_broadcast' @{ agent_id = 'deploy-smoke'; text = 'x'; topic = 'Bad Topic' } | Out-Null; $results['live-room-error-throws'] = $false }
    catch { $results['live-room-error-throws'] = ($_.Exception.Message -match 'exited 2') }

    Invoke-Room $checkout 'room_claim' @{ agent_id = 'deploy-smoke'; path = 'x.py' } | Out-Null
    Assert-V01State (Invoke-Room $checkout 'room_state') $settled
    $results['live-v01-view-accepted'] = $true

    $roomUrl = 'http://127.0.0.1:9/mcp'
    try { Invoke-Room $checkout 'room_state' | Out-Null; $results['unreachable-room-throws'] = $false }
    catch { $results['unreachable-room-throws'] = ($_.Exception.Message -match 'exited 1') }
}

$results | ConvertTo-Json
