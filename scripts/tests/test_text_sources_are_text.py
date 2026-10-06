"""No tracked source or documentation file may contain a NUL byte.

A stray `0x00` in `docs/specs/provenance-packet.spec.md` -- written while
documenting CESR's mid-padding, where the example needed the TEXT `\x00` and
got the byte -- made `file(1)` classify the canonical provenance specification
as `data` rather than UTF-8 text. Tooling follows: ripgrep reports a binary
match instead of matching lines, and Markdown and indexing pipelines are
entitled to truncate or reject it. The spec became unsearchable by the very
tools an auditor would reach for.

Checked generically over every tracked text-suffixed file rather than pinned to
the one that broke, because the next one will be a different file.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".rs",
    ".ts",
    ".js",
    ".txt",
    ".cfg",
    ".ini",
    ".sh",
    ".ps1",
}


def _tracked_text_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    names = result.stdout.decode("utf-8", "replace").split("\0")
    return [
        REPO_ROOT / name
        for name in names
        if name and Path(name).suffix.lower() in TEXT_SUFFIXES
    ]


def test_no_tracked_text_file_contains_a_nul_byte():
    files = _tracked_text_files()
    assert files, "git ls-files returned nothing; this guard would pass vacuously"

    offenders = []
    for path in files:
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"\x00" in data:
            index = data.index(b"\x00")
            line = data[:index].count(b"\n") + 1
            offenders.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{line}")

    assert offenders == [], (
        "these text files contain a NUL byte and will be treated as binary by "
        "grep, ripgrep and Markdown tooling; write the escape as literal "
        f"backslash text instead: {offenders}"
    )
