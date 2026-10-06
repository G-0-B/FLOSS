"""Reproduce the authorized Linux comparison without editing source or tests.

Run this orchestration helper with WSL's system Python. The tested interpreter
is the private Python 3.13 environment created below. All clones/runtime paths
are native Linux; receipts are mirrored to the authorized Windows folder.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET

ROOT=Path(sys.argv[1]).resolve()
BUNDLE=Path(sys.argv[2]).resolve()
DEST=Path(sys.argv[3]).resolve()
OUT=ROOT/'receipts'; OUT.mkdir(exist_ok=True)
BASE='4aab13e30f3c2960da787b47c90926256b4b5b73'
HEAD='806a99936d1dd752641d4b7d1f01e8085e156c5e'
CHECKPOINT='0281a47cd817efb2f2426886e3a1058c157b33eb'
assert str(ROOT).startswith('/home/kalis/room-board-linux-20261006-')
assert str(DEST).endswith('/docs/reviews/2026-10-02-room-board-v1/linux-run')
records=[]; runs={}; comparison=None; metadata={}
env=dict(os.environ)
env.pop('PYTHONPATH',None);env.pop('COORDINATION_ROOM_BOARD',None)
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',
           UV_CACHE_DIR=str(ROOT/'uv-cache'),UV_PYTHON_INSTALL_DIR=str(ROOT/'python'),
           PIP_CACHE_DIR=str(ROOT/'pip-cache'))
journal=(DEST/'commands.txt').read_text(encoding='utf-8')
(OUT/'commands.txt').write_text(journal,encoding='utf-8')

def mirror(name): shutil.copyfile(OUT/name,DEST/name)
def write(name,text):
    (OUT/name).write_text(text,encoding='utf-8');mirror(name)
def save_json(name,value): write(name,json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def journal_line(text):
    with (OUT/'commands.txt').open('a',encoding='utf-8') as f:f.write(text+'\n')
    mirror('commands.txt')

def command(args,cwd=ROOT,name=None,check=False,timeout=900,run_env=None):
    cmd=[str(x) for x in args]
    journal_line(f'\n[{time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}] cwd={cwd}\n$ {shlex.join(cmd)}')
    record={'command':cmd,'cwd':str(cwd),'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    started=time.monotonic()
    try:
        if name:
            with (OUT/name).open('wb') as f:
                done=subprocess.run(cmd,cwd=cwd,env=run_env or env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
            mirror(name); output=(OUT/name).read_text(encoding='utf-8',errors='replace')
        else:
            done=subprocess.run(cmd,cwd=cwd,env=run_env or env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
            output=done.stdout.decode('utf-8',errors='replace')
        record.update(returncode=done.returncode,elapsed_seconds=time.monotonic()-started,receipt=name)
    except subprocess.TimeoutExpired:
        if name:mirror(name)
        record.update(returncode=None,timed_out=True,elapsed_seconds=time.monotonic()-started,receipt=name)
        records.append(record);save_json('command-results.json',records)
        journal_line('TIMEOUT');raise
    records.append(record);save_json('command-results.json',records)
    journal_line(f'exit={done.returncode}; elapsed={record["elapsed_seconds"]:.2f}s'+(f'; output={name}' if name else '\n'+output.rstrip()))
    if check and done.returncode: raise RuntimeError(f'Command failed ({done.returncode}): {shlex.join(cmd)}')
    return done.returncode,output

def cases(name):
    out={}
    for tc in ET.parse(OUT/name).getroot().iter('testcase'):
        key=f'{tc.get("classname")}::{tc.get("name")}'
        if key in out:raise RuntimeError(f'Duplicate JUnit identity: {key}')
        marks=[c for c in tc if c.tag in ('failure','error','skipped')]
        out[key]=(marks[0].tag,(marks[0].get('message') or '')) if marks else ('passed','')
    if not out:raise RuntimeError(f'No cases in {name}')
    return out

def compare():
    base,head=cases('base.xml'),cases('head.xml')
    new=sorted(set(head)-set(base))
    return {
        'base_counts':dict(Counter(v[0] for v in base.values())),
        'head_counts':dict(Counter(v[0] for v in head.values())),
        'base_cases':len(base),'head_cases':len(head),
        'failing_on_base':{k:v[1] for k,v in base.items() if v[0] in ('failure','error')},
        'failing_on_head':{k:v[1] for k,v in head.items() if v[0] in ('failure','error')},
        'regressed':sorted(k for k,v in base.items() if v[0]=='passed' and k in head and head[k][0]!='passed'),
        'missing_on_head':sorted(set(base)-set(head)),
        'changed_outcomes':{k:{'base':v[0],'head':head[k][0]} for k,v in base.items() if k in head and v[0]!=head[k][0]},
        'new_cases':len(new),
        'new_not_passing':{k:head[k] for k in new if head[k][0] in ('failure','error')},
        'new_skipped':{k:head[k][1] for k in new if head[k][0]=='skipped'},
        'v01_compat':{k:v for k,v in head.items() if 'test_v01_compat' in k},
    }

def report(error=None,final=False):
    verdict='INCOMPLETE';sentence='The Linux comparison is in progress.'
    if error: sentence=f'The run stopped: {error}'
    if final and comparison:
        platform_skips=all(any(term in reason.lower() for term in ['windows','win32','powershell','junction']) for reason in comparison['new_skipped'].values())
        compat=bool(comparison['v01_compat']) and all(v[0]=='passed' for v in comparison['v01_compat'].values())
        dirty=any(r.get('status_before') or r.get('status_after') or r.get('status_final') for r in runs.values())
        fail=bool(comparison['regressed'] or comparison['missing_on_head'] or comparison['new_not_passing'] or not platform_skips or not compat or dirty)
        verdict='FAIL' if fail else 'PASS'
        if fail:sentence='The Linux comparison has a regression, missing case, unexplained skip, compatibility gap, or checkout mutation; see the evidence below.'
        else:
            n=len(comparison['failing_on_base'])
            sentence=f'No Linux regression relative to the base; the required test set remains red with {n} shared baseline failure(s).' if n else 'No Linux regression relative to the base, and both required test runs passed.'
    lines=[f'LINUX: {verdict} — {sentence}','','Date: 2026-10-06. Noncanonical verification evidence.','',
           '## Environment and exact targets','',
           f'- Base: `{BASE}`.',f'- Head pinned at start: `{HEAD}`.',
           f'- Non-document checkpoint: `{CHECKPOINT}`; Windows preflight diff exit 0.',
           '- Windows worktree was clean before receipt creation; Linux checkout status receipts are below.',
           f'- Linux root: `{ROOT}`; clones: `{ROOT}/base` and `{ROOT}/head`.',
           f'- Tested environment: `{ROOT}/venv`; uv-created managed Python 3.13, seeded pip, then `python -m pip install --upgrade pip` and `python -m pip install -r head/requirements-ci.txt`.',
           '- Same interpreter and installed dependencies for both stages. Setup commands and exit codes: `commands.txt` / `command-results.json`.',
           f'- Environment details: `{json.dumps(metadata,ensure_ascii=False)}`.',
           '- Exact dependency versions: `pip-freeze.txt` (when installation completes).','',
           '## Required test set','',
           '`python -m pytest -q -p no:cacheprovider packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded --junitxml=<stage.xml>`','',
           '| Stage | Passed | Failed | Errors | Skipped | Exit |','|---|---:|---:|---:|---:|---:|']
    for stage in ['base','head']:
        r=runs.get(stage)
        if r and (OUT/f'{stage}.xml').exists():
            counts=Counter(v[0] for v in cases(f'{stage}.xml').values())
            lines.append(f'| {stage} | {counts["passed"]} | {counts["failure"]} | {counts["error"]} | {counts["skipped"]} | {r["test_exit"]} |')
        else:lines.append(f'| {stage} | pending | pending | pending | pending | pending |')
    lines+=['','One known supersession test is deselected in each invocation, as in CI. XML test counts do not include deselection.','', '## Per-case findings','']
    if comparison:
        for title,key in [('Tests failing on base','failing_on_base'),('Tests failing on head','failing_on_head'),('Regressions (base pass no longer passes)','regressed'),('Missing on head','missing_on_head'),('Changed existing outcomes','changed_outcomes'),('New cases failing/erroring','new_not_passing'),('New cases skipped, with full reasons','new_skipped'),('v0.1 compatibility','v01_compat')]:
            lines += [f'### {title}','','```json',json.dumps(comparison[key],indent=2,ensure_ascii=False),'```','']
        lines += [f'New collected cases: **{comparison["new_cases"]}**. Full machine-readable comparison: `compare.json`.','']
    else:
        for stage in runs:
            if (OUT/f'{stage}.xml').exists():
                failed={k:v[1] for k,v in cases(f'{stage}.xml').items() if v[0] in ('failure','error')}
                lines += [f'Provisional {stage} failures:','```json',json.dumps(failed,indent=2),'```','']
        lines += ['The other stage and/or final comparison is still pending.','']
    lines+=['## Spec gate and checkout state','', '```json',json.dumps(runs,indent=2,ensure_ascii=False),'```','',
            'Both spec-gate output files and exact exit codes are retained. The Windows expectation is the same two missing Grok hooks and stale research_log.py entry, exit 1. A baseline failure or a nonzero spec gate is not relabelled green.','',
            '## Deviations and limits','',
            '- Two ordinary Linux clones were used instead of a clone plus linked worktree. Both retain complete Git history and valid Linux Git metadata; no tests run in /mnt/c.',
            '- HOME was left unchanged. FLOSS_AGENT_DIR, FLOSS_AUDIT_DIR, FLOSS_MCP_AUDIT_DIR, COORDINATION_ROOM_ROOT/LOG, and TMPDIR are set to fresh per-stage paths under the owned Linux root. PYTHONPATH and COORDINATION_ROOM_BOARD are unset. Overrides are recorded in runs.json.',
            '- Subprocess exit codes are captured directly instead of relying on the pytest-to-tee pipeline. Raw stdout/stderr and JUnit are retained byte for byte.',
            '- The comparison intentionally uses the head requirements for the base too. This verifies code differences under one current environment, not the historical base dependency resolution.',
            '- Ubuntu under WSL is a Linux verification environment, not a GitHub-hosted ubuntu-latest runner. Windows-only skips and every new skip are listed rather than counted as passes.',
            '- No source, test, plan, runtime configuration, or primary checkout changes; no fixes, live Windows daemon actions, push, pull, rebase, or PR. Only this receipt directory is authorized for the final project commit.',
            '- Linux clones and environment are retained for reruns. Expected heartbeat ticks may be written under the owned clone parent; checkout status does not establish that no external scratch files were created.',
            '- Not tested: advisory ARF suite, production deployment/rollback, live Hermes, load/soak, or Windows behaviour beyond the already existing receipts.','']
    if error:lines+=['## Execution interruption','','```text',str(error),'```','']
    write('REPORT.md','\n'.join(lines))

try:
    journal_line('Invocation: WSL Ubuntu system python3 run-linux.py <Linux root> <verified Windows bundle> <authorized receipt directory>')
    journal_line('HOME is not reassigned. Setup caches/installations are contained in the Linux root.')
    metadata.update(distribution=Path('/etc/os-release').read_text(),kernel=platform.release(),machine=platform.machine(),uid=os.getuid(),driver_python=sys.version)
    command(['git','clone','-b','feat/coordination-room-rebased',BUNDLE,ROOT/'head'],name='clone-head.txt',check=True)
    _,head=command(['git','rev-parse','HEAD'],cwd=ROOT/'head',check=True)
    assert head.strip()==HEAD,(head,HEAD)
    command(['git','diff','--exit-code',CHECKPOINT,HEAD,'--','.',':(exclude)docs'],cwd=ROOT/'head',name='checkpoint-diff.txt',check=True)
    command(['git','clone','--no-hardlinks','--no-checkout',ROOT/'head',ROOT/'base'],name='clone-base.txt',check=True)
    command(['git','checkout','--detach',BASE],cwd=ROOT/'base',name='checkout-base.txt',check=True)
    command(['git','cat-file','-e',BASE+'^{commit}'],cwd=ROOT/'head',check=True)
    command(['/home/kalis/.local/bin/uv','venv','--python','3.13','--seed',ROOT/'venv'],name='venv-create.txt',check=True)
    python=ROOT/'venv/bin/python'
    _,version=command([python,'--version'],check=True);metadata['tested_python']=version.strip()
    assert version.startswith('Python 3.13.'),version
    command([python,'-m','pip','install','--upgrade','pip'],name='pip-upgrade.txt',check=True)
    command([python,'-m','pip','install','-r',ROOT/'head/requirements-ci.txt'],name='dependency-install.txt',check=True)
    command([python,'-m','pip','freeze'],name='pip-freeze.txt',check=True)
    _,versions=command([python,'-c','import importlib.metadata,json; print(json.dumps({k:importlib.metadata.version(k) for k in ["mcp","pytest","pytest-asyncio","uvicorn","httpx"]}))'],check=True)
    metadata['versions']=json.loads(versions)
    save_json('environment.json',metadata);report()
    for stage in ['base','head']:
        clone=ROOT/stage;runtime=ROOT/'runtime'/stage;(runtime/'tmp').mkdir(parents=True)
        run_env=dict(env)
        run_env.update(FLOSS_AGENT_DIR=str(runtime/'agent'),FLOSS_AUDIT_DIR=str(runtime/'audit'),FLOSS_MCP_AUDIT_DIR=str(runtime/'audit'),
                       COORDINATION_ROOM_ROOT=str(runtime/'room'),COORDINATION_ROOM_LOG=str(runtime/'room/events.jsonl'),TMPDIR=str(runtime/'tmp'))
        overrides={k:run_env.get(k) for k in ['PYTHONPATH','COORDINATION_ROOM_BOARD','PYTHONDONTWRITEBYTECODE','FLOSS_AGENT_DIR','FLOSS_AUDIT_DIR','FLOSS_MCP_AUDIT_DIR','COORDINATION_ROOM_ROOT','COORDINATION_ROOM_LOG','TMPDIR']}
        journal_line('Test environment overrides: '+json.dumps(overrides))
        _,status=command(['git','status','--porcelain=v1','--untracked-files=all'],cwd=clone,name=f'{stage}-status-before.txt',check=True)
        assert not status.strip(),f'{stage} checkout is dirty before tests: {status}'
        cmd=[python,'-m','pytest','-q','-p','no:cacheprovider','packages/','tests/','scripts/tests/','--deselect',
             'scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded',f'--junitxml={OUT}/{stage}.xml']
        print(f'RUN {stage}',flush=True)
        code,output=command(cmd,cwd=clone,name=f'{stage}.txt',run_env=run_env)
        if (OUT/f'{stage}.xml').exists():mirror(f'{stage}.xml')
        _,after=command(['git','status','--porcelain=v1','--untracked-files=all'],cwd=clone,name=f'{stage}-status-after.txt',check=True)
        runs[stage]={'test_exit':code,'status_before':status,'status_after':after,'environment_overrides':overrides,'summary':output.strip().splitlines()[-1] if output.strip() else ''}
        save_json('runs.json',runs);report()
        print(stage,runs[stage]['summary'],flush=True)
    comparison=compare();save_json('compare.json',comparison);report()
    for stage in ['base','head']:
        code,output=command([python,'scripts/spec_gate.py','--check'],cwd=ROOT/stage,name=f'{stage}-spec-gate.txt')
        _,status=command(['git','status','--porcelain=v1','--untracked-files=all'],cwd=ROOT/stage,name=f'{stage}-status-final.txt',check=True)
        runs[stage].update(spec_gate_exit=code,spec_gate_output=output,status_final=status)
    save_json('runs.json',runs)
    save_json('spec-gate-comparison.json',{'same_output':runs['base']['spec_gate_output']==runs['head']['spec_gate_output'],'base_exit':runs['base']['spec_gate_exit'],'head_exit':runs['head']['spec_gate_exit']})
    report(final=True)
    print((OUT/'REPORT.md').read_text().splitlines()[0],flush=True)
except Exception as error:
    write('runner-error.txt',traceback.format_exc())
    report(error=repr(error))
    print('INCOMPLETE',repr(error),flush=True)
    raise
