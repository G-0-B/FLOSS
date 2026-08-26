"""Merkle anchor over the provenance packet store.

WHY THIS EXISTS

`provenance.py` makes INTERIOR deletion undeniable: sequence numbers are gapless
per identity, so removing a packet from the middle of a chain leaves an
arithmetic hole that `E_PROVENANCE_CHAIN_GAP` enumerates by exact sequence
number. That is the whole of what a self-signed chain can do for itself, and it
is less than it sounds:

  * Head truncation leaves no gap. Delete every packet above sequence n and the
    chain simply ends at n. Nothing inside the chain distinguishes truncation
    from an agent that has not written since n.
  * Deleting a single-packet identity removes the chain entirely, so there is
    nothing left for a gap to be measured against.

Measured on the live store on 2026-08-25: 96 of 99 identities are single-packet
chains. The existing mechanism therefore covers roughly 3% of identities and
zero head truncations.

The missing primitive is a commitment to the GLOBAL SET of packets, published
somewhere the store's owner does not control, recording each identity's HEAD --
because head position is precisely the thing a sequence number cannot
self-attest.

WHAT THIS DOES NOT DO

It does not make the operator honest. The operator controls the packet store,
the git remote, and the signing key, so this converts undetectable deletion into
detectable EQUIVOCATION -- and only for a verifier who retained a prior root.
Absent any retained copy it is a self-consistency check and nothing more. The
window between anchor runs is undefended: a packet created and deleted inside it
never enters a leaf set. `generated_at` is self-asserted and proves nothing about
time. And an anchor says nothing about whether the packets are VALID -- an
anchor over 252 invalid packets is a perfectly valid anchor. `validate_packet`
still owns signatures, SAIDs and the evidence DAG.

The honest one-line scope: this makes silent wholesale truncation impossible and
loud truncation attributable, for anyone holding one prior root.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import blake3
import jcs
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from packages.activity_log.provenance import (
    Identity,
    _b64url_decode,
    _b64url_encode,
)

ANCHOR_VERSION = "flossi-anchor-1"

# Domain separation, RFC 6962 style: a leaf hash and an interior hash must never
# be confusable, or a second-preimage attack can present an interior node as a
# leaf and forge an inclusion proof.
LEAF_TAG = b"\x00"
NODE_TAG = b"\x01"

# Status vocabulary. Deliberately four values, not a boolean: the difference
# between "the store grew" and "something anchored is gone" is the difference
# between a routine gate passing and an alarm, and collapsing them would either
# cry wolf every session or hide the alarm.
VERIFIED = "VERIFIED"
ANCHOR_STALE = "ANCHOR_STALE"
TRUNCATION_DETECTED = "TRUNCATION_DETECTED"
ANCHOR_MISMATCH = "ANCHOR_MISMATCH"
ANCHOR_UNAVAILABLE = "ANCHOR_UNAVAILABLE"

EXIT_CODES = {
    VERIFIED: 0,
    ANCHOR_STALE: 1,
    TRUNCATION_DETECTED: 2,
    ANCHOR_MISMATCH: 2,
    ANCHOR_UNAVAILABLE: 3,
}

# An unavailable anchor is NOT a pass. Emitted verbatim so an operator reading
# CI output cannot mistake silence for verification.
UNAVAILABLE_NOTE = "NOT a pass. Store is unverifiable, not verified."


@dataclass(frozen=True)
class PacketLeaf:
    identity: str
    sequence: int
    said: str


def _hash(*parts: bytes) -> bytes:
    digest = blake3.blake3()
    for part in parts:
        digest.update(part)
    return digest.digest()


def _encode_root(raw: bytes) -> str:
    # Same post-padded base64url the packet envelope uses, for the same reason
    # and with the same caveat: see spec section 9.3. This is an internal
    # identifier, never handed to a CESR decoder.
    return "E" + base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def leaf_preimage(identity: str, sequence: str | int, said: str) -> bytes:
    """Bind identity AND sequence AND digest into one leaf.

    Hashing the SAID alone would prove only that some packet with that digest
    existed once. Including `i` and `s` makes an inclusion proof a statement
    about CHAIN POSITION, which is the property head truncation attacks.
    """

    return jcs.canonicalize({"d": said, "i": identity, "s": str(sequence)})


def merkle_root(leaves: list[bytes]) -> str:
    """RFC 6962-shaped binary Merkle root over BLAKE3-256.

    The empty tree gets its own distinct constant rather than the hash of
    nothing, so "no packets" is never confusable with a real root.
    """

    if not leaves:
        return "E" + "0" * 43
    nodes = [_hash(LEAF_TAG, leaf) for leaf in leaves]
    while len(nodes) > 1:
        promoted: list[bytes] = []
        for index in range(0, len(nodes) - 1, 2):
            promoted.append(_hash(NODE_TAG, nodes[index], nodes[index + 1]))
        if len(nodes) % 2:
            promoted.append(nodes[-1])
        nodes = promoted
    return _encode_root(nodes[0])


def _relative(path: Path, provenance_root: Path) -> str:
    try:
        return path.resolve().relative_to(provenance_root.resolve()).as_posix()
    except ValueError:
        return path.name


def scan_packets(provenance_root: Path) -> tuple[list[PacketLeaf], list[dict]]:
    """Read every packet under `provenance_root`, at any depth.

    `rglob`, not a fixed `*/*.json` glob. Packets are normally filed into dated
    subdirectories, but a fixed depth means a packet MOVED to the root or one
    level deeper silently leaves the leaf set -- which would hand an attacker a
    way to shrink the commitment without deleting anything.

    Malformed files are named in the second return value rather than skipped
    silently or raised on: a half-written packet must not be able to wedge the
    anchor run, and must not be able to disappear quietly either.
    """

    leaves: list[PacketLeaf] = []
    unreadable: list[dict] = []
    if not provenance_root.exists():
        return leaves, unreadable

    for path in sorted(provenance_root.rglob("*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            unreadable.append(
                {"path": _relative(path, provenance_root), "error": str(exc)[:160]}
            )
            continue
        if not isinstance(document, dict) or document.get("t") != "prov":
            continue
        identity = document.get("i")
        sequence = document.get("s")
        said = document.get("d")
        if not (
            isinstance(identity, str)
            and isinstance(sequence, str)
            and isinstance(said, str)
        ):
            unreadable.append(
                {"path": _relative(path, provenance_root), "error": "malformed header"}
            )
            continue
        try:
            slot = int(sequence)
        except ValueError:
            unreadable.append(
                {
                    "path": _relative(path, provenance_root),
                    "error": f"non-integer sequence {sequence!r}",
                }
            )
            continue
        leaves.append(PacketLeaf(identity=identity, sequence=slot, said=said))

    # Deterministic total order makes the root a SET commitment: two verifiers
    # enumerating the same packets in different filesystem orders must derive
    # the same root, or the anchor proves nothing portable.
    leaves.sort(key=lambda leaf: (leaf.identity, leaf.sequence, leaf.said))
    return leaves, unreadable


def _root_of(leaves: list[PacketLeaf]) -> str:
    return merkle_root(
        [leaf_preimage(leaf.identity, leaf.sequence, leaf.said) for leaf in leaves]
    )


def _identity_summaries(leaves: list[PacketLeaf]) -> list[dict]:
    grouped: dict[str, list[PacketLeaf]] = {}
    for leaf in leaves:
        grouped.setdefault(leaf.identity, []).append(leaf)

    summaries: list[dict] = []
    for aid, group in sorted(grouped.items()):
        sequences = sorted(leaf.sequence for leaf in group)
        present = set(sequences)
        counts: dict[int, int] = {}
        for slot in sequences:
            counts[slot] = counts.get(slot, 0) + 1
        top = max(sequences)
        summaries.append(
            {
                "aid": aid,
                "count": len(group),
                "max_seq": top,
                # A list, not a scalar: slots in the live store already hold
                # more than one occupant, and flattening that would let a fork
                # be anchored as if it were a single head.
                "head_saids": sorted(
                    leaf.said for leaf in group if leaf.sequence == top
                ),
                # Recorded IN the anchor on purpose. Freezing the store's known
                # damage means later damage cannot be laundered as
                # pre-existing.
                "interior_gaps": [n for n in range(top + 1) if n not in present],
                "duplicate_seqs": sorted(n for n, c in counts.items() if c > 1),
            }
        )
    return summaries


def build_anchor(
    provenance_root: Path, previous: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build (but do not sign or publish) an anchor over the current store."""

    leaves, unreadable = scan_packets(provenance_root)
    return {
        "v": ANCHOR_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hash": "blake3-256/jcs",
        "packet_count": len(leaves),
        "identity_count": len({leaf.identity for leaf in leaves}),
        "merkle_root": _root_of(leaves),
        "identities": _identity_summaries(leaves),
        "unreadable": unreadable,
        # The anchor SERIES is itself a hash chain, so dropping an old anchor
        # breaks linkage and is visible rather than silent.
        "prev_root": (previous or {}).get("merkle_root"),
        "prev_generated_at": (previous or {}).get("generated_at"),
    }


