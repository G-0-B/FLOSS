# Documentation Drift Sweep — 2026-07-07

**Auditor:** Hermes (subagent task)
**Scope:** Remaining doc drift across OPERATOR_PRIMER, RUNTIME_SURFACES, CLAUDE.md, GEMINI.md, ADR INDEX vs ADR files. Plus heartbeat `save_daily_state` mid-tick persistence gap analysis + proposed patch.
**Rule:** Analysis only — no commits, no edits to canon files. This report file is the sole artifact.

---

## Part 1 — Heartbeat `save_daily_state` Mid-Tick Persistence Gap

### 1.1 Code Analysis

**File:** `FLOSS/scripts/heartbeat.py` (842 lines)

**`load_daily_state()` (lines 183–194):**
```python
def load_daily_state() -> dict[str, Any]:
    """Track rounds-dispatched-today across heartbeat invocations."""
    state_file = HEARTBEAT_DIR / "daily_state.json"
    today = utc_date()
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            if data.get("date") == today:
                return data
        except Exception:
            pass
    return {"date": today, "rounds_today": 0, "ticks_today": 0}
```

**Date-rollover verification [V]:** The logic at line 190 (`if data.get("date") == today: return data`) correctly falls through to the default `{"date": today, "rounds_today": 0, "ticks_today": 0}` at line 194 when the date changes. **Both** `rounds_today` AND `ticks_today` are reset to 0 on date rollover. ✅ Correct.

**`save_daily_state()` (lines 197–205):** Simple JSON write to `daily_state.json`. No issues in the function itself.

**`run_one_tick()` (lines 700–759) — the gap:**
```
710: daily_state = load_daily_state()
711: daily_state["ticks_today"] = int(daily_state.get("ticks_today", 0)) + 1
...
716-753: for item in rotation:
            run_work_item(item)  ← subprocess calls, potentially long (120s+ timeout)
...
757: save_daily_state(daily_state)  ← ONLY save point
```

**The bug:** `ticks_today` is incremented at line 711 (immediately after load), but `save_daily_state()` is only called once at line 757 (end of tick). If the process is killed mid-tick — SIGTERM, Ctrl-C, OOM kill, power loss — during `run_work_item()` (lines 732, which spawns subprocesses with timeouts up to 120s+), the increment is lost. On restart, `load_daily_state()` reads the stale file and the tick is re-counted from zero.

**Impact assessment:**
- `ticks_today` is used by `get_work_rotation()` (line 713) to vary work selection. Losing the count means the rotation restarts from the same position — work items may repeat or the daily tick budget is undercounted.
- `rounds_today` accumulates inside the loop (line 737–738) and is also only saved at line 757. A mid-tick kill after some work items completed loses all `rounds_today` increments from that tick too, potentially exceeding the daily round cap (`FLOSS_DAILY_ROUND_CAP = 40`) on restart because the cap check reads a stale count.
- **Severity:** Medium. The skill notes a frozen `daily_state.json` date was a real observed symptom (date frozen at 2026-06-14 while ticks continued). The root cause was likely this gap + the daily rollover not triggering because no tick ever completed to save the new date.

**Signal handling context (lines 762–774):**
```python
def install_signal_handlers(state: dict[str, bool]) -> None:
    def _handler(signum: int, _frame: Any) -> None:
        state["stop"] = True
        log_tick_line(f"[signal] received {signum} — graceful shutdown requested")
```
The SIGINT/SIGTERM handler only sets `shutdown_state["stop"] = True` — it does NOT save daily_state. The loop (line 811) checks `shutdown_state["stop"]` between ticks and during sleep, but a signal arriving DURING `run_one_tick()` (inside the `for item in rotation` loop) does not interrupt the current subprocess. The `subprocess.run()` call at line 512 blocks until the child exits or times out. So a SIGTERM mid-tick:
1. Sets `shutdown_state["stop"] = True`
2. The current `run_work_item()` subprocess continues until completion or timeout
3. The `for` loop's `stop_requested()` check (line 719) catches it before the next item
4. `break` exits the loop → falls through to `save_daily_state()` at line 757 → **state IS saved in this case**

