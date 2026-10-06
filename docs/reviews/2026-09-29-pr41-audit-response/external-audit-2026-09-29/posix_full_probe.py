import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
fixture = ROOT / 'posix-full-fixture'
owner = fixture / 'workspace'
target = owner / 'shared'
child = target / 'bad-identity'
child.mkdir(parents=True)
(child / '.flossi0ullk-managed.json').write_text(json.dumps({
    'managed_by': 'FLOSSI0ULLK shared skill surface', 'workspace_root': str(owner) + '\0',
    'source_path': str(owner / 'skills/bad-identity'), 'skill_name': 'bad-identity'}), encoding='utf-8')
manifest = owner / 'manifest.json'
manifest.write_text(json.dumps({'manifest_version': 'audit', 'skills': [], 'targets': {
    'first': {'enabled': True, 'scope': 'repo', 'install_path': 'shared'},
    'later': {'enabled': True, 'scope': 'repo', 'install_path': 'later'}}}), encoding='utf-8')
for label, repo in [('baseline', ROOT.parent / 'pr41-response-20260927/snapshot-5a1a2b1'),
                    ('endpoint', ROOT / 'snapshot-42e4d05')]:
    command = [sys.executable, str(repo / 'scripts/materialize_shared_skill_surface.py'),
        '--workspace-root', str(owner), '--manifest', str(manifest), '--output-dir', str(owner / 'out'), '--check']
    result = subprocess.run(command, capture_output=True, text=True)
    (ROOT / ('posix-full-' + label + '.txt')).write_text(result.stdout + result.stderr, encoding='utf-8')
    (ROOT / ('posix-full-' + label + '.command.json')).write_text(json.dumps({'command': command, 'exit_code': result.returncode}, indent=2), encoding='utf-8')
    print(label, 'exit=', result.returncode)
    print(result.stdout + result.stderr)
    if label == 'endpoint':
        assert 'ValueError: embedded null byte' in result.stderr
    else:
        assert 'Traceback' not in result.stderr and 'DRIFT' in result.stdout
print('ACTUAL_CLI_AND_MODULES_VERIFIED', 'Python=' + sys.version.split()[0])
