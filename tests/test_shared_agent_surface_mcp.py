"""Unit tests for MCP transport classification and per-target projection.

Covers the regression that broke the shared surface on 2026-07-17: an HTTP
(url-only) MCP server could not be projected to OpenCode, which made every
`materialize_shared_agent_surface.py` run crash and caused harness config
drift across five surfaces.

Run from repo root:  python -m pytest FLOSS/tests/test_shared_agent_surface_mcp.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import materialize_shared_agent_surface as mas  # noqa: E402


def test_classify_transport_stdio():
    transport, spec = mas.classify_transport(
        "serena", {"command": "januscope", "args": ["--config", "x.yaml"]}
    )
    assert transport == "stdio"
    assert spec["command"] == "januscope"
    assert spec["args"] == ["--config", "x.yaml"]
    assert spec["env"] is None


def test_classify_transport_http():
    transport, spec = mas.classify_transport(
        "flossiullk-consensus",
        {"type": "http", "url": "http://127.0.0.1:7331/mcp"},
    )
    assert transport == "http"
    assert spec["url"] == "http://127.0.0.1:7331/mcp"


def test_classify_transport_rejects_neither():
    with pytest.raises(mas.SharedSurfaceError, match="either `command` or `url`"):
        mas.classify_transport("broken", {"type": "http"})


def test_classify_transport_rejects_non_string_args():
    with pytest.raises(
        mas.SharedSurfaceError, match="`args` must be a list of strings"
    ):
        mas.classify_transport("bad", {"command": "x", "args": [1, 2]})


def test_classify_transport_prefers_stdio_when_both_present():
    """Documented precedence: stdio wins, url is ignored."""
    transport, spec = mas.classify_transport(
        "both", {"command": "januscope", "url": "http://127.0.0.1:7331/mcp"}
    )
    assert transport == "stdio"
    assert "url" not in spec


def test_classify_transport_rejects_non_dict():
    with pytest.raises(mas.SharedSurfaceError, match="must be a JSON object"):
        mas.classify_transport("bad", "not-a-dict")


def test_classify_transport_ignores_whitespace_only_command():
    """A blank command must not be treated as a usable stdio target."""
    transport, spec = mas.classify_transport(
        "ws", {"command": "   ", "url": "http://127.0.0.1:7331/mcp"}
    )
    assert transport == "http"


def test_classify_transport_rejects_non_string_env():
    with pytest.raises(mas.SharedSurfaceError, match="`env` must be a string map"):
        mas.classify_transport("bad", {"command": "x", "env": {"A": 1}})


def test_classify_transport_rejects_non_string_headers():
    with pytest.raises(mas.SharedSurfaceError, match="`headers` must be a string map"):
        mas.classify_transport(
            "bad", {"url": "http://127.0.0.1:7331/mcp", "headers": {"A": 1}}
        )


def test_opencode_stdio_projection():
    result = mas.convert_mcp_server_to_opencode(
        "serena", {"command": "januscope", "args": ["--config", "serena.yaml"]}
    )
    assert result == {
        "command": ["januscope", "--config", "serena.yaml"],
        "type": "local",
    }


def test_opencode_http_projection():
    """The 2026-07-17 regression: url-only servers must project, not crash."""
    result = mas.convert_mcp_server_to_opencode(
        "flossiullk-consensus",
        {"type": "http", "url": "http://127.0.0.1:7331/mcp"},
    )
    assert result == {"type": "remote", "url": "http://127.0.0.1:7331/mcp"}


def test_opencode_stdio_env_projection():
    result = mas.convert_mcp_server_to_opencode(
        "agentmemory",
        {"command": "januscope", "args": [], "env": {"AGENTMEMORY_TOOLS": "all"}},
    )
    assert result["environment"] == {"AGENTMEMORY_TOOLS": "all"}


def test_opencode_payload_preserves_unmanaged_servers():
    existing = {"mcp": {"openwork-browser": {"type": "remote", "url": "http://x/mcp"}}}
    payload = mas.build_opencode_payload(
        existing, {"flossiullk-consensus": {"url": "http://127.0.0.1:7331/mcp"}}
    )
    assert payload["mcp"]["openwork-browser"] == {
        "type": "remote",
        "url": "http://x/mcp",
    }
    assert payload["mcp"]["flossiullk-consensus"]["type"] == "remote"


import tomlkit

CODEX_EXISTING = """\
model = "gpt-5.6-sol"

[mcp_servers.node_repl]
type = "stdio"
command = "node_repl.exe"

[mcp_servers.agentmemory]
type = "stdio"
command = "npx"
args = ["-y", "@agentmemory/mcp"]

[mcp_servers.agentmemory.tools.memory_save]
approval_mode = "approve"
"""


def test_codex_http_uses_streamable_http_discriminator():
    doc = tomlkit.parse(CODEX_EXISTING)
    mas.apply_codex_mcp(
        doc,
        {"flossiullk-consensus": {"url": "http://127.0.0.1:7331/mcp"}},
        name_map={},
        overrides={},
    )
    entry = doc["mcp_servers"]["flossiullk-consensus"]
    assert entry["type"] == "streamable_http"
    assert entry["url"] == "http://127.0.0.1:7331/mcp"
    assert "command" not in entry


def test_codex_preserves_unmanaged_servers_and_subtables():
    doc = tomlkit.parse(CODEX_EXISTING)
    mas.apply_codex_mcp(
        doc,
        {"agentmemory": {"command": "januscope", "args": ["--config", "am.yaml"]}},
        name_map={},
        overrides={},
    )
    rendered = tomlkit.dumps(doc)
    assert doc["mcp_servers"]["node_repl"]["command"] == "node_repl.exe"
    assert (
        doc["mcp_servers"]["agentmemory"]["tools"]["memory_save"]["approval_mode"]
        == "approve"
    )
    assert doc["mcp_servers"]["agentmemory"]["command"] == "januscope"
    assert doc["mcp_servers"]["agentmemory"]["args"] == ["--config", "am.yaml"]
    assert 'model = "gpt-5.6-sol"' in rendered


def test_codex_output_reparses_with_values_in_the_right_tables():
    """Guards the TOML key-ordering hazard.

    A scalar written after a sub-table header belongs to that sub-table, so a
    naive append would silently move `command` into `agentmemory.tools`.
    """
    doc = tomlkit.parse(CODEX_EXISTING)
    mas.apply_codex_mcp(
        doc,
        {"agentmemory": {"command": "januscope", "args": ["--config", "am.yaml"]}},
        name_map={},
        overrides={},
    )
    reparsed = tomlkit.parse(tomlkit.dumps(doc))
    server = reparsed["mcp_servers"]["agentmemory"]
    assert server["command"] == "januscope"
    assert "command" not in server["tools"]["memory_save"]
    assert server["tools"]["memory_save"]["approval_mode"] == "approve"


def test_codex_env_preserved_when_shared_entry_has_no_env():
    doc = tomlkit.parse(
        '[mcp_servers.agentmemory]\ntype = "stdio"\ncommand = "npx"\n\n'
        '[mcp_servers.agentmemory.env]\nAGENTMEMORY_URL = "${AGENTMEMORY_URL}"\n'
    )
    mas.apply_codex_mcp(
        doc,
        {"agentmemory": {"command": "januscope", "args": []}},
        name_map={},
        overrides={},
    )
    assert (
        doc["mcp_servers"]["agentmemory"]["env"]["AGENTMEMORY_URL"]
        == "${AGENTMEMORY_URL}"
    )
