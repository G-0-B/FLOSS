# MCP Surface Propagation + Unified Surface Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the MCP propagator so it handles HTTP-transport servers, add Codex and Hermes as managed targets, and add one runner that regenerates and verifies the whole shared agent surface.

**Architecture:** Root `.mcp.json` stays the single source of truth. One `classify_transport` helper replaces the duplicated per-target transport logic that caused the outage. Codex and Hermes get merge-preserving writers built on round-trip parsers (`tomlkit`, `ruamel.yaml`) so unrelated config content and comments survive. A thin runner invokes all six existing materializers as subprocesses.

**Tech Stack:** Python 3.13, pytest, `tomlkit`, `ruamel.yaml`, existing `materialize_shared_*.py` scripts.

**Spec:** `docs/superpowers/specs/2026-07-24-mcp-surface-propagation-design.md`

> **Status: COMPLETE (2026-07-24).** All 11 tasks executed via subagent-driven development with two-stage review (spec compliance, then code quality) per task. 90 unit tests pass. The Task 9 fidelity gate passed against live configs — see the spec for the evidence table.
>
> **Three defects were found by review that the implementing agent's own tests did not catch**, each of which would have defeated the fidelity gate or a safety property:
> 1. **Codex `overrides` applied too early** — silently discarded any override whose key already existed in the target file, and contradicted the Hermes writer's ordering. *(Originated in this plan, not the implementation.)*
> 2. **Hermes delete-then-reinsert reordered keys on every run** — a no-op merge reordered `['command','args','env']` → `['env','command','args']`, guaranteeing a spurious diff on every propagation.
> 3. **A REFUSED write exited 0** — a live-gateway refusal on a real run reported success, and the runner would have printed `agent-surface ok`.
>
> Reviewers also determined the exact ruamel configuration that shrinks the Hermes round-trip diff from 398 lines to a single irreducible hunk (amendment 6 below), without which the fidelity gate could not have passed.

**Working directory:** All paths are relative to `C:\~shit\FLOSS` unless prefixed with `../`. The FLOSS directory is its own git repo (branch `working/2026-06-16-adr-cleanup-reconverge`); the workspace root `C:\~shit` is a *separate* repo. Commit in the FLOSS repo.

**Run tests with:** `C:\Python313\python.exe -m pytest FLOSS/tests/test_shared_agent_surface_mcp.py -v` from `C:\~shit`, or `python -m pytest tests/test_shared_agent_surface_mcp.py -v` from `C:\~shit\FLOSS`.

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `scripts/materialize_shared_agent_surface.py` | Owns MCP propagation to all targets | Modify |
| `scripts/refresh_agent_surfaces.py` | Runner over all six materializers | Create |
| `shared-agent-surface.json` | Manifest: targets, name maps, overrides | Modify |
| `tests/test_shared_agent_surface_mcp.py` | Unit tests for transport + converters + writers | Create |
| `tests/test_refresh_agent_surfaces.py` | Runner CLI contract tests | Create |

`materialize_shared_agent_surface.py` is already 1241 lines. This plan adds roughly 150 lines to it and removes duplicated transport logic. It stays one file because the per-target block pattern in `materialize()` is the established convention and splitting it would break the `--manifest`/`--check` contract other tooling depends on.

---

### Task 1: Extract `classify_transport`

The Vibe converter already implements correct stdio/http dispatch; OpenCode has its own broken copy. Extract one shared helper.

**Files:**
- Create: `tests/test_shared_agent_surface_mcp.py`
- Modify: `scripts/materialize_shared_agent_surface.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_shared_agent_surface_mcp.py`:

```python
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
    with pytest.raises(mas.SharedSurfaceError, match="`args` must be a list of strings"):
        mas.classify_transport("bad", {"command": "x", "args": [1, 2]})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Python313\python.exe -m pytest FLOSS/tests/test_shared_agent_surface_mcp.py -v`
Expected: FAIL — `AttributeError: module 'materialize_shared_agent_surface' has no attribute 'classify_transport'`

- [ ] **Step 3: Implement `classify_transport`**

In `scripts/materialize_shared_agent_surface.py`, insert immediately **above** `def convert_mcp_server_to_opencode` (currently ~line 276):

```python
def classify_transport(name: str, server: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Classify a shared MCP server entry as `stdio` or `http`.

    Returns `(transport, spec)`. For stdio, `spec` has `command` (str),
    `args` (list[str]) and `env` (dict[str, str] | None). For http, `spec`
    has `url` (str) and `headers` (dict[str, str] | None).

    This is the single source of transport dispatch for every target. Do not
    reimplement it per target -- divergent copies are what broke the surface
    on 2026-07-17.
    """
    if not isinstance(server, dict):
        raise SharedSurfaceError(f"Shared MCP server {name!r} must be a JSON object")

    command = server.get("command")
    url = server.get("url")

    if isinstance(command, str) and command.strip():
        args = server.get("args") or []
        if not isinstance(args, list) or not all(
            isinstance(item, str) for item in args
        ):
            raise SharedSurfaceError(
                f"Shared MCP server {name!r} stdio `args` must be a list of strings"
            )
        env = server.get("env")
        if env is not None and (
            not isinstance(env, dict)
            or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in env.items()
            )
        ):
            raise SharedSurfaceError(
                f"Shared MCP server {name!r} stdio `env` must be a string map"
            )
        return "stdio", {
            "command": command,
            "args": list(args),
            "env": dict(env) if env else None,
        }

    if isinstance(url, str) and url.strip():
        headers = server.get("headers")
        if headers is not None and (
            not isinstance(headers, dict)
            or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in headers.items()
            )
        ):
            raise SharedSurfaceError(
                f"Shared MCP server {name!r} HTTP `headers` must be a string map"
            )
        return "http", {"url": url, "headers": dict(headers) if headers else None}

    raise SharedSurfaceError(
        f"Shared MCP server {name!r} must define either `command` or `url`"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\Python313\python.exe -m pytest FLOSS/tests/test_shared_agent_surface_mcp.py -v`
