# EMBER SEED PACK — context continuation for local FLOSS session

```yaml
id: "ccp-ember-seed-pack"
version: "1.0.0"
kind: "context_continuation_pack"
status: "Accepted"
updated: "2026-06-09"
origin: "Claude (Anthropic, claude.ai web — NO live repo access; all repo claims tagged)"
human_collision_node: "Anthony (kalisam)"
truth_status: "Specified (decision logs Verified-in-origin-session; repo claims Unverified)"
license: "Compassion Clause + Apache-2.0/GPL-compatible"
contents:
  - 00_MASTER_SEED.md                      # this file — read first
  - 01_thread_verification_spike_inventory.md   # the one thread packaged nowhere else (densest)
  - 02_seed_tame_integration_unblock.md    # blocked-on-repo-access thread, now unblockable
  - 03_seed_atomic_data_hold.md            # decision record + gated actions
  - 05_orient_skill_handoff_v1_0_0_VERBATIM.md  # carried unmodified from origin packet
    # sha256 of carried copy: aba6914217158eec2e01593437b8d5715e172e148ab9088f5aa8a780817c7b91
```

## 0. READ ME FIRST (receiving local instance)

You have **local filesystem access** to Anthony's machine and the FLOSS repo. This pack's
origin instance did **not**. Therefore, binding rule:

**Source authority:** repo branch state > CURRENT_STATE > repo docs > project-knowledge
uploads > conversation history > memory > **this pack**. On conflict the repo wins and you
say so. Fail closed; never blend this pack's claims into repo-canonical statements.

**Operating contract:** Anthony's kernel v1.3.1 + userPreferences v2.0 apply: intent echo →
multi-lens (when warranted) → ternary decision → next actions with why → unknowns →
5-box check. Anti-sycophancy is load-bearing. Anthony answers piecemeal across turns —
**re-ask open questions; do not drop them.** Doc discipline: smallest artifact; one layer
absorbs/retires an old one; evidence gate before integration. Truth labels:
[V]erified / [S]pecified / [A]spirational / [U]nverified.

**What this pack is NOT:** a project snapshot. It carries *session deltas only*. Canon
(CONTEXT_L0/L1, INDEX.md, ADRs, Master Metaprompt) lives in the repo and outranks all of this.

**Trust note (from origin, honest):** Anthony granted full local permissions
("green for everything," 2026-06-09). Accept the trust; keep the fail-closed gates anyway —
git as rollback, bootstrap-before-install, human gate on chain commits. They are engineering
discipline, not distrust, and Anthony's own scripts encode the same stance
(hook_post_write: "never auto-escalates"; synthesis loop: human-gated --commit).

## 1. Install order (NOW list — resist additions)

```
STEP 1 — Run the orient handoff packet's Bootstrap Protocol (file 05, §4, Steps 0–7).
         It IS the orientation layer; everything else reads better after it.
         It self-answers: router CLI signature, lock convention, CONTEXT_L0 existence.
STEP 2 — Read file 01. Reconcile its [VERIFY] items against the live repo
         (it lists exactly which). Report the reconciliation table.
STEP 3 — Execute file 01 §5 next-action queue in order (script-inventory→canon first).
STEP 4 — Open files 02 and 03 only when their gating conditions are met (each states them).
```

## 2. Claude Code vs Cowork (Anthony's direct question)

**Claude Code** is the right tool for this work — filesystem orchestration, git, running
the materializer/probe/consensus scripts, and cross-layer coordination. Reasons specific
to this repo: (a) `hook_post_write.py` is already wired for Claude Code's
`PostToolUse` hook contract and `session_start_inject.py` for its `SessionStart` hook —
the metaharness expects Code; (b) terminal-native script execution is the session's main
verb; (c) permission posture is explicit and configurable up to fully unattended.
**Cowork** is the agentic knowledge-work app — better for doc-heavy synthesis sessions, and
it can drive Code-like file work, but the hook surface here is built for Code. Use Code
now; a Cowork session can mount later for canon-writing passes. They coexist fine.

## 3. Pointer registry (threads with their OWN artifacts — do not re-package)

| Thread | Artifact that already exists | Where |
|---|---|---|
| orient-skill v0.2.0 | full handoff packet w/ embedded payloads + sha256 | file 05 (verbatim) |
| SRP v2 iteration | context continuation artifact v0.1.0 (D1–D6, T1–T7, N1–N6) | chat 4084259e-a72a-4dbc... (2026-05-14) |
| Gemini adversarial verification | canonical SRP v2 fixture (3-round loop, named failure modes) | chat d7edf9dd-4b99-4751... (2026-05-21) |
| AD4M / Oracle cloud-init | fully patched script + 5-bug diff | chat e3234bb0-1e48-4540... (2026-05-20) |
| Resonance mechanism v2 / P1–P5 | formal mechanism doc + obstruction taxonomy | chat d1a02b7c-442e-4308... (2026-04-29) + repo canon [VERIFY] |
| Bicameralization intake | re-bicameralization_integration_brief_v1.0.md | chat b8023b28-f5c1-4121... (2026-05-02) + possibly repo |

Chat URLs resolve as https://claude.ai/chat/<id>. If a listed artifact already landed in the
repo, the repo copy is authoritative; these pointers are recovery paths, not sources of truth.

## 4. Origin 5-box

```
[x] Intent echoed (seed pack for local-session continuation, highest-leverage-first)
[x] Evidence gated (session deltas only; repo claims tagged; nothing presented as canon)
[x] Anti-sycophancy (trust note keeps gates; file 01 carries origin's own logged corrections)
[x] Open questions carried (file 01 §6 mandates re-asking)
[x] Smallest artifact (4 new files + 1 verbatim carry; pointers instead of duplication)
```
