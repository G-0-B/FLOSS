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
    """The invariant in this test's name, applied to what the pool side does NOW.

    `mixed` was exempt here because the pool side exempted it too. That stopped
    being true when resolve_voter_pool() began applying
    assert_roster_is_independent() to the combined mixed pool: a mixed run is
    admitted precisely BECAUSE online and local voters together clear the bar,
    so an outage that kills the online half leaves a correlated subset that
    this exemption would have reported as a normal consensus tier. The rule the
    name states is unchanged; only the list it resolves to moved.
    """
    survivors = [_r("a", "phi4-mini:latest", "phi")]

    assert synthesizer._survivor_independence_problem(survivors, "local") is None


def test_mixed_survivors_are_rechecked_because_the_pool_side_checks_them(
    monkeypatch,
):
    """The other half of the same rule. A mixed pool is judged as a whole at
    dispatch, so its survivors have to be judged too -- otherwise a provider
    outage silently converts an independent mixed ensemble into a correlated
    subset, and nothing downstream can tell."""
    monkeypatch.delenv("FLOSS_ALLOW_DEGRADED_ROSTER", raising=False)
    survivors = [
        _r("a", "groq/llama-3.1-8b-instant", "llama"),
        _r("b", "groq/gemma2-9b-it", "gemma"),
        _r("c", "groq/qwen-2.5-32b", "qwen"),
    ]

    problem = synthesizer._survivor_independence_problem(survivors, "mixed")

    assert problem is not None, "a one-surface mixed survivor set was accepted"


def test_an_empty_survivor_set_is_left_to_the_count_check(monkeypatch):
    """MIN_VOTERS already reports that case; do not report it twice."""
    assert synthesizer._survivor_independence_problem([], "online") is None


def test_an_override_that_silences_the_pool_check_silences_this_one(monkeypatch):
    """One switch, both checks. An operator who accepted a degraded roster at
    dispatch must not be told half-way through that it is degraded."""
    monkeypatch.setenv("FLOSS_ALLOW_DEGRADED_ROSTER", "1")
    survivors = [_r("a", "groq/llama-3.1-8b-instant", "llama")]

    assert synthesizer._survivor_independence_problem(survivors, "online") is None


def test_the_raising_and_reporting_forms_share_one_definition(monkeypatch):
    """assert_roster_is_independent must be a wrapper, not a second copy.

    Clears FLOSS_ALLOW_DEGRADED_ROSTER like its neighbours: with that set in
    the operator's environment both forms return None and this test fails for a
    reason that has nothing to do with what it checks.
    """
    monkeypatch.delenv("FLOSS_ALLOW_DEGRADED_ROSTER", raising=False)
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


def test_an_unwritable_staging_directory_does_not_lose_the_degraded_result(
    tmp_path, monkeypatch
):
    """`mkdir` sat outside the OSError guard, so a read-only workspace raised
    out of a function whose contract is to warn and return None -- and the
    caller it broke was the degraded path added in the same commit, which then
    discarded the voter responses it existed to preserve."""
    blocked = tmp_path / "not-a-dir" / "staging"
    (tmp_path / "not-a-dir").write_text("I am a file", encoding="utf-8")
    monkeypatch.setattr(synthesizer, "ENSEMBLE_STAGING", blocked)

    path = synthesizer._stage_synthesis(
        "prompt",
        "hash",
        "2026-08-31T00:00:00Z",
        synthesizer.TierClassification(
            tier="degraded",
            cluster_assignments={},
            cluster_sizes={},
            largest_cluster_id=0,
            largest_cluster_fraction=1.0,
            minority_coherent_voters=[],
            similarity_matrix=[],
            separation={},
        ),
        [],
        [],
        "synthesis text",
    )

    assert path is None, "staging must report failure, not raise"


