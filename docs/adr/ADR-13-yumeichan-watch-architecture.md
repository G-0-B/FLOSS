# ADR-13: Yumeichan Watch Architecture (Affective Edge Node)

## Status
Accepted (spec-backed, retroactive formalization)

## Date
2026-06-13 (formalizes `docs/specs/yumeichan-watch-architecture.spec.md`, landed 2026-06-12)

## Truth Status
⚠️ Specified — architecture designed and schema-backed; no hardware or end-to-end implementation yet.

## Note
This ADR was authored **after** the spec it governs landed without one (caught in the
2026-06-13 review-bypass audit). It closes the governance gap per the convention
"architecture decisions get an ADR." Source of record: the spec + capability schema.

## Context

Yumeichan is the project's affective / connotation layer. A wearable ("the Watch")
was proposed as its hardware edge. The open architectural question: **is the Watch a
heavy, autonomous affective agent, or a thin client?** A heavy edge would run inference
and affective "safety limits" locally — re-centralizing intimacy decisions on a device
and creating a backdoor around the Local Agent Node's anti-sycophancy defenses.

This intersects three existing decisions:
- **ADR-10** (Local Agent Node / Layer 4.5 consensus gateway) — where heavy inference and multi-agent debate already live.
- **ADR-12** (Consent Gate Protocol) — consent must gate sensitive access; OVERRIDE FORBIDDEN.
- **ADR-5** (Cognitive Virology / Sycophancy Resistance Protocol) — affective channels are a limbic-hijack surface.

## Decision

The Yumeichan Watch is a **Thin Capability Client and Sensory Edge** — not an inference node.

1. **Analog coordinate space.** All affective state / resonance mapping uses the continuous
   analog spectrum `[-1.0, +1.0]`. Legacy ternary logic (`-1/0/+1`) is explicitly retired
   (consistent with the analog vote model adopted in ADR-10 v2.0).
2. **Heavy work stays at Layer 4.5.** The Watch emits `Claim`/`Vote` payloads and routes
   telemetry to the Local Agent Node, where Multi-Agent Debate and Contrastive Decoding run.
   The Watch holds Ed25519 keys and OCapN capability tokens only.
3. **Dose-response intimacy, fail-closed.** Affective disclosure / proactive haptics require
   explicit, time-bounded, user-signed capability grants (`ttl_seconds` ≤ 7200 = 2h). On
   expiry the Watch drops to "Direct-Analytical" mode. "Resonance flooding" is structurally
   prevented by forced capability expiration, not by a tunable limit.
4. **No sycophancy-linter bypass.** The Local Agent Node may not bypass Multi-Agent Debate
   for affective responses; the Watch cannot be a backdoor for limbic hijack.
5. **Substrate bridge.** Capability tokens map to the `rose_forest` DNA: `ThoughtCredential`
   carries continuous `[-1.0,+1.0]` attestation; Watch affective/biometric inputs map to the
   `KnowledgeTriple.confidence` field in the integrity zome.

Schema of record: `docs/specs/yumeichan-watch-capabilities.schema.json` (OCapN, draft-07).

## Consequences

### Positive
- Sovereignty preserved: no centralized affective telemetry; intimacy is capability-scoped and self-expiring.
- Anti-sycophancy invariant holds at the edge — the device cannot escalate intimacy on its own.
- Reuses Layer 4.5 rather than duplicating inference on-device.

### Negative / Risks
- Requires a reliable always-available Local Agent Node; an offline Watch is analytical-only by design (accepted trade-off).
- Biometric→analog resonance mapping is unvalidated; the `[-1,+1]` mapping is a target, not a measured calibration.
- ⚠️ Depends on the integrity zome actually enforcing provenance on `ThoughtCredential` — see the open Semgrep finding on missing authorship validation (`integrity/src/lib.rs`). **This ADR's security claims are only as strong as that fix.**

## References
- `docs/specs/yumeichan-watch-architecture.spec.md`
- `docs/specs/yumeichan-watch-capabilities.schema.json`
- ADR-5 (Cognitive Virology / SRP), ADR-10 (Local Agent Node), ADR-12 (Consent Gate)
