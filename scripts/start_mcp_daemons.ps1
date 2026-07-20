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
$omni = Get-Process -Name 'node' -ErrorAction SilentlyContinue | Where-Object { $_.Path -match 'omniroute' }
if (-not $omni) {
    Start-Process -WindowStyle Hidden "omniroute" "--no-open"
    Write-Host "[FLOSS MCP] OmniRoute started (:20128)"
} else {
    Write-Host "[FLOSS MCP] OmniRoute already running (PID $($omni.Id))"
}

Write-Host "[FLOSS MCP] Daemons started (consensus :7331, ensemble :7332, omniroute :20128). PID guard prevents duplicates."
