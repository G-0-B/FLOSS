from pathlib import Path
import contextlib,io,os,sys,json,subprocess,importlib,threading,hashlib,stat,time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
FIX=ROOT/'fixtures-exact'
PACKET=Path(r'C:\~shit\FLOSS\docs\reviews\2026-10-02-room-board-v1\round-3')
WORK=ROOT/('adversarial-'+str(time.time_ns()));WORK.mkdir()
sys.path.insert(0,str(FIX/'proposal'))
from packages.coordination_room.room import CoordinationRoom,check_board_path
from packages.coordination_room.board import write_board
results={}
def room(name):
 p=WORK/name;p.mkdir()
 return p,CoordinationRoom(p,p/'events.jsonl',p/'BOARD.md')
def seqs(p):return [json.loads(l)['seq'] for l in (p/'events.jsonl').read_text(encoding='utf-8').split('\n') if l]
def record(name,**data):results[name]=data;print(name,json.dumps(data,ensure_ascii=True),flush=True)

p,r=room('old-stage-link');r.broadcast('a','seed');os.link(p/'events.jsonl',p/'BOARD.md.tmp')
reply=r.broadcast('a','safe')
record('old-stage-hardlink',reply=reply,seqs=seqs(p),still_same_file=os.path.samefile(p/'events.jsonl',p/'BOARD.md.tmp'))

p,r=room('late-board-link');r.broadcast('a','seed');(p/'BOARD.md').rename(p/'BOARD.before.md');os.link(p/'events.jsonl',p/'BOARD.md')
try:check_board_path(p/'events.jsonl',p/'BOARD.md')
except ValueError:refused=True
else:refused=False
reply=r.broadcast('a','safe')
record('late-board-hardlink',construction_guard_refused=refused,reply=reply,seqs=seqs(p),board_is_markdown=(p/'BOARD.md').read_text().startswith('# Coordination board'))

for kind in ['open-board','open-log-with-linked-board','readonly-board']:
 p,r=room(kind);r.broadcast('a','seed');before=(p/'BOARD.md').read_bytes()
 if kind=='open-log-with-linked-board':
  (p/'BOARD.md').rename(p/'BOARD.before.md');os.link(p/'events.jsonl',p/'BOARD.md');before=(p/'BOARD.md').read_bytes()
 if kind=='readonly-board':os.chmod(p/'BOARD.md',stat.S_IREAD)
 err=io.StringIO()
 with contextlib.ExitStack() as stack:
  if kind.startswith('open-'):stack.enter_context((p/('events.jsonl' if kind=='open-log-with-linked-board' else 'BOARD.md')).open('r',encoding='utf-8'))
  with contextlib.redirect_stderr(err):reply=r.broadcast('a','second')
 record(kind,reply=reply,seqs=seqs(p),board_changed=(p/'BOARD.md').read_bytes()!=before,stages=[x.name for x in p.glob('.BOARD.md.*.tmp')],stderr=err.getvalue())

# A directory alias changed AFTER the constructor is different from a leaf hard link.
p=WORK/'parent-rebind';p.mkdir();real=p/'real';real.mkdir();alias=p/'alias';alias.mkdir()
r=CoordinationRoom(p,real/'events.jsonl',alias/'events.jsonl');r.broadcast('a','seed')
alias.rename(p/'alias.preserved')
d=subprocess.run(['cmd.exe','/d','/c','mklink','/J',str(alias),str(real)],capture_output=True,text=True)
if d.returncode==0:
 reply=r.broadcast('a','after-parent-rebind')
 raw=(real/'events.jsonl').read_text(encoding='utf-8')
 try:r.read();read_error=None
 except Exception as e:read_error=type(e).__name__
 record('parent-rebind',junction=d.stdout.strip(),reply=reply,first_line=raw.split('\n')[0],next_read_error=read_error)
else:record('parent-rebind',blocked=d.stdout+d.stderr)

