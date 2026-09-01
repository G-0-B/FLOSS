# Re-Orientation Delta — 2026-08-30

**Supersedes the operational content of:** `flossioullk-context-continuation-seed-2026-06-20.md`, `yumeichan-heartbeat-bridge-local-implementation-packet-2026-06-20.md`, `agent-handoff-immediate-work-2026-06-20.md`, `yumeichan-v0-1-steward-task-packet-2026-06-20.md`
**Status:** ⚠️ Specified — read-only live-repo survey performed 2026-08-30. Repo state is authoritative over this file; this file is authoritative over the 2026-06-20 artifact set.
**Type:** Re-orientation delta. Comparison + correction only. No canon promotion, no new architecture, no new work track.

## 0. Headline

The 2026-06-20 artifact set is **historical**. Roughly ten weeks of real work landed since. Three of its four load-bearing assumptions were falsified by the live repo.

Notably: the heartbeat-bridge packet was itself ingested into the repo at
`FLOSS/docs/research/intake_raw/2026-07-07-root/reports/yumeichan-heartbeat-bridge-local-implementation-packet-2026-06-20.md`,
classified **non-canon, truth-status `U`**, annotated *"repo wins on conflict,"* and **never implemented**. That was the correct disposition under FLOSSI0ULLK's own source-authority rule. This delta does not re-litigate it.

## 1. Assumption corrections

| Prior assumption (2026-06-20) | Live reality (2026-08-30) | Verdict |
|---|---|---|
| Heartbeat stopped, STOP file present | No STOP file anywhere. Resumed **2026-05-26** after 5/5 spec↔code budget reconciliation. Last tick **2026-08-30T03:45:38** — today | ❌ Falsified |
| PR #38 open, awaiting merge | **Merged to `main` 2026-08-19 (`873cc0c`)**, alongside PR37/32/30. Successor **PR #41** (`reconcile/pr38-salvage-20260817`, 368 files) is now the dominant blocker; **PR #43** split out 2026-08-21 | ❌ Falsified (shape survives, moved downstream) |
| ADR-15 provenance/author binding specified but NOT enforced in code | **Enforced.** `validate()` destructures the action and threads `&action.author`; no `..`-discard arm; `E_BUDGET_AUTHOR` / `E_THOUGHT_PROVENANCE` / `E_TRIPLE_SOURCE` all reject mismatch; ~12 named unit tests. Header: `✅ Verified at unit level: R2–R4 implemented and tested` | ❌ Falsified |
| No Yumeichan implementation exists | Substantially correct. ADR-13 `⚠️ Specified`, no end-to-end impl. One real artifact exists: `FLOSS/scripts/yumeichan_watch_capabilities.py` (capability-token validator, schema + analog bounds + TTL) | ✅ Broadly held |

**Residual caveats on ADR-15 — do not over-claim it as closed:**
- Enforcement proven at **unit level only**. Two-agent conductor/Tryorama proof and **R5** (analog `i8`→`f32` migration) remain deferred.
- Working-todo §A.000000 P1 item 6 **still lists ADR-15 `BudgetEntry` unconditional `Ok(Valid)` as open**. That todo line is stale and contradicts the code. The code is right; the todo needs correcting.

## 2. My own prior recommendation now conflicts with accepted canon

Flagging this against my own earlier advice, because it matters more than the stale dates.

I proposed **Yumeichan as the always-on meta-steward / conductor / dispatcher** — the orchestration brain.

**ADR-13 (Accepted, 2026-06-13)** defines the Yumeichan watch as a **"Thin Capability Client and Sensory Edge," explicitly *not* an inference node.**

These are incompatible framings for the same name. Meanwhile the *actual* orchestration substrate that got built carries different names entirely:

