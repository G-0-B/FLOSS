# FLOSS/scripts/stop_mcp_daemons.ps1 — stop all FLOSS MCP daemons cleanly.
# Kills: consensus (:7331), ensemble (:7332), coordination room (:7334), OmniRoute (:20128).
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

# Anything this script deliberately leaves running or leaves on disk lands
# here, and the closing summary reports it. Declared as an explicit array: in
# PowerShell `$undefined + "text"` yields a STRING, and .Count on a scalar is
# not the count of anything.
$unresolved = @()

# Kill FLOSS MCP daemons via PID files
$pidFiles = @("consensus.pid", "reasoning_ensemble.pid", "coordination_room.pid")
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
            $unresolved += "$pidFile - unreadable pid file, left in place"
            continue
        }
        if ($daemonPid -eq $PID) {
            Write-Host "[FLOSS MCP] $pidFile names this very process ($PID) - refusing to self-terminate"
            $unresolved += "$pidFile - names this process, left in place"
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
            # BY INSTANCE, through the same helper the start workflow uses.
            #
            # Remove-Item deletes whatever is at the path with no snapshot
            # check, so a start script that reclaimed this same FOREIGN record
            # and installed a fresh reservation in between had that reservation
            # deleted here -- freeing the slot for yet another launcher and
            # letting two daemons start. Stop and start race over exactly the
            # same records, so they have to reclaim the same way.
            if ($py) {
                Push-Location $repoRoot
                $rc = & $py -m packages.mcp_daemon --reclaim-claim $pidPath 2>$null
                Pop-Location
                $rcTok = ($rc | Select-Object -Last 1)
                if ($rcTok) { $rcTok = $rcTok.ToString().Trim() }
                if ($rcTok -eq 'RECLAIMED') {
                    Write-Host "[FLOSS MCP] $pidFile PID $daemonPid is NOT our daemon - stale record cleared, killed nothing"
                } else {
                    Write-Host "[FLOSS MCP] $pidFile stale record was claimed by another process first - left alone"
                }
            } else {
                Write-Host "[FLOSS MCP] $pidFile PID $daemonPid is NOT our daemon, but no Python is available to clear the record safely; leaving it in place"
                $unresolved += "$pidFile - stale record left in place; set FLOSS_PYTHON"
            }
            continue
        }
        if ($verdict -ne 'OURS') {
            Write-Host "[FLOSS MCP] $pidFile PID $daemonPid identity UNVERIFIABLE (verdict=$verdict) - refusing to force-kill, and KEEPING the pid file so the daemon stays findable."
            $unresolved += "$pidFile PID $daemonPid - identity unverifiable, may still be running"
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
                $unresolved += "$pidFile PID $daemonPid - ALIVE, could not be stopped"
            }
        }
        if ($stopped) {
            # THE SIDECAR GOES FIRST, AND IT MUST GO.
            #
            # This branch removed only the pid file. The daemon's own atexit
            # cleanup usually takes the sidecar, but it does not run on a
            # force-kill or a crash -- so a stale <pid>.identity outlived the
            # slot. A replacement launcher then created and populated the new
            # pid file while that stale token still sat beside it, and a
            # concurrent claimant comparing the two saw a mismatch, judged the
            # valid claim stale, and reclaimed the slot: two daemons, both
            # believing they hold it.
            #
            # Ordering matters for the same reason mcp_daemon.py documents on
            # its own release path: freeing the slot first opens a window in
            # which a replacement writes its identity and this line deletes it.
            Remove-Item "$pidPath.identity" -Force -ErrorAction SilentlyContinue
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
            $unresolved += "OmniRoute PID $omniId - ALIVE, could not be stopped"
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
} elseif ($omniVerdict -eq 'FOREIGN' -and $py) {
    # Same instance-checked reclaim as the daemon branch above, and as the start
    # script: this had the identical race.
    Push-Location $repoRoot
    $rcOmni = & $py -m packages.mcp_daemon --reclaim-claim $omniPid 2>$null
    Pop-Location
    $rcOmniTok = ($rcOmni | Select-Object -Last 1)
    if ($rcOmniTok) { $rcOmniTok = $rcOmniTok.ToString().Trim() }
    if ($rcOmniTok -eq 'RECLAIMED') {
        Write-Host "[FLOSS MCP] OmniRoute record was stale (that PID is not ours) - cleared, killed nothing"
    } else {
        Write-Host "[FLOSS MCP] OmniRoute stale record was claimed by another process first - left alone"
    }
} elseif ($omniVerdict -eq 'FOREIGN') {
    Write-Host "[FLOSS MCP] OmniRoute record is stale but no Python is available to clear it safely; leaving it in place"
    $unresolved += "OmniRoute - stale record left in place; set FLOSS_PYTHON"
} else {
    Write-Host "[FLOSS MCP] OmniRoute not started by this stack, or identity unverifiable - killing nothing"
    if (Test-Path $omniPid) {
        $unresolved += "OmniRoute - record present but identity unverifiable, may still be listening on :20128"
    }
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

# THE SUMMARY MUST DESCRIBE WHAT HAPPENED.
#
# Every branch above that keeps a pid file does so deliberately -- an
# unverifiable holder may be alive, and a daemon that would not die stays
# findable. But the closing line said "All daemons stopped. PID files cleaned."
# unconditionally, so the careful refusals were reported as a clean shutdown.
# An operator then restarts, or frees the port, on a false premise.
if ($unresolved.Count -gt 0) {
    Write-Host "[FLOSS MCP] SHUTDOWN INCOMPLETE - $($unresolved.Count) item(s) left in place:"
    foreach ($item in $unresolved) {
        Write-Host "[FLOSS MCP]   $item"
    }
    Write-Host "[FLOSS MCP] Ports and pid files above are still in use. Resolve them before assuming the stack is down."
    exit 1
}

Write-Host "[FLOSS MCP] All daemons stopped. PID files cleaned."
