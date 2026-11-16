# Spec-Gate ("-1 layer") — D7

```yaml
id: "spec-gate"
status: "Adopted 2026-06-12 (Anthony: both wirings)"
truth_status: "Verified — check + hook wiring live, registry seeded (75 entries)"
decision_lineage: "Metaharness inventory D7 (Ember seed pack file 01, 2026-06-09) -> adopted 2026-06-12"
schema: "FLOSS/docs/specs/spec-registry.schema.json"
registry: "FLOSS/docs/specs/spec-registry.json"
code: "FLOSS/scripts/spec_gate.py"
```

## Problem

Root cause named by Anthony (2026-06-09): artifacts get **built before being
spec'd** as deliberate artifacts. Spec-driven development is intended, but the
"-1 layer" — plan/research/spec *before* build — was not enforced anywhere.
Result: script and doc sprawl, the project's empirically dominant failure mode.

## Mechanism

Every artifact on a **gated surface** must have a one-line spec stub in
`spec-registry.json` — a single sentence of intent. That is the entire tax.

- **Audit (fail-closed):** `python FLOSS/scripts/spec_gate.py --check` exits 1
  listing unregistered gated artifacts. Run alongside materializer `--check`
  sweeps; CI/pre-commit canary remains the deferred decision #10 slot.
- **Runtime (advisory):** `hook_post_write.py` calls `spec_gate.advisory_note()`
  on every mutating tool call; unregistered gated paths surface a warning as
  hook additionalContext. The hook never blocks — exit 0 always.
- **Registering costs one command:**
  `python FLOSS/scripts/spec_gate.py --add <path> --spec "<one-line intent>"`

## Scope discipline (the friction answer)

Gated (v0.1): `FLOSS/scripts/`, `FLOSS/docs/specs/`, `FLOSS/docs/adr/`.
Added since: `FLOSS/hooks/` (2026-07-26); `FLOSS/packages/`, `FLOSS/ARF/dnas/`,
`FLOSS/.github/workflows/` and the six `FLOSS/shared-*-surface.json` manifests
(2026-11-16). The tuple `GATED_SURFACES` in `spec_gate.py` is what is enforced.

Files already on the 2026-11-16 surfaces are registered `grandfathered: true`
with no tier, so the reuse gate does not judge them. That exemption has two
limits (operator decision 2026-11-16): a change that modifies such a file must
give its entry a tier in the same change (`--check --changed-from <ref>`), and
from `GRANDFATHER_DEADLINE` (2027-03-16) any entry still grandfathered fails
`--check`. The `--changed-from` flag is not yet passed by any CI workflow. The
gate's summary line counts judged and unjudged entries separately.

**Never gated:** the workspace root, `FLOSS/docs/research/` (including all
`intake_raw/` buckets), `docs/agent-memory/`, `.agent-surface/`, tests, caches.
Context-continuation packets, seed artifacts, and shared agent-memory states are
intake-mouth material — **pre-spec by definition**. The gate exists to stop
*canon* bloat, not to tax continuity. If a continuation artifact graduates into
`docs/specs/` or `docs/adr/`, it pays the one-line tax at promotion time, which
is exactly when intent should be stated anyway.

`FLOSS/packages/` is deliberately out of v0.1: package edits already get real
review via the post-write Claim + consensus round. Revisit at v0.2 if sprawl
appears there.

## Grandfathering

All artifacts existing at gate introduction were registered en masse with
`grandfathered: true` stubs. Backfill a deliberate one-liner on next touch —
the gate stays green meanwhile; the flag marks debt without blocking work.

## Failure modes considered

- Registry deleted/corrupt → `--check` fails closed; hook degrades to a
  registry-unreadable advisory (never blocks).
- Registered-but-deleted artifacts → reported as STALE, non-fatal (prune or
  restore deliberately; never auto-pruned).
- Hook recursion: `spec_gate.py` lives on a gated surface itself and is
  registered; advisory path is read-only and exception-swallowing.
