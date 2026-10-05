param([Parameter(Mandatory=$true)][string]$Launcher, [Parameter(Mandatory=$true)][string]$Plan)
# Inert trace: no actual process startup, inspection or termination.
$source=Get-Content -LiteralPath $Launcher -Raw
$tokens=$null;$parseErrors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$parseErrors)
if($parseErrors.Count){throw 'Launcher parse failure'}
$fn=$ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Start-Daemon'},$true)
if(-not $fn){throw 'Missing Start-Daemon'}
$fake='function Start-Daemon { param([string]$Interpreter,[string]$Module,[string]$Label,[string]$WorkDir); Write-Output ("WOULD_START " + $Module) | Out-Host; return [pscustomobject]@{ HasExited=$false } }'
$source=$source.Remove($fn.Extent.StartOffset,$fn.Extent.EndOffset-$fn.Extent.StartOffset).Insert($fn.Extent.StartOffset,$fake)
$stop=$source.IndexOf('# Start OmniRoute daemon')
if($stop -lt 0){throw 'Missing bounded trace marker'}
$source=$source.Substring(0,$stop)
$source=$source.Replace('$PSScriptRoot',"'"+(Split-Path -Parent $Launcher)+"'")
$env:FLOSS_PYTHON='C:\Python313\python.exe'
$env:FLOSS_AGENT_DIR=Join-Path $env:TEMP 'room-r2-inert-agent-path'
'R2-02 inert launcher trace; no real starts:'
& ([scriptblock]::Create($source))
$lines=Get-Content -LiteralPath $Plan
foreach($range in @(@(3042,3044),@(3050,3051))){
 $snippet=($lines[($range[0]-1)..($range[1]-1)] -join "`n")
 $errors=$null
 [System.Management.Automation.Language.Parser]::ParseInput($snippet,[ref]$null,[ref]$errors) | Out-Null
 '{0}-{1}: {2} parse errors' -f $range[0],$range[1],$errors.Count
}
$readSnippet=$lines[3041..3043] -join "`n"
$stopSnippet=$lines[3049]
function Get-Content {param($Path,[switch]$Raw) Write-Output ('READ_PID_PATH='+$Path) | Out-Host; return '4242'}
function Get-CimInstance {param($ClassName,$Filter) [pscustomobject]@{ProcessId=4242;CommandLine='python -m packages.coordination_room.server'}}
function Stop-Process {param($Id) Write-Output ('WOULD_STOP_PID='+$Id)}
'R2-03 CONFIGURED_AGENT_DIR='+$env:FLOSS_AGENT_DIR
& ([scriptblock]::Create($readSnippet+"`n"+$stopSnippet))
'No actual PID files or processes read or stopped.'
