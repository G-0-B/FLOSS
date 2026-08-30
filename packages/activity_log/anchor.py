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
import hashlib
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
    _said_digest,
)

# v1 -> v2 (2026-08-29): `signer` moved INSIDE the signed bytes, changing the
# pre-image, so v1 anchors cannot be verified under v2 rules.
#
# v2 -> v3 (2026-08-29): identities carry `leaf_saids`, the full [sequence, said]
# list. The subset check compared only OCCUPIED POSITIONS, so replacing a
# non-head packet with a different SAID at the same (identity, sequence) while
# the store also grew left every position occupied, the count higher, and the
# verdict ANCHOR_STALE -- which the pre-publish guard permits, so the loss was
# absorbed into the replacement anchor. That is the count-comparison defect one
# level up: positions are a weaker proxy for the same thing digests state
# exactly. Old anchors lack the field and are refused rather than checked
# loosely.
ANCHOR_VERSION = "flossi-anchor-3"
SUPPORTED_VERSIONS = frozenset({ANCHOR_VERSION})

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


def _file_digest(path: Path) -> str | None:
    """SHA-256 of a file's raw bytes, or None if it cannot be read.

    Unreadable packets are excluded from `leaves`, so they do not move the
    Merkle root -- which means the ONLY thing committing to them is this record.
    Comparing paths alone did not freeze the known damage it claimed to: swap a
    malformed file for different malformed bytes at the same path and both path
    sets match, the root is unchanged, and verification returned VERIFIED while
    the store's contents had changed.

    That is the same defect as comparing leaf POSITIONS instead of leaf digests,
    one level down: identity by locator rather than by content. Fixed there two
    commits ago and reintroduced here in the same breath.
    """

    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


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
        # UnicodeError too: Path.read_text raises UnicodeDecodeError on invalid
        # UTF-8, which is neither an OSError nor a JSONDecodeError, so a single
        # corrupt byte in any packet crashed BOTH publish and verify with a
        # traceback -- breaking verify_anchor's documented "never raises"
        # contract for exactly the malformed input the unreadable set exists to
        # report. provenance.py's indexers already catch it.
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            unreadable.append(
                {
                    "path": _relative(path, provenance_root),
                    "error": str(exc)[:160],
                    "sha256": _file_digest(path),
                }
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
                {
                    "path": _relative(path, provenance_root),
                    "error": "malformed header",
                    "sha256": _file_digest(path),
                }
            )
            continue
        try:
            slot = int(sequence)
        except ValueError:
            unreadable.append(
                {
                    "path": _relative(path, provenance_root),
                    "error": f"non-integer sequence {sequence!r}",
                    "sha256": _file_digest(path),
                }
            )
            continue
        # THE SAID MUST BE SATISFIED, NOT MERELY CLAIMED.
        #
        # The leaf used to be built from `t`/`i`/`s`/`d` copied straight off the
        # file, so a 129-byte header-only stub asserting the same four fields
        # reproduced the leaf of a 585-byte signed packet exactly -- signatures,
        # payload, artifact refs and evidence all deleted, anchor still
        # VERIFIED. Reproduced before this fix. That defeated the whole point:
        # the commitment was to what a file SAID about itself.
        #
        # `d` is a self-addressing digest over the packet's own content, so a
        # file merely claiming one cannot also satisfy it. Same reasoning
        # provenance._cursor_for already uses to pick between files claiming one
        # digest, and the same implementation -- not a second one.
        try:
            recomputed = _said_digest(document)
        except Exception:  # noqa: BLE001 -- malformed input must not wedge a scan
            recomputed = None
        if recomputed != said:
            unreadable.append(
                {
                    "path": _relative(path, provenance_root),
                    "error": (
                        f"SAID not satisfied: claims {said[:16]}..., content "
                        f"digests to {str(recomputed)[:16]}..."
                    ),
                    "sha256": _file_digest(path),
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
                # Every leaf, not just the heads. Positions alone cannot detect a
                # same-slot substitution, and the diagnosis has to be able to
                # name which digest went rather than only which slot emptied.
                "leaf_saids": sorted(
                    [leaf.sequence, leaf.said] for leaf in group
                ),
                # Recorded IN the anchor on purpose. Freezing the store's known
                # damage means later damage cannot be laundered as
                # pre-existing.
                "interior_gaps": [n for n in range(top + 1) if n not in present],
                "duplicate_seqs": sorted(n for n, c in counts.items() if c > 1),
            }
        )
    return summaries