- **coordination room** — `packages/coordination_room/`, spec created **2026-08-30 (today)**, file-claim MCP router on `127.0.0.1:7334`, tools `room_claim|room_release|room_state|room_broadcast|room_read`
- **OmniRoute inference plane + MCP daemon migration** — ADR-19, `:20128`, Truth Status **Verified** (Stages 0–3.5 implemented + tested, equivalence run closed 2026-07-26)
- **computer-use gateway** — `docs/specs/computer-use-gateway.spec.md`, created 2026-08-25, `SendInput` **default-deny**, currently killed on `:7333`

**Recommendation:** retire "Yumeichan" as the label for the meta-orchestrator role. It is already taken by an Accepted ADR for a narrower sensory-edge component. The orchestrator role is being filled by coordination-room + OmniRoute + MCP daemons. Use those names; keep Yumeichan scoped to ADR-13. If a steward/persona layer is still wanted on top, it needs a distinct name and its own ADR rather than colliding with ADR-13.

## 3. What actually landed since 2026-06-20

**Three new ADRs (none existed before):**

| ADR | Subject | Status |
|---|---|---|
| **ADR-18** | Prior-Art & Reuse Gate (`before_build_check`, enforced) | Accepted 2026-07-16 (shape B+C, 120-day window); `--check` enforcement Verified on landing |
| **ADR-19** | OmniRoute Inference Plane + MCP Daemon Migration | Accepted (operator-consented, **consensus-pending**), Blast Radius **System**, Truth Status **Verified**. Consensus ratification **deferred until ADR-12 consent gate exists** |
| **ADR-20** | Provenance Validator Reconciliation — evidence vocabulary drift + ancestor supersession | Accepted 2026-08-24. D-A1 + D-B3 implemented, **D-B1 unbuilt**. Blast radius **reclassified System → Substrate on 2026-08-25** after external meta-audit |

**ADR-20 carries the biggest single operational win:** the hook now lands claims — *"the first claim to land in the pilot's history."* The provenance spine had never landed one since 2026-08-10. 267 tests pass.

**New specs:** `provenance-anchor.spec.md`, `computer-use-gateway.spec.md`, `coordination-room.spec.md`, `reuse-gate.spec.md`; amendments to `provenance-packet.spec.md` (2026-08-25) and `budget-entry.spec.md` (v1.1.0).

**New packages:** `coordination_room/`, `computer_use_gateway/`, `activity_log/provenance.py`, `mcp_daemon.py`, `reasoning_ensemble/synthesizer.py`.

**New scripts:** `refresh_agent_surfaces.py`, `research_log.py`, `spec_gate.py`, `start_/stop_mcp_daemons.ps1`, `sweep_mcp_orphans.ps1`, plus a `scripts/tests/` suite.

**Live services:** consensus `:7331`, ensemble `:7332`, computer-use `:7333` (killed), coordination-room `:7334`, OmniRoute `:20128`, agentmemory `:3111` / viewer `:3113`.

**Working todo** now opens with a new **Section 0 — Active Work Board**, added 2026-08-18 because *"the operator works across several harnesses… and loses track of what is mid-flight."* Last refreshed **2026-08-21**.

## 4. Growth is real but unevenly reconciled

The honest shape is **capability up, orientation surfaces behind, several self-reported partial failures**:

- `provenance-anchor.spec.md` self-reports: **"CORRECTION 2026-08-29 — half of this mechanism does not work."** ADR-18 tier-2 review outcome: **REVISION REQUIRED**. Measured 2026-08-25: *96 of 99 identities are single-packet.*
- Provenance audit still failing at scale: `E_PROVENANCE_CHAIN_GAP:36,37,39`.
- Consensus/ensemble MCP handshakes still failing per `.remember/remember.md` — *"do not pile on."*
- Heartbeat is **alive but shallow**: current ticks are `[ok] probe 0.1s` only, not the old poll/synthesis rotation. `daily_state.json` frozen at **2026-07-29**.

## 5. Orientation drift — the recurring named defect

This is the pattern worth naming, because it has now recurred and widened:

