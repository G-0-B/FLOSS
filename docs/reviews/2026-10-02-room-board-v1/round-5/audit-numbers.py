"""Changed numeric surface: parser matrix plus official A2A client over HTTP."""
from pathlib import Path
import asyncio, dataclasses, hashlib, json, os, socket, sys, threading, time

P=Path(__file__).resolve().parent
W=Path(json.loads((P/'extraction-r5.json').read_text())['workspace']).parent
runtime=W/'number-audit'; runtime.mkdir(exist_ok=True)
os.environ.pop('PYTHONPATH',None)
os.environ.update(PYTHONDONTWRITEBYTECODE='1',FLOSS_AGENT_DIR=str(runtime/'agent'),FLOSS_AUDIT_DIR=str(runtime/'audit'),FLOSS_MCP_AUDIT_DIR=str(runtime/'audit'),COORDINATION_ROOM_ROOT=str(runtime/'room'),COORDINATION_ROOM_LOG=str(runtime/'room/events.jsonl'),COORDINATION_ROOM_BOARD=str(runtime/'room/BOARD.md'))
sys.path.insert(0,str(W/'fixtures-exact/proposal'))
import httpx, uvicorn
from packages.a2a_mesh.room_bridge import parse_command, CommandError, build_app, INTEGER_MAX
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import get_artifact_text, new_text_message
from a2a.types import Role, SendMessageRequest

results={'integer_max':INTEGER_MAX,'python_digit_limit':sys.get_int_max_str_digits(),'parser':[],'http':[]}
cases=[]
values=[('fraction','1.9'),('whole-float','1.0'),('true','true'),('false','false'),('positive-inf','1e999'),('negative-inf','-1e999'),('nan','NaN'),('exponent-integer','1e3'),('zero','0'),('negative-zero','-0'),('negative','-1'),('one','1'),('max-minus-one',str(INTEGER_MAX-1)),('max',str(INTEGER_MAX)),('max-plus-one',str(INTEGER_MAX+1)),('negative-max',str(-INTEGER_MAX)),('negative-overflow',str(-INTEGER_MAX-1)),('empty-string','""'),('decimal-string','"4"'),('plus-string','"+4"'),('minus-string','"-4"'),('space-string','" 4"'),('trailing-space','"4 "'),('leading-zero','"0004"'),('16-zeroes','"'+'0'*16+'"'),('17-zeroes','"'+'0'*17+'"'),('max-string','"'+str(INTEGER_MAX)+'"'),('max-overflow-string','"'+str(INTEGER_MAX+1)+'"'),('arabic-digit',json.dumps('٤')),('fullwidth-digit',json.dumps('４')),('unicode-minus',json.dumps('−4')),('superscript',json.dumps('²')),('underscore','"1_0"'),('list','[4]'),('object','{"n":4}'),('null','null'),('4300-digit-int','9'*4300),('4301-digit-int','9'*4301),('4301-digit-negative','-'+'9'*4301),('10000-digit-int','9'*10000),('10000-digit-string','"'+'9'*10000+'"')]
for field in ['reply_to','since_seq','limit']:
    for label,value in values:
        op='post' if field=='reply_to' else 'read'
        raw='{"op":"'+op+'","text":"x","'+field+'":'+value+'}'
        cases.append((field+'/'+label,raw))
for value in ['0','1','0004','+1','-1','1.0','1e3','٤','４',str(INTEGER_MAX),str(INTEGER_MAX+1),'9'*4301,'0'*17]:
    cases.append(('text-since/'+(value if len(value)<25 else str(len(value))+'-digits'),'read since='+value))
cases += [('text-read-topic','read #announcements since=4'),('text-read-default','read'),('text-read-trailing-whitespace','read since=4\n'),('text-read-split','read since=4 more'),('text-post-is-text','post #announcements 1e999'),('json-plus-number','{"op":"read","since_seq":+4}')]

def input_record(label,raw):
    return {'case':label,'input':raw if len(raw)<300 else raw[:65]+'... <see script>','input_length':len(raw),'input_sha256':hashlib.sha256(raw.encode()).hexdigest()}

for label,raw in cases:
    record=input_record(label,raw)
    try: record.update(outcome='accepted',command=dataclasses.asdict(parse_command(raw)))
    except CommandError as exc: record.update(outcome='CommandError',message=str(exc))
    except Exception as exc: record.update(outcome=type(exc).__name__,message=str(exc))
    results['parser'].append(record)

class Recorder:
    def __init__(self): self.calls=[]
    async def call(self,tool,arguments):
        self.calls.append({'tool':tool,'arguments':arguments})
        return {'ok':True,'seq':7,'events':[],'topic':'announcements'}

room=Recorder()
sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
assert port not in {7331,7332,7333,7334,7335,20128}
server=uvicorn.Server(uvicorn.Config(build_app('127.0.0.1',port,room),log_level='warning'))
thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
deadline=time.monotonic()+10
while not server.started:
    assert time.monotonic()<deadline,'scratch HTTP failed to start'
    time.sleep(.05)

async def check_http():
    async with httpx.AsyncClient() as h:
        card=await A2ACardResolver(httpx_client=h,base_url=f'http://127.0.0.1:{port}').get_agent_card()
    client=await create_client(agent=card,client_config=ClientConfig(streaming=False))
    try:
        for label,raw in cases:
            room.calls.clear(); record=input_record(label,raw)
            try:
                request=SendMessageRequest(message=new_text_message(raw,role=Role.ROLE_USER))
                chunks=[];artifacts=[];states=[]
                async for chunk in client.send_message(request):
                    kind=chunk.WhichOneof('payload');chunks.append(kind)
                    if kind=='task':
                        artifacts += [get_artifact_text(a) for a in chunk.task.artifacts]
                        states.append(int(chunk.task.status.state))
                    elif kind=='artifact_update': artifacts.append(get_artifact_text(chunk.artifact_update.artifact))
                record.update(outcome='response',artifacts=artifacts,states=states,chunks=chunks)
            except Exception as exc:
                record.update(outcome=type(exc).__name__,message=str(exc))
            record['room_calls']=list(room.calls)
            results['http'].append(record)
            (P/'number-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    finally: await client.close()

try: asyncio.run(check_http())
finally:
    server.should_exit=True;thread.join(timeout=10);sock.close()
    assert not thread.is_alive()
results['port']=port
results['summary']={'parser_cases':len(results['parser']),'http_cases':len(results['http']),'parser_unexpected':[r['case'] for r in results['parser'] if r['outcome'] not in ['accepted','CommandError']],'http_internal_errors':[r['case'] for r in results['http'] if r['outcome']!='response']}
(P/'number-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results['summary'],indent=2))
