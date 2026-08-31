from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

FLOSS_ROOT = Path(__file__).resolve().parents[2]


def load_surface_module():
    if str(FLOSS_ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(FLOSS_ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "shared_agent_surface_under_test",
        FLOSS_ROOT / "scripts" / "materialize_shared_agent_surface.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["shared_agent_surface_under_test"] = module
    spec.loader.exec_module(module)
    return module


def test_vibe_config_exposes_workspace_agent_path_and_default_agent(tmp_path):
    surface = load_surface_module()
    config = surface.build_vibe_config(
        tmp_path,
        {},
        {
            "active_model": "devstral-small",
            "default_agent": "flossi0ullk-align",
            "include_project_context": True,
            "agent_paths": [".vibe/agents"],
        },
    )

    assert 'default_agent = "flossi0ullk-align"' in config
    assert "include_project_context = true" in config
    assert f'agent_paths = ["{(tmp_path / ".vibe/agents").as_posix()}"]' in config


def test_vibe_launcher_seeds_startup_prompt_when_no_prompt_args():
    surface = load_surface_module()
    launcher = surface.build_vibe_launcher(
        {
            "env_path": "FLOSS/.env",
            "startup_prompt_path": ".agent-surface/VIBE_STARTUP.md",
        }
    )

    assert ".agent-surface\\VIBE_STARTUP.md" in launcher
    assert "$hasPromptArg = $false" in launcher
    assert "$argList.Add((Get-Content $startupPromptPath -Raw))" in launcher


def test_vibe_launcher_distinguishes_agent_values_from_prompt_values():
    surface = load_surface_module()
    launcher = surface.build_vibe_launcher({})

    assert '$promptValueOptions = @("-p", "--prompt")' in launcher
    assert (
        '$valueOnlyOptions = @("--agent", "--workdir", "--add-dir", "--max-turns", "--max-price", "--enabled-tools", "--output")'
        in launcher
    )
    assert (
        '$utilityOptions = @("-h", "--help", "-v", "--version", "--setup", "--resume", "-c")'
        in launcher
    )


def test_vibe_startup_prompt_names_current_phase_and_budget_state():
    surface = load_surface_module()
    prompt = surface.build_vibe_startup_prompt(
        {
            "startup_context_pointers": [
                ".agent-surface/context/CONTEXT_L0.md",
                "FLOSS/docs/architecture/OPERATOR_PRIMER.md",
                ".agent-surface/context/RESUMPTION.md",
            ]
        }
    )

    assert "MVP Phase 0 substrate viability is complete" in prompt
    assert "Do not restart old Tryorama/Phase 0 work" in prompt
    assert "heartbeat STOP file is intentionally present" in prompt
    assert "FLOSS/docs/architecture/OPERATOR_PRIMER.md" in prompt


def test_vibe_config_projects_reasoning_ensemble_mcp_with_cold_start_budget(tmp_path):
    surface = load_surface_module()
    config = surface.build_vibe_config(
        tmp_path,
        {
            "flossiullk-reasoning-ensemble": {
                "command": "npx",
                "args": [
                    "-y",
                    "januscope@latest",
                    "--config",
                    "C:/~shit/.mcp/lenses/flossiullk-reasoning-ensemble.yaml",
                ],
            }
        },
        {
            "mcp_servers": ["flossiullk-reasoning-ensemble"],
            "server_overrides": {
                "flossiullk-reasoning-ensemble": {
                    "startup_timeout_sec": 120,
                    "tool_timeout_sec": 420,
                    "sampling_enabled": False,
                }
            },
        },
    )

    assert 'name = "flossiullk-reasoning-ensemble"' in config
    assert "C:/~shit/.mcp/lenses/flossiullk-reasoning-ensemble.yaml" in config
    assert "startup_timeout_sec = 120.0" in config
    assert "tool_timeout_sec = 420.0" in config
    assert "sampling_enabled = false" in config


def test_openwork_instruction_projection_names_shared_packet_and_provenance():
    surface = load_surface_module()
    content = surface.build_opencode_agent_instruction(
        {
            "default_agent": "openwork",
            "agent_description": "OpenWork default FLOSSI0ULLK worker.",
            "startup_context_pointers": [
                ".agent-surface/context/CONTEXT_L0.md",
                ".agent-surface/harness/HARNESS_UPDATE_PACKET.md",
                ".agent-surface/harness/AI_ROSTER.md",
                ".agent-surface/memory/AGENT_MEMORY.md",
                "AGENTMEMORY.md",
            ],
        }
    )

    assert "You are OpenWork" in content
    assert ".agent-surface/harness/HARNESS_UPDATE_PACKET.md" in content
    assert "agentmemory" in content
    assert "provenance packet" in content
    assert "Repository canon wins" in content


def test_umbrella_materializer_refreshes_memory_before_context(tmp_path, monkeypatch):
    surface = load_surface_module()
    workspace = tmp_path
    floss = workspace / "FLOSS"
    floss.mkdir()
    manifest = floss / "shared-agent-surface.json"
    manifest.write_text(
        """
        {
          "manifest_version": "0.1.0",
          "workspace_id": "flossi0ullk",
          "workspace_name": "FLOSSI0ULLK",
          "mcp_source": ".mcp.json",
          "targets": {}
        }
        """,
        encoding="utf-8",
    )
    (workspace / ".mcp.json").write_text('{"mcpServers": {}}\n', encoding="utf-8")

    roster_manifest = floss / "shared-ai-roster-surface.json"
    memory_manifest = floss / "shared-agent-memory-surface.json"
    context_manifest = floss / "shared-context-surface.json"
    for path in (roster_manifest, memory_manifest, context_manifest):
        path.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(surface, "DEFAULT_AI_ROSTER_MANIFEST_PATH", roster_manifest)
    monkeypatch.setattr(surface, "DEFAULT_MEMORY_MANIFEST_PATH", memory_manifest)
    monkeypatch.setattr(surface, "DEFAULT_CONTEXT_MANIFEST_PATH", context_manifest)
    monkeypatch.setattr(
        surface, "DEFAULT_HOOK_MANIFEST_PATH", floss / "missing-hooks.json"
    )
    monkeypatch.setattr(
        surface, "DEFAULT_SKILL_MANIFEST_PATH", floss / "missing-skills.json"
    )

    calls: list[str] = []

    def fake_roster(**_kwargs):
        calls.append("roster")
        return ["OK roster"], False

    def fake_memory(**_kwargs):
        calls.append("memory")
        return ["OK memory"]

    def fake_context(**_kwargs):
        calls.append("context")
        return ["OK context"], False

    monkeypatch.setattr(surface, "materialize_ai_roster_surface", fake_roster)
    monkeypatch.setattr(surface, "materialize_memory_surface", fake_memory)
    monkeypatch.setattr(surface, "materialize_context_surface", fake_context)

    surface.materialize(workspace, manifest, check=False, dry_run=False)

    assert calls == ["roster", "memory", "context"]


def test_doctor_report_summarizes_surface_memory_provenance_and_heartbeat():
    surface = load_surface_module()

    report = surface.build_doctor_report(
        workspace_root=Path("C:/~shit"),
        surface_drift=False,
        roster_summary={
            "provider_count": 12,
            "model_count": 382,
            "mcp_server_count": 11,
        },
        agentmemory_status="healthy",
        heartbeat_stop_present=True,
        audit_counts={"valid": 8, "superseded": 2, "invalid": 1},
    )

    assert "Workspace: `C:/~shit`" in report
    assert "- Shared surface: `clean`" in report
    assert "- agentmemory: `healthy`" in report
    assert "- Heartbeat STOP: `present`" in report
    assert "- Providers: `12`" in report
    assert "- Provenance: `8 valid`, `2 superseded`, `1 invalid`" in report


def _mute_sub_materializers(surface, floss_dir, monkeypatch):
    """Point every optional sub-manifest at a nonexistent path.

    Their real counterparts live in the actual repo (this module is loaded
    from the real `scripts/` dir), which would make them run against a
    workspace_root that doesn't match -- irrelevant noise for guard tests
    that only care about the Hermes dispatch block.
    """
    monkeypatch.setattr(
        surface, "DEFAULT_AI_ROSTER_MANIFEST_PATH", floss_dir / "missing-roster.json"
    )
    monkeypatch.setattr(
        surface, "DEFAULT_MEMORY_MANIFEST_PATH", floss_dir / "missing-memory.json"
    )
    monkeypatch.setattr(
        surface, "DEFAULT_CONTEXT_MANIFEST_PATH", floss_dir / "missing-context.json"
    )
    monkeypatch.setattr(
        surface, "DEFAULT_HOOK_MANIFEST_PATH", floss_dir / "missing-hooks.json"
    )
    monkeypatch.setattr(
        surface, "DEFAULT_SKILL_MANIFEST_PATH", floss_dir / "missing-skills.json"
    )


def test_resolve_dotted_key_handles_nested_and_missing_paths():
    surface = load_surface_module()
    doc = {"approvals": {"mode": "smart"}, "hooks_auto_accept": False}

    assert surface.resolve_dotted_key(doc, "hooks_auto_accept") == (True, False)
    assert surface.resolve_dotted_key(doc, "approvals.mode") == (True, "smart")
    assert surface.resolve_dotted_key(doc, "approvals.cron_mode") == (False, None)
    assert surface.resolve_dotted_key(doc, "missing_top.level") == (False, None)
    # An intermediate segment that is not itself a mapping must not be
    # indexed into -- treated as "not found", not a crash.
    assert surface.resolve_dotted_key(
        {"approvals": "not-a-dict"}, "approvals.mode"
    ) == (False, None)


def test_check_guarded_keys_distinguishes_wrong_value_absent_and_match():
    surface = load_surface_module()
    doc = {
        "hooks_auto_accept": True,  # wrong -- expected False
        "approvals": {"mode": "smart"},  # matches expectation
        # approvals.cron_mode is entirely absent
    }
    guarded_keys = {
        "hooks_auto_accept": False,
        "approvals.mode": "smart",
        "approvals.cron_mode": "deny",
    }

    findings = surface.check_guarded_keys("hermes_user", doc, guarded_keys)

    assert (
        "GUARD DRIFT hermes_user hooks_auto_accept: expected False, found True"
        in findings
    )
    assert (
        "GUARD DRIFT hermes_user approvals.cron_mode: expected 'deny', key is absent"
        in findings
    )
    # A matching key produces no finding at all.
    assert not any("approvals.mode" in line for line in findings)
    assert len(findings) == 2


def test_guard_hermes_config_skips_silently_when_config_missing(tmp_path):
    surface = load_surface_module()
    missing = tmp_path / "does-not-exist" / "config.yaml"

    findings = surface.guard_hermes_config(
        "hermes_user", missing, {"hooks_auto_accept": False}
    )

    assert findings == []


def test_guard_hermes_config_reports_parse_failure_without_raising(tmp_path):
    surface = load_surface_module()
    bad = tmp_path / "config.yaml"
    bad.write_text("hooks_auto_accept: [unterminated\n", encoding="utf-8")

    findings = surface.guard_hermes_config(
        "hermes_user", bad, {"hooks_auto_accept": False}
    )

    assert len(findings) == 1
    assert findings[0].startswith("GUARD DRIFT hermes_user: could not parse")


def test_user_scope_hermes_target_guarded_without_include_user_scope(
    tmp_path, monkeypatch
):
    """The key regression test.

    A `hooks_auto_accept` flip in the user-scope (AppData) Hermes home must
    be caught by a routine repo-scope `--check` -- i.e. WITHOUT passing
    `--include-user-scope`. Scope gating exists to protect *writes* outside
    the repo; a guard check is read-only, so gating it behind the write
    flag would leave exactly the hole that let a real flip go unnoticed.
    """
    surface = load_surface_module()
    workspace = tmp_path
    floss = workspace / "FLOSS"
    floss.mkdir()
    (workspace / ".mcp.json").write_text('{"mcpServers": {}}\n', encoding="utf-8")

    hermes_user_dir = workspace / "fake_appdata_hermes"
    hermes_user_dir.mkdir()
    hermes_user_config = hermes_user_dir / "config.yaml"
    hermes_user_config.write_text(
        "hooks_auto_accept: true\n_config_version: 33\n",
        encoding="utf-8",
    )
    original_bytes = hermes_user_config.read_bytes()

    manifest = floss / "shared-agent-surface.json"
    manifest.write_text(
        json.dumps(
            {
                "manifest_version": "0.1.0",
                "workspace_id": "flossi0ullk",
                "workspace_name": "FLOSSI0ULLK",
                "mcp_source": ".mcp.json",
                "targets": {
                    "hermes_user": {
                        "scope": "user",
                        "config_path": "fake_appdata_hermes/config.yaml",
                        "guarded_keys": {"hooks_auto_accept": False},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    _mute_sub_materializers(surface, floss, monkeypatch)

    # No --include-user-scope: include_user_scope defaults False here, same
    # as a routine `refresh_agent_surfaces.py --check` invocation.
    results, drift_found = surface.materialize(
        workspace, manifest, check=True, dry_run=False, include_user_scope=False
    )

    assert drift_found is True
    assert (
        "GUARD DRIFT hermes_user hooks_auto_accept: expected False, found True"
        in results
    )
    # The write path is still scope-skipped -- guard visibility and write
    # gating are independent.
    assert any(line.startswith("SKIP  hermes_user (user scope") for line in results)
    # Read-only: the guard must never touch the file, drifted or not.
    assert hermes_user_config.read_bytes() == original_bytes


def test_repo_scope_hermes_guard_drift_never_raises_and_leaves_key_untouched(
    tmp_path, monkeypatch
):
    surface = load_surface_module()
    workspace = tmp_path
    floss = workspace / "FLOSS"
    floss.mkdir()
    (workspace / ".mcp.json").write_text('{"mcpServers": {}}\n', encoding="utf-8")

    hermes_dir = workspace / ".toilet" / "hermes"
    hermes_dir.mkdir(parents=True)
    hermes_config = hermes_dir / "config.yaml"
    hermes_config.write_text(
        "hooks_auto_accept: true\nmcp_servers: {}\n",
        encoding="utf-8",
    )

    manifest = floss / "shared-agent-surface.json"
    manifest.write_text(
        json.dumps(
            {
                "manifest_version": "0.1.0",
                "workspace_id": "flossi0ullk",
                "workspace_name": "FLOSSI0ULLK",
                "mcp_source": ".mcp.json",
                "targets": {
                    "hermes_workspace": {
                        "scope": "repo",
                        "config_path": ".toilet/hermes/config.yaml",
                        "guarded_keys": {"hooks_auto_accept": False},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    _mute_sub_materializers(surface, floss, monkeypatch)

    # Must not raise even though this target's write path (mcp merge) also
    # executes in the same run -- the guard finding and the mcp write are
    # independent, and neither should crash the other.
    results, drift_found = surface.materialize(
        workspace, manifest, check=False, dry_run=False, include_user_scope=False
    )

    assert drift_found is True
    assert (
        "GUARD DRIFT hermes_workspace hooks_auto_accept: expected False, found True"
        in results
    )
    # The write path only ever touches `mcp_servers`; the guarded key itself
    # must never be silently reset back to the expected value.
    updated = hermes_config.read_text(encoding="utf-8")
    assert "hooks_auto_accept: true" in updated


# ---------------------------------------------------------------------------
# A client timeout below the server's own work budget fails runs that are
# behaving correctly. Derived from the synthesizer's constants, not typed in,
# so raising a budget cannot silently outgrow the timeouts that wait on it.
# ---------------------------------------------------------------------------


def _reasoning_budget_seconds() -> int:
    if str(FLOSS_ROOT.parent) not in sys.path:
        sys.path.insert(0, str(FLOSS_ROOT.parent))
    from packages.reasoning_ensemble import synthesizer

    # Read the sum from the module that owns the budgets. Re-adding the terms
    # here is what let the Tier-4 logging embed go uncounted: the test agreed
    # with a derivation that was itself missing a step, so it passed while the
    # configured timeout sat 65 seconds under the real path.
    return synthesizer.WORST_CASE_RUN_SECONDS


def _reasoning_timeouts() -> list[tuple[str, int]]:
    surface = json.loads(
        (FLOSS_ROOT / "shared-agent-surface.json").read_text(encoding="utf-8")
    )
    found: list[tuple[str, int]] = []

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "flossiullk-reasoning-ensemble" and isinstance(value, dict):
                    for tkey in ("tool_timeout_sec", "timeout"):
                        if isinstance(value.get(tkey), (int, float)):
                            found.append((f"{path}.{key}.{tkey}", value[tkey]))
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]")

    walk(surface, "surface")
    return found


def test_every_reasoning_ensemble_timeout_clears_the_servers_own_budget():
    """A voter may legitimately take 180s and its embedding another 90s. A 120s
    client timeout fails that run while the server is inside every budget it was
    configured with -- and the operator sees a client error for a working
    server."""
    budget = _reasoning_budget_seconds()
    timeouts = _reasoning_timeouts()

    assert timeouts, "no reasoning-ensemble timeouts found -- has the shape moved?"
    too_small = [(where, value) for where, value in timeouts if value < budget]
    assert not too_small, (
        f"timeout(s) below the {budget}s server budget: {too_small}. "
        "Raise them, or lower the synthesizer's budgets to match."
    )