| Surface | State |
|---|---|
| `INDEX.md` | Last updated **2026-08-12**; canonical table stops at **ADR-17** — ADR-18/19/20 have **no rows**. Directory map missing `coordination_room`, `computer_use_gateway`, `activity_log`; still claims "31 scripts" |
| `CLAUDE.md` (root) | No "Last updated" line; content runs to ~2026-07-08; Phase Status names ADR-13..17 only |
| `FLOSS/CLAUDE.md` | Fresher — knows ADR-13..19, but **not ADR-20** |
| `.agent-surface/context/CONTEXT_L0.md` | Exists, manifest `0.3.0`, but carries **no generation timestamp at all**; content ~2026-08-10/12 → **~3 weeks stale**. Working-todo row 0.11 independently confirms materializer DRIFT |
| `docs/agent-memory/project/heartbeat-running.md` | Still asserts *"STOP is present"* and warns against removing it — **3 months stale**, actively misleading |

Also: ~10 stale worktree snapshot capsules at workspace root (`_pr43/`, `_dep46/`, `_codex_pr38_cleanup/`, …), each with a full `docs/adr/` stopping at ADR-17. **Do not read these as current state.** Any agent globbing the workspace root will hit them.

## 6. Real current priorities (replaces my 2026-06-20 NOW queue)

Sourced from the live working-todo Section 0 and the triage findings — not from my prior planning.

**P0 — security, still open:**
1. **Rotate the `ow_mcp_at_…` bearer token** in `opencode.jsonc:22`
2. **Rotate six provider keys** in `.hermes/plans/artifacts/omni-providers-before.json`

**P1 — integrity holes with named root causes:**
3. **`_AUDIT_SINK` never read** → *every consensus MCP invocation bypasses the audit trail.* Directly undermines the ADR-15/ADR-20 provenance thread; a provenance spine that isn't recording consensus calls is not a spine.
4. **`stop_mcp_daemons.ps1:19` assigns to read-only `$PID`** → the script never actually stops the daemons. Silent no-op on the intended kill path.
5. **Row 0.12 "armed footgun"** — hook-surface split-brain: live projections v0.2.0, FLOSS tree v0.1.0. Running `refresh_agent_surfaces.py` **without `--check`** wipes the 12 agentmemory hooks. Treat `--check` as mandatory until reconciled.

**P1 — dominant blocker:**
6. **PR #41 reconciliation review backlog** — ~2 months of accumulated work, 368 files, 27 triaged inline comments. Named "the dominant blocker" in the working todo.

**P2 — correctness / hygiene:**
7. Row 0.6: *"independence is policy, not enforcement"* — a degraded `balanced` profile (2 voters, 1 surface) voted and **nothing detected it**
8. Row 0.8: `mem::compress` failing **100%** (192 calls, 192 failures)
9. Row 0.11: context + agent-surface materializer drift (`--check` reports DRIFT on 2 of 6 steps)
10. Row 0.13: `jsonschema` undeclared in `ARF/requirements.txt`

**P2 — reconcile the stale surfaces named in §5:**
11. Add ADR-18/19/20 rows to `INDEX.md`; refresh its package list and script count
12. Correct `heartbeat-running.md` (STOP was removed 2026-05-26)
13. Correct working-todo §A.000000 P1 item 6 (ADR-15 `BudgetEntry` is enforced, not open)
14. Add a generation timestamp to `CONTEXT_L0.md` output so staleness is visible rather than inferred

## 7. Still-valid decisions from the earlier sessions

These were not falsified and carry forward:

- **Quests = cockpit / app forge, not trust substrate.** Unchanged.
- **OpenHuman = sovereign private-context layer; consented purpose-bound capsules only, never raw memory sync.** Unchanged.
- **Omnigent stays a WSL2/Docker execution enclave, not the Windows-native backbone.** Reinforced — the native orchestration plane that actually got built (OmniRoute + MCP daemons + coordination room) is exactly the Option-B "use what we have" path.
- **Permeable shells = glossary/narrative; no shell infrastructure.** Unchanged.
- **Reject "candidate ASI architecture" framing** per `2026-06-20-deepmind-asi-crosswalk-delta.md` §3. Unchanged and, given §4's partial-failure reports, more clearly correct.