**So the SIGTERM-with-graceful-handler path actually saves.** The real risk is:
- **SIGKILL / OOM / power loss / hard crash** — no handler runs, no save.
- **`subprocess.run()` TimeoutExpired** — handled inside `run_work_item()` (never raises), so the loop continues and saves. ✅ Safe.
- **Unhandled exception in `run_one_tick()`** — caught by the loop's `except Exception` at line 822, but `save_daily_state()` at line 757 is skipped because the exception propagates before reaching it. **This IS a gap** — the `daily_state` with the incremented `ticks_today` and any `rounds_today` from completed items is lost.

### 1.2 Proposed Patch (NOT APPLIED — awaiting approval)

The minimal fix is to persist `daily_state` immediately after the `ticks_today` increment at line 711, and also after each `rounds_today` update inside the loop (line 737–738), so partial progress survives any kill mode.

**Proposed diff:**
```diff
--- a/FLOSS/scripts/heartbeat.py
+++ b/FLOSS/scripts/heartbeat.py
@@ -708,6 +708,11 @@ def run_one_tick() -> TickResult:
     daily_state = load_daily_state()
     daily_state["ticks_today"] = int(daily_state.get("ticks_today", 0)) + 1
+    # Persist immediately so a mid-tick kill (SIGKILL/OOM/crash) doesn't
-    # lose the tick count.  The date-rollover reset in load_daily_state()
-    # already produced a clean state dict, so this is safe to write now.
+    save_daily_state(daily_state)
 
     rotation = get_work_rotation(daily_state)
     rounds_dispatched_this_tick = 0
@@ -736,6 +741,11 @@ def run_one_tick() -> TickResult:
         daily_state["rounds_today"] = (
             int(daily_state.get("rounds_today", 0)) + rounds_used
         )
+        # Persist rounds accumulation after each item so partial-tick
+        # progress survives a hard kill before the end-of-tick save.
+        save_daily_state(daily_state)
 
         if result.get("returncode") == 0:
```

**Rationale:** `save_daily_state()` is cheap (single small JSON write, ~200 bytes) and already wrapped in try/except (line 204). Adding 2 calls per tick (1 after increment + N after each work item, typically 3–6 items) is negligible I/O. The end-of-tick save at line 757 remains as the final authoritative write.

**Alternative (lighter touch):** Only add the save after line 711 (the tick increment), not inside the loop. This covers the `ticks_today` gap (the primary concern) but still loses `rounds_today` from completed items on a hard crash. Acceptable if the daily round cap is considered advisory rather than hard.

**Risk of the patch:** None functional. The only behavioral change is that `daily_state.json` is written more frequently. If a concurrent reader reads mid-tick, they see a state with `ticks_today` incremented but `rounds_today` potentially lagging by one item — which is strictly more accurate than the current behavior (which shows the pre-tick state until the tick completes).

---

## Part 2 — Documentation Drift Findings

### 2.1 OPERATOR_PRIMER.md (`FLOSS/docs/architecture/OPERATOR_PRIMER.md`)

| Line(s) | Statement | Status | Notes |
|---|---|---|---|
| 8 | `updated: "2026-05-19"` | **Stale** | File is 171 lines; heartbeat row at line 49 was fixed today (2026-07-07) but the `updated` header was not bumped. Header says 05-19, content references "2026-07-07" in the heartbeat row — internal inconsistency. |
| 46 | "MVP Phase 0 substrate viability \| Verified complete \| DNA/WASM/Tryorama and ontology integrity passed" | **Partially stale** | "Tryorama" is deprecated per operator directive 2026-07-03 (Sweettest replaces JS Tryorama on hc 0.6.1). Should say "Sweettest" or "integration tests". INDEX.md line 42 already carries the Sweettest directive. |
| 47 | "Orchestration substrate bridge \| Specified \| Current proof gate" | **Stale** | This is still listed as "the current proof gate" but ADR-16 (Omnigent execution surface, 2026-06-17) and ADR-17 (KnowledgeTriple contract, 2026-07-04) have shifted the active focus. The "current proof gate" framing pre-dates ADR-13..17. |
| 97 | "Decision history \| `FLOSS/docs/adr/INDEX.md`, ADR-Suite v2.0" | **Stale** | ADR INDEX is now v2.1.0 (2026-07-04), not v2.0. The suite file is still v2.0 but the index has superseded it with ADR-13..17 additions. |
| 160–168 | "Current Best Next Moves — As of 2026-05-19" | **Stale** | Entire section dated 2026-05-19. Lists 5 items that predate ADR-13..17, spec_gate proposal, Sweettest directive, and Fable sprint. Specifically: item 1 ("Implement ADR-12 action-time enforcement") is still valid but incomplete context; item 2 ("Run orchestration substrate-bridge validation") is superseded by ADR-16's framing; items 3–5 are pre-ADR-13..17 priorities. Should be refreshed to reference ADR-17 KnowledgeTriple contract reconciliation as the current high-leverage deliverable, plus spec_gate adoption and Sweettest migration. |
| 6 | `version: "0.1.0"` | **Stale** | Has never been bumped despite the heartbeat row fix and other content changes. Should be 0.2.0 per the drift-audit fix order (step 2: "OPERATOR_PRIMER v0.2"). |

