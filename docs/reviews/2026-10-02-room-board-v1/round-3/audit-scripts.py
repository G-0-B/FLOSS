from pathlib import Path
import os,subprocess,json
ROOT=Path(__file__).resolve().parent
PACKET=Path(r'C:\~shit\FLOSS\docs\reviews\2026-10-02-room-board-v1\round-3')
shells=[r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',r'C:\apPs\PowerShell\7\pwsh.exe']
results=[];parses=[]
work=ROOT/'script-cases';work.mkdir(exist_ok=True)
for shell in shells:
 for stage in ['baseline','rollback','phase1','proposal']:
  for script in ['start_mcp_daemons.ps1','stop_mcp_daemons.ps1']:
   path=ROOT/'fixtures-exact'/stage/'scripts'/script
   cmd=[shell,'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(ROOT/'script-harness.ps1'),'-Script',str(path)]
   d=subprocess.run(cmd+['-ParseOnly'],capture_output=True)
   parses.append({'stage':stage,'script':script,'shell':shell,'bom':path.read_bytes()[:3].hex(),'stdout':d.stdout.decode(errors='replace'),'stderr':d.stderr.decode(errors='replace'),'rc':d.returncode})
   selections=['room','consensus,ensemble','omniroute']+(['bridge'] if stage=='proposal' else [])
   cases=[(s,v,dry) for s in selections for v in ['OURS','FOREIGN','UNKNOWN','RESERVED','ABSENT'] for dry in [True,False]] if stage in ['rollback','proposal'] else []
   cases+=[('DEFAULT','ABSENT',False)]
   for select,verdict,dry in cases:
    case=work/str(len(results));case.mkdir()
    for name,pid in [('consensus',4240),('reasoning_ensemble',4241),('coordination_room',4242),('a2a_room_bridge',4243),('omniroute',4244)]:
     if verdict!='ABSENT':
      (case/f'{name}.pid').write_text('RESERVED 123' if verdict=='RESERVED' else str(pid),encoding='ascii')
      (case/f'{name}.pid.identity').write_text('STANDIN',encoding='ascii')
    args=cmd+['-CaseDir',str(case),'-Verdict',verdict]
    if select=='DEFAULT': args+=['-NoArguments']
    else: args+=['-Selection',select]+(['-Preview'] if dry else [])
    d=subprocess.run(args,capture_output=True,timeout=20)
    trace=case/'effects.txt'
    row={'stage':stage,'script':script,'shell':shell,'selection':select,'verdict':verdict,'dry':dry,'rc':d.returncode,'stdout':d.stdout.decode(errors='replace'),'stderr':d.stderr.decode(errors='replace'),'effects':trace.read_text() if trace.exists() else ''}
    results.append(row)
 (PACKET/'script-audit.json').write_text(json.dumps({'parses':parses,'runs':results},indent=2),encoding='utf-8')
 print('finished',shell,'cases',len(results),flush=True)
print('parse errors',[(r['stage'],r['script'],json.loads(r['stdout'])['Errors']) for r in parses if json.loads(r['stdout'])['Errors']],flush=True)
