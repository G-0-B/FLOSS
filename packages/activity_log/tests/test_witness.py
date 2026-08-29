"""The witness layer must degrade honestly and never overstate what it has.

`opentimestamps` is an optional dependency, deliberately: the direct probe on
2026-08-29 found every `ots` CLI subcommand broken on Windows/CPython 3.13
(`bitcoin.core.key` ctypes-loads a missing OpenSSL DLL) and two of three default
calendars serving expired TLS certificates. A hard requirement would have made
those someone else's problem at import time.

So most of these tests run with the package ABSENT, which is the configuration
CI actually has, and assert that absence is reported rather than papered over.
The network is never touched.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.activity_log import witness as witness_lib  # noqa: E402

ROOT = "E3Ehni4XGXL3Zku90BaAfB_HyCOGR4x_cZVCDGTUlYi0"
HAVE_OTS = witness_lib.available()


def test_the_root_string_is_what_gets_stamped():
    """Not the anchor file.

    The root is the commitment; the file is one serialization of it. Stamping
    the file would bind the proof to a formatting choice, so a re-indented
    anchor would need a new stamp for the same commitment.
    """
    assert witness_lib.root_digest(ROOT) == hashlib.sha256(ROOT.encode("ascii")).digest()
    assert len(witness_lib.root_digest(ROOT)) == 32
    assert witness_lib.root_digest(ROOT) != witness_lib.root_digest(ROOT + "x")


def test_a_missing_package_is_reported_not_raised():
    """Publishing must not die because an optional dependency is absent."""
    if HAVE_OTS:
        pytest.skip("opentimestamps is installed in this environment")

    result = witness_lib.stamp_root(ROOT)
    assert result["status"] == witness_lib.WITNESS_UNAVAILABLE
    assert result["proof"] is None
    assert "not installed" in result["reason"]
    # The digest is still reported: what WOULD have been stamped is useful even
    # when nothing was.
    assert result["digest"] == witness_lib.root_digest(ROOT).hex()


def test_inspect_and_upgrade_also_degrade():
    if HAVE_OTS:
        pytest.skip("opentimestamps is installed in this environment")

    assert witness_lib.inspect_proof(b"anything")["status"] == (
        witness_lib.WITNESS_UNAVAILABLE
    )
    assert witness_lib.upgrade_proof(b"anything")["status"] == (
        witness_lib.WITNESS_UNAVAILABLE
    )


def test_garbage_proof_bytes_are_unavailable_not_a_crash():
    if not HAVE_OTS:
        pytest.skip("needs opentimestamps to reach the parser")

    result = witness_lib.inspect_proof(b"not an ots proof at all")
    assert result["status"] == witness_lib.WITNESS_UNAVAILABLE
    assert "unreadable" in result["reason"]


def test_a_proof_for_a_different_digest_is_rejected():
    """Worse than no proof: it looks like evidence and attests another thing."""
    if not HAVE_OTS:
        pytest.skip("needs opentimestamps to construct a proof")

    from opentimestamps.core.notary import PendingAttestation
    from opentimestamps.core.op import OpSHA256
    from opentimestamps.core.serialize import BytesSerializationContext
    from opentimestamps.core.timestamp import DetachedTimestampFile, Timestamp

    other = hashlib.sha256(b"some other commitment").digest()
    timestamp = Timestamp(other)
    # An empty timestamp cannot be serialized, so give it one attestation. No
    # network: the point is the digest mismatch, not the attestation.
    timestamp.attestations.add(PendingAttestation("https://example.invalid"))
    buffer = BytesSerializationContext()
    DetachedTimestampFile(OpSHA256(), timestamp).serialize(buffer)

    result = witness_lib.inspect_proof(
        buffer.getbytes(), expected_digest=witness_lib.root_digest(ROOT)
    )
    assert result["status"] == witness_lib.WITNESS_UNAVAILABLE
    assert "but this" in result["reason"]


def test_pending_is_not_confirmed():
    """The distinction the whole layer turns on.

    Between stamping and Bitcoin confirmation you hold a volunteer-run server's
    promise. Reporting that as a witness would restate the git-tag mistake in a
    new place.
    """
    assert witness_lib.WITNESS_PENDING != witness_lib.WITNESS_CONFIRMED
    assert witness_lib.WITNESS_ABSENT != witness_lib.WITNESS_PENDING


def test_the_proof_path_is_a_sidecar_keyed_by_root(tmp_path):
    """Not a field inside the anchor.

    A pending proof is upgraded hours later. A signed anchor must not be edited
    after signing, so the immutable claim lives inside it and the mutable proof
    lives beside it.
    """
    path = witness_lib.proof_path(tmp_path, ROOT)
    assert path.parent == tmp_path / "witness"
    assert path.name == f"{ROOT}.ots"
    assert witness_lib.proof_path(tmp_path, ROOT + "x") != path


def test_the_calendar_list_is_configurable():
    """At probe time only one of the defaults answered.

    A hard-coded single point of failure inside a witnessing layer is its own
    defect, so the list is a parameter and the default is a tuple of several.
    """
    assert len(witness_lib.DEFAULT_CALENDARS) >= 3
    assert all(url.startswith("https://") for url in witness_lib.DEFAULT_CALENDARS)


def test_no_calendar_reachable_is_unavailable_not_pending():
    """A stamp that reached nobody is not a pending stamp."""
    if not HAVE_OTS:
        pytest.skip("needs opentimestamps to reach the calendar loop")

    result = witness_lib.stamp_root(
        ROOT, calendars=("https://127.0.0.1:1/nope",), timeout=2
    )
    assert result["status"] == witness_lib.WITNESS_UNAVAILABLE
    assert result["proof"] is None
    assert result["attested"] == []
    assert len(result["failed"]) == 1
