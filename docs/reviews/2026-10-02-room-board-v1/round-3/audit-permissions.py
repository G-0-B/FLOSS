from pathlib import Path
import subprocess,sys,json,time
ROOT=Path(__file__).resolve().parent
PACKET=Path(r'C:\~shit\FLOSS\docs\reviews\2026-10-02-room-board-v1\round-3')
sys.path.insert(0,str(ROOT/'fixtures-exact'/'proposal'))
from packages.coordination_room.board import write_board
p=ROOT/('permission-case-'+str(time.time_ns()));p.mkdir();target=p/'BOARD.md';target.write_text('PRIVATE',encoding='utf-8')
cmd=[r'C:\apPs\PowerShell\7\pwsh.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'acl-helper.ps1'),'-Path',str(target)]
before=subprocess.run(cmd+['-Restrict'],capture_output=True,text=True)
write_board(target,[])
after=subprocess.run(cmd,capture_output=True,text=True)
r={'before':{'rc':before.returncode,'stdout':before.stdout,'stderr':before.stderr},'after':{'rc':after.returncode,'stdout':after.stdout,'stderr':after.stderr}}
(PACKET/'permissions-results.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
print(json.dumps(r,indent=2))
