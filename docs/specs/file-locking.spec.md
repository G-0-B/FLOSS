# File Locking — Capability Spec

```yaml
id: "flossi0ullk-file-locking"
version: "0.1.0"
date: "2026-09-02"
status: "Specified — reuse verdict recorded; no lock code changed by this spec"
truth_status: "⚠️ Specified"
governed_by: "ADR-18 Prior-Art & Reuse Gate"
relates_to: ["ADR-20 (provenance validator reconciliation)", "ADR-12 (consent gate)"]
canonical_promotion: false
```

## Why this spec exists

`filelock` adoption was **accepted** on 2026-08-25 — ADR-20, *"Accepted but not
implemented here"* — after a four-auditor external meta-audit, and was still
undone eight days later while the hand-rolled lock accrued review rounds and
`py-filelock` 3.18.0 sat installed on the development machine, declared nowhere.

ADR-18's reuse gate did not catch it, and could not have: the gate reads
`docs/specs/spec-registry.json`, and the registry's `gated_surfaces` are
`FLOSS/scripts`, `FLOSS/hooks`, `FLOSS/docs/specs`, `FLOSS/docs/adr`.
**`FLOSS/packages/` — the product code, where every lock in this system lives —
is not a gated surface.** This spec exists in `docs/specs/` because that is
where the gate can see it.

## The capability, split by lifetime

The single most important thing in this document: **these are two different
capabilities and one library answers only one of them.** An undifferentiated
"adopt py-filelock" breaks the second.

### Surface A — process-lifetime locks. Verdict: **adopt**

A lock held for the duration of a running operation, released when that
operation ends *or when the process dies*. Current sites:

| Site | Lock file |
|---|---|
| `packages/activity_log/provenance.py:124` | `.identity.lock` |
| `packages/activity_log/provenance.py:273` | `.sequence.lock` |
| `packages/activity_log/anchor.py:215` | `.anchor-scan.lock` |

All three go through the hand-rolled `_acquire_lock`
(`packages/activity_log/provenance.py:159`), whose stale-reclamation defect
ADR-20 names as a likely cause of the holes and doubled origin in identity
`DkuYPguG98HM2nyR`.

`py-filelock` provides exactly these semantics — `msvcrt` on Windows, `fcntl`
on POSIX, a context manager, a timeout, and release-on-process-death for free
from the OS. There is no irreducible delta here. **Adopt.**

### Surface B — the daemon claim. Verdict: **build**, and the reason is load-bearing

A daemon's claim on a slot must **outlive the process that took it** — that is
the entire point of the claim. An OS advisory lock is released by the kernel on
process death **by definition**, so `py-filelock` cannot express this, and no
amount of configuration makes it able to.

This surface keeps the pid-file + `.identity` sidecar + compare-and-swap-remove
design. The irreducible delta is stated precisely: *a claim whose lifetime is
independent of any holding process*.

**A reviewer who reads only the verdict line will adopt the library for both
surfaces and silently break the daemon claim.** That is why this spec is
organised by lifetime rather than by call site.

## The transition, which is separate from the lifetime

Reclaiming a stale lock is not a matter of *checking harder*. Identity content —
pid, host, start time, command, source commit — narrows the window; it does not
close it. Between inspecting a lock and unlinking it, another process can create
a fresh one, and the reclaimer then deletes a live claim.

The transition must be a **compare-and-swap**: remove only if the file is still
the exact instance that was inspected, identified by `(st_dev, st_ino)` rather
than by path or content. Creation is `O_CREAT | O_EXCL`. This applies to
Surface B regardless of what Surface A adopts, and it is the correction that
closed three findings at once on the PR41 lineage after a review round had
concluded — wrongly — that no primitive existed beneath the claim.

## Sequencing, and what this spec deliberately does not do

1. **No lock code is changed by this spec.** ADR-20 reclassified this area
   **Substrate** (0.85, override forbidden) on 2026-08-25. Rewriting
   `_acquire_lock` is a governed change requiring a consensus round; the
   consensus gateway was unreachable when this was written
   (`ConnectionRefused` on `127.0.0.1:7334`).
2. **`py-filelock` is deliberately NOT yet added to `requirements-ci.txt`.**
   That file's stated scope is "exactly what `packages/`, `tests/`, and
   `scripts/tests/` need to import", and its own commentary records the
   discipline — *"Re-checked, not assumed."* Nothing imports `filelock` today.
   The declaration belongs in the same commit as the first import, not before
   it. Recorded here so the omission is a decision rather than an oversight.
3. **Surface A adoption should land before Surface B rework.** Adoption is a
   mechanical substitution with a library that already has the semantics;
   Surface B is a design change to a Substrate-class claim protocol.

## Acceptance criteria

- Every process-lifetime lock site goes through one adopted library, not a
  bespoke implementation.
- The daemon claim retains a lifetime independent of any holding process, and
  a test asserts a claim survives the death of the process that took it.
- Stale reclamation is a compare-and-swap against the inspected instance; a
  test asserts that a lock replaced between inspection and removal is not
  deleted.
- `filelock` appears in `requirements-ci.txt` in the same commit as the first
  `import filelock`, and not before.
- No claim of adoption is recorded until a logged invocation produced project
  value — see `docs/agent-memory/project/installation-not-adoption.md`.

## Evidence

- `packages/activity_log/provenance.py:159` — `_acquire_lock`, the hand-rolled implementation.
- `packages/activity_log/provenance.py:124,273`, `anchor.py:215` — the three call sites.
- `ADR-20:589` — *"Accepted but not implemented here"*, listing `filelock` adoption.
- ADR-20 §"What this found in the live chain" — the holes attributed to the
  `_acquire_lock` stale-reclamation bug and the daemon singleton races.
- `python -c "import filelock; print(filelock.__version__)"` → `3.18.0`, installed, undeclared.
- `docs/specs/spec-registry.json` `gated_surfaces` — `FLOSS/packages/` absent.
- `docs/reviews/2026-09-01-polyglot-plugin-materializer-spec/GATE-ADOPTION-AUDIT.md` — how the gate missed it.
