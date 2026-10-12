from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill-corpus" / "flossi0ullk-orient" / "SKILL.md"
CHANGELOG = ROOT / "skill-corpus" / "flossi0ullk-orient" / "CHANGELOG.md"
# Pin on the reviewed evidence copy of the orient skill. It exists so the skill
# cannot drift silently -- an edit here has to be a deliberate act with a new pin,
# not a side effect of some sweep passing through.
#
# Re-pinned 2026-08-21. The previous value (491A2B37...) was the copy promoted in
# 5de8bb0 "feat: promote orient skill v0.3.4". e648c7a "docs: rename the canonical
# kernel to match its version (v1.3.1 -> v1.4.0)" then swept two lines of this file
# without updating the pin, so the contract has been red ever since. The diff is
# exactly those two kernel-filename references and nothing else; every content
# assertion below still passes, and FLOSSI0ULLK_Master_Metaprompt_v1_4_0_Kernel.md
# is the file that actually exists. The rename was right; the pin was stale.
#
# Re-pinned 2026-10-12 for v0.3.5 (previous value 363D9523...). v0.3.5 is the
# weekly skill-review change set: Step 0 resolves the main checkout from a root-repo
# worktree, Step 0.5 plan intake, one commit line per repository in the envelope.
# It is NOT yet a reviewed evidence copy: the pin records this branch's content so
# the next change is deliberate, and review of the diff is still owed.
#
# To re-pin deliberately:
#   python -c "import hashlib,pathlib;print(hashlib.sha256(pathlib.Path(
#     'skill-corpus/flossi0ullk-orient/SKILL.md').read_bytes()).hexdigest().upper())"
EXPECTED_SHA256 = "B8E2F2DFEF90C7E777E2B8700FB5267437EAEF9458F72EFF4EC91A3CD1D9A221"


def test_canonical_orient_skill_is_the_pinned_v035_copy() -> None:
    skill_bytes = SKILL.read_bytes()
    skill_text = skill_bytes.decode("utf-8")

    assert hashlib.sha256(skill_bytes).hexdigest().upper() == EXPECTED_SHA256
    assert "version: 0.3.5" in skill_text

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

    for version in ("0.3.0", "0.3.1", "0.3.2", "0.3.3", "0.3.4", "0.3.5"):
        assert f"## {version}" in changelog
