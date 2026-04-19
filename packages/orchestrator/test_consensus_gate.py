"""
Tests for the FLOSSI0ULLK Consensus Gate — analog vote model.

All vote values are floats in [-CERTAINTY_LIMIT, CERTAINTY_LIMIT].
No test may use exact ±1.0. Ternary {-1, 0, +1} integer values are forbidden.

Spec: docs/superpowers/specs/2026-04-12-local-agent-node-design.md §4

Run: python -m pytest packages/orchestrator/test_consensus_gate.py -v
Or:  python packages/orchestrator/test_consensus_gate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.orchestrator.claim_schema import (
    CERTAINTY_LIMIT,
    BlastRadius,
    Claim,
    Decision,
    EvidenceRef,
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

CL = CERTAINTY_LIMIT  # shorthand: 0.999


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def mock_voter(name: str, weight: float, rationale: str = "test") -> Voter:
    """Build a Voter that always casts the same analog weight."""

    def _v(_claim: Claim) -> Vote:
        return Vote(voter=name, weight=weight, rationale=rationale)

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
# Spec §4 test vectors — approval paths
# ---------------------------------------------------------------------------


def test_vector_1_unanimous_strong_approval():
    """[0.999, 0.999, 0.999] on Module => APPROVED (mean=0.999 > θ_approve=0.50)."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", CL), mock_voter("c", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED
    assert len(decision.votes) == 3


def test_vector_1b_moderate_approval_module():
    """[0.6, 0.6, 0.6] on Module => APPROVED (mean=0.6 > θ_approve=0.50)."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", 0.6), mock_voter("b", 0.6), mock_voter("c", 0.6)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED


def test_vector_2_strong_rejection():
    """[-0.999, -0.999, -0.999] on System => REJECTED (mean=-0.999 < θ_reject=-0.50)."""
    claim = sample_claim(
        blast=BlastRadius.SYSTEM, proposal_type=ProposalType.SPEC_CHANGE
    )
    voters = [mock_voter("a", -CL), mock_voter("b", -CL), mock_voter("c", -CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.REJECTED


def test_vector_3a_high_support_with_abstain_approves():
    """[0.999, 0.999, 0.0] on System => APPROVED (mean≈0.666 > θ_approve=0.60)."""
    claim = sample_claim(
        blast=BlastRadius.SYSTEM, proposal_type=ProposalType.ADR_CHANGE
    )
    voters = [mock_voter("a", CL), mock_voter("b", CL), mock_voter("c", 0.0)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED


def test_vector_3b_low_support_with_abstains_defers():
    """[0.5, 0.0, 0.0] on System => DEFERRED (mean≈0.167 < θ_approve=0.60)."""
    claim = sample_claim(
        blast=BlastRadius.SYSTEM, proposal_type=ProposalType.ADR_CHANGE
    )
    voters = [mock_voter("a", 0.5), mock_voter("b", 0.0), mock_voter("c", 0.0)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


def test_vector_5_human_override_on_deferred():
    """DEFERRED decision can be overridden by a human voter."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", 0.0)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED

    overridden = override(
        decision, claim, human_voter="human-anthony", rationale="time-sensitive fix"
    )
    assert overridden.outcome == Outcome.OVERRIDDEN
    assert overridden.override_by == "human-anthony"
    assert len(overridden.votes) == 3  # a + b + human override


