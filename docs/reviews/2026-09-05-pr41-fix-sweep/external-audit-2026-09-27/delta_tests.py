import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
selected = json.loads((ROOT / 'new-tests.json').read_text(encoding='utf-8'))
env = dict(os.environ, PYTHONPATH='', PYTHONDONTWRITEBYTECODE='1',
           TEMP=str(ROOT / 'temp'), TMP=str(ROOT / 'temp'),
           PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
cwd = ROOT / 'baseline-aee4745'
cmd = [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
       '--basetemp=' + str(ROOT / 'pytest-delta-baseline'),
       '--junitxml=' + str(ROOT / 'delta-baseline.xml'), *selected]
with (ROOT / 'delta-baseline.txt').open('wb') as out:
    result = subprocess.run(cmd, cwd=cwd, env=env, stdout=out, stderr=subprocess.STDOUT)
(ROOT / 'delta-baseline.command.json').write_text(json.dumps({
    'command': cmd, 'cwd': str(cwd), 'exit_code': result.returncode
}, indent=2), encoding='utf-8')
print((ROOT / 'delta-baseline.txt').read_text(encoding='utf-8')[-4200:])
print('CAPTURED BASELINE EXIT:', result.returncode)