def anchor_signing_bytes(anchor: dict[str, Any]) -> bytes:
    """Canonical bytes under signature.

    `sig` and `signer` are excluded so the signature covers the anchor's claims
    and not itself -- the same shape `provenance._signing_bytes` uses, and for
    the same reason. Stated here explicitly because a verifier that guesses
    wrong gets a signature failure with no way to tell it apart from tampering.
    """

    clone = {k: v for k, v in anchor.items() if k not in ("sig", "signer")}
    return jcs.canonicalize(clone)


def sign_anchor(anchor: dict[str, Any], identity: Identity) -> dict[str, Any]:
    signed = dict(anchor)
    signed["signer"] = identity.aid
    signature = identity.signing_key.sign(anchor_signing_bytes(anchor)).signature
    signed["sig"] = "0B" + _b64url_encode(signature)
    return signed


def anchor_signature_problem(
    anchor: dict[str, Any], *, expected_signer: str | None = None
) -> str | None:
    """Return a reason the anchor's signature is unacceptable, or None.

    An unauthenticated anchor is treated as NO anchor by the caller. Signing is
    what stops anyone who can write to the repository from also writing the
    commitment that is supposed to constrain them.
    """

    signer = anchor.get("signer")
    signature = anchor.get("sig")
    if not isinstance(signer, str) or not signer.startswith(("D", "B")):
        return "anchor carries no usable signer identifier"
    if not isinstance(signature, str) or not signature.startswith("0B"):
        return "anchor carries no usable signature"
    if expected_signer is not None and signer != expected_signer:
        # Pinning is the actual root of trust here, not the signature: the
        # operator can always generate a fresh key and sign a fresh consistent
        # series. Only a verifier who pinned the key beforehand is protected.
        return (
            f"anchor signed by {signer[:16]}... but {expected_signer[:16]}... "
            f"was pinned"
        )
    try:
        VerifyKey(_b64url_decode(signer[1:])).verify(
            anchor_signing_bytes(anchor), _b64url_decode(signature[2:])
        )
    except (BadSignatureError, ValueError, TypeError) as exc:
        return f"anchor signature does not verify: {type(exc).__name__}"
    return None


