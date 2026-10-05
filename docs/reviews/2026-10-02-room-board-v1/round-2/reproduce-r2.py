"""Read proposed modules from --source-root; all mutation is in a new temp directory."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

p=argparse.ArgumentParser()
p.add_argument('--source-root', type=Path, required=True)
p.add_argument('--git-repo', type=Path, default=Path(r'C:\~shit\FLOSS'))
a=p.parse_args()
sys.path.insert(0,str(a.source_root.resolve()))
from packages.coordination_room.room import CoordinationRoom
from packages.coordination_room.log import EventLog
root=Path(tempfile.mkdtemp(prefix='room-board-r2-repro-'))
print('Isolated fixtures:',root)

def case(name):
    s=root/name;s.mkdir();return s

s=case('hardlink-stage');log=s/'events.jsonl';board=s/'BOARD.md';stage=s/'BOARD.md.tmp'
EventLog(log).append('broadcast','a',text='keep me')
os.link(log,stage)
print('R2-01 hardlink samefile=',os.path.samefile(log,stage))
r=CoordinationRoom(s,log,board)
result=r.broadcast('b','new post')
print('R2-01 broadcast=',result,'log_first_line=',repr(log.read_text(encoding='utf-8').split('\n')[0]))
try:r.read()
except Exception as e:print('R2-01 next_read=',type(e).__name__)

s=case('snapshot-before-guard');log=s/'events.jsonl'
old=CoordinationRoom(s,log);old.broadcast('old','seed')
with patch.dict(os.environ,{'COORDINATION_ROOM_ROOT':str(s),'COORDINATION_ROOM_LOG':str(log),'COORDINATION_ROOM_BOARD':str(s/'BOARD.md'),'FLOSS_AUDIT_DIR':str(s/'audit')}):
    from packages.coordination_room import server
old.broadcast('old','final event before exit')
server.room_broadcast(agent_id='new',text='first event after acquiring slot')
print('I1 simulated takeover seqs=',[e['seq'] for e in EventLog(log).load()])

s=case('rollback-state');log=s/'events.jsonl'
r=CoordinationRoom(s,log,s/'BOARD.md');r.claim('a','x.py',intent='work');r.broadcast('a','x',topic='news')
code=subprocess.check_output(['git','-C',str(a.git_repo),'show','4aab13e30f3c2960da787b47c90926256b4b5b73:packages/coordination_room/room.py']).decode()
ns={'__name__':'baseline_room_review'}
exec(compile(code,'baseline_room.py','exec'),ns)
old=ns['CoordinationRoom'](s,log)
print('R2-04 rollback state=',json.dumps(old.state()))
print('R2-04 missing_required_fields=',sorted({'root','log','board'}-old.state().keys()))
print('R2-04 rollback append=',old.broadcast('a','rollback continued'),'all_seqs=',[e['seq'] for e in old.read()])
