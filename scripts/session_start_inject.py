"""Session-start hook: inject FLOSSI0ULLK startup contract as additional context.

Wired in `.claude/settings.json` under `hooks.SessionStart`. Emits JSON shaped per
the Claude Code hook contract so the contract content rides at session start
without re-deriving from canon every time.

The output is intentionally small — STARTUP_CONTRACT.md is ~3KB and pointers
into CONTEXT_L0.md keep the heavy briefing one Read away when actually needed.

Per-harness equivalents (Gemini hook, Codex AGENTS.md, OpenCode openwork prompt)
should reference the same `.agent-surface/STARTUP_CONTRACT.md` so the contract
content stays in one place.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path("C:/~shit")
CONTRACT = WORKSPACE_ROOT / ".agent-surface" / "STARTUP_CONTRACT.md"


def main() -> int:
    try:
        contract = CONTRACT.read_text(encoding="utf-8")
    except OSError as e:
        # Silent-fail to avoid blocking the session; the contract isn't load-bearing
        # for tool execution — it's orientation.
        print(json.dumps({"continue": True, "additionalContext": f"# FLOSSI0ULLK startup contract unavailable: {e}"}))
        return 0

    payload = {
        "continue": True,
        "additionalContext": contract,
    }
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
