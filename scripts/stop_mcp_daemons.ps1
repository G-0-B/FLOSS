# FLOSS/scripts/stop_mcp_daemons.ps1 — stop all FLOSS MCP daemons cleanly.
# Kills: consensus (:7331), ensemble (:7332), OmniRoute (:20128).
# Removes PID files so next start is clean.

$flossAgent = "$env:USERPROFILE\.floss_agent"

# Kill FLOSS MCP daemons via PID files
$pidFiles = @("consensus.pid", "reasoning_ensemble.pid")
foreach ($pidFile in $pidFiles) {
    $pidPath = Join-Path $flossAgent $pidFile
    if (Test-Path $pidPath) {
        $pid = [int](Get-Content $pidPath -Raw).Trim()
        try {
            Stop-Process -Id $pid -Force -ErrorAction Stop
            Write-Host "[FLOSS MCP] Killed $pidFile (PID $pid)"
        } catch {
            Write-Host "[FLOSS MCP] $pidFile stale (PID $pid not running)"
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
