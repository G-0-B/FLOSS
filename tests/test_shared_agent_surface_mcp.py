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


def env_ref(name: str) -> str:
    """Reference an environment variable the way THIS platform expands it.

    `os.path.expandvars` expands `%VAR%` only on Windows; on POSIX it expands
    `$VAR` and leaves `%VAR%` as a literal. Tests that set a variable and then
    referenced it as `%VAR%` therefore passed on Windows and failed on the Linux
    CI runner with "references undefined environment variable".

    The production manifests keep `%LOCALAPPDATA%` because that target is
    Windows-only by nature and is skipped elsewhere; these tests are about the
    expansion mechanism itself, so they have to ask in the local dialect.
    """
    return f"%{name}%" if os.name == "nt" else f"${name}"


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


def test_codex_stdio_to_http_clears_stale_env():
    """A stdio->http transport switch must not carry the old `env` forward.

    Mirrors test_hermes_stdio_to_http_clears_stale_fields. Synthetic fixture
    only -- never the real Codex config, never a real credential value.
    """
    doc = tomlkit.parse(
        "[mcp_servers.switched]\n"
        'type = "stdio"\n'
        'command = "old-cmd"\n'
        'args = ["--old"]\n\n'
        "[mcp_servers.switched.env]\n"
        'STALE_TOKEN = "leftover"\n'
    )
    mas.apply_codex_mcp(
        doc,
        {"switched": {"url": "http://127.0.0.1:9999/mcp"}},
        name_map={},
        overrides={},
    )
    reparsed = tomlkit.parse(tomlkit.dumps(doc))
    entry = reparsed["mcp_servers"]["switched"]
    assert entry["type"] == "streamable_http"
    assert entry["url"] == "http://127.0.0.1:9999/mcp"
    assert "command" not in entry
    assert "env" not in entry


def test_codex_http_to_stdio_clears_stale_url():
    """An http->stdio transport switch must not carry the old `url` forward."""
    doc = tomlkit.parse(
        "[mcp_servers.switched]\n"
        'type = "streamable_http"\n'
        'url = "http://127.0.0.1:9999/mcp"\n'
    )
    mas.apply_codex_mcp(
        doc,
        {"switched": {"command": "new-cmd", "args": ["--new"]}},
        name_map={},
        overrides={},
    )
    reparsed = tomlkit.parse(tomlkit.dumps(doc))
    entry = reparsed["mcp_servers"]["switched"]
    assert entry["type"] == "stdio"
    assert entry["command"] == "new-cmd"
    assert entry["args"] == ["--new"]
    assert "url" not in entry


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


import io
import json
import os

from ruamel.yaml import YAML

HERMES_EXISTING = """\
model:
  default: pioneer/auto_v1.1
mcp_servers:
  Agent Memory:
    command: npx
    args:
      - -y
      - '@agentmemory/mcp'
    env:
      AGENTMEMORY_TOOLS: all
  docker:
    command: docker
    args: [mcp, gateway, run]
    enabled: false

# ── Fallback Model ──────────────────────────────
# fallback_model:
#   provider: openrouter
"""


def _roundtrip(text: str):
    yaml = YAML()
    yaml.preserve_quotes = True
    return yaml, yaml.load(io.StringIO(text))


def test_hermes_http_transport():
    yaml, data = _roundtrip(HERMES_EXISTING)
    mas.apply_hermes_mcp(
        data,
        {"flossiullk-consensus": {"url": "http://127.0.0.1:7331/mcp"}},
        name_map={},
        overrides={},
    )
    entry = data["mcp_servers"]["flossiullk-consensus"]
    assert entry["type"] == "http"
    assert entry["url"] == "http://127.0.0.1:7331/mcp"


def test_hermes_name_map_updates_existing_server():
    """`.mcp.json` calls it `agentmemory`; Hermes keys it `Agent Memory`."""
    yaml, data = _roundtrip(HERMES_EXISTING)
    mas.apply_hermes_mcp(
        data,
        {"agentmemory": {"command": "januscope", "args": ["--config", "am.yaml"]}},
        name_map={"agentmemory": "Agent Memory"},
        overrides={},
    )
    assert "agentmemory" not in data["mcp_servers"]
    assert data["mcp_servers"]["Agent Memory"]["command"] == "januscope"
    assert data["mcp_servers"]["Agent Memory"]["env"]["AGENTMEMORY_TOOLS"] == "all"


