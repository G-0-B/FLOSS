"""Check only the concurrent synthesizer correction, without changing the pinned audit."""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / 'snapshot-5a1a2b1'
LIVE = Path(r'C:\~shit\FLOSS\.worktrees\pr41-salvage')
END = '5e52d40a3e42499dc6360638a9c50f5f71d401f8'
OVERLAY = ROOT / 'supplement-5e52d40'
paths = ['packages/reasoning_ensemble/synthesizer.py',
         'packages/reasoning_ensemble/tests/test_survivor_independence.py',
         'docs/reviews/2026-09-05-pr41-fix-sweep/RESULT.md']
hashes = []
for name in paths:
    data = subprocess.check_output(['git', '-C', str(LIVE), 'show', END + ':' + name])
    path = OVERLAY / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    hashes.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest()})
(ROOT / 'supplement-identity.json').write_text(json.dumps({
    'commit': END, 'dependencies_from': '5a1a2b1655274d4d37bba9e27a3bb2d11f2e35f6',
    'files': hashes
}, indent=2), encoding='utf-8')

sys.path[:0] = [str(SNAPSHOT), str(SNAPSHOT / 'scripts')]
import packages.reasoning_ensemble as package
from packages.reasoning_ensemble import transport
from packages.metacoordinator_mcp import voters

name = 'packages.reasoning_ensemble.synthesizer'
spec = importlib.util.spec_from_file_location(name, OVERLAY / paths[0])
synth = importlib.util.module_from_spec(spec)
sys.modules[name] = synth
package.synthesizer = synth
spec.loader.exec_module(synth)
assert Path(synth.__file__) == OVERLAY / paths[0]

import pytest
code = pytest.main(['-q', '-p', 'no:cacheprovider',
    '--basetemp=' + str(ROOT / 'pytest-supplement'),
    '--junitxml=' + str(ROOT / 'supplement.xml'), str(OVERLAY / paths[1])])
print('SUPPLEMENT_SURVIVOR_SUITE_EXIT', code)
assert code == 0

os.environ.pop('FLOSS_ALLOW_DEGRADED_ROSTER', None)
os.environ.update(FLOSS_ENSEMBLE_ONLINE_PROFILE='diverse', FLOSS_ENSEMBLE_VOTER_MODE='mixed')
vectors = dict(zip([v['voter_id'] for v in transport.LOCAL_VOTER_POOL],
                   ([1, 0], [.99, .01], [.97, .03], [-1, 0])))
original_resolver = transport.resolve_voter_pool
original_checker = voters.roster_independence_problem
def admit_then_break():
    result = original_resolver()
    def broken(*args):
        raise RuntimeError('independent audit checker failure')
    voters.roster_independence_problem = broken
    return result
def generate(voter, *args):
    if voter['transport'] != 'ollama':
        raise ConnectionError('simulated online outage')
    return voter['voter_id']
try:
    with patch.object(transport, 'resolve_default_voter_specs', return_value={
            'audit-groq': 'groq/openai/gpt-oss-120b', 'audit-mistral': 'mistral/mistral-large-latest'}), \
         patch.object(transport, 'resolve_voter_pool', side_effect=admit_then_break), \
         patch.object(transport, 'resolve_embedder', return_value=('audit', lambda t: vectors[t])), \
         patch.object(transport, 'generate', side_effect=generate), \
         patch.object(synth, '_log_synthesis_action') as log:
        result = synth.synthesize('Supplemental checker audit', stage_artifact=False)
    outcome = {'tier': result.tier_classification.tier,
               'success': log.call_args.kwargs['success'],
               'error': log.call_args.kwargs['error'],
               'responses_retained': len(result.voter_responses),
               'answers_in_writeup': all(r.response in result.final_synthesis for r in result.voter_responses)}
    print('SUPPLEMENT_REAL_DISPATCH', json.dumps(outcome))
    assert outcome['tier'] == 'degraded' and outcome['success'] is False
    assert outcome['error'].startswith('independence_unknown:')
    assert outcome['responses_retained'] == 6 and outcome['answers_in_writeup']
    assert 'do not meet the independence bar' not in result.final_synthesis
finally:
    voters.roster_independence_problem = original_checker
