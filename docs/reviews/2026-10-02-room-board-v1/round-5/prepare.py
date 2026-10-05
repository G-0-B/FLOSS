"""Pinned, archive-only reconstruction. Writes workspace fixtures and this packet."""
from pathlib import Path
import ast, difflib, hashlib, json, shutil, subprocess

P = Path(__file__).resolve().parent
W = Path(r'C:\Users\kalis\AppData\Local\Temp\codex-room-board-r5-20261004-042545')
R4 = P.parent / 'round-4'
PLAN = Path(r'C:\~shit\FLOSS\docs\superpowers\plans\2026-10-02-coordination-room-board-v1.md')
SHA = 'f2a8392e874a6f90c6818657fccc0050625da518fb09860dff0d58c68b8d1752'
raw = PLAN.read_bytes()
assert hashlib.sha256(raw).hexdigest() == SHA
(P/'plan-revision-5.md').write_bytes(raw)
old = (R4/'plan-revision-4.md').read_text(encoding='utf-8').split('\n')
new = raw.decode('utf-8').replace('\r\n','\n').split('\n')
mapping = {}
for a,b,size in difflib.SequenceMatcher(None,old,new,autojunk=False).get_matching_blocks():
    mapping.update({a+i+1:b+i+1 for i in range(size)})
(P/'plan-r4-r5.diff').write_text(''.join(difflib.unified_diff([x+'\n' for x in old],[x+'\n' for x in new],fromfile='revision4',tofile='revision5')),encoding='utf-8')
source = (R4/'rebuild.py').read_text(encoding='utf-8')
# Every line-range endpoint must be a byte-identical line, or fail reconstruction.
class Relocate(ast.NodeTransformer):
    def visit_Constant(self,node):
        if isinstance(node.value,int) and 228 <= node.value <= 3841:
            assert node.value in mapping, ('unmapped endpoint',node.value)
            return ast.copy_location(ast.Constant(mapping[node.value]),node)
        return node
source = ast.unparse(Relocate().visit(ast.parse(source)))
source = source.replace("Path(tempfile.mkdtemp(prefix='codex-room-board-r4-20261004-')) / 'fixtures-exact'",f"Path({str(W / 'fixtures-exact')!r})")
source = source.replace(str(R4),str(P)).replace('plan-revision-4.md','plan-revision-5.md').replace('extraction-r4.json','extraction-r5.json').replace('7d40c37e91a1e6beb9f45a09cd9d73ca4c8b4cb32e5db7aebf6d6d9da955c6f1',SHA)
# ast.unparse renders Windows paths as escaped string literals.
source = source.replace(repr(str(R4)),repr(str(P)))
(P/'rebuild.py').write_text(source+'\n',encoding='utf-8')
exec(compile(source,str(P/'rebuild.py'),'exec'),{})
manifest=json.loads((P/'extraction-r5.json').read_text())
previous=json.loads((R4/'extraction-r4.json').read_text())
comparison={}
for stage,files in manifest['stages'].items():
    prior=previous['stages'][stage]
    comparison[stage]={'changed':[n for n in sorted(files.keys() & prior.keys()) if files[n]!=prior[n]],'added':sorted(files.keys()-prior.keys()),'removed':sorted(prior.keys()-files.keys()),'identical':sum(files[n]==prior[n] for n in files.keys() & prior.keys())}
(P/'r4-byte-comparison.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
runner=(R4/'run-checks.py').read_text().replace('extraction-r4.json','extraction-r5.json')
(P/'run-checks.py').write_text(runner,encoding='utf-8')
helpers=new.index("$ErrorActionPreference = 'Stop'",new.index('## Deployment (operator-gated, separate from the tasks)'))
end=new.index('```',helpers)
(P/'deploy_helpers.ps1').write_text('\n'.join(new[helpers:end])+'\n',encoding='utf-8')
print(json.dumps(comparison,indent=2))
