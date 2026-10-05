from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET,subprocess,sys,os
ROOT=Path(__file__).resolve().parent
PACKET=Path(r'C:\~shit\FLOSS\docs\reviews\2026-10-02-room-board-v1\round-3')
manifest=json.loads((PACKET/'extraction-r3.json').read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changed=[]
for stage,files in manifest['stages'].items():
 for rel,old in files.items():
  p=ROOT/'fixtures-exact'/stage/rel
  if not p.exists() or digest(p)!=old:changed.append([stage,rel])
summary={'source_changed_after_tests':changed,'runs':{}}
for suffix in ['green','mcp2-green']:
 for stage in ['baseline','phase1','proposal']:
  p=PACKET/f'{stage}-{suffix}.xml';tree=ET.parse(p);suite=tree.find('testsuite');tests=list(tree.iter('testcase'))
  def counts(cases):
   return {'passed':sum(x.find('failure') is None and x.find('error') is None and x.find('skipped') is None for x in cases),'failed':sum(x.find('failure') is not None or x.find('error') is not None for x in cases),'skipped':sum(x.find('skipped') is not None for x in cases)}
  def ids(tag):return [x.attrib['classname']+'::'+x.attrib['name'] for x in tests if x.find(tag) is not None]
  summary['runs'][f'{stage}-{suffix}']={'counts':counts(tests),'failures':ids('failure'),'skips':ids('skipped'),'groups':{name:counts([x for x in tests if x.attrib['classname'].startswith(prefix)]) for name,prefix in [('room','packages.coordination_room.'),('a2a','packages.a2a_mesh.'),('daemon_scope','scripts.tests.test_daemon_scope')]}}
summary['new_failures']=sorted(set(summary['runs']['proposal-green']['failures'])-set(summary['runs']['baseline-green']['failures']))
(PACKET/'verification-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
# Diagnose the two sandbox-sensitive baseline failures without querying any live PID.
done=subprocess.run(['tasklist','/FI','PID eq 99999999'],capture_output=True,text=True)
(PACKET/'baseline-environment.txt').write_text(f'Nonexistent PID probe; rc={done.returncode}\nstdout={done.stdout}\nstderr={done.stderr}\nArchive fixtures intentionally have no .git index.\n',encoding='utf-8')
# Record the original hash again at packet completion.
p=Path(r'C:\~shit\FLOSS\docs\superpowers\plans\2026-10-02-coordination-room-board-v1.md')
assert digest(p)==manifest['plan_sha256']
