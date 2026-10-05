from pathlib import Path
import subprocess,json,os,time
ROOT=Path(__file__).resolve().parent
PACKET=Path(r'C:\~shit\FLOSS\docs\reviews\2026-10-02-room-board-v1\round-3')
lines=(PACKET/'plan-revision-3.md').read_text(encoding='utf-8').split('\n')
work=ROOT/('deployment-cases-'+str(time.time_ns()));work.mkdir()
serve=work/'serving';serve.mkdir();(serve/'scripts').mkdir()
rollback=work/'rollback';rollback.mkdir();(rollback/'scripts').mkdir()
# No runtime code: these scripts can only emit the fact that they were reached.
(rollback/'scripts'/'start_mcp_daemons.ps1').write_text("param([string]$Only,[switch]$DryRun)\nWrite-Output \"STALE_ROLLBACK_START_REACHED only=$Only dry=$DryRun\"\n",encoding='ascii')
(serve/'scripts'/'stop_mcp_daemons.ps1').write_text("param([string]$Only,[switch]$DryRun)\nif($Only -eq 'bridge'){Write-Output 'SHUTDOWN INCOMPLETE bridge identity UNVERIFIABLE';exit 1}\nWrite-Output 'ROOM_STOP_REACHED'\n",encoding='ascii')
rollback_block='\n'.join(lines[3843:3846]).replace('C:\\~shit\\FLOSS\\.worktrees\\room-rollback',str(rollback)).replace('C:\\~shit\\FLOSS',str(work)).replace('<ROLLBACK_COMMIT>','4aab13e30f3c2960da787b47c90926256b4b5b73')
# A native command failure has the same control flow as failed git worktree add;
# no Git operation or worktree is created, even in the fixture.
prefix="function git { & $env:ComSpec /d /c 'exit 128'; Write-Host 'GIT_WORKTREE_ADD_FAILED_128' }\n"
(work/'failed-checkout.ps1').write_text(prefix+rollback_block,encoding='ascii')
(work/'failed-bridge-stop.ps1').write_text("$serve='"+str(serve)+"'\n& \"$serve\\scripts\\stop_mcp_daemons.ps1\" -Only bridge\n& \"$serve\\scripts\\stop_mcp_daemons.ps1\" -Only room\n",encoding='ascii')
port_block='\n'.join(lines[3796:3798])
(work/'failed-port-query.ps1').write_text("$agent='"+str(work)+"'\nfunction Get-NetTCPConnection { [CmdletBinding()]param($LocalPort,$State);Write-Error 'simulated access denied' }\n"+port_block+"\nWrite-Output 'NEXT_STEP_REACHED'\n",encoding='ascii')
archive=work/'archive';archive.mkdir();(archive/'BOARD.md').write_bytes(b'PRESERVE BOARD')
archive_block='\n'.join(lines[3836:3838])
(work/'archive-board.ps1').write_text("$log='"+str(archive/'events.jsonl')+"'\n"+archive_block+"\nGet-ChildItem -LiteralPath $dir -Filter 'BOARD.superseded-*.md' | ForEach-Object { $_.Name; Get-Content -LiteralPath $_.FullName }\n",encoding='ascii')
results=[]
for shell in [r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',r'C:\apPs\PowerShell\7\pwsh.exe']:
 for name in ['failed-checkout','failed-bridge-stop','failed-port-query']:
  done=subprocess.run([shell,'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(work/(name+'.ps1'))],capture_output=True,text=True)
  results.append({'case':name,'shell':shell,'rc':done.returncode,'stdout':done.stdout,'stderr':done.stderr})
 done=subprocess.run([shell,'-NoProfile','-NonInteractive','-Command','(Get-Command env).Source'],capture_output=True,text=True)
 results.append({'case':'env-resolution','shell':shell,'rc':done.returncode,'stdout':done.stdout,'stderr':done.stderr})
done=subprocess.run([shell,'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(work/'archive-board.ps1')],capture_output=True,text=True)
results.append({'case':'archive-board','shell':shell,'rc':done.returncode,'stdout':done.stdout,'stderr':done.stderr})
print(json.dumps(results,indent=2))
(PACKET/'deployment-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
