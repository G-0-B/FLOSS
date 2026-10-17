"""
FLOSSI0ULLK Semantic Claim Representation Module.
Defines ClaimVersion, NormalizedTriple, and AttributionNode with first-class linguistic qualifiers.
Part of Phase 2 (Task 2.1) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal, Any

ClaimType = Literal[
    "causal",
    "association",
    "observation",
    "definition",
    "recommendation",
    "hypothesis"
]

Polarity = Literal[
    "affirmed",
    "negated",
    "denied_evidence",
    "mixed",
    "unresolved"
]

ModalityType = Literal[
    "none",
    "epistemic",
    "deontic",
    "dynamic"
]

ModalityStrength = Literal[
    "asserted",
    "probable",
    "possible",
    "hypothetical"
]

AttributionKind = Literal[
    "study_report",
    "author_narrator",
    "cited_authority",
    "speculation"
]

OntologyStatus = Literal[
    "ALLOWLISTED",
    "CANDIDATE",
    "DISALLOWED"
]


@dataclass(frozen=True)
class NormalizedTriple:
    """Canonicalized ontology representation of the proposition."""
    subject: str  # e.g. "urn:entity:compound_x"
    predicate: str  # e.g. "increases"
    object: str  # e.g. "urn:entity:cellular_apoptosis_cortical_neurons"
    ontology_status: OntologyStatus = "ALLOWLISTED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "ontology_status": self.ontology_status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NormalizedTriple:
        return cls(
            subject=str(data["subject"]),
            predicate=str(data["predicate"]),
            object=str(data["object"]),
            ontology_status=data.get("ontology_status", "ALLOWLISTED"),
        )


@dataclass(frozen=True)
class AttributionNode:
    """Explicit speaker, narrator, or citation anchor in the attribution hierarchy."""
    speaker: str
    kind: AttributionKind = "study_report"
    nested_level: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "speaker": self.speaker,
            "kind": self.kind,
            "nested_level": self.nested_level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AttributionNode:
        return cls(
            speaker=str(data["speaker"]),
            kind=data.get("kind", "study_report"),
            nested_level=int(data.get("nested_level", 0)),
        )


@dataclass
class ClaimVersion:
    """
    Versioned semantic proposition with first-class linguistic qualifiers,
    modality strengths, polarity, and nested attribution chains.
    """
    claim_id: str
    claim_version: int
    claim_type: ClaimType
    statement: str
    subject_surface: str
    relation_surface: str
    object_surface: str
    normalized_triple: NormalizedTriple
    polarity: Polarity = "affirmed"
    modality_type: ModalityType = "none"
    modality_strength: ModalityStrength = "asserted"
    attribution_chain: list[AttributionNode] = field(default_factory=list)
    quantifiers: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    temporal_scope: Optional[str] = None
    population_scope: Optional[str] = None
    causal_direction: Optional[str] = None
    evidence_refs: list[str] = field(default_factory=list)
    normalization_map_id: Optional[str] = None
    abstention_reason: Optional[str] = None

    def validate_claim(self) -> tuple[bool, list[str]]:
        """Validate structural completeness and semantic consistency."""
        violations = []
        if not self.statement.strip():
            violations.append("Statement string cannot be empty")
        if not self.subject_surface.strip() or not self.object_surface.strip():
            violations.append("Subject surface and object surface must be non-empty")
        if not self.relation_surface.strip():
            violations.append("Relation surface must be non-empty")
        if not self.normalized_triple.predicate.strip():
            violations.append("Normalized triple predicate cannot be empty")
        return len(violations) == 0, violations

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_version": self.claim_version,
            "claim_type": self.claim_type,
            "statement": self.statement,
            "subject_surface": self.subject_surface,
            "relation_surface": self.relation_surface,
            "object_surface": self.object_surface,
            "normalized_triple": self.normalized_triple.to_dict(),
            "polarity": self.polarity,
            "modality_type": self.modality_type,
            "modality_strength": self.modality_strength,
            "attribution_chain": [a.to_dict() for a in self.attribution_chain],
            "quantifiers": self.quantifiers,
            "conditions": self.conditions,
            "temporal_scope": self.temporal_scope,
            "population_scope": self.population_scope,
            "causal_direction": self.causal_direction,
            "evidence_refs": self.evidence_refs,
            "normalization_map_id": self.normalization_map_id,
            "abstention_reason": self.abstention_reason,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClaimVersion:
        triple = NormalizedTriple.from_dict(data["normalized_triple"])
        attributions = [AttributionNode.from_dict(a) for a in data.get("attribution_chain", [])]
        return cls(
            claim_id=str(data["claim_id"]),
            claim_version=int(data.get("claim_version", 1)),
            claim_type=data.get("claim_type", "observation"),
            statement=str(data["statement"]),
            subject_surface=str(data["subject_surface"]),
            relation_surface=str(data["relation_surface"]),
            object_surface=str(data["object_surface"]),
            normalized_triple=triple,
            polarity=data.get("polarity", "affirmed"),
            modality_type=data.get("modality_type", "none"),
            modality_strength=data.get("modality_strength", "asserted"),
            attribution_chain=attributions,
            quantifiers=list(data.get("quantifiers", [])),
            conditions=list(data.get("conditions", [])),
            temporal_scope=data.get("temporal_scope"),
            population_scope=data.get("population_scope"),
            causal_direction=data.get("causal_direction"),
            evidence_refs=list(data.get("evidence_refs", [])),
            normalization_map_id=data.get("normalization_map_id"),
            abstention_reason=data.get("abstention_reason"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> ClaimVersion:
        return cls.from_dict(json.loads(json_str))
