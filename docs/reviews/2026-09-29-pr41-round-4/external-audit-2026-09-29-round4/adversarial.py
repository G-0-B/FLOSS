"""Audit-only probes: fixtures and preserved originals stay under this directory."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parent
END = ROOT / 'snapshot-0472ce1'
BASE = ROOT.parent / 'pr41-round3-20260929/snapshot-42e4d05'
FIX = ROOT / ('fixtures-' + os.name)
FIX.mkdir(exist_ok=False)
results = []

def load(repo, name):
    sys.path.insert(0, str(repo / 'scripts'))
    spec = importlib.util.spec_from_file_location(name, repo / 'scripts/materialize_shared_skill_surface.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def report(label, **data):
    row = dict(label=label, **data)
    results.append(row)
    print(json.dumps(row, ensure_ascii=True), flush=True)

def marker(m, owner):
    return json.dumps(dict(managed_by=m.MANAGED_BY, workspace_root=str(owner), skill_name='steady'))

def fixture(m, name):
    root = FIX / name
    owner = root / 'owner'
    source = owner / 'skills/steady'
    installed = root / 'target/steady'
    source.mkdir(parents=True)
    (source/'SKILL.md').write_text('---\nname: steady\ndescription: fixture\n---\nStable content.\n', encoding='utf-8')
    shutil.copytree(source, installed)
    skill = m.resolve_skill_entry(owner, {'path':'skills/steady'})
    return root, owner, source, installed, skill

for label, repo in [('base', BASE), ('endpoint', END)]:
    m = load(repo, label)
    for linktype in (['hardlink', 'symlink'] if os.name == 'posix' else ['hardlink']):
        root, owner, source, installed, skill = fixture(m, label + '-' + linktype)
        outside = root / 'outside-projection.json'
        original = marker(m, root/'old-workspace')
        outside.write_text(original, encoding='utf-8')
        mark = installed/m.MANAGED_MARKER
        if linktype == 'symlink':
            mark.symlink_to(outside)
        else:
            os.link(outside, mark)
        # Preserve, rather than delete, baseline's old tree. All other production
        # install operations run as written, including the new direct write.
        removals = []
        def preserve(path):
            removals.append(str(path))
            path.rename(root/'preserved-original')
        m.remove_path = preserve
        output, changed = m.install_skill_projection('audit', skill, installed.parent, 'new', check=False, dry_run=False, workspace_root=owner)
        report(label+'-'+linktype, external_changed=outside.read_text()!=original,
               marker_is_symlink=mark.is_symlink(), removed_via_preservation=removals,
               output=output, payload_retained=(installed/'SKILL.md').read_bytes()==(source/'SKILL.md').read_bytes())

    # Demonstrate that a clean current inventory cannot establish no past overwrite.
    root, owner, source, installed, skill = fixture(m, label+'-unmanaged-collision')
    evolved = b'Locally learned content.\n'
    (installed/'SKILL.md').write_bytes(evolved)
    m.remove_path = lambda path: path.rename(root/'preserved-evolved')
    messages, changed = m.install_skill_projection('audit', skill, installed.parent, 'new', check=False, dry_run=False, workspace_root=owner)
    report(label+'-unmanaged-collision', managed_before=False, evolved_before=True,
           current_inventory_equal=(installed/'SKILL.md').read_bytes()==(source/'SKILL.md').read_bytes(),
           evolved_original_preserved=(root/'preserved-evolved/SKILL.md').read_bytes()==evolved, output=messages)

    if os.name == 'posix':
        root, owner, source, installed, skill = fixture(m, label+'-newline')
        (source/'run.sh').write_bytes(b'exit 0\n')
        (installed/'run.sh').write_bytes(b'exit 0\r\n')
        skill = m.resolve_skill_entry(owner, {'path':'skills/steady'})
        (installed/m.MANAGED_MARKER).write_text(marker(m, owner), encoding='utf-8')
        before = subprocess.run(['bash', str(installed/'run.sh')], capture_output=True, text=True)
        m.remove_path = lambda path: path.rename(root/'preserved-newlines')
        messages, _ = m.install_skill_projection('audit', skill, installed.parent, 'new', check=False, dry_run=False, workspace_root=owner)
        after = subprocess.run(['bash', str(installed/'run.sh')], capture_output=True, text=True)
        check, drift = m.install_skill_projection('audit', skill, installed.parent, 'new', check=True, dry_run=False, workspace_root=owner)
        report(label+'-newline', before_exit=before.returncode, after_exit=after.returncode,
               stderr=after.stderr, output=messages, check=check, drift=drift,
               byte_equal=(installed/'run.sh').read_bytes()==(source/'run.sh').read_bytes())

if os.name == 'posix':
    m = load(END, 'cli_fixture')
    for kind in ['nul', 'loop']:
        owner = FIX / ('cli-'+kind) / 'owner'
        target = owner/'shared'
        bad = target/'a-unusable'
        stale = target/'z-withdrawn'
        bad.mkdir(parents=True)
        stale.mkdir()
        if kind == 'loop':
            loop = owner/'loop'
            loop.symlink_to(loop)
            identity = str(loop)
        else:
            identity = str(owner)+'\0tail'
        (bad/m.MANAGED_MARKER).write_text(marker(m, identity), encoding='utf-8')
        (stale/m.MANAGED_MARKER).write_text(marker(m, owner), encoding='utf-8')
        manifest = owner/'manifest.json'
        manifest.write_text(json.dumps({'manifest_version':'audit','skills':[], 'targets':{
            'first':{'enabled':True,'scope':'repo','install_path':'shared'},
            'later':{'enabled':True,'scope':'repo','install_path':'later'}}}), encoding='utf-8')
        for label, repo in [('base',BASE), ('endpoint',END)]:
            cmd=[sys.executable,str(repo/'scripts/materialize_shared_skill_surface.py'),'--workspace-root',str(owner),'--manifest',str(manifest),'--output-dir',str(owner/'out'),'--check']
            proc=subprocess.run(cmd, capture_output=True,text=True)
            (ROOT/(label+'-'+kind+'-cli.txt')).write_text(proc.stdout+proc.stderr,encoding='utf-8')
            report(label+'-'+kind+'-cli', command=cmd, exit_code=proc.returncode,
                   traceback='Traceback' in proc.stderr, stdout=proc.stdout, stderr=proc.stderr,
                   fixture_retained=bad.exists() and stale.exists())

(ROOT/('adversarial-'+os.name+'.json')).write_text(json.dumps({'python':sys.version,'results':results},indent=2),encoding='utf-8')
