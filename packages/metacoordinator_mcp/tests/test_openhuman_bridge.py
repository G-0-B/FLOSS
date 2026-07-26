import pytest
from pathlib import Path
from packages.source_chain.cell import CellDirectory
from packages.orchestrator.claim_schema import (
    Claim,
    Vote,
    ProposalType,
    BlastRadius,
    Outcome,
)
from packages.orchestrator.consensus_gate import decide


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

    # 3. OpenHuman 1 records its independent supporting evaluation locally.
    agent_1_vote = Vote(
        voter=agent_1_did,
        weight=0.85,
        rationale="My local Tauri traces observed the same parallel-sync starvation.",
    )
    agent_1_vote.validate()
    agent_1_vote_hash = openhuman_1_cell.append_entry(
        entry_type="vote",
        author_did=agent_1_did,
        content={"claim_id": claim_id_for_vote, "vote": agent_1_vote.to_dict()},
    )

    assert agent_1_vote_hash is not None
    chain_1 = openhuman_1_cell.read_chain()
    assert len(chain_1) == 2
    assert chain_1[0]["type"] == "vote"
    assert chain_1[0]["author_did"] == agent_1_did
    assert chain_1[0]["content"]["claim_id"] == claim_id_for_vote
    assert chain_1[0]["content"]["vote"]["voter"] == agent_1_vote.voter
    assert chain_1[0]["content"]["vote"]["weight"] == agent_1_vote.weight

    # 4. OpenHuman 2 receives the claim, evaluates it against its own memory, and votes.
    agent_2_did = "did:key:zOpenHuman2"

    oh_vote = Vote(
        voter=agent_2_did,
        weight=0.95,  # Strong support based on internal OpenHuman 2 memory
        rationale="My local SQLite traces confirm this pattern resolves starvation.",
    )
    oh_vote.validate()

    # 5. OpenHuman 2 appends the vote to its own local source chain.
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

    # 6. The FLOSSI0ULLK Consensus Gateway resolves the two-vote Module ballot.
    def agent_1_voter(_: Claim) -> Vote:
        return agent_1_vote

    def agent_2_voter(_: Claim) -> Vote:
        return oh_vote

    decision = decide(oh_claim, [agent_1_voter, agent_2_voter])

    assert decision.outcome == Outcome.APPROVED
    assert len(decision.votes) == 2
    assert [vote.voter for vote in decision.votes] == [agent_1_did, agent_2_did]
    assert decision.tally_mean == pytest.approx(0.90)
    assert decision.tally_variance == pytest.approx(0.0025)

    # Success! Two isolated personal AIs just formed a verifiable knowledge commons.
