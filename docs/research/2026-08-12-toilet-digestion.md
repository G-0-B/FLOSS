# 2026-08-12 `.toilet` Digestion Map

```yaml
id: "2026-08-12-toilet-digestion"
status: "Classification complete. ONE deletion executed (.toilet/hermes, operator-authorized). No intake relocation performed — destination column awaits operator approval."
truth_status:
  relocation: "Not performed (this pass classifies only)"
  classification: "Verified for the reuse-gate verdicts (8 adversarially re-checked, 8 refuted); Specified for the loose-doc destinations (single-agent read pass)"
  canon_promotion: "Not performed"
  deletion: "Verified — .toilet/hermes removed 2026-08-10, record at .agent-surface/intake/toilet-hermes-deletion-2026-08-10.json"
move_log: ".agent-surface/intake/toilet-intake-moves-<date>.json (NOT YET WRITTEN)"
raw_holding_area: "FLOSS/docs/research/intake_raw/<date>-toilet/{reports,reference,bundles}/ (NOT YET CREATED)"
authorized_by: "Operator instruction 2026-08-10 ('go ahead with the .toilet sweep'); deletion of .toilet/hermes separately authorized same day"
companion_record: "Follows FLOSS/docs/research/2026-08-10-root-intake-digestion.md (root pass)"
method: "9-agent workflow: 4 parallel surveyors, 8 adversarial verifiers (one per non-rejected adopt), 1 synthesis. Plus inline operator-side verification of the license and credential findings."
previous_passes: ["2026-05-19", "2026-05-22", "2026-05-25", "2026-06-08", "2026-06-12", "2026-07-07", "2026-08-10 (root)"]
```

## What changed — and why this pass is different

`.toilet/` has its own charter, and it inverts the default. `.toilet/README.md` states: *"Nothing here is canon. Never cite `.toilet/` as a source of truth."*, *"Contents are git-ignored and **safe to flush at any time** — assume they will be regularly."*, and *"No secrets here (it's shared and may be synced)."*

So unlike the root passes — where the default is *digest and promote* — here the default is **disposable**, and the burden falls on showing something deserves rescuing. 12 of 69 loose docs were left in place on exactly that basis.

The folder's own no-secrets rule was violated at scale. That drove the one destructive action in this pass.

**Scope: 69 loose documents, 21 third-party artifacts, 62 bulk entries.** The reuse-gate cluster is 21 subjects, not the 11 in earlier inventories — ten archives landed on 2026-08-10, after every prior survey.

---

## Cluster A — Credentials (resolved by deletion)

**25 verified-real credentials** were found, all inside `.toilet/hermes/`. Severity order:

| # | Credential | Location | Note |
|---|---|---|---|
| 1 | GitHub classic PAT (`ghp_`, 40 chars, **uncommented**) | `hermes/state-snapshots/20260716-171812-pre-update/.env:474` | Highest blast radius. Stripped from the live `.env` (472 lines) but retained in the 474-line pre-update snapshot. Distinct from the `ghp_xxxx…` placeholder at line 404 of the same file. |
| 2 | OpenRouter key (`sk-or-v1-`, 73 chars, **uncommented**) | same file, line 473 | Same story — survived in the snapshot after removal from the live file. |
| 3 | OAuth refresh tokens ×3 identities | `hermes/auth.json`, `auth.json.corrupt`, snapshot copy | openai-codex, xai-oauth, nous. Refresh tokens outlive access-token expiry and mint new ones. `auth.json.corrupt` **parses as valid JSON** despite its name and was the *sole* holder of the Nous set. |
| 4 | Pioneer API key (`pio_`, 68 chars) | `hermes/config.yaml:696`, `config.yaml.pre-specworkflow-removal.bak:730`, **and `.toilet/hermes-config.json:1313`** | One key, fingerprint `184df14597e2`, three copies. |

**Action taken:** `.toilet/hermes` deleted 2026-08-10 — 2.7 GB, 125,695 files. `.toilet` went 5.4 G → 2.7 G.

Pre-delete safety checks, all recorded in the deletion ledger with sha256 of the eight sensitive files:
- **Not the live runtime.** `gateway.pid` argv points at `C:/Users/kalis/AppData/Local/hermes`; `auth.json`, `config.yaml` and `.env` all differ between the two homes. `.toilet/hermes` was a divergent stale copy.
- **Nothing unique lost.** `SOUL.md` and `skills/SKILL_INDEX.md` byte-identical to the live home; `memories/MEMORY.md` older and smaller in `.toilet` (2,951 B / 07-16 vs 6,634 B / 07-30); the live home additionally holds `memories/USER.md`, absent from `.toilet`.

