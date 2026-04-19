"""
GatewayTools — the 5 MCP tool handlers for the FLOSSIØULLK consensus gateway.

The gateway is a router, not a controller (spec §5). It:
  - Accepts Claims and Votes from any agent
  - Reads the cell source chain to provide context to voters
  - Does NOT decide outcomes, command voters, or hold state outside the cell dir

Each public method returns a JSON string — the MCP wire format for tool results.
Errors are returned as {"error": "<message>"} rather than raised, so callers
(LLM agents reading tool results) always receive parseable output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.orchestrator.claim_schema import (  # noqa: E402
    BlastRadius,
    Claim,
    Decision,
    EvidenceRef,
    Outcome,
    ProposalType,
    TruthStatus,
    Vote,
)
from packages.orchestrator.consensus_gate import tally  # noqa: E402
from packages.source_chain.cell import CellDirectory  # noqa: E402

# Deferred type — avoids importing voters.py (and LiteLLM) at module load.
# Tests that never call run_consensus_round should never touch the network.
VoterFactory = Callable[[], list[Callable[[Claim], Vote]]]


def _claim_from_chain_entry(entry_content: dict[str, Any]) -> Claim:
    """Reconstruct a Claim dataclass from its to_dict() form on the source chain.

    Enums come back as strings; we parse them back to their Enum members so
    downstream validation and tally logic work against the typed API.
    """
    evidence = [
        EvidenceRef(type=e["type"], ref=e["ref"])
        for e in entry_content.get("evidence", [])
    ]
    return Claim(
        proposer=entry_content["proposer"],
        proposal_type=ProposalType(entry_content["proposal_type"]),
        summary=entry_content["summary"],
        body=entry_content["body"],
        blast_radius=BlastRadius(entry_content["blast_radius"]),
        evidence=evidence,
        truth_status=TruthStatus(entry_content.get("truth_status", "Unverified")),
        id=entry_content["id"],
        submitted_at=entry_content["submitted_at"],
    )


def _ok(data: Any) -> str:
    """Serialize a successful tool result into the compact JSON wire format."""
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def _err(msg: str) -> str:
    """Serialize a tool error so MCP callers always receive parseable JSON."""
    return json.dumps({"error": msg}, separators=(",", ":"))


def _vote_from_chain_entry(entry_content: dict[str, Any]) -> Vote:
    """Reconstruct and validate a Vote dataclass from persisted source-chain content."""
    vote = Vote(
        voter=entry_content["voter"],
        weight=float(entry_content["weight"]),
        rationale=entry_content["rationale"],
        voted_at=entry_content["voted_at"],
    )
    vote.validate()
    return vote


def _decision_outcome(entry_content: dict[str, Any]) -> Outcome:
    """Parse the Outcome enum from a persisted Decision payload."""
    return Outcome(entry_content["outcome"])


def _known_voter_name(voter: Callable[[Claim], Vote]) -> Optional[str]:
    """Return the configured voter name when it can be inferred without a network call."""
    name = getattr(voter, "__name__", "")
    for prefix in ("litellm_voter_", "flowith_voter_"):
        if name.startswith(prefix):
            return name[len(prefix) :]
    return None


class GatewayTools:
    """Stateless tool handlers. All state lives in the cell directory on disk."""

    def __init__(
        self,
        base_dir: Path,
        dna_hash: str,
        *,
        voter_factory: Optional[VoterFactory] = None,
    ) -> None:
        self._cell = CellDirectory(base_dir=base_dir, dna_hash=dna_hash)
        # voter_factory is lazy: default stays None so test harnesses that
        # don't exercise run_consensus_round never import voters.py / litellm.
        self._voter_factory: Optional[VoterFactory] = voter_factory

    # ------------------------------------------------------------------
    # Tool 1 — submit_claim
    # ------------------------------------------------------------------

    def submit_claim(
        self,
        proposer: str,
        proposal_type: str,
        summary: str,
        body: str,
        blast_radius: str,
        evidence: list[dict] | None = None,
    ) -> str:
        """Append a Claim entry to the source chain.

        Returns JSON: {"entry_hash": "<64-hex>", "claim_id": "<uuid>"}
        On validation error: {"error": "<message>"}
        """
        try:
            br = BlastRadius(blast_radius)
            pt = ProposalType(proposal_type)
        except ValueError as exc:
            return _err(f"E_SUBMIT_CLAIM_INVALID: {exc}")

        ev_refs: list[EvidenceRef] = []
        for item in evidence or []:
            if not isinstance(item, dict):
                return _err(
                    "E_SUBMIT_CLAIM_INVALID_EVIDENCE: "
                    "evidence items must be objects with 'type' and 'ref'"
                )
            try:
                ref = EvidenceRef(type=item["type"], ref=item["ref"])
                ref.validate()
                ev_refs.append(ref)
            except (KeyError, TypeError, ValueError) as exc:
                return _err(f"E_SUBMIT_CLAIM_INVALID_EVIDENCE: {exc}")

        try:
            claim = Claim(
                proposer=proposer,
                proposal_type=pt,
                summary=summary,
                body=body,
                blast_radius=br,
                evidence=ev_refs,
            )
            claim.validate()
        except ValueError as exc:
            return _err(f"E_SUBMIT_CLAIM_INVALID: {exc}")

        h = self._cell.append_entry(
            entry_type="claim",
            author_did=proposer,
            content=claim.to_dict(),
        )
        return _ok({"entry_hash": h, "claim_id": claim.id})

    # ------------------------------------------------------------------
    # Tool 2 — cast_vote
    # ------------------------------------------------------------------

    def cast_vote(
        self,
        claim_id: str,
        voter: str,
        weight: float,
        rationale: str,
    ) -> str:
        """Append a Vote entry for a given claim_id.

        weight must be a float in [-CERTAINTY_LIMIT, CERTAINTY_LIMIT].
        Returns JSON: {"entry_hash": "<64-hex>"}
        On validation error: {"error": "<message>"}
        """
        try:
            vote = Vote(voter=voter, weight=weight, rationale=rationale)
            vote.validate()
        except (ValueError, TypeError) as exc:
            return _err(f"E_CAST_VOTE_INVALID: {exc}")

        entries = self._cell.read_chain(limit=None)
        if not any(
            entry.get("type") == "claim"
            and entry.get("content", {}).get("id") == claim_id
            for entry in entries
        ):
            return _err(f"E_CLAIM_NOT_FOUND: no claim with id {claim_id}")
        latest_decision: Optional[dict[str, Any]] = None
        for entry in entries:
            if (
                entry.get("type") == "decision"
                and entry.get("content", {}).get("claim_id") == claim_id
            ):
                latest_decision = entry["content"]
                break
        if latest_decision is not None:
            try:
                latest_outcome = _decision_outcome(latest_decision)
            except (KeyError, ValueError) as exc:
                return _err(f"E_DECISION_MALFORMED: {exc}")
            if latest_outcome != Outcome.DEFERRED:
                return _err(
                    "E_ALREADY_DECIDED: claim "
                    f"{claim_id} already has a terminal decision ({latest_outcome.value})"
                )

        content = {"claim_id": claim_id, **vote.to_dict()}
        h = self._cell.append_entry(
            entry_type="vote",
            author_did=voter,
            content=content,
        )
        return _ok({"entry_hash": h})

    # ------------------------------------------------------------------
    # Tool 3 — get_chain_context
    # ------------------------------------------------------------------

    def get_chain_context(self, limit: int = 20) -> str:
        """Return the most recent source chain entries as a JSON list, newest first.

        Bounded by `limit` to fit within LLM context windows. For Phase 0,
        callers should use limit=20–50. Pagination is a Phase 1 concern.
        """
        entries = self._cell.read_chain(limit=limit)
        return _ok(entries)

    # ------------------------------------------------------------------
    # Tool 4 — get_decision
    # ------------------------------------------------------------------

    def get_decision(self, claim_id: str) -> str:
        """Return the Decision entry content for a given claim_id, or null.

        Scans the chain for the most recent entry of type "decision" whose
        content.claim_id matches. Returns null JSON if not yet decided.
        """
        entries = self._cell.read_chain(limit=None)
        for entry in entries:
            if (
                entry.get("type") == "decision"
                and entry.get("content", {}).get("claim_id") == claim_id
            ):
                return _ok(entry["content"])
        return _ok(None)

    # ------------------------------------------------------------------
    # Tool 5 — list_pending
    # ------------------------------------------------------------------

    def list_pending(self) -> str:
        """Return Claims whose latest Decision is absent or still DEFERRED.

        Returns JSON list of {"claim_id": "<uuid>", "summary": "<text>"}.
        """
        entries = self._cell.read_chain(limit=None)
        latest_outcome_by_claim: dict[str, str] = {}
        for entry in entries:
            if entry.get("type") != "decision":
                continue
            claim_id = entry.get("content", {}).get("claim_id")
            if claim_id and claim_id not in latest_outcome_by_claim:
                latest_outcome_by_claim[claim_id] = entry["content"].get("outcome", "")
        pending = [
            {
                "claim_id": e["content"]["id"],
                "summary": e["content"].get("summary", ""),
                "blast_radius": e["content"].get("blast_radius", ""),
            }
            for e in entries
            if e.get("type") == "claim"
            and latest_outcome_by_claim.get(e.get("content", {}).get("id"))
            in (None, Outcome.DEFERRED.value)
        ]
        return _ok(pending)

    # ------------------------------------------------------------------
    # Tool 6 — run_consensus_round
    #
    # The loop-closer: looks up a pending Claim by id, runs the configured
    # voters against it (default = env-resolved balanced roster),
    # appends every Vote to the chain, then appends the Decision.
    #
    # submit_claim stays passive (spec §5 — router not controller). This
    # tool is where controllability lives, and it is invoked explicitly.
    # ------------------------------------------------------------------

    def run_consensus_round(self, claim_id: str) -> str:
        """Run the active voter roster, folding prior on-chain votes into the tally.

        Looks up the Claim on the source chain by id, refuses to re-run if a
        non-deferred Decision already exists for it, calls the voters from
        `self._voter_factory` (or the LiteLLM default), merges those new votes
        with any existing source-chain votes for the same claim, writes only the
        newly collected Vote entries, then writes the Decision under the
        "metacoordinator" system DID. Claims whose latest Decision is DEFERRED
        may be re-run so additional votes can progress them.

        Returns JSON: the full Decision.to_dict() (outcome, votes, tally_mean,
        tally_variance, etc.). On lookup or validation failure: {"error": ...}.
        """
        entries = self._cell.read_chain(limit=None)

        claim_entry: Optional[dict[str, Any]] = None
        for e in entries:
            if e.get("type") == "claim" and e.get("content", {}).get("id") == claim_id:
                claim_entry = e
                break
        if claim_entry is None:
            return _err(f"E_CLAIM_NOT_FOUND: no claim with id {claim_id}")

        latest_decision: Optional[dict[str, Any]] = None
        for entry in entries:
            if (
                entry.get("type") == "decision"
                and entry.get("content", {}).get("claim_id") == claim_id
            ):
                latest_decision = entry["content"]
                break
        if latest_decision is not None:
            try:
                latest_outcome = _decision_outcome(latest_decision)
            except (KeyError, ValueError) as exc:
                return _err(f"E_DECISION_MALFORMED: {exc}")
            if latest_outcome != Outcome.DEFERRED:
                return _err(
                    "E_ALREADY_DECIDED: claim "
                    f"{claim_id} already has a terminal decision ({latest_outcome.value})"
                )

        try:
            claim = _claim_from_chain_entry(claim_entry["content"])
        except (KeyError, ValueError) as exc:
            return _err(f"E_CLAIM_MALFORMED: {exc}")

        existing_votes_by_voter: dict[str, Vote] = {}
        for entry in entries:
            if (
                entry.get("type") != "vote"
                or entry.get("content", {}).get("claim_id") != claim_id
            ):
                continue
            try:
                vote = _vote_from_chain_entry(entry["content"])
            except (KeyError, TypeError, ValueError) as exc:
                return _err(f"E_VOTE_MALFORMED: {exc}")
            existing_votes_by_voter.setdefault(vote.voter, vote)

        # Resolve voter factory lazily so tests that don't hit this code
        # path never import voters.py or any provider SDKs.
        factory = self._voter_factory
        if factory is None:
            from packages.metacoordinator_mcp.voters import build_default_voters

            factory = build_default_voters

        try:
            voters = factory()
        except Exception as exc:  # noqa: BLE001
            return _err(f"E_VOTER_BUILD_FAILED: {type(exc).__name__}: {exc}")

        try:
            new_votes: list[Vote] = []
            seen_voters = set(existing_votes_by_voter)
            for voter in voters:
                known_name = _known_voter_name(voter)
                if known_name and known_name in seen_voters:
                    continue
                vote = voter(claim)
                vote.validate()
                if vote.voter in seen_voters:
                    continue
                seen_voters.add(vote.voter)
                new_votes.append(vote)
        except Exception as exc:  # noqa: BLE001
            return _err(f"E_CONSENSUS_FAILED: {type(exc).__name__}: {exc}")

        all_votes = [*existing_votes_by_voter.values(), *new_votes]
        if not new_votes and latest_decision is not None:
            if latest_decision.get("votes") == [vote.to_dict() for vote in all_votes]:
                return _ok(latest_decision)
        outcome, mean, variance = tally(claim, all_votes)
        decision = Decision(
            claim_id=claim.id,
            blast_radius=claim.blast_radius,
            outcome=outcome,
            votes=all_votes,
            tally_mean=mean,
            tally_variance=variance,
        )

        # Append each vote under the voter's identity, then the decision
        # under the system author. If a chain write fails mid-way we accept
        # a partial record — the next list_pending call will see it as
        # still-pending because the decision entry is the last to land.
        try:
            for vote in new_votes:
                self._cell.append_entry(
                    entry_type="vote",
                    author_did=vote.voter,
                    content={"claim_id": claim_id, **vote.to_dict()},
                )

            self._cell.append_entry(
                entry_type="decision",
                author_did="metacoordinator",
                content=decision.to_dict(),
            )
        except Exception as exc:  # noqa: BLE001
            return _err(f"E_CHAIN_WRITE_FAILED: {type(exc).__name__}: {exc}")

        return _ok(decision.to_dict())
