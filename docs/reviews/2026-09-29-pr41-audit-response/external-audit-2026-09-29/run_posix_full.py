import subprocess
from pathlib import Path
root = Path(__file__).resolve().parent
result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'python3',
    '/mnt/c/~shit/_audit/pr41-round3-20260929/posix_full_probe.py'], capture_output=True)
(root / 'posix-full.txt').write_bytes(result.stdout + result.stderr)
print((result.stdout + result.stderr).decode('utf-8', 'replace'))
print('EXIT:', result.returncode)
