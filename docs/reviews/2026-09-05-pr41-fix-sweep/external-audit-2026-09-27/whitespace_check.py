import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE = Path(r'C:\~shit\FLOSS\.worktrees\pr41-salvage')
rows = []
for label, suffix in [('all', []), ('code', ['--', 'packages', 'scripts', 'tests', 'hooks'])]:
    command = ['git', '-C', str(LIVE), 'diff', '--check', 'aee4745..5a1a2b1', *suffix]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (ROOT / ('diff-check-' + label + '.txt')).write_bytes(result.stdout)
    diagnostics = [line for line in result.stdout.decode('utf-8', 'replace').splitlines()
                   if 'trailing whitespace.' in line or 'new blank line at EOF.' in line or 'space before tab in indent.' in line]
    files = sorted({line.rsplit(':', 2)[0] for line in diagnostics})
    row = {'scope': label, 'command': command, 'exit_code': result.returncode,
           'diagnostics': len(diagnostics), 'files': files}
    rows.append(row)
    print(label, 'exit', result.returncode, 'diagnostics', len(diagnostics), 'files', len(files))
(ROOT / 'diff-check-summary.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
