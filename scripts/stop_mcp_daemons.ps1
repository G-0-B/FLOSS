# FLOSS/scripts/stop_mcp_daemons.ps1 — stop all FLOSS MCP daemons cleanly.
# Kills: consensus (:7331), ensemble (:7332), OmniRoute (:20128).
# Removes PID files so next start is clean.

$flossAgent = "$env:USERPROFILE\.floss_agent"

# Kill FLOSS MCP daemons via PID files
$pidFiles = @("consensus.pid", "reasoning_ensemble.pid")
foreach ($pidFile in $pidFiles) {
    $pidPath = Join-Path $flossAgent $pidFile
    if (Test-Path $pidPath) {
        # MUST NOT be named $pid: PowerShell's $PID is a read-only automatic
        # variable holding THIS process's id, and the name is case-insensitive.
        # Assigning to it fails with "Cannot overwrite variable PID because it
        # is read-only or constant" -- and that error is NOT terminating at
        # script scope, so the old code carried straight on with $pid still
        # holding the running shell's own id. Stop-Process then targeted this
        # script's process, and Remove-Item deleted the pid file regardless,
        # leaving the real daemon alive and now unfindable. Strictly worse than
        # a no-op.
        $raw = (Get-Content $pidPath -Raw).Trim()
        $daemonPid = 0
        if (-not [int]::TryParse($raw, [ref]$daemonPid) -or $daemonPid -le 0) {
            Write-Host "[FLOSS MCP] $pidFile unreadable (contents: '$raw') - leaving it in place"
            continue
        }
        if ($daemonPid -eq $PID) {
            Write-Host "[FLOSS MCP] $pidFile names this very process ($PID) - refusing to self-terminate"
            continue
        }
        try {
            Stop-Process -Id $daemonPid -Force -ErrorAction Stop
            Write-Host "[FLOSS MCP] Killed $pidFile (PID $daemonPid)"
        } catch {
            Write-Host "[FLOSS MCP] $pidFile stale (PID $daemonPid not running)"
        }
        Remove-Item $pidPath -Force -ErrorAction SilentlyContinue
    }
}

# Kill OmniRoute
$omni = Get-Process -Name 'node' -ErrorAction SilentlyContinue | Where-Object { $_.Path -match 'omniroute' }
if ($omni) {
    $omni | ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }
    Write-Host "[FLOSS MCP] OmniRoute stopped"
} else {
    Write-Host "[FLOSS MCP] OmniRoute not running"
}

# Kill any orphaned npx @agentmemory processes
$orphans = Get-WmiObject Win32_Process -Filter "Name='node.exe'" | Where-Object { $_.CommandLine -match 'agentmemory|januscope' }
if ($orphans) {
    $orphans | ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "[FLOSS MCP] Killed orphan PID $($_.ProcessId)"
    }
}

Write-Host "[FLOSS MCP] All daemons stopped. PID files cleaned."
