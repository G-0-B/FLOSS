# Deployment helpers for the coordination room. Dot-source, then call:
#
#   . C:\path\to\checkout\packages\coordination_room\deploy.ps1
#
# Every helper throws on a failed precondition, and $ErrorActionPreference is
# set to Stop, so a block of calls halts at the first failure. Nothing here
# starts, stops or posts by itself: each function does one checked thing.
#
# Set any of $log, $agent, $py, $roomUrl before dot-sourcing to override the
# defaults derived below. Tested by tests/test_deploy_helpers.py.

$ErrorActionPreference = 'Stop'

$deployCheckout = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $log) {
    # Same rule as scripts/start_mcp_daemons.ps1: a checkout under
    # FLOSS\.worktrees\<name> shares the workspace's log, three levels up.
    $intakeRoot = if ($deployCheckout -match '\\.worktrees\\') {
        Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $deployCheckout))
    } else {
        Split-Path -Parent $deployCheckout
    }
    $log = Join-Path $intakeRoot '.agent-surface\rooms\default\events.jsonl'
}
if (-not $agent) {
    $agent = if ($env:FLOSS_AGENT_DIR) { $env:FLOSS_AGENT_DIR } else { "$env:USERPROFILE\.floss_agent" }
}
if (-not $py) {
    $py = if ($env:FLOSS_PYTHON) { $env:FLOSS_PYTHON } else { (Get-Command python -ErrorAction Stop).Source }
}
if (-not $roomUrl) { $roomUrl = 'http://127.0.0.1:7334/mcp' }

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

