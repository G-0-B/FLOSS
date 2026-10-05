param([Parameter(ValueFromRemainingArguments=$true)][string[]]$PythonArgs)
$env:PYTHONPATH=''
$env:PYTHONDONTWRITEBYTECODE='1'
$env:FLOSS_AGENT_DIR=Join-Path $PSScriptRoot 'runtime\agent'
$env:FLOSS_MCP_AUDIT_DIR=Join-Path $PSScriptRoot 'runtime\audit'
$env:FLOSS_AUDIT_DIR=$env:FLOSS_MCP_AUDIT_DIR
$env:COORDINATION_ROOM_ROOT=Join-Path $PSScriptRoot 'runtime\room'
$env:COORDINATION_ROOM_LOG=Join-Path $env:COORDINATION_ROOM_ROOT 'events.jsonl'
$env:COORDINATION_ROOM_BOARD=Join-Path $env:COORDINATION_ROOM_ROOT 'BOARD.md'
$env:TEMP=Join-Path $PSScriptRoot 'tmp'
$env:TMP=$env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
$python=Join-Path $PSScriptRoot 'review-venv\Scripts\python.exe'
if(-not(Test-Path $python)){$python='C:\Python313\python.exe'}
& $python @PythonArgs
exit $LASTEXITCODE