> ⚠️ **Deletion is not revocation.** Every credential above must still be rotated at its provider. Removing disk copies stops the spread; it does not invalidate access.
>
> ⚠️ **Still exposed:** `.toilet/hermes-config.json` retains the third `pio_` copy — outside the authorized subtree, deliberately untouched.

**Method caveat worth preserving:** the first scan of this directory used a `.gitignore`-respecting search tool over a git-ignored path and returned almost nothing. `.toilet` is ignored at `.gitignore:158`. Any future sweep here **must** use plain `grep`. This is the second time this project has been bitten by filter-limited scanning; the first is recorded in agentmemory from the PR38 privacy review (65 reported hits vs 22,370 under an unrestricted scan).

---

## Cluster B — Bulk-move hazards

- **`omnigent_eval/` is the only nested `.git`** (~1.2 GB, plus `.venv`, `.venv_system`, `.pytest_cache`, `omnigent.egg-info`). It is an evaluated-in-place checkout, not an extract. Never `mv` it — leave it or re-clone.
- 11 archives have extracted twins; **11 do not**. Orphan zips are the ten from 2026-08-10 plus `openhuman-0.63.12.zip`.
- Long-path risk: the known >260-char paths in this workspace are under `_pr38_salvage_capsules/` at root, not in `.toilet`.

---

## Cluster C — Third-party prior art: 21 subjects

### C1 — The eleven assessed by the workflow

**All eight non-rejected recommendations were adversarially re-checked. All eight were refuted.** No repo in this set survives as `adopt`. The verifiers found errors in the surveys' *evidence*, not merely their conclusions:

| Repo | Survey said | Final | What the verifier found |
|---|---|---|---|
| agentskills-main | adopt | **investigate** | Survey called the spec "off-disk and unread" — `docs/specification.mdx` (7,166 B) was one directory down, and `AGENTS.md` names it authoritative. Worse: the proposed integration point already exists — `materialize_shared_skill_surface.py:60–84` already fails closed on malformed frontmatter. |
| agent-plugins-spec-main | (conservative) | **adopt** | Refuted in the *opposite* direction: too conservative. Spec §7.1 makes Agent Skills normative for `SKILL.md`, so Agent Plugins is a strict **superset** of agentskills-main. Assessing them as peers was the error. |
| allagents-main | compose | **investigate** | ADR-18 requires ≥1 direct probe for `compose`/`build`; none ran. And a real collision the survey missed by not reading `src/`: `claude-mcp.ts:79,127` and `mcp-sync.ts:81` write root `.mcp.json` — MCP registry ownership inversion against `shared-agent-surface.json`. |
| deliberation-master | (do not replace) | **reject** | Top line survives; three of four supports fail. The named reusable component ("non-answer detection") is on disk just `GEMINI_MIN_ANSWER_CHARS=80`, a stdout character floor. |
| OpenViking-main | adopt | **investigate** | Cited neither ADR-18 nor the standing installation-is-not-adoption rule. Also collides with the sole-reservoir commitment in `CONTEXT_DAEMON_ARCHITECTURE.md` — no second source of truth. |
| oh-my-openagent | reject (license) | **reject + remediation** | Direction right, evidence inverted — see the SUL-1.0 finding below. |
| quantitative-grounding-main | adopt | **investigate** | Barred by `docs/agent-memory/project/installation-not-adoption.md`, a standing rule ratified by consensus claim `019e412d`, mean +0.90, which the survey never cited. |
| openhuman-0.63.12 | investigate at adapter boundary | **reject** | The recommended next action would consume an owner's time producing a mapping that cannot be produced. ADR-19 (OmniRoute, Accepted, Verified, System radius) was never cited. |

**Two standing rules did the work here** and should be cited by default in any future reuse assessment:
- ADR-18: *"`compose`/`build` verdicts require ≥1 direct probe; unprobed incompatibility claims cannot justify `build`."*
- `installation-not-adoption.md`: on-disk presence and tooling registration do **not** constitute a gate-pass.

### C2 — The ten that landed 2026-08-10, assessed here

None extracted; metadata read directly from the archives.