# Rollback checkpoint equals the pinned old room, while retaining scoped scripts.
old=FIX/'rollback'/'packages'/'coordination_room';base=FIX/'baseline'/'packages'/'coordination_room'
same=all((base/p.relative_to(old)).read_bytes()==p.read_bytes() for p in old.rglob('*') if p.is_file())
p,r=room('rollback-log');r.claim('alice','x.py',intent='test');r.broadcast('alice','v0.2',topic='inquiries')
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH='',COORDINATION_ROOM_ROOT=str(p),COORDINATION_ROOM_LOG=str(p/'events.jsonl'),COORDINATION_ROOM_BOARD=str(p/'BOARD.md'),FLOSS_AGENT_DIR=str(p/'agent'),FLOSS_AUDIT_DIR=str(p/'audit'))
code="from pathlib import Path;import json,os;from packages.coordination_room.room import CoordinationRoom;r=CoordinationRoom(Path(os.environ['COORDINATION_ROOM_ROOT']),Path(os.environ['COORDINATION_ROOM_LOG']));print(json.dumps({'state':r.state(),'post':r.broadcast('operator','rolled back to v0.1'),'seqs':[x['seq'] for x in r.read()]}))"
d=subprocess.run([sys.executable,'-c',code],cwd=FIX/'rollback',env=env,capture_output=True,text=True)
record('rollback',room_bytes_equal_base=same,rc=d.returncode,stdout=d.stdout,stderr=d.stderr)

p=WORK/'lazy';p.mkdir()
os.environ.update(COORDINATION_ROOM_ROOT=str(p),COORDINATION_ROOM_LOG=str(p/'events.jsonl'),COORDINATION_ROOM_BOARD=str(p/'BOARD.md'),FLOSS_AGENT_DIR=str(p/'agent'),FLOSS_AUDIT_DIR=str(p/'audit'))
import packages.coordination_room.server as server
import packages.mcp_daemon as daemon
record('lazy-import',tools_unbuilt=server._tools_instance is None,files=[x.name for x in p.iterdir()])
calls=[];original=server.CoordinationRoomTools
def build(*a,**kw):
 calls.append(threading.get_ident());time.sleep(.01);return original(*a,**kw)
with patch.object(server,'CoordinationRoomTools',build):
 with ThreadPoolExecutor(max_workers=32) as pool:instances=list(pool.map(lambda _:id(server._tools()),range(64)))
record('lazy-concurrency',constructors=len(calls),unique_instances=len(set(instances)))
server._tools_instance=None
(p/'events.jsonl').write_text('{torn',encoding='utf-8')
failures=[]
for _ in range(2):
 try:server.room_state()
 except Exception as e:failures.append(type(e).__name__)
cached=server._tools_instance is not None
(p/'events.jsonl').rename(p/'events.torn.preserved')
retry=json.loads(server.room_broadcast('a','after repair'))
record('lazy-first-failure',failures=failures,cached_failed_instance=cached,retry=retry)

# Exercise actual run_http_daemon/claim_singleton ordering, with only the serving call replaced.
server._tools_instance=None
previous=CoordinationRoom(p,p/'events.jsonl');previous.claim('old','held.py')
order=[];oldload=importlib.import_module('packages.coordination_room.log').EventLog.load
def observed_load(self):order.append('read');return oldload(self)
def claimed(filename):order.append('claim');return True
def serve(**kwargs):order.append('serve');record('takeover-state',state=json.loads(server.room_state()),conflict=json.loads(server.room_claim('new','held.py')))
with patch.object(daemon,'claim_singleton',claimed),patch.object(server.mcp,'run',serve),patch('packages.coordination_room.log.EventLog.load',observed_load):
 daemon.run_http_daemon(server.mcp,pid_filename='coordination_room.pid',port=19994)
record('ownership-order',order=order)
# Actual singleton claim is safe inside this child process's scratch agent dir.
owned=daemon.claim_singleton('coordination_room.pid')
server._tools_instance=None
(p/'events.jsonl').rename(p/'events.valid.preserved');(p/'events.jsonl').write_text('{torn',encoding='utf-8')
try:server.room_state()
except Exception as e:failed=type(e).__name__
record('failed-first-call-slot',claimed=owned,error=failed,pid_record_retained=(p/'agent'/'coordination_room.pid').exists(),cached=server._tools_instance is not None)
p,r=room('capture-stop-window');r.broadcast('old','captured')
captured=r.state()['last_seq'];r.broadcast('old','after capture before stop')
new=CoordinationRoom(p,p/'events.jsonl',p/'BOARD.md')
record('deployment-capture-window',captured=captured,after_stopped_owner=new.state()['last_seq'],step5_equality_passes=captured==new.state()['last_seq'])
(PACKET/'adversarial-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('WORK',WORK)
