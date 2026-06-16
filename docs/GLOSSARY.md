# FLOSSI0ULLK Glossary (Canonical, Deduplicated)

**Status:** Active · **Truth Status:** mixed per row (see column) · **Date:** 2026-06-13
**Origin:** promoted from the Lovable Grand Synthesis §7.2 (2026-06-13), extended with the
§4.3 "jargon that hides empty space" flags. Ratify or amend per term.

## Why this exists

One term per row; **all synonyms collapse here.** The corpus restates the same handful of ideas
in five vocabularies — this table is the alias map that makes it tractable. It is *net anti-sprawl*:
it retires confusion rather than adding a layer.

## Usage rule (proposed — ROI item 3)

1. Every new doc that uses a term below **cites this glossary** rather than re-defining it.
2. New synonyms get added as an **alias on the existing row**, never a new row.
3. Terms marked **U (Unverified)** are *mythos / Voice-and-Vision only* — they must **not** appear
   in a spec, ADR, or schema as if they denote a specified mechanism. Keep the poetry; quarantine
   it from the engineering.
4. Truth-status tags (V/S/A/U) are load-bearing: **V** verified/sourced, **S** specified
   (composition of V primitives), **A** aspirational, **U** asserted-but-undefined.

## Core vocabulary

| Term | Canonical meaning | Aliases across corpus | Status |
|---|---|---|---|
| Infinite game | Play whose purpose is continuation, not winning | frontier living; expanding circle; horizon | V (Carse 1986) |
| Finite game | Play whose purpose is winning within fixed rules | society; training (Carse) | V (Carse 1986) |
| Shell / Holon | Nested whole-and-part with a permeable membrane | membrane (Holochain); light-cone (TAME); circle (Flourishing) | V (Koestler 1967) |
| Permeability | Consent-governed pass-through across a boundary | toroidal flow; circulation; carrier-equivalence | S |
| Capability token | Cryptographic gate on a shell boundary | membrane proof (Holochain); circular consent (Flourishing) | V (Holochain / OCapN) |
| Reframe→Prime→Do→Sustain | Four-stage uncertainty operating loop | RPDS; UTN loop | V (Furr & Furr 2022) |
| Don't Force Machinery | Wait condition when balancers are unhealthy | sacred friction; playfulness | V (Furr & Furr 2022) |
| Balancer | Identity / relationship / resource anchor locked before exposure | backpack (UTN metaphor) | V (Furr & Furr 2022) |
| Transilience | Abrupt expansion of an agent's light-cone / capability | surprise (Carse, "education") | V (Furr & Furr 2022) |
| Strength (vs. Power) | Capacity to carry the past forward without closing the game | continuation; education | V (Carse 1986) |
| Agent-centric | Identity/data/authority rooted in the agent, not a global ledger | source chain + DHT neighborhood | V (Holochain) |
| Provenance | Verifiable author-of-record bound to an entry | attestation; signed claim | V (primitive) / S (enforcement — see ADR-15) |
| Doula (Peony) | Agent that holds a human's *stated values* in trust without controlling | peony; friend (Seed) | A (Seed; design note 2026-06-13) |
| Anti-sycophancy | Reflection of the user's values, not their mood | sacred friction | A → grounding V (Harber 1998 positive-feedback bias) |
| Anti-dependence | Support that increases the user's own capacity over time | "many ways of knowing" | A (Seed) |
| Truth-status (V/S/A/U) | Tag marking the evidential standing of a claim | claim truth model (kernel §4) | V (in active use) |

## Flagged: terms that currently denote nothing specified (handle with care)

These are **fine in mythos prose; harmful in specs.** Mark `U` until given an operational definition.

| Term | Issue | Disposition |
|---|---|---|
| **FLOSSIOULLK** | Never defined as acronym/framework/movement in the corpus | Decide: define it, or declare it a brand-mark (ROI item 22) |
| **Carrier-equivalence** | Used in the substantiate doc; no operational definition | Define or retire |
| **Anti-hoarding** | Slogan, not a mechanism | Define or move to Voice & Vision |
| **Agent-centric relativity** | Gestures at Holochain; not a specified property | Define or retire |
| **"singYOUlAIRAwrity" / Singularity** | Explicitly poetic | Voice & Vision only; never promote to spec |
| **Autopoietic love** | Affect-laden; not a primitive | Voice & Vision only |
| **"Infinite overflowing unconditional love"** | Audit flags as operationally dangerous if taken literally | Keep as mythos; specs use "federated intelligence commons, asymptotic" (ROI item 13 — **your call**) |

> Note: whether the `U` mythos terms stay as the project's recruiting/meaning surface is a
> **sovereign editorial decision (Anthony's)**, not an automatic deletion. This table enforces
> *where* they may appear, not *whether* they may exist.
