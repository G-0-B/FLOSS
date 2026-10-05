from pathlib import Path
import collections, hashlib, json, subprocess, sys, xml.etree.ElementTree as ET

P=Path(__file__).resolve().parent
manifest=json.loads((P/'extraction-r4.json').read_text())
fix=Path(manifest['workspace'])
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def cases(stage):
    result={}
    for t in ET.parse(P/f'{stage}-green.xml').getroot().iter('testcase'):
        key=t.get('classname')+'::'+t.get('name')
        assert key not in result,key
        result[key]='failed' if t.find('failure') is not None or t.find('error') is not None else 'skipped' if t.find('skipped') is not None else 'passed'
    return result
tests={s:cases(s) for s in ['baseline','phase1','proposal']}
base=tests['baseline']
changed={}
for stage,rows in tests.items():
    changed[stage]={
        'counts':dict(collections.Counter(rows.values())),
        'missing_baseline_cases':sorted(set(base)-set(rows)),
        'changed_baseline_outcomes':{k:[v,rows.get(k)] for k,v in base.items() if rows.get(k)!=v},
        'failures':[k for k,v in rows.items() if v=='failed'],
        'skips':[k for k,v in rows.items() if v=='skipped'],
        'room_counts':dict(collections.Counter(v for k,v in rows.items() if k.startswith('packages.coordination_room.'))),
        'a2a_counts':dict(collections.Counter(v for k,v in rows.items() if k.startswith('packages.a2a_mesh.'))),
        'scope_counts':dict(collections.Counter(v for k,v in rows.items() if k.startswith('scripts.tests.test_daemon_scope::'))),
    }
drift={s:[k for k,v in files.items() if not (fix/s/k).is_file() or digest(fix/s/k)!=v] for s,files in manifest['stages'].items()}
source=Path(r'C:\~shit\FLOSS\docs\superpowers\plans\2026-10-02-coordination-room-board-v1.md')
suffixes={'.md','.py','.json','.yaml','.yml','.toml','.rs','.ts','.js','.txt','.cfg','.ini','.sh','.ps1'}
nul_scan={}
for stage,files in manifest['stages'].items():
    paths=[k for k in files if Path(k).suffix.lower() in suffixes]
    nul_scan[stage]={'inspected_text_files':len(paths),'offenders':[k for k in paths if b'\0' in (fix/stage/k).read_bytes()]}
out={'review_date':'2026-10-04','python':sys.version,'source_plan_sha256':digest(source),'snapshot_sha256':digest(P/'plan-revision-4.md'),
     'line_count':len(source.read_text(encoding='utf-8').split('\n'))-1,
     'base':manifest['base'],'a2a_base':manifest['a2a_base'],'stages':changed,'source_drift_after_tests':drift,'independent_manifest_nul_scan':nul_scan,
     'primary_repo_head':subprocess.check_output(['git','-C',r'C:\~shit\FLOSS','rev-parse','HEAD'],text=True).strip()}
(P/'verification-summary.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
