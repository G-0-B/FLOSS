param([string]$CaseFile, [string]$Helpers, [string]$ResultFile)
. $Helpers
$cases = Get-Content -LiteralPath $CaseFile -Raw -Encoding UTF8 | ConvertFrom-Json
$results = @()
foreach ($case in $cases) {
    $log = $case.log
    $continued = $false
    $began = Get-Date
    $value = $null
    try {
        switch ($case.action) {
            'smoke' { Assert-SmokeEvent $case.seq $case.agent $case.marker }
            'row' { $value = Get-LogRow $case.seq }
            'preview' { Assert-OnlyAction $case.output $case.marker $case.expected }
            'settled' { $value = Get-SettledSeq }
            'markers' {
                $markers = @(1..1000 | ForEach-Object { New-SmokeMarker })
                if (@($markers | Sort-Object -Unique).Count -ne 1000) { throw 'Marker collision' }
                if (@($markers | Where-Object { $_ -cnotmatch '^deploy-smoke-[0-9a-f]{32}$' }).Count) { throw 'Unsafe marker alphabet' }
                $value = '1000 distinct markers, safe alphabet'
            }
            'step5-policy' {
                # Literal helpers plus an explicit model of plan 4144-4150's
                # manual MCP checks, not an extracted executable plan block.
                $state = $case.state
                if ($state.log -cne $case.log -or $state.board -cne $case.board -or $state.root -cne $case.root -or $state.last_seq -lt $case.settled) { throw 'Step 5 state precondition failed' }
                if ($case.settled -gt 0) {
                    $row = Get-LogRow $case.settled
                    if (@($case.read).Count -ne 1) { throw 'Step 5 requires one replay row' }
                    foreach ($field in @('seq','ts','type','agent_id')) {
                        if ($row.$field -cne $case.read[0].$field) { throw "Step 5 row mismatch: $field" }
                    }
                }
            }
            'rollback4-policy' {
                # Model of the manual state/claims precondition, plan 4237.
                if ($case.state.last_seq -lt $case.settled) { throw 'Rollback sequence precondition failed' }
                $actual = @($case.state.claims.PSObject.Properties | ForEach-Object { "$($_.Name)=$($_.Value)" } | Sort-Object)
                $expected = @($case.claims.PSObject.Properties | ForEach-Object { "$($_.Name)=$($_.Value)" } | Sort-Object)
                if (($actual -join "`n") -cne ($expected -join "`n")) { throw 'Rollback claims precondition failed' }
                Assert-SmokeEvent $case.seq $case.agent $case.marker
            }
            default { throw "Unknown audit action $($case.action)" }
        }
        $continued = $true
        $errorText = $null
    } catch { $errorText = $_.Exception.Message }
    $results += [pscustomobject]@{
        case=$case.name; action=$case.action; expected_accept=[bool]$case.accept;
        accepted=$continued; matched_expectation=($continued -eq [bool]$case.accept);
        reached_next_action=$continued; error=$errorText; value=$value;
        elapsed_ms=((Get-Date)-$began).TotalMilliseconds
    }
}
[pscustomobject]@{shell=$PSVersionTable.PSVersion.ToString(); results=$results} | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath $ResultFile -Encoding UTF8
if (@($results | Where-Object { -not $_.matched_expectation }).Count) { exit 1 }
