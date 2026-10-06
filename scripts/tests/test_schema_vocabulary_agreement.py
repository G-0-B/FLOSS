"""Cross-boundary drift guards for vocabularies that Python enforces.

D-A1 (ADR-20) collapsed the evidence-type vocabulary down to a single Python
authority, ``packages.orchestrator.claim_schema.EVIDENCE_TYPES``, after finding
that ``provenance.py`` carried a fourth restatement nobody knew existed. That
fix stopped at the language boundary. The same vocabulary is still written out
by hand in a JSON Schema and in a prose table, and nothing checked that those
agreed with the enforcing set -- which is precisely the shape of the bug D-A1
was created to remove, just relocated to a file Python never imports.

These tests close that. They are deliberately about *agreement*, not about the
contents of any list: a legitimate widening of the vocabulary should fail here
until every declaration has been updated together.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.orchestrator.claim_schema import (  # noqa: E402
    EVIDENCE_TYPES,
    BlastRadius,
)

SPECS = REPO_ROOT / "docs" / "specs"
PACKET_SCHEMA = SPECS / "provenance-packet.schema.json"
PACKET_SPEC = SPECS / "provenance-packet.spec.md"
CONSENT_SCHEMA = SPECS / "consent-payload.schema.json"


def _load(path: Path) -> dict:
    assert path.is_file(), f"{path} is missing; the drift guard has nothing to check"
    return json.loads(path.read_text(encoding="utf-8"))


def _find_enum(node: object, *, key: str) -> list[list[str]]:
    """Collect every ``enum`` declared on a property named ``key``."""

    found: list[list[str]] = []
    if isinstance(node, dict):
        for name, value in node.items():
            if (
                name == key
                and isinstance(value, dict)
                and isinstance(value.get("enum"), list)
            ):
                found.append([str(item) for item in value["enum"]])
            found.extend(_find_enum(value, key=key))
    elif isinstance(node, list):
        for item in node:
            found.extend(_find_enum(item, key=key))
    return found


def test_packet_schema_evidence_enum_matches_the_python_authority():
    enums = _find_enum(_load(PACKET_SCHEMA), key="type")
    evidence_enums = [
        values for values in enums if "provenance_packet" in values
    ]
    assert evidence_enums, (
        "provenance-packet.schema.json declares no evidence-type enum; either it "
        "was removed or its shape changed, and this guard is now blind"
    )
    for values in evidence_enums:
        assert set(values) == set(EVIDENCE_TYPES), (
            "provenance-packet.schema.json evidence enum disagrees with "
            "claim_schema.EVIDENCE_TYPES: "
            f"schema-only={sorted(set(values) - set(EVIDENCE_TYPES))}, "
            f"python-only={sorted(set(EVIDENCE_TYPES) - set(values))}"
        )
        assert len(values) == len(set(values)), (
            f"duplicate entries in the schema enum: {values}"
        )


def test_packet_spec_prose_lists_the_same_evidence_types():
    line = next(
        (
            text
            for text in PACKET_SPEC.read_text(encoding="utf-8").splitlines()
            if "`evidence_refs`" in text and "Types:" in text
        ),
        None,
    )
    assert line is not None, (
        "provenance-packet.spec.md no longer carries an `evidence_refs` row that "
        "names the types; update this guard rather than deleting it"
    )
    prose_types = set(re.findall(r"`([a-z_]+)`", line.split("Types:", 1)[1]))
    assert prose_types == set(EVIDENCE_TYPES), (
        "provenance-packet.spec.md prose disagrees with EVIDENCE_TYPES: "
        f"prose-only={sorted(prose_types - set(EVIDENCE_TYPES))}, "
        f"python-only={sorted(set(EVIDENCE_TYPES) - prose_types)}"
    )


def test_consent_schema_blast_radius_matches_the_python_enum():
    enums = _find_enum(_load(CONSENT_SCHEMA), key="blast_radius")
    assert enums, "consent-payload.schema.json declares no blast_radius enum"
    expected = {member.value for member in BlastRadius}
    for values in enums:
        assert set(values) == expected, (
            "consent-payload.schema.json blast_radius disagrees with "
            "claim_schema.BlastRadius: "
            f"schema-only={sorted(set(values) - expected)}, "
            f"python-only={sorted(expected - set(values))}"
        )
