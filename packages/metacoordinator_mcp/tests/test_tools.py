"""Tests for MCP gateway tool handlers (spec §5.2)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.metacoordinator_mcp.tools import GatewayTools  # noqa: E402
from packages.orchestrator.claim_schema import Vote  # noqa: E402

DNA_HASH = "b" * 64


def _approval_voter_factory():
    """Return a deterministic approving voter roster for gateway tests."""
    return [
        lambda claim: Vote(
            voter="groq-reviewer",
            weight=0.8,
            rationale=f"Approve {claim.id}",
        )
    ]


def make_gateway(tmp: str, voter_factory=None) -> GatewayTools:
    """Construct a test gateway rooted in a temporary source-chain directory."""
    return GatewayTools(
        base_dir=Path(tmp),
        dna_hash=DNA_HASH,
        voter_factory=voter_factory,
    )


def test_submit_claim_returns_entry_hash():
    """submit_claim() returns JSON with entry_hash (64 hex chars) and claim_id."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="CodeChange",
                summary="Add feature X",
                body="Detailed description of change",
                blast_radius="Local",
            )
        )
        assert "entry_hash" in result
        assert len(result["entry_hash"]) == 64
        assert "claim_id" in result


def test_cast_vote_returns_entry_hash():
    """cast_vote() returns JSON with entry_hash."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        claim_result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="CodeChange",
                summary="test",
                body="body",
                blast_radius="Local",
            )
        )
        vote_result = json.loads(
            gw.cast_vote(
                claim_id=claim_result["claim_id"],
                voter="gemini",
                weight=0.8,
                rationale="Looks good to me",
            )
        )
        assert "entry_hash" in vote_result
        assert len(vote_result["entry_hash"]) == 64


def test_cast_vote_rejects_unknown_claim_id():
    """cast_vote() rejects orphan votes whose claim_id is not present on-chain."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        result = json.loads(
            gw.cast_vote(
                claim_id="00000000-0000-7000-8000-000000000000",
                voter="gemini",
                weight=0.2,
                rationale="unknown claim",
            )
        )
        assert "error" in result
        assert "E_CLAIM_NOT_FOUND" in result["error"]


def test_get_chain_context_returns_list():
    """get_chain_context() returns a JSON list with at least the submitted claim."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        gw.submit_claim(
            proposer="claude",
            proposal_type="CodeChange",
            summary="test",
            body="body",
            blast_radius="Local",
        )
        result = json.loads(gw.get_chain_context(limit=10))
        assert isinstance(result, list)
        assert len(result) >= 1


def test_list_pending_returns_empty_when_no_claims():
    """list_pending() returns an empty list when no claims exist."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        result = json.loads(gw.list_pending())
        assert result == []


def test_list_pending_returns_unresolved_claims():
    """list_pending() includes submitted claims that have no Decision yet."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        claim_result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="CodeChange",
                summary="pending claim",
                body="body",
                blast_radius="Local",
            )
        )
        pending = json.loads(gw.list_pending())
        claim_ids = [c["claim_id"] for c in pending]
        assert claim_result["claim_id"] in claim_ids


def test_list_pending_includes_deferred_claims():
    """list_pending() keeps claims visible when their latest decision is DEFERRED."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        claim_result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="CodeChange",
                summary="needs more signal",
                body="body",
                blast_radius="Local",
            )
        )
        gw._cell.append_entry(
            entry_type="decision",
            author_did="metacoordinator",
            content={"claim_id": claim_result["claim_id"], "outcome": "DEFERRED"},
        )
        pending = json.loads(gw.list_pending())
        claim_ids = [c["claim_id"] for c in pending]
        assert claim_result["claim_id"] in claim_ids


def test_get_decision_returns_null_when_no_decision():
    """get_decision() returns null JSON when no Decision entry exists for the claim."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        claim_result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="CodeChange",
                summary="undecided",
                body="body",
                blast_radius="Local",
            )
        )
        result = json.loads(gw.get_decision(claim_result["claim_id"]))
        assert result is None


def test_submit_claim_rejects_invalid_blast_radius():
    """submit_claim() returns JSON with 'error' key for unknown blast_radius."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="CodeChange",
                summary="test",
                body="body",
                blast_radius="INVALID",
            )
        )
        assert "error" in result


def test_cast_vote_rejects_weight_above_limit():
    """cast_vote() returns JSON with 'error' key when weight > CERTAINTY_LIMIT."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        result = json.loads(
            gw.cast_vote(
                claim_id="00000000-0000-7000-8000-000000000000",
                voter="bad",
                weight=1.0,  # must be <= CERTAINTY_LIMIT=0.999
                rationale="test",
            )
        )
        assert "error" in result


def test_cast_vote_rejects_invalid_proposal_type():
    """submit_claim() returns JSON with 'error' key for unknown proposal_type."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="BOGUS",
                summary="test",
                body="body",
                blast_radius="Local",
            )
        )
        assert "error" in result


