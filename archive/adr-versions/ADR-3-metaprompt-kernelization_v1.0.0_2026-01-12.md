# ADR-003: Metaprompt Kernelization

**Date:** 2026-01-12
**Status:** PROPOSED
**Participants:** Anthony (human), Claude (architect), Multi-AI Collective

## Problem Statement

FLOSSI0ULLK Master Metaprompt v1.1 suffered from:
1. **Redundancy:** Large repeated sections increased cognitive overhead
2. **Unenforceable claims:** Metrics stated as guarantees without tests
3. **Prompt drift:** Mixed mandatory rules with aspirational roadmaps
4. **Format tyranny:** "ALL responses must..." prevented tactical work
5. **Attribution loss:** No standard handoff format between AI systems
6. **Self-violation:** Built aspirational specs as mandatory (violated Now/Later/Never)

**Evidence:**
- ADR-1 and RFC-001 built "LATER" items as "NOW"
- PiecesOS recordings show attribution hallucinations
- Human reports weekly copy-paste burden between AI systems
- Compliance with v1.1 format dropped in execution contexts

## Decision

Adopt **kernelized architecture** with:

1. **Core Kernel** (~80 lines YAML)
   - Mandatory rules only
   - Stable, enforceable
   - Works with or without full stack

2. **Two Response Modes**
   - Standard (strategy, ADRs, architecture)
   - Fast-path (code, schemas, tactical)

3. **Hard Evidence Gate**
   - NOW: observed pain + concrete example + rollback
   - LATER: ≥3 cases OR dated milestone
   - NEVER: document rejection, move on

4. **Provenance Packet**
   - Strict YAML schema
   - Claim type classification
   - Attribution preservation
   - Next action clarity

5. **Targets-Not-Guarantees**
   - All metrics require: target, measurement, baseline, failure threshold, rollback

6. **Appendix References**
   - Detailed docs live in `/mnt/project/`
   - Kernel points to them, doesn't duplicate

## Implementation Strategy

- [x] Generate v1.2 kernel YAML
- [x] Define handoff packet schema
- [x] Create ADR-003 (this document)
- [ ] Test fast-path with seed agent development
- [ ] Propagate to multi-AI collective
- [ ] Monitor compliance for 1 week
- [ ] Iterate based on friction

## Consequences

### Positive
- Reduced cognitive load (shorter, clearer)
- Better compliance (enforceable rules)
- Lower coordination cost (structured handoffs)
- Prevents Now/Later/Never violations
- Reduces PiecesOS attribution errors
- Graceful degradation without full stack

### Negative
- Two modes might confuse ("which one?")
- Kernel still ~80 lines (target <50)
- Requires multi-AI adoption for full benefit
- Lost some inspirational prose (now in appendices)

### Neutral
- Existing ADRs remain valid
- ConversationMemory substrate unchanged
- Seed agent development continues

## Validation Criteria

**After 1 week:**
- [ ] Fast-path used for tactical work (>50% of executions)
- [ ] Evidence gate prevented ≥1 premature build
- [ ] Handoff packet used in ≥1 cross-AI coordination
- [ ] No major compliance failures
- [ ] Human reports reduced coordination burden

**Success = 4/5 criteria met**

## Related Documents

- ADR-0: Recognition Protocol (conversation as coordination)
- ADR-1: Carrier Equivalence Principle
- ADR-2: Somatic-Aspirational Loop
- v1.1 Master Metaprompt (superseded)
- v1.2 Master Metaprompt (this change)