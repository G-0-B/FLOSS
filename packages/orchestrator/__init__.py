"""
FLOSSIØULLK Orchestrator — Python ↔ Holochain bridge and consensus gate.

This package is the seam between the ARF Python memory layer and the
Holochain substrate. It owns three things:

  - claim_schema    — dataclasses for Claim / Vote / Decision (wire format)
  - consensus_gate  — ternary {-1, 0, +1} voting → Outcome, with ADR stubs
  - holochain_connector / serialization — substrate bridge primitives

Reading this package fresh? Start with `consensus_gate.py` (it's the entry
point most other modules route through), then `claim_schema.py` for the
data model. The full contract lives in `docs/specs/consensus-gate.spec.md`;
design rationale is in `docs/adr/ADR-6-four-system-integration.md`.

The gate is a router, not a controller: it accepts Claims and Votes from
any agent — human, model, ensemble, or otherwise — and records decisions.
It does not command voters or decide outcomes on their behalf.
"""
