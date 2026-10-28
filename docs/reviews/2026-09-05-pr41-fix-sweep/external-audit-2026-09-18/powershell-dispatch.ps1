$auditScript = Join-Path $PSScriptRoot 'snapshot-303b1f9/scripts/start_mcp_daemons.ps1'
$auditTokens = $null
$auditErrors = $null
$auditAst = [System.Management.Automation.Language.Parser]::ParseFile($auditScript, [ref]$auditTokens, [ref]$auditErrors)
if ($auditErrors.Count) { throw ($auditErrors | Out-String) }
$auditDispatch = $auditAst.FindAll({ param($node)
    $node -is [System.Management.Automation.Language.IfStatementAst] -and
    $node.Clauses[0].Item1.Extent.Text -match '-not \$omniIsReservation'
}, $true) | Select-Object -First 1
if (-not $auditDispatch) { throw 'Dispatch AST not found' }
# Execute the actual dispatch conditions and refusal/OURS bodies. Substitute
# only the launch-containing else body, to make live daemon startup impossible.
$auditStart = $auditDispatch.Extent.StartOffset
$auditElseOffset = $auditDispatch.ElseClause.Extent.StartOffset - $auditStart
$auditCode = $auditDispatch.Extent.Text.Substring(0, $auditElseOffset) + '{ $script:auditOutcome = "SLOT" }'
$auditBlock = [scriptblock]::Create($auditCode)
function Test-Path { param($Path) return $script:auditPresent }
function Get-Content { param($Path, [switch]$Raw) return 'stub PID' }
function Write-Host { param($Object) }
$omniPid = 'test-only.pid'
$auditCount = 0
foreach ($omniVerdict in @('UNKNOWN', 'OURS', 'FOREIGN')) {
    foreach ($script:auditPresent in @($false, $true)) {
        foreach ($omniIsReservation in @($false, $true)) {
            $script:auditOutcome = 'OURS'
            $skipped = @()
            . $auditBlock
            if ($skipped.Count) { $script:auditOutcome = 'REFUSED' }
            $auditExpected = if ($omniVerdict -eq 'UNKNOWN' -and $script:auditPresent -and -not $omniIsReservation) { 'REFUSED' } elseif ($omniVerdict -eq 'OURS') { 'OURS' } else { 'SLOT' }
            if ($script:auditOutcome -ne $auditExpected) { throw "Mismatch: $omniVerdict/$script:auditPresent/$omniIsReservation" }
            Write-Output "$omniVerdict present=$script:auditPresent reservation=$omniIsReservation => $script:auditOutcome"
            $auditCount++
        }
    }
}
Write-Output "PASS $auditCount dispatch combinations; no process launched"