def test_two_runs_of_one_prompt_in_one_second_do_not_share_an_artifact(
    tmp_path, monkeypatch
):
    """The name is a second-resolution timestamp plus the prompt hash, so
    concurrent runs of the same prompt collide: one overwrites the other's raw
    voter responses and both Actions cite the same file."""
    staging = tmp_path / "staging"
    monkeypatch.setattr(synthesizer, "ENSEMBLE_STAGING", staging)
    monkeypatch.setattr(synthesizer, "WORKSPACE_ROOT", tmp_path)
    tier = synthesizer.TierClassification(
        tier="degraded",
        cluster_assignments={},
        cluster_sizes={},
        largest_cluster_id=0,
        largest_cluster_fraction=1.0,
        minority_coherent_voters=[],
        similarity_matrix=[],
        separation={},
    )

    # datetime is immutable, so the clock is pinned by swapping the name the
    # module resolves rather than by patching the type.
    class _FixedClock:
        @staticmethod
        def now(tz=None):
            import datetime as _dt

            return _dt.datetime(2026, 8, 31, 12, 0, 0, tzinfo=tz)

    monkeypatch.setattr(synthesizer, "datetime", _FixedClock)

    first = synthesizer._stage_synthesis("p", "hash", "t", tier, [], [], "first")
    second = synthesizer._stage_synthesis("p", "hash", "t", tier, [], [], "second")

    assert first is not None and second is not None
    assert first != second, "two runs shared one artifact path"
    written = sorted(staging.glob("*_synthesis.json"))
    assert len(written) == 2
    bodies = {
        json.loads(f.read_text(encoding="utf-8"))["final_synthesis"] for f in written
    }
    assert bodies == {"first", "second"}, "one run overwrote the other"


# ---------------------------------------------------------------------------
# Mixed mode judges the pool that actually votes.
# ---------------------------------------------------------------------------


def test_the_local_pool_is_one_surface_not_four():
    """LOCAL_VOTER_POOL carries bare Ollama tags, and its fourth entry --
    `hf.co/unsloth/...` -- is an Ollama tag with two slashes in it. Reading the
    surface off the id turns four local voters into two surfaces (or four, for
    the bare tags), which would let a mixed roster of nothing but local models
    clear the surface bar on its own. The transport field is the authority; the
    same mistake already sent one of these four to a cloud provider once.
    """
    from packages.metacoordinator_mcp.voters import _derive_surface
    from packages.reasoning_ensemble import transport

    routes = [transport._independence_route(v) for v in transport.LOCAL_VOTER_POOL]
    surfaces = {_derive_surface(route) for route in routes}

    assert surfaces == {"ollama"}, routes
    assert any("hf.co" in v["model"] for v in transport.LOCAL_VOTER_POOL), (
        "the slashed-Ollama-tag entry this guards against is gone; if the pool "
        "changed, re-check that the surface is still read from transport"
    )


def test_mixed_mode_judges_the_combined_pool(monkeypatch):
    """_online_pool() raised before the local voters were appended, so a narrow
    credential-filtered online subset refused a run whose combined roster is
    comfortably independent -- and the only way through was the degraded-roster
    override, which asserts the opposite of what is true about that roster."""
    from packages.reasoning_ensemble import transport

    checked: list[dict] = []

    def _narrow_specs(profile=None, include_unavailable=False):
        # Two surfaces, two families: refused on its own.
        return {"a": "groq/openai/gpt-oss-120b", "b": "mistral/mistral-large-latest"}

    def _record(profile, resolved):
        checked.append(dict(resolved))

    monkeypatch.setattr(transport, "resolve_default_voter_specs", _narrow_specs)
    monkeypatch.setattr(transport, "assert_roster_is_independent", _record)
    monkeypatch.setenv("FLOSS_ENSEMBLE_VOTER_MODE", "mixed")

    pool, mode = transport.resolve_voter_pool()

    assert mode == "mixed"
    assert len(checked) == 1, "the online subset must not be judged on its own"
    judged = checked[0]
    assert len(judged) == len(pool), "the check saw a different roster than voted"
    assert any(
        "ollama/" in route for route in judged.values()
    ), "the local voters were not part of the roster that was judged"


def test_a_duplicate_voter_id_in_the_mixed_pool_is_refused(monkeypatch):
    """assert_roster_is_independent takes a dict keyed by voter_id, so a
    collision between an online id and a LOCAL_VOTER_POOL id silently drops an
    entry: the check would approve a SMALLER roster than the one returned,
    and the duplicate would vote twice. No profile collides today, which is
    exactly what makes it silent if that stops being true."""
    import pytest

    from packages.reasoning_ensemble import transport

    collide = transport.LOCAL_VOTER_POOL[0]["voter_id"]

    monkeypatch.setattr(
        transport,
        "resolve_default_voter_specs",
        lambda profile=None, include_unavailable=False: {
            collide: "groq/openai/gpt-oss-120b"
        },
    )
    monkeypatch.setattr(transport, "assert_roster_is_independent", lambda *a, **k: None)
    monkeypatch.setenv("FLOSS_ENSEMBLE_VOTER_MODE", "mixed")

    with pytest.raises(RuntimeError, match="duplicate voter_id"):
        transport.resolve_voter_pool()
