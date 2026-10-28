import ast
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
GIT = Path(r'C:\~shit\FLOSS\.worktrees\pr41-salvage')
TARGET = ROOT / 'baseline-with-endpoint-tests'
TARGET.mkdir(exist_ok=True)
data = subprocess.check_output(['git', '-C', str(GIT), 'archive', '--format=zip', '2a55711^'])
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    archive.extractall(TARGET)
patch = (GIT / 'docs/reviews/2026-09-05-pr41-fix-sweep/test-changes.patch').read_text()
paths = sorted(set(re.findall(r'^diff --git a/(.*?) b/', patch, re.M)))
selected = []
for name in paths:
    before = TARGET / name
    old_tree = ast.parse(before.read_text(encoding='utf-8')) if before.exists() else ast.Module(body=[], type_ignores=[])
    previous = {node.name: ast.dump(node, include_attributes=False) for node in old_tree.body if isinstance(node, ast.FunctionDef)}
    content = (ROOT / 'snapshot-303b1f9' / name).read_text(encoding='utf-8')
    for node in ast.parse(content).body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_') and node.name not in previous:
            selected.append(name + '::' + node.name)
    before.parent.mkdir(parents=True, exist_ok=True)
    before.write_text(content, encoding='utf-8')
(ROOT / 'new-test-nodes.json').write_text(json.dumps(selected, indent=2))
print(f'{len(selected)} newly added test functions; baseline production 2a55711^, endpoint test files only')
