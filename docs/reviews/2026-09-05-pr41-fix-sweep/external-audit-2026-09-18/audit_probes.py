"""Read-only behavior probes against the immutable PR41 endpoint."""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).parent
REPO = ROOT / "snapshot-303b1f9"
sys.path[:0] = [str(REPO), str(REPO / "scripts")]
from packages.metacoordinator_mcp import voters
from packages.reasoning_ensemble import synthesizer, transport
import materialize_shared_agent_surface as surface
import materialize_shared_hook_surface as hooks
import materialize_shared_skill_surface as skills


def main():
    os.environ.pop("FLOSS_ALLOW_DEGRADED_ROSTER", None)
    os.environ["FLOSS_ENSEMBLE_ONLINE_PROFILE"] = "diverse"
    local = transport.LOCAL_VOTER_POOL
    admitted = {v["voter_id"]: transport._independence_route(v) for v in local}
    survivors = [synthesizer.VoterResponse(
        voter_id=v["voter_id"], model=v["model"], family=v["family"],
        response="A substantive response. Supporting reasoning.", response_hash="h",
        response_embedding=[1.0, 0.0], duration_seconds=0.1,
        transport_name=v["transport"],
    ) for v in local]
    before = voters.roster_independence_problem("diverse", admitted)
    after = synthesizer._survivor_independence_problem(survivors, "mixed")
    print("F1 local-only admission:", before)
    print("F1 same local-only survivors:", repr(after))
    assert before is not None and after is None

    for response, vector in zip(survivors, ([1, 0], [.99, .01], [.97, .03], [-1, 0])):
        response.response_embedding = vector
    online = {"audit-groq": "groq/openai/gpt-oss-120b", "audit-mistral": "mistral/mistral-large-latest"}
    failed_online = [synthesizer.VoterResponse(
        voter_id=name, model=model, family=transport.family_from_model(model),
        response="", response_hash="", response_embedding=None,
        duration_seconds=.1, error="simulated outage", transport_name="litellm",
    ) for name, model in online.items()]
    with patch.dict(os.environ, {"FLOSS_ENSEMBLE_VOTER_MODE": "mixed"}), \
         patch.object(transport, "resolve_default_voter_specs", return_value=online), \
         patch.object(transport, "resolve_embedder", return_value=("audit", lambda _: [1, 0])), \
         patch.object(synthesizer, "dispatch_parallel", return_value=failed_online + survivors), \
         patch.object(synthesizer, "_log_synthesis_action") as log:
        result = synthesizer.synthesize("Audit mixed provider outage", stage_artifact=False)
        print("F1 full synthesize after simulated online outage:", result.tier_classification.tier,
              "success=", log.call_args.kwargs["success"])
        assert result.tier_classification.tier != "degraded"
        assert log.call_args.kwargs["success"] is True

    fixture = ROOT / "probe-hermes"
    fixture.mkdir(exist_ok=True)
    config = fixture / "config.yaml"
    config.write_text("mcp_servers: {}\nhooks: {}\n", encoding="utf-8")
    pid = fixture / "gateway.pid"
    pid.write_text("not json{", encoding="utf-8")
    original = config.read_bytes()
    try:
        result = hooks.apply_yaml_target(config, {"format": "yaml", "hooks": {}}, check=True, dry_run=False)
    except Exception as exc:
        print("F2 YAML --check path:", type(exc).__name__, str(exc))
        assert isinstance(exc, surface.SharedSurfaceError)
    else:
        raise AssertionError(f"Expected the reproduced exception, got {result!r}")
    assert config.read_bytes() == original

    manifest = fixture / "hook-manifest.json"
    manifest.write_text(json.dumps({
        "rules": [], "targets": {
            "hermes": {"enabled": True, "scope": "repo", "format": "yaml",
                       "settings_path": "config.yaml", "hooks": {}},
            "later-target": {"enabled": True, "scope": "repo",
                             "settings_path": "later.json", "hooks": {}},
        },
    }), encoding="utf-8")
    try:
        hooks.materialize(fixture, manifest, fixture / "output", check=True, dry_run=False)
    except surface.SharedSurfaceError as exc:
        print("F2 full hook materialize --check: aborted", type(exc).__name__)
    else:
        raise AssertionError("Expected reproduced full hook materializer abort")

    for payload in (b"[]", b"null", b"\xff"):
        pid.write_bytes(payload)
        try:
            surface.hermes_gateway_alive(fixture)
        except Exception as exc:
            print("LIMIT malformed PID", repr(payload), type(exc).__name__)

    # Preserve the fixture; do not invoke the destructive pruning branch.
    target = ROOT / "probe-skills"
    stale = target / "other-workspace-skill"
    stale.mkdir(parents=True, exist_ok=True)
    (stale / "SKILL.md").write_text("other workspace instructions", encoding="utf-8")
    (stale / skills.MANAGED_MARKER).write_text(json.dumps({
        "managed_by": "FLOSSI0ULLK shared skill surface",
        "manifest_version": "99", "source_path": "Z:/other-workspace/skill-corpus/other-workspace-skill",
        "skill_name": stale.name,
    }), encoding="utf-8")
    print("LIMIT cross-workspace prune plan:", skills.prune_stale_projections(
        "codex", target, set(), check=False, dry_run=True))


if __name__ == "__main__":
    main()