def anchored_leaves(anchor: dict[str, Any]) -> set[tuple[str, int, str]]:
    """Every (identity, sequence, SAID) the anchor committed to.

    Read from `leaf_saids`, which v3 records. The position-only view below
    cannot see a packet being swapped for a different one in the same slot, and
    that is exactly what a subset check has to catch.
    """

    leaves: set[tuple[str, int, str]] = set()
    for entry in anchor.get("identities", []) or []:
        aid = entry.get("aid")
        if not isinstance(aid, str):
            continue
        for pair in entry.get("leaf_saids") or []:
            if (
                isinstance(pair, (list, tuple))
                and len(pair) == 2
                and isinstance(pair[0], int)
                and isinstance(pair[1], str)
            ):
                leaves.add((aid, pair[0], pair[1]))
    return leaves


def anchored_positions(anchor: dict[str, Any]) -> set[tuple[str, int]]:
    """Every (identity, sequence) the anchor committed to.

    Reconstructed from `max_seq` and `interior_gaps`, which together already
    describe the exact set of occupied slots per identity: {0..max_seq} minus
    the gaps. No new field, no growth in anchor size.

    This exists because `ANCHOR_STALE` was a COUNT comparison. The branch read
    `len(leaves) > packet_count` under a comment claiming "nothing anchored has
    gone", and nothing checked that -- so deleting an interior packet while
    adding two others reported honest growth. Four reviewers found it
    independently (G4) and it reproduced on the first try.
    """

    positions: set[tuple[str, int]] = set()
    for entry in anchor.get("identities", []) or []:
        aid = entry.get("aid")
        top = entry.get("max_seq")
        if not isinstance(aid, str) or not isinstance(top, int) or top < 0:
            continue
        gaps = {
            g for g in (entry.get("interior_gaps") or []) if isinstance(g, int)
        }
        positions.update((aid, n) for n in range(top + 1) if n not in gaps)
    return positions


def build_anchor(
    provenance_root: Path,
    previous: dict[str, Any] | None = None,
    witnesses: list[dict[str, Any]] | None = None,
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
        # External witnessing. Each entry records WHAT WAS REQUESTED -- kind,
        # digest, calendars -- and is covered by the signature. The proof itself
        # is a sidecar (see witness.proof_path): a pending stamp is upgraded to a
        # Bitcoin attestation hours later, and a signed anchor must not be edited
        # after signing.
        "witnesses": list(witnesses or []),
    }


def anchor_signing_bytes(anchor: dict[str, Any]) -> bytes:
    """Canonical bytes under signature. Excludes `sig` ONLY.

    `signer` used to be excluded too, which four reviewers independently flagged
    (G1) and one named as duplicate-signature key selection: with the identity
    outside the signed pre-image, any valid signature could be re-attributed to
    any `signer` value by editing one field. The signature attested the claims
    and not who made them.

    `sig` must still be excluded -- a signature cannot cover itself.
    """

    clone = {k: v for k, v in anchor.items() if k != "sig"}
    return jcs.canonicalize(clone)


def sign_anchor(anchor: dict[str, Any], identity: Identity) -> dict[str, Any]:
    """Sign the anchor INCLUDING its `signer` field.

    The signature must be computed over the dict that already carries `signer`,
    not over the one it was derived from -- otherwise the identity is still
    outside the pre-image and G1 is unfixed while looking fixed.
    """

    signed = dict(anchor)
    signed["signer"] = identity.aid
    signature = identity.signing_key.sign(anchor_signing_bytes(signed)).signature
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


SERIES_DIRNAME = "series"


