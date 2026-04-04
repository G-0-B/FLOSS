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
    OVERRIDE_ALLOWED,
    QUORUM_MIN,
    BlastRadius,
    Claim,
    Decision,
    Outcome,
    Vote,
)

logger = logging.getLogger("consensus_gate")

# Type alias: a Voter is a callable that evaluates a Claim and returns a Vote.
# Real voters will wrap LLM calls or human prompts. Tests inject mocks.
Voter = Callable[[Claim], Vote]


class ConsensusGateError(Exception):
    """Raised for gate-protocol violations (not invariant violations)."""


def tally(claim: Claim, votes: list[Vote]) -> Outcome:
    """Apply spec §4.1 tallying logic to produce an Outcome.

    Rules (in order):
      1. Any -1 vote => REJECTED (INV-007)
      2. Substrate blast radius requires ALL +1 (no 0/abstain)
      3. Quorum minimum not met => DEFERRED
      4. >= 2 votes == +1 AND all votes >= 0 => APPROVED (INV-006)
      5. Otherwise => DEFERRED
    """
    if not votes:
        return Outcome.DEFERRED

    # Rule 1: any rejection vetoes
    if any(v.vote == -1 for v in votes):
        return Outcome.REJECTED

    # Rule 2: substrate requires unanimous +1
    if claim.blast_radius == BlastRadius.SUBSTRATE:
        if all(v.vote == 1 for v in votes) and len(votes) >= QUORUM_MIN[BlastRadius.SUBSTRATE]:
            return Outcome.APPROVED
        return Outcome.DEFERRED

    # Rule 3: quorum check
    quorum_required = QUORUM_MIN[claim.blast_radius]
    if len(votes) < quorum_required:
        return Outcome.DEFERRED

    # Rule 4: approval requires >=2 yes votes with no rejections
    # (rejections already excluded above, so we only need to check >=2 yes)
    approvals = sum(1 for v in votes if v.vote == 1)
    if approvals >= 2:
        return Outcome.APPROVED

    # Local blast with single voter: 1 approval is enough (quorum_min=1)
    if claim.blast_radius == BlastRadius.LOCAL and approvals >= 1:
        return Outcome.APPROVED

    # Rule 5: default
    return Outcome.DEFERRED


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
    for voter in voters:
        vote = voter(claim)
        vote.validate()
        votes.append(vote)
        # Early-exit: a single -1 vetoes, no need to consult remaining voters
        if vote.vote == -1:
            logger.info(
                "Claim %s vetoed by voter %s: %s",
                claim.id,
                vote.voter,
                vote.rationale,
            )
            break

    outcome = tally(claim, votes)
    decision = Decision(claim_id=claim.id, outcome=outcome, votes=votes)

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
      ConsensusGateError: if override state is invalid per INV-009 or
                          if blast_radius disallows override.
    """
    if prior_decision.outcome != Outcome.DEFERRED:
        raise ConsensusGateError(
            "E_OVERRIDE_INVALID_STATE: override only valid on DEFERRED decisions, "
            "got %s" % prior_decision.outcome
        )
    if not OVERRIDE_ALLOWED[claim.blast_radius]:
        raise ConsensusGateError(
            "E_OVERRIDE_NOT_ALLOWED: blast_radius %s does not permit override"
            % claim.blast_radius.value
        )
    if not human_voter or not rationale:
        raise ConsensusGateError(
            "E_OVERRIDE_NOT_HUMAN: human_voter and rationale required"
        )

    override_vote = Vote(voter=human_voter, vote=1, rationale=rationale)
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
            lines.append(f"- **{v.voter}** ({v.vote:+d}) @ {v.voted_at}")
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
