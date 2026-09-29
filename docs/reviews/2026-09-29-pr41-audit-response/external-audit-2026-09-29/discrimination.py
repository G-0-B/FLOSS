import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / 'pr41-response-20260927/snapshot-5a1a2b1'
END = ROOT / 'snapshot-42e4d05'
BASE = ROOT / 'baseline-code'
assert not BASE.exists()
BASE.mkdir()
for name in ['packages', 'scripts', 'tests']:
    shutil.copytree(ORIGINAL / name, BASE / name)
for file in ORIGINAL.iterdir():
    if file.is_file() and file.suffix in {'.json', '.toml', '.ini', '.cfg'}:
        shutil.copyfile(file, BASE / file.name)
survivor = 'packages/reasoning_ensemble/tests/test_survivor_independence.py'
skill = 'scripts/tests/test_shared_skill_surface_scope.py'
agent = 'tests/test_shared_agent_surface_mcp.py'
for name in [survivor, skill, agent]:
    shutil.copyfile(END / name, BASE / name)
selected = [
    survivor + '::test_a_check_that_cannot_run_does_not_abort_the_deliberation',
    survivor + '::test_a_run_whose_check_crashed_is_degraded_and_keeps_its_responses',
    survivor + '::test_a_crashed_check_reports_independence_unknown_not_failed',
    agent + '::test_every_malformed_gateway_pid_shape_is_a_handled_refusal[integer-past-the-digit-limit]',
    agent + '::test_every_malformed_gateway_pid_shape_is_a_handled_refusal[nesting-past-the-recursion-limit]',
    skill + '::test_refreshing_either_of_two_nested_workspaces_keeps_the_others_projections',
    skill + '::test_a_relative_workspace_identity_proves_nothing',
    skill + '::test_a_marker_without_workspace_identity_is_kept_and_reported',
    skill + '::test_a_marker_this_materializer_writes_is_one_it_recognises_as_owned',
    skill + '::test_a_workspace_still_prunes_its_own_withdrawn_projection',
    agent + '::test_every_json_loader_reports_unreadable_input_as_its_own_error',
    agent + '::test_an_unreadable_roster_does_not_crash_the_doctor_summary',
    agent + '::test_a_malformed_agentmemory_reply_is_reported_not_raised',
    skill + '::test_an_unreadable_manifest_is_a_skill_surface_error',
]
command = [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
    '--basetemp=' + str(ROOT / 'pytest-baseline'), '--junitxml=' + str(ROOT / 'baseline.xml'), *selected]
env = dict(os.environ, PYTHONPATH='', PYTHONDONTWRITEBYTECODE='1', TEMP=str(ROOT / 'temp'), TMP=str(ROOT / 'temp'), PYTHONUTF8='1')
with (ROOT / 'baseline.txt').open('wb') as out:
    result = subprocess.run(command, cwd=BASE, env=env, stdout=out, stderr=subprocess.STDOUT)
(ROOT / 'baseline.command.json').write_text(json.dumps({'command': command, 'cwd': str(BASE), 'exit_code': result.returncode}, indent=2), encoding='utf-8')
print((ROOT / 'baseline.txt').read_text(encoding='utf-8')[-5000:])
print('BASELINE EXIT:', result.returncode)
