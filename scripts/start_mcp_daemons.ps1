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

function Release-OmniClaim {
    <#
      Release the OmniRoute claim ONLY if it is still the reservation this
      launcher made. Four sites across the two scripts used to release with
      `Remove-Item <path>`, which deletes whatever occupies the pathname --
      including the record of a launcher that legitimately reclaimed the slot
      and started a server. NOT_RELEASED simply means someone else owns it now,
      which is the state this cleanup wanted to reach anyway.

      With no token (a pre-marker or failed reservation) there is nothing to
      prove ownership with, so nothing is released: an occupied-but-
      unattributable slot blocks the next start, which is the safe failure.
    #>
    param([string]$Token)
    if (-not $Token) {
        Write-Host "[FLOSS MCP] No reservation token to release with; leaving $omniPid in place for an operator"
        return $false
    }
    if (-not $py) { return $false }
    Push-Location $repoRoot
    $out = & $py -m packages.mcp_daemon --release-claim $omniPid token $Token 2>$null
    Pop-Location
    $tok = ($out | Select-Object -Last 1)
    if ($tok) { $tok = $tok.ToString().Trim() }
    if ($tok -eq 'RELEASED') { return $true }
    if ($tok -eq 'SUPERSEDED') {
        Write-Host "[FLOSS MCP] OmniRoute slot is no longer ours to release - another launcher owns it; leaving its record intact"
        return $true
    }
    Write-Host "[FLOSS MCP] OmniRoute reservation could NOT be released (verdict=$tok); it will block the next start until an operator clears $omniPid"
    $script:skipped += "OmniRoute (:20128) - reservation could not be released; clear $omniPid by hand"
    return $false
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

# Anything this script declines to start, starts without being able to record,
# or watches die on the spot lands here, and the closing summary reports it.
# Explicit array: in PowerShell `$undefined + "text"` yields a STRING, and
# .Count on a scalar is not the count of anything.
$skipped = @()

function Start-Daemon {
    <#
      Fire-and-forget launches were never inspected, so a module that fails to
      import, a missing dependency, or a port already bound produced no output
      and no entry anywhere -- and the closing summary still reported the
      daemon up. A short settle window catches an immediate exit, which is what
      every one of those failures looks like. It cannot prove readiness; it does
      prove the process did not die on the spot, and that is the difference
      between a claim and a guess.
    #>
    param([string]$Interpreter, [string]$Module, [string]$Label, [string]$WorkDir)

    $proc = Start-Process -WindowStyle Hidden -PassThru -WorkingDirectory $WorkDir $Interpreter "-m $Module"
    if (-not $proc) {
        Write-Host "[FLOSS MCP] $Label failed to launch"
        return $null
    }
    Start-Sleep -Milliseconds 1500
    $proc.Refresh()
    if ($proc.HasExited) {
        # EXIT 0 IS THE SINGLETON DOING ITS JOB, NOT A FAILURE.
        #
        # claim_singleton() finds the daemon already running and exits cleanly,
        # which is the whole point of rerunning this script. Treating every
        # immediate exit as a failure made an idempotent rerun report STARTUP
        # INCOMPLETE and exit 1 while both ports were correctly served -- the
        # mirror of the bug this check was added to fix, in the other
        # direction: claiming failure it had not observed.
        if ($proc.ExitCode -eq 0) {
            Write-Host "[FLOSS MCP] $Label already running (singleton guard declined a duplicate)"
            return $proc
        }
        Write-Host "[FLOSS MCP] $Label exited immediately (code $($proc.ExitCode)) - run it by hand to see why: $Interpreter -m $Module"
        return $null
    }
    return $proc
}

# Start consensus gateway daemon (port 7331)
$consensusProc = Start-Daemon $py "packages.metacoordinator_mcp.server" "consensus gateway (:7331)" $workspace
if (-not $consensusProc) { $skipped += "consensus gateway (:7331) - exited immediately after launch" }

# Start reasoning ensemble daemon (port 7332)
$ensembleProc = Start-Daemon $py "packages.reasoning_ensemble.mcp_server" "reasoning ensemble (:7332)" $workspace
if (-not $ensembleProc) { $skipped += "reasoning ensemble (:7332) - exited immediately after launch" }

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
$omniRaw = if (Test-Path $omniPid) { (Get-Content $omniPid -Raw -ErrorAction SilentlyContinue) } else { $null }
if ($null -ne $omniRaw) { $omniRaw = $omniRaw.Trim() }
# EMPTY *OR* MARKED. Reservations used to be empty files, and this branch tested
# for emptiness. They now carry a `RESERVED <token>` line -- because an empty
# file made every reservation byte-identical and no filesystem identity fixes
# that once inodes are recycled -- so testing emptiness alone would send every
# new reservation down the UNVERIFIABLE path and never start OmniRoute again.
$omniIsReservation = ($omniRaw -eq '') -or ($omniRaw -like 'RESERVED*')
# NOT A BRANCH. This was the first arm of the if/elseif/else below, which is the
# opposite of what its own comment claimed: saying "fall through and let the
# slot claim decide" while structurally guaranteeing that the else block --
# where --reserve-slot lives -- could never run. So a launcher that died
# between reserving and recording left a reservation that was recognised,
# announced, and then never reclaimed even past its stale window; OmniRoute
# stayed disabled until someone deleted the file by hand, and because this arm
# added nothing to $skipped the closing summary still reported every daemon
# started. A message is a message; it must not consume the dispatch.
#
# Two lines now print for this case, and that is deliberate: this one is
# the DIAGNOSIS (what was found on disk) and the slot claim below emits the
# OUTCOME (what was done about it). A fresh reservation still ends in
# "already claimed by another launcher", which is true -- a launcher is
# mid-flight -- and now also lands in $skipped, which is the half that was
# missing. A stale one is reclaimed and OmniRoute starts.
#
# A RESERVATION is a claim whose launcher never came back, not an unverifiable
# holder, and --reserve-slot below knows how to reclaim one past its window.
if ($omniVerdict -eq 'UNKNOWN' -and (Test-Path $omniPid) -and $omniIsReservation) {
    Write-Host "[FLOSS MCP] OmniRoute record is an incomplete reservation - handing it to the slot claim, which reclaims it only past its stale window"
}
if ($omniVerdict -eq 'UNKNOWN' -and (Test-Path $omniPid) -and -not $omniIsReservation) {
    Write-Host "[FLOSS MCP] OmniRoute record exists but identity is UNVERIFIABLE - not starting a duplicate. Delete $omniPid if you know it is stale."
    $skipped += "OmniRoute (:20128) - not started; existing record is unverifiable"
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
    # A FOREIGN verdict is PROOF the record is stale, and the record still
    # exists. --reserve-slot is O_CREAT|O_EXCL, so it would return OCCUPIED
    # against that dead record forever: OmniRoute would never start again, and
    # every later run would repeat the failure. Clear a record we have proven
    # stale before reserving. UNKNOWN is untouched -- it is handled above and
    # stays conservative, because an unverifiable holder may be alive.
    if ($omniVerdict -eq 'FOREIGN' -and $py) {
        # BY INSTANCE, through the same helper the Python paths use. Removing
        # the record by pathname here let two start scripts both read it as
        # FOREIGN: the first deleted it and reserved, the second then deleted
        # THAT reservation and reserved too, so both launched a server on one
        # port and the loser overwrote the winner's identity record. Losing this
        # race must cost nothing -- NOT_RECLAIMED simply means someone else got
        # there, and --reserve-slot below will report OCCUPIED.
        Push-Location $repoRoot
        $reclaimOut = & $py -m packages.mcp_daemon --reclaim-claim $omniPid 2>$null
        Pop-Location
        $reclaimTok = ($reclaimOut | Select-Object -Last 1)
        if ($reclaimTok) { $reclaimTok = $reclaimTok.ToString().Trim() }
        if ($reclaimTok -eq 'RECLAIMED') {
            Write-Host "[FLOSS MCP] OmniRoute record was stale (that PID is not ours) - cleared before reserving"
        } else {
            Write-Host "[FLOSS MCP] OmniRoute stale record was claimed by another launcher first - deferring to it"
        }
    } elseif ($omniVerdict -eq 'FOREIGN') {
        Write-Host "[FLOSS MCP] OmniRoute record is stale but no Python is available to clear it safely; leaving it in place"
        $skipped += "OmniRoute (:20128) - stale record left in place; set FLOSS_PYTHON"
    }
    $reserved = $false
    $omniReserveToken = ''
    if ($py) {
        Push-Location $repoRoot
        $slotOut = & $py -m packages.mcp_daemon --reserve-slot $omniPid 2>$null
        Pop-Location
        $slotTok = ($slotOut | Select-Object -Last 1)
        if ($slotTok) { $slotTok = $slotTok.ToString().Trim() }
        # `RESERVED <token>`, not `RESERVED`. The token is the proof that the
        # reservation --record-identity writes into is the one THIS launcher
        # made: a launcher suspended past the stale window has its reservation
        # legitimately reclaimed, and without presenting the token it would
        # wake up and record its PID over the winner's live claim. An exact
        # equality test here would also read every successful reservation as a
        # failure and never start OmniRoute again.
        $reserved = ($slotTok -eq 'RESERVED') -or ($slotTok -like 'RESERVED *')
        if ($slotTok -like 'RESERVED *') {
            $omniReserveToken = $slotTok.Substring('RESERVED '.Length).Trim()
        }
    }
    if (-not $reserved) {
        # NOT `return`: this is script scope, so returning here would also skip
        # the summary line at the end of the file. Only the launch is skipped.
        Write-Host "[FLOSS MCP] OmniRoute slot is already claimed by another launcher - not starting a duplicate"
        $skipped += "OmniRoute (:20128) - not started; slot claimed by another launcher"
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
    $recTok = ''
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
        $recOut = & $py -m packages.mcp_daemon --record-identity $omniPid $serverPid $omniReserveToken
        Pop-Location
        $recTok = ($recOut | Select-Object -Last 1)
        if ($recTok) { $recTok = $recTok.ToString().Trim() }
        if ($recTok -ne 'RECORDED') {
            # RELEASING A SLOT WHOSE SERVER IS STILL RUNNING IS THE WORSE BUG.
            #
            # The reservation is an EMPTY file, which every reader treats as an
            # in-progress claim and therefore as occupied, so leaving it behind
            # after a failed recording blocks every future start. But dropping
            # it while the server we just launched is alive is worse: that
            # server becomes untracked, and the next start launches a duplicate
            # onto a bound port. Stop the server first, and only release the
            # slot once nothing is listening under it.
            Write-Host "[FLOSS MCP] WARNING: could not record the OmniRoute identity ($recTok)"
            $gone = $false
            try {
                Stop-Process -Id $serverPid -Force -ErrorAction Stop
                $gone = $true
            } catch {
                if (-not (Get-Process -Id $serverPid -ErrorAction SilentlyContinue)) { $gone = $true }
            }
            if ($gone) {
                Write-Host "[FLOSS MCP] Stopped the unrecorded OmniRoute (PID $serverPid) and released the reservation"
                $skipped += "OmniRoute (:20128) - launched but could not be recorded, so it was stopped again"
                # BY TOKEN, NOT BY PATHNAME.
                #
                # The most common reason recording fails here is
                # STALE_RESERVATION -- which means another launcher now owns
                # the slot. Deleting the pathname would remove THAT launcher's
                # pid and identity files, leaving its server live and
                # untracked, and let a later start launch a duplicate. The
                # cleanup for losing a race must not destroy the winner.
                Release-OmniClaim $omniReserveToken
            } else {
                # Keep the reservation: an occupied-but-unverifiable slot blocks
                # the next start, which is the conservative failure. An operator
                # can clear it once they have dealt with the process.
                Write-Host "[FLOSS MCP] OmniRoute PID $serverPid is ALIVE and unrecorded; KEEPING $omniPid so a later start does not launch a duplicate. Stop PID $serverPid and delete that file once handled."
                $skipped += "OmniRoute PID $serverPid - running but UNRECORDED; stop it manually"
            }
        }
    } elseif ($reserved) {
        # Reserved the slot and then failed to launch: release it rather than
        # leaving an empty claim that blocks forever.
        Write-Host "[FLOSS MCP] OmniRoute did not start; releasing the reserved slot"
        $skipped += "OmniRoute (:20128) - launch failed"
        # Same ownership check as the branch above: our reservation may already
        # have been reclaimed by a launcher that went on to start a server.
        Release-OmniClaim $omniReserveToken
    }
    # RECORDED is the only outcome meaning a server is up AND trackable.
    # This printed whenever $proc was truthy -- including the branch above
    # that STOPS the unrecorded server, so the script announced 'Stopped the
    # unrecorded OmniRoute' and 'OmniRoute started' on consecutive lines.
    # Third instance in this file of claiming a state it did not achieve.
    if ($proc -and $recTok -eq 'RECORDED') {
        Write-Host "[FLOSS MCP] OmniRoute started (:20128, PID $serverPid)"
    } elseif ($proc) {
        Write-Host "[FLOSS MCP] OmniRoute was NOT left running and recorded; see above"
    }
}

# THE SUMMARY MUST DESCRIBE WHAT HAPPENED.
#
# Sibling of the same defect in stop_mcp_daemons.ps1: the branches above
# deliberately decline to launch -- an unverifiable record may be a live
# server, a claimed slot belongs to another launcher -- and this line then
# reported all three daemons up regardless. An operator reads that and assumes
# :20128 is served by this stack when startup specifically declined to
# establish it.
if ($skipped.Count -gt 0) {
    Write-Host "[FLOSS MCP] STARTUP INCOMPLETE - $($skipped.Count) item(s) not started:"
    foreach ($item in $skipped) {
        Write-Host "[FLOSS MCP]   $item"
    }
    Write-Host "[FLOSS MCP] Do not assume the items above are being served."
    exit 1
}

Write-Host "[FLOSS MCP] Daemons started (consensus :7331, ensemble :7332, omniroute :20128). PID guard prevents duplicates."
