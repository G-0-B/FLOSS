# FLOSS/scripts/stop_mcp_daemons.ps1 — stop all FLOSS MCP daemons cleanly.
# Kills: consensus (:7331), ensemble (:7332), OmniRoute (:20128).
# Removes PID files so next start is clean.

# Same resolution mcp_daemon.py uses when it WRITES these files
# (`Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))`).
# Reading only ~/.floss_agent meant that under the supported override this
# script found no PID files, reported "All daemons stopped", and left every
# daemon running.
$flossAgent = if ($env:FLOSS_AGENT_DIR) { $env:FLOSS_AGENT_DIR } else { "$env:USERPROFILE\.floss_agent" }

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
        # Do NOT assume every Stop-Process failure means the process is gone.
        # It also fails on access-denied and on protected processes. Reporting
        # those as "stale" and deleting the pid file anyway makes a LIVE daemon
        # unfindable -- the same end state the $PID bug above produced, reached
        # a different way. Confirm the process is actually gone before removing
        # the file.
        $stopped = $false
        try {
            Stop-Process -Id $daemonPid -Force -ErrorAction Stop
            $stopped = $true
            Write-Host "[FLOSS MCP] Killed $pidFile (PID $daemonPid)"
        } catch {
            if (-not (Get-Process -Id $daemonPid -ErrorAction SilentlyContinue)) {
                $stopped = $true
                Write-Host "[FLOSS MCP] $pidFile stale (PID $daemonPid not running)"
            } else {
                Write-Host "[FLOSS MCP] $pidFile PID $daemonPid is ALIVE but could not be stopped: $($_.Exception.Message)"
                Write-Host "[FLOSS MCP] Keeping $pidFile so the daemon stays findable."
            }
        }
        if ($stopped) {
            Remove-Item $pidPath -Force -ErrorAction SilentlyContinue
        }
    }
}

# Kill OmniRoute.
# Match on the COMMAND LINE, not $_.Path. For an npm-installed OmniRoute the
# process is plain node.exe, so .Path is the Node binary and never contains
# "omniroute" -- the old filter found nothing and the script cheerfully reported
# OmniRoute stopped while it kept running. The identical mistake in
# start_mcp_daemons.ps1 launched a second copy on every rerun.
$omni = Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
    Where-Object { $_.CommandLine -match 'omniroute' }
if ($omni) {
    $omni | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Write-Host "[FLOSS MCP] OmniRoute stopped"
} else {
    Write-Host "[FLOSS MCP] OmniRoute not running"
}

# Kill any orphaned npx @agentmemory processes
$orphans = Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object { $_.CommandLine -match 'agentmemory|januscope' }
if ($orphans) {
    $orphans | ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "[FLOSS MCP] Killed orphan PID $($_.ProcessId)"
    }
}

Write-Host "[FLOSS MCP] All daemons stopped. PID files cleaned."
