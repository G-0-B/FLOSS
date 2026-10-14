import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
LIVE=Path(r'C:\~shit\FLOSS\.worktrees\pr41-salvage')
REPO=ROOT/'snapshot-0472ce1'
BASE=ROOT.parent/'pr41-round3-20260929/snapshot-42e4d05'
ENV=dict(os.environ, PYTHONPATH='',PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
def capture(label,cmd,cwd=REPO,env=ENV):
    p=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (ROOT/(label+'.txt')).write_text(p.stdout+p.stderr,encoding='utf-8')
    (ROOT/(label+'.command.json')).write_text(json.dumps(dict(command=cmd,cwd=str(cwd),exit_code=p.returncode),indent=2),encoding='utf-8')
    print(label, 'exit=',p.returncode, (p.stdout+p.stderr)[-2200:],flush=True)
    return p

shutil.copy2(Path(sys.executable).parents[1]/'Lib/site-packages/py.py',ROOT/'posix-deps/py.py')
native=capture('native-focused',['wsl.exe','-d','Ubuntu','--exec','env','PYTHONPATH=/mnt/c/~shit/_audit/pr41-round4-20260929/posix-deps','PYTHONDONTWRITEBYTECODE=1','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1','python3','-m','pytest','-q','-p','no:cacheprovider','--basetemp=/mnt/c/~shit/_audit/pr41-round4-20260929/temp/native-complete','/mnt/c/~shit/_audit/pr41-round4-20260929/snapshot-0472ce1/scripts/tests/test_shared_skill_surface_scope.py'])

old=ROOT/'baseline-code'
shutil.copytree(BASE/'scripts',old/'scripts')
shutil.copy2(BASE/'shared-skill-surface.json',old/'shared-skill-surface.json')
shutil.copy2(REPO/'scripts/tests/test_shared_skill_surface_scope.py',old/'scripts/tests/test_shared_skill_surface_scope.py')
selectors=['test_an_identity_the_os_cannot_resolve_is_unknown_not_a_crash','test_a_marker_the_os_cannot_resolve_does_not_stop_the_refresh','test_a_marker_with_an_unusable_identity_is_kept_and_reported','test_a_marker_from_a_workspace_that_no_longer_exists_is_kept_and_reported','test_a_marker_only_change_never_takes_the_installed_skill_away','test_a_projection_owned_by_another_workspace_is_never_removed']
cmd=[sys.executable,'-m','pytest','-q','-p','no:cacheprovider','--basetemp='+str(ROOT/'temp/discrimination')]+['scripts/tests/test_shared_skill_surface_scope.py::'+n for n in selectors]
capture('discrimination',cmd,cwd=old)

# Isolate the wording-only commit using the immediately preceding source blob.
wording=ROOT/'wording-before'
shutil.copytree(old,wording)
raw=subprocess.check_output(['git','-C',str(LIVE),'show','9a23477:scripts/materialize_shared_skill_surface.py'])
(wording/'scripts/materialize_shared_skill_surface.py').write_bytes(raw)
capture('wording-discrimination',[sys.executable,'-m','pytest','-q','-p','no:cacheprovider','--basetemp='+str(ROOT/'temp/wording'),'scripts/tests/test_shared_skill_surface_scope.py::test_a_marker_from_a_workspace_that_no_longer_exists_is_kept_and_reported'],cwd=wording)

metadata=json.loads((ROOT/'identity.json').read_text())
assert all(hashlib.sha256((REPO/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in metadata['files'])
end=metadata['endpoint']
def git(*args):return subprocess.check_output(['git','-C',str(LIVE),*args])
suffixes={'.md','.py','.json','.yaml','.yml','.toml','.rs','.ts','.js','.txt','.cfg','.ini','.sh','.ps1'}
names=[n for n in git('ls-tree','-r','--name-only',end).decode().splitlines() if Path(n).suffix.lower() in suffixes]
bad=[n for n in names if b'\0' in (REPO/n).read_bytes()]
unmodified={n:git('show',end+':'+n)==git('show',metadata['base']+':'+n) for n in ['packages/activity_log/provenance.py','packages/activity_log/tests/test_provenance.py']}
result=dict(reviewed_files_unchanged=len(metadata['files']),tracked_text_count=len(names),nul_offenders=bad,failing_paths_unchanged=unmodified,live_head=git('rev-parse','HEAD').decode().strip(),live_status=git('status','--short').decode())
(ROOT/'final-checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2),flush=True)
capture('spec-gate',[sys.executable,'scripts/spec_gate.py','--check'])
capture('ruff',[sys.executable,'-m','ruff','check','packages','scripts','tests','hooks'])
versions={n:importlib.metadata.version(n) for n in ['pytest','tomlkit','ruamel.yaml','ruff','filelock','litellm','blake3','jcs','pynacl']}
versions['python']=sys.version
(ROOT/'environment.json').write_text(json.dumps(versions,indent=2),encoding='utf-8')
