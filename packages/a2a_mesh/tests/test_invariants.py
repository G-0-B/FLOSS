from pathlib import Path
import json

# Worktree is nested under FLOSS/.worktrees/; walk up to workspace .mcp.json.
_here = Path(__file__).resolve()
ROOT = next(p for p in [_here, *_here.parents] if (p / ".mcp.json").is_file())


def test_root_mcp_json_has_no_a2a_server_key():
    data = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    names = set(data.get("mcpServers", {}))
    assert "a2a" not in {n.lower() for n in names}
    assert "flossiullk-a2a" not in names


def test_helloworld_agent_name_is_not_controller():
    from packages.a2a_mesh.helloworld import AGENT_NAME

    assert AGENT_NAME == "flossi0ullk-a2a-helloworld"
