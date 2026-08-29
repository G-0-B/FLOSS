from pathlib import Path
import json

# Workspace tool-bus root (brief/global constraint). Nested worktrees also
# inherit FLOSS/.mcp.json mirrors — check every .mcp.json from the test up
# through WORKSPACE inclusive.
WORKSPACE = Path(r"C:\~shit")
_here = Path(__file__).resolve()


def _mcp_json_paths() -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for p in [_here.parent, *_here.parents]:
        candidate = p / ".mcp.json"
        if candidate.is_file():
            key = candidate.resolve()
            if key not in seen:
                seen.add(key)
                found.append(key)
        if p.resolve() == WORKSPACE.resolve():
            break
    workspace_mcp = (WORKSPACE / ".mcp.json").resolve()
    if workspace_mcp.is_file() and workspace_mcp not in seen:
        found.append(workspace_mcp)
    assert workspace_mcp.is_file(), f"missing workspace tool-bus file: {workspace_mcp}"
    assert workspace_mcp in found
    return found


def test_root_mcp_json_has_no_a2a_server_key():
    for mcp_path in _mcp_json_paths():
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
        names = set(data.get("mcpServers", {}))
        assert "a2a" not in {n.lower() for n in names}, mcp_path
        assert "flossiullk-a2a" not in names, mcp_path


def test_helloworld_agent_name_is_not_controller():
    from packages.a2a_mesh.helloworld import AGENT_NAME

    assert AGENT_NAME == "flossi0ullk-a2a-helloworld"
