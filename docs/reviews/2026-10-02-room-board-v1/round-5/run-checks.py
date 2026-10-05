"""Audit-only paired suite; all runtime paths and subprocess ports are scratch."""
from pathlib import Path
import os, sys, subprocess, json, time, importlib.metadata

PACKET = Path(__file__).resolve().parent
FIX = Path(json.loads((PACKET/'extraction-r5.json').read_text())['workspace'])
env = dict(os.environ)
env.pop('PYTHONPATH', None)
env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
records=[]
(PACKET/'dependencies.json').write_text(json.dumps({d.metadata['Name']:d.version for d in importlib.metadata.distributions()},indent=2))
for stage in sys.argv[1:] or ['baseline','phase1','proposal']:
    runtime=FIX.parent/'runtime'/stage
    (runtime/'tmp').mkdir(parents=True,exist_ok=True)
    env.update(FLOSS_AGENT_DIR=str(runtime/'agent'), FLOSS_AUDIT_DIR=str(runtime/'audit'),
               FLOSS_MCP_AUDIT_DIR=str(runtime/'audit'), COORDINATION_ROOM_ROOT=str(runtime/'room'),
               COORDINATION_ROOM_LOG=str(runtime/'room/events.jsonl'), COORDINATION_ROOM_BOARD=str(runtime/'room/BOARD.md'),
               TEMP=str(runtime/'tmp'), TMP=str(runtime/'tmp'))
    command=[sys.executable,'-m','pytest','-q','-p','no:cacheprovider','packages/','tests/','scripts/tests/',
             '--deselect','scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded',
             f'--junitxml={PACKET}/{stage}-green.xml']
    print('RUN',stage,flush=True); start=time.monotonic()
    done=subprocess.run(command,cwd=FIX/stage,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=1200)
    (PACKET/f'{stage}-green.txt').write_bytes(done.stdout)
    records.append({'stage':stage,'command':command,'cwd':str(FIX/stage),'returncode':done.returncode,
                    'elapsed':time.monotonic()-start,'env':{k:env.get(k) for k in ['PYTHONPATH','PYTHONDONTWRITEBYTECODE','FLOSS_AGENT_DIR','FLOSS_AUDIT_DIR','COORDINATION_ROOM_ROOT','COORDINATION_ROOM_LOG','COORDINATION_ROOM_BOARD','TEMP']}})
    (PACKET/'green-runs.json').write_text(json.dumps(records,indent=2))
    print(done.stdout.decode('utf-8',errors='replace')[-1700:],flush=True)
