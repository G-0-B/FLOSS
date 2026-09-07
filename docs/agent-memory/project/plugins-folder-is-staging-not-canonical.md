---
id: project-plugins-folder-is-staging-not-canonical
type: project
created: '2026-07-25'
status: active
applies_to:
- any-agent
source: operator_correction
title: plugins/ at workspace root is a staging area, not canonical surface
---

`C:\~shit\plugins\` is a **holding area for plugins, skills, and packages the operator is checking out, evaluating, or installing**. It is not a canonical project surface and nothing in it should be treated as authoritative, wired into the shared agent surface, or materialized outward unless it is first promoted into the proper canonical location.

**Why:** operator correction, 2026-07-25. An agent could easily mistake its contents for project structure — it currently holds zips and unpacked trees (`agentmemory-0.9.28`, `context_fields`, `codex-claude-gemini-bridge`, `science-skills`, `holochain-agent-skill-0.2.0.zip`, and others) that look like first-class components but are staged material.

Specifically: `plugins/agentmemory-0.9.28/` was placed there solely to get the **Hermes memory integration** installed. It is not a second agentmemory deployment and is not the canonical agentmemory surface — see [[project-agentmemory-running]] for the live one.

**How to apply:**
- Do not cite anything under `plugins/` as project architecture or canon.
- Do not add `plugins/` paths to manifests, MCP configs, or the shared surface.
- Skills that live only under `plugins/` are candidates for promotion into `FLOSS/skill-corpus/` (the canonical skill source) — but promotion is an explicit act, not an assumption.
- This is distinct from the intake-mouth convention for the workspace root itself (see [[project-root-is-intake-mouth]]): root drops are material awaiting digestion into `FLOSS/docs/…`, whereas `plugins/` is a tool/package staging shelf that may never be digested at all.
