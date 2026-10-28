"""Independent, non-destructive probes of the pinned response commit."""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
REPO = ROOT / 'snapshot-5a1a2b1'
sys.path[:0] = [str(REPO), str(REPO / 'scripts')]
from packages.metacoordinator_mcp import voters
from packages.reasoning_ensemble import synthesizer, transport
import materialize_shared_agent_surface as surface
import materialize_shared_hook_surface as hooks
import materialize_shared_skill_surface as skills

os.environ.pop('FLOSS_ALLOW_DEGRADED_ROSTER', None)
os.environ['FLOSS_ENSEMBLE_ONLINE_PROFILE'] = 'diverse'
os.environ['FLOSS_ENSEMBLE_VOTER_MODE'] = 'mixed'

def synthesis_probe(checker_crash=False):
    local = transport.LOCAL_VOTER_POOL
    vectors = dict(zip([v['voter_id'] for v in local],
                       ([1, 0], [.99, .01], [.97, .03], [-1, 0])))
    online = {'audit-groq': 'groq/openai/gpt-oss-120b',
              'audit-mistral': 'mistral/mistral-large-latest'}
    admitted = transport.resolve_voter_pool
    def generate(voter, *args):
        if voter['transport'] != 'ollama':
            raise ConnectionError('simulated online outage')
        return voter['voter_id']
    def embed(text):
        return vectors.get(text, [1, 0])
    def resolve_then_break_checker():
        result = admitted()
        # Only break after the real admission check; keep its real verdict.
        voters.roster_independence_problem = lambda *args: (_ for _ in ()).throw(
            RuntimeError('independent audit checker failure'))
        return result
    original_checker = voters.roster_independence_problem
    try:
        with patch.object(transport, 'resolve_default_voter_specs', return_value=online), \
             patch.object(transport, 'resolve_embedder', return_value=('audit', embed)), \
             patch.object(transport, 'generate', side_effect=generate), \
             patch.object(synthesizer, '_log_synthesis_action') as log:
            if checker_crash:
                with patch.object(transport, 'resolve_voter_pool', side_effect=resolve_then_break_checker):
                    result = synthesizer.synthesize('Audit mixed outage', stage_artifact=False)
            else:
                result = synthesizer.synthesize('Audit mixed outage', stage_artifact=False)
        output = {'tier': result.tier_classification.tier,
                  'success': log.call_args.kwargs['success'],
                  'responses_retained': len(result.voter_responses),
                  'failed': sum(r.error is not None for r in result.voter_responses),
                  'transports': {r.voter_id: r.transport_name for r in result.voter_responses}}
        print('CHECKER_CRASH' if checker_crash else 'F1_REAL_DISPATCH', json.dumps(output))
        assert output['responses_retained'] == 6 and output['failed'] == 2
        if not checker_crash:
            assert output['tier'] == 'degraded' and output['success'] is False
        else:
            assert output['tier'] != 'degraded' and output['success'] is True
    finally:
        voters.roster_independence_problem = original_checker