| Archive | Size | License | What it is | Verdict |
|---|---|---|---|---|
| `AIngram-main.zip` | 2.3 M | **AGPL-3.0** | "Collective memory of AI agents" — agent-native knowledge base, vector-first search, multi-agent curation through debate, trust scoring per item | **Re-drop — already assessed.** See below. |
| `Agorai-main.zip` | 1.6 M | **AGPL-3.0-only** | Multi-agent + human collaboration platform; debate, persistent collective knowledge | **Re-drop — already in the reuse ledger** as entry `0068`, with a `kalisam` fork recorded. |
| `llm-council-master.zip` | 268 K | **NONE** | Group several providers into a "council"; they answer and rank each other | **reject for incorporation** — no license means no grant. Read-only study of the idea. Overlaps `flossiullk-reasoning-ensemble`. |
| `ruflo-main.zip` | 34 M | MIT | "Agent meta-harness for Claude Code and Codex. Agent = Model + Harness." | **investigate** — closest competitor to the metaharness line |
| `planning-with-files-master.zip` | 11 M | MIT | Keeps `task_plan.md` / `findings.md` / `progress.md` on disk, re-injects each turn to survive compaction | **investigate** — overlaps working-todo + context daemon; cheap idea, may not need the dependency |
| `camel-master.zip` | 116 M | Apache-2.0 | General multi-agent framework | **reject** — broad framework, no targeted overlap |
| `swarms-master.zip` | 49 M | Apache-2.0 | "Enterprise-grade multi-agent orchestration" | **reject** — same |
| `langroid-main.zip` | 57 M | MIT | Lightweight agent framework | **reject** — same |
| `solace-agent-mesh-main.zip` | 6.9 M | Apache-2.0 | Event-mesh-backed multi-agent framework, Solace Platform | **reject** — introduces a broker dependency; central-routing shape |
| `eigent-main.zip` | 6.8 M | Apache-2.0 / pkg MIT | Open-source "Cowork desktop" productivity app | **reject** — product, not substrate. License fields disagree between LICENSE and package.json; note if ever revisited |

> **AIngram and Agorai are re-drops, and this is the reuse gate working.** `docs/research/2026-04-14-aingram-deep-dive.md` (23 KB, 2026-04-14) already assessed AIngram in depth — 60-migration PostgreSQL platform, AGPL-3.0, same author (Steven Johnson) as Agorai, arXiv 2603.20833. Agorai is reuse-ledger entry `0068`. **Do not re-research either.** Re-read the existing artifacts instead.
>
> ⚠️ **But the April plan is now license-blocked.** That deep dive recommends porting AIngram's `formal-vote.ts` + `lifecycle.ts` + `vote-weight.ts` into our integrity zomes. Both AIngram and Agorai are **AGPL-3.0**; this project is **GPL-3.0** (see below). AGPL-licensed code cannot be incorporated into a GPL-3.0 work distributed under GPL-3.0 alone. The medium-term item in that April document must be reopened, not executed.
>
> Agorai's ledger entry also flags a **P5 violation risk** — its built-in orchestrator and centralized GUI suggest central routing, which `resonance_mechanism_v2.md` forbids.

---

## Cluster D — Loose documents (69)

| Destination | Count |
|---|---|
| `reports/` | 29 |
| `reuse-gate` (hand off to ADR-18, not intake) | 22 |
| `stays-in-.toilet` (genuinely disposable per the charter) | 12 |
| `reference/` | 3 |
| `delete-candidate` (**hash-verified redundant**) | 3 |

**The three delete-candidates are verified, not assumed:**
1. `Cryptographically Verifiable Context Artifacts…md` — md5 `1eb55426fcdb29f98076e2ab505f1ced`, byte-identical (40,689 B) to the copy already relocated. `RESEARCH-REGISTER.md` also declares it superseded.
2. `FLOSSI0ULLK Context Artifact Architecture  State Analysis & OVCA Integration Map.md` (double-space filename) — md5 `842244110326b000c195dc0116f576fa`, byte-identical to its single-space twin. Keep the single-space copy.
3. `flossioullk-context-continuation-seed-2026-06-20-v2.md` — superseded by `-v3`; `diff` is one hunk, two lines. Keep v3.

> **Blocking dependency:** `.toilet/2026-07-16-prior-art-reuse-gate-continuation.md` is cited by `docs/adr/ADR-18-prior-art-reuse-gate.md` as a design record. Moving it **dangles a canon pointer** unless ADR-18 is updated in the same commit. This is the same failure repaired during the root pass; do not repeat it.
>
> Two entries in the `reports/` list are this session's own working artifacts, not intake: `root-consolidation-plan-2026-08-09.md` and `phase4_move.py`. Dispose of them as scratch.

---

## NEVER-list

