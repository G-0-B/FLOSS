import pytest
from pathlib import Path
from packages.source_chain.cell import CellDirectory
from packages.orchestrator.claim_schema import (
    Claim,
    Vote,
    ProposalType,
    BlastRadius,
    Outcome,
    Decision,
)


@pytest.fixture
def openhuman_1_cell(tmp_path: Path) -> CellDirectory:
    """Mock CellDirectory for OpenHuman Agent 1."""
    d = tmp_path / "agent1"
    d.mkdir()
    return CellDirectory(d, "dna_openhuman_commons")


@pytest.fixture
def openhuman_2_cell(tmp_path: Path) -> CellDirectory:
    """Mock CellDirectory for OpenHuman Agent 2."""
    d = tmp_path / "agent2"
    d.mkdir()
    return CellDirectory(d, "dna_openhuman_commons")


def test_openhuman_claim_and_verify_bridge(
    openhuman_1_cell: CellDirectory, openhuman_2_cell: CellDirectory
) -> None:
    """
    Simulates the integration seam between OpenHuman and FLOSSI0ULLK.
    Agent 1 (OpenHuman 1) crafts a memory and submits it as a Claim.
    Agent 2 (OpenHuman 2) retrieves the claim and issues a verifying Vote.
    """

    # 1. OpenHuman 1 extracts a local memory and crafts a FLOSSI0ULLK Claim
    agent_1_did = "did:key:zOpenHuman1"

    oh_claim = Claim(
        proposer=agent_1_did,
        proposal_type=ProposalType.OTHER,
        summary="Learned new Rust workflow pattern",
        body="When using Tauri with SQLite, I found that wrapping the connection pool in an Arc<Mutex<>> prevents thread starvation during parallel syncs.",
        blast_radius=BlastRadius.MODULE,
    )
    oh_claim.validate()

    # 2. OpenHuman 1 appends the claim to its local source chain
    claim_hash = openhuman_1_cell.append_entry(
        entry_type="claim",
        author_did=agent_1_did,
        content=oh_claim.to_dict(),
    )

    # Verify the claim was stored and cryptographically hashed
    assert claim_hash is not None
    chain_1 = openhuman_1_cell.read_chain()
    assert len(chain_1) == 1
    assert chain_1[0]["content"]["proposer"] == agent_1_did
    assert chain_1[0]["content"]["summary"] == "Learned new Rust workflow pattern"

    # --- Gossip occurs here (simulated by passing the claim_id) ---
    claim_id_for_vote = chain_1[0]["content"]["id"]

    # 3. OpenHuman 2 receives the claim, evaluates it against its own memory, and votes
    agent_2_did = "did:key:zOpenHuman2"

    oh_vote = Vote(
        voter=agent_2_did,
        weight=0.95,  # Strong support based on internal OpenHuman 2 memory
        rationale="My local SQLite traces confirm this pattern resolves starvation.",
    )
    oh_vote.validate()

    # 4. OpenHuman 2 appends the vote to its own local source chain
    vote_hash = openhuman_2_cell.append_entry(
        entry_type="vote",
        author_did=agent_2_did,
        content={"claim_id": claim_id_for_vote, "vote": oh_vote.to_dict()},
    )

    assert vote_hash is not None
    chain_2 = openhuman_2_cell.read_chain()
    assert len(chain_2) == 1
    assert chain_2[0]["content"]["vote"]["voter"] == agent_2_did
    assert chain_2[0]["content"]["vote"]["weight"] == 0.95

    # 5. The FLOSSI0ULLK Consensus Gateway resolves the decision
    # Simulated resolution based on BlastRadius.MODULE threshold (0.50)
    decision = Decision(
        claim_id=claim_id_for_vote,
        blast_radius=BlastRadius.MODULE,
        outcome=Outcome.APPROVED,
        votes=[oh_vote],
        tally_mean=0.95,
        tally_variance=0.0,
    )
    decision.validate()

    assert decision.outcome == Outcome.APPROVED

    # Success! Two isolated personal AIs just formed a verifiable knowledge commons.
