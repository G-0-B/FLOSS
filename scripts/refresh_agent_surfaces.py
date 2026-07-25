"""Run every shared-surface materializer in dependency order.

One entry point for regenerating (or verifying) the whole FLOSSI0ULLK agent
surface: MCP registry, context pack, skills, agent memory, hooks, AI roster.

Each step is invoked as a subprocess because every materializer already
exposes the same CLI contract (`--check`, `--dry-run`, `--workspace-root`).
Subprocesses keep the steps independently runnable and stop one failure from
aborting the rest.

Usage:
    python scripts/refresh_agent_surfaces.py                      # regenerate, repo scope
    python scripts/refresh_agent_surfaces.py --check              # verify only, no writes
    python scripts/refresh_agent_surfaces.py --include-user-scope # + user-level configs
    python scripts/refresh_agent_surfaces.py --only skill         # a single step

Exit codes:
    0  every step succeeded with no drift
    1  at least one step failed or reported drift
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

# Only the agent-surface materializer understands user-scope targets.
USER_SCOPE_STEPS = {"agent-surface"}


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify without writing.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Report intended writes."
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
    failed = 0
    for name, code in outcomes:
        if code == 0:
            status = "ok"
        elif code == 1:
            status = "DRIFT" if args.check else "FAILED"
        else:
            status = f"FAILED (exit {code})"
        if code != 0:
            failed += 1
        print(f"{name:<14} {status}")

    if failed:
        print(f"\n{failed} of {len(outcomes)} step(s) need attention.")
        return 1
    print(f"\nAll {len(outcomes)} step(s) clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