def test_vector_6_insufficient_quorum_defers():
    """2 votes on System (quorum=3) => DEFERRED when variance is low."""
    claim = sample_claim(blast=BlastRadius.SYSTEM)
    voters = [mock_voter("a", CL), mock_voter("b", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


# ---------------------------------------------------------------------------
# CONFLICT tests — high variance routes to human, overrides quorum
# ---------------------------------------------------------------------------


def test_conflict_high_variance_module():
    """[0.999, -0.999] on Module => CONFLICT (σ²≈0.999 > θ_polarization=0.50)."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", -CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.CONFLICT


def test_conflict_overrides_quorum_check():
    """CONFLICT fires even when n < QUORUM_MIN (variance check runs first)."""
    claim = sample_claim(blast=BlastRadius.SYSTEM)
    # Only 2 voters (quorum=3), but they disagree violently
    voters = [mock_voter("a", CL), mock_voter("b", -CL)]
    decision = decide(claim, voters)
    # variance check fires before quorum check → CONFLICT not DEFERRED
    assert decision.outcome == Outcome.CONFLICT


def test_conflict_substrate():
    """[0.999, -0.999, 0.0] on Substrate => CONFLICT (σ² > θ_polarization=0.25)."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", CL), mock_voter("b", -CL), mock_voter("c", 0.0)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.CONFLICT


def test_no_conflict_low_variance():
    """[0.7, 0.8, 0.9] on Module => APPROVED, not CONFLICT (σ²≈0.0067 < θ=0.50)."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", 0.7), mock_voter("b", 0.8), mock_voter("c", 0.9)]
    decision = decide(claim, voters)
    assert decision.outcome != Outcome.CONFLICT
    assert decision.outcome == Outcome.APPROVED


# ---------------------------------------------------------------------------
# Quorum boundary tests — all four blast radii
# ---------------------------------------------------------------------------


def test_substrate_single_voter_defers():
    """A single strong-support vote on SUBSTRATE => DEFERRED (quorum=3)."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


def test_substrate_two_voters_defers():
    """Two strong-support votes on SUBSTRATE => DEFERRED (quorum=3, no conflict)."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", CL), mock_voter("b", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


def test_substrate_three_voters_high_support_approves():
    """Three high-support votes on SUBSTRATE => APPROVED (mean=0.999 > θ=0.85)."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", CL), mock_voter("b", CL), mock_voter("c", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED


def test_substrate_single_negative_does_not_veto():
    """A single -0.999 on SUBSTRATE with n=1 => DEFERRED, NOT REJECTED.

    The old ternary model allowed a single -1 to veto substrate changes.
    The analog model requires quorum=3 AND mean < θ_reject=-0.85 for REJECTED.
    A lone dissenter produces DEFERRED, not a veto.
    """
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", -CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED
    assert decision.outcome != Outcome.REJECTED


def test_substrate_three_strong_opposition_rejects():
    """[-0.999, -0.999, -0.999] on SUBSTRATE => REJECTED (mean=-0.999 < θ_reject=-0.85)."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", -CL), mock_voter("b", -CL), mock_voter("c", -CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.REJECTED


def test_system_two_voters_defers():
    """Two votes on SYSTEM (quorum=3) => DEFERRED when no conflict."""
    claim = sample_claim(blast=BlastRadius.SYSTEM)
    voters = [mock_voter("a", CL), mock_voter("b", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


def test_module_single_voter_defers():
    """One vote on MODULE (quorum=2) => DEFERRED (quorum not met, no conflict)."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


def test_module_two_voters_approves():
    """Two high-support votes on MODULE (quorum=2) => APPROVED."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED


# ---------------------------------------------------------------------------
# Local blast radius
# ---------------------------------------------------------------------------


def test_local_blast_single_voter_approves():
    """LOCAL needs only 1 voter. 0.4 > θ_approve=0.30 => APPROVED."""
    claim = sample_claim(blast=BlastRadius.LOCAL)
    voters = [mock_voter("a", 0.4)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED


def test_local_blast_below_threshold_defers():
    """LOCAL single voter with weight=0.1 < θ_approve=0.30 => DEFERRED."""
    claim = sample_claim(blast=BlastRadius.LOCAL)
    voters = [mock_voter("a", 0.1)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


# ---------------------------------------------------------------------------
# All voters are consulted (no early-exit)
# ---------------------------------------------------------------------------


def test_all_voters_consulted_despite_strong_opposition():
    """In the analog model, ALL voters are called before tally. No early-exit."""
    called = []

    def spy_voter(name: str, weight_val: float):
        def _v(_c):
            called.append(name)
            return Vote(voter=name, weight=weight_val, rationale="spy")

        return _v

    claim = sample_claim(blast=BlastRadius.SYSTEM)
    # b casts -0.999 but c must still be called — early-exit is gone
    voters = [spy_voter("a", CL), spy_voter("b", -CL), spy_voter("c", CL)]
    decide(claim, voters)
    assert called == ["a", "b", "c"]  # all three called


# ---------------------------------------------------------------------------
# Override tests
# ---------------------------------------------------------------------------


def test_override_rejects_non_deferred():
    """Override on APPROVED raises E_OVERRIDE_INVALID_STATE."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", CL)]
    approved = decide(claim, voters)
    assert approved.outcome == Outcome.APPROVED

    try:
        override(approved, claim, "human-x", "nope")
    except ConsensusGateError as e:
        assert "E_OVERRIDE_INVALID_STATE" in str(e)
    else:
        raise AssertionError("expected ConsensusGateError")


