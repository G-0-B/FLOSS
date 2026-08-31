# FLOSS/scripts/start_mcp_daemons.ps1 — start OmniRoute + both MCP daemons if not already up.
# Idempotent: PID guard in mcp_daemon.py makes re-runs safe (second launch self-exits).
# Register as a Scheduled Task:
#   schtasks /Create /TN "FLOSS-MCP-Daemons" /TR "powershell -WindowStyle Hidden -File C:\~shit\FLOSS\scripts\start_mcp_daemons.ps1" /SC ONLOGON /RU "MSI\kalis" /RL LIMITED /F

# Derive everything from where THIS script lives. The hardcoded
# C:\~shit\FLOSS and C:\Python313\python.exe worked on exactly one machine and
# one checkout: from a clone at any other path this started daemons whose
# PYTHONPATH pointed at a different working tree than the one being developed,
# with no error to say so, and on a machine without that interpreter it failed
# outright. $PSScriptRoot is scripts/, so the repository root is its parent.
$workspace = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = $workspace
# `$workspace` is the REPOSITORY root here (parent of scripts/), despite the
# name. Aliased so the identity calls below read correctly, and the agent
# directory is resolved the same way mcp_daemon.py and the stop script do.
$repoRoot = $workspace
$flossAgent = if ($env:FLOSS_AGENT_DIR) { $env:FLOSS_AGENT_DIR } else { "$env:USERPROFILE\.floss_agent" }

# Honour an explicit interpreter, then a venv inside the checkout, then PATH.
if ($env:FLOSS_PYTHON) {
    $py = $env:FLOSS_PYTHON
} elseif (Test-Path (Join-Path $workspace "venv\Scripts\python.exe")) {
    $py = Join-Path $workspace "venv\Scripts\python.exe"
} else {
    # `?.` is PowerShell 7.1+. The documented Scheduled Task registers this
    # with `powershell`, which is Windows PowerShell 5.1 -- and 5.1 fails to
    # PARSE the whole file on that operator, so no daemon starts at all.
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    $py = if ($cmd) { $cmd.Source } else { $null }
}
if (-not $py -or -not (Test-Path $py)) {
    Write-Error "[FLOSS MCP] No usable Python found. Set FLOSS_PYTHON to an interpreter, or create $workspace\venv."
    exit 1
}

function Resolve-ServerPid {
    <#
      npm installs `omniroute` as a .cmd shim on Windows; Start-Process -PassThru
      returns that shim, not the Node server it spawns. Walk the process tree
      down from the launcher and return the first node process found, polling
      because the child does not exist the instant Start-Process returns.
      Returns 0 if no node descendant appears within the timeout.
    #>
    param([int]$RootPid, [int]$TimeoutMs = 8000)

    $deadline = (Get-Date).AddMilliseconds($TimeoutMs)
    while ((Get-Date) -lt $deadline) {
        $frontier = @($RootPid)
        $guard = 0
        while ($frontier.Count -gt 0 -and $guard -lt 8) {
            $guard++
            $next = @()
            foreach ($parent in $frontier) {
                $kids = Get-CimInstance Win32_Process -Filter "ParentProcessId=$parent" -ErrorAction SilentlyContinue
                foreach ($kid in $kids) {
                    if ($kid.Name -eq 'node.exe') { return [int]$kid.ProcessId }
                    $next += [int]$kid.ProcessId
                }
            }
            $frontier = $next
        }
        Start-Sleep -Milliseconds 250
    }
    return 0
}

# Start consensus gateway daemon (port 7331)
Start-Process -WindowStyle Hidden -WorkingDirectory $workspace $py "-m packages.metacoordinator_mcp.server"

# Start reasoning ensemble daemon (port 7332)
Start-Process -WindowStyle Hidden -WorkingDirectory $workspace $py "-m packages.reasoning_ensemble.mcp_server"