Expected: PASS — 4 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_shared_agent_surface_mcp.py scripts/materialize_shared_agent_surface.py
git commit -m "surface: extract classify_transport helper for MCP targets"
```

---

### Task 2: Teach the OpenCode converter about HTTP

This is the actual outage fix.

**Files:**
- Modify: `scripts/materialize_shared_agent_surface.py:276-303` (`convert_mcp_server_to_opencode`)
- Test: `tests/test_shared_agent_surface_mcp.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_shared_agent_surface_mcp.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Python313\python.exe -m pytest FLOSS/tests/test_shared_agent_surface_mcp.py::test_opencode_http_projection -v`
Expected: FAIL — `SharedSurfaceError: Shared MCP server 'flossiullk-consensus' cannot be projected to OpenCode without a `command` string`

- [ ] **Step 3: Rewrite the converter**

Replace the whole body of `convert_mcp_server_to_opencode`:

```python
def convert_mcp_server_to_opencode(name: str, server: dict[str, Any]) -> dict[str, Any]:
    """Project a shared MCP server into OpenCode's config shape.

    OpenCode uses `{"type": "local", "command": [...]}` for stdio and
    `{"type": "remote", "url": ...}` for HTTP (the shape its own
    `openwork-browser`/`chrome` entries already use).
    """
    transport, spec = classify_transport(name, server)

    if transport == "http":
        return {"type": "remote", "url": spec["url"]}

    payload: dict[str, Any] = {
        "command": [spec["command"], *spec["args"]],
        "type": "local",
    }
    if spec["env"]:
        payload["environment"] = spec["env"]
    return payload
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `C:\Python313\python.exe -m pytest FLOSS/tests/test_shared_agent_surface_mcp.py -v`
Expected: PASS — 8 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_shared_agent_surface_mcp.py scripts/materialize_shared_agent_surface.py
git commit -m "fix: project HTTP-transport MCP servers to OpenCode

Unblocks materialize_shared_agent_surface.py, which has crashed on every
run since 01bdeb8 moved consensus/ensemble to HTTP daemon URLs."
```

---

### Task 3: Fix the OpenCode/Vibe scope bug

At ~line 1054 the OpenCode `agent_instruction_path` block sits inside the `vibe_cfg` block and reads `opencode_cfg`. If Vibe is configured without OpenCode, `opencode_cfg` is `None` → `AttributeError`.

**Files:**
- Modify: `scripts/materialize_shared_agent_surface.py:~1034-1075`

- [ ] **Step 1: Read the current block**

Run: `sed -n '1034,1075p' scripts/materialize_shared_agent_surface.py`
Confirm `agent_instruction_raw = opencode_cfg.get("agent_instruction_path")` is indented inside the `if isinstance(vibe_cfg, dict) and vibe_cfg.get("config_path"):` block.

- [ ] **Step 2: Move the block**

Cut this fragment out of the `vibe_cfg` block:

```python
        agent_instruction_raw = opencode_cfg.get("agent_instruction_path")
        if agent_instruction_raw is not None:
            if (
                not isinstance(agent_instruction_raw, str)
                or not agent_instruction_raw.strip()
            ):
                raise SharedSurfaceError(
                    "OpenCode target field `agent_instruction_path` must be a non-empty string"
                )
            agent_instruction_path = workspace_root / agent_instruction_raw
            message, changed = check_or_write_text(
                agent_instruction_path,
                build_opencode_agent_instruction(opencode_cfg),
                check=check,
                dry_run=dry_run,
            )
            results.append(message)
            drift_found = drift_found or changed
```

and paste it at the end of the `opencode_cfg` block (immediately after that block's `drift_found = drift_found or changed`), keeping the same indentation level as the other statements inside the `if isinstance(opencode_cfg, dict) ...:` body.

- [ ] **Step 3: Verify no syntax or regression damage**

Run: `C:\Python313\python.exe -m pytest FLOSS/tests/test_shared_agent_surface_mcp.py -v`
Expected: PASS — 8 passed

Run: `C:\Python313\python.exe -c "import ast,pathlib; ast.parse(pathlib.Path(r'C:/~shit/FLOSS/scripts/materialize_shared_agent_surface.py').read_text(encoding='utf-8')); print('parse OK')"`
Expected: `parse OK`

- [ ] **Step 4: Commit**

```bash
git add scripts/materialize_shared_agent_surface.py
git commit -m "fix: move OpenCode agent-instruction write out of the Vibe block"
```

---

### Task 4: Integration checkpoint — the propagator runs again

Before adding targets, prove the outage is over against the real repo.

**Files:** none modified.

- [ ] **Step 1: Dry-run against the live manifest**

Run from `C:\~shit\FLOSS`:
```bash
C:\Python313\python.exe scripts/materialize_shared_agent_surface.py --dry-run
```
Expected: exits 0, no traceback, prints one line per generated artifact. **If it still raises `SharedSurfaceError`, stop and fix before continuing.**

- [ ] **Step 2: Check mode**

Run: `C:\Python313\python.exe scripts/materialize_shared_agent_surface.py --check`
Expected: exits 0 or 1 (1 = drift detected, which is expected and fine here — the point is that it no longer *crashes*). Record which, and which files it reports as drifted.

- [ ] **Step 3: Confirm the OpenCode projection matches tonight's verified config**

Run: `C:\Python313\python.exe scripts/materialize_shared_agent_surface.py --dry-run` and inspect the OpenCode diff it would write. Compare against `../opworkers/opencode.jsonc`:
- `flossiullk-consensus` → `{"type": "remote", "url": "http://127.0.0.1:7331/mcp"}`
- `flossiullk-reasoning-ensemble` → `{"type": "remote", "url": "http://127.0.0.1:7332/mcp"}`
- `serena` → `{"command": ["januscope", "--config", "C:/~shit/.mcp/lenses/serena.yaml"], "type": "local"}`
- `agentmemory` → same shape with the agentmemory lens
- `openwork-browser`, `chrome`, `openwork-ui` → unchanged

If any differ, the manifest or `.mcp.json` is wrong — fix that, not the test.

---

### Task 5: Codex TOML target

**Files:**
- Modify: `scripts/materialize_shared_agent_surface.py`
- Test: `tests/test_shared_agent_surface_mcp.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_shared_agent_surface_mcp.py`:

```python
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
    # unmanaged server untouched
    assert doc["mcp_servers"]["node_repl"]["command"] == "node_repl.exe"
    # unmanaged subtable on a MANAGED server survives
    assert doc["mcp_servers"]["agentmemory"]["tools"]["memory_save"]["approval_mode"] == "approve"
    # transport fields replaced
    assert doc["mcp_servers"]["agentmemory"]["command"] == "januscope"
    assert doc["mcp_servers"]["agentmemory"]["args"] == ["--config", "am.yaml"]
    # unrelated top-level content survives
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
        doc, {"agentmemory": {"command": "januscope", "args": []}}, name_map={}, overrides={}
    )
    assert doc["mcp_servers"]["agentmemory"]["env"]["AGENTMEMORY_URL"] == "${AGENTMEMORY_URL}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Python313\python.exe -m pytest FLOSS/tests/test_shared_agent_surface_mcp.py -k codex -v`