def test_hermes_preserves_comments_and_unmanaged_servers():
    yaml, data = _roundtrip(HERMES_EXISTING)
    mas.apply_hermes_mcp(
        data,
        {"flossiullk-consensus": {"url": "http://127.0.0.1:7331/mcp"}},
        name_map={},
        overrides={},
    )
    buf = io.StringIO()
    yaml.dump(data, buf)
    rendered = buf.getvalue()
    assert "Fallback Model" in rendered
    assert "fallback_model" in rendered
    assert data["mcp_servers"]["docker"]["enabled"] is False


def test_hermes_overrides_applied():
    yaml, data = _roundtrip(HERMES_EXISTING)
    mas.apply_hermes_mcp(
        data,
        {"flossiullk-consensus": {"url": "http://127.0.0.1:7331/mcp"}},
        name_map={},
        overrides={"flossiullk-consensus": {"enabled": True, "timeout": 120}},
    )
    assert data["mcp_servers"]["flossiullk-consensus"]["timeout"] == 120


def test_hermes_override_beats_existing_field():
    """Overrides are highest precedence, matching apply_codex_mcp."""
    yaml, data = _roundtrip(HERMES_EXISTING)
    mas.apply_hermes_mcp(
        data,
        {"docker-shared": {"command": "docker", "args": []}},
        name_map={"docker-shared": "docker"},
        overrides={"docker-shared": {"enabled": True}},
    )
    assert data["mcp_servers"]["docker"]["enabled"] is True


def test_hermes_gateway_alive_returns_none_without_pid_file(tmp_path):
    assert mas.hermes_gateway_alive(tmp_path) is None


def test_hermes_gateway_alive_detects_dead_pid(tmp_path):
    (tmp_path / "gateway.pid").write_text(
        json.dumps({"pid": 999999, "kind": "hermes-gateway"}), encoding="utf-8"
    )
    assert mas.hermes_gateway_alive(tmp_path) is None


def test_hermes_gateway_alive_detects_own_process(tmp_path):
    import os

    (tmp_path / "gateway.pid").write_text(
        json.dumps({"pid": os.getpid(), "kind": "hermes-gateway"}), encoding="utf-8"
    )
    assert mas.hermes_gateway_alive(tmp_path) == os.getpid()


def test_hermes_gateway_alive_tolerates_corrupt_pid_file(tmp_path):
    (tmp_path / "gateway.pid").write_text("not json{", encoding="utf-8")
    assert mas.hermes_gateway_alive(tmp_path) is None