# Start OmniRoute daemon (port 20128) — model routing + token compression
# Match on the COMMAND LINE, not $_.Path. For an npm-installed OmniRoute the
# process is plain node.exe, so .Path is the Node binary and never contains
# "omniroute". The old filter therefore found nothing every time, and this
# script started ANOTHER OmniRoute on every rerun despite the duplicate
# guard it advertises below. Same root cause as the stop script, opposite
# and equally wrong outcome.
# IDENTITY, NOT COMMAND-LINE MATCHING.
#
# Matching `omniroute` across every node.exe on the host let ANOTHER
# project's OmniRoute satisfy this duplicate guard, so the launcher skipped
# its own startup and then reported all daemons started -- on a different
# port, config and credentials.
#
# Scoping the match to this checkout does not work: `omniroute --no-open`
# produces a command line referencing the globally installed package and
# never the working directory, so a checkout filter matches nothing and
# classifies our own process as foreign. That was tried and it was wrong.
#
# So the PID and creation token are recorded at launch, exactly as
# claim_singleton does for the Python daemons. One mechanism, third caller.
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
# UNKNOWN IS OCCUPIED, not free.
#
# The stop path and claim_singleton both treat an unverifiable holder as
# still holding; this branch treated it as absent and started a duplicate.
# The duplicate then loses the port bind, but --record-identity has ALREADY
# overwritten the record with its PID -- so when it exits, the original
# OmniRoute is live, untracked, and can no longer be stopped by the
# companion script. Same verdict, three callers, and this was the one that
# read it optimistically.
if ($omniVerdict -eq 'UNKNOWN' -and (Test-Path $omniPid)) {
    Write-Host "[FLOSS MCP] OmniRoute record exists but identity is UNVERIFIABLE - not starting a duplicate. Delete $omniPid if you know it is stale."
} elseif ($omniVerdict -eq 'OURS') {
    Write-Host "[FLOSS MCP] OmniRoute already running (recorded PID $(Get-Content $omniPid -Raw))"
} else {
    # RESERVE THE SLOT BEFORE LAUNCHING, NOT AFTER.
    #
    # Two copies of this script with no omniroute.pid could both reach this
    # branch, both launch, and both record: the one that lost the port bind
    # recorded last and then exited, leaving the bound server live and
    # untracked. --reserve-slot is O_CREAT|O_EXCL through the same primitive
    # claim_singleton uses, so exactly one launcher gets past this line.
    $reserved = $false
    if ($py) {
        Push-Location $repoRoot
        $slotOut = & $py -m packages.mcp_daemon --reserve-slot $omniPid 2>$null
        Pop-Location
        $slotTok = ($slotOut | Select-Object -Last 1)
        if ($slotTok) { $slotTok = $slotTok.ToString().Trim() }
        $reserved = ($slotTok -eq 'RESERVED')
    }
    if (-not $reserved) {
        # NOT `return`: this is script scope, so returning here would also skip
        # the summary line at the end of the file. Only the launch is skipped.
        Write-Host "[FLOSS MCP] OmniRoute slot is already claimed by another launcher - not starting a duplicate"
        $proc = $null
    } else {
        $proc = Start-Process -WindowStyle Hidden -PassThru 'omniroute' '--no-open'
    }
    # RECORD THE SERVER, NOT THE SHIM.
    #
    # On the documented Windows npm install, `omniroute` is a .cmd shim, so
    # -PassThru hands back cmd.exe and the Node server is its child. Windows
    # does not kill children with their parent, so recording the shim let the
    # stop script delete the sidecars and leave OmniRoute listening and
    # untracked -- the exact orphan the identity mechanism replaced command-line
    # matching to prevent. Walk to the real process before recording.
    $serverPid = 0
    if ($proc) {
        if ($proc.Name -eq 'node') {
            $serverPid = $proc.Id
        } else {
            $serverPid = Resolve-ServerPid $proc.Id
        }
    }
    if ($serverPid -eq 0 -and $proc) {
        # Recording nothing is worse: the duplicate guard reads an absent record
        # as free and starts a second server. Record the shim so the guard still
        # holds, and say plainly that stop cannot reach the child.
        $serverPid = $proc.Id
        Write-Host "[FLOSS MCP] WARNING: could not identify the OmniRoute Node process under PID $($proc.Id); recording the launcher instead, so stopping may leave the server running. Inspect it with Get-CimInstance Win32_Process -Filter ParentProcessId=$($proc.Id)"
    }
    if ($serverPid -and $py) {
        Push-Location $repoRoot
        $recOut = & $py -m packages.mcp_daemon --record-identity $omniPid $serverPid
        Pop-Location
        $recTok = ($recOut | Select-Object -Last 1)
        if ($recTok) { $recTok = $recTok.ToString().Trim() }
        if ($recTok -ne 'RECORDED') {
            # The reservation is an EMPTY file, which every reader treats as an
            # in-progress claim and therefore as occupied. Left behind after a
            # failed recording it would block every future start with nothing
            # running. We hold it exclusively, so clearing it is ours to do.
            Write-Host "[FLOSS MCP] WARNING: could not record the OmniRoute identity ($recTok); releasing the reservation so a later start is not blocked"
            Remove-Item $omniPid -Force -ErrorAction SilentlyContinue
        }
    } elseif ($reserved) {
        # Reserved the slot and then failed to launch: release it rather than
        # leaving an empty claim that blocks forever.
        Write-Host "[FLOSS MCP] OmniRoute did not start; releasing the reserved slot"
        Remove-Item $omniPid -Force -ErrorAction SilentlyContinue
    }
    if ($proc) {
        Write-Host "[FLOSS MCP] OmniRoute started (:20128, PID $serverPid)"
    }
}

Write-Host "[FLOSS MCP] Daemons started (consensus :7331, ensemble :7332, omniroute :20128). PID guard prevents duplicates."
