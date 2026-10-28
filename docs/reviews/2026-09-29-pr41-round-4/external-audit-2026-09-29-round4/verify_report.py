import hashlib
import json
from pathlib import Path
import re
import subprocess

root=Path(__file__).resolve().parent
report=root/'REVIEW.md'
body=report.read_text(encoding='utf-8')
links=re.findall(r'\]\((C:/[^)]+)\)',body)
missing=[]
for link in links:
    path=re.sub(r':\d+$','',link)
    if not Path(path).is_file():missing.append(link)
assert not missing,missing
live=Path(r'C:\~shit\FLOSS\.worktrees\pr41-salvage')
head=subprocess.check_output(['git','-C',str(live),'rev-parse','HEAD']).decode().strip()
status=subprocess.check_output(['git','-C',str(live),'status','--short']).decode()
assert head=='6ea76202efce3ac85dc68bbbdc99ac21b6925ac4'
assert status==''
files=[p for p in root.iterdir() if p.is_file() and p.name!='report-readback.json']
receipt={'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),'links_checked':len(links),'missing_links':missing,'live_head':head,'live_status':status,'evidence_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}}
(root/'report-readback.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='evidence_sha256'},indent=2))