1. **Never scan `.toilet` with a `.gitignore`-respecting tool.** It is ignored at `.gitignore:158`. Use plain `grep`. Two recorded undercounts in this project trace to this.
2. **Never treat a survey's license claim as verified.** The AGPL/GPL error below was found only because a reviewer opened `LICENSE` instead of trusting the register.
3. **Never mark a repo `adopt` on install-visibility.** Standing rule, consensus-ratified, mean +0.90.
4. **Never `mv` `omnigent_eval/`** — nested `.git`.
5. **Never assume a `.corrupt` file is unreadable.** `auth.json.corrupt` parsed cleanly and held credentials absent from the live file.
6. **Never re-research AIngram or Agorai** — prior artifacts exist; read those.
7. `.toilet` contents are not canon and never were. **`FLOSS/archive/` is wrong for all of them** — archive is for superseded *canonical* docs only.

---

## Cross-cutting finding: ADR-7 adopted AGPL-3.0; only `FLOSS/LICENSE` lags

**Corrected 2026-08-12.** An earlier revision of this map said the project "is GPL-3.0, not AGPL" and concluded the April AIngram port plan was license-blocked. Both halves were wrong, and the second was backwards.

**The decision exists.** `docs/adr/ADR-7-agpl-cascade.md` — "Embracing AGPL-3.0 Copyleft Cascade", **Accepted 2026-04-15**, `docs/adr/INDEX.md:34`, Truth Status **Specified**. Committed as `9ef2b70` with operator approval. It names AIngram and Agorai as the motivating case and explicitly removes the MCP-boundary constraint so their code *may* be ported directly.

**What actually lags is one file.** `FLOSSI_U/LICENSE` carries the AGPL SPDX line as ADR-7 describes; `FLOSS/LICENSE` still holds the 674-line GPL-3.0 text. Truth Status "Specified" was the correct label all along — I read the register and the LICENSE file, and failed to read the ADR that governs both.

**So the AIngram/Agorai port is *unblocked*, not blocked** — that is ADR-7's stated purpose, and `reuse-ledger-seed.yaml:0068` already recorded it correctly (`"compatible with AGPL-3 cascade per ADR-7"`). The C2 table above is corrected accordingly.

**12b still stands and is unaffected:** SUL-1.0 is incompatible with AGPL-3.0 just as it is with GPL-3.0, so `voters.py`'s adapted `MOMUS_PERSONA_SYSTEM` still needs a decision.

Tracked as working-todo **A.000000 item 12** (corrected twice) and **12b**.

**Method lesson worth keeping:** two independent surfaces (a register entry and a LICENSE file) disagreed, and I resolved the conflict by trusting the artifact I had personally opened. The kernel's own §11b source-authority ladder puts *repo docs* above *conversation and memory*, and ADR-7 is a repo doc that settles it. **Check for a governing ADR before declaring a documentation conflict unresolved.**

**12b — SUL-1.0 text in a GPL-3.0 tree.** `packages/metacoordinator_mcp/voters.py:198–211` carries `MOMUS_PERSONA_SYSTEM`, documented in-file as adapted from `oh-my-opencode v4.0.0`'s `MOMUS_DEFAULT_PROMPT`. oh-my-openagent is **SUL-1.0** (`package.json:149`) — source-available, not OSI open-source. Provenance was recorded honestly in `docs/agent-memory/project/omo-momus-voter.md`, and the text is adapted rather than copied, so this is a license question and not a lift. It is still shipped code in a GPL-3.0 tree and needs a decision: keep with permission, clean-room rewrite, or drop.

---

## Priority queue

1. **Rotate the four credential sets.** Deletion removed copies, not access. GitHub PAT first.
2. **Delete `.toilet/hermes-config.json`** or scrub its `pio_` key — the surviving third copy.
3. **Settle the license question.** It gates 12b, the AIngram/Agorai port plan, and every reuse verdict computed against the wrong inbound license.
4. **Re-read `2026-04-14-aingram-deep-dive.md`** under GPL-3.0 constraints and reopen its medium-term item.
5. **Fold the 22 `reuse-gate` loose docs into `reuse-ledger-seed.yaml`** rather than relocating them into intake.
6. Relocate the 29 `reports/` + 3 `reference/` items, updating ADR-18's `design_record` in the same commit.
7. Execute the 3 hash-verified deletions.

## What would break under a naive bulk operation

- `omnigent_eval/` — nested `.git` corrupts on move.
- ADR-18's `design_record` — dangles if the continuation packet moves alone.
- The 11 orphan zips have no extracted twin; deleting a zip is not recoverable from disk elsewhere.
- `.toilet` is git-ignored, so **nothing here is recoverable from git history**. The only safety net is `.toilet/snap-*.bundle` (which covers the two repos, not `.toilet` itself) and the deletion ledger's hashes.
