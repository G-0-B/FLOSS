#!/usr/bin/env python3
"""Advisory `cargo clippy` gate on Rust changes, fired at end of turn.

WHY THIS EXISTS
---------------
On 2026-09-07 a `workflow_dispatch` on `rust-ci.yml` ran `cargo clippy` against
this repository's Rust for the first time. It failed on two lints that had been
sitting in the integrity zome for months. Nothing had caught them:

  * the CI clippy job is gated `if: github.event_name == 'workflow_dispatch'`,
    so no push, PR or cron ever reached it;
  * `FLOSS/CLAUDE.md` documents `cargo fmt && cargo clippy` but nothing runs it;
  * no pre-commit config exists, and the other hooks in this directory do
    provenance, not linting.

Reproducing locally took one command and about a minute -- and surfaced FIVE
errors where CI had reported two, because CI stops at the first failing crate.
Iterating through CI instead would have cost an hour per round to learn them one
crate at a time. That asymmetry is the whole argument for this hook.

WHY `Stop` AND NOT `PostToolUse`
--------------------------------
`cargo clippy -p rose_forest_integrity` measured 11.55s warm; the full workspace
is far longer. Per-edit that is prohibitive, and the hook surface manifest's own
rule says to prefer non-blocking observability over prompt-time token burn.
Clippy's value is before a commit, not after a keystroke. `Stop` fires once per
turn, and this hook returns in milliseconds when no Rust changed -- the git
check runs before cargo is even considered.

ADVISORY, ALWAYS
----------------
This hook never blocks and always exits 0. A lint result is information for the
next decision, not a veto over work already done. It reports through the shared
hook log and, with `--stdout-json`, as `additionalContext`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
LOG_FILE = AGENT_DIR / "hook.log"
EMIT_STDOUT_JSON = "--stdout-json" in sys.argv[1:]

# Matches the CI invocation in .github/workflows/rust-ci.yml exactly. If they
# drift, the hook stops predicting CI and becomes noise -- change both together.
#
# `--force-warn dead_code`, not `-W dead_code`: `-D warnings` denies at group
# level and beats a later lint-level `-W`, so `-W` leaves dead code failing.
# Measured both ways 2026-09-07.
CLIPPY_ARGS = [
    "--all-targets",
    "--all-features",
    "--",
    "-D",
    "warnings",
    "--force-warn",
    "dead_code",
]

# The two Cargo workspaces, in the order a developer would care about. ARF is
# the guest/WASM workspace; ARF/tests/sweettest is a standalone child that links
# the Holochain conductor as a library and is deliberately NOT a member of ARF
# (that separation keeps conductor deps out of the guest lock).
WORKSPACES = (
    ("ARF", REPO_ROOT / "ARF" / "Cargo.toml"),
    ("ARF/tests/sweettest", REPO_ROOT / "ARF" / "tests" / "sweettest" / "Cargo.toml"),
)

# A Stop hook that hangs is worse than one that never runs: it stalls the turn
# with no output and no way to tell whether it is working. A cold clippy on the
# sweettest crate pulls the whole Holochain tree and can exceed any bound worth
# waiting for at end of turn, so cap it and report the cap honestly rather than
# pretending a timeout is a pass.
TIMEOUT_SECONDS = int(os.environ.get("FLOSS_RUST_LINT_TIMEOUT", "180"))


def log(message: str) -> None:
    try:
        AGENT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(f"[{stamp}] {message}\n")
    except OSError:
        # Logging must never be the reason a hook fails. The turn matters more
        # than the record of it.
        pass


def changed_rust_files() -> list[str]:
    """Rust files changed against HEAD, including untracked ones.

    Untracked files are included deliberately: a brand-new .rs file is exactly
    the case where nobody has run clippy on it yet.
    """
    files: set[str] = set()
    for args in (
        ["git", "diff", "--name-only", "HEAD", "--", "*.rs"],
        ["git", "ls-files", "--others", "--exclude-standard", "--", "*.rs"],
    ):
        try:
            out = subprocess.run(
                args,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return []
        if out.returncode == 0:
            files.update(
                line.strip() for line in out.stdout.splitlines() if line.strip()
            )
    return sorted(files)


def workspaces_for(files: list[str]) -> list[tuple[str, Path]]:
    """Only lint a workspace that actually has a changed file under it.

    Checked most-specific first, because ARF/tests/sweettest sits inside ARF on
    disk while being a separate workspace; a plain prefix test in declaration
    order would attribute every sweettest change to ARF and lint the wrong tree.

    A nested workspace claims its files even when its manifest is ABSENT, and
    this is the subtle half. ARF/tests/sweettest exists only on the Sweettest
    branch, so on most checkouts that manifest is missing -- and an earlier
    version of this function skipped absent workspaces before consuming their
    prefix, which let every sweettest change fall through to ARF. The hook then
    linted the guest workspace over a change that was not in it: not a false
    positive, a report about the wrong tree. Caught by the attribution test
    below, not by reading. Claim the prefix first; only lint if the manifest is
    really there.
    """
    selected: list[tuple[str, Path]] = []
    for name, manifest in sorted(WORKSPACES, key=lambda item: -len(item[0])):
        prefix = f"{name}/"
        claimed = [path for path in files if path.startswith(prefix)]
        if not claimed:
            continue
        files = [path for path in files if not path.startswith(prefix)]
        if manifest.is_file():
            selected.append((name, manifest))
    return selected


def run_clippy(name: str, manifest: Path) -> tuple[str, str]:
    """Return (status, detail). Status is one of ok | findings | skipped."""
    cmd = ["cargo", "clippy", "--manifest-path", str(manifest), *CLIPPY_ARGS]
    try:
        out = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        return "skipped", "cargo not on PATH"
    except subprocess.TimeoutExpired:
        return "skipped", (
            f"exceeded {TIMEOUT_SECONDS}s (cold build?) -- run it yourself: "
            f"cargo clippy --manifest-path {manifest} " + " ".join(CLIPPY_ARGS)
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return "skipped", f"{type(exc).__name__}: {exc}"

    if out.returncode == 0:
        warnings = [
            line for line in out.stderr.splitlines() if line.startswith("warning:")
        ]
        return "ok", f"{len(warnings)} warning(s)" if warnings else "clean"

    # Report the first few diagnostics rather than the whole stderr. The full
    # output belongs in a terminal the reader controls, not in a hook log.
    errors = [line for line in out.stderr.splitlines() if line.startswith("error")]
    head = "; ".join(errors[:4]) or f"exit {out.returncode}"
    if len(errors) > 4:
        head += f"; +{len(errors) - 4} more"
    return "findings", head


def main() -> int:
    try:
        sys.stdin.read()
    except (OSError, ValueError):
        pass

    files = changed_rust_files()
    if not files:
        return 0

    selected = workspaces_for(files)
    if not selected:
        log(f"[rust-lint] {len(files)} changed .rs file(s) under no known workspace")
        return 0

    lines: list[str] = []
    for name, manifest in selected:
        status, detail = run_clippy(name, manifest)
        log(f"[rust-lint] {status} {name}: {detail}")
        if status != "ok":
            lines.append(f"{name}: {status} -- {detail}")

    if lines and EMIT_STDOUT_JSON:
        body = "cargo clippy (advisory, matches CI): " + " | ".join(lines)
        print(json.dumps({"hookSpecificOutput": {"additionalContext": body}}))

    # Always 0. See the module docstring: advisory, never a veto.
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        # A lint advisory must not be able to take down a turn.
        log(f"[rust-lint] hook error: {type(exc).__name__}: {exc}")
        sys.exit(0)