def test_override_rejects_conflict():
    """Override on CONFLICT raises E_OVERRIDE_INVALID_STATE (CONFLICT is not DEFERRED)."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", -CL)]
    conflicted = decide(claim, voters)
    assert conflicted.outcome == Outcome.CONFLICT

    try:
        override(conflicted, claim, "human-x", "trying to shortcut conflict")
    except ConsensusGateError as e:
        assert "E_OVERRIDE_INVALID_STATE" in str(e)
    else:
        raise AssertionError(
            "expected ConsensusGateError — CONFLICT requires human resolution, not override"
        )


def test_override_rejects_substrate():
    """SUBSTRATE disallows human override."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", CL), mock_voter("b", CL), mock_voter("c", 0.1)]
    deferred = decide(claim, voters)
    assert deferred.outcome == Outcome.DEFERRED

    try:
        override(deferred, claim, "human-x", "bypass")
    except ConsensusGateError as e:
        assert "E_OVERRIDE_NOT_ALLOWED" in str(e)
    else:
        raise AssertionError("expected ConsensusGateError")


def test_override_rejects_claim_id_mismatch():
    """override() rejects a prior_decision whose claim_id doesn't match the claim."""
    claim_a = sample_claim(blast=BlastRadius.MODULE)
    claim_b = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", 0.0)]
    deferred_a = decide(claim_a, voters)
    assert deferred_a.outcome == Outcome.DEFERRED

    try:
        override(deferred_a, claim_b, "human-x", "wrong claim")
    except ConsensusGateError as e:
        assert "E_OVERRIDE_CLAIM_MISMATCH" in str(e)
    else:
        raise AssertionError("expected ConsensusGateError for claim_id mismatch")


def test_override_rejects_blast_radius_mismatch():
    """override() rejects a caller-supplied claim that downgrades blast radius."""
    original = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", CL), mock_voter("b", CL), mock_voter("c", 0.1)]
    deferred = decide(original, voters)
    assert deferred.outcome == Outcome.DEFERRED

    forged = sample_claim(blast=BlastRadius.LOCAL)
    forged.id = original.id

    try:
        override(deferred, forged, "human-x", "attempt downgrade")
    except ConsensusGateError as e:
        assert "E_OVERRIDE_RADIUS_MISMATCH" in str(e)
    else:
        raise AssertionError("expected ConsensusGateError for blast_radius mismatch")


