"""Independence is a property of who survived, not of who was invited.

PR41 review finding against synthesizer.py: the >=3 provider surfaces / >=4
model families bar was enforced once, on the pool, before any voter ran. After
generation the only gate was MIN_VOTERS, a COUNT -- and three voters cannot
span four families, so an outage that left three survivors of a four-family
profile passed and went on to report Tier-1 consensus.

The check is re-applied to the embedded subset through the SAME function the
pool-side check uses, because two implementations of "is this roster
independent" is how the two views drift apart -- which is the failure the
pool-side check was itself added to fix.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from packages.metacoordinator_mcp import voters as voters_lib  # noqa: E402
from packages.reasoning_ensemble import synthesizer  # noqa: E402


def _r(voter_id: str, model: str, family: str) -> synthesizer.VoterResponse:
    return synthesizer.VoterResponse(
        voter_id=voter_id,
        model=model,
        family=family,
        response="text",
        response_hash="h",
        response_embedding=[0.1],
        duration_seconds=0.1,
    )


def test_three_survivors_cannot_satisfy_a_four_family_bar(monkeypatch):
    monkeypatch.delenv("FLOSS_ALLOW_DEGRADED_ROSTER", raising=False)
    survivors = [
        _r("a", "groq/llama-3.1-8b-instant", "llama"),
        _r("b", "groq/llama-3.3-70b-versatile", "llama"),
        _r("c", "groq/gemma2-9b-it", "gemma"),
    ]

    problem = synthesizer._survivor_independence_problem(survivors, "online")

    assert problem is not None
    assert "independence" in problem


def test_the_check_is_skipped_where_the_pool_side_check_skips_it(monkeypatch):
    """local and mixed are exempt through the same DEGRADED_OK_PROFILES list."""
    survivors = [_r("a", "phi4-mini:latest", "phi")]

    assert synthesizer._survivor_independence_problem(survivors, "local") is None
    assert synthesizer._survivor_independence_problem(survivors, "mixed") is None


def test_an_empty_survivor_set_is_left_to_the_count_check(monkeypatch):
    """MIN_VOTERS already reports that case; do not report it twice."""
    assert synthesizer._survivor_independence_problem([], "online") is None


def test_an_override_that_silences_the_pool_check_silences_this_one(monkeypatch):
    """One switch, both checks. An operator who accepted a degraded roster at
    dispatch must not be told half-way through that it is degraded."""
    monkeypatch.setenv("FLOSS_ALLOW_DEGRADED_ROSTER", "1")
    survivors = [_r("a", "groq/llama-3.1-8b-instant", "llama")]

    assert synthesizer._survivor_independence_problem(survivors, "online") is None


def test_the_raising_and_reporting_forms_share_one_definition():
    """assert_roster_is_independent must be a wrapper, not a second copy."""
    thin = {"a": "groq/llama-3.1-8b-instant"}

    problem = voters_lib.roster_independence_problem("diverse", thin)
    assert problem is not None

    try:
        voters_lib.assert_roster_is_independent("diverse", thin)
    except RuntimeError as exc:
        assert str(exc) == problem
    else:  # pragma: no cover - the assert form must still raise
        raise AssertionError("assert_roster_is_independent did not raise")


def test_a_check_that_cannot_run_does_not_abort_the_deliberation(monkeypatch):
    """A broken registry must degrade the CHECK, never the run."""

    def boom(*args, **kwargs):
        raise RuntimeError("registry unreadable")

    monkeypatch.setattr(voters_lib, "roster_independence_problem", boom)
    survivors = [_r("a", "groq/llama-3.1-8b-instant", "llama")]

    assert synthesizer._survivor_independence_problem(survivors, "online") is None
