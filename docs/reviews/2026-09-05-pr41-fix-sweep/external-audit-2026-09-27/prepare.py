import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE = Path(r'C:\~shit\FLOSS\.worktrees\pr41-salvage')
END = '5a1a2b1655274d4d37bba9e27a3bb2d11f2e35f6'

def git(*args):
    return subprocess.check_output(['git', '-C', str(LIVE), *args])

snapshot = ROOT / 'snapshot-5a1a2b1'
assert not snapshot.exists(), 'Do not overwrite an audit snapshot'
archive = git('archive', '--format=zip', END)
with zipfile.ZipFile(io.BytesIO(archive)) as zf:
    zf.extractall(snapshot)
(ROOT / 'temp').mkdir(exist_ok=True)
paths = git('diff', '--name-only', 'aee4745', END).decode().splitlines()
rows = []
for name in paths:
    blob = git('show', f'{END}:{name}')
    exported = (snapshot / name).read_bytes()
    rows.append({'path': name, 'git_sha256': hashlib.sha256(blob).hexdigest(),
                 'export_sha256': hashlib.sha256(exported).hexdigest(),
                 'exact': blob == exported,
                 'same_lf': blob.replace(b'\r\n', b'\n') == exported.replace(b'\r\n', b'\n')})
(ROOT / 'identity.json').write_text(json.dumps({
    'endpoint': END, 'base': git('rev-parse', 'aee4745').decode().strip(),
    'start': git('rev-parse', 'e747a75').decode().strip(),
    'live_head_at_export': git('rev-parse', 'HEAD').decode().strip(),
    'live_status_at_export': git('status', '--short').decode(),
    'archive_sha256': hashlib.sha256(archive).hexdigest(), 'files': rows,
}, indent=2), encoding='utf-8')
(ROOT / 'source-diff.patch').write_bytes(git('diff', 'aee4745', END, '--',
    'packages/reasoning_ensemble/synthesizer.py',
    'scripts/materialize_shared_agent_surface.py',
    'scripts/materialize_shared_hook_surface.py',
    'scripts/materialize_shared_skill_surface.py'))
print(json.dumps({'snapshot': str(snapshot), 'changed_files': len(rows),
                  'exact': sum(r['exact'] for r in rows),
                  'same_lf': sum(r['same_lf'] for r in rows)}, indent=2))