def test_run_consensus_round_finds_old_claim_beyond_500_entries():
    """run_consensus_round() can still locate a buried claim on a long chain."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp, voter_factory=_approval_voter_factory)
        claim_result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="CodeChange",
                summary="old claim",
                body="body",
                blast_radius="Local",
            )
        )
        for i in range(501):
            gw.submit_claim(
                proposer="noise",
                proposal_type="CodeChange",
                summary=f"noise {i}",
                body="body",
                blast_radius="Local",
            )
        decision = json.loads(gw.run_consensus_round(claim_result["claim_id"]))
        assert decision["claim_id"] == claim_result["claim_id"]
        assert decision["outcome"] == "APPROVED"


def test_run_consensus_round_detects_buried_existing_decision():
    """Idempotency check still sees older decisions after 500 newer entries."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp, voter_factory=_approval_voter_factory)
        claim_result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="CodeChange",
                summary="already decided",
                body="body",
                blast_radius="Local",
            )
        )
        gw._cell.append_entry(
            entry_type="decision",
            author_did="metacoordinator",
            content={"claim_id": claim_result["claim_id"], "outcome": "APPROVED"},
        )
        for i in range(501):
            gw.submit_claim(
                proposer="noise",
                proposal_type="CodeChange",
                summary=f"noise {i}",
                body="body",
                blast_radius="Local",
            )
        result = json.loads(gw.run_consensus_round(claim_result["claim_id"]))
        assert "error" in result
        assert "E_ALREADY_DECIDED" in result["error"]


def test_run_consensus_round_counts_existing_manual_votes():
    """run_consensus_round() tallies prior chain votes alongside new automated votes."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp, voter_factory=_approval_voter_factory)
        claim_result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="CodeChange",
                summary="manual vote should count",
                body="body",
                blast_radius="Local",
            )
        )
        json.loads(
            gw.cast_vote(
                claim_id=claim_result["claim_id"],
                voter="human-reviewer",
                weight=-0.8,
                rationale="Needs work first",
            )
        )
        decision = json.loads(gw.run_consensus_round(claim_result["claim_id"]))
        assert decision["claim_id"] == claim_result["claim_id"]
        assert decision["outcome"] == "CONFLICT"
        assert decision["tally_mean"] == 0.0
        assert {vote["voter"] for vote in decision["votes"]} == {
            "human-reviewer",
            "groq-reviewer",
        }


def test_run_consensus_round_allows_rerun_after_deferred():
    """run_consensus_round() may progress claims whose latest decision is DEFERRED."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp, voter_factory=_approval_voter_factory)
        claim_result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="CodeChange",
                summary="deferred can progress",
                body="body",
                blast_radius="Local",
            )
        )
        gw._cell.append_entry(
            entry_type="decision",
            author_did="metacoordinator",
            content={"claim_id": claim_result["claim_id"], "outcome": "DEFERRED"},
        )
        decision = json.loads(gw.run_consensus_round(claim_result["claim_id"]))
        assert decision["claim_id"] == claim_result["claim_id"]
        assert decision["outcome"] == "APPROVED"


def test_get_decision_finds_buried_decision():
    """get_decision() traverses past the last 500 entries when needed."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        claim_result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="CodeChange",
                summary="buried decision",
                body="body",
                blast_radius="Local",
            )
        )
        gw._cell.append_entry(
            entry_type="decision",
            author_did="metacoordinator",
            content={"claim_id": claim_result["claim_id"], "outcome": "APPROVED"},
        )
        for i in range(501):
            gw.submit_claim(
                proposer="noise",
                proposal_type="CodeChange",
                summary=f"noise {i}",
                body="body",
                blast_radius="Local",
            )
        decision = json.loads(gw.get_decision(claim_result["claim_id"]))
        assert decision["claim_id"] == claim_result["claim_id"]
        assert decision["outcome"] == "APPROVED"


def test_run_consensus_round_returns_json_error_on_write_failure():
    """Chain write failures are surfaced as parseable JSON errors."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp, voter_factory=_approval_voter_factory)
        claim_result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="CodeChange",
                summary="write failure",
                body="body",
                blast_radius="Local",
            )
        )

        def fail_append_entry(*args, **kwargs):
            """Simulate a source-chain append failure from the storage layer."""
            raise OSError("disk full")

        gw._cell.append_entry = fail_append_entry
        result = json.loads(gw.run_consensus_round(claim_result["claim_id"]))
        assert "error" in result
        assert "E_CHAIN_WRITE_FAILED" in result["error"]
        assert "disk full" in result["error"]


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------


def _run_all():
    """Run the standalone gateway test bundle without invoking pytest."""
    tests = [
        test_submit_claim_returns_entry_hash,
        test_cast_vote_returns_entry_hash,
        test_cast_vote_rejects_unknown_claim_id,
        test_get_chain_context_returns_list,
        test_list_pending_returns_empty_when_no_claims,
        test_list_pending_returns_unresolved_claims,
        test_list_pending_includes_deferred_claims,
        test_get_decision_returns_null_when_no_decision,
        test_submit_claim_rejects_invalid_blast_radius,
        test_cast_vote_rejects_weight_above_limit,
        test_cast_vote_rejects_invalid_proposal_type,
        test_run_consensus_round_finds_old_claim_beyond_500_entries,
        test_run_consensus_round_detects_buried_existing_decision,
        test_run_consensus_round_counts_existing_manual_votes,
        test_run_consensus_round_allows_rerun_after_deferred,
        test_get_decision_finds_buried_decision,
        test_run_consensus_round_returns_json_error_on_write_failure,
    ]
    passed = failed = 0
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
