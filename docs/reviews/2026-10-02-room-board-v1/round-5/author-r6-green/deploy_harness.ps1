# Scratch-only inert test of deploy_helpers.ps1: fake checkouts, a scratch
# port, a scratch log. No real daemon, PID file or port 7334/7335 is touched.
param([string]$Work)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'deploy_helpers.ps1')
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

Assert-PortFree 19994 'none.pid'
$results['free-port-passes'] = $true

$holderFile = Join-Path $Work 'hold_port.py'
Set-Content $holderFile -Encoding ascii -Value "import socket, time`ns = socket.socket()`ns.bind(('127.0.0.1', 19994))`ns.listen()`ntime.sleep(20)"
$holder = Start-Process -PassThru -WindowStyle Hidden -FilePath $py -ArgumentList "`"$holderFile`""
Start-Sleep -Milliseconds 1500
$results['holder-running'] = -not $holder.HasExited
try { Assert-PortFree 19994 'none.pid'; $results['bound-port-throws'] = $false }
catch { $results['bound-port-throws'] = ($_.Exception.Message -match 'still bound') }
Stop-Process -Id $holder.Id -Force -ErrorAction SilentlyContinue

Set-Content (Join-Path $agent 'coordination_room.pid') '4242'
try { Assert-PortFree 19994 'coordination_room.pid'; $results['leftover-pid-throws'] = $false }
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

try { New-RollbackCheckout $repo $commit.Substring(0, 7) (Join-Path $Work 'rb-short'); $results['short-commit-throws'] = $false }
catch { $results['short-commit-throws'] = ($_.Exception.Message -match '40-character') }

New-Item -ItemType Directory -Force (Join-Path $Work 'rb-exists') | Out-Null
try { New-RollbackCheckout $repo $commit (Join-Path $Work 'rb-exists'); $results['existing-path-throws'] = $false }
catch { $results['existing-path-throws'] = ($_.Exception.Message -match 'already exists') }

try { New-RollbackCheckout $repo ('0' * 40) (Join-Path $Work 'rb-missing'); $results['unknown-commit-throws'] = $false }
catch { $results['unknown-commit-throws'] = ($_.Exception.Message -match 'exited') }

New-RollbackCheckout $repo $commit (Join-Path $Work 'rb-good')
$results['good-checkout-passes'] = ("$(git -C (Join-Path $Work 'rb-good') rev-parse HEAD)".Trim() -eq $commit)

$results | ConvertTo-Json
