"""Tests for Hashline-style deterministic edit verification."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.metacoordinator_mcp.hashline import (
    build_pre_write_checkpoint,
    render_verification_section,
    verify_tool_edit,
)


def test_verify_replace_reports_verified_when_new_lands_cleanly():
    """Replace verification should pass when only the new snippet remains."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.py"
        path.write_text("def answer():\n    return 43\n", encoding="utf-8")
        result = verify_tool_edit(
            str(path),
            "replace",
            {"old_string": "return 42", "new_string": "return 43"},
        )
        assert result["status"] == "VERIFIED"
        assert result["checks"][0]["matched_new"][0]["start_line"] == 2


def test_verify_replace_reports_unverified_when_old_and_new_both_exist():
    """Replace verification should stay ambiguous when both snippets remain."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.py"
        path.write_text(
            "def first():\n    return 42\n\ndef second():\n    return 43\n",
            encoding="utf-8",
        )
        result = verify_tool_edit(
            str(path),
            "replace",
            {"old_string": "return 42", "new_string": "return 43"},
        )
        assert result["status"] == "UNVERIFIED"


def test_verify_replace_reports_mismatch_when_new_is_absent():
    """Replace verification should fail when the new snippet never appears."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.py"
        path.write_text("def answer():\n    return 42\n", encoding="utf-8")
        result = verify_tool_edit(
            str(path),
            "replace",
            {"old_string": "return 42", "new_string": "return 43"},
        )
        assert result["status"] == "MISMATCH"


def test_verify_write_reports_exact_file_match():
    """Write verification should compare whole-file hashes exactly."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.py"
        content = "def answer():\n    return 42\n"
        path.write_text(content, encoding="utf-8")
        result = verify_tool_edit(
            str(path),
            "write_file",
            {"content": content},
        )
        assert result["status"] == "VERIFIED"
        assert (
            result["checks"][0]["expected_sha256"]
            == result["checks"][0]["actual_sha256"]
        )


def test_verify_multiedit_aggregates_subchecks():
    """Multiedit verification should summarize the status of each sub-edit."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.py"
        path.write_text(
            "def alpha():\n    return 10\n\ndef beta():\n    return 21\n",
            encoding="utf-8",
        )
        result = verify_tool_edit(
            str(path),
            "multiedit",
            {
                "edits": [
                    {"old_string": "return 10", "new_string": "return 10"},
                    {"old_string": "return 20", "new_string": "return 21"},
                ]
            },
        )
        assert result["status"] == "VERIFIED"
        assert "2/2 verified" in result["reason"]


def test_verify_replace_uses_exact_pre_write_checkpoint_when_post_image_matches():
    """Exact checkpoint post-images should override weaker replace heuristics."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.py"
        pre_text = "def answer():\n    return 42\n"
        post_text = "def answer():\n    return 43\n"
        path.write_text(post_text, encoding="utf-8")
        checkpoint = build_pre_write_checkpoint(
            str(path),
            "replace",
            {"old_string": "return 42", "new_string": "return 43"},
            pre_text=pre_text,
            source_exists=True,
        )
        result = verify_tool_edit(
            str(path),
            "replace",
            {"old_string": "return 42", "new_string": "return 43"},
            pre_checkpoint=checkpoint,
        )
        assert result["status"] == "VERIFIED"
        assert result["checkpoint"]["status"] == "MATCHED_EXACT_POST"


def test_verify_replace_reports_mismatch_when_exact_post_image_diverges():
    """Checkpoint divergence should promote an otherwise verified edit to mismatch."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.py"
        pre_text = "def answer():\n    return 42\n"
        path.write_text(
            "def answer():\n    return 43\n# intervening write\n", encoding="utf-8"
        )
        checkpoint = build_pre_write_checkpoint(
            str(path),
            "replace",
            {"old_string": "return 42", "new_string": "return 43"},
            pre_text=pre_text,
            source_exists=True,
        )
        result = verify_tool_edit(
            str(path),
            "replace",
            {"old_string": "return 42", "new_string": "return 43"},
            pre_checkpoint=checkpoint,
        )
        assert result["checks"][0]["status"] == "VERIFIED"
        assert result["status"] == "MISMATCH"
        assert result["checkpoint"]["status"] == "DIVERGED_FROM_EXACT_POST"


def test_render_verification_section_includes_hashlined_evidence():
    """Rendered reports should include the headline verification evidence blocks."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.py"
        path.write_text("def answer():\n    return 43\n", encoding="utf-8")
        result = verify_tool_edit(
            str(path),
            "replace",
            {"old_string": "return 42", "new_string": "return 43"},
        )
        rendered = render_verification_section(result)
        assert "VERIFICATION (Hashline spike):" in rendered
        assert "Expected new fingerprint:" in rendered
        assert "Matched new locations:" in rendered


def _run_all() -> int:
    """Run the lightweight standalone test bundle without pytest."""
    tests = [
        test_verify_replace_reports_verified_when_new_lands_cleanly,
        test_verify_replace_reports_unverified_when_old_and_new_both_exist,
        test_verify_replace_reports_mismatch_when_new_is_absent,
        test_verify_write_reports_exact_file_match,
        test_verify_multiedit_aggregates_subchecks,
        test_verify_replace_uses_exact_pre_write_checkpoint_when_post_image_matches,
        test_verify_replace_reports_mismatch_when_exact_post_image_diverges,
        test_render_verification_section_includes_hashlined_evidence,
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {test.__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(_run_all())
