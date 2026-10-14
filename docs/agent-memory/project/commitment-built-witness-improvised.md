---
id: project-commitment-built-witness-improvised
type: project
created: '2026-08-29'
status: active
applies_to:
- any-agent
source: cross_audit
title: This project builds the commitment and improvises the witness
---

# This project builds the commitment and improvises the witness

**Date:** 2026-08-29
**Status:** ✅ Verified — four independent instances, found by two unrelated review panels
**Related:** [`scale-mismatch-is-the-recurring-defect.md`](scale-mismatch-is-the-recurring-defect.md), `docs/research/2026-08-29-cross-audit-learnings.md`

## The pattern

| Artifact | Commitment layer | Witness layer |
|---|---|---|
| Provenance anchor | Merkle set commitment — sound | git tag: one carrier dead, the other never created |
| Provenance packets | BLAKE3 + Ed25519 — sound | KERI-*shaped*, not KERI-compatible |
| Materializer | BLAKE3 hashline — sound | no signed attestation; SLSA L1 equivalent |
| Review records | 9 real reviewers, real findings | unresolvable path, then unpinned content |

The hard cryptographic part is done carefully every time. The part that makes the
result legible to someone outside the project is invented on the spot every time.

Two unrelated panels — the anchor review and the ADR-18 materializer audit —
found this independently against different artifacts. That is what makes it a
bias rather than four coincidences, and it means the pattern is visible from
outside even when it is not visible from inside.

## Why it happens

A commitment has to fit your data, so building one feels like the job. A witness
has to be recognisable to a party who does not trust you — and that requirement
is invisible while you are the only reader. Every one of these held up fine until
someone external tried to check it.

## The rule

> **The witness is the part to adopt.**

Build the commitment; adopt the witness. A standard exists precisely because a
stranger has to be able to read it. Concretely, in descending order of how much
was learned the hard way:

- OpenTimestamps over the anchor root, not a git tag whose carrier expires in 30
  days and whose other half GitHub removed in 2025-10.
- in-toto Statements around provenance packets, not a bespoke envelope wearing
  KERI's field names without KERI's encoding.
- Sigstore for signing — via the Python client, **not** by shelling out to
  `cosign`; the OpenTimestamps probe showed the CLI is the fragile part while the
  library API works.
- A pinned content digest on any evidence record, not a path that merely
  resolves.

## Corollary

**A mechanism whose value depends on it firing needs a test that it fires**,
separate from a test that it is configured. The anchor's tag was never created;
ADR-20's reviewer record never resolved; the materializer assumes Tier-A clients
honour blocking hooks with no runtime probe. Three instances, same shape:
configured is not the same as working, and only the second one is worth anything.