function Assert-PinnedLog {
    # A start preview must show the room pinned to the shared log. Any other
    # path is a separate, empty bus.
    param([string]$Output)
    if ($Output -notmatch [regex]::Escape("coordination room log: $log ")) {
        throw "The start preview does not pin the room to $log. Stop here."
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

function Get-LogRows {
    # Every row of the shared log. Strict on purpose: the room skips a line it
    # cannot read and carries on, but a deployment must not. If this throws,
    # stop, copy the log somewhere safe, and look at it. Never edit it in place.
    # A log that does not exist yet is an empty log: a room that has never
    # been posted to has not created it.
    if (-not (Test-Path $log)) { return }
    $number = 0
    foreach ($line in (Get-Content $log -Encoding UTF8)) {
        $number++
        if (-not $line.Trim()) { continue }
        try { ConvertFrom-Json $line }
        catch { throw "Line $number of $log is not readable JSON. Stop here: copy the log aside and inspect it before going on." }
    }
}

function Get-SettledSeq {
    # The last seq in the shared log. Read it only after the previous owner has
    # stopped: before that, it can still append. Once a room is serving again,
    # other agents may append at any time, so this is a lower bound from then
    # on, never something to compare a later tail against.
    $rows = @(Get-LogRows)
    if ($rows.Count -eq 0) { return 0 }
    return [int]$rows[-1].seq
}

function Get-LogRow {
    # The one row of the shared log with this seq. Throws if it is missing or
    # if the seq appears more than once.
    param([int]$Seq)
    $rows = @(Get-LogRows | Where-Object { $_.seq -eq $Seq })
    if ($rows.Count -ne 1) { throw "seq $Seq appears $($rows.Count) times in $log. Stop here." }
    return $rows[0]
}

function Get-LogClaims {
    # The claims the log itself implies, as sorted "path=agent" strings.
    $held = [ordered]@{}
    foreach ($row in (Get-LogRows)) {
        if ($row.type -ceq 'claim') { $held[$row.path] = $row.agent_id }
        elseif ($row.type -ceq 'release') { $held.Remove($row.path) }
    }
    return @($held.Keys | Sort-Object | ForEach-Object { "$_=$($held[$_])" })
}

function Invoke-Room {
    # One room tool call through the room's own client, run from a checkout
    # that has it. Returns the parsed reply. Throws if the call fails or the
    # room answers ok:false.
    param([string]$Checkout, [string]$Tool, [hashtable]$Arguments = @{})
    $json = $Arguments | ConvertTo-Json -Compress -Depth 5
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $savedPath = $env:PYTHONPATH
    $errors = [IO.Path]::GetTempFileName()
    Push-Location $Checkout
    try {
        $env:PYTHONPATH = ''
        # stdout is the reply (one ASCII JSON line); stderr is kept apart so a
        # warning can never be parsed as the reply.
        $out = $json | & $py -m packages.coordination_room.client --url $roomUrl $Tool - 2> $errors | Out-String
        $code = $LASTEXITCODE
        $detail = Get-Content $errors -Raw
    } finally {
        $env:PYTHONPATH = $savedPath
        Pop-Location
        Remove-Item $errors -Force -ErrorAction SilentlyContinue
        $ErrorActionPreference = $previous
    }
    if ($code -ne 0) { throw "room call $Tool exited $code. Stop here. $out $detail" }
    return ($out.Trim() | ConvertFrom-Json)
}

function Assert-RoomState {
    # For a v0.2 room: it must name the shared log, the board beside it and the
    # expected root; be at or past the settled seq; and report a readable log.
    # "At or past", not "equal": other agents may already have posted.
    param($State, [string]$Root, [int]$MinSeq)
    $board = Join-Path (Split-Path $log) 'BOARD.md'
    $problems = @()
    if ("$($State.log)" -ne $log) { $problems += "log is '$($State.log)', expected '$log'" }
    if ("$($State.board)" -ne $board) { $problems += "board is '$($State.board)', expected '$board'" }
    if ([IO.Path]::GetFullPath("$($State.root)") -ne [IO.Path]::GetFullPath($Root)) {
        $problems += "root is '$($State.root)', expected '$Root'"
    }
    if ([int]$State.last_seq -lt $MinSeq) { $problems += "last_seq $($State.last_seq) is below the settled $MinSeq" }
    if ([int]$State.log_skipped_lines -ne 0) { $problems += "$($State.log_skipped_lines) unreadable line(s) in the log" }
    if ($problems.Count -gt 0) { throw "This is not the room to post to: $($problems -join '; '). Stop here." }
}

function Assert-V01State {
    # A v0.1 room cannot name its paths. What it can show: a seq at or past the
    # settled one, and the same claims the shared log implies.
    param($State, [int]$MinSeq)
    if ([int]$State.last_seq -lt $MinSeq) {
        throw "last_seq $($State.last_seq) is below the settled $MinSeq. Stop here."
    }
    $fromRoom = @($State.claims.PSObject.Properties | Sort-Object Name | ForEach-Object { "$($_.Name)=$($_.Value)" })
    $fromLog = @(Get-LogClaims)
    if (($fromRoom -join '|') -cne ($fromLog -join '|')) {
        throw "The room's claims ($($fromRoom -join ', ')) differ from the log's ($($fromLog -join ', ')). If another agent just claimed or released, run this again; if it persists, stop."
    }
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
    # Only a marker New-SmokeMarker made is accepted: an empty or hand-typed one
    # (say, from a fresh session where $marker is unset) would match too much.
    if ($Marker -cnotmatch '^deploy-smoke-[0-9a-f]{32}$') {
        throw "'$Marker' is not a marker from New-SmokeMarker. Stop here."
    }
    $row = Get-LogRow $Seq
    # Contains(): literal and case-sensitive. -like would read the text as a pattern.
    if ($row.type -cne 'broadcast' -or $row.agent_id -cne $Agent -or -not "$($row.text)".Contains($Marker)) {
        throw "seq $Seq in $log is not the smoke post by $Agent ($Marker). The room that answered is not writing the shared log. Stop here."
    }
}

function New-PinnedCheckout {
    # A detached checkout of one recorded commit, refused unless it really is
    # that commit. Used for the checkout that serves and for the rollback one,
    # so neither is a worktree somebody is still editing.
    param([string]$Repo, [string]$Commit, [string]$Path)
    if ($Commit -notmatch '^[0-9a-f]{40}$') {
        throw "A pinned checkout needs a full 40-character commit id, got '$Commit'."
    }
    if (Test-Path $Path) {
        throw "$Path already exists. Do not reuse it, and do not remove it without the operator's say-so."
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
    if ($head -ne $Commit) { throw "The checkout is at $head, not $Commit. Stop here." }
}
