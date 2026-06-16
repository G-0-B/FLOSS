---
id: project-root-is-intake-mouth
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_root_is_intake_mouth.md
title: Workspace root is the intake mouth, not an orphan zone
legacy_description: C:\~shit root-level files are NEW material dropped in for digestion
  into research/, never archive
origin_session_id: 7a8fdf1c-cf5f-4d01-a344-82a0dec070b6
---

Files dropped directly into `C:\~shit\` and `C:\~shit\FLOSS\` root are **intake / pre-digestion material**, not stale orphans. The user treats the workspace root as a shared "mouth" where they (and any agentic collaborator) leave things for mutual internalization into the project.

**Why:** User explicitly said "the root folder is our mouth for digestion so to speak... everything in the root is new not to be archived but put into research or current working poop w.e i guess that is what research is." The root is a live intake surface, not debt.

**How to apply:**
- Do NOT flag root `.md` files as "violating the no-top-level docs rule" or suggest moving them to `archive/`.
- The digestion path is: **root → `FLOSS/docs/research/`** (or whichever subdirectory matches: architecture, vision, governance, adr).
- `archive/` is reserved for *superseded* canonical docs (old versions, replaced specs) — raw intake has never been canonical, so it skips archive entirely.
- When surveying, frame root files as "pending intake / digestion queue," not "orphaned / needs triage for removal."
- This applies to both `C:\~shit\` root (workspace intake) and `C:\~shit\FLOSS\` root (project intake). Exception: session/tooling config files (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.mcp.json`, `INDEX.md`) belong at their respective roots by design.
