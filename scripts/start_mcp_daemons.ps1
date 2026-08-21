# FLOSS/scripts/start_mcp_daemons.ps1 — start OmniRoute + both MCP daemons if not already up.
# Idempotent: PID guard in mcp_daemon.py makes re-runs safe (second launch self-exits).
# Register as a Scheduled Task:
#   schtasks /Create /TN "FLOSS-MCP-Daemons" /TR "powershell -WindowStyle Hidden -File C:\~shit\FLOSS\scripts\start_mcp_daemons.ps1" /SC ONLOGON /RU "MSI\kalis" /RL LIMITED /F

$py = "C:\Python313\python.exe"
$env:PYTHONPATH = "C:/~shit/FLOSS"
$workspace = "C:\~shit\FLOSS"

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
$omni = Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
    Where-Object { $_.CommandLine -match 'omniroute' }
if (-not $omni) {
    Start-Process -WindowStyle Hidden "omniroute" "--no-open"
    Write-Host "[FLOSS MCP] OmniRoute started (:20128)"
} else {
    Write-Host "[FLOSS MCP] OmniRoute already running (PID $($omni.Id))"
}

Write-Host "[FLOSS MCP] Daemons started (consensus :7331, ensemble :7332, omniroute :20128). PID guard prevents duplicates."
