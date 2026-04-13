"""
FLOSSI0ULLK Consensus Gate — ADR-6 Seam 1.

Intercepts proposed structural changes, routes them through ternary consensus
({-1, 0, +1}), and records decisions as ADR stubs for provenance.

See:
- docs/specs/consensus-gate.spec.md — full contract
- docs/adr/ADR-6-four-system-integration.md — context + rationale
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

from .claim_schema import (
    APPROVE_THRESHOLD,
    CERTAINTY_LIMIT,
    OVERRIDE_ALLOWED,
    POLARIZATION_THRESHOLD,
    QUORUM_MIN,
    REJECT_THRESHOLD,
    BlastRadius,
    Claim,
    Decision,
    Outcome,
    Vote,
)

logger = logging.getLogger("consensus_gate")

# Type alias: a Voter is a callable that evaluates a Claim and returns a Vote.
# Real voters will wrap LLM calls or human prompts. Tests inject mocks.
#
# TODO(ADR-6 Seam 2): this gate currently trusts `vote.voter` / `human_voter`
# strings from callers. Integrate with the identity_integrity zome
# (register_aid / create_identity_seal) to resolve and authenticate voter AIDs
# before tallying, mirroring the substrate bridge's provenance model. Until
# that wiring lands, decide()/override() enforce *local* per-claim
# de-duplication by voter string, which prevents a single caller from stuffing
# the ballot but does not prevent cross-caller identity spoofing.
Voter = Callable[[Claim], Vote]


class ConsensusGateError(Exception):
    """Raised for gate-protocol violations (not invariant violations)."""


def tally(claim: Claim, votes: list[Vote]) -> tuple[Outcome, float, float]:
    """Apply analog tally logic (spec §4.2). Returns (outcome, mean, variance).

    Steps (in order — do not reorder):
      1. Conflict check: σ² > θ_polarization → CONFLICT (runs before quorum)
      2. Quorum check: n < QUORUM_MIN → DEFERRED
      3. Direction check: μ > θ_approve → APPROVED; μ < θ_reject → REJECTED; else DEFERRED

    CONFLICT overrides the quorum check by design. If two agents vote [0.9, -0.9],
    a third vote won't resolve the fight — it determines a winner. Human intervention
    is needed before more votes are collected, not after.

    Returns the outcome plus the computed mean and variance so callers can store them
    in Decision.tally_mean / Decision.tally_variance for auditability.
    """
    if not votes:
        return Outcome.DEFERRED, 0.0, 0.0

    weights = [v.weight for v in votes]
    n = len(weights)
    mean = sum(weights) / n
    variance = sum((w - mean) ** 2 for w in weights) / n  # population variance

    br = claim.blast_radius

    # Step 1 — Conflict check (variance runs regardless of quorum)
    if variance > POLARIZATION_THRESHOLD[br]:
        return Outcome.CONFLICT, mean, variance

    # Step 2 — Quorum check
    if n < QUORUM_MIN[br]:
        return Outcome.DEFERRED, mean, variance

    # Step 3 — Direction check
    if mean > APPROVE_THRESHOLD[br]:
        return Outcome.APPROVED, mean, variance
    if mean < REJECT_THRESHOLD[br]:
        return Outcome.REJECTED, mean, variance
    return Outcome.DEFERRED, mean, variance


def decide(
    claim: Claim,
    voters: list[Voter],
    adr_writer: Optional[Callable[[Decision, Claim], str]] = None,
) -> Decision:
    """Run the full gate: validate claim, collect votes, tally, record ADR.

    Args:
      claim: The proposed change. Must be valid (Claim.validate() called here).
      voters: List of Voter callables. Called synchronously in order.
      adr_writer: Optional callable that writes an ADR stub and returns its path.
                  If None, Decision.adr_ref is left unset.

    Returns:
      Decision with tallied outcome, all votes, and (if written) adr_ref.
    """
    claim.validate()

    votes: list[Vote] = []
    seen_voters: set[str] = set()
    for voter in voters:
        vote = voter(claim)
        vote.validate()
        if vote.voter in seen_voters:
            raise ConsensusGateError(
                f"E_VOTE_DUPLICATE: voter {vote.voter!r} already voted on claim {claim.id}"
            )
        seen_voters.add(vote.voter)
        votes.append(vote)
    # All voters consulted before tallying — CONFLICT requires the full vote set.
    # No early-exit: a single strong dissenter cannot suppress other voters' signals.

    outcome, mean, variance = tally(claim, votes)
    decision = Decision(
        claim_id=claim.id,
        outcome=outcome,
        votes=votes,
        tally_mean=mean,
        tally_variance=variance,
    )

    if adr_writer is not None:
        try:
            decision.adr_ref = adr_writer(decision, claim)
        except Exception as exc:  # noqa: BLE001 — ADR writing is best-effort
            logger.warning("Failed to write ADR stub for claim %s: %s", claim.id, exc)

    decision.validate()
    return decision


def override(
    prior_decision: Decision,
    claim: Claim,
    human_voter: str,
    rationale: str,
    adr_writer: Optional[Callable[[Decision, Claim], str]] = None,
) -> Decision:
    """Human override path for DEFERRED decisions. See spec §4.2.

    Raises:
      ConsensusGateError: if override state is invalid per INV-009,
                          if blast_radius disallows override, or
                          if prior_decision.claim_id does not match claim.id.
    """
    if prior_decision.claim_id != claim.id:
        raise ConsensusGateError(
            f"E_OVERRIDE_CLAIM_MISMATCH: prior decision {prior_decision.claim_id} "
            f"does not belong to claim {claim.id}"
        )
    if prior_decision.outcome != Outcome.DEFERRED:
        raise ConsensusGateError(
            f"E_OVERRIDE_INVALID_STATE: override only valid on DEFERRED decisions, "
            f"got {prior_decision.outcome}"
        )
    if not OVERRIDE_ALLOWED[claim.blast_radius]:
        raise ConsensusGateError(
            f"E_OVERRIDE_NOT_ALLOWED: blast_radius {claim.blast_radius.value} "
            f"does not permit override"
        )
    if not human_voter or not rationale:
        raise ConsensusGateError(
            "E_OVERRIDE_NOT_HUMAN: human_voter and rationale required"
        )
    if any(v.voter == human_voter for v in prior_decision.votes):
        raise ConsensusGateError(
            f"E_OVERRIDE_DUPLICATE: {human_voter!r} already voted on claim {claim.id}"
        )

    override_vote = Vote(voter=human_voter, weight=CERTAINTY_LIMIT, rationale=rationale)
    override_vote.validate()

    decision = Decision(
        claim_id=claim.id,
        outcome=Outcome.OVERRIDDEN,
        votes=[*prior_decision.votes, override_vote],
        override_by=human_voter,
    )

    if adr_writer is not None:
        try:
            decision.adr_ref = adr_writer(decision, claim)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to write override ADR stub: %s", exc)

    decision.validate()
    return decision


def default_adr_writer(adr_dir: Path) -> Callable[[Decision, Claim], str]:
    """Return an adr_writer that writes decisions as markdown stubs.

    ADR stubs land at: <adr_dir>/decisions/<date>-<claim-id>.md
    """

    def _write(decision: Decision, claim: Claim) -> str:
        """Write the decision as a markdown stub and return the written file path."""
        decisions_dir = adr_dir / "decisions"
        decisions_dir.mkdir(parents=True, exist_ok=True)
        date_part = decision.decided_at[:10]  # YYYY-MM-DD
        path = decisions_dir / f"{date_part}-{claim.id}.md"

        lines = [
            f"# Decision Record — Claim {claim.id}",
            "",
            f"**Outcome:** {decision.outcome.value}",
            f"**Decided:** {decision.decided_at}",
            f"**Proposer:** {claim.proposer}",
            f"**Proposal Type:** {claim.proposal_type.value}",
            f"**Blast Radius:** {claim.blast_radius.value}",
            "",
            "## Summary",
            "",
            claim.summary,
            "",
            "## Votes",
            "",
        ]
        for v in decision.votes:
            lines.append(f"- **{v.voter}** ({v.weight:+.4f}) @ {v.voted_at}")
            lines.append(f"  - {v.rationale}")

        if decision.override_by:
            lines.extend([
                "",
                "## Override",
                "",
                f"Overridden by human voter: **{decision.override_by}**",
            ])

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return str(path)

    return _write
