"""External witnessing for the provenance anchor, via OpenTimestamps.

WHY THIS REPLACES THE GIT TAG

The anchor's original witness was the merkle root carried in a git tag name and
commit message, on the theory that a public push puts those into GitHub's event
firehose where the operator cannot rewrite them. Review found half of that false
and the other half unexercised:

  * `PushEvent` has carried no `commits` key since 2025-10-07, so the commit
    message reaches nobody. Verified against this repository's own pushes.
  * `CreateEvent` still carries the tag ref, so the tag-name carrier works -- but
    no tag was ever created.
  * Events API retention was cut from 90 days to 30 on 2025-01-30, so even the
    working carrier expires.

A Bitcoin block header does not expire, and no operator-controlled ref sits in
the trust path. That is the whole argument.

WHAT OPENTIMESTAMPS IS AND IS NOT

It timestamps a DIGEST. It cannot commit to a packet set, so it does not replace
the Merkle anchor -- it replaces the anchor's publication mechanism. The ladder
verdict is compose, not adopt.

It proves "no later than", never "no earlier than". Backdating remains
unprevented. It attests that a digest existed, not that the digest is the store's
true contents. An operator can simply stop stamping, and absence of a proof is
evidence of nothing.

OPTIONAL BY DESIGN

`opentimestamps` is NOT a project requirement and is not in any requirements
file. The direct probe on 2026-08-29 found two reasons to keep it optional:
every `ots` CLI subcommand dies on Windows/CPython 3.13 inside
`bitcoin.core.key` (it ctypes-loads an OpenSSL DLL that is not present), and two
of the three default calendars had expired TLS certificates. The library API
avoids the broken module, which is why this uses it directly and never shells out
to `ots`.

Absent the package, every function here degrades to a reported unavailability.
It never raises, and a missing witness is never silently treated as a present
one.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

# Default calendar pool. Configurable because it must be: at probe time only one
# of these three answered, and a hard-coded single point of failure in a
# witnessing layer is its own defect.
DEFAULT_CALENDARS = (
    "https://b.pool.opentimestamps.org",
    "https://a.pool.opentimestamps.org",
    "https://alice.btc.calendar.opentimestamps.org",
    "https://bob.btc.calendar.opentimestamps.org",
)

WITNESS_KIND = "opentimestamps"

# Witness states. PENDING is deliberately not a witness: between stamping and
# Bitcoin confirmation you hold a calendar's promise, and a promise from a
# volunteer-run server is not the property this layer exists to provide.
WITNESS_ABSENT = "ABSENT"
WITNESS_UNAVAILABLE = "UNAVAILABLE"
WITNESS_PENDING = "PENDING"
WITNESS_CONFIRMED = "CONFIRMED"


def root_digest(merkle_root: str) -> bytes:
    """The 32 bytes handed to OpenTimestamps.

    The ROOT STRING, not the anchor file. The root is the commitment; the file
    is one serialization of it, and stamping the file would bind the proof to a
    formatting choice.
    """

    return hashlib.sha256(merkle_root.encode("ascii")).digest()


def _ots():
    """Import the library, or return None. Never raises."""

    try:
        from opentimestamps.calendar import RemoteCalendar
        from opentimestamps.core.op import OpSHA256
        from opentimestamps.core.serialize import (
            BytesDeserializationContext,
            BytesSerializationContext,
        )
        from opentimestamps.core.timestamp import DetachedTimestampFile, Timestamp

        return {
            "RemoteCalendar": RemoteCalendar,
            "OpSHA256": OpSHA256,
            "Timestamp": Timestamp,
            "DetachedTimestampFile": DetachedTimestampFile,
            "ser": BytesSerializationContext,
            "deser": BytesDeserializationContext,
        }
    except Exception:  # noqa: BLE001 -- absent, broken install, or platform issue
        return None


def available() -> bool:
    return _ots() is not None


def stamp_root(
    merkle_root: str,
    *,
    calendars: tuple[str, ...] = DEFAULT_CALENDARS,
    timeout: int = 30,
) -> dict[str, Any]:
    """Request a timestamp over the root. Returns a report; never raises.

    Calendar failure is a reported outcome, not an exception. At probe time two
    of three defaults were unreachable on expired certificates, so a stamp run
    that treated any failure as fatal would fail most of the time for reasons
    that have nothing to do with the store.
    """

    ots = _ots()
    if ots is None:
        return {
            "status": WITNESS_UNAVAILABLE,
            "reason": "the `opentimestamps` package is not installed or not importable",
            "digest": root_digest(merkle_root).hex(),
            "attested": [],
            "failed": [],
            "proof": None,
        }

    digest = root_digest(merkle_root)
    timestamp = ots["Timestamp"](digest)
    attested: list[str] = []
    failed: list[dict[str, str]] = []
    for url in calendars:
        try:
            timestamp.merge(
                ots["RemoteCalendar"](url).submit(digest, timeout=timeout)
            )
            attested.append(url)
        except Exception as exc:  # noqa: BLE001
            failed.append({"calendar": url, "error": f"{type(exc).__name__}: {exc}"[:200]})

    if not attested:
        return {
            "status": WITNESS_UNAVAILABLE,
            "reason": "no calendar accepted the stamp",
            "digest": digest.hex(),
            "attested": [],
            "failed": failed,
            "proof": None,
        }

    buffer = ots["ser"]()
    ots["DetachedTimestampFile"](ots["OpSHA256"](), timestamp).serialize(buffer)
    return {
        "status": WITNESS_PENDING,
        "digest": digest.hex(),
        "attested": attested,
        "failed": failed,
        "proof": buffer.getbytes(),
    }


def _attestation_counts(timestamp, ots) -> tuple[int, int, list[str]]:
    from opentimestamps.core.notary import (
        BitcoinBlockHeaderAttestation,
        PendingAttestation,
    )

    pending = confirmed = 0
    heights: list[str] = []

    def walk(node):
        nonlocal pending, confirmed
        for attestation in node.attestations:
            if isinstance(attestation, BitcoinBlockHeaderAttestation):
                confirmed += 1
                heights.append(str(attestation.height))
            elif isinstance(attestation, PendingAttestation):
                pending += 1
        for _op, child in node.ops.items():
            walk(child)

    walk(timestamp)
    return pending, confirmed, heights


def inspect_proof(proof: bytes, *, expected_digest: bytes | None = None) -> dict[str, Any]:
    """Report what a proof actually attests. Never raises."""

    ots = _ots()
    if ots is None:
        return {
            "status": WITNESS_UNAVAILABLE,
            "reason": "the `opentimestamps` package is not installed or not importable",
        }
    try:
        detached = ots["DetachedTimestampFile"].deserialize(ots["deser"](proof))
    except Exception as exc:  # noqa: BLE001
        return {"status": WITNESS_UNAVAILABLE, "reason": f"unreadable proof: {exc}"[:200]}

    if expected_digest is not None and detached.file_digest != expected_digest:
        # A proof for some other digest is worse than no proof: it looks like
        # evidence and attests a different thing.
        return {
            "status": WITNESS_UNAVAILABLE,
            "reason": (
                f"proof is over {detached.file_digest.hex()[:16]}... but this "
                f"anchor's root digests to {expected_digest.hex()[:16]}..."
            ),
        }

    pending, confirmed, heights = _attestation_counts(detached.timestamp, ots)
    return {
        "status": WITNESS_CONFIRMED if confirmed else WITNESS_PENDING,
        "digest": detached.file_digest.hex(),
        "pending_attestations": pending,
        "bitcoin_attestations": confirmed,
        "bitcoin_block_heights": heights,
        # Said plainly, because "PENDING" reads like partial success and is not.
        "note": (
            None
            if confirmed
            else "PENDING is a calendar promise, not a Bitcoin attestation. "
            "It is not yet an external witness."
        ),
    }


def upgrade_proof(proof: bytes, *, timeout: int = 30) -> dict[str, Any]:
    """Ask the calendars to complete a pending proof. Never raises."""

    ots = _ots()
    if ots is None:
        return {"status": WITNESS_UNAVAILABLE, "reason": "package not importable"}
    from opentimestamps.core.notary import PendingAttestation

    try:
        detached = ots["DetachedTimestampFile"].deserialize(ots["deser"](proof))
    except Exception as exc:  # noqa: BLE001
        return {"status": WITNESS_UNAVAILABLE, "reason": f"unreadable proof: {exc}"[:200]}

    def pendings(node):
        for attestation in node.attestations:
            if isinstance(attestation, PendingAttestation):
                yield attestation, node
        for _op, child in node.ops.items():
            yield from pendings(child)

    upgraded = 0
    notes: list[str] = []
    for attestation, node in list(pendings(detached.timestamp)):
        url = attestation.uri
        url = url.decode() if isinstance(url, bytes) else url
        try:
            node.merge(ots["RemoteCalendar"](url).get_timestamp(node.msg, timeout=timeout))
            upgraded += 1
        except Exception as exc:  # noqa: BLE001
            notes.append(f"{url}: {type(exc).__name__}: {exc}"[:200])

    buffer = ots["ser"]()
    detached.serialize(buffer)
    result = inspect_proof(buffer.getbytes())
    result["upgraded_attestations"] = upgraded
    result["notes"] = notes
    result["proof"] = buffer.getbytes()
    return result


def proof_path(anchor_dir: Path, merkle_root: str) -> Path:
    """Where a root's proof lives.

    A sidecar, NOT a field inside the anchor. A pending proof is upgraded to a
    Bitcoin attestation hours later, and a signed anchor must not be edited after
    signing -- so the immutable claim (that a stamp was requested, over which
    digest, at which calendars) lives in the signed anchor, and the mutable proof
    lives here.
    """

    return anchor_dir / "witness" / f"{merkle_root}.ots"
