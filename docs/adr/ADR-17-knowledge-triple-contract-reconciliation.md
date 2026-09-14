# ADR-17 — KnowledgeTriple Contract Reconciliation: Signed-Gradient Confidence + Enum-Now/URI-Later Predicates

```yaml
adr: 17
title: "KnowledgeTriple contract reconciliation (spec.md vs schema.json vs integrity zome)"
status: "Proposed"
date: "2026-07-04"
supersedes: []
relates_to:
  - "ADR-10 v2.0 (analog vote model — the signed-gradient precedent)"
  - "ADR-13 (Yumeichan ternary connotation — source of the affective predicates)"
  - "ADR-4 (SDD — spec/schema/code must be one contract)"
  - "F10 in docs/superpowers/plans/2026-07-fable5-adversarial-review.md (the finding this resolves)"
decision: "+1 adopt D1, D2, and D4 below on acceptance; 0 hold on D3 (provenance shape) pending spec v2.0 rewrite"
truth_status:
  divergence: "Verified — spec.md [0,1]/URIs vs schema.json+zome [-1,+1]/enum, live-read 2026-07-04 (zome lib.rs:225,233)"
  d1_confidence: "Specified — zome already enforces it; spec.md text change pending"
  d2_predicates: "Specified — mapping table below; extension batch not yet proposed through the gate"
  d3_provenance: "Specified — deferred to spec v2.0"
generator: "claude-fable-5"
friction_tier: "high"   # touches Phase 1's primary deliverable contract
rollback_plan: "Status stays Proposed until accepted through the consensus gate; revert = delete this file, the spec.md divergence banner remains as the honest state"
```

## Context

`docs/specs/knowledge-triple.spec.md` (v1.0/1.1), `docs/specs/knowledge-triple.schema.json`,
and the live integrity zome (`ARF/dnas/rose_forest/zomes/integrity/src/lib.rs`)
silently forked into two contracts (F10, Verified 2026-07-04):

| Aspect | spec.md | schema.json + zome (implemented, on-chain-validated) |
|---|---|---|
| `confidence` | `[0.0, 1.0]` | `[-1.0, +1.0]` signed gradient |
| `predicate` | ontology URIs (foaf/dcterms/urn:floss:ont:*) | 15-entry short-name enum (`VALID_PREDICATES`) |
| provenance | structured object | flat `source` AgentPubKey + chain-native authorship |

The convention (ADR-4, `FLOSS/CLAUDE.md`) is that `.spec.md` + `.schema.json` are
paired representations of **one** contract. The WS1 eval sets and WS3 Pioneer seed
follow the spec.md side; the WS3 fine-tune launch is on hold until this ADR lands.

## Decision

### D1 — Confidence domain: signed gradient `[-1.0, +1.0]`, extractors emit `[0.0, 1.0)`

The zome/schema side wins; it is the *decided* direction (analog vote model,
ADR-10 v2.0; ternary alignment, ADR-13) and it is already enforced on-chain.
Semantics: negative = asserted *away from* truth (counter-evidence), 0 = neutral,
positive = toward truth.

**Layered emission rule:** `LlmExtraction`-sourced triples emit only
`[0.0, 1.0)` — an extractor asserts toward-truth with bounded certainty and
never emits counter-evidence or absolute certainty. Negative values are
reserved for downstream layers (symbolic inference, committee review, curation)
that can *establish* contradiction.

Invariant restatements for spec v2.0:
- **INV-003′:** `confidence ∈ [-1.0, +1.0]` (closed).
- **INV-006′:** `source_type = LlmExtraction` ⇒ `confidence ∈ [0.0, 1.0)`.
- **INV-008′:** inferred triples: `|confidence| ≤ min(|parent confidence|)`;
  sign is determined by the inference rule, not inherited blindly.

**Data impact: none.** WS1 evals + WS3 seed already sit in `[0, 1) ⊂ [-1, +1]`.

### D2 — Predicate form: enum-now / URI-later (superset registry)

1. The zome's `VALID_PREDICATES` (15 entries) **is** registered-ontology **v0**
   and remains the on-chain wire form for now.
