---
id: project-vibe-alignment
type: project
created: '2026-05-19'
status: active
applies_to:
- any-agent
source: codex_session
title: Mistral Vibe now has a generated FLOSSI0ULLK alignment path
---

Mistral Vibe drifted because its default session could start from project context
without being forced through the generated shared context and current runtime
state. A captured Vibe response now stored at
`FLOSS/docs/research/intake_raw/2026-05-19-root/reports/Vibe.txt` still leaned
toward old Phase 0/Tryorama framing.

As of 2026-05-19, Vibe is aligned through the shared agent surface:

- Canonical source: `FLOSS/shared-agent-surface.json` `targets.vibe`
- Materializer: `FLOSS/scripts/materialize_shared_agent_surface.py`
- Generated config: `.vibe/config.toml`
- Generated default agent: `.vibe/agents/flossi0ullk-align.toml`
- Generated startup prompt: `.agent-surface/VIBE_STARTUP.md`
- Launcher: `vibe-floss.ps1`

Current generated posture:

- `default_agent = "flossi0ullk-align"`
- `agent_paths = ["C:/~shit/.vibe/agents"]`
- startup prompt is injected by `vibe-floss.ps1` when a new interactive session
  starts without an explicit prompt/resume/help/version command
- startup prompt tells Vibe to read `CONTEXT_L0.md`, `RESUMPTION.md`,
  `AGENT_MEMORY.md`, `CONTEXT_POINTERS.md`, runtime-budget spec, substrate-bridge
  spec, and working todo before proposing work

Hard corrections the Vibe path must preserve:

- MVP Phase 0 substrate viability is complete; do not restart old Tryorama/Phase
  0 work unless explicitly auditing evidence drift.
- Current gate is orchestration substrate-bridge validation plus Phase 1
  KnowledgeTriple/MVC work.
- Heartbeat STOP is intentionally present after the 2026-05-19 Groq token-burn
  fix; routine background consensus uses `balanced`, not `diverse-max`.
- SDD discipline applies to Vibe too: spec first, tests before behavior changes,
  and generated projections come from canonical manifests.

Verification at landing:

- `python -m pytest scripts\tests\test_shared_agent_surface.py scripts\tests\test_shared_agent_memory.py scripts\tests\test_heartbeat_budget.py -q` => 13 passed
- `python FLOSS\scripts\materialize_shared_agent_surface.py --workspace-root C:\~shit --check` => all Vibe/shared projections OK
- `powershell -ExecutionPolicy Bypass -File .\vibe-floss.ps1 --help` => help prints cleanly
- `powershell -ExecutionPolicy Bypass -File .\vibe-floss.ps1 --version` => `vibe 2.10.0`