def test_hermes_name_map_collision_raises():
    yaml, data = _roundtrip(HERMES_EXISTING)
    with pytest.raises(mas.SharedSurfaceError, match="name_map collision"):
        mas.apply_hermes_mcp(
            data,
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


def test_hermes_rejects_non_mapping_existing_entry():
    yaml, data = _roundtrip(HERMES_EXISTING)
    data["mcp_servers"]["serena"] = "foo"
    with pytest.raises(mas.SharedSurfaceError, match="not a mapping"):
        mas.apply_hermes_mcp(
            data,
            {"serena": {"command": "januscope", "args": []}},
            name_map={},
            overrides={},
        )


def test_hermes_rejects_null_existing_entry():
    """A present-but-null YAML value (`serena:` with nothing after it)

    parses to None. `.get()` can't distinguish that from "key absent", so
    an earlier revision let it slip past the malformed-entry guard and
    crash later with `TypeError: argument of type 'NoneType' is not
    iterable`. Membership must be checked explicitly instead.
    """
    text = "mcp_servers:\n  serena:\n"
    yaml, data = _roundtrip(text)
    assert data["mcp_servers"]["serena"] is None
    with pytest.raises(mas.SharedSurfaceError, match="not a mapping"):
        mas.apply_hermes_mcp(
            data,
            {"serena": {"command": "januscope", "args": []}},
            name_map={},
            overrides={},
        )


def test_hermes_noop_merge_preserves_key_order():
    """Regression test for Fix 1: a merge that changes nothing must leave

    key order byte-identical. `CommentedMap.__setitem__` preserves an
    existing key's position; only `del` followed by re-add moves a key to
    the end. An earlier revision deleted every managed field
    unconditionally before reassigning, which reordered every touched
    entry on every run -- including this no-op case -- and would break
    Task 9's fidelity gate (regenerating must produce no spurious diff
    against a verified-good config).
    """
    text = """\
mcp_servers:
  Agent Memory:
    command: januscope
    args:
      - --config
      - am.yaml
    env:
      AGENTMEMORY_TOOLS: all
  flossiullk-consensus:
    type: http
    url: http://127.0.0.1:7331/mcp
    enabled: true
    timeout: 120
"""
    yaml, data = _roundtrip(text)
    before_stdio_keys = list(data["mcp_servers"]["Agent Memory"].keys())
    before_http_keys = list(data["mcp_servers"]["flossiullk-consensus"].keys())

    mas.apply_hermes_mcp(
        data,
        {
            "agentmemory": {
                "command": "januscope",
                "args": ["--config", "am.yaml"],
                "env": {"AGENTMEMORY_TOOLS": "all"},
            },
            "flossiullk-consensus": {"url": "http://127.0.0.1:7331/mcp"},
        },
        name_map={"agentmemory": "Agent Memory"},
        overrides={},
    )

    assert list(data["mcp_servers"]["Agent Memory"].keys()) == before_stdio_keys
    assert list(data["mcp_servers"]["flossiullk-consensus"].keys()) == before_http_keys


def test_hermes_stdio_to_http_clears_stale_fields():
    text = """\
mcp_servers:
  switched:
    command: old-cmd
    args: [--old]
    env:
      OLD: value
"""
    yaml, data = _roundtrip(text)
    mas.apply_hermes_mcp(
        data,
        {"switched": {"url": "http://127.0.0.1:9999/mcp"}},
        name_map={},
        overrides={},
    )
    entry = data["mcp_servers"]["switched"]
    assert entry["type"] == "http"
    assert entry["url"] == "http://127.0.0.1:9999/mcp"
    assert "command" not in entry
    assert "args" not in entry
    assert "env" not in entry


def test_hermes_http_to_stdio_clears_stale_fields():
    text = """\
mcp_servers:
  switched:
    type: http
    url: http://127.0.0.1:9999/mcp
"""
    yaml, data = _roundtrip(text)
    mas.apply_hermes_mcp(
        data,
        {"switched": {"command": "new-cmd", "args": ["--new"]}},
        name_map={},
        overrides={},
    )
    entry = data["mcp_servers"]["switched"]
    assert entry["command"] == "new-cmd"
    assert entry["args"] == ["--new"]
    assert "type" not in entry
    assert "url" not in entry


# ---------------------------------------------------------------------------
# materialize()-level dispatch tests (Task 7)
#
# Before this, materialize()'s per-target blocks had zero test coverage --
# the only end-to-end test (test_umbrella_materializer_refreshes_memory_
# before_context in scripts/tests/test_shared_agent_surface.py) passes
# `"targets": {}` and never enters the Codex/Hermes dispatch. These tests
# exercise the real materialize() with a synthetic manifest and tmp_path
# fixtures -- never the real workspace configs -- so a real write can never
# land on this machine's actual Codex/Hermes config.
# ---------------------------------------------------------------------------


def _stub_downstream_materializers(monkeypatch, workspace: Path) -> None:
    """Point the five downstream per-surface manifests at nonexistent files.

    materialize() unconditionally probes DEFAULT_AI_ROSTER_MANIFEST_PATH,
    DEFAULT_MEMORY_MANIFEST_PATH, DEFAULT_CONTEXT_MANIFEST_PATH,
    DEFAULT_HOOK_MANIFEST_PATH, and DEFAULT_SKILL_MANIFEST_PATH -- which
    default to the real `FLOSS/shared-*-surface.json` files -- and
    materializes each one if it `.exists()`. Left unpatched, calling
    materialize() from this test file would touch the real repo's
    `.agent-surface/` tree. Redirecting them into `tmp_path` (which does not
    contain those filenames) makes each `.exists()` check False, so those
    blocks are skipped entirely and this test is isolated to the Codex/
    Hermes dispatch under test.
    """
    for attr in (
        "DEFAULT_AI_ROSTER_MANIFEST_PATH",
        "DEFAULT_MEMORY_MANIFEST_PATH",
        "DEFAULT_CONTEXT_MANIFEST_PATH",
        "DEFAULT_HOOK_MANIFEST_PATH",
        "DEFAULT_SKILL_MANIFEST_PATH",
    ):
        monkeypatch.setattr(mas, attr, workspace / f"missing-{attr}.json")


def _write_synthetic_manifest(workspace: Path, targets: dict) -> Path:
    """Write a minimal valid shared-agent-surface manifest plus its
    `.mcp.json` source into `workspace`, with only the given `targets`.
    """
    manifest_path = workspace / "shared-agent-surface.json"
    manifest_path.write_text(
        json.dumps(
            {
                "manifest_version": "0.2.0",
                "workspace_id": "test",
                "workspace_name": "Test",
                "mcp_source": ".mcp.json",
                "targets": targets,
            }
        ),
        encoding="utf-8",
    )
    (workspace / ".mcp.json").write_text(
        json.dumps(
            {"mcpServers": {"agentmemory": {"command": "januscope", "args": []}}}
        ),
        encoding="utf-8",
    )
    return manifest_path


def test_resolve_manifest_rejects_unknown_target_key(tmp_path):
    """A typo'd or not-yet-wired target key under `targets` must raise
    loudly. Before this check, materialize() dispatched by a fixed set of
    literal keys with no validation that every manifest key was one of
    them -- an unrecognized key (e.g. a typo, or a new 7th harness) was a
    silent no-op: empty results, drift=False, exit 0, nothing written.
    """
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        {
            "hermes_wrkspace_typo": {"config_path": "hermes.yaml"},
            "windsurf": {"config_path": "windsurf.toml"},
        },
    )
    with pytest.raises(mas.SharedSurfaceError, match="unrecognized key"):
        mas.resolve_manifest(tmp_path, manifest_path)


