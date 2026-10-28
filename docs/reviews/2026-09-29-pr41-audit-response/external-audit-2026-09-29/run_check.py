import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
label, *args = sys.argv[1:]
output = ROOT / (label + '.txt')
assert not output.exists(), output
env = dict(os.environ, PYTHONPATH='', PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
           PYTHONIOENCODING='utf-8', TEMP=str(ROOT / 'temp'), TMP=str(ROOT / 'temp'))
command = [sys.executable, *args]
cwd = ROOT / 'snapshot-42e4d05'
with output.open('wb') as out:
    result = subprocess.run(command, cwd=cwd, env=env, stdout=out, stderr=subprocess.STDOUT)
(ROOT / (label + '.command.json')).write_text(json.dumps({'command': command,
    'cwd': str(cwd), 'exit_code': result.returncode,
    'env_overrides': {k: env[k] for k in ['PYTHONPATH', 'PYTHONDONTWRITEBYTECODE', 'PYTHONUTF8', 'PYTHONIOENCODING', 'TEMP', 'TMP']}
}, indent=2), encoding='utf-8')
print(output.read_text(encoding='utf-8', errors='replace')[-11000:])
print('CAPTURED EXIT:', result.returncode)
sys.exit(result.returncode)
