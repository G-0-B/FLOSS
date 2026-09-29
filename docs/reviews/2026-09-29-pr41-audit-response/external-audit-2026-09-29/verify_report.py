import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent
report = root / 'REVIEW.md'
data = report.read_bytes()
assert b'\0' not in data
links = re.findall(r'\]\(([^)]+)\)', data.decode('utf-8'))
missing = [p for p in links if not (root / p.split('#')[0]).is_file()]
assert not missing, missing
receipt = {'sha256': hashlib.sha256(data).hexdigest(), 'local_links_checked': len(links), 'missing_links': missing}
(root / 'report-readback.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
