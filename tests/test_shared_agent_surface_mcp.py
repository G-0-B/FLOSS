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
    """Regression check on the TOML key-ordering hazard the writer guards
    against with defense-in-depth ordering (scalars/overrides before
    sub-tables).

    Note: on tomlkit 0.15.0 this test does NOT actually discriminate a
    careful scalars-before-tables merge from a naive one -- `tomlkit`'s
    `Container` bubbles scalar keys ahead of sub-tables at render time
    regardless of assignment order (verified empirically). This test just
    confirms the writer's output re-parses with `command` in the server
    table and not inside `agentmemory.tools`; it is not proof the ordering
    discipline in `apply_codex_mcp` is load-bearing on this tomlkit version.
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


CODEX_EXISTING_WITH_TIMEOUT = """\
model = "gpt-5.6-sol"

[mcp_servers.agentmemory]
type = "stdio"
command = "npx"
args = ["-y", "@agentmemory/mcp"]
startup_timeout_sec = 30

[mcp_servers.agentmemory.tools.memory_save]
approval_mode = "approve"
"""


def test_codex_override_beats_existing_field():
    """Overrides must win even over a pre-existing field of the same name.

    Reviewer-verified regression: with the overrides loop applied before the
    preserved-scalars loop, a pre-existing `startup_timeout_sec = 30` on the
    target entry silently discarded an `overrides` value of 5.
    """
    doc = tomlkit.parse(CODEX_EXISTING_WITH_TIMEOUT)
    mas.apply_codex_mcp(
        doc,
        {"agentmemory": {"command": "januscope", "args": []}},
        name_map={},
        overrides={"agentmemory": {"startup_timeout_sec": 5}},
    )
    reparsed = tomlkit.parse(tomlkit.dumps(doc))
    assert reparsed["mcp_servers"]["agentmemory"]["startup_timeout_sec"] == 5


def test_codex_name_map_renames_server():
    doc = tomlkit.parse(CODEX_EXISTING)
    mas.apply_codex_mcp(
        doc,
        {"agentmemory": {"command": "januscope", "args": ["--config", "am.yaml"]}},
        name_map={"agentmemory": "Agent Memory"},
        overrides={},
    )
    reparsed = tomlkit.parse(tomlkit.dumps(doc))
    mapped = reparsed["mcp_servers"]["Agent Memory"]
    assert mapped["type"] == "stdio"
    assert mapped["command"] == "januscope"
    assert mapped["args"] == ["--config", "am.yaml"]


def test_codex_name_map_collision_raises():
    doc = tomlkit.parse(CODEX_EXISTING)
    with pytest.raises(mas.SharedSurfaceError, match="name_map collision"):
        mas.apply_codex_mcp(
            doc,
            {
                "agentmemory": {"command": "januscope", "args": []},
                "agentmemory-alt": {"command": "other", "args": []},
            },
            name_map={
                "agentmemory": "shared_target",
                "agentmemory-alt": "shared_target",
            },
            overrides={},
        )


def test_codex_rejects_non_table_existing_entry():
    doc = tomlkit.parse('agentmemory = "foo"\n')
    doc["mcp_servers"] = tomlkit.table(is_super_table=True)
    doc["mcp_servers"]["agentmemory"] = "foo"
    with pytest.raises(mas.SharedSurfaceError, match="not a table"):
        mas.apply_codex_mcp(
            doc,
            {"agentmemory": {"command": "januscope", "args": []}},
            name_map={},
            overrides={},
        )
