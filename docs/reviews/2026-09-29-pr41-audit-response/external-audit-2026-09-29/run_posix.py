import json
import subprocess
from pathlib import Path
root = Path(__file__).resolve().parent
cmd = ['wsl.exe', '-d', 'Ubuntu', '--exec', 'python3', '/mnt/c/~shit/_audit/pr41-round3-20260929/posix_probe.py']
result = subprocess.run(cmd, capture_output=True)
(root / 'posix.txt').write_bytes(result.stdout + result.stderr)
(root / 'posix.command.json').write_text(json.dumps({'command': cmd, 'exit_code': result.returncode}, indent=2), encoding='utf-8')
print((result.stdout + result.stderr).decode('utf-8', 'replace'))
print('EXIT:', result.returncode)
