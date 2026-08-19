from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill-corpus" / "flossi0ullk-orient" / "SKILL.md"
CHANGELOG = ROOT / "skill-corpus" / "flossi0ullk-orient" / "CHANGELOG.md"
EXPECTED_SHA256 = "491A2B37B9CF73A3FCDF7FCA5D9CEF0B0E81D8B62A10DA40238E0EF695B266EE"


def test_canonical_orient_skill_is_the_reviewed_v034_evidence_copy() -> None:
    skill_bytes = SKILL.read_bytes()
    skill_text = skill_bytes.decode("utf-8")

    assert hashlib.sha256(skill_bytes).hexdigest().upper() == EXPECTED_SHA256
    assert "version: 0.3.4" in skill_text

    for required_text in (
        "Mandatory response/output skeleton",
        "Fact: <observed artifact or output>",
        "documentation examples: <excluded list | none>",
        "Durable-write disposition",
        "OmniRoute attempt (repeat only for each actual request)",
        "successful independent families:",
        "CONFLICT — human resolution",
    ):
        assert required_text in skill_text


def test_orient_skill_changelog_records_each_tested_v03_evolution() -> None:
    changelog = CHANGELOG.read_text(encoding="utf-8")

    for version in ("0.3.0", "0.3.1", "0.3.2", "0.3.3", "0.3.4"):
        assert f"## {version}" in changelog
