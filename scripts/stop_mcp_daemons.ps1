# FLOSS/scripts/stop_mcp_daemons.ps1 — stop all FLOSS MCP daemons cleanly.
# Kills: consensus (:7331), ensemble (:7332), OmniRoute (:20128).
# Removes PID files so next start is clean.

# Same resolution mcp_daemon.py uses when it WRITES these files
# (`Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))`).
# Reading only ~/.floss_agent meant that under the supported override this
# script found no PID files, reported "All daemons stopped", and left every
# daemon running.
$flossAgent = if ($env:FLOSS_AGENT_DIR) { $env:FLOSS_AGENT_DIR } else { "$env:USERPROFILE\.floss_agent" }

# Same interpreter resolution the START script uses: explicit FLOSS_PYTHON,
# then a venv inside the checkout, then PATH. The identity check delegates to
# `packages.mcp_daemon`, so running it under a different interpreter -- or
# from outside the repository -- makes the import fail. PowerShell does NOT
# enter catch for a failed external command; it records exit 1, which this
# script previously read as a proven identity mismatch and acted on by
# deleting the PID files while the daemons kept running, unfindable.
$repoRoot = Split-Path -Parent $PSScriptRoot
$workspace = Split-Path -Parent $repoRoot
if ($env:FLOSS_PYTHON) {
    $py = $env:FLOSS_PYTHON
} elseif (Test-Path (Join-Path $workspace 'venv\Scripts\python.exe')) {
    $py = Join-Path $workspace 'venv\Scripts\python.exe'
} elseif (Test-Path (Join-Path $repoRoot 'venv\Scripts\python.exe')) {
    $py = Join-Path $repoRoot 'venv\Scripts\python.exe'
} else {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    $py = if ($cmd) { $cmd.Source } else { $null }
}

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
        # IDENTITY BEFORE FORCE. claim_singleton records a process-creation
        # token beside the PID file; this path never read it, so after a crash
        # or reboot a reassigned PID was killed and its file deleted -- the
        # user-impacting half of the PID-reuse defect, still live after the
        # claim-side fix.
        #
        # The check is DELEGATED to mcp_daemon rather than reimplemented here.
        # One implementation, two callers: a first attempt at computing the
        # token in PowerShell produced a DIFFERENT value for the same PID,
        # because `-band 0xFFFFFFFF` does not mask an int64. A stop path with a
        # slightly different token would refuse to stop real daemons or agree
        # to kill innocent ones.
        #
        # Exit 0 = provably ours, 1 = provably not, 2 = cannot tell. Only 0 may
        # kill; 2 keeps the conservative behaviour claim_singleton uses.
        # The VERDICT IS THE TOKEN ON STDOUT, not the exit status. A checker
        # that failed to start also exits 1, and treating that as FOREIGN is
        # exactly how live daemons got orphaned. A process that never ran
        # cannot print a token it never produced.
        $verdict = 'UNKNOWN'
        if ($py) {
            try {
                Push-Location $repoRoot
                $out = & $py -m packages.mcp_daemon --check-identity $pidPath 2>$null
                Pop-Location
                $token = ($out | Select-Object -Last 1)
                if ($token) { $token = $token.ToString().Trim() }
                if ($token -eq 'OURS' -or $token -eq 'FOREIGN') { $verdict = $token }
            } catch {
                $verdict = 'UNKNOWN'
            }
        } else {
            Write-Host "[FLOSS MCP] no usable Python found - identity unverifiable. Set FLOSS_PYTHON."
        }
        if ($verdict -eq 'FOREIGN') {
            Write-Host "[FLOSS MCP] $pidFile PID $daemonPid is NOT our daemon (identity mismatch or process gone) - removing the stale file, killing nothing"
            Remove-Item $pidPath -Force -ErrorAction SilentlyContinue
            Remove-Item "$pidPath.identity" -Force -ErrorAction SilentlyContinue
            continue
        }
        if ($verdict -ne 'OURS') {
            Write-Host "[FLOSS MCP] $pidFile PID $daemonPid identity UNVERIFIABLE (verdict=$verdict) - refusing to force-kill, and KEEPING the pid file so the daemon stays findable."
            continue
        }

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
# IDENTITY, NOT COMMAND-LINE MATCHING.
#
# First this matched `omniroute` across every node.exe on the host and
# force-killed all of them, including another project's. Then it was scoped
# to processes whose command line referenced this checkout -- which was ALSO
# wrong, and worse: the start script runs `omniroute --no-open`, so the child
# command line names the globally installed package and never the working
# directory. That filter matched nothing, classified our own OmniRoute as
# foreign, and left it running on every stop.
#
# Two wrong filters in two commits is the signal to stop filtering. The start
# script now records the PID and creation token at launch, the same mechanism
# claim_singleton uses, and this reads it.
$omniPid = Join-Path $flossAgent 'omniroute.pid'
$omniVerdict = 'UNKNOWN'
if ($py -and (Test-Path $omniPid)) {
    Push-Location $repoRoot
    $out = & $py -m packages.mcp_daemon --check-identity $omniPid 2>$null
    Pop-Location
    $tok = ($out | Select-Object -Last 1)
    if ($tok) { $tok = $tok.ToString().Trim() }
    if ($tok -eq 'OURS' -or $tok -eq 'FOREIGN') { $omniVerdict = $tok }
}
if ($omniVerdict -eq 'OURS') {
    # CONFIRM IT IS GONE BEFORE DELETING THE RECORD.
    #
    # -ErrorAction SilentlyContinue swallowed access-denied and every other
    # transient failure, and the next two lines deleted the record anyway:
    # the live process became unfindable while the script reported it
    # stopped. The Python-daemon branch fifteen lines above does this
    # correctly and says why; this branch was written without looking at it.
    $omniId = [int]((Get-Content $omniPid -Raw).Trim())
    $omniStopped = $false
    try {
        Stop-Process -Id $omniId -Force -ErrorAction Stop
        $omniStopped = $true
    } catch {
        if (-not (Get-Process -Id $omniId -ErrorAction SilentlyContinue)) {
            $omniStopped = $true
        } else {
            Write-Host "[FLOSS MCP] OmniRoute PID $omniId is ALIVE but could not be stopped: $($_.Exception.Message)"
            Write-Host "[FLOSS MCP] Keeping $omniPid so it stays findable."
        }
    }
    if ($omniStopped) {
        # THE SIDECAR GOES FIRST, for the reason mcp_daemon.py already records
        # against its own release path: freeing the PID slot first lets a
        # replacement launcher claim it and write ITS identity inside the
        # window, and the next line then deletes the replacement's identity.
        # The new server stays live with an unverifiable record, which both
        # start and stop refuse to act on. Removing the identity first means
        # the worst case is an unverifiable holder, which blocks.
        Remove-Item "$omniPid.identity" -Force -ErrorAction SilentlyContinue
        Remove-Item $omniPid -Force -ErrorAction SilentlyContinue
        Write-Host "[FLOSS MCP] OmniRoute stopped (PID $omniId)"
    }
} elseif ($omniVerdict -eq 'FOREIGN') {
    # Same ordering as the stopped branch above: sidecar first, slot second.
    Remove-Item "$omniPid.identity" -Force -ErrorAction SilentlyContinue
    Remove-Item $omniPid -Force -ErrorAction SilentlyContinue
    Write-Host "[FLOSS MCP] OmniRoute record was stale (that PID is not ours) - cleared, killed nothing"
} else {
    Write-Host "[FLOSS MCP] OmniRoute not started by this stack, or identity unverifiable - killing nothing"
}

