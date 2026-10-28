"""Execute the pinned ownership predicate on actual POSIX pathlib."""
import ast
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'snapshot-42e4d05/scripts/materialize_shared_skill_surface.py'
body = ast.parse(SOURCE.read_text(encoding='utf-8'))
names = {'read_managed_marker', 'projection_owned_by', 'prune_stale_projections'}
nodes = [node for node in body.body if isinstance(node, ast.FunctionDef) and node.name in names]
namespace = {'Path': Path, 'Any': object, 'json': json, 'os': os,
             'MANAGED_BY': 'FLOSSI0ULLK shared skill surface', 'MANAGED_MARKER': '.flossi0ullk-managed.json'}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), 'exec'), namespace)
owner = ROOT / 'posix-fixture' / 'owner'
target = ROOT / 'posix-fixture' / 'shared'
child = target / 'bad-identity'
child.mkdir(parents=True)
(child / namespace['MANAGED_MARKER']).write_text(json.dumps({
    'managed_by': namespace['MANAGED_BY'], 'workspace_root': str(owner) + '\0',
    'source_path': str(owner / 'skills/bad-identity')}), encoding='utf-8')
print('PLATFORM', os.name)
print('EXECUTION', 'unaltered AST of three pinned production functions; no third-party imports needed')
try:
    outcome = namespace['prune_stale_projections']('shared', target, set(), check=True, dry_run=False, owner_root=owner)
except Exception as exc:
    print('POSIX_BAD_IDENTITY_PRUNE', type(exc).__name__, str(exc))
    assert isinstance(exc, ValueError) and 'null' in str(exc)
else:
    print('POSIX_BAD_IDENTITY_PRUNE', outcome)
    raise AssertionError('expected reproduced exception')
print('FIXTURE_UNMODIFIED', child.is_dir())