2. The ontology registry (Phase 1) defines a **URI superset**: every enum entry
   gets exactly one canonical URI; RDF / AD4M / PROV-O projections use URIs via
   the mapping table; the on-chain form stays the short name until a dedicated
   migration ADR.
3. **Extension mechanism:** adding a predicate = one `SpecChange` claim at
   Module radius through the consensus gate, updating zome const + schema enum
   + mapping table together (they can no longer drift silently — one claim, three files).

**Seed mapping table (enum → canonical URI):**

| enum (on-chain v0) | canonical URI |
|---|---|
| `is_a` | `http://www.w3.org/1999/02/22-rdf-syntax-ns#type` |
| `part_of` | `urn:floss:ont:partOf` |
| `related_to`, `relates_to` | `urn:floss:ont:relatesTo` ⚠️ duplicate pair — consolidate to one enum entry in the first extension batch |
| `has_property` | `urn:floss:ont:hasProperty` |
| `trained_on` | `urn:floss:ont:trainedOn` |
| `improves_upon` | `urn:floss:ont:improvesUpon` |
| `capable_of` | `urn:floss:ont:capableOf` |
| `evaluated_on` | `urn:floss:ont:evaluatedOn` |
| `supports` | `urn:floss:ont:supports` |
| `contradicts` | `urn:floss:ont:contradicts` |
| `heals`, `releases`, `neutralizes`, `recalibrates` | `urn:floss:ont:{heals,releases,neutralizes,recalibrates}` (Yumeichan affective set, ADR-13) |

**Honest gap statement:** the enum (AI/ML + affective domain) and the WS1/WS3
extraction vocabulary (social/organizational/software facts: `foaf:knows`,
`dcterms:creator`, `dependsOn`, `supersedes`, `implements`, `validates`, …)
overlap at essentially **one** predicate (`is_a` ↔ `rdf:type`). Neither replaces
the other. Therefore:

4. **First extension batch (gate-routed, follows acceptance of this ADR):** the
   15 WS1/WS3 extraction predicates are proposed as enum entries (snake_case
   short names + their existing URIs into the mapping table). The Pioneer
   extractor's output vocabulary = the enum **after** this batch lands; the WS3
   seed remaps URI→short-name by table (mechanical, scripted, no data loss).
   The WS3 fine-tune hold lifts when the batch is accepted.

### D3 — Provenance shape: deferred (Decision = 0)

On-chain, authorship + timestamp are chain-native; the flat `source` field plus
the provenance-packet layer (spec v1.4) may make the spec.md structured object
partially redundant. Constraint for the spec v2.0 rewrite: **`parent_triples`
must be on-chain-visible** if INV-007/008′ are to be zome-enforced. Resolving
the full shape belongs to that rewrite, not this ADR.

### D4 — Temporal and Contextual Decay Fields (Synthesis Delta)

Per the Holo-RBI synthesis delta feedback, facts require temporal and contextual bounds to prevent epistemic drift. The following fields are added to the schema:
- `valid_context` (string): Context in which the fact is considered valid.
- `known_failures` (array of strings): Conditions or edge cases where the fact fails.
- `expiry_or_retest_date` (string/ISO8601): When the fact should be retested or expires.

**Data impact:** These fields are optional for backwards compatibility, but strongly recommended for `LlmExtraction`-sourced triples.

## Consequences

- `knowledge-triple.spec.md` v2.0 rewrite scheduled (confidence domain,
  predicate section, D3, D4): replaces the divergence banner. Until then the banner
  states the interim authority split (zome for domain, spec for extraction semantics).
- `knowledge-triple.schema.json` `$id` bumps and gains the mapping-table pointer
  when the first extension batch lands (one claim, three files rule).
- WS1 evals keep URI predicates until the batch lands, then remap in the same
  script pass as the seed (goldens and seed must always share vocabulary).
- The interop story (spec v1.1 §6b — AD4M/RDF-star/PROV-O/SHACL) is unaffected:
  projections were already defined against URIs, which D2 preserves as the
  canonical export form.

## Rollback

Proposed-status document; not yet routed through the consensus gate. If
rejected: delete this ADR, keep the F10 banner, and the fine-tune hold stands
until an alternative reconciliation is accepted.
