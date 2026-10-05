"""Scratch A2A boundary test; fake room only, no room daemon or real log."""
from pathlib import Path
import asyncio, json, sys, threading, time
import httpx, uvicorn

P=Path(__file__).resolve().parent
fix=Path(json.loads((P/'extraction-r4.json').read_text())['workspace'])
sys.path.insert(0,str(fix/'proposal'))
from packages.a2a_mesh.room_bridge import build_app
from packages.a2a_mesh.client import _send_hello_async

class Recorder:
    def __init__(self): self.calls=[]
    async def call(self,tool,arguments):
        self.calls.append({'tool':tool,'arguments':arguments})
        return {'ok':True,'seq':2,'topic':'general'}

room=Recorder()
server=uvicorn.Server(uvicorn.Config(build_app('127.0.0.1',19998,room),host='127.0.0.1',port=19998,log_level='warning'))
thread=threading.Thread(target=server.run,daemon=True);thread.start()
deadline=time.monotonic()+10
while time.monotonic()<deadline:
    try:
        httpx.get('http://127.0.0.1:19998/.well-known/agent-card.json',timeout=.3).raise_for_status();break
    except httpx.HTTPError: time.sleep(.1)
else: raise RuntimeError('Scratch bridge did not start')
results=[]
try:
    for value in ['1.9','true','1e999','"abc"']:
        room.calls.clear()
        text='{"op":"post","text":"reply","reply_to":'+value+'}'
        try:
            response=asyncio.run(asyncio.wait_for(_send_hello_async('http://127.0.0.1:19998',text),timeout=10))
            result={'response':response}
        except Exception as exc:
            result={'exception':type(exc).__name__,'message':str(exc)}
        results.append({'input':text,'room_calls':list(room.calls),**result})
finally:
    server.should_exit=True;thread.join(timeout=5)
    assert not thread.is_alive()
(P/'bridge-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
