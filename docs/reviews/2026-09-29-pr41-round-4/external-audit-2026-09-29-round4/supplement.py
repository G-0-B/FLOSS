import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
END=ROOT/'snapshot-0472ce1'
BASE=ROOT.parent/'pr41-round3-20260929/snapshot-42e4d05'
env=dict(os.environ,PYTHONPATH='',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
cmd=[sys.executable,'-m','ruff','check','packages','scripts','tests','hooks']
p=subprocess.run(cmd,cwd=BASE,env=env,capture_output=True,text=True,encoding='utf-8')
(ROOT/'ruff-base.txt').write_text(p.stdout+p.stderr,encoding='utf-8')
(ROOT/'ruff-base.command.json').write_text(json.dumps({'command':cmd,'cwd':str(BASE),'exit_code':p.returncode},indent=2),encoding='utf-8')
print('RUFF_DIAGNOSTICS_IDENTICAL_TO_BASE',p.stdout+p.stderr==(ROOT/'ruff.txt').read_text(encoding='utf-8'))
sys.path.insert(0,str(END/'scripts'))
import materialize_shared_skill_surface as m
root=ROOT/'torn-marker-fixture'
owner=root/'owner'
source=owner/'skills/steady'
source.mkdir(parents=True)
(source/'SKILL.md').write_text('---\nname: steady\ndescription: fixture\n---\nContent.\n',encoding='utf-8')
skill=m.resolve_skill_entry(owner,{'path':'skills/steady'})
target=root/'installed/steady'
target.mkdir(parents=True)
(target/'SKILL.md').write_bytes((source/'SKILL.md').read_bytes())
(target/m.MANAGED_MARKER).write_bytes(b'{"workspace_root":"C:/caf\xc3')
assert m.read_managed_marker(target) is None
rows=[]
for check in [True,False]:
    try:
        m.install_skill_projection('audit',skill,target.parent,'test',check=check,dry_run=False,workspace_root=owner)
    except Exception as exc:
        row={'check':check,'exception':type(exc).__name__,'detail':str(exc),'payload_intact':(target/'SKILL.md').read_bytes()==(source/'SKILL.md').read_bytes()}
        rows.append(row)
        print(json.dumps(row))
    else:
        raise AssertionError('Expected observed marker recovery gap')
(ROOT/'torn-marker.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