def load_series(series_dir: Path | None) -> dict[str, dict[str, Any]]:
    """Every retained anchor, keyed by its merkle_root.

    `publish` used to write a single `anchor.json` and overwrite it, so the
    `prev_root` field pointed backwards into nothing and the spec's Verify step 2
    described a walk over a series that was never retained. Four reviewers
    flagged the missing walk (G5); one noticed the deeper problem that there was
    nothing to walk.
    """

    series: dict[str, dict[str, Any]] = {}
    if series_dir is None or not series_dir.exists():
        return series
    for path in sorted(series_dir.glob("*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        # UnicodeError too. `scan_packets` was fixed for exactly this and its two
        # sibling readers were not, so one invalid byte in an unrelated retained
        # anchor crashed the whole verdict instead of producing the structured
        # ANCHOR_UNAVAILABLE the caller is promised.
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        root = document.get("merkle_root")
        if isinstance(root, str):
            series[root] = document
    return series


def walk_series(
    anchor: dict[str, Any],
    series: dict[str, dict[str, Any]],
    *,
    expected_signer: str | None = None,
) -> dict[str, Any]:
    """Follow `prev_root` back to genesis. Reports, never raises.

    Every link is signature-checked. An unsigned or wrongly-signed ancestor is
    the same problem as an unsigned head: an anchor series whose history can be
    rewritten by anyone is not a series.
    """

    chain: list[str] = []
    seen: set[str] = set()
    cursor: dict[str, Any] | None = anchor
    problems: list[str] = []
    while cursor is not None:
        root = cursor.get("merkle_root")
        if not isinstance(root, str):
            problems.append("an anchor in the series has no merkle_root")
            break
        if root in seen:
            problems.append(f"cycle in the anchor series at {root[:16]}...")
            break
        seen.add(root)
        chain.append(root)
        prev = cursor.get("prev_root")
        if prev is None:
            return {
                "reached_genesis": True,
                "length": len(chain),
                "chain": chain,
                "problems": problems,
            }
        if not isinstance(prev, str):
            problems.append(f"{root[:16]}... has a non-string prev_root")
            break
        ancestor = series.get(prev)
        if ancestor is None:
            # A retained series that does not reach genesis is a hole, and the
            # hole is the finding. Do not silently treat the oldest file on disk
            # as the beginning of history.
            problems.append(
                f"anchor series breaks at {prev[:16]}...: no retained anchor "
                f"carries that root"
            )
            break
        ancestor_problem = anchor_signature_problem(
            ancestor, expected_signer=expected_signer
        )
        if ancestor_problem is not None:
            problems.append(f"ancestor {prev[:16]}...: {ancestor_problem}")
            break
        cursor = ancestor
    return {
        "reached_genesis": False,
        "length": len(chain),
        "chain": chain,
        "problems": problems,
    }


def verify_anchor(
    provenance_root: Path,
    anchor: dict[str, Any] | None,
    *,
    expected_signer: str | None = None,
    series_dir: Path | None = None,
) -> dict[str, Any]:
    """Compare the current store against an anchor. Never raises."""

    if anchor is None:
        return {
            "status": ANCHOR_UNAVAILABLE,
            "reason": "no anchor found",
            "note": UNAVAILABLE_NOTE,
        }
    version = anchor.get("v")
    if version not in SUPPORTED_VERSIONS:
        # G20: the version field was written and never read, so a v1 anchor --
        # signed over a DIFFERENT pre-image, without `signer` -- would have been
        # handed to v2 verification rules. Refuse rather than guess.
        return {
            "status": ANCHOR_UNAVAILABLE,
            "reason": (
                f"anchor version {version!r} is not supported "
                f"(this build verifies {sorted(SUPPORTED_VERSIONS)})"
            ),
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

    # Verify step 2, which the spec has always specified and the code never did.
    series = walk_series(
        anchor, load_series(series_dir), expected_signer=expected_signer
    )

    result: dict[str, Any] = {
        "series": series,
        "anchored_root": anchored_root,
        "current_root": current_root,
        "anchored_at": anchor.get("generated_at"),
        "anchored_packets": anchor.get("packet_count"),
        "current_packets": len(leaves),
        "unreadable_now": unreadable,
    }
    # The unreadable set is part of the commitment, not a footnote.
    #
    # scan_packets excludes malformed and SAID-failing files from `leaves`, so
    # they do not move the root -- which meant a malformed packet could appear,
    # or an anchored malformed packet could be DELETED, and verification still
    # said VERIFIED. The spec's promise that malformed packets are "named rather
    # than skipped" was true of build and false of verify.
    #
    # Compared as sets rather than counted, and compared against the ANCHORED
    # set rather than required to be empty: the live store carries three
    # permanently damaged packets, so demanding an empty set would brick
    # verification forever -- the b0de2fe mistake this register records as CF-1.
    # Known damage is frozen; new or vanished damage is a finding.
    anchored_unreadable = {
        (str(entry.get("path")), entry.get("sha256"))
        for entry in (anchor.get("unreadable") or [])
        if isinstance(entry, dict)
    }
    current_unreadable = {(entry["path"], entry.get("sha256")) for entry in unreadable}
    result["unreadable_appeared"] = [
        {"path": path, "sha256": digest}
        for path, digest in sorted(
            current_unreadable - anchored_unreadable, key=lambda x: (x[0], x[1] or "")
        )
    ]
    result["unreadable_vanished"] = [
        {"path": path, "sha256": digest}
        for path, digest in sorted(
            anchored_unreadable - current_unreadable, key=lambda x: (x[0], x[1] or "")
        )
    ]

    # THESE TWO CHECKS ARE ABOUT THE ANCHOR, NOT THE STORE DELTA, SO THEY RUN
    # FIRST.
    #
    # Both were previously nested inside `if current_root == anchored_root`,
    # which made each of them conditional on the one thing they have nothing to
    # do with. Add one valid packet alongside a malformed one and the root
    # changes, so the unreadable comparison never ran and the verdict was
    # ANCHOR_STALE -- which publish permits, signing the new damage into the
    # baseline. Likewise a legitimately growing store over a BROKEN series
    # returned ANCHOR_STALE, publish accepted it, another link went onto the
    # broken history, and verification of the anchor just written reported
    # ANCHOR_UNAVAILABLE.
    #
    # A history that does not hold together is unusable whatever the store did
    # since, and damage appearing or vanishing is a finding whether or not the
    # root also moved.
    if series["problems"]:
        result["status"] = ANCHOR_UNAVAILABLE
        result["reason"] = "; ".join(series["problems"])
        result["note"] = UNAVAILABLE_NOTE
        return result

    if result["unreadable_appeared"] or result["unreadable_vanished"]:
        result["status"] = ANCHOR_MISMATCH
        result["findings"] = {
            "vanished_identities": [],
            "head_regressions": [],
            "missing_anchored_heads": [],
            "missing_anchored_positions": [],
            "missing_anchored_leaves": [],
            "packet_delta": len(leaves) - (anchor.get("packet_count") or 0),
            "unreadable_appeared": result["unreadable_appeared"],
            "unreadable_vanished": result["unreadable_vanished"],
        }
        return result

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

    # THE SUBSET CHECK. `ANCHOR_STALE` may only be reported when every position
    # the anchor committed to is still present. Growth is not evidence that
    # nothing was lost, and treating it as such is exactly the G4 defect.
    current_positions = {(leaf.identity, leaf.sequence) for leaf in leaves}
    missing_positions = sorted(anchored_positions(anchor) - current_positions)
    # And the digests, which positions cannot speak for.
    current_leaves = {(leaf.identity, leaf.sequence, leaf.said) for leaf in leaves}
    missing_leaves = sorted(anchored_leaves(anchor) - current_leaves)

    if vanished or regressions or missing_heads:
        result["status"] = TRUNCATION_DETECTED
    elif missing_positions or missing_leaves:
        # Anchored content is gone, but no head and no identity: an interior
        # loss. Reported as a mismatch rather than a truncation so the status
        # does not claim more than the evidence shows -- but never as STALE.
        result["status"] = ANCHOR_MISMATCH
    elif len(leaves) > (anchor.get("packet_count") or 0):
        # Growth only, and now actually checked: the anchored set is a subset of
        # what is present. The common case between runs. Distinct from VERIFIED
        # on purpose -- a stale anchor is not a passing anchor -- and distinct
        # from a loss so it does not cry wolf.
        result["status"] = ANCHOR_STALE
    else:
        result["status"] = ANCHOR_MISMATCH
    result["findings"] = {
        "vanished_identities": vanished,
        "head_regressions": regressions,
        "missing_anchored_heads": missing_heads,
        "missing_anchored_positions": [
            {"aid": aid, "sequence": seq} for aid, seq in missing_positions
        ],
        "missing_anchored_leaves": [
            {"aid": aid, "sequence": seq, "said": said}
            for aid, seq, said in missing_leaves
        ],
        "packet_delta": len(leaves) - (anchor.get("packet_count") or 0),
    }
    return result


def load_anchor(path: Path) -> dict[str, Any] | None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    # The third reader, unnamed by review. A corrupt anchor.json crashed BOTH
    # publish and verify -- and publish reads it to decide whether a predecessor
    # exists, so a single bad byte took down the command that would replace it.
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    # And valid JSON of the wrong SHAPE. Fixing the exception type without
    # checking the result type left `[]`, a bare string or a number sailing
    # through to `.get()` in verify_anchor and publish's preflight. An
    # operator-writable file cannot be trusted to be an object just because it
    # parsed.
    if not isinstance(document, dict):
        return None
    return document