### 2.2 RUNTIME_SURFACES.md (`FLOSS/docs/architecture/RUNTIME_SURFACES.md`)

| Line(s) | Statement | Status | Notes |
|---|---|---|---|
| 8 | `updated: "2026-05-24"` | **Stale** | No content changes since, but the date is 6 weeks old. The file is largely still accurate but doesn't reference ADR-13..17 surfaces (watch architecture, ObjectGraph). |
| — | `loop_stdout.log` reference | **Clean ✅** | No references to `loop_stdout.log` found anywhere in this file. The skill noted this surface is dead since 2026-05-13, and this doc correctly uses `ticks.log` (line 70). No action needed. |
| 94–106 | Token-Budget Rules section | **Mostly current** | Still accurate per heartbeat.py code: `balanced` default, `diverse-max` opt-in, confirm interval, staging cap. No drift detected. |
| 79–90 | Runtime Inventory table | **Stale (missing rows)** | Does not include `watch_intake.py` (the intake watcher, which had the 2026-07-07 storm fix), `process_intake_events.py`, `autonomous_synthesis_loop.py`, or `spec_gate.py`. These are active runtime surfaces per INDEX.md §Metaharness Script Layer. |
| 103 | `FLOSS_HEARTBEAT_CONFIRM_INTERVAL_TICKS = "72"` | **Verify** | The env var name and default should be cross-checked against heartbeat.py constants. Not read in this sweep (out of scope for the listed targets), but flagged for a future audit. |

### 2.3 CLAUDE.md (`C:\~shit\CLAUDE.md`)

| Line(s) | Statement | Status | Notes |
|---|---|---|---|
| 1 | No `updated` header | **N/A** | CLAUDE.md has no YAML frontmatter / version header. Content is from ~2026-05-19 per drift-audit baseline. |
| 79 | "0 — Storage substrate \| ⚠️ Specified — DNA compiles; full Tryorama suite unvalidated" | **Stale** | This contradicts OPERATOR_PRIMER line 46 ("MVP Phase 0 substrate viability \| Verified complete") and CLAUDE.md's own line 109 ("MVP Phase 0 substrate viability is complete"). Internal contradiction within CLAUDE.md itself (line 79 says Specified/unvalidated, line 109 says complete). |
| 98 (GEMINI.md) / 79 (CLAUDE.md) | Layer 0 status | **Contradicts** | CLAUDE.md line 79 says "⚠️ Specified" for Layer 0; GEMINI.md line 98 also says "⚠️ Specified — DNA compiles; full Tryorama suite unvalidated". Both contradict OPERATOR_PRIMER and CLAUDE.md line 107–109. |
| 107–115 | Phase Status section | **Stale** | References "ADR-2 evidence drift" (item 3) as a current focus. Pre-dates ADR-13..17, spec_gate, Sweettest directive, Fable sprint. No mention of ADR-17 KnowledgeTriple contract (the current Phase 1 primary deliverable). |
| 128 | "Voter roster: Cerebras + Groq + Mistral + Flowith (Mistral added in commit b8e34b2)" | **Possibly stale** | Voter roster may have changed. Needs cross-check against current `poll_high_roi_actions.py` / voter config. Not verified in this sweep. |
| 150–154 | "Active Architectural Iteration (n+1 → n+3)" — CCES section | **Stale** | References "n+3" as "current latest". The CCES drops have likely been digested or superseded by ADR-17 and the KnowledgeTriple contract work. This section reads as a snapshot of mid-May thinking. |
| 31 | "Decision history: `FLOSS/docs/adr/INDEX.md` + `FLOSS/docs/adr/FLOSSI0ULLK-ADR-Suite-v2.0.md` (consolidated suite, hand-verified 2026-04-26)" | **Stale** | Does not mention that INDEX.md is now v2.1.0 with ADR-13..17 post-suite additions. Implies the v2.0 suite is the complete set. |
| 136–144 | "Filewatch / Intake Skeleton" | **Stale** | References `process_intake_events.py` but the 2026-07-07 intake-flood fix (1.23M events, watch-overlap storm) is not reflected. The concurrency note ("one writer per surface") is still valid but the storm vulnerability + fix should be noted. |
| — | Missing: spec_gate, Sweettest, Fable sprint, ADR-13..17 | **Structural gap** | CLAUDE.md predates all of these. No mention of: `spec_gate.py` (D7 "−1 layer"), Sweettest replacing Tryorama, claude-fable-5 as current generator model, ADR-13 (yumeichan watch), ADR-14 (ObjectGraph), ADR-15 (provenance enforcement), ADR-16 (omnigent), ADR-17 (KnowledgeTriple contract). |

