"""Tests for deferral handling in scripts/autonomous_synthesis_loop.py.

Regression cover for a silent data-loss path found on PR41: a file over the
chunk cap returned a plain ``"SKIPPED: ..."`` string, the caller's only guard
checked for ``"LLM Extraction Failed"``, so the skip message fell through and
was staged as though it were extraction output. Staging excluded the file from
later pending runs, and ``--commit`` then recorded it as a completed
``knowledge_distillation`` -- permanently marking large files processed with
nothing extracted from them.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "autonomous_synthesis_loop.py"


def load_module():
    """Load the loop module by path; it is a script, not an importable package."""
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    spec = importlib.util.spec_from_file_location("autonomous_synthesis_loop", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_oversized_file_is_deferred_not_extracted(tmp_path):
    """A file over the cap returns the deferral sentinel and makes no LLM call."""
    module = load_module()

    oversized = tmp_path / "big.md"
    oversized.write_text("word " * 200_000, encoding="utf-8")

    result = module.extract_semantics(oversized, "groq/irrelevant")

    assert result.startswith(module.DEFERRED_PREFIX)
    assert str(module.MAX_CHUNKS_PER_FILE) in result


def test_deferral_is_not_mistaken_for_an_llm_failure(tmp_path):
    """The deferral must not rely on the caller's LLM-error guard.

    This is the exact hole: the caller checked only for "LLM Extraction Failed",
    which a skip message never contained, so the skip fell through to staging.
    """
    module = load_module()

    oversized = tmp_path / "big.md"
    oversized.write_text("word " * 200_000, encoding="utf-8")

    result = module.extract_semantics(oversized, "groq/irrelevant")

    assert "LLM Extraction Failed" not in result
    assert result.startswith(module.DEFERRED_PREFIX)


def test_caller_skips_staging_before_it_can_stage_a_deferral():
    """main() must test for the deferral sentinel *before* calling stage_draft."""
    module = load_module()
    source = inspect.getsource(module.main)

    assert "DEFERRED_PREFIX" in source, "main() no longer checks for deferrals"
    assert source.index("DEFERRED_PREFIX") < source.index("stage_draft(file_path"), (
        "deferral check must precede staging, or deferred files get recorded as "
        "completed distillations again"
    )


def test_main_actually_runs_the_deferral_branch_without_crashing(tmp_path, capsys, monkeypatch):
    """Execute the deferral path in main() rather than reading its source.

    The source-text assertion above passed while main() was in fact broken:
    the deferral branch appended to a name that was never defined, so every
    deferral raised NameError and aborted the run -- the exact opposite of
    leaving the file pending. Ruff caught it as F821; the test suite did not,
    because no test ever executed that branch. This one does.
    """
    module = load_module()

    doc = tmp_path / "oversized.md"
    doc.write_text("# oversized\n", encoding="utf-8")

    monkeypatch.setattr(module, "_get_files_to_process", lambda *a, **k: [doc])
    monkeypatch.setattr(module, "_get_processed_files", lambda *a, **k: set())
    monkeypatch.setattr(
        module,
        "extract_semantics",
        lambda *a, **k: f"{module.DEFERRED_PREFIX}over the chunk cap",
    )

    def _fail_if_staged(*a, **k):
        raise AssertionError("a deferred file must never be staged")

    monkeypatch.setattr(module, "stage_draft", _fail_if_staged)
    monkeypatch.setattr(module.time, "sleep", lambda *_: None)
    monkeypatch.setattr(sys, "argv", ["autonomous_synthesis_loop.py", "--limit", "1"])

    assert module.main() == 0

    out = capsys.readouterr().out
    assert "DEFERRED" in out
    assert doc.name in out, "the deferred file must be named in the summary"


def test_force_full_flag_exists():
    """The deferral message advertises --force-full; it must actually exist.

    The original message told operators to "use --force-full" while no such flag
    was ever defined, so the documented escape hatch silently did not exist.
    """
    module = load_module()
    source = inspect.getsource(module.main)

    assert "--force-full" in source
    assert "force_full" in inspect.signature(module.extract_semantics).parameters


def test_force_full_bypasses_the_cap_check(tmp_path):
    """With force_full set, the cap must not short-circuit into a deferral.

    Asserted by reading the guard rather than by running extraction: a real run
    would fan out to hundreds of live model calls with rate-limit sleeps.
    """
    module = load_module()
    source = inspect.getsource(module.extract_semantics)

    assert "not force_full" in source, (
        "the chunk-cap guard must honour force_full, or the flag does nothing"
    )


def test_rate_limit_retry_still_defers_an_oversized_file(tmp_path, capsys, monkeypatch):
    """The deferral path must survive the rate-limit retry.

    The first attempt returns a rate-limit failure; the retry returns the
    deferral sentinel. Before this was fixed the retry dropped `force_full`,
    got DEFERRED:: back, and -- because that string is not "LLM Extraction
    Failed" -- fell through to stage_draft(). A later --commit then recorded the
    oversized file as a completed distillation with nothing extracted.
    """
    module = load_module()

    doc = tmp_path / "oversized.md"
    doc.write_text("# oversized" + chr(92) + "n", encoding="utf-8")

    calls = []

    def flaky(path, model, force_full=False):
        calls.append(force_full)
        if len(calls) == 1:
            return "LLM Extraction Failed for chunk 1: RateLimitError"
        return f"{module.DEFERRED_PREFIX}over the chunk cap"

    monkeypatch.setattr(module, "_get_files_to_process", lambda *a, **k: [doc])
    monkeypatch.setattr(module, "_get_processed_files", lambda *a, **k: set())
    monkeypatch.setattr(module, "extract_semantics", flaky)

    def _fail_if_staged(*a, **k):
        raise AssertionError(
            "a file deferred on retry must never be staged -- that is the "
            "silent data loss this whole path exists to prevent"
        )

    monkeypatch.setattr(module, "stage_draft", _fail_if_staged)
    monkeypatch.setattr(module.time, "sleep", lambda *_: None)
    monkeypatch.setattr(
        sys, "argv", ["autonomous_synthesis_loop.py", "--limit", "1", "--force-full"]
    )

    assert module.main() == 0

    assert calls == [True, True], (
        f"force_full must be threaded through the retry; got {calls}"
    )
    out = capsys.readouterr().out
    assert "DEFERRED" in out
    assert doc.name in out
