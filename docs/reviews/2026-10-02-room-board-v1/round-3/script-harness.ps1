param([string]$Script,[string]$CaseDir,[string]$Selection='room',[string]$Verdict='UNKNOWN',[switch]$Preview,[switch]$NoArguments,[switch]$ParseOnly)
$ErrorActionPreference='Stop'
if($ParseOnly){
  $err=$null
  [System.Management.Automation.Language.Parser]::ParseFile($Script,[ref]$null,[ref]$err) | Out-Null
  [pscustomobject]@{Shell=$PSVersionTable.PSVersion.ToString();DefaultEncoding=[System.Text.Encoding]::Default.WebName;Errors=@($err|ForEach-Object{[pscustomobject]@{Line=$_.Extent.StartLineNumber;Message=$_.Message}})} | ConvertTo-Json -Depth 5
  exit 0
}
$env:FLOSS_AGENT_DIR=$CaseDir
$env:FLOSS_AUDIT_DIR=Join-Path $CaseDir 'audit'
$env:COORDINATION_ROOM_ROOT=$CaseDir
$env:COORDINATION_ROOM_LOG=Join-Path $CaseDir 'events.jsonl'
$env:COORDINATION_ROOM_BOARD=Join-Path $CaseDir 'BOARD.md'
$env:PYTHONPATH=''
$env:PYTHONDONTWRITEBYTECODE='1'
$env:FLOSS_PYTHON=Join-Path $PSScriptRoot 'interpreter-standin.ps1'
$env:REVIEW_VERDICT=$Verdict
$env:REVIEW_TRACE=Join-Path $CaseDir 'effects.txt'
function global:Start-Process {
  param($WindowStyle,[switch]$PassThru,$WorkingDirectory,$FilePath,$ArgumentList)
  [IO.File]::AppendAllText($env:REVIEW_TRACE,"LAUNCH $FilePath $ArgumentList`n")
  $p=[pscustomobject]@{Id=987654;HasExited=$false;ExitCode=0}
  $p|Add-Member -MemberType ScriptMethod -Name Refresh -Value {};$p
}
function global:Stop-Process {
  param($Id,[switch]$Force,$ErrorAction)
  [IO.File]::AppendAllText($env:REVIEW_TRACE,"KILL $Id`n")
}
function global:Remove-Item {
  param($Path,[switch]$Force,$ErrorAction)
  [IO.File]::AppendAllText($env:REVIEW_TRACE,"REMOVE $Path`n")
}
function global:Get-Process { param($Id,$ErrorAction);return $null }
function global:Get-CimInstance { param($ClassName,$Filter,$ErrorAction);return @() }
function global:Start-Sleep { param($Milliseconds) }
function global:Get-Command {
  param($Name,$ErrorAction)
  if($Name -eq 'omniroute'){return $null}
  Microsoft.PowerShell.Core\Get-Command $Name -ErrorAction SilentlyContinue
}
$ErrorActionPreference='Continue'
if($NoArguments){ & $Script } elseif($Preview) { & $Script -Only $Selection.Split(',') -DryRun } else { & $Script -Only $Selection.Split(',') }
