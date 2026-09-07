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


def test_caller_classifies_before_it_can_stage():
    """main() must classify the result *before* calling stage_draft.

    This asserted on the name DEFERRED_PREFIX appearing in main(). That name
    moved into the shared pending_marker()/record_pending() helpers when the
    first-attempt and retry sites were unified, so the guard broke on a
    refactor that did not change the invariant at all -- the fourth
    source-splitting guard in this session to need repointing. Anchored on the
    call that does the classifying now, which is the thing that must not move
    below staging.
    """
    module = load_module()
    source = inspect.getsource(module.main)

    assert "pending_marker(" in source, "main() no longer classifies results"
    assert source.index("pending_marker(") < source.index("stage_draft(file_path"), (
        "classification must precede staging, or deferred and unreadable files "
        "get recorded as completed distillations again"
    )
    # Both sites, not one: the retry used to carry its own narrower check.
    #
    # Counted over CODE lines only. The first version of this assertion counted
    # every occurrence in the source and got 3, because a comment in main()
    # names the function -- matching prose instead of code, in the test written
    # to replace a test that had matched prose instead of code.
    calls = [
        line
        for line in source.splitlines()
        if "pending_marker(" in line and not line.strip().startswith("#")
    ]
    assert len(calls) == 2, (
        "the first attempt and the rate-limit retry must both classify, and "
        f"through the same predicate; found {len(calls)}: {calls}"
    )


def test_main_actually_runs_the_deferral_branch_without_crashing(
    tmp_path, capsys, monkeypatch
):
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

    assert (
        "not force_full" in source
    ), "the chunk-cap guard must honour force_full, or the flag does nothing"


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

    assert calls == [
        True,
        True,
    ], f"force_full must be threaded through the retry; got {calls}"
    out = capsys.readouterr().out
    assert "DEFERRED" in out
    assert doc.name in out


def test_deferred_files_do_not_consume_the_batch_limit():
    """`pending_files[:limit]` fixed the batch before knowing which files the
    extractor would decline. One oversized file with --limit 1 filled the
    batch, deferred, stayed pending, and the next invocation selected the
    identical prefix -- starving every normal-sized file after it forever."""
    source = (
        Path(__file__).resolve().parents[2] / "scripts" / "autonomous_synthesis_loop.py"
    ).read_text(encoding="utf-8")

    assert (
        "pending_files[:args.limit]" not in source
    ), "the batch is still a fixed prefix; deferrals starve the rest"
    body = source.split("for file_path in to_process:", 1)[1]
    assert "attempted += 1" in body
    assert "completed += 1" in body
    assert "if completed >= args.limit or attempted >= attempt_cap:" in body


def test_the_scan_past_deferrals_is_bounded():
    """A deferral costs an LLM call, so a store full of oversized files must not
    turn a --limit 1 run into a sweep of everything pending."""
    source = (
        Path(__file__).resolve().parents[2] / "scripts" / "autonomous_synthesis_loop.py"
    ).read_text(encoding="utf-8")

    assert "DEFER_SCAN_FACTOR" in source, "the scan is unbounded"
    assert "attempt_cap = max(args.limit, args.limit * DEFER_SCAN_FACTOR)" in source


def test_an_exhausted_scan_says_so():
    """Silence here would read as 'the limit was met'."""
    source = (
        Path(__file__).resolve().parents[2] / "scripts" / "autonomous_synthesis_loop.py"
    ).read_text(encoding="utf-8")

    assert "too many consecutive deferrals" in source


