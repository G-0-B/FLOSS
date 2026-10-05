from pathlib import Path
import os,sys,subprocess,json,time

ROOT=Path(__file__).resolve().parent
PACKET=Path(r'C:\~shit\FLOSS\docs\reviews\2026-10-02-room-board-v1\round-3')
FIX=ROOT/'fixtures-exact'
env=dict(os.environ)
env.pop('PYTHONPATH',None);env['PYTHONDONTWRITEBYTECODE']='1'
env['PYTHONIOENCODING']='utf-8'
records=[]
for stage in sys.argv[1:] or ['baseline','phase1','proposal']:
    command=[sys.executable,'-m','pytest','-q','-p','no:cacheprovider','packages/','tests/','scripts/tests/','--deselect','scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded',f'--junitxml={PACKET}/{stage}-green.xml']
    print('RUN',stage,flush=True);start=time.monotonic()
    done=subprocess.run(command,cwd=FIX/stage,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (PACKET/f'{stage}-green.txt').write_bytes(done.stdout)
    record={'stage':stage,'command':command,'cwd':str(FIX/stage),'returncode':done.returncode,'elapsed':time.monotonic()-start,'env':{k:env.get(k) for k in ['PYTHONPATH','PYTHONDONTWRITEBYTECODE','FLOSS_AGENT_DIR','FLOSS_AUDIT_DIR','COORDINATION_ROOM_ROOT','COORDINATION_ROOM_LOG','COORDINATION_ROOM_BOARD','TEMP']}}
    records.append(record)
    (PACKET/'green-runs.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print(done.stdout.decode('utf-8',errors='replace')[-3500:],flush=True)
