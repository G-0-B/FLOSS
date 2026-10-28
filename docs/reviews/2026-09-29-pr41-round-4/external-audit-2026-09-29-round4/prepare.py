import hashlib
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE = Path(r'C:\~shit\FLOSS\.worktrees\pr41-salvage')
PACKET = 'docs/reviews/2026-09-29-pr41-round-4'
def git(*args):
    return subprocess.check_output(['git', '-C', str(LIVE), *args])
end = git('rev-parse', '0472ce1').decode().strip()
base = git('rev-parse', '42e4d05').decode().strip()
head = git('rev-parse', 'HEAD').decode().strip()
snapshot = ROOT / 'snapshot-0472ce1'
assert not snapshot.exists()
archive = git('archive', '--format=zip', end)
with zipfile.ZipFile(io.BytesIO(archive)) as zf:
    zf.extractall(snapshot)
(ROOT / 'temp').mkdir()
(ROOT / 'packet').mkdir()
fidelity = []
for file in ['PACKET.md', 'source-changes.patch', 'test-changes.patch']:
    data = (LIVE / PACKET / file).read_bytes()
    (ROOT / 'packet' / file).write_bytes(data)
    if file.endswith('.patch'):
        body = data.decode().replace('\r\n', '\n')
        parts = re.split(r'^=== COMMIT ([0-9a-f]+):[^\n]*\n', body, flags=re.M)
        for i in range(1, len(parts), 2):
            commit, patch = parts[i], parts[i+1].strip()
            files = re.findall(r'^diff --git a/(.*?) b/', patch, flags=re.M)
            actual = git('diff', commit + '^', commit, '--', *files).decode().strip()
            fidelity.append({'packet': file, 'commit': commit, 'files': files, 'matches': actual == patch})
rows = []
for name in git('diff', '--name-only', base, end).decode().splitlines():
    a, b = git('show', end + ':' + name), (snapshot / name).read_bytes()
    rows.append({'path': name, 'sha256': hashlib.sha256(b).hexdigest(),
                 'exact': a == b, 'same_lf': a.replace(b'\r\n', b'\n') == b.replace(b'\r\n', b'\n')})
(ROOT / 'identity.json').write_text(json.dumps({'base': base, 'endpoint': end,
    'live_head': head, 'live_status': git('status', '--short').decode(), 'files': rows,
    'patch_fidelity': fidelity}, indent=2), encoding='utf-8')
assert all(x['matches'] for x in fidelity), fidelity
assert all(x['same_lf'] for x in rows)
print(json.dumps({'endpoint': end, 'base': base, 'live_head': head,
    'patch_sections_matching': len(fidelity), 'changed_files': len(rows),
    'exact_files': sum(x['exact'] for x in rows)}, indent=2))
