"""artifact_actions input `except json.JSONDecodeError` did not cover.

Two readers here. _run parses a child script's stdout and falls back to
`{"raw": ...}`; act_activity_tail parses the activity log line by line and
falls back to `{"unparsed": ...}` per line. An integer past CPython's 4300-digit
limit (a plain ValueError) was already caught by _run but not by the tail, and
nesting past the recursion limit (RecursionError) was caught by neither -- main()
then enveloped the whole action as an error. Invalid UTF-8 cannot reach either
json.loads: subprocess.run(text=True) and read_text(errors="replace") decode
first.

A child that prints JSON that is not an object is legitimate output
(context_router prints a list), so _run returns it unchanged. It only broke on
a non-zero exit, where _run adds `stderr` and `returncode` by key.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

FLOSS_ROOT = Path(__file__).resolve().parents[2]

_UNREADABLE = ['{"n": ' + "9" * 5000 + "}", "[" * 100_000 + "]" * 100_000]
_UNREADABLE_IDS = ["integer-past-the-digit-limit", "nesting-past-the-recursion-limit"]


def load_actions_module():
    spec = importlib.util.spec_from_file_location(
        "artifact_actions_under_test", FLOSS_ROOT / "scripts" / "artifact_actions.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["artifact_actions_under_test"] = module
    spec.loader.exec_module(module)
    return module


def _fake_run(stdout: str, returncode: int = 0):
    def run(cmd, **kwargs):
        return subprocess.CompletedProcess(
            cmd, returncode, stdout=stdout, stderr="boom"
        )

    return run


@pytest.mark.parametrize("stdout", _UNREADABLE, ids=_UNREADABLE_IDS)
def test_unreadable_child_output_is_kept_raw(monkeypatch, stdout):
    actions = load_actions_module()
    monkeypatch.setattr(actions.subprocess, "run", _fake_run(stdout))

    assert "raw" in actions._run(["child"])


@pytest.mark.parametrize(
    "stdout, parsed",
    [("[1, 2]", [1, 2]), ("null", None), ('"a string"', "a string")],
    ids=["list", "null", "string"],
)
def test_non_object_child_output_is_returned_unchanged(monkeypatch, stdout, parsed):
    """Guard: this is well-formed output, not a failure."""
    actions = load_actions_module()
    monkeypatch.setattr(actions.subprocess, "run", _fake_run(stdout))

    assert actions._run(["child"]) == parsed


@pytest.mark.parametrize(
    "stdout", ["[1, 2]", "null", '"a string"'], ids=["list", "null", "string"]
)
def test_a_failing_child_keeps_its_stderr_whatever_it_printed(monkeypatch, stdout):
    actions = load_actions_module()
    monkeypatch.setattr(actions.subprocess, "run", _fake_run(stdout, returncode=2))

    result = actions._run(["child"])

    assert result["returncode"] == 2
    assert result["stderr"] == "boom"


@pytest.mark.parametrize("line", _UNREADABLE, ids=_UNREADABLE_IDS)
def test_an_unreadable_activity_line_is_unparsed_not_fatal(tmp_path, monkeypatch, line):
    actions = load_actions_module()
    log = tmp_path / "activity.jsonl"
    log.write_text('{"ok": 1}\n' + line + "\n", encoding="utf-8")
    monkeypatch.setattr(actions, "ACTIVITY", log)

    records = actions.act_activity_tail("10")["records"]

    assert records[0] == {"ok": 1}
    assert "unparsed" in records[1]


@pytest.mark.parametrize(
    "separator", [" ", " ", "\x85"], ids=["U+2028", "U+2029", "U+0085"]
)
def test_a_row_with_a_unicode_line_separator_round_trips(
    tmp_path, monkeypatch, separator
):
    """activity_log.append_action writes with ensure_ascii=False, so these
    three reach the file raw. str.splitlines() breaks a row on them as well as
    on newline, which showed one row as two `unparsed` halves."""
    actions = load_actions_module()
    plain = {"action_id": "plain"}
    split_prone = {"action_id": "split-prone", "inputs": {"prompt": f"a{separator}b"}}
    log = tmp_path / "activity.jsonl"
    log.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in [plain, split_prone]),
        encoding="utf-8",
    )
    monkeypatch.setattr(actions, "ACTIVITY", log)

    tail = actions.act_activity_tail("10")

    assert tail["records"] == [plain, split_prone]
    assert tail["total_lines"] == 2


def test_the_final_newline_does_not_count_as_a_line(tmp_path, monkeypatch):
    """Guard: every row ends in a newline, and the one after the last row
    ends the file rather than starting an empty line."""
    actions = load_actions_module()
    log = tmp_path / "activity.jsonl"
    log.write_text('{"a": 1}\n{"b": 2}\n', encoding="utf-8")
    monkeypatch.setattr(actions, "ACTIVITY", log)

    assert actions.act_activity_tail("10") == {
        "total_lines": 2,
        "returned": 2,
        "records": [{"a": 1}, {"b": 2}],
    }


@pytest.mark.parametrize("returncode", [0, 2], ids=["success", "failure"])
def test_real_child_list_output_preserves_exit_details(returncode):
    """Exercise the actual subprocess text/exit boundary, not a fake runner."""
    actions = load_actions_module()
    child = (
        "import sys; print('[1, 2]'); "
        "print('child detail', file=sys.stderr); "
        f"sys.exit({returncode})"
    )

    result = actions._run([sys.executable, "-B", "-c", child], timeout=10)

    if returncode == 0:
        assert result == [1, 2]
    else:
        assert result == {
            "output": [1, 2],
            "stderr": "child detail",
            "returncode": 2,
        }


def test_actual_activity_writer_round_trips_unicode_text(tmp_path, monkeypatch):
    """The actual writer emits raw Unicode; the reader must retain one row."""
    spec = importlib.util.spec_from_file_location(
        "activity_writer_under_test", FLOSS_ROOT / "packages/activity_log/schema.py"
    )
    writer = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = writer
    assert spec.loader is not None
    spec.loader.exec_module(writer)
    log = tmp_path / "activity.jsonl"
    monkeypatch.setattr(writer, "ACTIVITY_LOG", log)
    actions = load_actions_module()
    monkeypatch.setattr(actions, "ACTIVITY", log)
    action = writer.Action(
        action_id="unicode-writer-reader",
        kind="test",
        harness="retained-C01-fixture",
        started_at="2026-10-23T00:00:00Z",
        ended_at="2026-10-23T00:00:00Z",
        duration_seconds=0,
        success=True,
        inputs={"text": "a\u2028b\u2029c\u0085d"},
        outputs={},
    )

    assert writer.append_action(action) is True
    assert b"\xe2\x80\xa8" in log.read_bytes()
    tail = actions.act_activity_tail("10")

    assert tail["total_lines"] == tail["returned"] == 1
    assert tail["records"][0]["action_id"] == "unicode-writer-reader"
    assert tail["records"][0]["inputs"] == {"text": "a\u2028b\u2029c\u0085d"}


def test_main_emits_one_success_envelope_with_unicode_record(tmp_path, monkeypatch, capsys):
    actions = load_actions_module()
    log = tmp_path / "activity.jsonl"
    log.write_text('{"text":"a\u2028b"}\n', encoding="utf-8")
    monkeypatch.setattr(actions, "ACTIVITY", log)
    monkeypatch.setattr(sys, "argv", ["artifact_actions.py", "activity_tail", "10"])

    assert actions.main() == 0
    captured = capsys.readouterr()
    envelope = json.loads(captured.out)

    assert captured.err == ""
    assert captured.out.count("\n") == 1
    assert envelope == {
        "ok": True,
        "action": "activity_tail",
        "data": {"total_lines": 1, "returned": 1, "records": [{"text": "a\u2028b"}]},
    }


def test_main_envelopes_a_real_reader_error(tmp_path, monkeypatch, capsys):
    actions = load_actions_module()
    monkeypatch.setattr(actions, "ACTIVITY", tmp_path)
    monkeypatch.setattr(sys, "argv", ["artifact_actions.py", "activity_tail", "10"])

    assert actions.main() == 1
    captured = capsys.readouterr()
    envelope = json.loads(captured.out)

    assert captured.err == ""
    assert captured.out.count("\n") == 1
    assert envelope["ok"] is False
    assert envelope["action"] == "activity_tail"
    assert isinstance(envelope["error"], str) and envelope["error"]
    assert "data" not in envelope


@pytest.mark.parametrize("action", ["not-allowed", "route"])
def test_actual_cli_rejects_invalid_requests_without_extra_output(action, tmp_path):
    """These inputs stop before any live router, model or activity-log read."""
    result = subprocess.run(
        [sys.executable, "-B", str(FLOSS_ROOT / "scripts/artifact_actions.py"), action],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    envelope = json.loads(result.stdout)

    assert result.returncode == 1
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    assert envelope["ok"] is False
    assert envelope["action"] == action
    assert isinstance(envelope["error"], str) and envelope["error"]
    assert "data" not in envelope
