"""Capture command, full output and status without altering the source checkout."""
import json
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
label, *args = sys.argv[1:]
path = root / (label + '.txt')
assert not path.exists(), path
env = dict(os.environ, PYTHONPATH='', PYTHONDONTWRITEBYTECODE='1',
           TEMP=str(root / 'temp'), TMP=str(root / 'temp'),
           PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
cmd = [sys.executable, *args]
with path.open('wb') as out:
    result = subprocess.run(cmd, cwd=root / 'snapshot-5a1a2b1', env=env,
                            stdout=out, stderr=subprocess.STDOUT)
(root / (label + '.command.json')).write_text(json.dumps({
    'command': cmd, 'cwd': str(root / 'snapshot-5a1a2b1'),
    'exit_code': result.returncode, 'env_overrides': {
        k: env[k] for k in ('PYTHONPATH', 'PYTHONDONTWRITEBYTECODE', 'TEMP', 'TMP', 'PYTHONUTF8', 'PYTHONIOENCODING')}
}, indent=2), encoding='utf-8')
print(path.read_text(encoding='utf-8', errors='replace')[-14000:])
print('CAPTURED EXIT CODE:', result.returncode)
sys.exit(result.returncode)
