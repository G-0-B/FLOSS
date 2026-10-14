import ast
import hashlib
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE = Path(r'C:\~shit\FLOSS\.worktrees\pr41-salvage')
SNAPSHOT = ROOT / 'snapshot-5a1a2b1'
OLD = Path(r'C:\~shit\_audit\pr41-fix-sweep-20260918')

def git(*args):
    return subprocess.check_output(['git', '-C', str(LIVE), *args])

copied = SNAPSHOT / 'docs/reviews/2026-09-05-pr41-fix-sweep/external-audit-2026-09-18'
rows = []
for file in sorted(copied.iterdir()):
    original = OLD / file.name
    a, b = file.read_bytes(), original.read_bytes()
    rows.append({'file': file.name, 'exact': a == b,
        'same_lf': a.replace(b'\r\n', b'\n') == b.replace(b'\r\n', b'\n'),
        'original_sha256': hashlib.sha256(b).hexdigest(),
        'copied_sha256': hashlib.sha256(a).hexdigest()})
report = (copied / 'REVIEW.md').read_text(encoding='utf-8')
links = [p for p in re.findall(r'\]\(([^)]+)\)', report) if not p.startswith(('https:', 'http:'))]
missing = [p for p in links if not (copied / p.split('#')[0]).exists()]
(ROOT / 'evidence-fidelity.json').write_text(json.dumps({
    'files': rows, 'relative_links_checked': len(links), 'missing_links': missing
}, indent=2), encoding='utf-8')
print('COPIED_EVIDENCE', len(rows), 'files;', sum(r['exact'] for r in rows), 'byte equal;',
      sum(r['same_lf'] for r in rows), 'LF-normalized equal;', len(links), 'links;', len(missing), 'missing')

# Re-run newly named tests over exact pre-response source, preserving both snapshots.
baseline = ROOT / 'baseline-aee4745'
assert not baseline.exists()
with zipfile.ZipFile(io.BytesIO(git('archive', '--format=zip', 'aee4745'))) as archive:
    archive.extractall(baseline)
tests = ['packages/reasoning_ensemble/tests/test_survivor_independence.py',
         'scripts/tests/test_shared_skill_surface_scope.py',
         'tests/test_shared_agent_surface_mcp.py']
selected = []
for file in tests:
    old = ast.parse((baseline / file).read_text(encoding='utf-8'))
    new_data = (SNAPSHOT / file).read_bytes()
    new = ast.parse(new_data)
    old_names = {n.name for n in old.body if isinstance(n, ast.FunctionDef)}
    selected.extend(f'{file}::{n.name}' for n in new.body
                    if isinstance(n, ast.FunctionDef) and n.name.startswith('test_') and n.name not in old_names)
    (baseline / file).write_bytes(new_data)
(ROOT / 'new-tests.json').write_text(json.dumps(selected, indent=2), encoding='utf-8')
print('BASELINE_PREPARED', len(selected), 'new test functions')
