# Provenance Anchor Specification

- Version: 1.0.0
- Version: 2.0.0 — `flossi-anchor-2`. v1 anchors are refused, not upgraded:
  `signer` moved inside the signed bytes, so the pre-image differs.
- Status: ⚠️ Specified — implementation ✅ Verified against the live store.
  **External witnessing: git-tag carrier ❌ Blocked; OpenTimestamps ⚠️ Specified**
  — stamping is implemented and exercised end-to-end, but no proof has yet
  reached a Bitcoin attestation, and PENDING is not a witness. See Witnessing.
- **ADR-18 tier-2 review: PERFORMED 2026-08-29, outcome REVISION REQUIRED.**
  9 reviewers, 68 findings. Record:
  `docs/reviews/2026-08-29-model-identity-anomoly/MERGE-GROUPS.md`.
  Open against this spec: `G1` signer excluded from the signed bytes,
  `G4` `ANCHOR_STALE` is a count not a subset check (reproduced),
  `G5` the `prev_root` walk is unimplemented, `G9` key auto-mint with pinning off
  by default, `G2` the ladder was not satisfied for witnessing, `G12` the
  headline claim is false after a republish over a truncated store.
  **`spec_gate --check` passes on this entry. That is the gate reporting that a
  review happened, not that it approved.**
- Implementation: `packages/activity_log/anchor.py`, `scripts/provenance_anchor.py`
- Tests: `packages/activity_log/tests/test_anchor.py`
- Supersedes nothing. Complements `docs/specs/provenance-packet.spec.md`.

## Purpose

`provenance.py` makes **interior** deletion undeniable. Sequence numbers are
gapless per identity, so removing a packet from the middle of a chain leaves an
arithmetic hole that `E_PROVENANCE_CHAIN_GAP` enumerates by exact sequence
number.

That is the whole of what a self-signed chain can do for itself, and it is less
than it sounds:

- **Head truncation leaves no gap.** Delete every packet above sequence *n* and
  the chain ends at *n*. Nothing inside a self-signed chain distinguishes
  truncation from an agent that has not written since *n*.
- **Deleting a single-packet identity removes the chain entirely**, so nothing
  survives for a gap to be measured against.

Measured on the live store 2026-08-25: **96 of 99 identities are single-packet
chains**. The existing mechanism therefore covers roughly 3% of identities and
zero head truncations. Four external review layers rated wholesale head
truncation Critical; fourteen commits of validator hardening did not move it,
because no amount of validation inside a store can attest to what the store no
longer contains.

The missing primitive is a commitment to the **global set** of packets,
published where the store's owner does not control the record, recording each
identity's **head** — head position being precisely what a sequence number
cannot self-attest.

## Leaf

One leaf per packet. Preimage is RFC 8785 JCS over:

```json
{"d": "<SAID>", "i": "<AID>", "s": "<sequence as string>"}
```

Binding `i` and `s` alongside `d` is load-bearing. Hashing the SAID alone would
prove only that *some* packet with that digest existed once; including identity
and sequence makes an inclusion proof a statement about **chain position**,
which is the property head truncation attacks.

Leaves are sorted by `(identity, int(sequence), said)` before hashing. The
deterministic total order is what makes the root a **set commitment**: two
verifiers enumerating the same packets in different filesystem orders derive the
same root, or the anchor proves nothing portable.

## Tree

RFC 6962-shaped binary Merkle over BLAKE3-256, with domain separation:

| Node | Hash |
|---|---|
| Leaf | `blake3(0x00 ‖ preimage)` |
| Interior | `blake3(0x01 ‖ left ‖ right)` |
| Odd node | promoted unchanged to the next level |

Domain separation is not decorative: without it an interior node can be
presented as a leaf and an inclusion proof forged. Odd nodes are **promoted, not
duplicated** — duplicating the last node admits a second tree with the same
root.

The empty tree has its own constant, `E` + 43 zeros, so "no packets" is never
confusable with a real commitment.

BLAKE3 and `jcs` are already hard dependencies of `provenance.py`. This adds no
package.

Root encoding reuses the packet envelope's post-padded base64url — see
`provenance-packet.spec.md` section 9.3. It is an internal identifier and is
never handed to a CESR decoder.

