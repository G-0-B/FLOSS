"""Counterexamples use only scratch logs and inert deployment code."""
from pathlib import Path
import contextlib, io, json, os, sys, subprocess, tempfile, importlib.util

P=Path(__file__).resolve().parent
fix=Path(json.loads((P/'extraction-r4.json').read_text())['workspace'])
work=Path(tempfile.mkdtemp(prefix='adversarial-r4-',dir=fix.parent))
sys.path.insert(0,str(fix/'proposal'))
from packages.coordination_room.room import CoordinationRoom
from packages.a2a_mesh.room_bridge import parse_command
spec=importlib.util.spec_from_file_location('rollback_room',fix/'rollback/packages/coordination_room/room.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
results={}

def room(name, rollback=False):
    p=work/name;p.mkdir(exist_ok=True)
    return p,(old.CoordinationRoom(p,p/'events.jsonl') if rollback else CoordinationRoom(p,p/'events.jsonl',p/'BOARD.md'))

# Every room here is the sole writer of its own file. No PID/HTTP control.
shared,a=room('shared',True);shadow,b=room('shadow',True)
a.broadcast('previous','seed');b.broadcast('previous','seed')
settled=a.state()['last_seq']
wrong_reply=b.broadcast('operator','rolled back to v0.1; probe R4')
a.broadcast('other-agent','unrelated shared-bus traffic')
lines=(P/'plan-revision-4.md').read_text(encoding='utf-8').split('\n')
check=lines[4099]
script=work/'verify-tail.ps1'
script.write_text("param([string]$SharedLog,[int]$Seq)\n. '"+str(P/'deploy_helpers.ps1')+"'\n$log=$SharedLog\n$settled=$Seq\n"+check+"\nWrite-Output 'ROLLBACK_CHECK_PASSED'\n",encoding='utf-8')
shells=[r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',r'C:\apPs\PowerShell\7\pwsh.exe']
cases=[]
for shell in shells:
    d=subprocess.run([shell,'-NoProfile','-NonInteractive','-File',str(script),str(shared/'events.jsonl'),str(settled)],capture_output=True,text=True,errors='replace')
    cases.append({'shell':shell,'rc':d.returncode,'stdout':d.stdout,'stderr':d.stderr})
results['wrong-bus-accepted']={'settled':settled,'probe_reply':wrong_reply,'shared_rows':a.read(),'shadow_rows':b.read(),'checks':cases}

correct,c=room('correct-with-peer',True);c.broadcast('previous','seed');settled=c.state()['last_seq']
reply=c.broadcast('operator','rolled back to v0.1; correct probe')
c.broadcast('other-agent','after correct probe')
cases=[]
for shell in shells:
    d=subprocess.run([shell,'-NoProfile','-NonInteractive','-File',str(script),str(correct/'events.jsonl'),str(settled)],capture_output=True,text=True,errors='replace')
    cases.append({'shell':shell,'rc':d.returncode,'stdout':d.stdout,'stderr':d.stderr})
results['correct-bus-rejected']={'settled':settled,'probe_reply':reply,'rows':c.read(),'checks':cases}

# New recheck must preserve the log after parent-directory retargeting.
p=work/'parent-rebind';p.mkdir();real=p/'real';real.mkdir();alias=p/'alias';alias.mkdir()
r=CoordinationRoom(p,real/'events.jsonl',alias/'events.jsonl');r.broadcast('a','seed')
alias.rename(p/'alias.preserved')
import _winapi
_winapi.CreateJunction(str(real),str(alias))
err=io.StringIO()
with contextlib.redirect_stderr(err): reply=r.broadcast('a','after-rebind')
results['parent-rebind-refused']={'reply':reply,'rows':r.read(),'stderr':err.getvalue()}

# Parse JSON numerics without reinterpretation of the selected parent thread.
parser=[]
for body in ['{"op":"post","text":"reply","reply_to":1.9}', '{"op":"post","text":"reply","reply_to":true}', '{"op":"post","text":"reply","reply_to":1e999}']:
    try:
        cmd=parse_command(body)
        result={'reply_to':cmd.reply_to,'exception':None}
    except Exception as e:
        result={'exception':type(e).__name__,'message':str(e)}
    parser.append({'input':body,**result})
results['parser-numeric-boundary']=parser
(P/'adversarial-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