def test_resolve_manifest_accepts_all_known_target_keys(tmp_path):
    """Every currently-dispatched target key must NOT raise -- this is the
    inverse of test_resolve_manifest_rejects_unknown_target_key and guards
    against KNOWN_TARGET_KEYS drifting out of sync with the real manifest.
    """
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        {key: {} for key in mas.KNOWN_TARGET_KEYS},
    )
    mas.resolve_manifest(tmp_path, manifest_path)


def test_materialize_writes_repo_scope_codex_target(tmp_path, monkeypatch):
    _stub_downstream_materializers(monkeypatch, tmp_path)
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        {
            "codex": {
                "scope": "repo",
                "config_path": "codex/config.toml",
                "name_map": {},
                "overrides": {},
            }
        },
    )

    results, drift = mas.materialize(
        tmp_path, manifest_path, check=False, dry_run=False
    )

    codex_path = tmp_path / "codex" / "config.toml"
    assert codex_path.exists()
    assert 'command = "januscope"' in codex_path.read_text(encoding="utf-8")
    assert drift is True
    assert any(msg.startswith("WROTE") and "codex" in msg for msg in results)


def test_materialize_skips_user_scope_codex_target_without_flag(tmp_path, monkeypatch):
    _stub_downstream_materializers(monkeypatch, tmp_path)
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        {
            "codex_user": {
                "scope": "user",
                "config_path": "codex_user/config.toml",
                "name_map": {},
                "overrides": {},
            }
        },
    )
    codex_user_path = tmp_path / "codex_user" / "config.toml"

    results, drift = mas.materialize(
        tmp_path, manifest_path, check=False, dry_run=False
    )

    assert not codex_user_path.exists()
    assert any("SKIP  codex_user (user scope" in msg for msg in results)
    assert drift is False


def test_materialize_writes_user_scope_codex_target_with_flag(tmp_path, monkeypatch):
    _stub_downstream_materializers(monkeypatch, tmp_path)
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        {
            "codex_user": {
                "scope": "user",
                "config_path": "codex_user/config.toml",
                "name_map": {},
                "overrides": {},
            }
        },
    )
    codex_user_path = tmp_path / "codex_user" / "config.toml"

    results, drift = mas.materialize(
        tmp_path,
        manifest_path,
        check=False,
        dry_run=False,
        include_user_scope=True,
    )

    assert codex_user_path.exists()
    assert drift is True
    assert any(msg.startswith("WROTE") for msg in results)