## Anchor document

```
v                  "flossi-anchor-1"
generated_at       UTC ISO 8601. SELF-ASSERTED; see Limits.
hash               "blake3-256/jcs"
packet_count       integer
identity_count     integer
merkle_root        root over all leaves
identities[]       aid, count, max_seq, head_saids[], interior_gaps[], duplicate_seqs[]
unreadable[]       malformed files, NAMED rather than skipped
prev_root          previous anchor's merkle_root, or null at genesis
prev_generated_at  previous anchor's generated_at, or null
signer             Ed25519 AID
sig                "0B" + base64url signature
```

`head_saids` is a **list**. Slots in the live store already hold two occupants;
flattening that would anchor a fork as if it were a single head.

`interior_gaps` and `duplicate_seqs` are recorded **in** the anchor on purpose.
Freezing the store's known damage — the four holes on `DkuY…` at 3/36/37/39, the
duplicate slots on `DVpMe…` — means later damage cannot be laundered as
pre-existing. That is a strictly weaker and more honest claim than repairing
them, which is impossible: those packets are signed and gone.

**Signature scope.** **`sig` alone is excluded** from the signed bytes.
Everything else — including `signer` and the per-identity head summaries — is
covered. A signature cannot cover itself; the identity must be covered or the
signature attests the claims without attesting who made them.

Corrected 2026-08-29. This paragraph previously said `signer` was excluded too,
contradicting `anchor_signing_bytes()` in the same release that moved `signer`
inside the pre-image. A verifier written from the old text would reject every
anchor this code emits, and one that implemented the old rule faithfully would
reintroduce the signer-substitution flaw v2 exists to fix. Stated explicitly
because a verifier that guesses the scope wrong gets a signature failure
indistinguishable from tampering.

The anchor series is itself a hash chain via `prev_root`, so dropping an old
anchor breaks linkage and is visible rather than silent.

## Publish

1. Build the anchor, chaining `prev_root` to the previous one.
2. Sign with an existing Ed25519 identity from `.agent-surface/identity/` — the
   same PyNaCl path `create_packet` uses. No GPG, no SSH key, no new key type.
3. Write to `.anchors/anchor.json` in the repository.
4. Tag with the root **in the tag name** — this is the only carrier that
   reaches the public event record; see the correction below. The root is also
   written into the commit message, which is useful to a human reading `git log`
   and reaches no third party.
5. Push to the public remote.

**CORRECTION 2026-08-29 — half of this mechanism does not work.**

External review (`docs/reviews/2026-08-29-model-identity-anomoly`, finding
`GLM/F1`) claimed GitHub had removed commit content from `PushEvent`. Verified
against the live API, on this repository's own pushes:

```
$ gh api repos/G-0-B/FLOSS/events --jq '[.[]|select(.type=="PushEvent")][0].payload|keys'
["before","head","push_id","ref","repository_id"]
```

There is no `commits` key. GitHub announced the removal of push commit summaries
and counts on 2025-08-08, brownout-tested it on 2025-09-08, and shipped it on
2025-10-07 — ten months before this anchor was written. **The commit message
never reaches the firehose.** The genesis anchor `fbaae97` placed the root in a
commit message; that placement witnesses nothing.

The tag-name half survives. `CreateEvent` still carries the ref verbatim:

```
CreateEvent payload keys: ["description","full_ref","master_branch","pusher_type","ref","ref_type"]
```

so a tag named `prov-anchor-<timestamp>-<root>` does place the root in the public
event record. `DeleteEvent` carries `ref` too, so deleting an anchor tag is
itself externally visible — a partial answer to tag mutability, worth only as
much as the retention window below.

**Combined with `GROK/F3` — the repository has no tags and the CLI never creates
them — the surviving half has never been exercised, and the half that was used
does not work. The external-witness claim is ❌ Blocked, not ⚠️ Specified, until
a tag is pushed and its root retrieved from a third party.**

**Why the tag name.** The operator controls the store *and* the git remote, so a
ref they can rewrite constrains nobody. What the operator does not control is the
record third parties keep of a public push: a public repository emits
`CreateEvent` into GitHub's public events firehose, and that event carries the
ref name to mirrors with no write path back. Putting the
root in the ref name rather than only in file contents is what gets it into that
retained record.

