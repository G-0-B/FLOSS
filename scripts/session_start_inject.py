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

# Hard cap on the memory-recall detour so a slow/unavailable agentmemory can
# never push session start meaningfully past its normal latency. Measured
# handshake+call cost is ~240ms; 0.8s leaves headroom while keeping the
# documented "output is intentionally small" budget from being blown by a
# retry storm or a half-hung child.
MEMORY_RECALL_TIMEOUT_SECONDS = 0.8
MEMORY_RECALL_LIMIT = 3
MEMORY_ITEM_MAX_CHARS = 160


def recall_recent_memories() -> list[str]:
    """Best-effort recall of a few relevant recent memories for session-start
    context. Must never raise and must never add more than
    MEMORY_RECALL_TIMEOUT_SECONDS of wall-clock time -- on any failure
    (missing node, hung server, malformed response) this degrades silently
    to the pre-existing behavior of injecting only the startup contract.
    """
    try:
        scripts_dir = str(Path(__file__).resolve().parent)
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import agentmemory_client

        items = agentmemory_client.recall(
            "FLOSSI0ULLK recent session decisions and outcomes",
            limit=MEMORY_RECALL_LIMIT,
            timeout=MEMORY_RECALL_TIMEOUT_SECONDS,
        )
        trimmed = []
        for item in items:
            if not isinstance(item, str):
                continue
            item = item.strip()
            if not item:
                continue
            if len(item) > MEMORY_ITEM_MAX_CHARS:
                item = item[:MEMORY_ITEM_MAX_CHARS] + "…"
            trimmed.append(item)
        return trimmed
    except Exception:  # noqa: BLE001 -- session start must never fail on this
        return []


def render_memory_section(items: list[str]) -> str:
    """Render the recalled-memories block. Defensively re-trims each item
    and caps the item count itself -- this is the last stop before the
    text gets injected into the session, so it must not simply trust that
    `recall_recent_memories()` already bounded everything upstream.
    """
    if not items:
        return ""
    bounded_items = []
    for item in items[:MEMORY_RECALL_LIMIT]:
        if not isinstance(item, str):
            continue
        item = item.strip()
        if len(item) > MEMORY_ITEM_MAX_CHARS:
            item = item[:MEMORY_ITEM_MAX_CHARS] + "…"
        if item:
            bounded_items.append(item)
    if not bounded_items:
        return ""
    lines = "\n".join(f"- {item}" for item in bounded_items)
    return "\n\n## Recent memory\n" + lines


def main() -> int:
    try:
        contract = CONTRACT.read_text(encoding="utf-8")
    except OSError as e:
        # Silent-fail to avoid blocking the session; the contract isn't load-bearing
        # for tool execution — it's orientation.
        print(
            json.dumps(
                {
                    "continue": True,
                    "additionalContext": f"# FLOSSI0ULLK startup contract unavailable: {e}",
                }
            )
        )
        return 0

    memory_section = render_memory_section(recall_recent_memories())

    payload = {
        "continue": True,
        "additionalContext": contract + memory_section,
    }
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
