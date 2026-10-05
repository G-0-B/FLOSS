"""Reproduce review cases against extracted proposed files only; preserve all fixtures."""
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timezone
import os
import runpy
import sys
import uuid
import json

ARTIFACTS = Path(__file__).resolve().parent
PROPOSED = ARTIFACTS / 'FLOSS'
sys.path.insert(0, str(PROPOSED))
from packages.coordination_room.room import CoordinationRoom
from packages.coordination_room.log import EventLog
from packages.coordination_room.board import render_board
from packages.coordination_room import room as room_module
import packages.mcp_daemon as daemon

cases = ARTIFACTS / ('reproduction-' + uuid.uuid4().hex[:8])
cases.mkdir()
print('Fixtures:', cases)

def case(name):
    result = cases / name
    result.mkdir()
    return result

s = case('duplicate-start')
EventLog(s / 'events.jsonl').append('broadcast', 'holder', text='existing event')
(s / 'BOARD.md').write_text('existing board owned by daemon\n', encoding='utf-8')
before = (s / 'BOARD.md').read_bytes()
with patch.dict(os.environ, {'COORDINATION_ROOM_ROOT': str(s), 'COORDINATION_ROOM_LOG': str(s / 'events.jsonl'), 'COORDINATION_ROOM_BOARD': str(s / 'BOARD.md'), 'FLOSS_AUDIT_DIR': str(s / 'audit')}):
    with patch.object(daemon, 'claim_singleton', return_value=False) as guard:
        try:
            runpy.run_module('packages.coordination_room.server', run_name='__main__')
        except SystemExit as exc:
            code = exc.code
print('B2 rejected-start exit=', code, 'guard_called=', guard.called, 'board_changed=', before != (s / 'BOARD.md').read_bytes())

s = case('board-log-alias')
log = s / 'events.jsonl'
EventLog(log).append('broadcast', 'holder', text='retain this')
CoordinationRoom(s, log, log)
print('B5 alias first_line=', repr(log.read_text(encoding='utf-8').split('\n')[0]))
try:
    CoordinationRoom(s, log, log)
except Exception as exc:
    print('B5 alias restart=', type(exc).__name__)

s = case('evidence-interleaving')
proof = s / 'proof.md'
proof.write_text('original', encoding='utf-8')
room = CoordinationRoom(s, s / 'events.jsonl')
resolve = room_module.resolve_all

def change_after_lookup(root, refs):
    result = resolve(root, refs)
    proof.rename(s / 'proof-renamed.md')
    return result

with patch.object(room_module, 'resolve_all', side_effect=change_after_lookup):
    result = room.broadcast('a', 'exists at post time?', evidence_refs=['file:proof.md'])
print('B6 result=', json.dumps(result), 'file_exists_at_append=', proof.exists())

rows = [{'seq': 1, 'ts': '2026-10-01T12:00:00Z', 'type': 'broadcast', 'agent_id': 'old-agent', 'text': 'x'}]
early = render_board(rows, datetime(2026, 10, 2, 11, 59, tzinfo=timezone.utc))
late = render_board(rows, datetime(2026, 10, 2, 12, 1, tzinfo=timezone.utc))
print('B7 same_log_different_projection=', early != late, 'last_seq_same=', 'Last seq: 1' in early and 'Last seq: 1' in late)

s = case('inherited-append-failure')
room = CoordinationRoom(s, s / 'events.jsonl', s / 'BOARD.md')
with patch.object(room._log, 'append', side_effect=OSError('injected disk failure')):
    try:
        room.claim('a', 'x.py')
    except OSError:
        pass
print('Inherited claim_after_failed_append=', room.state()['claims'], 'restarted_claims=', CoordinationRoom(s, s / 'events.jsonl').state()['claims'])