def test_override_rejects_duplicate_human_voter():
    """override() rejects a human_voter who already voted."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("human-anthony", CL), mock_voter("b", 0.0)]
    deferred = decide(claim, voters)
    assert deferred.outcome == Outcome.DEFERRED

    try:
        override(deferred, claim, human_voter="human-anthony", rationale="double-vote")
    except ConsensusGateError as e:
        assert "E_OVERRIDE_DUPLICATE" in str(e)
    else:
        raise AssertionError("expected ConsensusGateError for duplicate override voter")


# ---------------------------------------------------------------------------
# Vote validation
# ---------------------------------------------------------------------------


def test_invalid_weight_above_limit_raises():
    """weight > CERTAINTY_LIMIT raises E_VOTE_INVALID_RANGE."""
    try:
        Vote(voter="bad", weight=1.0, rationale="over limit").validate()
    except ValueError as e:
        assert "E_VOTE_INVALID_RANGE" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_invalid_weight_below_limit_raises():
    """weight < -CERTAINTY_LIMIT raises E_VOTE_INVALID_RANGE."""
    try:
        Vote(voter="bad", weight=-1.0, rationale="under limit").validate()
    except ValueError as e:
        assert "E_VOTE_INVALID_RANGE" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_nan_weight_raises():
    """NaN weight raises E_VOTE_INVALID_RANGE."""
    import math

    try:
        Vote(voter="bad", weight=math.nan, rationale="nan").validate()
    except ValueError as e:
        assert "E_VOTE_INVALID_RANGE" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_inf_weight_raises():
    """Infinite weight raises E_VOTE_INVALID_RANGE."""
    import math

    try:
        Vote(voter="bad", weight=math.inf, rationale="inf").validate()
    except ValueError as e:
        assert "E_VOTE_INVALID_RANGE" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_integer_weight_raises():
    """Integer weight (not float) raises E_VOTE_INVALID_RANGE."""
    try:
        Vote(voter="bad", weight=1, rationale="int not float").validate()  # type: ignore[arg-type]
    except ValueError as e:
        assert "E_VOTE_INVALID_RANGE" in str(e)
    else:
        raise AssertionError("expected ValueError — weight must be float, not int")


# ---------------------------------------------------------------------------
# Claim validation
# ---------------------------------------------------------------------------


def test_claim_summary_length():
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


def test_claim_validate_rejects_non_uuidv7():
    claim = sample_claim()
    claim.id = "not-a-uuid"
    try:
        claim.validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_claim_validate_rejects_uuid4():
    import uuid as _uuid

    claim = sample_claim()
    claim.id = str(_uuid.uuid4())
    try:
        claim.validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError for UUIDv4")


def test_claim_validate_rejects_bad_submitted_at():
    claim = sample_claim()
    claim.submitted_at = "yesterday"
    try:
        claim.validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_claim_validate_rejects_bad_proposal_type():
    claim = sample_claim()
    object.__setattr__(claim, "proposal_type", "CodeChange")
    try:
        claim.validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_claim_validate_rejects_bad_blast_radius():
    claim = sample_claim()
    object.__setattr__(claim, "blast_radius", "Module")
    try:
        claim.validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_claim_validate_rejects_non_evidence_ref_entries():
    claim = sample_claim()
    claim.evidence = [{"type": "spec", "ref": "docs/specs/consensus-gate.spec.md"}]
    try:
        claim.validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
        assert "evidence[0]" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_claim_validate_rejects_blank_evidence_ref():
    claim = sample_claim()
    claim.evidence = [EvidenceRef(type="spec", ref="  ")]
    try:
        claim.validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_claim_to_dict_serializes_validated_evidence():
    claim = sample_claim()
    claim.evidence = [
        EvidenceRef(type="spec", ref="docs/specs/consensus-gate.spec.md"),
        EvidenceRef(type="test", ref="packages/orchestrator/test_consensus_gate.py"),
    ]
    data = claim.to_dict()
    assert data["evidence"] == [
        {"type": "spec", "ref": "docs/specs/consensus-gate.spec.md"},
        {"type": "test", "ref": "packages/orchestrator/test_consensus_gate.py"},
    ]


# ---------------------------------------------------------------------------
# Decision validation
# ---------------------------------------------------------------------------


def test_decision_validate_rejects_string_outcome():
    claim = sample_claim()
    decision = Decision(
        claim_id=claim.id,
        blast_radius=claim.blast_radius,
        outcome="APPROVED",  # type: ignore[arg-type]
        votes=[Vote(voter="a", weight=CL, rationale="ok")],
    )
    try:
        decision.validate()
    except ValueError as e:
        assert "E_DECISION_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_decision_validate_rejects_non_vote_entries():
    claim = sample_claim()
    decision = Decision(
        claim_id=claim.id,
        blast_radius=claim.blast_radius,
        outcome=Outcome.APPROVED,
        votes=[{"voter": "a", "weight": CL, "rationale": "ok"}],  # type: ignore[list-item]
    )
    try:
        decision.validate()
    except ValueError as e:
        assert "E_DECISION_INVALID_SCHEMA" in str(e)
        assert "votes[0]" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_decision_validate_rejects_override_by_without_overridden():
    claim = sample_claim()
    decision = Decision(
        claim_id=claim.id,
        blast_radius=claim.blast_radius,
        outcome=Outcome.APPROVED,
        votes=[Vote(voter="a", weight=CL, rationale="ok")],
        override_by="human-x",
    )
    try:
        decision.validate()
    except ValueError as e:
        assert "E_DECISION_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_decision_to_dict_validates_before_serializing():
    claim = sample_claim()
    decision = Decision(
        claim_id=claim.id,
        blast_radius=claim.blast_radius,
        outcome=Outcome.APPROVED,
        votes=[Vote(voter="a", weight=CL, rationale="ok")],
        decided_at="not-a-timestamp",
    )
    try:
        decision.to_dict()
    except ValueError as e:
        assert "E_DECISION_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


# ---------------------------------------------------------------------------
# Ballot integrity
# ---------------------------------------------------------------------------


def test_decide_rejects_duplicate_voters():
    claim = sample_claim(blast=BlastRadius.SYSTEM)
    voters = [mock_voter("dup", CL), mock_voter("dup", CL), mock_voter("c", CL)]
    try:
        decide(claim, voters)
    except ConsensusGateError as e:
        assert "E_VOTE_DUPLICATE" in str(e)
    else:
        raise AssertionError("expected ConsensusGateError")


# ---------------------------------------------------------------------------
# ADR writer
# ---------------------------------------------------------------------------


def test_adr_writer_produces_file():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        adr_dir = Path(tmp)
        writer = default_adr_writer(adr_dir)
        claim = sample_claim(blast=BlastRadius.MODULE)
        voters = [mock_voter("a", CL), mock_voter("b", CL)]
        decision = decide(claim, voters, adr_writer=writer)
        assert decision.outcome == Outcome.APPROVED
        assert decision.adr_ref is not None
        path = Path(decision.adr_ref)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "APPROVED" in content
        assert claim.id in content
        assert "a" in content and "b" in content


def test_adr_writer_uses_unique_file_per_decision_event():
    """A later override must not overwrite the earlier deferred decision record."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        adr_dir = Path(tmp)
        writer = default_adr_writer(adr_dir)
        claim = sample_claim(blast=BlastRadius.MODULE)
        voters = [mock_voter("a", CL), mock_voter("b", 0.0)]
        deferred = decide(claim, voters, adr_writer=writer)
        overridden = override(
            deferred,
            claim,
            human_voter="human-x",
            rationale="time-sensitive fix",
            adr_writer=writer,
        )
        assert deferred.adr_ref is not None
        assert overridden.adr_ref is not None
        assert deferred.adr_ref != overridden.adr_ref
        assert Path(deferred.adr_ref).exists()
        assert Path(overridden.adr_ref).exists()


