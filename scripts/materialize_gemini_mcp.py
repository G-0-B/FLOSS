"""Backward-compatible wrapper for Gemini MCP materialization.

Prefer `materialize_shared_agent_surface.py` for the full shared-surface flow.
This wrapper exists so older commands still work while delegating to the
canonical shared-surface materializer.
"""

from __future__ import annotations

from materialize_shared_agent_surface import main

if __name__ == "__main__":
    raise SystemExit(main())
