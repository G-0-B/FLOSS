---
id: project-workflow-branches-unused
type: project
created: '2026-05-25'
status: active
applies_to:
- any-agent
title: Most work lands in the working tree, not branches; root workspace is not under git
---

## What's actually true about the FLOSSI0ULLK git workflow

As of 2026-05-25, surveying the workspace produced these findings — they're load-bearing for any agent trying to figure out "what's the latest work":

- **Root workspace `C:\~shit\` is not a git repo.** `git status` reports "no commits"; every root-level artifact (`.agent-surface/`, root intake drops, `AGENTMEMORY.md`, `INDEX.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, the fresh research drops) is unversioned and recoverable only from the local disk.
- **`FLOSS/` is the git repo**, but most live work happens directly in the working tree rather than on branches. The branch `codex/document-holochain-zomes` is 2+ weeks stale (HEAD `5b5cefd`), identical to `lappytop`, and its name no longer reflects work done on it — the 40 commits ahead of `main` are DeepSource hygiene + consensus-gateway hardening + ADR-9, not zome documentation.
- **The `quirky-mcnulty` worktree under `FLOSS/.claude/worktrees/`** is a goop/image dump (806 files, mostly PNGs in `wtfaimgen/` and a `bash.exe.stackdump`) — not load-bearing for main project work.
- Substrate-level artifacts often live only as untracked working-tree files. As of 2026-05-25 the untracked-but-load-bearing set includes:
  - `ARF/dnas/rose_forest/zomes/consent_{coordinator,integrity}/` — the active consent zome
  - `docs/adr/ADR-12-consent-gate-protocol.md` — claims "locally verified" while its backing code is uncommitted
  - `docs/adr/FLOSSI0ULLK-ADR-Suite-v2.0.md` — the canonical ADR suite
  - `packages/activity_log/` — the U1 metaharness unification module
  - 12+ new architecture docs (CFIS_v0.3, OPERATOR_PRIMER, RUNTIME_SURFACES, STACK_CROSSWALK, META_COORDINATION_KERNEL_v4.0, LIVING_HOLISTIC_VISION, FLOSSI0ULLK-Architecture-Spec-v0.1, INTEGRATION-STATUS)
  - `docs/governance/{ancestry-sweep-v1.0,personal-meta-harness-v1.0}.md`
  - `docs/specs/provenance-packet.{schema.json,spec.md}` and likely `consent-payload.schema.json`

**Why:** Iteration speed. The user works fast across many parallel surfaces and treats branches/commits as friction; the master operational artifact is `FLOSS/docs/research/2026-05-15-working-todo-list.md`, refreshed in place rather than via PRs.

**How to apply going forward:**

- When surveying state, never rely on `git log` alone. Always also walk `find -mtime -N` on the working tree and root, and read the master working-todo-list.
- When the user asks "what's the latest work," check file mtimes and the working-todo-list, not the commit graph.
- Before any `git clean`, `git reset --hard`, or worktree teardown, snapshot untracked files. The ADR-12-backing consent zome lives only in your working tree right now.
- Recommend committing canonical artifacts (ADRs, specs, substrate zomes) the same day they land — even if dev/research code stays loose. Use logical commit clusters so the canon-stabilization commits don't drown in DeepSource churn.
- The named branch `codex/document-holochain-zomes` does not document zomes. Don't trust branch names as task descriptions; trust the working-todo-list.
- The workspace root itself probably wants `git init` + a `.gitignore` for noisy bits (`node_modules`, `.ruff_cache`, `data/state_store.db/`, `.agent-surface/heartbeat/ticks.log`, etc.) so root artifacts get versioning too. This is a workflow-hygiene fix to schedule, not an urgent break.
