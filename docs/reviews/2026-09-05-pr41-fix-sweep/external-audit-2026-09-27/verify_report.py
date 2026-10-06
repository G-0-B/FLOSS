import hashlib
import importlib.metadata
import json
import platform
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
report = ROOT / 'REVIEW.md'
body = report.read_text(encoding='utf-8')
links = re.findall(r'\]\(([^)]+)\)', body)
missing = [target for target in links if not (ROOT / target.split('#')[0]).is_file()]
assert not missing, missing
versions = {name: importlib.metadata.version(name) for name in (
    'pytest', 'tomlkit', 'ruamel.yaml', 'ruff', 'filelock', 'litellm', 'blake3', 'jcs', 'pynacl')}
versions['python'] = platform.python_version()
(ROOT / 'environment.json').write_text(json.dumps(versions, indent=2), encoding='utf-8')
receipt = {'report_sha256': hashlib.sha256(report.read_bytes()).hexdigest(),
           'local_links': len(links), 'missing_links': missing,
           'environment': versions}
(ROOT / 'report-readback.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
