"""Compare every JUnit outcome; rehash fixtures and pinned inputs read-only."""
from pathlib import Path
import collections, hashlib, json, subprocess, sys, xml.etree.ElementTree as ET

P=Path(__file__).resolve().parent
manifest=json.loads((P/'extraction-r5.json').read_text())
fix=Path(manifest['workspace'])
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def command(argv,cwd=None):
    p=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,errors='replace')
    return dict(command=argv,cwd=str(cwd) if cwd else None,rc=p.returncode,stdout=p.stdout,stderr=p.stderr)
summary={'python':sys.version,'executable':sys.executable,'stages':{},'comparisons':{},'hashes':{},'source_drift':{}}
for stage in ['baseline','phase1','proposal']:
    tree=ET.parse(P/f'{stage}-green.xml')
    cases={}
    for case in tree.iter('testcase'):
        key=case.attrib['classname']+'::'+case.attrib['name']
        assert key not in cases,key
        outcome='passed'; detail=''
        for kind in ['failure','error','skipped']:
            found=case.find(kind)
            if found is not None:outcome=kind;detail=found.attrib.get('message','');break
        cases[key]={'outcome':outcome,'detail':detail}
    summary['stages'][stage]={'counts':dict(collections.Counter(c['outcome'] for c in cases.values())),'failures':{k:v for k,v in cases.items() if v['outcome'] in ['failure','error']},'skips':{k:v for k,v in cases.items() if v['outcome']=='skipped'},'cases':cases}
for left,right in [('baseline','phase1'),('baseline','proposal'),('phase1','proposal')]:
    a=summary['stages'][left]['cases'];b=summary['stages'][right]['cases']
    summary['comparisons'][left+'-'+right]={'missing':sorted(a.keys()-b.keys()),'added':sorted(b.keys()-a.keys()),'changed':{k:{'before':a[k]['outcome'],'after':b[k]['outcome']} for k in sorted(a.keys()&b.keys()) if a[k]['outcome']!=b[k]['outcome']}}
suffixes={'.md','.py','.json','.yaml','.yml','.toml','.rs','.ts','.js','.txt','.cfg','.ini','.sh','.ps1'}
for stage,files in manifest['stages'].items():
    summary['source_drift'][stage]=[name for name,h in files.items() if not (fix/stage/name).exists() or digest(fix/stage/name)!=h]
    texts=[name for name in files if Path(name).suffix.lower() in suffixes]
    summary.setdefault('archive_text_scan',{})[stage]={'count':len(texts),'nul_offenders':[name for name in texts if b'\0' in (fix/stage/name).read_bytes()]}
for name,path in [('snapshot',P/'plan-revision-5.md'),('live',Path(r'C:\~shit\FLOSS\docs\superpowers\plans\2026-10-02-coordination-room-board-v1.md')),('round4',P.parent/'round-4/plan-revision-4.md')]:
    summary['hashes'][name]={'sha256':digest(path),'newline_lines':len(path.read_text(encoding='utf-8').split('\n'))}
summary['git_bases']=command(['git','-c','safe.directory=C:/~shit/FLOSS','-C',r'C:\~shit\FLOSS','rev-parse','feat/coordination-room-rebased','feat/a2a-harness-mesh'])
summary['baseline_environment']={'tasklist':command(['tasklist','/FI','PID eq 999999','/FO','CSV','/NH']),'git_inventory':command(['git','ls-files'],fix/'baseline')}
numbers=json.loads((P/'number-results.json').read_text())
summary['numbers']=numbers['summary']
summary['numbers']['outcomes']=dict(collections.Counter(r['outcome'] for r in numbers['parser']))
normal_errors=[r for r in numbers['http'] if r['outcome']=='response' and any(a.startswith('error: ') for a in r['artifacts'])]
summary['numbers']['normal_errors']=len(normal_errors)
summary['numbers']['all_normal_errors_failed_and_no_calls']=all(r['states']==[4] and r['room_calls']==[] for r in normal_errors)
summary['numbers']['all_internal_errors_no_calls']=all(r['room_calls']==[] for r in numbers['http'] if r['outcome']!='response')
summary['deployment']=[{'shell':r['result']['shell'],'cases':len(r['result']['results']),'unexpected':[c['case'] for c in r['result']['results'] if not c['matched_expectation']]} for r in json.loads((P/'deployment-results.json').read_text())]
(P/'verification-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({k:({n:{'counts':v['counts'],'failures':list(v['failures'])} for n,v in value.items()} if k=='stages' else value) for k,value in summary.items() if k not in ['comparisons']},indent=2))
print(json.dumps({name:{'missing':v['missing'],'added_count':len(v['added']),'changed':v['changed']} for name,v in summary['comparisons'].items()},indent=2))