def test_materialize_skips_hermes_target_with_no_existing_config(tmp_path, monkeypatch):
    """Constraint 1: Hermes targets must never fabricate a config where none
    exists -- `check_or_write_text` would happily create one via
    `write_text`'s `mkdir(parents=True, exist_ok=True)`, which is correct
    for Codex but wrong for Hermes (there is no "update only if present"
    write primitive, so the dispatch itself must check `.exists()` first).
    """
    _stub_downstream_materializers(monkeypatch, tmp_path)
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        {
            "hermes_workspace": {
                "scope": "repo",
                "config_path": "hermes/config.yaml",
                "name_map": {},
                "overrides": {},
            }
        },
    )
    hermes_path = tmp_path / "hermes" / "config.yaml"

    results, drift = mas.materialize(
        tmp_path, manifest_path, check=False, dry_run=False
    )

    assert not hermes_path.exists()
    assert any(
        "SKIP  hermes_workspace" in msg and "no config at" in msg for msg in results
    )
    assert drift is False


def test_materialize_refuses_hermes_write_when_gateway_is_live(tmp_path, monkeypatch):
    import os

    _stub_downstream_materializers(monkeypatch, tmp_path)
    hermes_dir = tmp_path / "hermes"
    hermes_dir.mkdir()
    hermes_config_path = hermes_dir / "config.yaml"
    original_content = "mcp_servers:\n  existing:\n    command: foo\n"
    hermes_config_path.write_text(original_content, encoding="utf-8")
    (hermes_dir / "gateway.pid").write_text(
        json.dumps({"pid": os.getpid(), "kind": "hermes-gateway"}), encoding="utf-8"
    )
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        {
            "hermes_workspace": {
                "scope": "repo",
                "config_path": "hermes/config.yaml",
                "name_map": {},
                "overrides": {},
            }
        },
    )

    results, drift = mas.materialize(
        tmp_path, manifest_path, check=False, dry_run=False
    )

    assert drift is True
    assert any(
        msg.startswith("REFUSED hermes_workspace:") and str(os.getpid()) in msg
        for msg in results
    )
    # The refused write must not have touched the file at all.
    assert hermes_config_path.read_text(encoding="utf-8") == original_content


def test_materialize_refuses_hermes_write_under_check_too(tmp_path, monkeypatch):
    """Design decision: REFUSED fires during `--check` as well as a real
    write. `--check` never writes either way, but the point of `--check` is
    to let an operator discover problems -- including "a live gateway will
    clobber this on shutdown" -- before attempting a real write, not only
    after one has already failed.
    """
    import os

    _stub_downstream_materializers(monkeypatch, tmp_path)
    hermes_dir = tmp_path / "hermes"
    hermes_dir.mkdir()
    (hermes_dir / "config.yaml").write_text(
        "mcp_servers:\n  existing:\n    command: foo\n", encoding="utf-8"
    )
    (hermes_dir / "gateway.pid").write_text(
        json.dumps({"pid": os.getpid(), "kind": "hermes-gateway"}), encoding="utf-8"
    )
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        {
            "hermes_workspace": {
                "scope": "repo",
                "config_path": "hermes/config.yaml",
                "name_map": {},
                "overrides": {},
            }
        },
    )

    results, drift = mas.materialize(tmp_path, manifest_path, check=True, dry_run=False)

    assert drift is True
    assert any(msg.startswith("REFUSED hermes_workspace:") for msg in results)


def test_target_in_scope_repo_always_true():
    assert mas.target_in_scope({"scope": "repo"}, False) is True
    assert mas.target_in_scope({"scope": "repo"}, True) is True


def test_target_in_scope_user_requires_flag():
    assert mas.target_in_scope({"scope": "user"}, False) is False
    assert mas.target_in_scope({"scope": "user"}, True) is True


def test_target_in_scope_requires_explicit_scope_field():
    """Fix 4 (review of 79dd0d6): absence of `scope` must raise, not

    default to "repo" (i.e. write unconditionally). This function exists to
    gate writes outside the repo; defaulting absence to the affirmative
    would let a future manifest entry that forgets `scope` on a user-scope
    target skip the gate entirely.
    """
    with pytest.raises(mas.SharedSurfaceError, match="scope"):
        mas.target_in_scope({}, False)


def test_target_in_scope_rejects_invalid_scope_value():
    with pytest.raises(mas.SharedSurfaceError, match="scope"):
        mas.target_in_scope({"scope": "workspace"}, False)


