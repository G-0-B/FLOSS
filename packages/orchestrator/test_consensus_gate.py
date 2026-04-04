"""
Tests for the FLOSSI0ULLK Consensus Gate (ADR-6 Seam 1).

Covers the 6 test vectors from docs/specs/consensus-gate.spec.md §6
plus error cases.

Run: python -m pytest packages/orchestrator/test_consensus_gate.py -v
Or:  python packages/orchestrator/test_consensus_gate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Support running via `python packages/orchestrator/test_consensus_gate.py`
_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.orchestrator.claim_schema import (
    BlastRadius,
    Claim,
    Decision,
    Outcome,
    ProposalType,
    Vote,
)
from packages.orchestrator.consensus_gate import (
    ConsensusGateError,
    Voter,
    decide,
    default_adr_writer,
    override,
    tally,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def mock_voter(name: str, vote: int, rationale: str = "test") -> Voter:
    """Build a Voter that always casts the same vote."""
    def _v(_claim: Claim) -> Vote:
        return Vote(voter=name, vote=vote, rationale=rationale)
    return _v


def sample_claim(
    blast: BlastRadius = BlastRadius.MODULE,
    proposal_type: ProposalType = ProposalType.CODE_CHANGE,
) -> Claim:
    return Claim(
        proposer="agent-test",
        proposal_type=proposal_type,
        summary="test claim",
        body="proposed change body",
        blast_radius=blast,
    )


# ---------------------------------------------------------------------------
# Spec §6 test vectors
# ---------------------------------------------------------------------------


def test_vector_1_unanimous_approval():
    """§6.1: [+1, +1, +1] on Module => APPROVED."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", 1), mock_voter("b", 1), mock_voter("c", 1)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED
    assert len(decision.votes) == 3


def test_vector_2_single_rejection_vetoes():
    """§6.2: [+1, +1, -1] on System => REJECTED (INV-007)."""
    claim = sample_claim(
        blast=BlastRadius.SYSTEM, proposal_type=ProposalType.SPEC_CHANGE
    )
    voters = [mock_voter("a", 1), mock_voter("b", 1), mock_voter("c", -1)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.REJECTED


def test_vector_3a_two_yes_one_abstain_approves():
    """§6.3 correction: [+1, +1, 0] satisfies INV-006 => APPROVED."""
    claim = sample_claim(
        blast=BlastRadius.SYSTEM, proposal_type=ProposalType.ADR_CHANGE
    )
    voters = [mock_voter("a", 1), mock_voter("b", 1), mock_voter("c", 0)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED


def test_vector_3b_one_yes_two_abstain_defers():
    """§6.3 corrected: [+1, 0, 0] insufficient approvals => DEFERRED."""
    claim = sample_claim(
        blast=BlastRadius.SYSTEM, proposal_type=ProposalType.ADR_CHANGE
    )
    voters = [mock_voter("a", 1), mock_voter("b", 0), mock_voter("c", 0)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


def test_vector_4_substrate_requires_unanimous():
    """§6.4: Substrate with [+1, +1, 0] => DEFERRED (no override path)."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", 1), mock_voter("b", 1), mock_voter("c", 0)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


def test_vector_4b_substrate_unanimous_approves():
    """Substrate with [+1, +1, +1] => APPROVED."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", 1), mock_voter("b", 1), mock_voter("c", 1)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED


def test_vector_5_human_override_on_deferred():
    """§6.5: DEFERRED decision can be overridden by human voter."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", 1), mock_voter("b", 0)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED

    overridden = override(
        decision,
        claim,
        human_voter="human-anthony",
        rationale="time-sensitive fix",
    )
    assert overridden.outcome == Outcome.OVERRIDDEN
    assert overridden.override_by == "human-anthony"
    # Original votes preserved + override vote appended
    assert len(overridden.votes) == 3


def test_vector_6_insufficient_quorum():
    """§6.6: 2 votes on System (needs 3) => DEFERRED."""
    claim = sample_claim(blast=BlastRadius.SYSTEM)
    voters = [mock_voter("a", 1), mock_voter("b", 1)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


# ---------------------------------------------------------------------------
# Additional coverage
# ---------------------------------------------------------------------------


def test_local_blast_single_voter_approves():
    """Local needs only 1 voter + 1 approval."""
    claim = sample_claim(blast=BlastRadius.LOCAL)
    voters = [mock_voter("a", 1)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED


def test_early_exit_on_first_rejection():
    """A -1 vote short-circuits subsequent voters."""
    called = []

    def spy_voter(name: str, vote_val: int):
        def _v(_c):
            called.append(name)
            return Vote(voter=name, vote=vote_val, rationale="spy")
        return _v

    claim = sample_claim(blast=BlastRadius.SYSTEM)
    voters = [spy_voter("a", 1), spy_voter("b", -1), spy_voter("c", 1)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.REJECTED
    assert called == ["a", "b"]  # voter c never called
    assert len(decision.votes) == 2


def test_override_rejects_non_deferred():
    """Override on APPROVED should raise."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", 1), mock_voter("b", 1)]
    approved = decide(claim, voters)
    assert approved.outcome == Outcome.APPROVED

    try:
        override(approved, claim, "human-x", "nope")
    except ConsensusGateError as e:
        assert "E_OVERRIDE_INVALID_STATE" in str(e)
    else:
        raise AssertionError("expected ConsensusGateError")


