"""
FLOSSI0ULLK Append-Only Epistemic Event Ledger.
Records immutable, content-addressed events for belief updates, evidence alignment, and claim proposals.
Part of Phase 2 (Task 2.3) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Literal, Any, Sequence

from .graph_schema import EpistemicGraph, EpistemicNode, EpistemicEdge

EventType = Literal[
    "SOURCE_ACQUIRED",
    "DOCUMENT_PARSED",
    "EVIDENCE_ALIGNED",
    "CLAIM_PROPOSED",
    "ASSESSMENT_RECORDED",
    "BELIEF_REVISED",
    "CLAIM_SUPERSEDED",
    "CLAIM_RETRACTED",
    "DECISION_RECORDED"
]

AuthorityTier = Literal[
    "non_authoritative",
    "provisional",
    "consensus_validated",
    "steward_governed"
]


@dataclass(frozen=True)
class EpistemicEvent:
    """An immutable, content-addressed event in the append-only ledger."""
    event_type: EventType
    event_id: str
    occurred_at: str
    actor: str
    inputs: list[str]
    outputs: list[str]
    policy_hash: str
    rationale_refs: list[str]
    authority_tier: AuthorityTier = "non_authoritative"
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": self.event_id,
            "occurred_at": self.occurred_at,
            "actor": self.actor,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "policy_hash": self.policy_hash,
            "rationale_refs": self.rationale_refs,
            "authority_tier": self.authority_tier,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EpistemicEvent:
        return cls(
            event_type=data["event_type"],
            event_id=str(data["event_id"]),
            occurred_at=str(data["occurred_at"]),
            actor=str(data["actor"]),
            inputs=list(data.get("inputs", [])),
            outputs=list(data.get("outputs", [])),
            policy_hash=str(data.get("policy_hash", "")),
            rationale_refs=list(data.get("rationale_refs", [])),
            authority_tier=data.get("authority_tier", "non_authoritative"),
            payload=dict(data.get("payload", {})),
        )


def create_epistemic_event(
    event_type: EventType,
    actor: str,
    inputs: list[str],
    outputs: list[str],
    policy_hash: str,
    rationale_refs: list[str],
    authority_tier: AuthorityTier = "non_authoritative",
    payload: Optional[dict[str, Any]] = None,
    occurred_at: Optional[str] = None
) -> EpistemicEvent:
    """Creates a content-addressed EpistemicEvent."""
    ts = occurred_at or datetime.datetime.now(datetime.timezone.utc).isoformat()
    raw_payload = payload or {}

    # Compute deterministic event_id
    id_body = {
        "event_type": event_type,
        "occurred_at": ts,
        "actor": actor,
        "inputs": sorted(inputs),
        "outputs": sorted(outputs),
        "policy_hash": policy_hash,
        "rationale_refs": sorted(rationale_refs),
        "authority_tier": authority_tier,
    }
    encoded = json.dumps(id_body, sort_keys=True).encode("utf-8")
    event_id = hashlib.sha256(encoded).hexdigest()

    return EpistemicEvent(
        event_type=event_type,
        event_id=event_id,
        occurred_at=ts,
        actor=actor,
        inputs=inputs,
        outputs=outputs,
        policy_hash=policy_hash,
        rationale_refs=rationale_refs,
        authority_tier=authority_tier,
        payload=raw_payload,
    )


class EventLedger:
    """Append-only storage and replay manager for epistemic events."""

    def __init__(self, log_path: Optional[Path | str] = None):
        self.log_path = Path(log_path) if log_path else None
        self.events: list[EpistemicEvent] = []

    def append(self, event: EpistemicEvent) -> str:
        """Appends an event to memory and optionally writes to JSONL on disk."""
        self.events.append(event)
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        return event.event_id

    def load_from_disk(self) -> None:
        """Loads events from the JSONL log file if it exists."""
        if self.log_path and self.log_path.is_file():
            self.events = []
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        self.events.append(EpistemicEvent.from_dict(json.loads(line)))

    def replay_to_graph(self) -> EpistemicGraph:
        """Reconstructs the EpistemicGraph from the sequence of events."""
        graph = EpistemicGraph()
        for ev in self.events:
            ev_node = EpistemicNode(
                node_id=f"event:{ev.event_id}",
                node_type="Observation",
                payload={"event_type": ev.event_type, "actor": ev.actor},
                created_at=ev.occurred_at
            )
            graph.add_node(ev_node)

            for inp in ev.inputs:
                if inp not in graph.nodes:
                    graph.add_node(EpistemicNode(node_id=inp, node_type="Observation"))
                graph.add_edge(EpistemicEdge(source_id=inp, target_id=ev_node.node_id, edge_type="updates"))

            for out in ev.outputs:
                if out not in graph.nodes:
                    graph.add_node(EpistemicNode(node_id=out, node_type="Observation"))
                graph.add_edge(EpistemicEdge(source_id=ev_node.node_id, target_id=out, edge_type="derived_from"))

        return graph