# ---------------------------------------------------------------------------
# tally() unit tests
# ---------------------------------------------------------------------------


def test_tally_direct_approved():
    claim = sample_claim(blast=BlastRadius.MODULE)
    vs = [
        Vote(voter="a", weight=CL, rationale="ok"),
        Vote(voter="b", weight=CL, rationale="ok"),
    ]
    outcome, mean, variance = tally(claim, vs)
    assert outcome == Outcome.APPROVED
    assert mean > 0
    assert variance == 0.0


def test_tally_direct_rejected():
    claim = sample_claim(blast=BlastRadius.MODULE)
    vs = [
        Vote(voter="a", weight=-CL, rationale="no"),
        Vote(voter="b", weight=-CL, rationale="no"),
    ]
    outcome, mean, variance = tally(claim, vs)
    assert outcome == Outcome.REJECTED


def test_tally_direct_conflict():
    claim = sample_claim(blast=BlastRadius.MODULE)
    vs = [
        Vote(voter="a", weight=CL, rationale="yes"),
        Vote(voter="b", weight=-CL, rationale="no"),
    ]
    outcome, mean, variance = tally(claim, vs)
    assert outcome == Outcome.CONFLICT


def test_tally_empty_defers():
    claim = sample_claim(blast=BlastRadius.MODULE)
    outcome, mean, variance = tally(claim, [])
    assert outcome == Outcome.DEFERRED
    assert mean == 0.0
    assert variance == 0.0


