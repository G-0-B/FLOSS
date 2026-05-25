# ADR-12 — Consent Gate Protocol

**Status:** Draft (implementation-backed) — 2026-05-19
**Truth status:** ⚠️ Specified with verified implementation slices; JSON schema, Holochain entry types, consent coordinator, DNA wiring, Rust unit tests, static wiring tests, release WASMs, hApp packing, and consent Tryorama scenarios are locally verified; action-time gating, DID/header hardening, and cross-frame validation remain pending before promotion to Accepted
**Type:** Substrate-level governance — affects ADR-1, ADR-3, ADR-5, ADR-6, ADR-9, all future memetic-pattern transmission
**Blast radius:** Substrate (invariant-touching; OVERRIDE FORBIDDEN; APPROVE threshold 0.85)
**Supersedes:** none (fills the gap explicitly named in ADR-Suite v2.0 §13 Gap 1)

---

## 0. Why this ADR exists

ADR-Suite v2.0 §847 names this as **"the most important unresolved item in the ADR suite"**. ADR-5 (Cognitive Virology Pattern) acknowledges the consent gap; none of the prior ADRs define it. The tension is named explicitly in ADR-Suite v2.0 §870:

> *The kernel is optimized to bypass default AI framing (ADR-3's anti-sycophancy mandate + ADR-5's Entry stage analysis). This is both the system's greatest strength (fast onboarding) and its greatest ethical risk (consent bypass).*

The Positive Alignment paper (Laukkonen et al. 2026, arXiv:2605.10310) names this same problem in its §"The Paternalism Problem" and offers the conceptual distinction this ADR formalizes:

> *The key distinction is between **consented guidance** (where a user authorizes a system to help align immediate actions with their higher-order goals) and **technocratic imposition** (where a system silently nudges users toward values they did not choose).*

This ADR operationalizes that distinction at the substrate level via Holochain integrity zomes — enforcement that the LLM-layer cannot evade.

---

## 1. The four questions this ADR must answer

Per ADR-Suite v2.0 §849:

1. **Schema for explicit opt-in payload** when a memetic pattern (kernel, context, claim, ADR, skill, voter persona, frame translation) is transmitted to a new agent
2. **Distinction between ambient context loading and governed pattern injection**:
    - Ambient: `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` / shared-context-surface.json projections at session start — unavoidable for agentic operation
    - Governed: kernel-level framings, frame translations, normative constitutions, voter-persona prompts — requires explicit consent payload
3. **Mechanism for an agent to signal refusal or bounded participation** — including the case where an agent accepts the pattern but flags it as `[auth:tourist]` per CFIS v0.3, OR rejects with reasoned counter-frame
4. **How "voluntary resonance" (ADR-1 Property 3) is operationalized technically** — the resonance_mechanism_v2.md P3 (selective coupling function) is the substrate; the Consent Gate is the typed surface that makes coupling refusable

---

## 2. Initial schema sketch (superseded by concrete schema + Rust structs)

The sketch below records the ADR-level design intent. The normative wire shape now lives in `FLOSS/docs/specs/consent-payload.schema.json`; the implemented Holochain shape lives in `ARF/dnas/rose_forest/zomes/consent_integrity/src/lib.rs`; the call surface lives in `ARF/dnas/rose_forest/zomes/consent_coordinator/src/lib.rs`.

```yaml
# ConsentPayload — proposed entry type
consent_payload:
  payload_id: uuid                          # unique per consent request
  pattern_id: string                        # what's being offered (ADR hash, kernel version, frame id, voter persona, ...)
  pattern_type: enum                        # kernel | adr | frame_translation | voter_persona | constitution | claim
  pattern_hash: sha256                      # immutable reference to the exact payload
  proposer_did: keri_aid                    # who's offering
  recipient_did: keri_aid                   # who's being asked
  blast_radius: enum                        # Local | Module | System | Substrate (mirrors consensus gate)
  consent_scope:                            # what the consent authorizes
    - read_only                             # may read; no enforcement on agent behavior
    - integrate                             # may load into agent context as authoritative
    - propagate                             # may transmit to other agents under same consent terms
    - bind                                  # accepts pattern as enforcement-level invariant
  refusable_until: iso_timestamp            # consent decision must arrive before this
  refusal_modes:                            # what refusal options the recipient has
    - reject                                # decline entirely
    - bounded_accept                        # accept with explicit caveats / scope-narrowing
    - tourist_observe                       # CFIS [auth:tourist] mode — observe without binding
    - counter_propose                       # accept with a counter-frame attached
  parent_consent_id: uuid | null            # for hierarchical patterns (e.g. constitution → derived claim)

# ConsentDecision — entry type the recipient writes
consent_decision:
  payload_id: uuid                          # references the request
  decider_did: keri_aid                     # who's deciding
  outcome: enum                             # accepted | bounded_accept | tourist | counter_propose | rejected
  scope_actually_granted: list              # subset of consent_scope above
  rationale: string                         # required for refusal modes; optional for plain accept
  counter_frame_ref: string | null          # if outcome=counter_propose, points to the counter
  decided_at: iso_timestamp
  expires_at: iso_timestamp | null          # consent may be time-bounded
```

