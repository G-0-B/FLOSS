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

from packages.metacoordinator_mcp.tools import GatewayTools

DNA_HASH = "b" * 64


def make_gateway(tmp: str) -> GatewayTools:
    return GatewayTools(base_dir=Path(tmp), dna_hash=DNA_HASH)


def test_submit_claim_returns_entry_hash():
    """submit_claim() returns JSON with entry_hash (64 hex chars) and claim_id."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        result = json.loads(gw.submit_claim(
            proposer="claude",
            proposal_type="CodeChange",
            summary="Add feature X",
            body="Detailed description of change",
            blast_radius="Local",
        ))
        assert "entry_hash" in result
        assert len(result["entry_hash"]) == 64
        assert "claim_id" in result


def test_cast_vote_returns_entry_hash():
    """cast_vote() returns JSON with entry_hash."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        claim_result = json.loads(gw.submit_claim(
            proposer="claude", proposal_type="CodeChange",
            summary="test", body="body", blast_radius="Local",
        ))
        vote_result = json.loads(gw.cast_vote(
            claim_id=claim_result["claim_id"],
            voter="gemini",
            weight=0.8,
            rationale="Looks good to me",
        ))
        assert "entry_hash" in vote_result
        assert len(vote_result["entry_hash"]) == 64


def test_get_chain_context_returns_list():
    """get_chain_context() returns a JSON list with at least the submitted claim."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        gw.submit_claim(
            proposer="claude", proposal_type="CodeChange",
            summary="test", body="body", blast_radius="Local",
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
        claim_result = json.loads(gw.submit_claim(
            proposer="claude", proposal_type="CodeChange",
            summary="pending claim", body="body", blast_radius="Local",
        ))
        pending = json.loads(gw.list_pending())
        claim_ids = [c["claim_id"] for c in pending]
        assert claim_result["claim_id"] in claim_ids


def test_get_decision_returns_null_when_no_decision():
    """get_decision() returns null JSON when no Decision entry exists for the claim."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        claim_result = json.loads(gw.submit_claim(
            proposer="claude", proposal_type="CodeChange",
            summary="undecided", body="body", blast_radius="Local",
        ))
        result = json.loads(gw.get_decision(claim_result["claim_id"]))
        assert result is None


def test_submit_claim_rejects_invalid_blast_radius():
    """submit_claim() returns JSON with 'error' key for unknown blast_radius."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        result = json.loads(gw.submit_claim(
            proposer="claude", proposal_type="CodeChange",
            summary="test", body="body", blast_radius="INVALID",
        ))
        assert "error" in result


def test_cast_vote_rejects_weight_above_limit():
    """cast_vote() returns JSON with 'error' key when weight > CERTAINTY_LIMIT."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        result = json.loads(gw.cast_vote(
            claim_id="00000000-0000-7000-8000-000000000000",
            voter="bad",
            weight=1.0,  # must be <= CERTAINTY_LIMIT=0.999
            rationale="test",
        ))
        assert "error" in result


def test_cast_vote_rejects_invalid_proposal_type():
    """submit_claim() returns JSON with 'error' key for unknown proposal_type."""
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        result = json.loads(gw.submit_claim(
            proposer="claude", proposal_type="BOGUS",
            summary="test", body="body", blast_radius="Local",
        ))
        assert "error" in result


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------

def _run_all():
    tests = [
        test_submit_claim_returns_entry_hash,
        test_cast_vote_returns_entry_hash,
        test_get_chain_context_returns_list,
        test_list_pending_returns_empty_when_no_claims,
        test_list_pending_returns_unresolved_claims,
        test_get_decision_returns_null_when_no_decision,
        test_submit_claim_rejects_invalid_blast_radius,
        test_cast_vote_rejects_weight_above_limit,
        test_cast_vote_rejects_invalid_proposal_type,
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
