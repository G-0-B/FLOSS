"""Independent behavioral checks; all fixtures stay inside this audit directory."""
import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
REPO = ROOT / 'snapshot-42e4d05'
sys.path[:0] = [str(REPO), str(REPO / 'scripts')]
import materialize_shared_skill_surface as skills
import materialize_shared_agent_surface as surface
import materialize_shared_hook_surface as hooks
from packages.reasoning_ensemble import synthesizer as synth, transport
from packages.metacoordinator_mcp import voters

def workspace(root, name):
    source = root / 'skills' / name
    source.mkdir(parents=True)
    (source / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: audit fixture\n---\nInstructions from {root.name}\n', encoding='utf-8')
    return skills.resolve_skill_entry(root, {'path': f'skills/{name}'})

def manifest(root, target, names):
    path = root / 'manifest.json'
    path.write_text(json.dumps({'manifest_version': 'audit', 'skills': [{'path': f'skills/{n}'} for n in names],
        'targets': {'shared': {'enabled': True, 'scope': 'user', 'install_path': str(target)}}}), encoding='utf-8')
    return path

def ownership():
    owner = ROOT / 'ownership' / 'outer'
    nested = owner / 'checkouts' / 'nested'
    target = ROOT / 'ownership' / 'shared'
    for root, name in [(owner, 'outer-live'), (nested, 'nested-live')]:
        entry = workspace(root, name)
        skills.materialize(root, manifest(root, target, [name]), root / 'out', check=False, dry_run=False, include_user_scope=True)
    for root, name, foreign in [(owner, 'outer-live', 'nested-live'), (nested, 'nested-live', 'outer-live')]:
        before = (target / foreign / skills.MANAGED_MARKER).read_bytes()
        messages, drift = skills.materialize(root, manifest(root, target, [name]), root / 'out', check=False, dry_run=False, include_user_scope=True)
        assert (target / foreign / skills.MANAGED_MARKER).read_bytes() == before
        print('NESTED_REFRESH', root.name, 'foreign_marker_unchanged=True', 'drift=', drift)
    child = target / 'malformed-identity'
    child.mkdir()
    cases = {'relative': '.', 'null': None, 'empty': '', 'NUL': str(owner) + '\0',
             'surrogate': str(owner) + '\ud800', 'missing': str(owner / 'missing'), 'wrong-type': [],
             'case-alias': str(owner).swapcase(), 'dot-alias': str(owner / '..' / 'outer')}
    for name, identity in cases.items():
        marker = {'managed_by': skills.MANAGED_BY, 'source_path': str(owner), 'workspace_root': identity}
        (child / skills.MANAGED_MARKER).write_text(json.dumps(marker), encoding='utf-8')
        try:
            result = skills.projection_owned_by(child, owner)
        except Exception as exc:
            print('IDENTITY', name, 'UNHANDLED', type(exc).__name__, repr(str(exc)))
        else:
            print('IDENTITY', name, 'owned=', result)
    # Legacy owned-looking ancestry is not used to infer identity.
    (child / skills.MANAGED_MARKER).write_text(json.dumps({'managed_by': skills.MANAGED_BY,
        'source_path': str(owner / 'old-skill')}), encoding='utf-8')
    messages, drift = skills.prune_stale_projections('shared', target, {'outer-live', 'nested-live'}, check=True, dry_run=False, owner_root=owner)
    assert any('KEEP' in x and 'identity' in x for x in messages) and not drift
    print('LEGACY_KEEP', messages)

def migration():
    basefile = Path(r'C:\~shit\_audit\pr41-response-20260927\snapshot-5a1a2b1\scripts\materialize_shared_skill_surface.py')
    spec = importlib.util.spec_from_file_location('baseline_skills', basefile)
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    owner = ROOT / 'migration' / 'workspace'
    entry = workspace(owner, 'unchanged')
    target = ROOT / 'migration' / 'shared'
    projection = target / entry['skill_name']
    projection.mkdir(parents=True)
    (projection / 'SKILL.md').write_text(entry['files']['SKILL.md'], encoding='utf-8')
    (projection / skills.MANAGED_MARKER).write_text(baseline.serialize_marker(entry, 'audit'), encoding='utf-8')
    messages, drift = baseline.install_skill_projection('shared', entry, target, 'audit', check=False, dry_run=False)
    print('MIGRATION_BASELINE', messages, 'drift=', drift)
    assert not drift
    backup = ROOT / 'migration' / 'preserved-original'
    calls = []
    def preserve_instead_of_delete(path):
        assert path.resolve() == projection.resolve()
        path.resolve().relative_to(ROOT.resolve())
        backup.resolve().relative_to(ROOT.resolve())
        calls.append('remove')
        path.rename(backup)
    def fail_copy(*args, **kwargs):
        calls.append('copy')
        raise PermissionError('audit simulated copy failure')
    with patch.object(skills, 'remove_path', side_effect=preserve_instead_of_delete), patch.object(skills.shutil, 'copytree', side_effect=fail_copy):
        try:
            skills.install_skill_projection('shared', entry, target, 'audit', check=False, dry_run=False, workspace_root=owner)
        except PermissionError as exc:
            print('MIGRATION_FAILURE', str(exc), 'order=', calls, 'installed_exists=', projection.exists(), 'old_bytes_preserved=', backup.exists())
    assert calls == ['remove', 'copy'] and not projection.exists() and backup.exists()
    # Rerun is claimed to recover: exercise it with no simulated failure.
    skills.install_skill_projection('shared', entry, target, 'audit', check=False, dry_run=False, workspace_root=owner)
    print('MIGRATION_RERUN', 'restored=', (projection / 'SKILL.md').read_text(encoding='utf-8') == entry['files']['SKILL.md'])

def collision():
    base = ROOT / 'collision'
    first, second = base / 'first', base / 'second'
    a, b = workspace(first, 'same-name'), workspace(second, 'same-name')
    target = base / 'shared'
    skills.install_skill_projection('shared', a, target, 'audit', check=False, dry_run=False, workspace_root=first)
    # Prove actual removal selection while preserving the directory and stopping before mutation.
    selected = []
    def stop_before_delete(path):
        selected.append(str(path))
        raise RuntimeError('audit stopped before deletion')
    with patch.object(skills, 'remove_path', side_effect=stop_before_delete):
        try:
            skills.materialize(second, manifest(second, target, ['same-name']), second / 'out', check=False, dry_run=False, include_user_scope=True)
        except RuntimeError:
            pass
    print('SAME_NAME_FOREIGN_INSTALL', 'selected_for_removal=', bool(selected), 'current_owner_still_first=', skills.projection_owned_by(target / 'same-name', first))
    assert selected and skills.projection_owned_by(target / 'same-name', first)

def pid_shapes():
    home = ROOT / 'hermes'
    home.mkdir()
    config = home / 'config.yaml'
    config.write_text('mcp_servers: {}\nhooks: {}\n', encoding='utf-8')
    path = home / 'manifest.json'
    path.write_text(json.dumps({'rules': [], 'targets': {
        'hermes': {'enabled': True, 'scope': 'repo', 'format': 'yaml', 'settings_path': 'config.yaml', 'hooks': {}},
        'later': {'enabled': True, 'scope': 'repo', 'settings_path': 'later.json', 'hooks': {}}}}), encoding='utf-8')
    for name, payload in [('large-int', b'{"pid":' + b'9' * 5000 + b'}'), ('deep-json', b'[' * 100_000 + b']' * 100_000)]:
        (home / 'gateway.pid').write_bytes(payload)
        messages, drift = hooks.materialize(home, path, home / 'out', check=True, dry_run=False)
        ok = any(x.startswith('REFUSED') for x in messages) and any('later.json' in x for x in messages)
        print('PID_CHAIN', name, 'refused_and_continued=', ok)
        assert ok

def synthesis():
    os.environ.pop('FLOSS_ALLOW_DEGRADED_ROSTER', None)
    os.environ.update(FLOSS_ENSEMBLE_ONLINE_PROFILE='diverse', FLOSS_ENSEMBLE_VOTER_MODE='mixed')
    original_resolver = transport.resolve_voter_pool
    original_checker = voters.roster_independence_problem
    def admit_then_break():
        result = original_resolver()
        def broken(*args):
            raise RuntimeError('audit checker unreadable')
        voters.roster_independence_problem = broken
        return result
    def generate(voter, *args):
        if voter['transport'] != 'ollama':
            raise ConnectionError('audit outage')
        return 'Raw response from ' + voter['voter_id']
    try:
        with patch.object(transport, 'resolve_default_voter_specs', return_value={'audit-groq': 'groq/openai/gpt-oss-120b', 'audit-mistral': 'mistral/mistral-large-latest'}), \
             patch.object(transport, 'resolve_voter_pool', side_effect=admit_then_break), \
             patch.object(transport, 'generate', side_effect=generate), \
             patch.object(transport, 'resolve_embedder', return_value=('audit', lambda _: [1, 0])), \
             patch.object(synth, 'WORKSPACE_ROOT', ROOT), patch.object(synth, 'ENSEMBLE_STAGING', ROOT / 'staged'), \
             patch.object(synth, '_log_synthesis_action') as log:
            result = synth.synthesize('Critical review checker failure', stage_artifact=True)
        staged = json.loads((ROOT / result.staging_path).read_text(encoding='utf-8'))
        outcome = {'tier': result.tier_classification.tier, 'success': log.call_args.kwargs['success'],
                   'error': log.call_args.kwargs['error'], 'responses': len(result.voter_responses),
                   'staged_responses': len(staged['voter_responses']), 'staged_tier': staged['tier']}
        print('SYNTHESIS_REAL_DISPATCH_AND_STAGE', json.dumps(outcome))
        assert outcome['tier'] == 'degraded' and outcome['staged_tier'] == 'degraded'
        assert outcome['success'] is False and outcome['error'].startswith('independence_unknown:')
        assert outcome['responses'] == outcome['staged_responses'] == 6
        assert all(r.response in staged['final_synthesis'] for r in result.voter_responses)
    finally:
        voters.roster_independence_problem = original_checker

if __name__ == '__main__':
    ownership()
    migration()
    collision()
    pid_shapes()
    synthesis()
