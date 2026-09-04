# Draft Schemas — v0.4 Continuation Bundle

These schemas are **Specified drafts**, not canonical contracts.

Before implementation:

1. search the target branch for equivalent schemas;
2. reconcile with `docs/specs/provenance-packet.spec.md`, consent/source-chain contracts, shared-context/room contracts, and `spec-registry.json`;
3. reuse current evidence-reference types rather than widening allowlists casually;
4. choose current project identity/signature conventions for CapabilityDescriptor;
5. register any accepted canonical schema through the existing spec gate.

Core runtime chain:

```text
LedgerEntry -> Claim -> AdmissionDecision -> SharedGist
```

Supporting objects:

- `CapabilityDescriptor` — soft-state discovery only.
- `TaskContract` — task scope/risk/verification constraints.
- `PrivateMemoryPiece` — LATER per-agent memory experiment.
- `EvidenceRef` — draft adapter reference; not a replacement for Provenance Packet v1.4 semantics.

## Reconciled against repo canon, 2026-09-04

Four schemas were changed after a reuse check against current repo contracts. Full evidence: `docs/reviews/2026-09-04-v04-continuation-bundle/REUSE-MAP.md`.

| Change | Why |
|---|---|
| `claim.schema.json` renamed to `runtime-claim.schema.json`, title `RuntimeClaim` | `packages/orchestrator/claim_schema.Claim` already exists and is a *governance proposal to the consensus gate* -- a different concept with a different lifecycle. Two `Claim` types in one system get conflated. |
| `evidence-ref` `type` now carries the ten-value enum | It was an unconstrained string with the rule in its description. A schema validates strings, not descriptions. The enum MUST stay identical to `claim_schema.EVIDENCE_TYPES`, the single authority ADR-20 D-A1 established after four allow-lists drifted and caused a 100% claim-rejection rate. |
| `admission-decision` `decision` is now `admit`/`abstain`/`reject` | It was `[-1, 0, 1]`, notation indistinguishable from the ternary vote model ADR-10 v2.0 superseded in favour of analog weights. An admission verdict is not a vote weight. |
| `task-contract` `risk_tier` replaced by `blast_radius` | `R0..R3` duplicated `claim_schema.BlastRadius` (Local/Module/System/Substrate), which already drives `QUORUM_MIN` and override rules, and collided visually with the R1/R2 rule numbering in `integrity-provenance-validation.spec.md`. |

**Reading the word "Claim" in this bundle's prose:** the markdown documents predate this rename and use `Claim` for both concepts. Where a document discusses submitting to the consensus gate (notably `14_CONSENSUS_CLAIM_PACKET.md`) it means the repo's governance `Claim`. Where it discusses task-runtime epistemic state alongside LedgerEntry and SharedGist, it means `RuntimeClaim`. The prose was left unedited rather than mass-rewritten, because most usages are already correct and a sweep would have broken them.
