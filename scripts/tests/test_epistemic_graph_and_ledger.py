"""
Unit tests for FLOSS/scripts/epistemic/ (Graph, Ledger, BeliefPolicy).
Verifies DAG indexing, content-addressed event logging, and deterministic belief transitions.
Part of Phase 2 (Task 2.3) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import pytest

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from epistemic.graph_schema import EpistemicNode, EpistemicEdge, EpistemicGraph
from epistemic.event_ledger import EpistemicEvent, EventLedger, create_epistemic_event
from epistemic.belief_policy import BeliefState, BeliefUpdatePolicy
from claim_candidate import ClaimVersion, NormalizedTriple
from entailment_gate import EntailmentAssessment


def test_epistemic_graph_dag_indexing():
    graph = EpistemicGraph()
    n_claim = EpistemicNode(node_id="claim:001", node_type="ClaimVersion")
    n_ev = EpistemicNode(node_id="ev:001", node_type="EvidenceAtom")
    n_asm = EpistemicNode(node_id="asm:001", node_type="Assessment")

    graph.add_node(n_claim)
    graph.add_node(n_ev)
    graph.add_node(n_asm)

    e1 = EpistemicEdge(source_id="ev:001", target_id="asm:001", edge_type="qualifies")
    e2 = EpistemicEdge(source_id="asm:001", target_id="claim:001", edge_type="supports")

    graph.add_edge(e1)
    graph.add_edge(e2)

    assert graph.get_node("claim:001") == n_claim
    assert len(graph.get_incoming("claim:001", edge_type="supports")) == 1
    assert len(graph.get_outgoing("ev:001", edge_type="qualifies")) == 1


def test_event_ledger_content_addressing_and_replay():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "events.jsonl"
        ledger = EventLedger(log_path=log_file)

        ev1 = create_epistemic_event(
            event_type="CLAIM_PROPOSED",
            actor="model:nuextract3",
            inputs=["doc:p01"],
            outputs=["claim:001"],
            policy_hash="p-v1",
            rationale_refs=["ev:001"]
        )

        ev2 = create_epistemic_event(
            event_type="ASSESSMENT_RECORDED",
            actor="rule:entailment-v1",
            inputs=["claim:001", "ev:001"],
            outputs=["asm:001"],
            policy_hash="p-v1",
            rationale_refs=["ev:001"]
        )

        ledger.append(ev1)
        ledger.append(ev2)

        # Re-load from disk
        ledger_restored = EventLedger(log_path=log_file)
        ledger_restored.load_from_disk()
        assert len(ledger_restored.events) == 2
        assert ledger_restored.events[0].event_id == ev1.event_id

        # Replay to graph
        g = ledger_restored.replay_to_graph()
        assert len(g.nodes) >= 4  # event nodes + referenced input/output nodes


def test_belief_update_policy_transitions():
    policy = BeliefUpdatePolicy()
    claim = ClaimVersion(
        claim_id="clm-test",
        claim_version=1,
        claim_type="causal",
        statement="Test statement",
        subject_surface="S",
        relation_surface="R",
        object_surface="O",
        normalized_triple=NormalizedTriple(subject="s", predicate="r", object="o")
    )

    # 1. Assessment is SUPPORTED -> ACTIVE_BELIEF (+0.850)
    asm_supported = EntailmentAssessment(
        assessment_id="asm-01",
        claim_id=claim.claim_id,
        claim_version=1,
        evidence_atom_ids=["ev-01"],
        support=True,
        refutation=False,
        rationale="Entailed"
    )
    b_state1, ev1 = policy.apply_assessment(None, claim, asm_supported)
    assert b_state1.disposition == "ACTIVE_BELIEF"
    assert b_state1.signed_confidence == 0.850
    assert b_state1.active is True
    assert ev1.event_type == "BELIEF_REVISED"

    # 2. Assessment is CONTRADICTED -> CONTRADICTED (-0.900)
    asm_contradicted = EntailmentAssessment(
        assessment_id="asm-02",
        claim_id=claim.claim_id,
        claim_version=1,
        evidence_atom_ids=["ev-02"],
        support=False,
        refutation=True,
        rationale="Polarity inverted"
    )
    b_state2, ev2 = policy.apply_assessment(b_state1, claim, asm_contradicted)
    assert b_state2.disposition == "CONTRADICTED"
    assert b_state2.signed_confidence == -0.900
    assert b_state2.active is False

    # 3. Assessment is CONFLICTING -> SUSPENDED (0.000)
    asm_conflicting = EntailmentAssessment(
        assessment_id="asm-03",
        claim_id=claim.claim_id,
        claim_version=1,
        evidence_atom_ids=["ev-01", "ev-02"],
        support=True,
        refutation=True,
        rationale="Mixed evidence"
    )
    b_state3, ev3 = policy.apply_assessment(b_state2, claim, asm_conflicting)
    assert b_state3.disposition == "SUSPENDED"
    assert b_state3.signed_confidence == 0.000
    assert b_state3.active is False
