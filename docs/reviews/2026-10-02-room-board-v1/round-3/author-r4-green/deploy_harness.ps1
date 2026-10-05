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
