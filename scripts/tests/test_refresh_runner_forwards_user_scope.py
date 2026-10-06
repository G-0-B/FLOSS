"""The refresh runner must forward --include-user-scope to every step that takes it.

`USER_SCOPE_STEPS` in refresh_agent_surfaces.py was a hand-maintained allowlist
containing only `agent-surface`. The hook materializer later grew both the
`--include-user-scope` flag and two user-scope targets (`claude_user`,
`hermes_user`), and nothing connected the two facts: `refresh_agent_surfaces.py
--only hook --include-user-scope` dropped the flag, skipped both targets, and
exited 0. An operator who asked for a user-scope refresh got a success report
and no refresh.

These tests derive the expected set from the materializer sources, so the next
script to grow the flag fails here instead of silently doing nothing.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "refresh_agent_surfaces", SCRIPTS_DIR / "refresh_agent_surfaces.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _steps_declaring_the_flag(runner) -> set[str]:
    """Step names whose materializer script actually accepts the flag."""
    declaring = set()
    for step_name, script in runner.STEPS:
        source = (SCRIPTS_DIR / script).read_text(encoding="utf-8")
        if '"--include-user-scope"' in source:
            declaring.add(step_name)
    return declaring


def test_the_allowlist_matches_the_scripts_that_accept_the_flag():
    runner = _load_runner()
    assert runner.USER_SCOPE_STEPS == _steps_declaring_the_flag(runner), (
        "USER_SCOPE_STEPS has drifted from the materializers that accept "
        "--include-user-scope; a step missing from the set is silently skipped "
        "on a user-scope refresh"
    )


@pytest.mark.parametrize("step_name", sorted({"agent-surface", "hook"}))
def test_the_flag_is_forwarded_to_each_user_scope_step(step_name):
    runner = _load_runner()
    script = dict(runner.STEPS)[step_name]
    command = runner.build_command(
        step_name, script, check=False, dry_run=False, include_user_scope=True
    )
    assert "--include-user-scope" in command


def test_the_flag_is_not_forwarded_to_steps_that_reject_it():
    """Forwarding it everywhere would just fail with an argparse error."""
    runner = _load_runner()
    for step_name, script in runner.STEPS:
        if step_name in runner.USER_SCOPE_STEPS:
            continue
        command = runner.build_command(
            step_name, script, check=False, dry_run=False, include_user_scope=True
        )
        assert "--include-user-scope" not in command, step_name


def test_the_flag_is_absent_when_not_requested():
    runner = _load_runner()
    for step_name, script in runner.STEPS:
        command = runner.build_command(
            step_name, script, check=False, dry_run=False, include_user_scope=False
        )
        assert "--include-user-scope" not in command, step_name