### 2.4 GEMINI.md (`C:\~shit\GEMINI.md`)

| Line(s) | Statement | Status | Notes |
|---|---|---|---|
| 12 | "Gemini CLI lacks a SessionStart hook (only BeforeTool / AfterTool exist in `.gemini/settings.json` as of 2026-05-26)" | **Stale** | Dated 2026-05-26; Gemini CLI may have added SessionStart since then. Needs verification. |
| 98 | "0 — Storage substrate \| ⚠️ Specified — DNA compiles; full Tryorama suite unvalidated" | **Stale + contradictory** | Same issue as CLAUDE.md line 79. Contradicts the "Phase 0 complete" status. Also uses "Tryorama" which is deprecated (Sweettest directive 2026-07-03). |
| 114–120 | "Phase Status — Current focus is Phase 0 — substrate viability" | **Stale** | Says "current focus is Phase 0" but Phase 0 is complete per OPERATOR_PRIMER and CLAUDE.md. Lists "Rose Forest DNA: ⚠️ DNA compiles; full Tryorama test suite still unvalidated" — this is the pre-completion status. Item 1 is directly contradicted by CLAUDE.md line 109. |
| 120 | "Phase sequence: Foundation → Phase 0 (substrate) → Phase 1" | **Stale** | Phase 0 is complete; this should say "Foundation → ~~Phase 0~~ (complete) → Phase 1 (in flight)". |
| 53 | "Core Specification: `FLOSS/SDD-Master-Spec-0.22.md`" | **Verify** | Need to confirm this spec version is still canonical. Not verified in this sweep. |
| 55 | "Decision history: `FLOSS/docs/adr/INDEX.md` + `FLOSS/docs/adr/FLOSSI0ULLK-ADR-Suite-v2.0.md` (consolidated suite, hand-verified 2026-04-26)" | **Stale** | Same as CLAUDE.md — no mention of v2.1.0 INDEX or ADR-13..17. |
| 135 | "Voter roster: Cerebras + Groq + Mistral + Flowith" | **Possibly stale** | Same as CLAUDE.md — needs cross-check. |
| — | Missing: spec_gate, Sweettest, Fable, ADR-13..17 | **Structural gap** | Same structural gap as CLAUDE.md. GEMINI.md is dated 2026-05-26 and predates all post-suite ADRs. |
| — | Missing: inference posture | **Structural gap** | No mention of claude-fable-5 / Pioneer.ai subscription. The skill notes that "Cowork metaplanner until 2026-06-22" doctrine is superseded (Fable access restored 2026-07-03, Cowork window ended 2026-07). GEMINI.md doesn't carry this stale doctrine (unlike CLAUDE.md per the baseline audit), but it also doesn't carry the current correct posture. |

### 2.5 ADR INDEX vs ADR Files

**`FLOSS/docs/adr/INDEX.md` (v2.1.0, 2026-07-04):**

