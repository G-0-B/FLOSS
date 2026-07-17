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

# OmniRoute daemon (enabled in Stage 4 once configured):
# Start-Process -WindowStyle Hidden "omniroute" "--no-open"

Write-Host "[FLOSS MCP] Daemons started (consensus :7331, ensemble :7332). PID guard prevents duplicates."
