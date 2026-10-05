param([string]$Root)
$rows=@()
foreach($stage in 'baseline','phase1','proposal'){
 foreach($name in 'start_mcp_daemons.ps1','stop_mcp_daemons.ps1'){
  $p=Join-Path (Join-Path (Join-Path $Root $stage) 'scripts') $name
  $bytes=[IO.File]::ReadAllBytes($p)
  foreach($encoding in 'utf-8','windows-1252'){
   $e=$null
   $text=[Text.Encoding]::GetEncoding($encoding).GetString($bytes)
   [System.Management.Automation.Language.Parser]::ParseInput($text,[ref]$null,[ref]$e)|Out-Null
   $rows+= [pscustomobject]@{stage=$stage;file=$name;decode=$encoding;errors=@($e|ForEach-Object{[pscustomobject]@{line=$_.Extent.StartLineNumber;message=$_.Message}})}
  }
 }
}
$rows|ConvertTo-Json -Depth 5
