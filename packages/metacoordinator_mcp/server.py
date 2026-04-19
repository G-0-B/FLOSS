"""
FastMCP server for the FLOSSIØULLK consensus gateway.

Exposes the 5 tools from spec §5.2 via the MCP protocol. The server is a
router/switch — it routes Claims to voters and appends results to the
file-based source chain. It does NOT decide outcomes or command voters.

Usage:
    python -m packages.metacoordinator_mcp.server

Environment variables:
    FLOSS_AGENT_DIR   Base directory for cell storage (default: ~/.floss_agent)
    FLOSS_DNA_HASH    64-char hex dna_hash for the active cell (default: zeros)
    FLOSS_VOTER_PROFILE  Built-in roster profile (`balanced` default; `fast`,
                         `flowith`, `subscriptions`, and `amplified` optional)
    FLOSS_VOTER_ROSTER   Full `name=model` roster override
    FLOSS_EXTRA_VOTERS   Extra `name=model` voters appended to the built-in profile
"""

from __future__ import annotations

import os
from pathlib import Path

from .tools import GatewayTools

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent


def _load_repo_env() -> None:
    """Load repo-local `.env` so MCP-launched servers see provider credentials."""
    env_path = Path(os.environ.get("FLOSS_ENV_PATH", _REPO_ROOT / ".env")).expanduser()
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(env_path, override=False)


_load_repo_env()

BASE_DIR = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
DNA_HASH = os.environ.get("FLOSS_DNA_HASH", "0" * 64)

_gateway = GatewayTools(base_dir=BASE_DIR, dna_hash=DNA_HASH)


def submit_claim(
    proposer: str,
    proposal_type: str,
    summary: str,
    body: str,
    blast_radius: str,
) -> str:
    """Submit a proposed change to the consensus gate.

    proposal_type: CodeChange | ConfigChange | SpecChange | AdrChange | Other
    blast_radius: Local | Module | System | Substrate
    Returns JSON with entry_hash and claim_id, or {"error": "..."} on failure.
    """
    return _gateway.submit_claim(proposer, proposal_type, summary, body, blast_radius)


def cast_vote(claim_id: str, voter: str, weight: float, rationale: str) -> str:
    """Cast an analog vote on a pending Claim.

    weight: float in [-0.999, 0.999]. Positive = support, negative = oppose.
    Returns JSON with entry_hash, or {"error": "..."} on failure.
    """
    return _gateway.cast_vote(claim_id, voter, weight, rationale)


def get_chain_context(limit: int = 20) -> str:
    """Return the most recent source chain entries for voter context.

    Returns JSON list, newest first. Use limit to stay within token budgets.
    """
    return _gateway.get_chain_context(limit)


def get_decision(claim_id: str) -> str:
    """Return the Decision for a given claim_id, or null if not yet decided."""
    return _gateway.get_decision(claim_id)


def list_pending() -> str:
    """List all Claims that have not yet received a Decision."""
    return _gateway.list_pending()


def run_consensus_round(claim_id: str) -> str:
    """Run the active voter roster against a pending Claim and append the Decision.

    Resolves voters from the env-aware profile system in `voters.py`, calls every
    voter on the claim, appends each Vote to the chain, then appends the
    resulting Decision. Idempotent: a claim that already has a Decision returns
    {"error": "E_ALREADY_DECIDED"}.

    Returns JSON with the full Decision (outcome, votes, tally_mean,
    tally_variance), or {"error": "..."} on lookup / voter / tally failure.
    """
    return _gateway.run_consensus_round(claim_id)


def _create_mcp():
    """Build the FastMCP app when the optional MCP SDK is available."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        return None

    app = FastMCP("FLOSSIØULLK Consensus Gateway")
    for tool in (
        submit_claim,
        cast_vote,
        get_chain_context,
        get_decision,
        list_pending,
        run_consensus_round,
    ):
        app.tool()(tool)
    return app


mcp = _create_mcp()


if __name__ == "__main__":
    if mcp is None:
        raise ImportError("MCP SDK not installed. Run: pip install mcp")
    mcp.run()
