import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT / 'snapshot-42e4d05'
LIVE = Path(r'C:\~shit\FLOSS\.worktrees\pr41-salvage')
sys.path.insert(0, str(REPO / 'scripts'))
import materialize_shared_skill_surface as skills
def git(*args):
    return subprocess.check_output(['git', '-C', str(LIVE), *args])
metadata = json.loads((ROOT / 'identity.json').read_text(encoding='utf-8'))
end = metadata['endpoint']
unchanged = all(hashlib.sha256((REPO / row['path']).read_bytes()).hexdigest() == row['sha256'] for row in metadata['files'])
assert unchanged
print('ALL_REVIEWED_FILES_UNCHANGED', len(metadata['files']))
suffixes = {'.md', '.py', '.json', '.yaml', '.yml', '.toml', '.rs', '.ts', '.js', '.txt', '.cfg', '.ini', '.sh', '.ps1'}
names = [name for name in git('ls-tree', '-r', '--name-only', end).decode().splitlines() if Path(name).suffix.lower() in suffixes]
bad = [name for name in names if b'\0' in (REPO / name).read_bytes()]
assert not bad
print('EXACT_TRACKED_TEXT', len(names), 'NUL offenders:', bad)
owner = ROOT / 'ownership/outer'
alias = ROOT / 'ownership/outer-alias'
child = ROOT / 'ownership/shared/outer-live'
assert alias.is_junction()
assert skills.projection_owned_by(child, alias)
written = json.loads(skills.serialize_marker({'resolved_path': str(owner / 'skills/outer-live'), 'skill_name': 'outer-live'}, 'audit', alias))
assert written['workspace_root'] == str(owner.resolve())
print('REAL_WINDOWS_JUNCTION', 'read_alias_matches=True', 'write_alias_records_resolved_owner=True')
unmodified = ['packages/activity_log/provenance.py', 'packages/activity_log/tests/test_provenance.py',
              'packages/metacoordinator_mcp/tests/test_voter_context_rendering.py']
for name in unmodified:
    assert git('show', end + ':' + name) == git('show', metadata['base'] + ':' + name)
print('WINERROR_FAILURE_PATHS_BYTE_IDENTICAL_TO_BASE', unmodified)
env = {name: importlib.metadata.version(name) for name in ['pytest', 'tomlkit', 'ruamel.yaml', 'ruff', 'filelock', 'litellm', 'blake3', 'jcs', 'pynacl']}
env['python'] = platform.python_version()
(ROOT / 'environment.json').write_text(json.dumps(env, indent=2), encoding='utf-8')
print('LIVE_HEAD', git('rev-parse', 'HEAD').decode().strip())
print('LIVE_STATUS', repr(git('status', '--short').decode()))
