"""Semantic validation for Yumeichan Watch capability grants."""

from __future__ import annotations

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


def validate_capability(capability: Mapping[str, Any]) -> None:
    """Validate a capability's declared shape and ordered analog bounds.

    JSON Schema enforces the token shape. This small semantic layer enforces
    the cross-item invariant that the lower threshold cannot exceed the upper.
    Cryptographic signature verification remains outside this validator.
    """
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=capability, schema=schema)

    minimum, maximum = capability["analog_threshold_bounds"]
    if not math.isfinite(minimum) or not math.isfinite(maximum):
        raise jsonschema.ValidationError(
            "analog_threshold_bounds values must be finite"
        )
    if minimum > maximum:
        raise jsonschema.ValidationError(
            "analog_threshold_bounds minimum must not exceed maximum"
        )