## 8. Guidance for the next agent

1. **Do not read the 2026-06-20 artifact set as current.** Start here, then verify against live repo.
2. **Do not read workspace-root `_*/` snapshot capsules as current.** They stop at ADR-17.
3. **Do not trust `INDEX.md`, root `CLAUDE.md`, `CONTEXT_L0.md`, or `heartbeat-running.md` for recency.** All are stale by 3 weeks to 3 months in specific, documented ways.
4. **Do not run `refresh_agent_surfaces.py` without `--check`.**
5. **Do not "restore the heartbeat."** It is running. If it looks wrong, the issue is depth (probe-only) and `daily_state.json` staleness, not a STOP file.
6. **Do not pile onto the consensus/ensemble handshake failure** — explicitly flagged in `.remember/remember.md`.
7. Prefer **reconciliation over new construction.** The measured pattern here is capability outrunning its own orientation surfaces; adding surfaces makes that worse, correcting them makes it better.

## 10. Atlas cross-check (added 2026-08-30, source dated 2026-08-23)

Source: `2026-08-23-flossi0ullk-repo-atlas` — a 10-file, SHA-256-sealed structural census of `G-0-B/FLOSS` at commit `db80571ddd29f8a5e76dd5121e667d1dd322db67`, anchored to **PR #41** head branch `reconcile/pr38-salvage-20260817`. Self-labeled *"noncanonical generated projection,"* `schema_version 0.2.0`, generated `2026-08-23T18:14:06-04:00`.

**It predates this survey by 7 days and is formally stale by its own criteria.** `PROVENANCE.md` lists 8 revalidation triggers; **three have fired**: PR41 head/state moved, the tracked path set changed, and the ADR index changed. Its own instruction: *"Do not patch TSV rows by intuition. Re-materialize and rerun full validation."*

**Its scope is narrower than it first appears.** Inventories derive only from the immutable Git commit object, not the working checkout. Explicitly excluded: `.agent-surface/`, `.toilet/`, `_reference/`, root intake, untracked files, private runtime state. It ran **zero tests** — *"No repository Python, Rust, TypeScript, Worker, Holochain, or integration test suite was run."* So it is authoritative on *what exists, where, how big, who owns it*, and silent on *whether any of it works*.

### 10.1 🔴 NEW P0 — committed credential, and a second-order leak

Not in my survey. Two archived files share **one identical blob** `f4beee025a6a00eb0441f6c976e361990588afd4` (291 bytes each):

- `archive/bolt_snapshot_5_4/project/.env`
- `archive/old_project/.env`

Both contain a **live-form Supabase anon JWT** (`VITE_SUPABASE_ANON_KEY`). Decoded payload references project ref `cprppkgapugpuhlyrnsw`, role `anon`, `exp` ≈ 2035. **This is committed to Git history**, so rotation alone is insufficient — the blob persists in history unless purged.

**Second-order leak:** the atlas's own `FILE_INVENTORY.tsv` reproduces the **complete token verbatim** at lines 370 and 476, as the "summary" field for those two paths. So the credential now also exists in an unencrypted TSV outside Git. The atlas does not flag this. Its `PLAN.md` lists *"credential/formula/control-character safety checks"* only as a requirement for a **future** materializer (⚠️ *"Specified, not implemented"*) — this run validated formula-injection and control-chars at 0, but had **no credential redaction**. Meanwhile `context-domains.json` declares the `agent-memory` hard stop: *"Never store secrets or unredacted credentials."* Self-inconsistent.

