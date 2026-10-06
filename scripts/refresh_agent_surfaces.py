"""Run every shared-surface materializer in dependency order.

One entry point for regenerating (or verifying) the whole FLOSSI0ULLK agent
surface: MCP registry, context pack, skills, agent memory, hooks, AI roster.

Each step is invoked as a subprocess because every materializer already
exposes the same CLI contract (`--check`, `--dry-run`). This runner itself
does not accept `--workspace-root` or forward one — each materializer keeps
its own default. Subprocesses keep the steps independently runnable and stop
one failure from aborting the rest.

If both `--check` and `--dry-run` are given, `--check` takes precedence:
output uses the CHECK OK/DRIFT wording (not PLAN), and the summary reflects
drift/exit status, not "planned".

Usage:
    python scripts/refresh_agent_surfaces.py                      # regenerate, repo scope
    python scripts/refresh_agent_surfaces.py --check              # verify only, no writes
    python scripts/refresh_agent_surfaces.py --dry-run            # report intended writes, no writes
    python scripts/refresh_agent_surfaces.py --include-user-scope # + user-level configs
    python scripts/refresh_agent_surfaces.py --only skill         # a single step

Exit codes:
    0  every step succeeded with no drift (or, under --dry-run alone, every
       step reported its plan without error)
    1  at least one step failed or reported drift

Caveat: every materializer exits 1 both for "`--check` found drift" AND for
an unhandled step error (missing manifest, bad JSON, etc — Python's default
exception handler also exits 1). This runner cannot tell those apart from
the exit code alone, so under `--check` a step showing exit 1 is labelled
"DRIFT (or step error — see output above)" — check that step's own output
above the summary to know which one it was.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

# Order matters: agent-surface owns the MCP registry and the context pack that
# later steps reference.
STEPS: list[tuple[str, str]] = [
    ("agent-surface", "materialize_shared_agent_surface.py"),
    ("context", "materialize_shared_context_surface.py"),
    ("skill", "materialize_shared_skill_surface.py"),
    ("agent-memory", "materialize_shared_agent_memory.py"),
    ("hook", "materialize_shared_hook_surface.py"),
    ("ai-roster", "materialize_shared_ai_roster.py"),
]

# Materializers that understand `--include-user-scope`. The hook materializer
# grew the flag and two user-scope targets (`claude_user`, `hermes_user`) after
# this set was written, and nothing tied the two together: running the supported
# `--only hook --include-user-scope` silently dropped the flag, skipped both
# targets, and still exited 0 -- an operator asking for a user-scope refresh got
# a clean report and no refresh. The skill materializer joined them when its own
# scope gate landed (`~/.codex/skills`, the Hermes skills directory).
#
# test_refresh_runner_forwards_user_scope.py derives this same set from the
# materializer sources, so the next script to grow the flag fails a test instead
# of silently doing nothing.
USER_SCOPE_STEPS = {"agent-surface", "hook", "skill"}


def build_command(
    step_name: str,
    script: str,
    check: bool,
    dry_run: bool,
    include_user_scope: bool,
) -> list[str]:
    command = [sys.executable, str(SCRIPTS_DIR / script)]
    if check:
        command.append("--check")
    if dry_run:
        command.append("--dry-run")
    if include_user_scope and step_name in USER_SCOPE_STEPS:
        command.append("--include-user-scope")
    return command


def summarize(
    outcomes: list[tuple[str, int]], *, check: bool, dry_run: bool
) -> tuple[list[str], int]:
    """Render summary lines and compute the exit code from step outcomes.

    `check` takes precedence over `dry_run` when both are set (see module
    docstring): a clean run is reported as "ok"/"clean", not "planned", once
    `check` is in play.
    """
    dry_run_only = dry_run and not check

    lines: list[str] = []
    failed = 0
    for name, code in outcomes:
        if code == 0:
            status = "planned" if dry_run_only else "ok"
        elif code == 1:
            if check:
                status = "DRIFT (or step error — see output above)"
            else:
                status = "FAILED"
        else:
            status = f"FAILED (exit {code})"
        if code != 0:
            failed += 1
        lines.append(f"{name:<14} {status}")

    lines.append("")
    if failed:
        lines.append(f"{failed} of {len(outcomes)} step(s) need attention.")
        exit_code = 1
    elif dry_run_only:
        lines.append(
            f"{len(outcomes)} step(s) planned (dry-run only — pass --check to detect drift)."
        )
        exit_code = 0
    else:
        lines.append(f"All {len(outcomes)} step(s) clean.")
        exit_code = 0

    return lines, exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify without writing.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report intended writes. Ignored (in favor of CHECK wording) if --check is also given.",
    )
    parser.add_argument(
        "--include-user-scope",
        action="store_true",
        help="Also write user-level configs outside the workspace.",
    )
    parser.add_argument("--only", help="Run a single step by name.")
    parser.add_argument("--list", action="store_true", help="List step names and exit.")
    args = parser.parse_args()

    if args.list:
        for name, script in STEPS:
            print(f"{name:<14} {script}")
        return 0

    steps = STEPS
    if args.only:
        steps = [item for item in STEPS if item[0] == args.only]
        if not steps:
            known = ", ".join(name for name, _ in STEPS)
            parser.error(f"unknown step {args.only!r}; expected one of: {known}")

    outcomes: list[tuple[str, int]] = []
    for name, script in steps:
        command = build_command(
            name, script, args.check, args.dry_run, args.include_user_scope
        )
        print(f"\n=== {name} ===", flush=True)
        completed = subprocess.run(command, check=False)
        outcomes.append((name, completed.returncode))

    print("\n=== summary ===")
    lines, exit_code = summarize(outcomes, check=args.check, dry_run=args.dry_run)
    for line in lines:
        print(line)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
