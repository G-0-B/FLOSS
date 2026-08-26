# Provenance Anchor Specification

- Version: 1.0.0
- Status: ⚠️ Specified — implementation ✅ Verified against the live store, publication ⚠️ not yet performed
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

**Signature scope.** `sig` and `signer` are excluded from the signed bytes;
everything else is included, so the per-identity head summaries are covered.
This is stated explicitly because a verifier that guesses the scope wrong gets a
signature failure indistinguishable from tampering.

The anchor series is itself a hash chain via `prev_root`, so dropping an old
anchor breaks linkage and is visible rather than silent.

## Publish

1. Build the anchor, chaining `prev_root` to the previous one.
2. Sign with an existing Ed25519 identity from `.agent-surface/identity/` — the
   same PyNaCl path `create_packet` uses. No GPG, no SSH key, no new key type.
3. Write to `.anchors/anchor.json` in the repository.
4. Commit with the root **in the commit message**; tag with the root **in the
   tag name**.
5. Push to the public remote.

**Why the tag name and the message, not only the file.** This is the whole
trick. The operator controls the store *and* the git remote, so a ref they can
rewrite constrains nobody. What the operator does not control is the record
third parties keep of a public push: a public repository emits `PushEvent` and
`CreateEvent` into GitHub's public events firehose, and those events carry ref
names and commit message text to mirrors with no write path back. Putting the
root in the ref name and message rather than only in file contents is what gets
it into that retained record.

`scripts/provenance_anchor.py` prints those git commands and runs none of them.
Publishing to a public repository is an operator decision.

## Verify

A verifier needs a clone of the public repository and the pinned Ed25519 public
key.

1. Verify `sig` against the pinned key. An unauthenticated anchor is treated as
   **no anchor**.
2. Walk `prev_root` backwards and confirm the series is unbroken.
3. Independently recompute the root from whatever packet set they hold.
4. Cross-check the root against the tag name, the commit message, and — the
   load-bearing step — a **third-party mirror** of the event stream, with that
   mirror's ingest timestamp.

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
