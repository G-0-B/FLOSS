import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE = Path(r'C:\~shit\FLOSS\.worktrees\pr41-salvage')
SNAPSHOT = ROOT / 'snapshot-5a1a2b1'
END = '5a1a2b1655274d4d37bba9e27a3bb2d11f2e35f6'

def git(*args):
    return subprocess.check_output(['git', '-C', str(LIVE), *args])

names = git('ls-tree', '-r', '--name-only', END).decode().splitlines()
suffixes = {'.md', '.py', '.json', '.yaml', '.yml', '.toml', '.rs', '.ts', '.js', '.txt', '.cfg', '.ini', '.sh', '.ps1'}
paths = [name for name in names if Path(name).suffix.lower() in suffixes]
offenders = [name for name in paths if b'\0' in (SNAPSHOT / name).read_bytes()]
print('PINNED_TRACKED_TEXT', len(paths), 'files; NUL offenders:', offenders)
assert not offenders

copied = 'docs/reviews/2026-09-05-pr41-fix-sweep/external-audit-2026-09-18/'
original = Path(r'C:\~shit\_audit\pr41-fix-sweep-20260918')
differences = []
for name in names:
    if name.startswith(copied):
        a, b = git('show', END + ':' + name), (original / Path(name).name).read_bytes()
        assert a.replace(b'\r\n', b'\n') == b.replace(b'\r\n', b'\n'), name
        if a != b:
            differences.append(Path(name).name)
print('COMMITTED_EVIDENCE_NORMALIZED_FILES', json.dumps(differences))

identity = json.loads((ROOT / 'identity.json').read_text(encoding='utf-8'))
changed = [r['path'] for r in identity['files'] if r['path'].endswith('.py') and not r['path'].startswith('docs/')]
for name in changed:
    ast.parse((SNAPSHOT / name).read_bytes(), filename=name)
print('CHANGED_PYTHON_PARSE', len(changed), 'passed')
unchanged = all(hashlib.sha256((SNAPSHOT / row['path']).read_bytes()).hexdigest() == row['export_sha256'] for row in identity['files'])
print('PINNED_CHANGED_FILES_UNMODIFIED', unchanged)
assert unchanged
print('LIVE_HEAD_END', git('rev-parse', 'HEAD').decode().strip())
print('LIVE_STATUS_END\n' + git('status', '--short').decode())