def test_resolve_manifest_path_expands_env_vars(tmp_path, monkeypatch):
    """Extension for Task 7: resolve_manifest_path must also expand
    `%VAR%`/`$VAR` environment references, not just `~`, since
    `hermes_user`'s manifest path is `%LOCALAPPDATA%/hermes/config.yaml`.
    """
    monkeypatch.setenv("MAS_TEST_VAR", str(tmp_path / "expanded"))
    resolved = mas.resolve_manifest_path(
        tmp_path, env_ref("MAS_TEST_VAR") + "/hermes/config.yaml"
    )
    assert resolved == (tmp_path / "expanded" / "hermes" / "config.yaml").resolve()


# ---------------------------------------------------------------------------
# Review fixes on top of 79dd0d6 (risk/robustness issues found in quality
# review; spec compliance passed cleanly).
# ---------------------------------------------------------------------------


def test_resolve_manifest_path_raises_on_undefined_env_var(tmp_path, monkeypatch):
    """Fix 3: an undefined `%VAR%`/`$VAR` must raise loudly, not silently

    resolve to a bogus literal path nested inside the workspace tree.
    `os.path.expandvars` leaves an undefined reference untouched instead of
    raising, which -- left unchecked -- makes a stripped-environment run
    (scheduled task, minimal CI shell, ...) silently treat a real config as
    "not found" instead of failing.
    """
    monkeypatch.delenv("MAS_DEFINITELY_UNDEFINED_VAR", raising=False)
    with pytest.raises(mas.SharedSurfaceError, match="MAS_DEFINITELY_UNDEFINED_VAR"):
        mas.resolve_manifest_path(
            tmp_path, "%MAS_DEFINITELY_UNDEFINED_VAR%/hermes/config.yaml"
        )


def test_materialize_exits_nonzero_on_refused_hermes_write_on_real_run(
    tmp_path, monkeypatch
):
    """Fix 1 (CRITICAL): a REFUSED write must not report process success.

    Calls the real `main()` entry point (via a monkeypatched `sys.argv`)
    against a synthetic tmp_path manifest -- never the real workspace
    config -- on a plain (non-`--check`) run, since the bug was specifically
    that `main()`'s exit code only considered drift under `--check`. Before
    this fix, `args.check and drift_found` was `False` on a non-`--check`
    run, so a REFUSED Hermes write (which sets `drift_found = True` but
    never writes) still exited 0 -- indistinguishable from success to a
    caller like `refresh_agent_surfaces.py` that keys off exit code alone.
    """
    import os
    import sys

    _stub_downstream_materializers(monkeypatch, tmp_path)
    hermes_dir = tmp_path / "hermes"
    hermes_dir.mkdir()
    hermes_config_path = hermes_dir / "config.yaml"
    original_content = "mcp_servers:\n  existing:\n    command: foo\n"
    hermes_config_path.write_text(original_content, encoding="utf-8")
    (hermes_dir / "gateway.pid").write_text(
        json.dumps({"pid": os.getpid(), "kind": "hermes-gateway"}), encoding="utf-8"
    )
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        {
            "hermes_workspace": {
                "scope": "repo",
                "config_path": "hermes/config.yaml",
                "name_map": {},
                "overrides": {},
            }
        },
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "materialize_shared_agent_surface.py",
            "--workspace-root",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
        ],
    )

    exit_code = mas.main()

    assert exit_code == 1
    # The refused write must not have touched the file.
    assert hermes_config_path.read_text(encoding="utf-8") == original_content


def test_materialize_wraps_malformed_codex_toml_in_shared_surface_error(
    tmp_path, monkeypatch
):
    """Fix 2: a malformed hand-edited Codex config must raise one actionable

    SharedSurfaceError naming the path, not a raw tomlkit traceback that
    (since `results` is only printed after materialize() returns in full)
    would discard every result gathered before it and silently skip the
    downstream sub-materializers that run later in the function.
    """
    _stub_downstream_materializers(monkeypatch, tmp_path)
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir()
    (codex_dir / "config.toml").write_text("not [valid toml", encoding="utf-8")
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        {
            "codex": {
                "scope": "repo",
                "config_path": "codex/config.toml",
                "name_map": {},
                "overrides": {},
            }
        },
    )

    with pytest.raises(mas.SharedSurfaceError, match="Codex config"):
        mas.materialize(tmp_path, manifest_path, check=False, dry_run=False)


