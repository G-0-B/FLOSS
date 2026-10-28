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
_REPO_ROOT = _THIS_DIR.parent.parent


def _load_repo_env() -> None:
    """Load repo-local `.env` so MCP-launched servers see provider credentials."""
    env_path = Path(os.environ.get("FLOSS_ENV_PATH", _REPO_ROOT / ".env")).expanduser()
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise RuntimeError(
            "python-dotenv is required to load repo credentials from "
            f"{env_path}. Install python-dotenv or remove the env file override."
        ) from exc
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
    evidence: list[dict] | None = None,
) -> str:
    """Submit a proposed change to the consensus gate.

    proposal_type: CodeChange | ConfigChange | SpecChange | AdrChange | Other
    blast_radius: Local | Module | System | Substrate
    evidence: optional list of provenance packets. Required for governed claims
        (System/Substrate blast radius with SpecChange/ConfigChange/AdrChange);
        without it those claims fail closed with E_GOVERNED_PROVENANCE_REQUIRED.
    Returns JSON with entry_hash and claim_id, or {"error": "..."} on failure.
    """
    return _gateway.submit_claim(
        proposer, proposal_type, summary, body, blast_radius, evidence=evidence
    )


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


_SERVER_INSTRUCTIONS = """\
FLOSSIØULLK Consensus Gateway — passive router, not a controller.

Invariants you MUST honor when using these tools:
- Vote weights are analog floats in [-0.999, +0.999]. Never use ±1.0.
- The gateway does not decide outcomes; it routes Claims to voters and
  appends Decisions. Treat outcomes as data, not directives.
- blast_radius selection:
      Local     = routine, single-module change. APPROVE threshold 0.30.
      Module    = config/spec change spanning files. APPROVE 0.50.
      System    = cross-module architectural shift. APPROVE 0.60.
      Substrate = invariant-touching, OVERRIDE FORBIDDEN. APPROVE 0.85.
- Every Claim is durable on the source chain. Submit only what you
  would commit to permanent provenance.
- Voters are LLMs with different cognitive styles (model family +
  persona). Variance > polarization_threshold returns CONFLICT
  requiring human resolution, not more votes.
"""

_WORKSPACE_ROOT = _REPO_ROOT.parent


def _audit_sink_path(filename: str) -> str:
    """Resolve the audit sink against the workspace, not a hardcoded absolute.

    This was the literal string "C:/~shit/.agent-surface/heartbeat/...". From
    any other checkout the audited calls landed outside that checkout's own
    advertised `.agent-surface` trail; on POSIX the Windows-looking value is not
    absolute at all, so it created a literal `C:/~shit/...` subtree under
    whatever the process working directory happened to be.

    An audit trail that writes somewhere other than where the operator is told
    to look is worse than none -- it reads as present.

    Override with FLOSS_AUDIT_DIR when the trail belongs elsewhere.
    """
    override = os.environ.get("FLOSS_AUDIT_DIR")
    base = (
        Path(override).expanduser()
        if override
        else _WORKSPACE_ROOT / ".agent-surface" / "heartbeat"
    )
    return str(base / filename)


_AUDIT_SINK = _audit_sink_path("janus-consensus-audit.jsonl")


def _create_mcp():
    """Build the FastMCP app when the optional MCP SDK is available."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        return None

    app = FastMCP("FLOSSIØULLK Consensus Gateway", instructions=_SERVER_INSTRUCTIONS)
    # Registered through register_audited_tools so each invocation lands in
    # _AUDIT_SINK. Registering the bare functions (the previous behaviour) left
    # audit_appender with no production caller and _AUDIT_SINK never read, so
    # every consensus tool call bypassed the audit trail entirely.
    from packages.mcp_daemon import register_audited_tools

    register_audited_tools(
        app,
        (
            submit_claim,
            cast_vote,
            get_chain_context,
            get_decision,
            list_pending,
            run_consensus_round,
        ),
        _AUDIT_SINK,
    )
    return app


mcp = _create_mcp()


if __name__ == "__main__":
    if mcp is None:
        raise ImportError("MCP SDK not installed. Run: pip install mcp")
    from packages.mcp_daemon import run_http_daemon

    run_http_daemon(mcp, pid_filename="consensus.pid", port=7331)
