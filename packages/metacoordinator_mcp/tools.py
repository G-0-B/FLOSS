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

from packages.orchestrator.claim_schema import (
    CERTAINTY_LIMIT,
    BlastRadius,
    Claim,
    EvidenceRef,
    ProposalType,
    TruthStatus,
    Vote,
)
from packages.orchestrator.consensus_gate import decide
from packages.source_chain.cell import CellDirectory

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
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def _err(msg: str) -> str:
    return json.dumps({"error": msg}, separators=(",", ":"))


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
        for item in (evidence or []):
            try:
                ref = EvidenceRef(type=item["type"], ref=item["ref"])
                ref.validate()
                ev_refs.append(ref)
            except (KeyError, ValueError) as exc:
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
        entries = self._cell.read_chain(limit=500)
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
        """Return all Claims that have no corresponding Decision entry yet.

        Returns JSON list of {"claim_id": "<uuid>", "summary": "<text>"}.
        """
        entries = self._cell.read_chain(limit=500)
        decided_claim_ids = {
            e["content"]["claim_id"]
            for e in entries
            if e.get("type") == "decision" and "claim_id" in e.get("content", {})
        }
        pending = [
            {
                "claim_id": e["content"]["id"],
                "summary": e["content"].get("summary", ""),
                "blast_radius": e["content"].get("blast_radius", ""),
            }
            for e in entries
            if e.get("type") == "claim"
            and e.get("content", {}).get("id") not in decided_claim_ids
        ]
        return _ok(pending)

    # ------------------------------------------------------------------
    # Tool 6 — run_consensus_round
    #
    # The loop-closer: looks up a pending Claim by id, runs the configured
    # voters against it (default = Cerebras + Groq GPT-OSS + Groq Qwen3),
    # appends every Vote to the chain, then appends the Decision.
    #
    # submit_claim stays passive (spec §5 — router not controller). This
    # tool is where controllability lives, and it is invoked explicitly.
    # ------------------------------------------------------------------

    def run_consensus_round(self, claim_id: str) -> str:
        """Run the default voter roster against a pending Claim and record the Decision.

        Looks up the Claim on the source chain by id, refuses to re-run if a
        Decision already exists for it, calls `decide()` with the voters from
        `self._voter_factory` (or the LiteLLM default), writes each Vote to
        the chain under the voter's DID, then writes the Decision under the
        "metacoordinator" system DID.

        Returns JSON: the full Decision.to_dict() (outcome, votes, tally_mean,
        tally_variance, etc.). On lookup or validation failure: {"error": ...}.
        """
        entries = self._cell.read_chain(limit=500)

        claim_entry: Optional[dict[str, Any]] = None
        for e in entries:
            if (
                e.get("type") == "claim"
                and e.get("content", {}).get("id") == claim_id
            ):
                claim_entry = e
                break
        if claim_entry is None:
            return _err(f"E_CLAIM_NOT_FOUND: no claim with id {claim_id}")

        # Idempotency: don't double-vote on an already-decided claim. The
        # chain is append-only so a stale re-run would produce confusing
        # duplicate votes with conflicting weights.
        for e in entries:
            if (
                e.get("type") == "decision"
                and e.get("content", {}).get("claim_id") == claim_id
            ):
                return _err(
                    f"E_ALREADY_DECIDED: claim {claim_id} already has a decision"
                )

        try:
            claim = _claim_from_chain_entry(claim_entry["content"])
        except (KeyError, ValueError) as exc:
            return _err(f"E_CLAIM_MALFORMED: {exc}")

        # Resolve voter factory lazily so tests that don't hit this code
        # path never import voters.py (and therefore never import litellm).
        factory = self._voter_factory
        if factory is None:
            from packages.metacoordinator_mcp.voters import build_default_voters
            factory = build_default_voters

        try:
            voters = factory()
        except Exception as exc:  # noqa: BLE001
            return _err(f"E_VOTER_BUILD_FAILED: {type(exc).__name__}: {exc}")

        try:
            decision = decide(claim, voters)
        except Exception as exc:  # noqa: BLE001
            return _err(f"E_CONSENSUS_FAILED: {type(exc).__name__}: {exc}")

        # Append each vote under the voter's identity, then the decision
        # under the system author. If a chain write fails mid-way we accept
        # a partial record — the next list_pending call will see it as
        # still-pending because the decision entry is the last to land.
        for vote in decision.votes:
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

        return _ok(decision.to_dict())
