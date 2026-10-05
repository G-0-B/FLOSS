from pathlib import Path
import hashlib, json, subprocess, zipfile, shutil

ROOT=Path(__file__).resolve().parent/'fixtures-exact'
ROOT.mkdir(exist_ok=True)
PACKET=Path(r'C:\~shit\FLOSS\docs\reviews\2026-10-02-room-board-v1\round-3')
REPO=Path(r'C:\~shit\FLOSS')
BASE='4aab13e30f3c2960da787b47c90926256b4b5b73'
A2A='225287c2ed310158a3f699688447db2964e425b2'
PLAN=PACKET/'plan-revision-3.md'
SHA='7d25eee2bc44286a141419aa7058978bd9fb6ac7fd27bb33dfb712b2bd02af73'
assert hashlib.sha256(PLAN.read_bytes()).hexdigest()==SHA
lines=PLAN.read_text(encoding='utf-8').split('\n')
def git(*args):
    return subprocess.check_output(['git','-c','safe.directory=C:/~shit/FLOSS','-C',str(REPO),*args])
def body(a,b):
    return '\n'.join(lines[a-1:b])+'\n'
ops=[]
baseline=ROOT/'baseline'
proposal=ROOT/'proposal'
assert not baseline.exists() and not proposal.exists()
archive=ROOT/'base.zip'
archive.write_bytes(git('archive','--format=zip',BASE))
with zipfile.ZipFile(archive) as z:
    z.extractall(baseline)
shutil.copytree(baseline,proposal)
def put(path,a,b):
    p=proposal/path;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(body(a,b).encode('utf-8'))
    ops.append({'action':'body','path':path,'lines':[a,b]})
def replace(path,a,b,c,d):
    p=proposal/path
    raw=p.read_bytes()
    newline='\n'
    old=body(a,b).rstrip('\n').encode('utf-8')
    if old not in raw:
        newline='\r\n';old=old.replace(b'\n',b'\r\n')
    new=body(c,d).rstrip('\n').replace('\n',newline).encode('utf-8')
    assert raw.count(old)==1,(path,a,raw.count(old))
    p.write_bytes(raw.replace(old,new))
    ops.append({'action':'replace','path':path,'old':[a,b],'new':[c,d]})
def pairs(path,lo,hi):
    # Every numbered Edit in this section contains exactly two simple fences.
    import re
    section='\n'.join(lines[lo-1:hi])
    matches=list(re.finditer(r'^```(?:powershell|python)\n(.*?)^```$',section,re.M|re.S))
    assert len(matches)%2==0
    for first,second in zip(matches[::2],matches[1::2]):
        a=lo+section[:first.start(1)].count('\n');b=a+first.group(1).count('\n')-1
        c=lo+section[:second.start(1)].count('\n');d=c+second.group(1).count('\n')-1
        replace(path,a,b,c,d)
put('docs/specs/coordination-room.spec.md',212,302)
put('docs/specs/coordination-room.schema.json',308,368)
replace('docs/specs/spec-registry.json',374,374,380,380)
put('scripts/tests/test_daemon_scope.py',426,576)
pairs('scripts/start_mcp_daemons.ps1',589,728)
pairs('scripts/stop_mcp_daemons.ps1',732,813)
# Rollback content checkpoint: no commit/branch mutation required.
rollback=ROOT/'rollback'
shutil.copytree(proposal,rollback)
for path,a,b in [
 ('packages/coordination_room/tests/test_evidence.py',858,973),
 ('packages/coordination_room/evidence.py',987,1072),
 ('packages/coordination_room/tests/test_board.py',1108,1294),
 ('packages/coordination_room/board.py',1308,1473),
 ('packages/coordination_room/tests/test_message_board.py',1511,1766),
 ('packages/coordination_room/tests/test_gateway_board.py',1770,1858),
 ('packages/coordination_room/tests/test_schema.py',1862,1941),
 ('packages/coordination_room/room.py',1955,2158),
 ('packages/coordination_room/gateway.py',2164,2253),
 ('packages/coordination_room/tests/test_server_tools.py',2305,2423),
 ('packages/coordination_room/tests/test_server_http.py',2427,2535),
 ('packages/coordination_room/server.py',2549,2734),
 ('packages/coordination_room/README.md',2742,2753),
]: put(path,a,b)
p=proposal/'requirements-ci.txt';raw=p.read_bytes();assert raw.count(b'\nmcp\n')==1;p.write_bytes(raw.replace(b'\nmcp\n',b'\nmcp>=1.27\n'))
ops.append({'action':'replace-line','path':'requirements-ci.txt','old':'mcp','new':'mcp>=1.27'})
for a,b,c,d in [(2761,2765,2771,2777),(2783,2783,2789,2789),(2795,2795,2801,2801)]:
    replace('docs/agent-memory/project/coordination-room-v0.md',a,b,c,d)
phase1=ROOT/'phase1'
shutil.copytree(proposal,phase1)
# Task 7 imports the A2A package and its two exact documents from the pinned branch.
for name in git('ls-tree','-r','--name-only',A2A,'--','packages/a2a_mesh','docs/research/2026-08-29-a2a-harness-mesh-research.md','docs/superpowers/plans/2026-08-29-a2a-harness-mesh.md').decode().splitlines():
    p=proposal/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(git('show',f'{A2A}:{name}'))
    ops.append({'action':'git-show','path':name,'commit':A2A})
p=proposal/'requirements-ci.txt'
base_reqs=git('show',f'{BASE}:requirements-ci.txt')
a2a_reqs=git('show',f'{A2A}:requirements-ci.txt')
assert a2a_reqs.startswith(base_reqs)
p.write_bytes(p.read_bytes()+a2a_reqs[len(base_reqs):])
ops.append({'action':'merge-append','path':'requirements-ci.txt','commit':A2A})
for path,a,b in [
 ('packages/a2a_mesh/tests/test_room_bridge_parse.py',2886,2974),
 ('packages/a2a_mesh/tests/test_room_bridge_pair.py',2978,3098),
 ('packages/a2a_mesh/tests/test_room_bridge_invariants.py',3102,3144),
 ('packages/a2a_mesh/tests/test_room_bridge_e2e.py',3148,3223),
 ('packages/a2a_mesh/room_bridge.py',3237,3525),
]:put(path,a,b)
pairs('scripts/tests/test_daemon_scope.py',3571,3621)
pairs('scripts/start_mcp_daemons.ps1',3633,3666)
pairs('scripts/stop_mcp_daemons.ps1',3670,3709)
replace('docs/agent-memory/project/coordination-room-v0.md',3726,3726,3732,3732)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'plan_sha256':SHA,'plan_lines':len(lines),'base':BASE,'a2a_base':A2A,'workspace':str(ROOT),'ops':ops,'stages':{}}
for name,folder in [('baseline',baseline),('rollback',rollback),('phase1',phase1),('proposal',proposal)]:
    manifest['stages'][name]={str(p.relative_to(folder)).replace('\\','/'):digest(p) for p in folder.rglob('*') if p.is_file()}
(PACKET/'extraction-r3.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({'roots':[str(x) for x in [baseline,rollback,phase1,proposal]],'operations':len(ops),'file_counts':{k:len(v) for k,v in manifest['stages'].items()}},indent=2))