Expected: FAIL — `AttributeError: module ... has no attribute 'apply_codex_mcp'`

- [ ] **Step 3: Implement the Codex writer**

Do **not** add `import tomlkit` at module top. A missing round-trip library must fail only the target that needs it, not every target (the Gemini/OpenCode/Vibe projections have no such dependency). Add this helper near the top of the file instead:

```python
def require_module(module_name: str, target: str) -> Any:
    """Import a round-trip serializer, failing loudly for one target only.

    Never fall back to a non-round-trip writer -- that would silently strip
    comments and reorder keys in large hand-maintained configs.
    """
    import importlib

    try:
        return importlib.import_module(module_name)
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SharedSurfaceError(
            f"Target {target!r} requires the {module_name!r} package "
            f"(pip install {module_name.split('.')[0]})"
        ) from exc
```

Then add near the other converters:

```python
# Transport fields the propagator owns on a managed server. Everything else
# on that server (tools tables, timeouts, approval modes) is preserved.
MANAGED_TRANSPORT_FIELDS = ("type", "command", "args", "url")


def apply_codex_mcp(
    doc: Any,
    shared_mcp: dict[str, Any],
    name_map: dict[str, str],
    overrides: dict[str, Any],
) -> Any:
    """Merge shared MCP servers into a parsed Codex config.toml document.

    Codex requires an explicit transport discriminator: `type = "stdio"` with
    command/args, or `type = "streamable_http"` with url. A bare `url` key is
    rejected with `url is not supported for stdio`.

    `env` is treated as managed only when the shared entry defines it, so a
    target-local templated env block survives.

    Scalar transport keys are written into a fresh table that is re-inserted
    ahead of any existing sub-tables. In TOML a scalar key appearing after a
    sub-table header belongs to that sub-table, so appending `command` to a
    server that already has `[mcp_servers.<name>.tools.*]` would silently
    produce a wrong (or invalid) document.
    """
    tomlkit = require_module("tomlkit", "codex")

    if "mcp_servers" not in doc:
        doc["mcp_servers"] = tomlkit.table(is_super_table=True)
    servers = doc["mcp_servers"]

    for shared_name, server in shared_mcp.items():
        target_name = name_map.get(shared_name, shared_name)
        transport, spec = classify_transport(shared_name, server)

        existing = servers.get(target_name)
        preserved_scalars: dict[str, Any] = {}
        preserved_tables: dict[str, Any] = {}
        preserved_env: Any = None
        if existing is not None:
            for key, value in existing.items():
                if key in MANAGED_TRANSPORT_FIELDS:
                    continue
                if key == "env":
                    preserved_env = value
                elif hasattr(value, "items"):
                    preserved_tables[key] = value
                else:
                    preserved_scalars[key] = value

        entry = tomlkit.table()

        # 1. managed scalars
        if transport == "http":
            entry["type"] = "streamable_http"
            entry["url"] = spec["url"]
        else:
            entry["type"] = "stdio"
            entry["command"] = spec["command"]
            entry["args"] = spec["args"]

        # 2. preserved scalars (startup_timeout_sec, enabled, ...)
        for key, value in preserved_scalars.items():
            entry[key] = value

        # 3. tables before overrides. `env` is managed only when the shared
        #    entry defines one.
        if transport == "stdio" and spec["env"] is not None:
            entry["env"] = spec["env"]
        elif preserved_env is not None:
            entry["env"] = preserved_env
        for key, value in preserved_tables.items():
            entry[key] = value

        # 4. manifest overrides LAST so they beat everything, including
        #    pre-existing file content. Both this and `apply_hermes_mcp` must
        #    apply overrides last or the two targets honor opposite contracts.
        for key, value in (overrides.get(shared_name) or {}).items():
            entry[key] = value

        servers[target_name] = entry

    return doc
```

