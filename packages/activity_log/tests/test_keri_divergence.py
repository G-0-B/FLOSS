"""Pin the ways this envelope diverges from KERI/CESR.

These tests assert the DIVERGENCE, not conformance. That is deliberate.

The packet envelope borrows KERI's field names, its SAID dummy-character
algorithm, its version-string shape, and its code letters at CESR-correct
lengths. The resemblance is close enough that a reader can reasonably conclude
the packets are CESR primitives and can be handed to a KERI implementation.
They cannot. The most dangerous divergence (see spec section 9.3) does not make
a CESR decoder raise -- it makes it return a plausible, wrong 32 bytes.

So the divergence is written down here as executable fact. If someone later
makes the envelope genuinely CESR-correct, these tests fail. That failure is
the intended signal: a substrate-class migration has started, every SAID and
identifier in the existing chain has changed, and spec section 9 needs
rewriting rather than these assertions needing deleting.

Reference: docs/specs/provenance-packet.spec.md section 9.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.activity_log import provenance  # noqa: E402


def cesr_encode(raw: bytes, code: str) -> str:
    """Encode the way CESR actually specifies: pad bytes BEFORE conversion."""

    pad = (3 - (len(raw) % 3)) % 3
    encoded = base64.urlsafe_b64encode(bytes(pad) + raw).decode("ascii")
    return code + encoded[pad:]


def cesr_decode(value: str, code: str) -> bytes:
    """Inverse of cesr_encode, as a conforming outside reader would do it."""

    pad = len(code)
    restored = "A" * pad + value[len(code):]
    return base64.urlsafe_b64decode(restored.encode("ascii"))[pad:]


def test_the_envelope_post_pads_where_cesr_mid_pads():
    raw = bytes(range(32))
    here = "E" + provenance._b64url_encode(raw)
    there = cesr_encode(raw, "E")

    assert len(here) == len(there) == 44, (
        "both encodings are 44 characters; the length is not what differs"
    )
    assert here != there, (
        "the envelope now agrees with CESR mid-padding. If that was "
        "intentional, spec section 9.3 is obsolete and every SAID, identifier "
        "and signature in the existing chain has changed. Do not just delete "
        "this assertion."
    )


def test_a_cesr_reader_silently_recovers_wrong_bytes_from_our_encoding():
    """The failure mode is corruption, not rejection. That is why 9.3 exists."""

    raw = bytes(range(32))
    here = "E" + provenance._b64url_encode(raw)

    recovered = cesr_decode(here, "E")
    assert len(recovered) == len(raw), (
        "a CESR reader gets a full-length value back -- it has no signal that "
        "anything is wrong"
    )
    assert recovered != raw, "spec section 9.3 claims corruption; reproduce it"

    assert cesr_decode(cesr_encode(raw, "E"), "E") == raw, (
        "sanity: the reference encoder/decoder pair does round-trip, so the "
        "mismatch above is ours and not an artifact of this test"
    )


def test_our_own_decoder_round_trips_so_nothing_in_repo_is_corrupted_today():
    """Internal consistency is intact; only cross-implementation reads break."""

    for size in (32, 64):
        raw = bytes(range(size))
        assert provenance._b64url_decode(provenance._b64url_encode(raw)) == raw


def test_signature_code_diverges_the_same_way():
    raw = bytes(range(64))
    here = "0B" + provenance._b64url_encode(raw)
    there = cesr_encode(raw, "0B")

    assert len(here) == len(there) == 88
    assert here != there


def test_jcs_puts_the_version_string_where_no_keri_parser_will_look():
    packet = {
        "v": provenance.VERSION_PLACEHOLDER,
        "t": "prov",
        "d": provenance.SAID_PLACEHOLDER,
        "i": "D" + "A" * 43,
        "s": "0",
        "p": None,
        "a": [],
        "sigs": [],
    }
    on_wire = json.loads(provenance.canonical_bytes(packet).decode("utf-8"))

    assert list(on_wire) == ["a", "d", "i", "p", "s", "sigs", "t", "v"], (
        "JCS sorts keys; KERI needs v, t, d at the head of the frame"
    )
    assert list(on_wire)[0] != "v", (
        "if v is first again, the envelope may have stopped using JCS -- which "
        "changes canonicalization and therefore every SAID"
    )


def test_version_string_is_not_keri_length():
    packet = {"v": provenance.VERSION_PLACEHOLDER, "t": "prov"}
    version = provenance._version_with_size(packet)

    assert version.startswith(provenance.VERSION_PREFIX)
    assert version.endswith("_")
    assert len(version) == 19, (
        "FLOSSI10JSON + 6 hex + _ = 19; KERI's KERIvvSSSShhhhhh_ is 17, so a "
        "fixed-span version read misparses (spec section 9.5)"
    )
    assert len(version) != 17
