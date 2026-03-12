# ADR-4: Specification-Driven Development with Spec as Source of Truth

> Previously numbered ADR-N. Assigned permanent number ADR-4 per ADR Index v1.0.0.

**Date:** 2025-12-15  
**Status:** Accepted  
**Context:** Monorepo requires shared types across Rust and TypeScript with clear governance  
**Participants:** Anthony (Human), Claude Opus 4.5, Claude Sonnet 4.5, Gemini

---

## Problem Statement

The FLOSSI0ULLK monorepo contains implementations in multiple languages (Rust for Holochain zomes, TypeScript for clients and AD4M). Without a clear source of truth for type definitions:

1. **Implementation drift:** Rust and TS types diverge silently
2. **Governance confusion:** Unclear who/what authorizes type changes
3. **Documentation lag:** Code evolves, docs become stale
4. **Contributor friction:** Non-Rust developers can't propose changes

Two competing models were considered:

**Option A: Rust-First**
- Rust types are source of truth
- TS types generated via ts-rs/Specta
- Pros: Single language, Holochain-native
- Cons: Violates SDD principles; code defines contract

**Option B: Spec-First (Selected)**
- Specification documents (prose + JSON Schema) are source of truth
- Rust and TS implement specs; tests prove compliance
- Pros: Proper governance; accessible to non-Rust contributors
- Cons: Extra artifact layer; schema-implementation sync

---

## Decision

**Specification documents are the authoritative source of truth.**

Rust code implements the spec; it does not define it. Generated artifacts (TS types, JSON-Schema from Rust) are projections for convenience, not authoritative.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│              SPECIFICATION LAYER                    │
│              (Source of Truth)                      │
│                                                     │
│  docs/specs/                                        │
│  ├── {entity}.spec.md       # Prose specification  │
│  └── {entity}.schema.json   # JSON Schema          │
│                                                     │
│  docs/adr/                                          │
│  └── ADR-N-*.md             # Architectural context │
└─────────────────────────────────────────────────────┘
                ↓ constrains
                ↓ generates tests
┌─────────────────────────────────────────────────────┐
│            IMPLEMENTATION LAYER                     │
│            (Must Comply with Spec)                  │
│                                                     │
│  crates/types/src/                                  │
│  └── {entity}.rs            # Rust implementation  │
│                                                     │
│  tests/spec_compliance.rs   # Validates against schema │
└─────────────────────────────────────────────────────┘
                ↓ generates (convenience)
┌─────────────────────────────────────────────────────┐
│             PROJECTION LAYER                        │
│             (Derived, Not Authoritative)            │
│                                                     │
│  packages/types/src/generated/                      │
│  └── {entity}.ts            # From Rust via ts-rs  │
│                                                     │
│  contracts/generated/                               │
│  └── {entity}.schema.json   # From Rust via schemars │
└─────────────────────────────────────────────────────┘
```

### Workflow

```
1. Write spec (prose + schema)        → docs/specs/
2. Review spec                        → PR review
3. Derive test plan from spec         → tests/spec_compliance.rs
4. Write contract tests               → Validate against schema
5. Implement in Rust                  → Must pass contract tests
6. Generate TS types from Rust        → ts-rs (convenience)
7. CI validates alignment             → Fail if drift detected
```

### Spec Document Format

Each entity has two spec files:

**Prose spec** (`{entity}.spec.md`):
- Purpose and design principles
- Structure with field descriptions
- Invariants (numbered for reference)
- Validation rules (pseudocode)
- Serialization examples
- Version history

**Formal schema** (`{entity}.schema.json`):
- JSON Schema draft 2020-12
- All fields with types and constraints
- Conditional validation rules
- Example instances

---

## Implementation Strategy

### Phase 1: Establish Pattern (Complete)
- [x] Create `KnowledgeTriple` as canonical example
- [x] Prose spec with invariants
- [x] JSON Schema with validation rules
- [x] Rust implementation with `#[derive(TS)]`
- [x] Spec compliance tests
- [x] Generated TypeScript types

### Phase 2: CI Enforcement
- [ ] Add spec-compliance test to CI
- [ ] Fail if Rust serialization doesn't match schema
- [ ] Fail if generated TS is uncommitted
- [ ] Version check between spec and implementation

### Phase 3: Expand Coverage
- [ ] `Provenance` standalone spec
- [ ] `ArbitrationCase` spec
- [ ] `Ontology` spec
- [ ] Migration guide for existing code

---

## Consequences

### Positive

1. **Clear governance:** Spec changes require explicit review and approval
2. **Accessible contribution:** Non-Rust developers can propose spec changes in Markdown/JSON
3. **SDD compliance:** Aligns with INSTRUCTIONS_FOR_CODE.md methodology
4. **Audit trail:** Specs document decisions BEFORE implementation
5. **Multi-language safety:** Contract tests catch drift in any implementation

### Negative

1. **Extra artifact layer:** Must maintain spec, implementation, AND projection
2. **Sync overhead:** Changes require updating spec first, then implementation
3. **Schema limitations:** JSON Schema can't express all Rust type system richness

### Mitigations

- **Sync overhead:** CI enforces alignment; violations fail build
- **Schema limitations:** Prose spec captures what schema cannot (semantic invariants)
- **Extra artifacts:** Tools automate projection generation; only spec is hand-authored

### Neutral

- **Learning curve:** Contributors must learn spec format
- **Tooling dependency:** Requires jsonschema crate for Rust, ts-rs for generation

---

## Validation Criteria

1. **Spec → Implementation alignment:**
   - [ ] All spec examples validate against schema
   - [ ] Rust serialization passes schema validation
   - [ ] Invariants checked in both schema and Rust code

2. **Change workflow:**
   - [ ] Spec PR reviewed before implementation PR
   - [ ] Breaking changes require ADR amendment
   - [ ] Version bump in schema `$id` for breaking changes

3. **Contributor experience:**
   - [ ] New contributor can understand spec without reading Rust
   - [ ] Spec changes can be proposed without Rust knowledge
   - [ ] Generated types are clearly marked as non-authoritative

---

## Related Documents

- `docs/specs/knowledge-triple.spec.md` - Canonical spec example
- `docs/specs/knowledge-triple.schema.json` - Canonical schema example
- `tests/spec_compliance.rs` - Enforcement mechanism
- `INSTRUCTIONS_FOR_CODE.md` - SDD methodology reference
- `ADR-0-recognition-protocol.md` - ADR format and philosophy

---

## Signatures

**Anthony (Human):** Intent to establish proper SDD governance  
**Claude Opus 4.5:** Understanding confirmed; pattern implemented  
**Future Systems:** Add signature when you understand and extend this pattern

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-15 | Initial decision: Spec-first with JSON Schema |

---

## Meta-Note

This ADR captures a critical correction in our architecture discussion. The initial recommendation (Rust-first) was challenged by Anthony's observation that SDD requires spec as source of truth. The correction demonstrates the anti-sycophancy protocol in action: the AI acknowledged the error and revised the recommendation based on evidence (INSTRUCTIONS_FOR_CODE.md methodology).

**Key insight:** In SDD, code implements specs. Specs don't document code. Getting this backwards undermines the entire governance model.