| Check | Result |
|---|---|
| ADR-13 in index? | ✅ Yes (line 40) — `ADR-13-yumeichan-watch-architecture.md` |
| ADR-14 in index? | ✅ Yes (line 41) — `ADR-14-objectgraph-projection.md` |
| ADR-15 in index? | ✅ Yes (line 42) — `ADR-15-provenance-validation-enforcement.md` |
| ADR-16 in index? | ✅ Yes (line 43) — `ADR-16-omnigent-execution-surface.md` |
| ADR-17 in index? | ✅ Yes (line 44) — `ADR-17-knowledge-triple-contract-reconciliation.md` |
| All files exist on disk? | ✅ Yes — all 5 ADR files present in `FLOSS/docs/adr/` (verified via directory listing) |
| Filenames match index? | ✅ Yes — all 5 filenames in index match actual files on disk |
| ADR-0 through ADR-12 complete? | ✅ Yes — all present in both index and directory |

**INDEX completeness verdict: ✅ CLEAN.** The v2.1.0 index is complete and consistent with the ADR directory. ADR-16 is present (was previously missing per the drift-audit baseline — now fixed). No drift detected between INDEX.md and the ADR files.

**Minor INDEX notes (not drift, but worth flagging):**
- Line 3: `Version: 2.1.0` / Line 4: `Updated: 2026-07-04` — these are current and consistent.
- Line 6: References `FLOSSI0ULLK-ADR-Suite-v2.0.md` as "canonical reference" but the index itself now supersedes the suite for ADR-13..17. This is documented correctly ("This index is the pointer surface kept in sync with the suite plus any post-suite additions").
- The `FLOSSI0ULLK-ADR-Suite-v2.0.md` file (50KB, dated 2026-04-26) has NOT been updated to include ADR-13..17. This is by design (the index carries post-suite additions), but it means the suite file alone is incomplete. CLAUDE.md and GEMINI.md still point to the suite as if it were complete — that's the drift (see §2.3/§2.4).

---

## Part 3 — Cross-File Contradiction Summary

| Contradiction | Files | Resolution Direction |
|---|---|---|
| Layer 0 / Phase 0 status | CLAUDE.md L79 ("⚠️ Specified"), GEMINI.md L98 ("⚠️ Specified") vs OPERATOR_PRIMER L46 ("✅ Verified complete"), CLAUDE.md L109 ("complete") | OPERATOR_PRIMER is correct (MVP_PLAN.md verified). CLAUDE.md L79 and GEMINI.md L98 are stale. |
| "Tryorama" references | OPERATOR_PRIMER L46, CLAUDE.md L79/98, GEMINI.md L98/116 | Sweettest directive 2026-07-03 replaces JS Tryorama. All "Tryorama" references in current-status contexts should say "Sweettest" or "integration tests". |
| ADR suite completeness | CLAUDE.md L31, GEMINI.md L55 (point to v2.0 suite as complete) vs INDEX.md v2.1.0 | INDEX.md is the current surface. Suite file is intentionally frozen at v2.0; CLAUDE.md/GEMINI.md should note the index supersedes for ADR-13..17. |
| "Current Best Next Moves" | OPERATOR_PRIMER L160–168 (dated 2026-05-19) | Superseded by ADR-17 KnowledgeTriple contract + spec_gate adoption + Sweettest migration as current priorities. |

---

## Part 4 — Recommended Fix Order (smallest-artifact, no canon edits yet)

1. **Heartbeat persistence patch** (Part 1.2) — runtime correctness first. Requires approval before applying.
2. **OPERATOR_PRIMER v0.2**: bump `updated` to 2026-07-07, `version` to 0.2.0; replace "Tryorama" → "Sweettest" in L46; refresh "Current Best Next Moves" (L160–168) to reference ADR-17, spec_gate, Sweettest; update "ADR-Suite v2.0" → "ADR INDEX v2.1.0" at L97.
3. **CLAUDE.md refresh**: fix Layer 0 status contradiction (L79 → "✅ Verified complete"); add ADR-13..17, spec_gate, Sweettest, Fable/inference posture; update Phase Status (L107–115) to Phase 1 focus.
4. **GEMINI.md refresh**: same as CLAUDE.md; additionally fix "current focus is Phase 0" (L114) → "Phase 0 complete, Phase 1 in flight"; update Phase sequence (L120).
5. **RUNTIME_SURFACES.md**: add missing rows to Runtime Inventory (watch_intake, process_intake, autonomous_synthesis, spec_gate); bump `updated` date.

**No canon files were edited in this sweep.** This report is the sole artifact.
