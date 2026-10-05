"""Real scratch room logs, exact PS helpers, and explicitly labelled manual-step models."""
from pathlib import Path
import copy, importlib.util, json, os, subprocess, sys, uuid

P=Path(__file__).resolve().parent
W=Path(json.loads((P/'extraction-r5.json').read_text())['workspace']).parent
work=W/'deployment-audit';work.mkdir(exist_ok=True)
os.environ.pop('PYTHONPATH',None)
os.environ.update(PYTHONDONTWRITEBYTECODE='1',FLOSS_AGENT_DIR=str(work/'agent'),FLOSS_AUDIT_DIR=str(work/'audit'),FLOSS_MCP_AUDIT_DIR=str(work/'audit'),COORDINATION_ROOM_ROOT=str(work/'room'),COORDINATION_ROOM_LOG=str(work/'room/events.jsonl'),COORDINATION_ROOM_BOARD=str(work/'room/BOARD.md'))
sys.path.insert(0,str(W/'fixtures-exact/proposal'))
from packages.coordination_room.room import CoordinationRoom
spec=importlib.util.spec_from_file_location('rollback_room',W/'fixtures-exact/rollback/packages/coordination_room/room.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
cases=[]; room_evidence=[]
marker='deploy-smoke-'+uuid.uuid4().hex
def make_room(name,rollback=False):
    root=work/name;root.mkdir(exist_ok=True)
    return (old.CoordinationRoom(root,root/'events.jsonl') if rollback else CoordinationRoom(root,root/'events.jsonl',root/'BOARD.md'))
def smoke_case(name,path,seq=2,agent='deploy-smoke',mark=marker,accept=True):
    cases.append(dict(name=name,action='smoke',log=str(path),seq=seq,agent=agent,marker=mark,accept=accept))

for stage in ['upgrade','rollback']:
    for wrong in [True,False]:
        shared=make_room(stage+('-wrong' if wrong else '-correct'),stage=='rollback')
        shadow=make_room(stage+('-shadow-wrong' if wrong else '-shadow-control'),stage=='rollback')
        for room in [shared,shadow]:room.broadcast('seed','predecessor')
        reply=(shadow if wrong else shared).broadcast('deploy-smoke',('rolled back to v0.1 ' if stage=='rollback' else '')+marker)
        shared.broadcast('peer','later peer with non-ASCII: café 中 😀 \u2028 \u2029 \u0085')
        name=stage+('/wrong-bus' if wrong else '/correct-with-peer')
        path=work/(stage+('-wrong' if wrong else '-correct'))/'events.jsonl'
        smoke_case(name,path,seq=reply['seq'],accept=not wrong)
        room_evidence.append(dict(case=name,reply=reply,shared_rows=shared.read(),shadow_rows=shadow.read(),shared_state=shared.state()))
        if stage=='upgrade':
            state=shared.state() if not wrong else shadow.state()
            cases.append(dict(name='step5/'+name,action='step5-policy',log=str(path),board=str(path.parent/'BOARD.md'),root=str(path.parent),settled=1,state=state,read=shared.read(since_seq=0,limit=1) if not wrong else shadow.read(since_seq=0,limit=1),accept=not wrong))
        else:
            cases.append(dict(name='rollback4/'+name,action='rollback4-policy',log=str(path),seq=reply['seq'],agent='deploy-smoke',marker=marker,settled=1,state=shared.state() if not wrong else shadow.state(),claims={},accept=not wrong))

row={'seq':2,'ts':'2026-10-04T00:00:00Z','type':'broadcast','agent_id':'deploy-smoke','text':marker}
seed={'seq':1,'ts':'2026-10-04T00:00:00Z','type':'broadcast','agent_id':'seed','text':'previous'}
def log_case(name,rows,accept=True,encoding='utf-8',seq=2,mark=marker):
    path=work/(name+'.jsonl')
    path.write_bytes(('\n'.join(json.dumps(r,ensure_ascii=False) for r in rows)+'\n').encode(encoding))
    smoke_case(name,path,seq=seq,mark=mark,accept=accept)
    return path

log_case('utf8-bom',[seed,row],encoding='utf-8-sig')
log_case('utf16-bom',[seed,row],encoding='utf-16')
log_case('unicode-smoke',[seed,{**row,'text':'café 😀 \u2028 \u2029 \u0085 '+marker+' \" \\ \n'}])
log_case('wildcards-in-text',[seed,{**row,'text':'[?*] '+marker+' [a-z]'}])
log_case('wrong-agent',[seed,{**row,'agent_id':'peer'}],False)
log_case('wrong-type',[seed,{**row,'type':'claim'}],False)
log_case('wrong-marker',[seed,{**row,'text':'unrelated'}],False)
log_case('marker-case-fold',[seed,{**row,'text':marker.upper()}],True)
log_case('reused-marker-wrong-seq',[{**row,'seq':1},{**row,'text':'different'}],False)
log_case('duplicate-seq',[seed,row,row],False)
log_case('missing-seq',[seed],False)
log_case('missing-file',[],False)
cases[-1]['log']=str(work/'never-created.jsonl')
log_case('max-int32',[seed,{**row,'seq':2147483647}],True,seq=2147483647)
log_case('above-int32',[seed,{**row,'seq':2147483648}],False,seq=2147483648)
# Check the range boundary with the real room append, not just a hand-built row.
highroot=work/'real-high-sequence';highroot.mkdir(exist_ok=True)
highlog=highroot/'events.jsonl'
highlog.write_text(json.dumps({**seed,'seq':2147483647})+'\n',encoding='utf-8')
highroom=CoordinationRoom(highroot,highlog,highroot/'BOARD.md')
highreply=highroom.broadcast('deploy-smoke',marker)
assert highreply['seq']==2147483648
room_evidence.append(dict(case='real-room-above-int32',reply=highreply,shared_rows=highroom.read(),shared_state=highroom.state()))
smoke_case('real-room-above-int32',highlog,seq=highreply['seq'],accept=False)
cases.append(dict(name='settled-above-int32-inherited',action='settled',log=str(highlog),accept=False))
# Deliberately unsupported inputs: generated markers never contain these.
log_case('non-generated-wildcard-marker',[seed,{**row,'text':'unrelated'}],True,mark='*')
log_case('non-generated-empty-marker',[seed,{**row,'text':'unrelated'}],True,mark='')
large=[{**seed,'seq':i,'text':'large-log peer '+('x'*80)} for i in range(1,20001)]
large[998]={**row,'seq':999}
log_case('large-log-20000',[*large],True,seq=999)
partial=work/'partial-trailing.jsonl';partial.write_text(json.dumps(seed)+'\n'+json.dumps(row)+'\n{"seq":3,',encoding='utf-8')
smoke_case('partial-trailing-refuses',partial,accept=False)

preview='[FLOSS MCP] WOULD_START packages.coordination_room.server'
for name,output,accept in [('exact',preview,True),('prefix',preview+'_other (wrong)',False),('wrong-case',preview.upper(),False),('two',preview+'\n'+preview,False),('none','no actions',False)]:
    cases.append(dict(name='preview/'+name,action='preview',output=output,marker='WOULD_START',expected='packages.coordination_room.server',accept=accept))
for name,target,accept in [('pid-exact','coordination_room.pid',True),('pid-suffix','coordination_room.pid.bak',False)]:
    cases.append(dict(name='preview/'+name,action='preview',output='WOULD_STOP '+target,marker='WOULD_STOP',expected='coordination_room.pid',accept=accept))
cases.append(dict(name='markers/1000',action='markers',accept=True))

good=next(c for c in cases if c['name']=='step5/upgrade/correct-with-peer')
for field,value in [('log','wrong-bus'),('root','wrong-root'),('board','wrong-board'),('last_seq',0)]:
    changed=copy.deepcopy(good);changed['name']='step5/wrong-'+field;changed['state'][field]=value;changed['accept']=False;cases.append(changed)
for field in ['seq','ts','type','agent_id']:
    changed=copy.deepcopy(good);changed['name']='step5/row-'+field;changed['read'][0][field]=999 if field=='seq' else 'mismatch';changed['accept']=False;cases.append(changed)
empty=make_room('empty')
cases.append(dict(name='step5/empty-log',action='step5-policy',log=str(work/'empty/events.jsonl'),root=str(work/'empty'),board=str(work/'empty/BOARD.md'),settled=0,state=empty.state(),read=[],accept=True))
goodrb=next(c for c in cases if c['name']=='rollback4/rollback/correct-with-peer')
for name in ['tail','claims']:
    changed=copy.deepcopy(goodrb);changed['name']='rollback4/wrong-'+name;changed['accept']=False
    if name=='tail': changed['state']['last_seq']=0
    else: changed['state']['claims']={'x':'someone'}
    cases.append(changed)

(P/'deployment-inputs.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
(P/'room-smoke-evidence.json').write_text(json.dumps(room_evidence,indent=2),encoding='utf-8')
shells=[r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',r'C:\apPs\PowerShell\7\pwsh.exe']
records=[]
for i,shell in enumerate(shells):
    output=P/f'deployment-shell-{i}.json'
    cmd=[shell,'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(P/'deployment-cases.ps1'),'-CaseFile',str(P/'deployment-inputs.json'),'-Helpers',str(P/'deploy_helpers.ps1'),'-ResultFile',str(output)]
    done=subprocess.run(cmd,capture_output=True,text=True,errors='replace',timeout=120)
    result=json.loads(output.read_text(encoding='utf-8-sig')) if output.exists() else None
    records.append(dict(command=cmd,rc=done.returncode,stdout=done.stdout,stderr=done.stderr,result=result))
(P/'deployment-results.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print(json.dumps([{'shell':r['result']['shell'] if r['result'] else None,'rc':r['rc'],'cases':len(r['result']['results']) if r['result'] else 0,'unexpected':[c['case'] for c in r['result']['results'] if not c['matched_expectation']] if r['result'] else r['stderr']} for r in records],indent=2))
