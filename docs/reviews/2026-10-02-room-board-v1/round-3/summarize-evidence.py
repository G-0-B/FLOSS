from pathlib import Path
import json,xml.etree.ElementTree as ET,subprocess,sys,os,hashlib
ROOT=Path(__file__).resolve().parent
PACKET=Path(r'C:\~shit\FLOSS\docs\reviews\2026-10-02-room-board-v1\round-3')
data=json.loads((PACKET/'script-audit.json').read_text())
violations=[]
selected={'consensus':'consensus.pid','ensemble':'reasoning_ensemble.pid','room':'coordination_room.pid','bridge':'a2a_room_bridge.pid','omniroute':'omniroute.pid'}
pids={'4240':'consensus','4241':'ensemble','4242':'room','4243':'bridge','4244':'omniroute'}
modules={'packages.metacoordinator_mcp.server':'consensus','packages.reasoning_ensemble.mcp_server':'ensemble','packages.coordination_room.server':'room','packages.a2a_mesh.room_bridge':'bridge'}
for i,r in enumerate(data['runs']):
 if r['selection']=='DEFAULT':continue
 names=r['selection'].split(',')
 for effect in r['effects'].splitlines():
  if effect.startswith('CHECK'):continue
  if r['dry']:violations.append({'run':i,'reason':'dry mutation','effect':effect})
  for name,pidfile in selected.items():
   if pidfile in effect and name not in names:violations.append({'run':i,'reason':'unselected file mutation','effect':effect})
  for module,name in modules.items():
   if effect.startswith('LAUNCH') and module in effect and name not in names:violations.append({'run':i,'reason':'unselected launch','effect':effect})
  if effect.startswith('LAUNCH') and '--no-open' in effect and 'omniroute' not in names:violations.append({'run':i,'reason':'unselected omni launch','effect':effect})
  if effect.startswith('KILL') and pids.get(effect.split()[1]) not in names:violations.append({'run':i,'reason':'unselected kill','effect':effect})
summary={'runs':len(data['runs']),'dry_runs':sum(r['dry'] for r in data['runs']),'parse_calls':len(data['parses']),'parse_errors':sum(len(json.loads(r['stdout'])['Errors']) for r in data['parses']),'violations':violations,'shells':list({json.loads(r['stdout'])['Shell'] for r in data['parses']})}
(PACKET/'script-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(summary)
for stage in ['baseline','phase1','proposal']:
 for name,args in [('spec-gate',['scripts/spec_gate.py','--check'])]+([('ruff',['-m','ruff','check','packages/coordination_room','packages/a2a_mesh/room_bridge.py','scripts/tests/test_daemon_scope.py']+[str(p.relative_to(ROOT/'fixtures-exact'/stage)) for p in (ROOT/'fixtures-exact'/stage/'packages/a2a_mesh/tests').glob('test_room_bridge_*.py')])] if stage=='proposal' else []):
  done=subprocess.run([sys.executable,*args],cwd=ROOT/'fixtures-exact'/stage,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (PACKET/f'{stage}-{name}.txt').write_bytes(done.stdout+f'\nEXIT_CODE={done.returncode}\n'.encode())
  print(stage,name,done.returncode,done.stdout.decode(errors='replace')[-1200:])
hashes={}
for name in ['REVIEW.md','plan-revision-1.md','round-2/REVIEW.md','round-2/antigravity-review.md','round-2/plan-revision-2.md','round-3/plan-revision-3.md']:
 p=PACKET.parent/name;hashes[name]=hashlib.sha256(p.read_bytes()).hexdigest()
hashes['current_plan']=hashlib.sha256(Path(r'C:\~shit\FLOSS\docs\superpowers\plans\2026-10-02-coordination-room-board-v1.md').read_bytes()).hexdigest()
(PACKET/'input-hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