`scripts/provenance_anchor.py` prints those git commands and runs none of them.
Publishing to a public repository is an operator decision.

## Witnessing

The git-tag mechanism is retained only as a human-readable convenience. The
witness of record is an OpenTimestamps stamp over the **merkle root string** —
not over the anchor file, since the root is the commitment and the file is one
serialization of it.

| | Git tag / firehose | OpenTimestamps |
|---|---|---|
| Operator-controlled ref in the trust path | yes | **no** |
| Expiry | **30 days** (Events API retention) | none — a Bitcoin block header does not expire |
| Exercised | never | end-to-end, pending confirmation |

**`opentimestamps` is an optional dependency and is in no requirements file.**
The direct probe (`docs/reviews/2026-08-29-model-identity-anomoly/PROBE-opentimestamps.md`)
found every `ots` CLI subcommand broken on Windows/CPython 3.13 — `python-bitcoinlib`
ctypes-loads an OpenSSL DLL that is not present — and two of three default
calendars serving expired TLS certificates. So this uses the library API directly
and never shells out, the calendar list is configurable, calendar failure is a
reported outcome rather than an exception, and absence of the package degrades to
publishing without a witness rather than to an import error.

Where things live:

- The **claim** — kind, digest, the calendars that accepted it — is a
  `witnesses[]` entry inside the anchor, covered by the signature, so witness
  claims cannot be added or removed after signing.
- The **proof** is a sidecar at `.anchors/witness/<root>.ots`. A pending stamp is
  upgraded to a Bitcoin attestation hours later, and a signed anchor must not be
  edited after signing.

Witness states: `ABSENT`, `UNAVAILABLE`, `PENDING`, `CONFIRMED`.

> **`PENDING` is not a witness.** Between stamping and Bitcoin confirmation you
> hold a volunteer-run calendar's promise. Reporting that as external witnessing
> would restate the git-tag mistake in a new place.

Witness state is reported **alongside** the store verdict and never folded into
it. A confirmed witness does not make a truncated store `VERIFIED`, and a missing
witness does not make an intact store a failure — they answer different
questions.

## What this still does not do

OpenTimestamps timestamps a **digest**. It cannot commit to a packet set, so it
does not replace the anchor — it replaces the anchor's publication mechanism. It
proves "no later than", never "no earlier than", so backdating remains
unprevented. It attests that a digest existed, not that the digest is the store's
true contents. An operator can simply stop stamping, and absence of a proof is
evidence of nothing.

Against the standing finding that republishing a consistent anchor over a
truncated store returns `VERIFIED`: this **improves it without solving it**. The
operator can still stamp a fresh anchor. What changes is that they cannot delete
the earlier proof, so equivocation becomes permanent and self-verifying for
anyone holding one — where the git-tag path let the record simply expire.

## Verify

A verifier needs a clone of the public repository and the pinned Ed25519 public
key.

1. Verify `sig` against the pinned key. An unauthenticated anchor is treated as
   **no anchor**.
2. Walk `prev_root` backwards and confirm the series is unbroken.
3. Independently recompute the root from whatever packet set they hold.
4. Cross-check the root against the **tag name** and — the load-bearing step —
   a **third-party mirror** of the event stream, with that mirror's ingest
   timestamp. Not the commit message: it is not in the event payload.

Steps 1–3 detect accident and third-party tampering. **Step 4 is the only step
that survives an operator who rewrites their own repository.**

## Outcomes

| Status | Exit | Meaning |
|---|---|---|
| `VERIFIED` | 0 | Roots match. |
| `ANCHOR_STALE` | 1 | Store is a strict superset; nothing anchored has gone. |
| `TRUNCATION_DETECTED` | 2 | Something anchored is gone. Names vanished identities, head regressions, missing head SAIDs. |
| `ANCHOR_MISMATCH` | 2 | Root differs with no head loss — an interior packet changed or went. |
| `ANCHOR_UNAVAILABLE` | 3 | No anchor, bad signature, or wrong pinned signer. |

The `STALE`/`TRUNCATION` split is what makes this usable as a routine gate:
honest growth is the common case and must not cry wolf, while loss must be loud.
`ANCHOR_STALE` is deliberately neither a pass nor a failure — a stale anchor is
not a verified one.

