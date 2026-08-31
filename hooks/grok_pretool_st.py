"""Grok PreToolUse: remind to use st, not grep.

Grok docs: PreToolUse additionalContext reaches the model after the call.
Matcher should be grep (Grok tool name; Grep aliases to it).
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    print(
        json.dumps(
            {
                "decision": "allow",
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": (
                        "Workspace rule: use st / smart-tree MCP "
                        "(smart-tree__search, st --search, st --mode ai), "
                        "not grep/ls/find. Durable memory is agentmemory "
                        "memory_save / recall, not .remember/remember.md."
                    ),
                },
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
