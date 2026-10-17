# FLOSSI0ULLK Layer 3 Annotation Guidelines & Evaluation Unit Contract

> **Version:** 2.0.0  
> **Status:** Locked Standard  
> **Applicability:** Layer 3 (Locked Realistic Acceptance Set - 100 Documents)

---

## 1. Evaluation Unit Definition

In prior evaluation regimes, "100 documents" was ambiguous because documents vary in length from 200-word abstracts to 30-page papers, yielding anywhere from 1 to 500 factual propositions per document.

In **Layer 3**, the evaluation hierarchy is strictly structured:
```text
Document (100 total)
  ├── Metadata & Rights Receipt (pre-parse license & security classification)
  ├── DocumentIR (NFC canonical text + layout blocks + TransformMap)
  └── Passages (Selected test units: paragraphs, tables, figure captions, or null sections)
        ├── Null Passage (0 claims expected; tests H11 Abstention)
        └── Informative Passage
              ├── Eligible Atomic Claims (1..N claims)
              │     ├── Statement (natural language proposition)
              │     ├── Surface Terms (subject_surface, relation_surface, object_surface)
              │     ├── Normalized Triple (subject URI, predicate URI, object URI)
              │     ├── Polarity (affirmed | negated | denied_evidence)
              │     ├── Modality Strength (asserted | probable | possible | hypothetical)
              │     ├── Attribution Chain (study_report | author_narrator | cited_authority)
              │     └── EvidenceSet (>=1 typed EvidenceAtoms grounded in DocumentIR)
              └── Non-Factual / Boilerplate Spans (excluded)
```

---

## 2. Claim Eligibility Rules

A candidate proposition in a document is an **Eligible Claim** if and only if:
1. **Factuality / Falsifiability:** It expresses a testable empirical finding, causal relation, formal definition, or association.
2. **Atomicity:** It cannot be decomposed into independent conjuncts without loss of meaning.
   - *Example:* "Compound X inhibits enzyme Y and reduces cellular apoptosis" must be decomposed into two distinct claims:
     - Claim 1: Compound X inhibits enzyme Y.
     - Claim 2: Compound X reduces cellular apoptosis.
3. **Evidence Grounding:** Every claim must be supported by at least one explicit evidence atom within the passage. If the text merely mentions an entity without asserting a predicate relationship, no claim is eligible.

---

## 3. Evidence Grounding Hierarchy

Evidence atoms must be recorded with their strongest verifiable grounding:
- `CANONICAL_CHAR_EXACT`: Zero-based, half-open code-point range `[start, end)` in `DocumentIR.canonical_text` matching literal content.
- `SOURCE_TEXT_EXACT`: Code-point interval in native extracted text stream.
- `RAW_BYTE_EXACT`: Exact byte interval in source file.
- `TRANSFORM_MAPPED`: Replayable via `TransformMap` across hyphenation merges or normalization shifts.
- `STRUCTURE_GROUNDED`: Grounded to table cell ID, figure region, or equation object.

---

## 4. Semantic Hazard Annotation (H1–H17)

Every eligible claim and passage must record tested hazard targets:
- **Polarity (H4):** Whether the claim is affirmed or negated. Refuted and negated claims are essential controls.
- **Modality (H5):** If the text hedges with "may", "suggests", or "hypothesized", the claim's modality must be marked `possible` or `hypothetical`. It must NOT be promoted to `asserted`.
- **Attribution (H6):** Speculation reported from prior literature must be tagged `cited_authority` or `speculation`, never `study_report` (author truth).
- **Abstention (H11):** At least 15% of passages in the corpus must be **Null Passages** (boilerplates, disclaimers, acknowledgments) where the gold claim list is strictly `[]`.

---

## 5. Dual Annotation & Adjudication Protocol

To guarantee evaluator independence:
1. Every document and passage is reviewed independently by **Annotator A** and **Annotator B**.
2. Inter-annotator agreement is calculated across:
   - Span boundary F1 (exact vs token overlap)
   - Predicate classification agreement
   - Polarity and modality concordance
3. Disagreements are flagged and resolved by a designated **Steward Adjudicator**, recording:
   - `adjudication_id`: Unique identifier
   - `disagreement_type`: Boundary shift, predicate divergence, or inclusion/exclusion
   - `final_ruling`: Rationale for accepted gold representation