def test_a_dry_run_previews_no_more_files_than_the_limit(tmp_path, capsys, monkeypatch):
    """--dry-run --limit 1 previewed DEFER_SCAN_FACTOR files, not one.

    The dry-run branch continued without touching `completed`, so the only
    thing that ended the loop was the deferral scan cap -- which exists to let
    a run walk PAST declined files, not to multiply the batch. The banner said
    "up to 1" while five previews scrolled by. A dry run's whole job is to show
    what the real run would do.
    """
    module = load_module()

    docs = []
    for index in range(module.DEFER_SCAN_FACTOR + 2):
        doc = tmp_path / f"doc{index}.md"
        doc.write_text("# doc\n", encoding="utf-8")
        docs.append(doc)

    monkeypatch.setattr(module, "_get_files_to_process", lambda *a, **k: list(docs))
    monkeypatch.setattr(module, "_get_processed_files", lambda *a, **k: set())

    def _no_llm(*a, **k):
        raise AssertionError("a dry run must not call the extractor")

    monkeypatch.setattr(module, "extract_semantics", _no_llm)
    monkeypatch.setattr(
        sys,
        "argv",
        ["autonomous_synthesis_loop.py", "--dry-run", "--limit", "1"],
    )

    assert module.main() == 0

    out = capsys.readouterr().out
    assert out.count("[DRY RUN]") == 1, (
        "a dry run previewed more files than --limit allows; the preview is "
        f"the unit of work, so it consumes the limit (saw {out.count('[DRY RUN]')})"
    )


def test_a_dry_run_under_a_larger_limit_still_previews_up_to_it(
    tmp_path, capsys, monkeypatch
):
    """The cap is the limit, not one: counting previews must not clamp them.

    Written behaviourally on purpose. The first version of this test read the
    dry-run branch's source and split it on "continue" -- which matched the
    word inside the comment above the fix, so it failed against the fixed code
    and would have passed against prose that said anything at all.
    """
    module = load_module()

    docs = []
    for index in range(7):
        doc = tmp_path / f"doc{index}.md"
        doc.write_text("# doc" + chr(10), encoding="utf-8")
        docs.append(doc)

    monkeypatch.setattr(module, "_get_files_to_process", lambda *a, **k: list(docs))
    monkeypatch.setattr(module, "_get_processed_files", lambda *a, **k: set())
    monkeypatch.setattr(
        sys,
        "argv",
        ["autonomous_synthesis_loop.py", "--dry-run", "--limit", "3"],
    )

    assert module.main() == 0

    assert capsys.readouterr().out.count("[DRY RUN]") == 3


def test_an_unreadable_file_is_never_staged(tmp_path, capsys, monkeypatch):
    """A read failure returned a plain "Error reading file: ..." string, which
    contains neither DEFERRED_PREFIX nor "LLM Extraction Failed", so both of
    the caller's guards missed it and stage_draft() recorded the I/O error as
    the file's extracted semantics. A later --commit then wrote a completed
    knowledge_distillation whose entire content was that error, and the file
    was thereafter treated as processed with nothing extracted from it.
    """
    module = load_module()

    doc = tmp_path / "broken.md"
    doc.write_bytes(b"\xff\xfe not utf-8 \xff")

    monkeypatch.setattr(module, "_get_files_to_process", lambda *a, **k: [doc])
    monkeypatch.setattr(module, "_get_processed_files", lambda *a, **k: set())

    def _fail_if_staged(*a, **k):
        raise AssertionError("an unreadable file must never be staged")

    monkeypatch.setattr(module, "stage_draft", _fail_if_staged)
    monkeypatch.setattr(sys, "argv", ["autonomous_synthesis_loop.py", "--limit", "1"])

    assert module.main() == 0

    out = capsys.readouterr().out
    assert "COULD NOT BE READ" in out
    assert doc.name in out


def test_the_unreadable_marker_is_distinct_from_the_deferral_marker(tmp_path):
    """A deferral says 're-run with --force-full'; an unreadable file says
    'check encoding and permissions'. Sending an operator to the wrong fix is
    the reason these are two markers and not one."""
    module = load_module()

    doc = tmp_path / "broken.md"
    doc.write_bytes(b"\xff\xfe\x00")

    result = module.extract_semantics(doc, "groq/irrelevant")

    assert result.startswith(module.UNREADABLE_PREFIX)
    assert not result.startswith(module.DEFERRED_PREFIX)
    assert "LLM Extraction Failed" not in result