# agentmemory / JanuScope: REPORTED, NOT KILLED.
#
# This block matched every node.exe on the host whose command line mentioned
# agentmemory or januscope and force-killed all of them -- including the live
# wrapper of an active Claude, Codex or Hermes session that this script has
# nothing to do with. It checked neither parent liveness nor whether the
# process belonged to this stack, so "stop my two HTTP daemons" could take
# down someone else's running agent.
#
# It is also the SAME over-broad match fixed for OmniRoute twenty lines above,
# in the same commit -- one site scoped, its sibling left alone.
#
# sweep_mcp_orphans.ps1 already does this properly: parent-liveness, an age
# and CPU heuristic for leaked subagent wrappers, and a protected-PID list.
# Reimplementing a weaker copy of it here is how the two drift apart, so this
# reports and defers rather than guessing.
$candidates = Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
    Where-Object { $_.CommandLine -match 'agentmemory|januscope' }
if ($candidates) {
    Write-Host "[FLOSS MCP] $($candidates.Count) agentmemory/JanuScope node process(es) present. NOT killed - they may belong to a live agent session."
    foreach ($c in $candidates) {
        Write-Host "[FLOSS MCP]   PID $($c.ProcessId) (parent $($c.ParentProcessId))"
    }
    Write-Host "[FLOSS MCP] Run scripts/sweep_mcp_orphans.ps1 to reap genuinely orphaned ones - it checks parent liveness and protects the daemons."
}

Write-Host "[FLOSS MCP] All daemons stopped. PID files cleaned."