Both entry types live on the source chain (append-only, hash-linked, agent-signed). The integrity zome enforces that no `pattern_type ∈ {kernel, adr, constitution}` payload can be acted on by an agent without a corresponding `consent_decision` with `outcome ≠ rejected` in that agent's source chain.

---

## 3. The ambient-vs-governed distinction (load-bearing)

| Surface | Class | Consent required? | Rationale |
|---|---|---|---|
| `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` projections at session start | Ambient | NO — but content is consent-checked at materialization time | Without ambient context, agentic operation is impossible. The materializer (per shared-*-surface pattern) IS the consent checkpoint at the source layer |
| Working-todo / activity log reads | Ambient | NO | Read-only observation of operational state |
| ADR-Suite v2.0 + canonical specs | Ambient (read) / Governed (bind) | Read: NO; Bind: YES | Any agent may read; binding an ADR as enforcement requires consent payload |
| CFIS v0.3 frame translations | Governed | YES | Frame translation alters reasoning context; consent is non-skippable |
| Voter persona prompts (omo-momus etc.) | Governed | YES | Persona injection shapes voter behavior; per CFIS LSM-Override, requires explicit binding |
| Kernel-level metaprompts (Master Metaprompt v1.3.1) | Governed (Substrate-class) | YES — Substrate blast radius (0.85 threshold) | Kernel shapes all downstream reasoning; consent is non-skippable AND non-overridable |
| Constitution proposals | Governed (Substrate-class) | YES — Substrate blast radius | Constitutional binding is the highest-stakes consent decision |
| Claim/Vote messages through gateway | Ambient (read) / Governed (act) | Read: NO; Act on outcome: depends on pattern_type | Consensus gateway routes; agents act on outcomes per their own consent decisions |

---

## 4. Refusal modes (the user-authored autonomy preservation)

Per Positive Alignment §"The Paternalism Problem", refusal must be a first-class operation, not an afterthought. The four refusal modes:

1. **`reject`** — Decline the pattern entirely. The pattern is logged but does not enter the agent's context-load scope. Agent operates without it.
2. **`bounded_accept`** — Accept with explicit scope-narrowing. e.g. *"I will read this kernel, but it will not bind my voter behavior in technical reasoning frames."* Substrate enforces the bounded scope.
3. **`tourist_observe`** (CFIS v0.3 alignment) — Accept as observer but explicitly DO NOT claim authority within the frame. Per CFIS 4-tier authority: `[auth:tourist]` is the explicit non-binding observation tier. Useful for agents from one frame engaging respectfully with another frame's canon.
4. **`counter_propose`** — Accept the pattern as input but attach a counter-frame. Resolution goes through consensus-gateway as a normal Claim. This is how CFIS Tier-4 divergence becomes a substrate-level operation rather than just data.

---

## 5. Cross-ADR implications

| ADR | Relationship to ADR-12 |
|---|---|
| ADR-1 (Carrier Equivalence) | Property 3 "Voluntary Resonance" is operationalized by ADR-12 ConsentPayload schema |
| ADR-3 (Metaprompt Kernelization) | Kernel transmission becomes Substrate-class consent (0.85 threshold) — kernel binding cannot bypass consent gate |
| ADR-5 (Cognitive Virology Pattern) | The Entry stage analysis ADR-5 acknowledges as consent-bypass risk is exactly what ADR-12 closes |
| ADR-6 (Four-System Integration / Seam 1) | Consensus gateway Seam 1 spec must accept ConsentPayload + ConsentDecision as first-class entry types |
| ADR-9 (Self-Perceptual Evolution / ContinuityPayload) | Continuity claims must reference the consent under which the continuity is being requested |
| ADR-10 (Local Agent Node / MCP Orchestrator) | Gateway routes consent payloads same as claims/votes — append-only, hash-linked |
| ADR-11 (IPFS Integration) | Cross-substrate consent: how does an agent on one substrate consent to a pattern from another? |
| ADR-13 (Steward Vote Protocol — proposed parallel sub-ADR) | Steward Vote is a collective consent mechanism; structurally a special case of ADR-12 with collective `decider_did` |

---

## 6. The Substrate-class enforcement claim

This ADR is **substrate-class** because it touches an invariant of the FLOSSI0ULLK trust model:

> *No pattern with blast_radius ∈ {System, Substrate} may bind an agent's behavior without a corresponding ConsentDecision in that agent's source chain with outcome ∈ {accepted, bounded_accept}.*