`ANCHOR_UNAVAILABLE` emits verbatim: *"NOT a pass. Store is unverifiable, not
verified."*

## Verified behaviour

Exercised against a copy of the live 253-packet store:

| Scenario | Result |
|---|---|
| Unchanged | `VERIFIED` |
| Head truncation (5 packets off the longest chain) | `TRUNCATION_DETECTED`, 1 head regression |
| Single-packet identity wiped | `TRUNCATION_DETECTED`, 1 vanished identity |
| Growth only | `ANCHOR_STALE`, delta +1 |
| Interior deletion | `ANCHOR_MISMATCH` (sequence gaps already own this) |
| Head removed **and** a packet added, counts equal | `TRUNCATION_DETECTED`, delta 0 |
| Packet moved to the store root | `VERIFIED` — `rglob`, not a fixed depth |
| Anchor field edited | `ANCHOR_UNAVAILABLE` |
| Wrong pinned signer | `ANCHOR_UNAVAILABLE` |

## Limits

Stated in full, because an unstated limit reads as a guarantee.

- **It does not stop the operator.** It converts undetectable deletion into
  detectable **equivocation**, and only for a party who retained a prior root.
  Absent any retained copy this is a self-consistency check and nothing more.
- **The window before the first witness is undefended.** A packet created and
  deleted between anchor runs never enters a leaf set. The anchor period *is*
  the exposure window.
- **Backdating is not prevented.** `generated_at` is self-asserted. Only a
  mirror's ingest time is external, and it bounds "no later than", never "no
  earlier than".
- **Repository deletion defeats the ref.** Deleting or privating the repository
  removes the anchor; only already-ingested firehose records survive — which is
  exactly why the root must ride in the tag name.
- **The ingestion window is 30 days, not 90.** GitHub cut Events API retention
  from 90 days to 30 on 2025-01-30 (review finding `GLM/F5`, confirmed). A mirror
  that does not ingest within 30 days has nothing to ingest, so anchor cadence
  and mirror-confirmation cadence are both bounded by that number.
- **The signing key is the operator's key.** A rotated identity can sign a fresh
  consistent series. **Pinning the public key beforehand is the actual root of
  trust**, not the signature.
- **It says nothing about validity or truth.** Membership and completeness only.
  An anchor over 253 invalid packets is a perfectly valid anchor.
  `validate_packet` still owns signatures, SAIDs and the evidence DAG.
- **It does not repair the existing holes.** They are signed and unrecoverable.
- **Third-party mirror retention is ⚠️ Specified, not ✅ Verified.** The
  repository is public and the events mechanism exists, but no mirror has been
  confirmed to have indexed it. Publish one anchor, then confirm the root is
  retrievable externally. If it is not, step 4 of Verify does not hold and the
  Limits section becomes the whole story.

Truthful one-line scope: **this makes silent wholesale truncation impossible and
loud truncation attributable, for anyone who has held one prior root — it does
not make the operator honest.**

## Composition

The leaf and root construction is the stable interface; witnessing is pluggable.
A future `witnesses[]` array carries `{kind, ref, witnessed_at}`. Git-ref is
`kind: "git-ref"`. Rekor becomes a `hashed-rekord` over the same root, at which
point a non-operator-controlled Merkle log anchors ours and real inclusion
proofs exist. SCITT: the anchor is already shaped as a signed statement with the
root as payload. Holochain: the root becomes a DHT entry whose validation
callback re-derives it, at which point the anchor stops being external and
becomes substrate-native.

**None of these require changing leaf computation** — the root string is the
whole interface, and multi-witness disagreement is itself the strongest possible
signal.

Holochain is the correct terminal destination and is **disqualified as the first
anchor**: a single-operator DHT provides zero anchoring in principle, and the
node is not running.

## Outstanding

The ADR-18 tier-2 reuse review has **not** been performed. The prior-art survey
(Rekor, SCITT, Trillian, git tags, Holochain) was conducted by a single model
family, which does not satisfy the ≥3 provider surfaces / ≥4 model families
independence bar. The registry entry is marked `emergency` accordingly, which
emits a retrospective-audit warning rather than a silent pass.
