# FLOSS/scripts/sweep_mcp_orphans.ps1 — periodic sweep of orphaned MCP processes.
#
# The stray-process problem: stdio-spawned MCP servers (node @agentmemory/mcp,
# januscope lens wrappers, python fallback servers) outlive the harness that
# spawned them. Windows doesn't reap orphans, none of the harnesses implement
# parent-pid watchdogs, and JanuScope wrappers keep polling upstream forever.
#
# What counts as "orphan": a node/python process whose command line matches an
# MCP-server signature (agentmemory-mcp bin, januscope cli, python -m packages.*)
# AND whose parent process is either gone (dead PID) or is a shell/PowerShell
# instance that has since exited.
#
# What we NEVER kill:
#   - the FLOSS HTTP daemons (protected by PID files under ~/.floss_agent/)
#   - OmniRoute (kept by an active parent)
#   - hermes gateway (identified by its own PID files under %LOCALAPPDATA%\hermes)
#   - anything whose parent is still alive (that's a live harness's child)
#
# Idempotent. Safe to run on a schedule (Task Scheduler, cron, or hand).
# Register: schtasks /Create /TN "FLOSS-MCP-Orphan-Sweep" /TR "powershell -WindowStyle Hidden -File C:\~shit\FLOSS\scripts\sweep_mcp_orphans.ps1" /SC MINUTE /MO 15 /RU "MSI\kalis" /RL LIMITED /F

param(
    [switch]$DryRun,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# Load protected PIDs from FLOSS daemon PID files
$flossAgent = "$env:USERPROFILE\.floss_agent"
$protectedPids = @()
foreach ($pidFile in @("consensus.pid", "reasoning_ensemble.pid")) {
    $p = Join-Path $flossAgent $pidFile
    if (Test-Path $p) {
        try {
            $val = [int]((Get-Content $p -Raw).Trim())
            if ($val -gt 0) { $protectedPids += $val }
        } catch { }
    }
}

# Also protect hermes gateway if a PID file exists
$hermesGwPid = "$env:LOCALAPPDATA\hermes\gateway.pid"
if (Test-Path $hermesGwPid) {
    try {
        $val = [int]((Get-Content $hermesGwPid -Raw).Trim())
        if ($val -gt 0) { $protectedPids += $val }
    } catch { }
}

# MCP-server command-line signatures we recognize
$mcpSignatures = @(
    'agentmemory-mcp\\bin\.mjs',
    '@agentmemory/mcp',
    'januscope[\\/](dist[\\/])?cli',
    'januscope@latest',
    '@modelcontextprotocol',
    '-m packages\.metacoordinator_mcp',
    '-m packages\.reasoning_ensemble',
    'spec-workflow-mcp',
    '@upstash/context7-mcp'
)
$sigRegex = ($mcpSignatures -join '|')

# Build lookup: pid -> parentPid, so we can check if parent is dead
$allProcs = Get-WmiObject Win32_Process | Select-Object ProcessId, ParentProcessId, Name, CommandLine
$livePids = @{}
foreach ($p in $allProcs) { $livePids[[int]$p.ProcessId] = $true }

$candidates = $allProcs | Where-Object {
    ($_.Name -eq 'node.exe' -or $_.Name -eq 'python.exe') -and
    $_.CommandLine -and
    ($_.CommandLine -match $sigRegex)
}

$killed = @()
$kept = @()
foreach ($proc in $candidates) {
    $procId = [int]$proc.ProcessId
    $ppid = [int]$proc.ParentProcessId
    $cmd = $proc.CommandLine.Substring(0, [Math]::Min(100, $proc.CommandLine.Length))

    if ($protectedPids -contains $procId) {
        $kept += "PROTECTED PID=$procId (daemon): $cmd"
        continue
    }
    if ($livePids.ContainsKey($ppid) -and $ppid -gt 4) {
        # parent still alive → this is a live harness's child, leave it
        $kept += "LIVE-PARENT PID=$procId parent=${ppid}: $cmd"
        continue
    }
    # Orphan (parent dead) — kill it
    if ($DryRun) {
        $killed += "WOULD-KILL PID=$procId parent=$ppid (dead): $cmd"
    } else {
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            $killed += "KILLED PID=$procId parent=$ppid (dead): $cmd"
        } catch {
            $killed += "FAIL-KILL PID=$procId ($($_.Exception.Message)): $cmd"
        }
    }
}

# Log summary (append-only, so scheduled runs leave a trail)
$logDir = "$flossAgent\sweep-log"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$logPath = Join-Path $logDir ("sweep-" + (Get-Date -Format "yyyy-MM-dd") + ".log")
$stamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
Add-Content -Path $logPath -Value "[$stamp] sweep: killed=$($killed.Count) kept=$($kept.Count) protected=$($protectedPids -join ',')"
foreach ($line in $killed) { Add-Content -Path $logPath -Value "[$stamp]   $line" }
if ($Verbose) {
    foreach ($line in $kept) { Add-Content -Path $logPath -Value "[$stamp]   $line" }
}

# Stdout summary (visible when run manually)
Write-Host "[sweep] killed: $($killed.Count) | kept: $($kept.Count) | protected daemons: $($protectedPids.Count)"
if ($killed.Count -gt 0 -and -not $DryRun) {
    Write-Host "  --- killed ---"
    foreach ($line in $killed) { Write-Host "  $line" }
}
if ($DryRun) {
    Write-Host "  --- DRY RUN (nothing killed) ---"
    foreach ($line in $killed) { Write-Host "  $line" }
}