def test_materialize_wraps_malformed_hermes_yaml_in_shared_surface_error(
    tmp_path, monkeypatch
):
    """Fix 2, Hermes side: same guard as the Codex test above."""
    _stub_downstream_materializers(monkeypatch, tmp_path)
    hermes_dir = tmp_path / "hermes"
    hermes_dir.mkdir()
    (hermes_dir / "config.yaml").write_text(
        "mcp_servers:\n  existing:\n    command: foo\n  bad: [unterminated\n",
        encoding="utf-8",
    )
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        {
            "hermes_workspace": {
                "scope": "repo",
                "config_path": "hermes/config.yaml",
                "name_map": {},
                "overrides": {},
            }
        },
    )

    with pytest.raises(mas.SharedSurfaceError, match="Hermes config"):
        mas.materialize(tmp_path, manifest_path, check=False, dry_run=False)


def test_materialize_reports_clear_error_for_codex_config_path_that_is_a_directory(
    tmp_path, monkeypatch
):
    """Fix 5: `.exists()` is True for a directory too, so a `config_path`

    that names a directory must not fall through to a raw
    IsADirectoryError/PermissionError from `read_text()`.
    """
    _stub_downstream_materializers(monkeypatch, tmp_path)
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir()
    (codex_dir / "config.toml").mkdir()  # config_path resolves to a directory
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        {
            "codex": {
                "scope": "repo",
                "config_path": "codex/config.toml",
                "name_map": {},
                "overrides": {},
            }
        },
    )

    with pytest.raises(mas.SharedSurfaceError, match="Codex config"):
        mas.materialize(tmp_path, manifest_path, check=False, dry_run=False)


def test_materialize_reports_clear_error_for_hermes_config_path_that_is_a_directory(
    tmp_path, monkeypatch
):
    """Fix 5, Hermes side: same guard as the Codex test above."""
    _stub_downstream_materializers(monkeypatch, tmp_path)
    hermes_dir = tmp_path / "hermes"
    hermes_dir.mkdir()
    (hermes_dir / "config.yaml").mkdir()  # config_path resolves to a directory
    manifest_path = _write_synthetic_manifest(
        tmp_path,
        {
            "hermes_workspace": {
                "scope": "repo",
                "config_path": "hermes/config.yaml",
                "name_map": {},
                "overrides": {},
            }
        },
    )

    with pytest.raises(mas.SharedSurfaceError, match="Hermes config"):
        mas.materialize(tmp_path, manifest_path, check=False, dry_run=False)


def test_opencode_remote_projection_keeps_its_headers():
    """classify_transport() validates and returns the header map, and the
    OpenCode branch emitted only type and url -- so an MCP whose auth lives in
    an Authorization header was projected as an unauthenticated server. It
    parses, it installs, and it fails at connect time against a config file
    that looks correct, with nothing in it to suggest anything was removed.
    """
    projected = mas.convert_mcp_server_to_opencode(
        "authed",
        {
            "type": "http",
            "url": "https://example.invalid/mcp",
            "headers": {"Authorization": "Bearer token-value"},
        },
    )

    assert projected["type"] == "remote"
    assert projected["url"] == "https://example.invalid/mcp"
    assert projected["headers"] == {"Authorization": "Bearer token-value"}


def test_opencode_remote_projection_omits_absent_headers():
    """An unauthenticated server must not gain an empty headers key."""
    projected = mas.convert_mcp_server_to_opencode(
        "plain", {"type": "http", "url": "https://example.invalid/mcp"}
    )

    assert projected == {"type": "remote", "url": "https://example.invalid/mcp"}


HEADERED = {
    "type": "http",
    "url": "https://example.invalid/mcp",
    "headers": {"Authorization": "Bearer token-value"},
}


def test_codex_projects_headers_to_http_headers():
    """The Codex branch wrote only type and url, so an MCP authenticated by
    header was emitted as an unauthenticated server -- the same defect fixed
    for OpenCode one commit earlier, in the same file, three functions away."""
    doc = tomlkit.parse("")
    result = mas.apply_codex_mcp(doc, {"authed": HEADERED}, {}, {})

    entry = result["mcp_servers"]["authed"]
    assert entry["type"] == "streamable_http"
    assert dict(entry["http_headers"]) == {"Authorization": "Bearer token-value"}


