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
if ($omniVerdict -eq 'OURS') {
    Write-Host "[FLOSS MCP] OmniRoute already running (recorded PID $(Get-Content $omniPid -Raw))"
} else {
    $proc = Start-Process -WindowStyle Hidden -PassThru 'omniroute' '--no-open'
    if ($proc -and $py) {
        Push-Location $repoRoot
        & $py -m packages.mcp_daemon --record-identity $omniPid $($proc.Id) | Out-Null
        Pop-Location
    }
    Write-Host "[FLOSS MCP] OmniRoute started (:20128, PID $($proc.Id))"
}

Write-Host "[FLOSS MCP] Daemons started (consensus :7331, ensemble :7332, omniroute :20128). PID guard prevents duplicates."
