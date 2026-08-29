from pathlib import Path
import json

import pytest

# .mcp.json is gitignored machine-local launch config. CI checks out FLOSS
# alone, so walk ancestors and skip when none exist (same pattern as
# tests/test_refresh_agent_surfaces.py).
_here = Path(__file__).resolve()


def _mcp_json_paths() -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for p in _here.parents:
        candidate = p / ".mcp.json"
        if candidate.is_file():
            key = candidate.resolve()
            if key not in seen:
                seen.add(key)
                found.append(key)
    return found


def test_root_mcp_json_has_no_a2a_server_key():
    paths = _mcp_json_paths()
    if not paths:
        pytest.skip(
            "no .mcp.json walking ancestors from test file "
            "(CI / bare checkout; file is gitignored)"
        )
    for mcp_path in paths:
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
        names = set(data.get("mcpServers", {}))
        assert "a2a" not in {n.lower() for n in names}, mcp_path
        assert "flossiullk-a2a" not in names, mcp_path


def test_helloworld_agent_name_is_not_controller():
    from packages.a2a_mesh.helloworld import AGENT_NAME

    assert AGENT_NAME == "flossi0ullk-a2a-helloworld"
