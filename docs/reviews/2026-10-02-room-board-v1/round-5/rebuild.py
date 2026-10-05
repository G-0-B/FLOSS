from pathlib import Path
import hashlib, json, subprocess, zipfile, shutil
import tempfile
ROOT = Path('C:\\Users\\kalis\\AppData\\Local\\Temp\\codex-room-board-r5-20261004-042545\\fixtures-exact')
ROOT.mkdir(exist_ok=True)
PACKET = Path('C:\\~shit\\FLOSS\\docs\\reviews\\2026-10-02-room-board-v1\\round-5')
REPO = Path('C:\\~shit\\FLOSS')
BASE = '4aab13e30f3c2960da787b47c90926256b4b5b73'
A2A = '225287c2ed310158a3f699688447db2964e425b2'
PLAN = PACKET / 'plan-revision-5.md'
SHA = 'f2a8392e874a6f90c6818657fccc0050625da518fb09860dff0d58c68b8d1752'
assert hashlib.sha256(PLAN.read_bytes()).hexdigest() == SHA
lines = PLAN.read_text(encoding='utf-8').split('\n')

def git(*args):
    return subprocess.check_output(['git', '-c', 'safe.directory=C:/~shit/FLOSS', '-C', str(REPO), *args])

def body(a, b):
    return '\n'.join(lines[a - 1:b]) + '\n'
ops = []
baseline = ROOT / 'baseline'
proposal = ROOT / 'proposal'
assert not baseline.exists() and (not proposal.exists())
archive = ROOT / 'base.zip'
archive.write_bytes(git('archive', '--format=zip', BASE))
with zipfile.ZipFile(archive) as z:
    z.extractall(baseline)
shutil.copytree(baseline, proposal)

def put(path, a, b):
    p = proposal / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(body(a, b).encode('utf-8'))
    ops.append({'action': 'body', 'path': path, 'lines': [a, b]})

def replace(path, a, b, c, d):
    p = proposal / path
    raw = p.read_bytes()
    newline = '\n'
    old = body(a, b).rstrip('\n').encode('utf-8')
    if old not in raw:
        newline = '\r\n'
        old = old.replace(b'\n', b'\r\n')
    new = body(c, d).rstrip('\n').replace('\n', newline).encode('utf-8')
    assert raw.count(old) == 1, (path, a, raw.count(old))
    p.write_bytes(raw.replace(old, new))
    ops.append({'action': 'replace', 'path': path, 'old': [a, b], 'new': [c, d]})

def pairs(path, lo, hi):
    import re
    section = '\n'.join(lines[lo - 1:hi])
    matches = list(re.finditer('^```(?:powershell|python)\\n(.*?)^```$', section, re.M | re.S))
    assert len(matches) % 2 == 0
    for first, second in zip(matches[::2], matches[1::2]):
        a = lo + section[:first.start(1)].count('\n')
        b = a + first.group(1).count('\n') - 1
        c = lo + section[:second.start(1)].count('\n')
        d = c + second.group(1).count('\n') - 1
        replace(path, a, b, c, d)
put('docs/specs/coordination-room.spec.md', 242, 337)
put('docs/specs/coordination-room.schema.json', 343, 403)
replace('docs/specs/spec-registry.json', 409, 409, 415, 415)
put('scripts/tests/test_daemon_scope.py', 462, 626)
pairs('scripts/start_mcp_daemons.ps1', 641, 783)
pairs('scripts/stop_mcp_daemons.ps1', 789, 873)
rollback = ROOT / 'rollback'
shutil.copytree(proposal, rollback)
for path, a, b in [('packages/coordination_room/tests/test_evidence.py', 926, 1041), ('packages/coordination_room/evidence.py', 1055, 1140), ('packages/coordination_room/tests/test_board.py', 1176, 1362), ('packages/coordination_room/board.py', 1376, 1541), ('packages/coordination_room/tests/test_message_board.py', 1579, 1868), ('packages/coordination_room/tests/test_gateway_board.py', 1872, 1960), ('packages/coordination_room/tests/test_schema.py', 1964, 2043), ('packages/coordination_room/room.py', 2057, 2274), ('packages/coordination_room/gateway.py', 2280, 2369), ('packages/coordination_room/tests/test_server_tools.py', 2421, 2539), ('packages/coordination_room/tests/test_server_http.py', 2543, 2651), ('packages/coordination_room/server.py', 2665, 2850), ('packages/coordination_room/README.md', 2858, 2869)]:
    put(path, a, b)
p = proposal / 'requirements-ci.txt'
raw = p.read_bytes()
assert raw.count(b'\nmcp\n') == 1
p.write_bytes(raw.replace(b'\nmcp\n', b'\nmcp>=1.27,<2\n'))
ops.append({'action': 'replace-line', 'path': 'requirements-ci.txt', 'old': 'mcp', 'new': 'mcp>=1.27,<2'})
for a, b, c, d in [(2877, 2881, 2887, 2893), (2899, 2899, 2905, 2905), (2911, 2911, 2917, 2917)]:
    replace('docs/agent-memory/project/coordination-room-v0.md', a, b, c, d)
phase1 = ROOT / 'phase1'
shutil.copytree(proposal, phase1)
for name in git('ls-tree', '-r', '--name-only', A2A, '--', 'packages/a2a_mesh', 'docs/research/2026-08-29-a2a-harness-mesh-research.md', 'docs/superpowers/plans/2026-08-29-a2a-harness-mesh.md').decode().splitlines():
    p = proposal / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(git('show', f'{A2A}:{name}'))
    ops.append({'action': 'git-show', 'path': name, 'commit': A2A})
p = proposal / 'requirements-ci.txt'
base_reqs = git('show', f'{BASE}:requirements-ci.txt')
a2a_reqs = git('show', f'{A2A}:requirements-ci.txt')
assert a2a_reqs.startswith(base_reqs)
p.write_bytes(p.read_bytes() + a2a_reqs[len(base_reqs):])
ops.append({'action': 'merge-append', 'path': 'requirements-ci.txt', 'commit': A2A})
for path, a, b in [('packages/a2a_mesh/tests/test_room_bridge_parse.py', 3002, 3127), ('packages/a2a_mesh/tests/test_room_bridge_pair.py', 3131, 3268), ('packages/a2a_mesh/tests/test_room_bridge_invariants.py', 3272, 3314), ('packages/a2a_mesh/tests/test_room_bridge_e2e.py', 3318, 3393), ('packages/a2a_mesh/room_bridge.py', 3407, 3719)]:
    put(path, a, b)
pairs('scripts/tests/test_daemon_scope.py', 3767, 3810)
pairs('scripts/start_mcp_daemons.ps1', 3824, 3867)
pairs('scripts/stop_mcp_daemons.ps1', 3873, 3910)
replace('docs/agent-memory/project/coordination-room-v0.md', 3927, 3927, 3933, 3933)

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
manifest = {'plan_sha256': SHA, 'plan_lines': len(lines), 'base': BASE, 'a2a_base': A2A, 'workspace': str(ROOT), 'ops': ops, 'stages': {}}
for name, folder in [('baseline', baseline), ('rollback', rollback), ('phase1', phase1), ('proposal', proposal)]:
    manifest['stages'][name] = {str(p.relative_to(folder)).replace('\\', '/'): digest(p) for p in folder.rglob('*') if p.is_file()}
(PACKET / 'extraction-r5.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps({'roots': [str(x) for x in [baseline, rollback, phase1, proposal]], 'operations': len(ops), 'file_counts': {k: len(v) for k, v in manifest['stages'].items()}}, indent=2))
