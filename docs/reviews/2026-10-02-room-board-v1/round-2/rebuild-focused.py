from pathlib import Path
import subprocess,json,hashlib,sys,tempfile
repo=Path(r'C:\~shit\FLOSS')
packet=Path(__file__).resolve().parent
out=Path(tempfile.mkdtemp(prefix='room-board-r2-rebuild-'))
plan=packet/'plan-revision-2.md'
ls=plan.read_text(encoding='utf-8').split('\n')
assert hashlib.sha256(plan.read_bytes()).hexdigest()=='6dabb8e6a6ef9f353af7d5f52f2765cf63746a34f69a493e8e7019be635ca635'
root=out/'FLOSS'
root.mkdir(parents=True,exist_ok=True)
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
def extract(ref,*prefixes):
    for name in git('ls-tree','-r','--name-only',ref,'--',*prefixes).decode().splitlines():
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(git('show',f'{ref}:{name}'))
extract('4aab13e30f3c2960da787b47c90926256b4b5b73','packages/coordination_room','packages/mcp_daemon.py')
extract('225287c2ed310158a3f699688447db2964e425b2','packages/a2a_mesh')
blocks={
'docs/specs/coordination-room.spec.md':(181,265),
'docs/specs/coordination-room.schema.json':(271,331),
'packages/coordination_room/evidence.py':(510,595),
'packages/coordination_room/board.py':(804,965),
'packages/coordination_room/room.py':(1423,1624),
'packages/coordination_room/gateway.py':(1630,1719),
'packages/coordination_room/tests/test_evidence.py':(384,499),
'packages/coordination_room/tests/test_board.py':(628,793),
'packages/coordination_room/tests/test_message_board.py':(1000,1237),
'packages/coordination_room/tests/test_gateway_board.py':(1241,1329),
'packages/coordination_room/tests/test_schema.py':(1333,1412),
'packages/coordination_room/tests/test_server_tools.py':(1762,1862),
'packages/coordination_room/tests/test_server_http.py':(1866,1974),
'packages/a2a_mesh/room_bridge.py':(2622,2910),
'packages/a2a_mesh/tests/test_room_bridge_parse.py':(2274,2362),
'packages/a2a_mesh/tests/test_room_bridge_pair.py':(2366,2486),
'packages/a2a_mesh/tests/test_room_bridge_invariants.py':(2490,2532),
'packages/a2a_mesh/tests/test_room_bridge_e2e.py':(2536,2611),
'packages/coordination_room/README.md':(2134,2145),
}
for name,(a,b) in blocks.items():
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('\n'.join(ls[a-1:b])+'\n',encoding='utf-8')
p=root/'packages/coordination_room/server.py';src=git('show','4aab13e30f3c2960da787b47c90926256b4b5b73:packages/coordination_room/server.py').decode()
for a,b,c,d in [(1987,1987,1993,2000),(2006,2017,2023,2041),(2047,2054,2060,2097),(2103,2103,2109,2109),(2115,2117,2123,2126)]:
    old='\n'.join(ls[a-1:b]);new='\n'.join(ls[c-1:d]);assert src.count(old)==1,(a,src.count(old));src=src.replace(old,new)
p.write_text(src,encoding='utf-8')
(out/'extraction-r2.json').write_text(json.dumps({'plan_sha256':hashlib.sha256(plan.read_bytes()).hexdigest(),'source_lines':blocks,'base':'4aab13e30f3c2960da787b47c90926256b4b5b73','a2a_base':'225287c2ed310158a3f699688447db2964e425b2'},indent=2),encoding='utf-8')
print(root)
