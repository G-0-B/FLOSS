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

import json
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


# ---------------------------------------------------------------------------
# A degraded round must say what actually failed, and must still be readable
# afterwards. Both were consequences of adding the survivor check.
# ---------------------------------------------------------------------------


def test_the_writeup_names_the_independence_failure_not_a_voter_shortage():
    """Enough voters embedded; the survivors are the problem. An operator told
    'fewer than 3 voters embedded' goes looking for dead voters that are fine."""
    embedded = [_r("a", "m", "f"), _r("b", "m", "f"), _r("c", "m", "f")]

    reason = synthesizer._degraded_reason(embedded, embedded, "2 surfaces, 2 families")

    assert "Fewer than" not in reason
    assert "independence bar" in reason
    assert "2 surfaces, 2 families" in reason


def test_the_writeup_still_names_a_genuine_voter_shortage():
    embedded = [_r("a", "m", "f")]
    responses = embedded + [_r("b", "m", "f"), _r("c", "m", "f")]

    reason = synthesizer._degraded_reason(embedded, responses, None)

    assert "Fewer than" in reason and "(1/3)" in reason
    assert "independence bar" not in reason


def test_both_failures_are_reported_when_both_hold():
    embedded = [_r("a", "m", "f")]
    responses = embedded + [_r("b", "m", "f")]

    reason = synthesizer._degraded_reason(embedded, responses, "1 surface, 1 family")

    assert "Fewer than" in reason
    assert "independence bar" in reason


def test_a_degraded_round_still_writes_a_durable_draft(tmp_path, monkeypatch):
    """The run an operator most needs to inspect was the only one with nothing
    to inspect: it returned before the staging block."""
    staging = tmp_path / "staging"
    monkeypatch.setattr(synthesizer, "ENSEMBLE_STAGING", staging)
    monkeypatch.setattr(synthesizer, "WORKSPACE_ROOT", tmp_path)
    monkeypatch.setattr(synthesizer, "_log_synthesis_action", lambda *a, **k: None)
    monkeypatch.setattr(
        synthesizer.transport,
        "resolve_embedder",
        lambda *a, **k: ("mxbai-embed-large", lambda text: [0.1]),
    )
    # One embedding short of MIN_VOTERS: degraded by COUNT, no independence
    # involvement, so this pins the staging fix on its own.
    survivors = [_r("a", "m", "f"), _r("b", "m", "f")]
    survivors.append(
        synthesizer.VoterResponse(
            voter_id="c",
            model="m",
            family="f",
            response="",
            response_hash="h",
            response_embedding=None,
            duration_seconds=0.1,
            error="timeout",
        )
    )
    monkeypatch.setattr(synthesizer, "dispatch_parallel", lambda *a, **k: survivors)

    result = synthesizer.synthesize(
        "prompt",
        voter_pool=[
            {"voter_id": v.voter_id, "model": "m", "family": "f"} for v in survivors
        ],
    )

    assert result.tier_classification.tier == "degraded"
    assert result.staging_path is not None, "degraded round staged nothing"
    written = list(staging.glob("*_synthesis.json"))
    assert len(written) == 1
    staged = json.loads(written[0].read_text(encoding="utf-8"))
    assert staged["tier"] == "degraded"
    assert len(staged["voter_responses"]) == 3, "raw responses must survive"


def test_a_profile_alias_resolves_to_the_same_name_both_checks_use(monkeypatch):
    """`mistral-free` follows the registry alias to the exempt `mistral`
    profile for roster resolution, and the independence check received the raw
    alias -- so it failed to find it in DEGRADED_OK_PROFILES and refused the
    healthy single-provider roster the alias exists to select."""
    from packages.reasoning_ensemble import transport

    assert transport.active_online_profile("mistral-free") == "mistral"
    assert transport.active_online_profile("diverse") == "diverse"


def test_the_exempt_profile_is_exempt_when_reached_through_its_alias(monkeypatch):
    monkeypatch.delenv("FLOSS_ALLOW_DEGRADED_ROSTER", raising=False)
    monkeypatch.setenv("FLOSS_ENSEMBLE_ONLINE_PROFILE", "mistral-free")
    survivors = [_r("a", "mistral/mistral-small-latest", "mistral")]

    assert synthesizer._survivor_independence_problem(survivors, "online") is None