**Actions:**
1. Revoke/rotate the Supabase anon key for project `cprppkgapugpuhlyrnsw`.
2. Treat the Git blob as permanently exposed unless history is purged; decide purge vs. rotate-and-accept.
3. **Do not copy `FILE_INVENTORY.tsv` into any project, repo, or shared surface** — it carries the plaintext token.
4. Add credential redaction to the atlas materializer **before** it is ever automated (already in its own requirements list — treat as blocking, not optional).
5. Note this is a *third* credential exposure alongside the `ow_mcp_at_…` token and the six provider keys in §6 P0. Three independent exposures is a pattern, not an incident — a repo-wide secret scan is warranted.

### 10.2 Correction to my own ADR-15 claim

I wrote in §1 that ADR-15 is *"proven at unit level only."* The atlas shows that is too strong.

`ARF/tests/tryorama/provenance_validation.test.ts` (3,205 B) **exists in the tree**, and its extracted first line reads: *"Coordinator stamps provenance = alice; the integrity zome's R3 check."* That is an integration/conductor-level test of exactly the binding ADR-15 specifies.

**But the atlas ran nothing**, so there is no evidence it passes or is wired into CI. Corrected status:

> An integration-level Tryorama test for ADR-15 R3 **exists**. Its pass/CI status is **Unverified**. The gap is not "no integration test written" — it is "integration test written, execution status unknown." Check CI wiring before either claiming or dismissing coverage.

Supporting: `docs/specs/integrity-provenance-validation.spec.md` (5,947 B). In the atlas's `provenance` share set, ADR-15 sits in `expand`, not `start`.

### 10.3 Two drift findings the atlas has and I did not

**Serena drift — the atlas's most-repeated finding** (all 5 Markdown files + `context-domains.json` ×2 + 2 TSV rows). `.serena/project.yml` (10,358 B, **added in PR41**) is tracked, and `shared-context-surface.json` still advertises a `serena-memory` corpus — *"despite the operator reporting Serena was never adopted."* Labeled *"documented drift, not verified capability."* Deliberately **retained, not fixed**, since deletion and shared-surface edits carry separate approval. `PROVENANCE.md`: *"The Serena contradiction remains unresolved."*

This matters beyond Serena: `CONTEXT_L0.md`'s route order (which I quoted in the earlier survey) **includes `serena-memory` as a lane**. If Serena was never adopted, that lane is routing to nothing. Same class as `installation-not-adoption.md`, an existing agent-memory note — and the same class as the reuse-ledger's own 2026-05-19 correction demoting `holochain-agent-skill` from adopt→investigate for exactly this reason. Third instance of one recurring defect.

**Kernel version-label drift** (flagged 4× in the atlas). `FLOSSI0ULLK_Master_Metaprompt_v1_4_0_Kernel.md`, blob `bb1b32fb…`, 14,255 B: *"Filename labels the kernel v1.4.0, but the immutable snapshot blob's first heading still says v1.3.1."* An uncommitted worktree fix exists but was excluded from the snapshot. Since the kernel is the top-of-authority document, a version-label mismatch on it is worth closing cheaply.

### 10.4 Structural numbers (the atlas's real contribution)

Validator exit `0`; 0 missing/extra rows, 0 mode/blob/size mismatches, 0 unknown domains, 0 empty summaries.

- **1,319 tracked files** across **265 tracked directories** (from 1,194 / 236 — net **+125 / +29**)
- PR41 diff at snapshot: **277 files, +33,389 / −2,748**
- Delta vs prior atlas: **325 path records, +36,448 / −3,766 across 155 commits** (163 added / 114 modified / 38 deleted / 10 renamed)
- `docs/` **547** · `ARF/` **318** · `archive/` **210** · `skill-corpus/` **72** · `scripts/` **54** · `packages/` **42**
- `docs/research/` **305** (of which `intake_raw/` **193**) · `docs/architecture/` **45** · `docs/specs/` **37** · `docs/adr/` **23** · `docs/agent-memory/` **59**
- Evidence labels: `verified` **28** · `extracted` **937** · `inferred` **283** · `binary` **71**
- Retrieval priority: L0 **50** · L1 **660** · L2 **609**
- **20 domains** (19 tracked + 1 workspace-only), **23 task share sets**

