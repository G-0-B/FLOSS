"""
Canonical serialization for FLOSSIØULLK source chain entries.

All source chain entries MUST be serialized via canonical_serialize() before
hashing. This ensures byte-identical SHA256 digests across Python, Rust, and
TypeScript implementations.

Cross-language invariants (any implementation MUST satisfy):
  1. Reject NaN and ±Inf — raise an error, never serialize them.
  2. Normalize -0.0 to 0.0 before serialization (IEEE 754 sign-bit collapse).
  3. Round floats to exactly 6 decimal places using round-half-to-even (banker's rounding).
  4. Emit raw UTF-8 strings — do NOT escape non-ASCII code points as \\uXXXX.
  5. Sort all object keys lexicographically (byte order of UTF-8 encoded key strings).
  6. No whitespace between tokens (separators=(',', ':')).

See: docs/superpowers/specs/2026-04-12-local-agent-node-design.md §3.3
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

FLOAT_PRECISION = 6


def normalize_float(x: float) -> float:
    """Normalize a float for canonical serialization.

    Rejects non-finite values (NaN, ±Inf), collapses -0.0 to 0.0 via IEEE 754
    positive-zero addition, then rounds to FLOAT_PRECISION decimal places.

    Raises:
        ValueError: if x is NaN, +Inf, or -Inf.
    """
    if not math.isfinite(x):
        raise ValueError(
            f"Non-finite float forbidden in source chain entries: {x!r}. "
            "Ensure vote weights are finite before submitting a Claim."
        )
    # (x + 0.0) collapses -0.0 to 0.0 at the IEEE 754 bit level.
    # Python's round() uses banker's rounding (round-half-to-even) by default,
    # matching IEEE 754. Rust implementors: use a round-half-to-even function,
    # not f64::round() which rounds half-away-from-zero.
    return round(x + 0.0, FLOAT_PRECISION)


def _normalize_val(obj: Any) -> Any:
    """Recursively normalize an object for canonical JSON serialization."""
    if isinstance(obj, float):
        return normalize_float(obj)
    if isinstance(obj, bool):
        # bool is a subclass of int in Python — check before int.
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return {k: _normalize_val(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_normalize_val(x) for x in obj]
    if obj is None:
        return obj
    raise TypeError(
        f"Unserializable type {type(obj).__name__!r} in source chain entry. "
        "Only str, int, float, bool, None, dict, and list are permitted."
    )


def canonical_serialize(data: dict) -> bytes:
    """Serialize a source chain entry to canonical UTF-8 bytes for hashing.

    The output is deterministic: same logical content always produces the same
    bytes, regardless of insertion order or float representation quirks.

    Args:
        data: The entry dict to serialize. Must contain only JSON-safe types.

    Returns:
        UTF-8 encoded canonical JSON bytes.

    Raises:
        ValueError: if any float in data is NaN or ±Inf.
        TypeError: if data contains a type that cannot be serialized.
    """
    return json.dumps(
        _normalize_val(data),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,  # raw UTF-8 — do NOT escape non-ASCII as \uXXXX
        allow_nan=False,  # belt-and-suspenders: normalize_float catches this first
    ).encode("utf-8")


def entry_hash(data: dict) -> str:
    """Return the SHA256 hex digest of a canonically serialized entry.

    This is the filename used in the source chain directory:
        cells/<dna_hash>/source_chain/<entry_hash>.json

    Args:
        data: The entry dict to hash.

    Returns:
        64-character lowercase hex string (SHA256 digest).
    """
    return hashlib.sha256(canonical_serialize(data)).hexdigest()
