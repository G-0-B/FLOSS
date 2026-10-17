"""
FLOSSI0ULLK Epistemic State Graph Node & Edge Schemas.
Represents the DAG of observations, hypotheses, claims, assessments, and revisions.
Part of Phase 2 (Task 2.3) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal, Any, Sequence

NodeType = Literal[
    "SourceArtifact",
    "DocumentRevision",
    "EvidenceAtom",
    "ClaimVersion",
    "Hypothesis",
    "Question",
    "TestPlan",
    "TestExecution",
    "Observation",
    "Assessment",
    "BeliefState",
    "Decision",
    "PolicyVersion"
]

EdgeType = Literal[
    "derived_from",
    "observed_in",
    "supports",
    "refutes",
    "contextualizes",
    "attributes_to",
    "qualifies",
    "tests",
    "depends_on",
    "updates",
    "supersedes",
    "retracts",
    "disagrees_with",
    "requires_review",
    "authorized_by"
]


@dataclass(frozen=True)
class EpistemicNode:
    """A typed vertex in the Epistemic State Graph."""
    node_id: str
    node_type: NodeType
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "payload": self.payload,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EpistemicNode:
        return cls(
            node_id=str(data["node_id"]),
            node_type=data.get("node_type", "ClaimVersion"),
            payload=dict(data.get("payload", {})),
            created_at=str(data.get("created_at", "")),
        )


@dataclass(frozen=True)
class EpistemicEdge:
    """A typed provenance, entailment, or revision relation between two epistemic vertices."""
    source_id: str
    target_id: str
    edge_type: EdgeType
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EpistemicEdge:
        return cls(
            source_id=str(data["source_id"]),
            target_id=str(data["target_id"]),
            edge_type=data.get("edge_type", "derived_from"),
            metadata=dict(data.get("metadata", {})),
        )


class EpistemicGraph:
    """In-memory DAG representation of the epistemic state with adjacency indices."""

    def __init__(self):
        self.nodes: dict[str, EpistemicNode] = {}
        self.edges: list[EpistemicEdge] = []
        self._out_edges: dict[str, list[EpistemicEdge]] = {}
        self._in_edges: dict[str, list[EpistemicEdge]] = {}

    def add_node(self, node: EpistemicNode) -> None:
        self.nodes[node.node_id] = node
        if node.node_id not in self._out_edges:
            self._out_edges[node.node_id] = []
        if node.node_id not in self._in_edges:
            self._in_edges[node.node_id] = []

    def add_edge(self, edge: EpistemicEdge) -> None:
        if edge.source_id not in self.nodes:
            raise KeyError(f"Source node {edge.source_id} does not exist in graph")
        if edge.target_id not in self.nodes:
            raise KeyError(f"Target node {edge.target_id} does not exist in graph")

        self.edges.append(edge)
        self._out_edges[edge.source_id].append(edge)
        self._in_edges[edge.target_id].append(edge)

    def get_node(self, node_id: str) -> Optional[EpistemicNode]:
        return self.nodes.get(node_id)

    def get_outgoing(self, node_id: str, edge_type: Optional[EdgeType] = None) -> list[EpistemicEdge]:
        out = self._out_edges.get(node_id, [])
        if edge_type is None:
            return list(out)
        return [e for e in out if e.edge_type == edge_type]

    def get_incoming(self, node_id: str, edge_type: Optional[EdgeType] = None) -> list[EpistemicEdge]:
        inc = self._in_edges.get(node_id, [])
        if edge_type is None:
            return list(inc)
        return [e for e in inc if e.edge_type == edge_type]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EpistemicGraph:
        g = cls()
        for nid, ndata in data.get("nodes", {}).items():
            g.add_node(EpistemicNode.from_dict(ndata))
        for edata in data.get("edges", []):
            g.add_edge(EpistemicEdge.from_dict(edata))
        return g