⚠️ **No LOC counts, no test-coverage data, no dependency list, no TODO/FIXME census.** A `TODO|FIXME` grep across the whole inventory returned **zero** hits — meaning absence of data, not absence of debt.

**Zome ground truth (✅ verified from `ARF/Cargo.toml`) — exactly four active workspace members:** `integrity`, `coordinator`, `consent_integrity`, `consent_coordinator`. Explicitly demoted to `arf-lab-history`: `hrea_*`, `identity_*`, `memory_coordinator`, `ontology_integrity`, and all `infinity_bridge/zomes/*`. Useful guard against treating lab zomes as live.

Both integrity zomes changed between snapshots (`integrity/src/lib.rs` 18,622 → 20,092 B; `consent_integrity/src/lib.rs` 33,511 → 33,543 B) — consistent with ADR-15 enforcement landing. The atlas records new blob identities but *"does not reinterpret or re-approve those governed changes."*

### 10.5 ADR-20 absence confirms the timeline

`docs/adr/` is **exactly 23 files, numbering stops at ADR-19**, direct count = recursive count = 23, so there is no room for an unlisted file. **ADR-20 does not exist in the atlas.** This independently confirms ADR-20 was authored 2026-08-23 and implemented 2026-08-24 — *after* this snapshot.

**ADR-18 and ADR-19 were both `ADDED` in PR41** (`PATH_DELTA.tsv` lines 66–67), and ADR-19 is one of only 50 **L0** files. This raises an open question my survey did not resolve:

> Are ADR-18/19/20 on `main`, or only on the `reconcile/pr38-salvage-20260817` branch? If PR41 is still open and my live read was taken from that branch's checkout, then three ADRs — including a System/Substrate-class one — exist only on an unmerged branch. That would make PR41's review backlog block canon, not just code.

**Notable:** the atlas reproduces **no ADR status strings at all** and never opened `docs/adr/INDEX.md`. Its `verified` label on INDEX.md means only *"summary was bound to an authoritative structural source"* — explicitly *not* a claim that the file's contents are current. So the atlas neither confirms nor contradicts §5's "INDEX stale at ADR-17"; and since ADR-18/19 were added in PR41 while INDEX.md was not modified in that region, **stale-at-ADR-17 is exactly what the delta predicts.**

Also inventoried: `docs/agent-memory/project/adr19-ratification-deferred-to-consent-gate.md` (2,127 B) — filename corroborates ADR-19's consensus-ratification deferral independently of the ADR header.

### 10.6 Dead code, duplication, and an untapped debt register

- `scripts/triage_review_queue.py` (980 B) — *"DEPRECATED shim — merged into review_queue.py."* Deletion candidate.
- **Duplicate blob:** `docs/agent-memory/CHATGPT_MEMORY_EXPORT.md` and `docs/agent-memory/MEMORY.md` are byte-identical (15,021 B, blob `78c90c0d…`). One should be a pointer.
- Zero-byte tracked files: `docs/research/_write_agorai_deepdive.py` (empty blob `e69de29b…`).
- **26 tracked `__pycache__/*.pyc` files** removed in this delta — build artifacts that were in Git.
- `scripts/session_start_inject.py` deleted, superseded by `hooks/session_start_inject.py` — **not** detected as a rename, so history is split.
- `pprevious_working_task.md` — 55,036 B root file with a typo'd name, still tracked.
- Two "shadow-collision" ADR files (ADR-2, ADR-3) moved to `archive/adr-versions/` — prior ADR numbering collisions.
- **Internal inconsistency in the atlas itself:** `context-domains.json` line 79 still says *"not part of the 1,194-file PR snapshot"* — the prior count. Its validator checked row counts and route paths but not prose numerals.

