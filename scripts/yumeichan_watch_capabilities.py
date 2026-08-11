"""Semantic validation for Yumeichan Watch capability grants."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
from typing import Any, Mapping

import jsonschema


SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "specs"
    / "yumeichan-watch-capabilities.schema.json"
)


def validate_capability(
    capability: Mapping[str, Any], *, now: datetime | None = None
) -> None:
    """Validate a capability's shape, analog bounds, and active lifetime.

    JSON Schema enforces the token shape. This small semantic layer enforces
    the ordered-threshold and time-bounded grant invariants. Cryptographic
    signature verification remains outside this validator.
    """
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(
        instance=capability,
        schema=schema,
        format_checker=jsonschema.FormatChecker(),
    )

    minimum, maximum = capability["analog_threshold_bounds"]
    if not math.isfinite(minimum) or not math.isfinite(maximum):
        raise jsonschema.ValidationError(
            "analog_threshold_bounds values must be finite"
        )
    if minimum > maximum:
        raise jsonschema.ValidationError(
            "analog_threshold_bounds minimum must not exceed maximum"
        )

    current_time = datetime.now(timezone.utc) if now is None else now
    if (
        not isinstance(current_time, datetime)
        or current_time.tzinfo is None
        or current_time.utcoffset() is None
    ):
        raise jsonschema.ValidationError("now must be timezone-aware")

    issued_at_text = capability["issued_at"]
    if issued_at_text.endswith("Z"):
        issued_at_text = f"{issued_at_text[:-1]}+00:00"
    try:
        issued_at = datetime.fromisoformat(issued_at_text)
    except (TypeError, ValueError) as exc:
        raise jsonschema.ValidationError(
            "issued_at must be a timezone-aware ISO 8601 instant"
        ) from exc
    if issued_at.tzinfo is None or issued_at.utcoffset() is None:
        raise jsonschema.ValidationError(
            "issued_at must be a timezone-aware ISO 8601 instant"
        )

    if issued_at > current_time:
        raise jsonschema.ValidationError("capability was issued in the future")

    try:
        expires_at = issued_at + timedelta(seconds=capability["ttl_seconds"])
    except OverflowError as exc:
        raise jsonschema.ValidationError(
            "capability expiration could not be computed"
        ) from exc
    if expires_at <= current_time:
        raise jsonschema.ValidationError("capability has expired")