def pid_probes():
    fixture = ROOT / 'probe-hermes'
    fixture.mkdir()
    config = fixture / 'config.yaml'
    config.write_text('mcp_servers: {}\nhooks: {}\n', encoding='utf-8')
    before = config.read_bytes()
    manifest = fixture / 'manifest.json'
    manifest.write_text(json.dumps({'rules': [], 'targets': {
        'hermes': {'enabled': True, 'scope': 'repo', 'format': 'yaml',
                   'settings_path': 'config.yaml', 'hooks': {}},
        'later': {'enabled': True, 'scope': 'repo', 'settings_path': 'later.json', 'hooks': {}}
    }}), encoding='utf-8')
    cases = {'bad-json': b'not json{', 'list': b'[]', 'null': b'null',
             'utf8': b'\xff', 'bool': b'{"pid":true}', 'zero': b'{"pid":0}',
             'negative': b'{"pid":-1}', 'posix-overflow': b'{"pid":2147483648}',
             'missing-pid': b'{}', 'string-pid': b'{"pid":"42"}',
             'float-pid': b'{"pid":42.5}', 'huge-integer': b'{"pid":' + b'9' * 5000 + b'}',
             'deep-json': b'[' * 1500 + b'0' + b']' * 1500}
    for name, payload in cases.items():
        (fixture / 'gateway.pid').write_bytes(payload)
        try:
            results, drift = hooks.materialize(fixture, manifest, fixture / 'output',
                                                check=True, dry_run=False)
        except Exception as exc:
            print('PID', name, 'UNHANDLED', type(exc).__name__, str(exc)[:180])
        else:
            refused = any(r.startswith('REFUSED') for r in results)
            later = any('later.json' in r for r in results)
            print('PID', name, json.dumps({'refused': refused, 'later_target_checked': later, 'drift': drift}))
            assert refused and later and drift
        assert config.read_bytes() == before
    # Refusal must hold in write mode too, without writing the target.
    (fixture / 'gateway.pid').write_bytes(b'[]')
    message, drift = hooks.apply_yaml_target(config, {'format': 'yaml', 'hooks': {}},
                                             check=False, dry_run=False)
    assert message.startswith('REFUSED') and drift and config.read_bytes() == before
    print('F2_WRITE_REFUSAL config_bytes_unchanged=True')
    # No real Windows os.kill call: this is only an exception-handling probe.
    for exc in (OverflowError('audit overflow'), ValueError('audit invalid PID')):
        with patch.object(surface.os, 'name', 'posix'), patch.object(surface.os, 'kill', side_effect=exc):
            assert surface._pid_alive(3_000_000_000) is True
    print('PID_SIMULATED_POSIX overflow_and_value_error_fail_closed=True')

def skill_probes():
    base = ROOT / 'probe-skills'
    owner = base / 'outer-workspace'
    nested = owner / 'checkouts' / 'independent-workspace'
    sibling = base / 'sibling-workspace'
    target = base / 'shared-user-skills'
    for name, workspace in [('nested-live', nested), ('sibling-live', sibling), ('own-stale', owner)]:
        source = workspace / 'FLOSS' / 'skill-corpus' / name
        source.mkdir(parents=True)
        (source / 'SKILL.md').write_text('---\nname: ' + name + '\ndescription: audit fixture\n---\nInstructions', encoding='utf-8')
        child = target / name
        child.mkdir(parents=True)
        # Use the production resolver and serializer, not invented marker keys.
        entry = skills.resolve_skill_entry(workspace, {'path': f'FLOSS/skill-corpus/{name}'})
        (child / skills.MANAGED_MARKER).write_text(skills.serialize_marker(entry, 'audit'), encoding='utf-8')
        print('OWNER', name, skills.projection_owned_by(child, owner))
    manifest = owner / 'manifest.json'
    manifest.write_text(json.dumps({'manifest_version': 'audit', 'skills': [], 'targets': {
        'audit-shared': {'enabled': True, 'scope': 'user', 'install_path': str(target)}
    }}), encoding='utf-8')
    results, drift = skills.materialize(owner, manifest, owner / 'output',
                                        check=False, dry_run=True, include_user_scope=True)
    removals = [r for r in results if 'remove' in r]
    print('NESTED_WORKSPACE_FULL_MATERIALIZE', json.dumps({'plans': removals, 'drift': drift}))
    assert any('nested-live' in r for r in removals)
    assert not any('sibling-live' in r for r in removals)
    assert (target / 'nested-live').is_dir()
    # Unknown marker ownership is claimed if its relative source resolves under cwd.
    relative = target / 'relative-marker'
    relative.mkdir()
    (relative / skills.MANAGED_MARKER).write_text(json.dumps({
        'managed_by': skills.MANAGED_BY, 'source_path': '.', 'skill_name': 'relative-marker'}), encoding='utf-8')
    saved_cwd = Path.cwd()
    try:
        os.chdir(owner)
        print('RELATIVE_MARKER_OWNER', skills.projection_owned_by(relative, owner))
    finally:
        os.chdir(saved_cwd)
    print('SKILL_PROBES no_pruning_executed=True')

if __name__ == '__main__':
    synthesis_probe()
    synthesis_probe(checker_crash=True)
    pid_probes()
    skill_probes()
