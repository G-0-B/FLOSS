"""FastMCP server for the FLOSSI0ULLK Reasoning Ensemble (Inline CFIS Router + Synthesizer).

=========================================================================
WHAT THIS IS
=========================================================================
The MCP transport layer exposing the local Router + Synthesizer as
first-class MCP tools. Any MCP-aware client (Claude Code, Codex CLI,
Gemini CLI, OpenCode, future agents) can invoke per-prompt mode
classification + multi-model debate deliberation directly without
shelling out to Python.

=========================================================================
WHY THIS EXISTS
=========================================================================
1. Metaharness unification (`docs/research/2026-05-18-metaharness-
   unification.md`) — every running surface should be invocable through
   the same atomic interface. Shelling out to Python from each agent
   reproduces the doc-explosion pattern at the integration layer.
2. The reasoning ensemble runs locally for cost reasons (token-budget
   discipline per `docs/specs/heartbeat-runtime-budget.spec.md`), but
   client agents are cloud-hosted (Claude Code, Codex, Gemini). The MCP
   transport bridges the locality gap without forcing every client to
   speak Ollama HTTP directly.
3. Working-todo §A.6 gate #4 (MCP wrapper) was the last v0.1 gate for
   the Inline Reasoning Ensemble proposal — this module closes it.

=========================================================================
HOW IT WORKS (high level)
=========================================================================
1. FastMCP framework exposes four functions as MCP tools.
2. Each tool delegates to the actual implementation in `router.py` or
   `synthesizer.py` — this module is pure transport, no business logic.
3. Tool outputs are JSON strings (MCP convention) suitable for any
   client model to parse.
4. Activity-log appending is handled by the underlying modules; this
   server is stateless.

=========================================================================
SPECS, ADRS, AND RELATED RESEARCH
=========================================================================
- Underlying implementations:
  - `FLOSS/packages/reasoning_ensemble/router.py` (mode classifier)
  - `FLOSS/packages/reasoning_ensemble/synthesizer.py` (ensemble executor)
- Pattern reference: `FLOSS/packages/metacoordinator_mcp/server.py`
  (consensus gateway MCP — this server follows the same shape)
- Architecture proposal:
  `docs/research/2026-05-17-inline-reasoning-ensemble.md`
- Unification doctrine:
  `docs/research/2026-05-18-metaharness-unification.md` (single Action
  schema, single activity log, shared invocation convention)
- Decision-grade peer:
  `docs/adr/ADR-MCP-ORCHESTRATOR.md` (ADR-10 — consensus gateway is
  decision-grade routing; this is reasoning-grade routing)
- Consent: `docs/adr/ADR-12-consent-gate-protocol.md` (the MCP tool
  surface is itself a governed pattern at the integrate level)
- Operator guide: `docs/architecture/RUNTIME_SURFACES.md`
- Skill counterpart:
  `FLOSS/skill-corpus/reasoning-ensemble/SKILL.md` (canonical skill
  documenting these tools; materialized to Codex/Claude/Gemini/
  OpenCode views)
- MCP framework: `mcp.server.fastmcp.FastMCP`

=========================================================================

Exposes Router + Synthesizer as MCP tools so any MCP-aware client (Claude Code,
Codex CLI, Gemini CLI, OpenCode, future agents) can invoke per-prompt mode
classification + multi-model debate deliberation directly without shelling out
to Python.

This is gate #5 of working-todo §A.6 v0.2 sequence. Follows the existing
`metacoordinator_mcp/server.py` pattern.

Tools exposed:
  route_prompt(prompt) -> RouterDecision JSON
  deliberate(prompt, force_mode?) -> EnsembleSynthesis JSON (or single-call passthrough)
  get_recent_decisions(limit) -> tail of `.agent-surface/reasoning/activity.jsonl`
  get_ensemble_drafts(limit) -> tail of `.agent-surface/reasoning/ensemble/`

Plane A discipline:
  - No tool writes to canonical surfaces
  - All outputs go to `.agent-surface/reasoning/` for review
  - Activity log appended atomically
  - The consensus gateway is a SEPARATE MCP — this server only handles
    reasoning-grade routing/synthesis. Decision-grade Claims still flow
    through `mcp__flossiullk-consensus__*`.

Usage:
    python -m FLOSS.packages.reasoning_ensemble.mcp_server

Register in `.mcp.json` alongside the consensus gateway:
    "flossiullk-reasoning-ensemble": {
      "command": "python",
      "args": ["-m", "FLOSS.packages.reasoning_ensemble.mcp_server"]
    }

Environment variables (also honored by router.py / synthesizer.py):
    OLLAMA_BASE_URL          default http://127.0.0.1:11434
    FLOSS_ROUTER_MODEL       default phi4-mini:latest
    FLOSS_EMBED_MODEL        default mxbai-embed-large
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Allow running both as a module and as a CLI script
_THIS_DIR = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _THIS_DIR.parents[2]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))

try:
    from FLOSS.packages.reasoning_ensemble.router import classify as router_classify
    from FLOSS.packages.reasoning_ensemble.router import RouterDecision
    from FLOSS.packages.reasoning_ensemble import synthesizer as synthesizer_mod
except ImportError:
    sys.path.insert(0, str(_THIS_DIR.parent.parent))
    from packages.reasoning_ensemble.router import classify as router_classify
    from packages.reasoning_ensemble.router import RouterDecision
    from packages.reasoning_ensemble import synthesizer as synthesizer_mod


REASONING_DIR = _WORKSPACE_ROOT / ".agent-surface" / "reasoning"
ACTIVITY_LOG = REASONING_DIR / "activity.jsonl"
ENSEMBLE_DIR = REASONING_DIR / "ensemble"


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def route_prompt(prompt: str, force_mode: str | None = None) -> str:
    """Classify a prompt into pass_through / single_strong / ensemble mode.

    The Router runs locally (default: phi4-mini via Ollama) at ~10s warm-call.
    Returns JSON with mode, reason, confidence, bias_applied, duration_seconds.

    If force_mode is supplied (one of pass_through, single_strong, ensemble),
    the classifier is bypassed and that mode is returned. Use for --debate
    overrides or user-explicit routing.

    bias_applied="tier4_similarity" means a past Tier-4 divergence on a
    semantically-adjacent prompt forced ensemble mode per Upgrade A in
    2026-05-17-inline-reasoning-ensemble.md §12.2.
    """
    try:
        decision: RouterDecision = router_classify(prompt, force_mode=force_mode)
        from dataclasses import asdict
        return json.dumps(asdict(decision), ensure_ascii=False, indent=2)
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False)


def deliberate(prompt: str, force_mode: str | None = None) -> str:
    """Full reasoning-ensemble deliberation: route + (if ensemble) synthesize.

    For mode=ensemble: dispatches parallel calls to ≥3 diverse voter models,
    embeds responses via mxbai-embed-large, builds similarity matrix,
    runs cluster-based Tier-1/2/4 classification per the v0.2 §12.3 cluster-
    based Tier classification logic, applies the coherence-threshold guard
    for dissent surfacing (Upgrade D §12.5), writes a synthesis draft to
    `.agent-surface/reasoning/ensemble/<ts>_<hash>_synthesis.json`.

    For mode=pass_through or single_strong: the prompt is returned with
    routing metadata. The caller (Claude session, agent) is responsible
    for invoking the chosen mode against its own model surface — this MCP
    only handles ensemble synthesis. Pass-through and single-strong work
    through the caller's normal channels.

    Returns JSON with:
      mode: the routing decision
      tier (if mode=ensemble): tier1 | tier2 | tier4
      synthesis_path (if mode=ensemble): durable draft location
      final_synthesis (if mode=ensemble): readable digest
      router_decision: full RouterDecision JSON
    """
    try:
        # Step 1: Route
        decision: RouterDecision = router_classify(prompt, force_mode=force_mode)
        out = {
            "mode": decision.mode,
            "router_decision": {
                "mode": decision.mode,
                "reason": decision.reason,
                "confidence": decision.confidence,
                "bias_applied": decision.bias_applied,
                "duration_seconds": decision.duration_seconds,
            },
        }

        # Step 2: For ensemble mode, run synthesizer
        if decision.mode == "ensemble":
            synth_result = synthesizer_mod.synthesize(prompt=prompt)
            out["tier"] = synth_result.get("tier")
            out["synthesis_path"] = synth_result.get("synthesis_path")
            out["final_synthesis"] = synth_result.get("final_synthesis")
            out["voter_count"] = synth_result.get("voter_count")
            out["largest_cluster_fraction"] = synth_result.get("largest_cluster_fraction")
            out["minority_coherent_voters"] = synth_result.get("minority_coherent_voters", [])
        else:
            out["note"] = (
                f"mode={decision.mode}: caller invokes their normal model surface; "
                f"this MCP only handles ensemble synthesis. The router decision is "
                f"durably logged at .agent-surface/reasoning/activity.jsonl."
            )

        return json.dumps(out, ensure_ascii=False, indent=2)
    except AttributeError:
        return json.dumps({
            "error": "synthesizer.synthesize() not callable — check FLOSS/packages/reasoning_ensemble/synthesizer.py exposes a synthesize(prompt) function"
        }, ensure_ascii=False)
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False)


def get_recent_decisions(limit: int = 10) -> str:
    """Return the most recent Router decisions from the activity log.

    JSON list, newest first. Useful for cold-start agents to see recent
    routing patterns + Tier-4 divergences (for similarity-bias seeding).
    """
    if not ACTIVITY_LOG.exists():
        return json.dumps([], ensure_ascii=False)
    try:
        lines = ACTIVITY_LOG.read_text(encoding='utf-8').strip().splitlines()
    except OSError as exc:
        return json.dumps({"error": f"activity log read failed: {exc}"}, ensure_ascii=False)
    out = []
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            d = json.loads(line)
            # Strip embeddings to keep response size manageable
            d.pop("prompt_embedding", None)
            out.append(d)
        except json.JSONDecodeError:
            continue
        if len(out) >= limit:
            break
    return json.dumps(out, ensure_ascii=False, indent=2)


def get_ensemble_drafts(limit: int = 5) -> str:
    """Return the most recent ensemble synthesis drafts.

    Each entry has: filename, tier, voter_count, largest_cluster_fraction,
    minority_coherent_count, prompt_preview, final_synthesis_preview.
    Full drafts are at the listed file paths for direct read.
    """
    if not ENSEMBLE_DIR.exists():
        return json.dumps([], ensure_ascii=False)
    files = sorted(ENSEMBLE_DIR.glob("*_synthesis.json"), reverse=True)[:limit]
    out = []
    for f in files:
        try:
            d = json.loads(f.read_text(encoding='utf-8'))
            out.append({
                "filename": f.name,
                "tier": d.get("tier"),
                "voter_count": d.get("voter_count"),
                "largest_cluster_fraction": d.get("largest_cluster_fraction"),
                "minority_coherent_count": len(d.get("minority_coherent_voters", [])),
                "prompt_preview": (d.get("prompt") or "")[:200],
                "final_synthesis_preview": (d.get("final_synthesis") or "")[:500],
                "full_path": str(f.relative_to(_WORKSPACE_ROOT).as_posix()),
            })
        except Exception:  # noqa: BLE001
            continue
    return json.dumps(out, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# MCP server boilerplate (matches metacoordinator_mcp/server.py pattern)
# ---------------------------------------------------------------------------

def _create_mcp():
    """Build the FastMCP app when the optional MCP SDK is available."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        return None

    app = FastMCP("FLOSSI0ULLK Reasoning Ensemble (Inline CFIS Router + Synthesizer)")
    for tool in (
        route_prompt,
        deliberate,
        get_recent_decisions,
        get_ensemble_drafts,
    ):
        app.tool()(tool)
    return app


mcp = _create_mcp()


if __name__ == "__main__":
    if mcp is None:
        raise ImportError("MCP SDK not installed. Run: pip install mcp")
    mcp.run()