**`docs/agent-memory/project/` (42 files) is an untapped debt register** — inventoried but mostly labeled `inferred`, meaning never opened. High-value filenames: `omniroute-voter-probe-log.md` (6,863 B — relevant to the provider-key and voter-independence threads), `jsonschema-format-silent-noop.md` (a silent-failure bug, and note §6 item 10 flags `jsonschema` undeclared in `ARF/requirements.txt` — likely the same root), `installation-not-adoption.md`, `tryorama-tooling-gap-2026-05-26.md`, `holochain-0-7-migration-pending.md`, `ci-green-list-ratchet.md`, `hash-pins-need-repin-discipline.md`, `doc-explosion-acknowledged.md`. Reading these 42 files is probably the cheapest remaining source of real findings in the repo.

### 10.7 The atlas is not wired in

*"The packet is not wired into shared context surfaces or harness startup"* — not in `shared-context-surface.json`, generated L0/L1 context, nested instruction files, MCP resources, or the context router. So this high-integrity census is invisible to every agent that starts from the standard orientation path. Given §5's finding that the *standard* surfaces are 3 weeks to 3 months stale, the best-quality structural map in the repo is the one nothing reads. Wiring it in — read-only, with `--check` — is a cheap, high-leverage reconciliation.

### 10.8 Net assessment

**Atlas ahead of my survey (4):** the committed Supabase JWT + its TSV re-leak; the Serena drift dossier; the kernel v1.4.0/v1.3.1 heading mismatch; the existence of an integration-level ADR-15 Tryorama test.

**My survey ahead of the atlas (6):** `_AUDIT_SINK` audit-trail bypass (atlas: zero mentions); `ow_mcp_at_…` + provider keys (zero mentions); PR #43 (postdates snapshot); ADR-20 (does not exist); per-ADR statuses (atlas records none); working-todo Section 0 (structurally out of scope as workspace-root material).

**Neither covers:** whether the Tryorama ADR-15 test passes in CI; whether ADR-18/19/20 are on `main` or branch-only; the contents of the 42-file agent-memory debt register.

The two are complementary and non-redundant: the atlas is a **structural census that ran no tests**; my survey was a **semantic/runtime read that never counted files**. Neither is a substitute for the other, and both are now stale by their own standards.

## 11. 5-box check

- **Intent echoed:** re-orient against the live repo after a major update; produce a durable continuation packet replacing the stale set; then cross-check against the 2026-08-23 repo atlas.
- **Evidence:** read-only live survey 2026-08-30 — heartbeat tick timestamp, `873cc0c` merge line, integrity-zome code inspection, ADR-15/18/19/20 status headers, working-todo Section 0, orientation-surface dates. Snapshot capsules excluded. Atlas cross-check added §10 from a SHA-256-sealed structural census at `db80571dd`, with its own staleness and zero-test-execution limits stated.
- **Anti-sycophancy:** recorded that 3 of my 4 assumptions were falsified; corrected my own "unit level only" ADR-15 claim after the atlas showed an integration test exists (§10.2); flagged that my Yumeichan-as-orchestrator recommendation conflicts with Accepted ADR-13; declined to treat either "massively upgraded" or the atlas's clean validator exit as uniformly good — the atlas leaks a credential it never flagged, and the system self-reports half a mechanism not working.
- **Open questions carried:** Are ADR-18/19/20 on `main` or only on `reconcile/pr38-salvage-20260817`? Does `ARF/tests/tryorama/provenance_validation.test.ts` pass, and is it in CI? Does the ADR-18 tier-2 REVISION REQUIRED on `provenance-anchor` block ADR-20 D-B1? Who owns the now-three credential rotations? What is in the 42-file agent-memory debt register?
- **Smallest artifact:** one delta file extended in place rather than a new one; four stale artifacts carry supersession pointers; cockpit updated in place; nothing copied from the atlas (deliberately — `FILE_INVENTORY.tsv` carries a plaintext token).