> **Correction (2026-07-24, from Task 5's code review):** an earlier revision of this plan applied overrides at step 2, *before* preserved scalars. That silently discarded any override whose key already existed in the target file — verified empirically: an override of `startup_timeout_sec: 5` against an existing `startup_timeout_sec = 30` yielded 30. It also contradicted `apply_hermes_mcp` below, which applies overrides last. Overrides must be applied last in **both** writers.
>
> Also from that review: the scalars-before-tables ordering is **defense-in-depth, not load-bearing** on tomlkit 0.15.0 — `Container.append()` auto-reorders scalars ahead of sub-tables for freshly-built tables, so even a naive merge currently round-trips correctly. Keep the ordering as insurance against a tomlkit behavior change, but do not describe it as the only thing preventing corruption, and do not trust `test_codex_output_reparses_with_values_in_the_right_tables` to catch a regression to naive merging.

- [ ] **Step 4: Run tests to verify they pass**

Run: `C:\Python313\python.exe -m pytest FLOSS/tests/test_shared_agent_surface_mcp.py -v`
Expected: PASS — 12 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_shared_agent_surface_mcp.py scripts/materialize_shared_agent_surface.py
git commit -m "surface: add Codex TOML MCP writer with transport discriminator"
```

---

### Task 6: Hermes YAML target + liveness guard

**Files:**
- Modify: `scripts/materialize_shared_agent_surface.py`
- Test: `tests/test_shared_agent_surface_mcp.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_shared_agent_surface_mcp.py`:

```python
import io
import json

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
    # unmanaged field on the managed server survives
    assert data["mcp_servers"]["Agent Memory"]["env"]["AGENTMEMORY_TOOLS"] == "all"


def test_hermes_preserves_comments_and_unmanaged_servers():
    yaml, data = _roundtrip(HERMES_EXISTING)
    mas.apply_hermes_mcp(
        data, {"flossiullk-consensus": {"url": "http://127.0.0.1:7331/mcp"}},
        name_map={}, overrides={},
    )
    buf = io.StringIO()
    yaml.dump(data, buf)
    rendered = buf.getvalue()
    assert "Fallback Model" in rendered          # trailing comment block survives
    assert "fallback_model" in rendered
    assert data["mcp_servers"]["docker"]["enabled"] is False


def test_hermes_overrides_applied():
    yaml, data = _roundtrip(HERMES_EXISTING)
    mas.apply_hermes_mcp(
        data, {"flossiullk-consensus": {"url": "http://127.0.0.1:7331/mcp"}},
        name_map={}, overrides={"flossiullk-consensus": {"enabled": True, "timeout": 120}},
    )
    assert data["mcp_servers"]["flossiullk-consensus"]["timeout"] == 120


def test_hermes_gateway_alive_returns_none_without_pid_file(tmp_path):
    assert mas.hermes_gateway_alive(tmp_path) is None


def test_hermes_gateway_alive_detects_dead_pid(tmp_path):
    # PID 999999 is above Windows' practical range and will not be running.
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Python313\python.exe -m pytest FLOSS/tests/test_shared_agent_surface_mcp.py -k hermes -v`
Expected: FAIL — `AttributeError: module ... has no attribute 'apply_hermes_mcp'`

- [ ] **Step 3: Implement the Hermes writer and liveness guard**

Add `import os` and `import subprocess` to the imports. `ruamel.yaml` is **not** imported at module top — it is loaded lazily via `require_module` in the dispatch block (Task 7), so a missing package fails only the Hermes target. `apply_hermes_mcp` itself operates on an already-parsed document and needs no import. Add:

```python
def _pid_alive(pid: int) -> bool:
    """Return True if `pid` is a live process."""
    if os.name == "nt":
        completed = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False,
        )
        return str(pid) in completed.stdout
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def hermes_gateway_alive(home: Path) -> int | None:
    """Return the PID of a live Hermes gateway for `home`, else None.

    A running gateway rewrites its own config.yaml on shutdown and would
    clobber anything written underneath it, so writes must be refused while
    it is alive.
    """
    pid_file = home / "gateway.pid"
    if not pid_file.exists():
        return None
    try:
        payload = json.loads(pid_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    pid = payload.get("pid")
    if not isinstance(pid, int):
        return None
    return pid if _pid_alive(pid) else None


def apply_hermes_mcp(
    data: Any,
    shared_mcp: dict[str, Any],
    name_map: dict[str, str],
    overrides: dict[str, Any],
) -> Any:
    """Merge shared MCP servers into a parsed Hermes config.yaml document.

    Hermes supports Streamable HTTP natively via `type: http` + `url`, and
    stdio via `command`/`args`/`env`.
    """
    servers = data.get("mcp_servers")
    if servers is None:
        data["mcp_servers"] = {}
        servers = data["mcp_servers"]

    for shared_name, server in shared_mcp.items():
        target_name = name_map.get(shared_name, shared_name)
        transport, spec = classify_transport(shared_name, server)

        if target_name not in servers:
            servers[target_name] = {}
        entry = servers[target_name]

        for key in MANAGED_TRANSPORT_FIELDS:
            if key in entry:
                del entry[key]

        if transport == "http":
            entry["type"] = "http"
            entry["url"] = spec["url"]
        else:
            entry["command"] = spec["command"]
            entry["args"] = spec["args"]
            if spec["env"] is not None:
                entry["env"] = spec["env"]

        for key, value in (overrides.get(shared_name) or {}).items():
            entry[key] = value

    return data
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `C:\Python313\python.exe -m pytest FLOSS/tests/test_shared_agent_surface_mcp.py -v`
Expected: PASS — 19 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_shared_agent_surface_mcp.py scripts/materialize_shared_agent_surface.py
git commit -m "surface: add Hermes YAML MCP writer with gateway liveness guard"
```

---

### Task 7: Wire the new targets into `materialize()` with scope gating

> **Required amendments discovered during Task 3's review — read before starting.**
>
> 1. **Reuse `resolve_manifest_path`, don't hand-roll path resolution.** It already exists (`scripts/materialize_shared_agent_surface.py:~462`) and does `Path(raw).expanduser()` then returns it if absolute, else joins to `workspace_root`. The existing per-target blocks bypass it and use `workspace_root / cfg[...]` — which happens to work for absolute paths (pathlib discards the left operand) but does **not** expand `~`. It also does **not** expand `%LOCALAPPDATA%`, which `hermes_user` needs. Extend `resolve_manifest_path` with `os.path.expandvars` (a safe improvement for all callers) and route the four new targets through it.
> 2. **`check_or_write_text` CREATES missing files.** It delegates to `write_text`, which does `path.parent.mkdir(parents=True, exist_ok=True)`. There is no "update only if present" mode, and `changed` defaults to `True` for a nonexistent file — missing is indistinguishable from "content differs". The Hermes blocks must therefore guard existence *before* calling it, or they will fabricate a Hermes config where none exists.
> 3. **There is no "REFUSED" vocabulary in this codebase.** The message set is `CHECK DRIFT/OK`, `PLAN WRITE/KEEP`, `WROTE`, `OK`. A refused Hermes write must append its own message to `results` and set `drift_found = True` manually. Note that `main()` only converts `drift_found` into exit 1 **when `--check` is passed** — in a normal writing run the message is the only signal.
> 4. **`materialize()`'s per-target dispatch has ZERO test coverage today.** The only end-to-end test (`scripts/tests/test_shared_agent_surface.py::test_umbrella_materializer_refreshes_memory_before_context`) passes `"targets": {}`, so it never enters the per-target blocks. Every other test calls `build_*` helpers directly. **Task 7 must add `materialize()`-level tests with populated `targets`** covering: repo-scope target written, user-scope target skipped without the flag, user-scope target written with the flag, and Hermes refused when a gateway PID is live. Without these the four new blocks land unprotected.
> 5. **Validate `name_map` collisions once, centrally.** Two shared servers mapping to one target name is silent data loss. Task 5's review added a guard inside the Codex writer; prefer hoisting the check so every target gets it rather than duplicating per-writer. *(Done in Task 6 — `ensure_no_name_map_collisions`.)*
>
> **Further amendments from Task 6's code review — these are prerequisites for the Task 9 fidelity gate, not optional polish:**
>
> 6. **Use exactly this ruamel configuration** when opening a Hermes `config.yaml`. This is the single biggest lever on diff size:
>    ```python
>    yaml = YAML()
>    yaml.preserve_quotes = True
>    yaml.indent(mapping=2, sequence=4, offset=2)
>    yaml.width = 4096
>    ```
>    Measured on a copy of the real `.toilet/hermes/config.yaml` (748 lines) with a no-op merge: bare `YAML()` produces a **398-line diff** (global block-sequence reflow — `args` lists shift from the file's native offset style to flush style, even on entries the writer never touched). Adding `indent(...)` alone but leaving the default width (~80) introduces a *new* bug: the `api_key` scalar sits at 81 chars and gets force-wrapped across two lines. With `indent(...)` **and** `width=4096` together the diff collapses to a **single hunk**.
> 7. **The residual hunk is irreducible — do not chase it.** It is the `personalities:` block: 8 long strings that were wrapped by some other YAML emitter, at fold points ruamel's greedy wrapper does not reproduce at any width. Any width that avoids the `api_key` mis-wrap collapses them to single long lines instead. It is cosmetic, confined to pre-existing content the writer never touches, and vastly smaller than the unconfigured blast radius. **Task 9 must expect this diff on Hermes and not treat it as a fidelity failure.**
> 8. **Fail closed at the call site on undeterminable liveness.** `hermes_gateway_alive` returning `None` means "no live gateway" for the *defined* states (no pidfile, corrupt pidfile, dead PID). Task 6's fix makes `_pid_alive` return `True` when it cannot determine liveness of a valid PID, so the refusal path triggers. Do not add call-site logic that reinterprets `None` as unconditionally safe.
> 9. **Add a real-file-shape fidelity test.** The existing Hermes tests use a ~20-line fixture that is too tidy to catch either the width-driven `api_key` mis-wrap or the personalities reflow — both only appear against a file with long unwrapped scalars and pre-wrapped content. Build a secret-stripped fixture with that shape and assert a no-op round-trip produces a diff confined to a documented allowlist.

**Files:**
- Modify: `scripts/materialize_shared_agent_surface.py` (`materialize()` signature + dispatch, `main()` argparse)

- [ ] **Step 1: Add the scope parameter**

Change the `materialize(...)` signature to accept `include_user_scope: bool = False`, and add a helper above it:

```python
def target_in_scope(target_cfg: dict[str, Any], include_user_scope: bool) -> bool:
    """Repo-scope targets always run; user-scope needs an explicit opt-in."""
    scope = str(target_cfg.get("scope", "repo")).strip().lower()
    if scope not in {"repo", "user"}:
        raise SharedSurfaceError(
            f"Target `scope` must be 'repo' or 'user', got {scope!r}"
        )
    return scope == "repo" or include_user_scope
```

- [ ] **Step 2: Add the Codex dispatch block**

In `materialize()`, after the `vibe_cfg` block, add:

```python
    for codex_key in ("codex", "codex_user"):
        codex_cfg = targets.get(codex_key)
        if not (isinstance(codex_cfg, dict) and codex_cfg.get("config_path")):
            continue
        if not target_in_scope(codex_cfg, include_user_scope):
            results.append(f"skip (user scope) {codex_key}")
            continue
        codex_path = Path(
            os.path.expandvars(os.path.expanduser(str(codex_cfg["config_path"])))
        )
        if not codex_path.is_absolute():
            codex_path = workspace_root / codex_path
        existing_text = (
            codex_path.read_text(encoding="utf-8") if codex_path.exists() else ""
        )
        doc = tomlkit.parse(existing_text)
        apply_codex_mcp(
            doc,
            shared_mcp,
            codex_cfg.get("name_map") or {},
            codex_cfg.get("overrides") or {},
        )
        message, changed = check_or_write_text(
            codex_path, tomlkit.dumps(doc), check=check, dry_run=dry_run
        )
        results.append(message)
        drift_found = drift_found or changed
```

- [ ] **Step 3: Add the Hermes dispatch block**

Immediately after the Codex block:

```python
    for hermes_key in ("hermes_workspace", "hermes_user"):
        hermes_cfg = targets.get(hermes_key)
        if not (isinstance(hermes_cfg, dict) and hermes_cfg.get("config_path")):
            continue
        if not target_in_scope(hermes_cfg, include_user_scope):
            results.append(f"skip (user scope) {hermes_key}")
            continue
        hermes_path = Path(
            os.path.expandvars(os.path.expanduser(str(hermes_cfg["config_path"])))
        )
        if not hermes_path.is_absolute():
            hermes_path = workspace_root / hermes_path
        if not hermes_path.exists():
            results.append(f"skip (absent) {hermes_key}: {hermes_path}")
            continue
        live_pid = hermes_gateway_alive(hermes_path.parent)
        if live_pid is not None and not check:
            results.append(
                f"REFUSED {hermes_key}: gateway PID {live_pid} is live; "
                "stop it and re-run, or the config will be clobbered on shutdown"
            )
            drift_found = True
            continue
        ruamel_yaml = require_module("ruamel.yaml", hermes_key)
        yaml_rt = ruamel_yaml.YAML()
        yaml_rt.preserve_quotes = True
        yaml_rt.width = 4096
        with hermes_path.open("r", encoding="utf-8") as handle:
            data = yaml_rt.load(handle)
        apply_hermes_mcp(
            data,
            shared_mcp,
            hermes_cfg.get("name_map") or {},
            hermes_cfg.get("overrides") or {},
        )
        buffer = io.StringIO()
        yaml_rt.dump(data, buffer)
        message, changed = check_or_write_text(
            hermes_path, buffer.getvalue(), check=check, dry_run=dry_run
        )
        results.append(message)
        drift_found = drift_found or changed
```

Add `import io` to the imports if not already present.

- [ ] **Step 4: Add the CLI flag**

In `main()`, add to the argument parser:

```python
    parser.add_argument(
        "--include-user-scope",
        action="store_true",
        help=(
            "Also write user-scope targets outside the workspace "
            "(~/.codex/config.toml, the AppData Hermes home)."
        ),
    )
```

and pass it through to the `materialize(...)` call:

```python
        include_user_scope=args.include_user_scope,
```

- [ ] **Step 5: Verify nothing regressed**

Run: `C:\Python313\python.exe -m pytest FLOSS/tests/test_shared_agent_surface_mcp.py -v`
Expected: PASS — 19 passed

Run: `C:\Python313\python.exe scripts/materialize_shared_agent_surface.py --dry-run`
Expected: exits 0. Because the manifest has no `codex`/`hermes` blocks yet, the new loops are no-ops.

- [ ] **Step 6: Commit**

```bash
git add scripts/materialize_shared_agent_surface.py
git commit -m "surface: dispatch Codex + Hermes targets with user-scope gating"
```

---

### Task 8: Add the Codex and Hermes manifest blocks

**Files:**
- Modify: `shared-agent-surface.json`

- [ ] **Step 1: Add the four target blocks**

In `shared-agent-surface.json`, inside `"targets"`, add alongside `gemini`/`opencode`/`vibe`:

```json
    "codex": {
      "scope": "repo",
      "config_path": ".codex/config.toml",
      "name_map": {},
      "overrides": {}
    },
    "codex_user": {
      "scope": "user",
      "config_path": "~/.codex/config.toml",
      "name_map": {},
      "overrides": {}
    },
    "hermes_workspace": {
      "scope": "repo",
      "config_path": ".toilet/hermes/config.yaml",
      "name_map": { "agentmemory": "Agent Memory" },
      "overrides": {
        "serena": { "enabled": true, "timeout": 120 },
        "flossiullk-consensus": { "enabled": true, "timeout": 120 },
        "flossiullk-reasoning-ensemble": { "enabled": true, "timeout": 120 }
      }
    },
    "hermes_user": {
      "scope": "user",
      "config_path": "%LOCALAPPDATA%/hermes/config.yaml",
      "name_map": { "agentmemory": "Agent Memory" },
      "overrides": {
        "flossiullk-consensus": { "enabled": true, "timeout": 120 },
        "flossiullk-reasoning-ensemble": { "enabled": true, "timeout": 120 }
      }
    }
```

Bump `manifest_version` from `0.1.4` to `0.2.0`.

- [ ] **Step 2: Validate the manifest parses**

Run: `C:\Python313\python.exe -c "import json;d=json.load(open(r'C:/~shit/FLOSS/shared-agent-surface.json'));print(sorted(d['targets']))"`
Expected: `['codex', 'codex_user', 'gemini', 'hermes_workspace', 'hermes_user', 'opencode', 'vibe']`

- [ ] **Step 3: Dry-run repo scope**

Run: `C:\Python313\python.exe scripts/materialize_shared_agent_surface.py --dry-run`
Expected: exits 0; output includes the `.codex/config.toml` and `.toilet/hermes/config.yaml` targets and `skip (user scope)` lines for `codex_user` and `hermes_user`.

- [ ] **Step 4: Dry-run with user scope**

Run: `C:\Python313\python.exe scripts/materialize_shared_agent_surface.py --dry-run --include-user-scope`
Expected: exits 0; no `skip (user scope)` lines. If the AppData Hermes gateway is live, expect the `REFUSED hermes_user: gateway PID ... is live` line — that is the guard working, not a bug.

- [ ] **Step 5: Commit**

```bash
git add shared-agent-surface.json
git commit -m "surface: register Codex + Hermes MCP targets in the manifest"
```

---

### Task 9: Fidelity gate — the propagator must not revert the 2026-07-24 fixes

This is the acceptance test for the whole effort.

> **Expected-diff allowlist (from Task 6's review).** Two diffs are known-benign and must NOT be treated as gate failures:
>
> - **Hermes `personalities:` block reflow.** ruamel re-emits 8 long strings that another tool wrapped, at different fold points. Cosmetic, confined to content the writer never touches, unavoidable. See Task 7 amendment 7.
> - **Gemini `settings.json` wholesale MCP rewrite.** `.gemini/settings.json` was never migrated — it still carries all four servers as `npx -y januscope@latest`, the full pre-migration state. The propagator correcting it to canonical is the *intended* outcome, not a regression. This surface was discovered during Task 4 and nobody had noticed it was stale.
>
> Everything else — any change to a server's transport, command, or URL in OpenCode, Codex, or Hermes — is a genuine failure of the gate.

**Files:** none modified (verification only).

- [ ] **Step 1: Snapshot the current verified-good configs**

```bash
mkdir -p /tmp/surface-snapshot
cp ../opworkers/opencode.jsonc /tmp/surface-snapshot/
cp ../.codex/config.toml /tmp/surface-snapshot/
cp ../.toilet/hermes/config.yaml /tmp/surface-snapshot/
```

- [ ] **Step 2: Run the propagator for real, repo scope**

Run: `C:\Python313\python.exe scripts/materialize_shared_agent_surface.py`
Expected: exits 0.

- [ ] **Step 3: Diff every managed server against the snapshot**

```bash
diff /tmp/surface-snapshot/opencode.jsonc ../opworkers/opencode.jsonc
diff /tmp/surface-snapshot/config.toml ../.codex/config.toml
diff /tmp/surface-snapshot/config.yaml ../.toilet/hermes/config.yaml
```

Expected: formatting-only differences at most. **Any change to these specific values is a failure** — fix the manifest or `.mcp.json`, restore from snapshot, and re-run:
- consensus → `http://127.0.0.1:7331/mcp`, ensemble → `http://127.0.0.1:7332/mcp`
- Codex uses `type = "streamable_http"` for both
- serena → `januscope --config C:/~shit/.mcp/lenses/serena.yaml`
- agentmemory → `januscope --config C:/~shit/.mcp/lenses/agentmemory.yaml`
- OpenCode keeps `openwork-browser`, `chrome`, `openwork-ui`
- Hermes keeps `docker` and its trailing `fallback_model` comment block

- [ ] **Step 4: Confirm check mode is now clean**

Run: `C:\Python313\python.exe scripts/materialize_shared_agent_surface.py --check`
Expected: exits 0, no drift.

- [ ] **Step 5: Commit any legitimate regenerated output**

```bash
cd C:\~shit
git add .codex/config.toml opworkers/opencode.jsonc
git commit -m "surface: regenerate MCP projections from canonical .mcp.json"
```

(`.toilet/` is gitignored, so it will not appear. The workspace root is a different repo from FLOSS — commit there.)

---

### Task 10: The unified runner

**Files:**
- Create: `scripts/refresh_agent_surfaces.py`
- Create: `tests/test_refresh_agent_surfaces.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_refresh_agent_surfaces.py`:

```python
"""CLI contract tests for scripts/refresh_agent_surfaces.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "refresh_agent_surfaces.py"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_list_names_every_step():
    result = run("--list")
    assert result.returncode == 0
    for name in ("agent-surface", "context", "skill", "agent-memory", "hook", "ai-roster"):
        assert name in result.stdout


def test_only_rejects_unknown_step():
    result = run("--only", "nope")
    assert result.returncode != 0
    assert "nope" in (result.stderr + result.stdout)


def test_dry_run_check_exits_cleanly():
    result = run("--only", "ai-roster", "--dry-run")
    assert result.returncode in (0, 1)
    assert "ai-roster" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Python313\python.exe -m pytest FLOSS/tests/test_refresh_agent_surfaces.py -v`
Expected: FAIL — runner does not exist (`can't open file ... refresh_agent_surfaces.py`)

- [ ] **Step 3: Implement the runner**

Create `scripts/refresh_agent_surfaces.py`:

```python
"""Run every shared-surface materializer in dependency order.

One entry point for regenerating (or verifying) the whole FLOSSI0ULLK agent
surface: MCP registry, context pack, skills, agent memory, hooks, AI roster.

Each step is invoked as a subprocess because every materializer already
exposes the same CLI contract (`--check`, `--dry-run`, `--workspace-root`).
Subprocesses keep the steps independently runnable and stop one failure from
aborting the rest.

Usage:
    python scripts/refresh_agent_surfaces.py                      # regenerate, repo scope
    python scripts/refresh_agent_surfaces.py --check              # verify only, no writes
    python scripts/refresh_agent_surfaces.py --include-user-scope # + user-level configs
    python scripts/refresh_agent_surfaces.py --only skill         # a single step

Exit codes:
    0  every step succeeded with no drift
    1  at least one step failed or reported drift
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

# Order matters: agent-surface owns the MCP registry and the context pack that
# later steps reference.
STEPS: list[tuple[str, str]] = [
    ("agent-surface", "materialize_shared_agent_surface.py"),
    ("context", "materialize_shared_context_surface.py"),
    ("skill", "materialize_shared_skill_surface.py"),
    ("agent-memory", "materialize_shared_agent_memory.py"),
    ("hook", "materialize_shared_hook_surface.py"),
    ("ai-roster", "materialize_shared_ai_roster.py"),
]

# Only the agent-surface materializer understands user-scope targets.
USER_SCOPE_STEPS = {"agent-surface"}


def build_command(
    step_name: str,
    script: str,
    check: bool,
    dry_run: bool,
    include_user_scope: bool,
) -> list[str]:
    command = [sys.executable, str(SCRIPTS_DIR / script)]
    if check:
        command.append("--check")
    if dry_run:
        command.append("--dry-run")
    if include_user_scope and step_name in USER_SCOPE_STEPS:
        command.append("--include-user-scope")
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify without writing.")
    parser.add_argument("--dry-run", action="store_true", help="Report intended writes.")
    parser.add_argument(
        "--include-user-scope",
        action="store_true",
        help="Also write user-level configs outside the workspace.",
    )
    parser.add_argument("--only", help="Run a single step by name.")
    parser.add_argument(
        "--list", action="store_true", help="List step names and exit."
    )
    args = parser.parse_args()

    if args.list:
        for name, script in STEPS:
            print(f"{name:<14} {script}")
        return 0

    steps = STEPS
    if args.only:
        steps = [item for item in STEPS if item[0] == args.only]
        if not steps:
            known = ", ".join(name for name, _ in STEPS)
            parser.error(f"unknown step {args.only!r}; expected one of: {known}")

    outcomes: list[tuple[str, int]] = []
    for name, script in steps:
        command = build_command(
            name, script, args.check, args.dry_run, args.include_user_scope
        )
        print(f"\n=== {name} ===", flush=True)
        completed = subprocess.run(command, check=False)
        outcomes.append((name, completed.returncode))

    print("\n=== summary ===")
    failed = 0
    for name, code in outcomes:
        if code == 0:
            status = "ok"
        elif code == 1:
            status = "DRIFT" if args.check else "FAILED"
        else:
            status = f"FAILED (exit {code})"
        if code != 0:
            failed += 1
        print(f"{name:<14} {status}")

    if failed:
        print(f"\n{failed} of {len(outcomes)} step(s) need attention.")
        return 1
    print(f"\nAll {len(outcomes)} step(s) clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `C:\Python313\python.exe -m pytest FLOSS/tests/test_refresh_agent_surfaces.py -v`
Expected: PASS — 3 passed

- [ ] **Step 5: Run the real thing in check mode**

Run: `C:\Python313\python.exe scripts/refresh_agent_surfaces.py --check`
Expected: a summary table listing all six steps. Investigate any step reporting `DRIFT` or `FAILED` before proceeding.

- [ ] **Step 6: Commit**

```bash
git add scripts/refresh_agent_surfaces.py tests/test_refresh_agent_surfaces.py
git commit -m "surface: add refresh_agent_surfaces.py runner over all materializers"
```

---

### Task 11: Documentation

**Files:**
- Modify: `../.claude/skills/flossi0ullk-shared-surface/SKILL.md`
- Modify: `docs/superpowers/specs/2026-07-24-mcp-surface-propagation-design.md`

- [ ] **Step 1: Update the shared-surface skill**

In `../.claude/skills/flossi0ullk-shared-surface/SKILL.md`, replace the four-line list of individual `materialize_*` commands in "Core workflow" step 2 with:

```markdown
2. Regenerate native views with the single runner:
   - `python FLOSS/scripts/refresh_agent_surfaces.py`
   - `python FLOSS/scripts/refresh_agent_surfaces.py --check` before stopping
   - Add `--include-user-scope` to also write `~/.codex/config.toml` and the
     AppData Hermes home. A live Hermes gateway is refused, not clobbered.
   - Individual materializers still work; `--only <step>` runs just one.
```

Also add to "Rules":

```markdown
- `.mcp.json` is the single source of truth for MCP servers. Never hand-edit a
  harness config (Codex, Hermes, OpenCode, Gemini, Vibe) — change `.mcp.json`
  and re-run the surface runner. Hand-editing is what caused the 2026-07-24
  five-surface drift.
```

- [ ] **Step 2: Flip the spec's Truth Status**

In the spec, change:

```markdown
**Truth Status:** ⚠️ Specified (design approved, not yet implemented)
```

to:

```markdown
**Truth Status:** ✅ Verified — implemented 2026-07-24; unit tests pass, fidelity gate (Task 9) confirmed the propagator reproduces the verified harness configs rather than reverting them.
```

- [ ] **Step 3: Run the full test suite one last time**

Run: `C:\Python313\python.exe -m pytest FLOSS/tests/test_shared_agent_surface_mcp.py FLOSS/tests/test_refresh_agent_surfaces.py -v`
Expected: PASS — 22 passed

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-07-24-mcp-surface-propagation-design.md
git commit -m "docs: mark MCP surface propagation verified"
cd C:\~shit
git add .claude/skills/flossi0ullk-shared-surface/SKILL.md
git commit -m "skill: point shared-surface workflow at the unified runner"
```

---

## Done when

- `python FLOSS/scripts/refresh_agent_surfaces.py --check` exits 0 with all six steps clean.
- 22 unit tests pass.
- Every harness config still matches the 2026-07-24 verified state (Task 9).
- Changing a server in `.mcp.json` and re-running propagates it to Gemini, OpenCode, Vibe, Codex (both layers), and Hermes (both homes) with no hand-editing.