def test_codex_drops_a_stale_header_table_when_the_transport_changes():
    """http_headers is managed, not preserved: a server converted to stdio
    must not keep credential-bearing headers from its previous configuration.
    Same reasoning the `env` handling already documents, in reverse.

    The stale table is seeded DIRECTLY rather than produced by a first
    projection. Written that way, the test passed against the unfixed code for
    a vacuous reason -- the old code never wrote http_headers at all, so
    "not in entry" was true either way. It has to start from a config that
    already carries the credentials.
    """
    doc = tomlkit.parse(
        chr(10).join(
            [
                "[mcp_servers.srv]",
                'type = "streamable_http"',
                'url = "https://example.invalid/mcp"',
                "",
                "[mcp_servers.srv.http_headers]",
                'Authorization = "Bearer stale-token"',
            ]
        )
    )
    assert "http_headers" in doc["mcp_servers"]["srv"], "fixture is not stale"

    result = mas.apply_codex_mcp(
        doc, {"srv": {"command": "run", "args": ["--x"]}}, {}, {}
    )

    entry = result["mcp_servers"]["srv"]
    assert entry["type"] == "stdio"
    assert "http_headers" not in entry, "a stale credential table survived"


def test_codex_omits_http_headers_when_there_are_none():
    doc = tomlkit.parse("")
    result = mas.apply_codex_mcp(
        doc, {"plain": {"type": "http", "url": "https://example.invalid/mcp"}}, {}, {}
    )

    assert "http_headers" not in result["mcp_servers"]["plain"]


def test_a_target_with_no_header_field_refuses_rather_than_dropping_them():
    """Antigravity and Hermes have no verified header field. Inventing one
    would be the same silent failure with extra steps, and writing the server
    without its credentials is the defect itself -- so it fails loudly at
    materialization, naming the server and the target."""
    with pytest.raises(mas.SharedSurfaceError, match="Antigravity"):
        mas.build_antigravity_payload({}, {"authed": HEADERED})

    # Hermes, not Antigravity twice. The second assertion here called the same
    # function with the same argument and only varied the match pattern -- and
    # both patterns appear in the one error message, so it asserted nothing the
    # first had not. The point of the guard is that BOTH header-less targets
    # refuse; testing one of them twice is how a sibling stays uncovered.
    with pytest.raises(mas.SharedSurfaceError, match="Hermes"):
        mas.apply_hermes_mcp({}, {"authed": HEADERED}, {}, {})


def test_an_unauthenticated_http_server_still_projects_everywhere():
    """Fail-closed must not refuse the ordinary case."""
    plain = {"type": "http", "url": "https://example.invalid/mcp"}

    payload = mas.build_antigravity_payload({}, {"plain": plain})

    assert payload["mcpServers"]["plain"] == {
        "serverUrl": "https://example.invalid/mcp"
    }


def test_an_override_that_flips_the_transport_strands_no_credentials():
    """Overrides are applied last and can set `type` to anything, including
    flipping an http entry to stdio after http_headers was written -- leaving
    credentials on an entry that will never send them, in a file an operator
    reads as current."""
    doc = tomlkit.parse("")

    result = mas.apply_codex_mcp(
        doc, {"srv": HEADERED}, {}, {"srv": {"type": "stdio", "command": "run"}}
    )

    entry = result["mcp_servers"]["srv"]
    assert entry["type"] == "stdio"
    assert "http_headers" not in entry, "credentials outlived their transport"


def test_a_scalar_override_renders_outside_the_header_table():
    """Pins the RENDERED shape, and passes against the unfixed code by design.

    Overrides used to be applied wholesale after the tables, which contradicts
    the ordering rule this function exists to honour -- adding http_headers put
    a table in front of the override loop for exactly the entries that carry
    credentials. Splitting overrides into scalars and tables restores the rule.

    This test cannot discriminate that change, and saying so is the point:
    tomlkit at the pinned version re-orders on render, so the output is
    identical either way. What it guards is the day that stops being true,
    which is the same reason the ordering rule is written down at all -- the
    function's own docstring calls it defense-in-depth, not load-bearing today.
    """
    doc = tomlkit.parse("")

    result = mas.apply_codex_mcp(
        doc, {"srv": HEADERED}, {}, {"srv": {"startup_timeout_sec": 45}}
    )

    rendered = tomlkit.dumps(result)
    headers_at = rendered.index("[mcp_servers.srv.http_headers]")
    scalar_at = rendered.index("startup_timeout_sec")
    assert scalar_at < headers_at, (
        "a scalar override was emitted after the header table, which is the "
        f"re-parenting hazard the ordering rule exists for:\n{rendered}"
    )
    assert result["mcp_servers"]["srv"]["startup_timeout_sec"] == 45