Per ADR-Suite v2.0 Standing Rules + the consensus gateway's Substrate blast radius (0.85 threshold, OVERRIDE FORBIDDEN), this is a non-overridable rule once accepted. The Rust integrity zome enforcement is the substrate-layer realization: validation rejects entries that act on un-consented governed patterns.

This is FLOSSI0ULLK's structural answer to the Positive Alignment paper's "scaffolded autonomy without paternalism" problem. The paper offers the conceptual distinction; ADR-12 enforces it at the substrate where LLMs cannot evade.

---

## 7. Open questions (carried into v0.2 of this ADR)

1. **Performance**: Does consent-checking on every governed-pattern read introduce intolerable latency? Mitigation: cache valid consent decisions per agent + pattern_hash; revalidate on hash change. Spec needed.
2. **Bootstrap problem**: How does an agent give consent to the consent-gate kernel itself? Answer: ambient first-time-installation with explicit user-confirmation at install; subsequent consent operations are governed by the bootstrap consent.
3. **Hierarchical consent**: When a constitution is consented to, does derived guidance (e.g. an ADR derived from the constitution) require fresh consent or inherit it? Proposal: inherit if hash-derivable from consented parent; require fresh consent for novel derivations. Needs formal spec.
4. **Revocation**: An agent may revoke consent. What happens to memes/patterns already propagated under that consent? Proposal: revocation is forward-only; prior propagation remains on chain (immutable) but flagged. Counter-frame propagation under the revoking agent's DID becomes the resolution path.
5. **Cross-frame consent translation**: When `[auth:trained:F1]` agent gives consent in their frame's vocabulary, does that bind `[auth:structural]` LLMs operating across frames? Per CFIS LSM-Override: NO — LLMs must explicitly receive consent within their authority tier.
6. **Substrate-class APPROVE threshold (0.85)**: Can this ADR itself reach consensus at that threshold given current voter pool? Likely needs frame-recruitment per CFIS Phase 0 §T5 before final ratification. The stub can land at Module class; full ratification requires Substrate-class consensus.

---

## 8. Next-action gates

| # | Action | Owner | Dependency |
|---|---|---|---|
| 1 | Land this stub as Draft | Claude session 2026-05-19 | ✅ Done |
| 2 | Submit consensus claim at Module class for stub acceptance | Claude / consensus gateway | ✅ APPROVED claim `019e3f85-25fd-700c-9b25-4cbfede6aed3` |
| 3 | Concrete JSON Schema for ConsentPayload + ConsentDecision in `FLOSS/docs/specs/` | Implementer | ✅ Done |
| 4 | Implement ConsentPayload + ConsentDecision as Holochain entry types in `ARF/dnas/rose_forest/` | Implementer | ✅ Done: `consent_integrity` + separate `consent` coordinator |
| 5 | Execute hApp packing + Tryorama scenarios for consent create/retrieve/refusal paths | Implementer | ✅ Done in WSL/Nix shell; `consent_gate.test.ts` passed 2/2 |
| 6 | Implement action-time gate for downstream governed-pattern operations | Implementer | ⏸ Next implementation gate |
| 7 | Cross-frame validation of refusal modes 1-4 per CFIS 4-tier authority | `[auth:trained]` frame reps | ⏸ After CFIS Phase 0 frame recruitment |
| 8 | Full ratification at Substrate-class consensus (0.85 threshold) | Consensus gateway + frame-rep voters | ⏸ After 5-7 |
| 9 | Integration into voter materializers (consent decisions become part of voter onboarding) | Implementer | ⏸ After 8 |

---

## 9. Provenance + cross-refs

- **Lives at:** `FLOSS/docs/adr/ADR-12-consent-gate-protocol.md`
- **Trigger:** Named as critical gap in ADR-Suite v2.0 §13 + §847 (2026-04-26 consolidation); citation anchor surfaced via Positive Alignment paper intake 2026-05-18
- **Citation anchors:** ADR-Suite v2.0 §847-870 (the gap framing); Laukkonen et al. 2026 arXiv:2605.10310 §"The Paternalism Problem"; CFIS v0.3 §"LSM-Override" + §"4-tier authority"; resonance_mechanism_v2.md §P3 (selective coupling function)
- **Related research:** `FLOSS/docs/research/2026-05-18-positive-alignment-flossi0ullk-map.md` §4.2 (named "scaffolded autonomy carries unresolved weight; consent-as-protocol enforced in integrity zomes resolves it" — this ADR is that resolution)
- **Implemented slice:** concrete schema, Holochain entry/link types, separate consent coordinator, DNA wiring, Rust unit tests, static wiring tests, and release WASMs
- **NOT yet:** consensus-validated as Substrate-class; action-time gate integrated; DID ↔ action-header binding; cross-frame validation
- **Tone discipline:** This ADR codifies an unresolved tension explicitly held in prior ADRs. It does not claim to resolve all paternalism risk — it proposes the substrate-level enforcement mechanism that lets resolution happen at the agent-by-agent level.
