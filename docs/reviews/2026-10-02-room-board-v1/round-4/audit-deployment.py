"""Extract exact helpers and exercise them only against scratch/inert targets."""
from pathlib import Path
import json, os, subprocess

P=Path(__file__).resolve().parent
root=Path(json.loads((P/'extraction-r4.json').read_text())['workspace']).parent
work=root/'deployment';work.mkdir(exist_ok=True)
lines=(P/'plan-revision-4.md').read_text(encoding='utf-8').split('\n')
(work/'deploy_helpers.ps1').write_text('\n'.join(lines[3881:3974])+'\n',encoding='utf-8')
(P/'deploy_helpers.ps1').write_bytes((work/'deploy_helpers.ps1').read_bytes())
# Author's test is a control; point it at the exact helper text extracted above.
(work/'deploy_harness.ps1').write_bytes((P.parent/'round-3/author-r4-green/deploy_harness.ps1').read_bytes())
cases={
'missing-interpreter': '''
$py = Join-Path $Work 'absent-python.exe'
$global:LASTEXITCODE = 0
try { Assert-PortFree 19994 'none.pid'; Write-Output 'PORT_CHECK_PASSED' }
catch { Write-Output ('PORT_CHECK_REFUSED: ' + $_.Exception.Message) }
''',
'missing-shell': '''
$env:PATH = $Work
$global:LASTEXITCODE = 0
try { Invoke-DaemonScript $Work 'absent.ps1' @('-Only','room') | Out-Null; Write-Output 'SCRIPT_CHECK_PASSED' }
catch { Write-Output ('SCRIPT_CHECK_REFUSED: ' + $_.Exception.Message) }
''',
'tail-shape': '''
foreach ($content in @('{"seq": 8}', '{"seq": 8}' + "`n`n", '{"other": true}', '{"seq": 2147483648}')) {
    [IO.File]::WriteAllText($log,$content)
    try { Write-Output ("TAIL_VALUE=" + (Get-SettledSeq)) }
    catch { Write-Output ('TAIL_REFUSED: ' + $_.Exception.Message) }
}
''',
'preview-prefix': '''
try { Assert-OnlyAction 'WOULD_START packages.coordination_room.server_other (wrong)' 'WOULD_START' 'packages.coordination_room.server'; Write-Output 'WRONG_MODULE_PASSED' }
catch { Write-Output ('WRONG_MODULE_REFUSED: ' + $_.Exception.Message) }
'''
}
shells=[r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',r'C:\apPs\PowerShell\7\pwsh.exe']
results=[]
for i,shell in enumerate(shells):
    control=work/f'control-{i}';control.mkdir(exist_ok=True)
    cmd=[shell,'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(work/'deploy_harness.ps1'),'-Work',str(control)]
    d=subprocess.run(cmd,capture_output=True,text=True,errors='replace',timeout=90)
    results.append(dict(case='author-controls',command=cmd,rc=d.returncode,stdout=d.stdout,stderr=d.stderr))
    for name,body in cases.items():
        target=work/f'{name}-{i}';target.mkdir(exist_ok=True)
        code="param([string]$Work)\n. (Join-Path $PSScriptRoot 'deploy_helpers.ps1')\n$agent=$Work\n$log=Join-Path $Work 'events.jsonl'\n"+body
        script=work/(name+'.ps1');script.write_text(code,encoding='utf-8')
        cmd=[shell,'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(script),'-Work',str(target)]
        d=subprocess.run(cmd,capture_output=True,text=True,errors='replace',timeout=30)
        results.append(dict(case=name,command=cmd,rc=d.returncode,stdout=d.stdout,stderr=d.stderr))
(P/'deployment-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
for r in results: print(r['case'],Path(r['command'][0]).name,r['rc'],r['stdout'][-1800:])