def test_override_rejects_substrate():
    """Substrate disallows human override."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", 1), mock_voter("b", 0), mock_voter("c", 1)]
    deferred = decide(claim, voters)
    assert deferred.outcome == Outcome.DEFERRED

    try:
        override(deferred, claim, "human-x", "bypass")
    except ConsensusGateError as e:
        assert "E_OVERRIDE_NOT_ALLOWED" in str(e)
    else:
        raise AssertionError("expected ConsensusGateError")


def test_invalid_vote_range_raises():
    """Vote value outside {-1, 0, +1} raises."""
    try:
        Vote(voter="bad", vote=2, rationale="out of range").validate()
    except ValueError as e:
        assert "E_VOTE_INVALID_RANGE" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_claim_summary_length():
    """Summary > 200 chars raises."""
    try:
        Claim(
            proposer="a",
            proposal_type=ProposalType.CODE_CHANGE,
            summary="x" * 201,
            body="body",
            blast_radius=BlastRadius.LOCAL,
        ).validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_adr_writer_produces_file(tmp_path_factory=None):
    """default_adr_writer writes a parseable markdown stub."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        adr_dir = Path(tmp)
        writer = default_adr_writer(adr_dir)
        claim = sample_claim(blast=BlastRadius.MODULE)
        voters = [mock_voter("a", 1), mock_voter("b", 1)]
        decision = decide(claim, voters, adr_writer=writer)
        assert decision.outcome == Outcome.APPROVED
        assert decision.adr_ref is not None
        path = Path(decision.adr_ref)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "APPROVED" in content
        assert claim.id in content
        assert "a" in content and "b" in content


def test_tally_direct():
    """Exercise tally() without voter mocks."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    vs = [
        Vote(voter="a", vote=1, rationale="ok"),
        Vote(voter="b", vote=1, rationale="ok"),
    ]
    assert tally(claim, vs) == Outcome.APPROVED

    vs_reject = vs + [Vote(voter="c", vote=-1, rationale="no")]
    assert tally(claim, vs_reject) == Outcome.REJECTED

    assert tally(claim, []) == Outcome.DEFERRED


# ---------------------------------------------------------------------------
# CLI runner (no pytest required)
# ---------------------------------------------------------------------------


def _run_all():
    tests = [
        test_vector_1_unanimous_approval,
        test_vector_2_single_rejection_vetoes,
        test_vector_3a_two_yes_one_abstain_approves,
        test_vector_3b_one_yes_two_abstain_defers,
        test_vector_4_substrate_requires_unanimous,
        test_vector_4b_substrate_unanimous_approves,
        test_vector_5_human_override_on_deferred,
        test_vector_6_insufficient_quorum,
        test_local_blast_single_voter_approves,
        test_early_exit_on_first_rejection,
        test_override_rejects_non_deferred,
        test_override_rejects_substrate,
        test_invalid_vote_range_raises,
        test_claim_summary_length,
        test_adr_writer_produces_file,
        test_tally_direct,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {t.__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all())
