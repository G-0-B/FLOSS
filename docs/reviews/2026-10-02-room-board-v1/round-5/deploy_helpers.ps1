$ErrorActionPreference = 'Stop'
$serve = 'C:\~shit\FLOSS\.worktrees\room-board-v1'      # checkout whose code should serve
$log   = 'C:\~shit\.agent-surface\rooms\default\events.jsonl'
$agent = if ($env:FLOSS_AGENT_DIR) { $env:FLOSS_AGENT_DIR } else { "$env:USERPROFILE\.floss_agent" }
$py    = 'C:\Python313\python.exe'

function Invoke-DaemonScript {
    # Runs a daemon script in a child Windows PowerShell, so the script's own
    # exit code is what gets tested, and throws on anything but 0. Returns the
    # script's output so the caller can check it too.
    param([string]$Checkout, [string]$Script, [string[]]$Arguments)
    $path = Join-Path $Checkout "scripts\$Script"
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'   # 5.1 turns redirected stderr into errors
    try {
        $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $path @Arguments 2>&1 | Out-String
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previous
    }
    Write-Host $out
    if ($code -ne 0) {
        throw "$Script $($Arguments -join ' ') exited $code. Stop here and read its output."
    }
    return $out
}

function Assert-OnlyAction {
    # A dry run's output must name exactly one action, and its target (the word
    # after the marker: a module or a PID file) must be exactly the expected
    # name. `...server_other` is not `...server`.
    param([string]$Output, [string]$Marker, [string]$Expected)
    $targets = @($Output -split "`r?`n" | ForEach-Object {
        if ($_ -cmatch "$Marker\s+(\S+)") { $Matches[1] }
    })
    if ($targets.Count -ne 1 -or $targets[0] -cne $Expected) {
        throw "Expected exactly one $Marker for $Expected, got: $($targets -join ' | ')"
    }
}

function Assert-PortFree {
    # A bind attempt, not a query: a failed or denied query must never read as
    # "free". Exit 0 means this process could bind it, so nothing holds it.
    param([int]$Port, [string]$PidFile)
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $py -c "import socket, sys; s = socket.socket(); s.bind(('127.0.0.1', int(sys.argv[1]))); s.close()" $Port
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previous
    }
    if ($code -ne 0) { throw "Port $Port is still bound, or could not be checked. Stop here." }
    if ($PidFile -and (Test-Path (Join-Path $agent $PidFile))) {
        throw "$PidFile is still present in $agent. Stop here."
    }
}

function Get-SettledSeq {
    # The last seq in the shared log. Read it only after the previous owner has
    # stopped: before that, it can still append. Once a room is serving again,
    # other agents may append at any time, so this is a lower bound from then
    # on, never something to compare a later tail against.
    $last = Get-Content $log -Tail 1 -Encoding UTF8
    if (-not $last) { return 0 }
    return [int](ConvertFrom-Json $last).seq
}

function Get-LogRow {
    # The one row of the shared log with this seq. Throws if it is missing or
    # if the seq appears more than once.
    param([int]$Seq)
    $rows = @(Get-Content $log -Encoding UTF8 |
        Where-Object { $_.Trim() } |
        ForEach-Object { ConvertFrom-Json $_ } |
        Where-Object { $_.seq -eq $Seq })
    if ($rows.Count -ne 1) { throw "seq $Seq appears $($rows.Count) times in $log. Stop here." }
    return $rows[0]
}

function New-SmokeMarker {
    # A text no other post will contain.
    return "deploy-smoke-$([guid]::NewGuid().ToString('N'))"
}

function Assert-SmokeEvent {
    # Proves one specific post reached the shared log: the row with the seq the
    # room returned must be a broadcast by this agent carrying this marker.
    # Counting the tail cannot prove that: another agent's post moves the tail
    # too. Rows other agents add before or after this one are fine.
    param([int]$Seq, [string]$Agent, [string]$Marker)
    $row = Get-LogRow $Seq
    if ($row.type -cne 'broadcast' -or $row.agent_id -cne $Agent -or "$($row.text)" -notlike "*$Marker*") {
        throw "seq $Seq in $log is not the smoke post by $Agent ($Marker). The room that answered is not writing the shared log. Stop here."
    }
}

function Assert-PinnedLog {
    # A start preview must show the room pinned to the shared log. Any other
    # path is a separate, empty bus.
    param([string]$Output)
    if ($Output -notmatch [regex]::Escape("coordination room log: $log ")) {
        throw "The start preview does not pin the room to $log. Stop here."
    }
}

function New-RollbackCheckout {
    # A detached checkout of the recorded rollback commit, refused unless it
    # really is that commit.
    param([string]$Repo, [string]$Commit, [string]$Path)
    if ($Commit -notmatch '^[0-9a-f]{40}$') {
        throw "ROLLBACK_COMMIT must be a full 40-character commit id, got '$Commit'."
    }
    if (Test-Path $Path) {
        throw "$Path already exists. Inspect it or remove it deliberately; do not reuse it."
    }
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        git -C $Repo worktree add --detach $Path $Commit
        $code = $LASTEXITCODE
        $head = if ($code -eq 0) { "$(git -C $Path rev-parse HEAD)".Trim() } else { '' }
    } finally {
        $ErrorActionPreference = $previous
    }
    if ($code -ne 0) { throw "git worktree add exited $code. Stop here." }
    if ($head -ne $Commit) { throw "The rollback checkout is at $head, not $Commit. Stop here." }
}