def verify_anchor(
    provenance_root: Path,
    anchor: dict[str, Any] | None,
    *,
    expected_signer: str | None = None,
) -> dict[str, Any]:
    """Compare the current store against an anchor. Never raises."""

    if anchor is None:
        return {
            "status": ANCHOR_UNAVAILABLE,
            "reason": "no anchor found",
            "note": UNAVAILABLE_NOTE,
        }
    signature_problem = anchor_signature_problem(
        anchor, expected_signer=expected_signer
    )
    if signature_problem is not None:
        return {
            "status": ANCHOR_UNAVAILABLE,
            "reason": signature_problem,
            "note": UNAVAILABLE_NOTE,
        }

    leaves, unreadable = scan_packets(provenance_root)
    current_root = _root_of(leaves)
    anchored_root = anchor.get("merkle_root")

    result: dict[str, Any] = {
        "anchored_root": anchored_root,
        "current_root": current_root,
        "anchored_at": anchor.get("generated_at"),
        "anchored_packets": anchor.get("packet_count"),
        "current_packets": len(leaves),
        "unreadable_now": unreadable,
    }
    if current_root == anchored_root:
        result["status"] = VERIFIED
        return result

    anchored_identities = {
        entry.get("aid") for entry in anchor.get("identities", []) or []
    }
    current_identities = {leaf.identity for leaf in leaves}
    current_max: dict[str, int] = {}
    for leaf in leaves:
        current_max[leaf.identity] = max(
            current_max.get(leaf.identity, -1), leaf.sequence
        )
    current_saids = {leaf.said for leaf in leaves}

    vanished = sorted(aid for aid in anchored_identities - current_identities if aid)
    regressions: list[dict] = []
    missing_heads: list[dict] = []
    for entry in anchor.get("identities", []) or []:
        aid = entry.get("aid")
        anchored_max = entry.get("max_seq")
        now = current_max.get(aid)
        if now is not None and isinstance(anchored_max, int) and now < anchored_max:
            regressions.append(
                {"aid": aid, "anchored_max_seq": anchored_max, "current_max_seq": now}
            )
        for said in entry.get("head_saids", []) or []:
            if said not in current_saids:
                missing_heads.append({"aid": aid, "said": said})

    if vanished or regressions or missing_heads:
        result["status"] = TRUNCATION_DETECTED
    elif len(leaves) > (anchor.get("packet_count") or 0):
        # Growth only, nothing anchored has gone. The common case between runs.
        # Distinct from VERIFIED on purpose -- a stale anchor is not a passing
        # anchor -- and distinct from TRUNCATION so it does not cry wolf.
        result["status"] = ANCHOR_STALE
    else:
        # Root differs, no head is missing and no identity vanished: an interior
        # packet changed or went. Named separately so the report does not claim
        # a truncation it cannot demonstrate.
        result["status"] = ANCHOR_MISMATCH
    result["findings"] = {
        "vanished_identities": vanished,
        "head_regressions": regressions,
        "missing_anchored_heads": missing_heads,
        "packet_delta": len(leaves) - (anchor.get("packet_count") or 0),
    }
    return result


def load_anchor(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