def test_tally_stores_stats_on_decision():
    """decide() populates tally_mean and tally_variance on the returned Decision."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", 0.5)]
    decision = decide(claim, voters)
    assert decision.tally_mean is not None
    assert decision.tally_variance is not None


# ---------------------------------------------------------------------------
# CLI runner (no pytest required)
# ---------------------------------------------------------------------------


def _run_all():
    tests = [
        test_vector_1_unanimous_strong_approval,
        test_vector_1b_moderate_approval_module,
        test_vector_2_strong_rejection,
        test_vector_3a_high_support_with_abstain_approves,
        test_vector_3b_low_support_with_abstains_defers,
        test_vector_5_human_override_on_deferred,
        test_vector_6_insufficient_quorum_defers,
        test_conflict_high_variance_module,
        test_conflict_overrides_quorum_check,
        test_conflict_substrate,
        test_no_conflict_low_variance,
        test_substrate_single_voter_defers,
        test_substrate_two_voters_defers,
        test_substrate_three_voters_high_support_approves,
        test_substrate_single_negative_does_not_veto,
        test_substrate_three_strong_opposition_rejects,
        test_system_two_voters_defers,
        test_module_single_voter_defers,
        test_module_two_voters_approves,
        test_local_blast_single_voter_approves,
        test_local_blast_below_threshold_defers,
        test_all_voters_consulted_despite_strong_opposition,
        test_override_rejects_non_deferred,
        test_override_rejects_conflict,
        test_override_rejects_substrate,
        test_override_rejects_claim_id_mismatch,
        test_override_rejects_blast_radius_mismatch,
        test_override_rejects_duplicate_human_voter,
        test_invalid_weight_above_limit_raises,
        test_invalid_weight_below_limit_raises,
        test_nan_weight_raises,
        test_inf_weight_raises,
        test_integer_weight_raises,
        test_claim_summary_length,
        test_claim_validate_rejects_non_uuidv7,
        test_claim_validate_rejects_uuid4,
        test_claim_validate_rejects_bad_submitted_at,
        test_claim_validate_rejects_bad_proposal_type,
        test_claim_validate_rejects_bad_blast_radius,
        test_claim_validate_rejects_non_evidence_ref_entries,
        test_claim_validate_rejects_blank_evidence_ref,
        test_claim_to_dict_serializes_validated_evidence,
        test_decision_validate_rejects_string_outcome,
        test_decision_validate_rejects_non_vote_entries,
        test_decision_validate_rejects_override_by_without_overridden,
        test_decision_to_dict_validates_before_serializing,
        test_decide_rejects_duplicate_voters,
        test_adr_writer_produces_file,
        test_adr_writer_uses_unique_file_per_decision_event,
        test_tally_direct_approved,
        test_tally_direct_rejected,
        test_tally_direct_conflict,
        test_tally_empty_defers,
        test_tally_stores_stats_on_decision,
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
