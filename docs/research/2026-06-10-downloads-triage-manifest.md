# Downloads Triage Manifest + Session Decision Record — 2026-06-10

```yaml
# --- UpgradableArtifact Header ---
id: "research-2026-06-10-downloads-triage-manifest"
version: "1.0.0"
kind: "intake_triage_manifest"
status: "Accepted"
updated: "2026-06-10"
origin: "Claude (Fable 5, Cowork session with live filesystem access), human collision node Anthony (kalisam)"
truth_status: "Verified (file existence, hashes, copies, repo cross-checks done this session) / Specified (routing verdicts) — content of triaged files mostly UNREAD, classified by title+peek only"
license: "Compassion Clause + Apache-2.0/GPL-compatible"
note: "Session decisions are folded into this file instead of a second artifact (smallest-artifact rule). APPEND_ONLY_KNOWLEDGE_LOG was NOT hand-edited — it is auto-generated and says so."
```

## 1. Session decisions (Anthony, 2026-06-10, via structured question — record of answer, not implementation)

| # | Question (from ember seed pack file 01 §6 / this session) | Decision | Implementation note |
|---|---|---|---|
| D-N5 | Spec-gate ("-1 layer"): fail-closed "no new script/doc without one-line spec stub in registry" | **ADOPT — wire BOTH** (materializer `--check` + `hook_post_write`) | Belongs in a Claude Code session per pack §2; NOT implemented here |
| D-N6 | ObjectGraph spike resume | **CONDITIONAL GO** — after N1–N3 land; risk-probes first (cross-node synthesis regression; adversarial routing); pilot skill-corpus only, read-only resolve_context | Gated as written in file 01 N6 |
| D-TAME | P1–P5 goal-scope vs structural-resonance | **STRUCTURAL-RESONANCE** reading; recover `tame_integration_brief_v0_1.md` from origin chat 8778c081-27f5-468b-9475-e10bc1a0e5ff **before** TAME-seed N3–N5 | Brief confirmed NOT in repo (searched this session) — chat-only; recovery needs a claude.ai session |
| D-DL | Downloads ingestion depth | **Copy new .md set into intake mouth + this manifest**; PDF clusters as classified pointers | Executed and verified below |

Still open, re-ask (file 01 §6, unanswered): (a) orient-packet decisions #9/#10 — pytest suite for materializers; CI canary; (b) SRP v2 T2 blocker — replace seven-country citation with Savolainen/Schimmelpfennig/Folk triangulation?

## 2. Ember seed pack reconciliation (pack claims vs live repo, checked 2026-06-10)

| Pack claim | Live repo state | Verdict |
|---|---|---|
| Pack integrity (SHA256SUMS + file 00's embedded hash for file 05) | All 5 hashes match computed values | ✅ **Verified intact** |
| §4 inventory: "20 scripts" (13 read, 7 inferred) | `FLOSS/scripts/` has **29** scripts. Not in pack inventory (9): `backfill_kalisam_fork`, `backfill_stabilization_provenance`, `fork_ancestry_gather`, `hook_bg_round`, `hook_pre_write`, `materialize_gemini_mcp`, `smoke_test_gateway`, `smoke_test_inference`, `smoke_test_voters` | ⚠️ **Undercount** — N1 consolidation pass must inventory the live 29, not the pack's 20 |
| review_queue / triage_review_queue redundant pair | Both still present | ✅ Confirmed — N4 merge candidate live |
| Router CLI signature self-answers | `context_router.py "<q>" --format markdown --limit 4` ran clean | ✅ |
| CONTEXT_L0/L1 exist, generated | Present at `.agent-surface/context/`; L0 headers say generated | ✅ |
| Pointer registry: resonance_mechanism_v2 "repo canon [VERIFY]" | `docs/research/resonance_mechanism_v2.md` exists | ✅ Pointer resolves — chat recovery NOT needed |
| Pointer registry: re-bicameralization brief "possibly repo" | `docs/research/intake_raw/2026-05-19-root/reports/` has it | ✅ Pointer resolves |
| TAME brief location unknown (file 02 open question) | NOT in repo; only the TAME paper PDF in `_reference/ai-ml/` | ❌ **Chat-only** — recover per D-TAME |
| Levin corpus briefs | v0.1–v0.3 already in `intake_raw/2026-06-08-root/` (+ synthesis in `docs/research/2026-05-26-levin-corpus-cces-implications.md`) | ✅ Downloads copy is a duplicate — skipped |
| Runtime note (not a pack claim): heartbeat | Last tick 2026-06-03 (7 days stale); 25 synthesis drafts staged; review queue 5 polls | ⚠️ Resumption surface backlog awaits a Code session |

## 3. Copied into intake mouth `C:\~shit\` (verified byte-for-byte present; originals remain in Downloads)

| File | Size | Why |
|---|---|---|
| FLOSSI0ULLK_Knowledge_Interchange_v2.0.md | 68,059 B | Interchange format thread — feeds Atomic-Data HOLD gate (seed 03) when that work resumes |
| FLOSSI0ULLK_Verified_Foundations_v0.1.md | 18,837 B | Verification-discipline doc, not previously in repo |
| FLOSSIOULLK_ADRs_ALL_v1.0.0.md | 18,947 B | Historical ADR snapshot — **supersession-check against ADR Suite v2.0 required**; relevant to the open ADR-2 evidence-drift item |
| Automated Agent Orchestration for Decentralized Open-Source AI Development.md | 44,520 B | 2026-06-07 research synthesis, newest md in Downloads; an earlier 1/15 draft variant exists there (not copied) |
| automating-flossioullk.md | 30,253 B | Automation design notes (2025-12) |
| human_ai_co-evolution.md | 54,831 B | Co-evolution thread — cross-checks file 01 §3 cluster verdict |
| BASEDPROper.md | 3,880 B | **P1–P5 Resonance Kernel** (Pieces export, 2026-03-02) — direct primary source for the structural-resonance reading just adopted (D-TAME) |
| plate.md | 18,022 B | "Axioms of Immanence" manifesto synthesis — kin to today's permeable-shells vision seed |
| query-routing-flow.mermaid | 1,103 B | Diagram, pairs with context-router policy |
| vector-db-components.mermaid | 933 B | Diagram, pairs with decentralized-vector-DB thread in knowledge log |

## 4. Deliberately NOT copied (already in repo — duplicates)

`resonance_mechanism_v2.md` · `re-bicameralization_integration_brief_v1.0.md` · `LEVIN-CORPUS-INTEGRATION-BRIEF-v0.1.md` · `flossi0ullk_seed_packet_v1.0.0.md` · `context_compression_packet_v1_1.md` · Downloads `INDEX.md` (stale copy of workspace index) · `Project-Spine v0.2 / unversioned` (repo governance spine is v0.5 — superseded; archive-grade only)

## 5. Pointer clusters (stay in place; route when a thread actually needs them)

- **Psych corpus (~30 PDFs, 2026-06-09, + folders `healthpsych2024`, `PSYCHOLOGY OF EMOTIONS READINGS 2021`, `socialpsychology`, `behavioralscienceresearchdesign`)** — Harber/Pennebaker social-support, trauma-disclosure, emotional-broadcaster, directive-vs-nondirective support, expectancy-effects literature. **This is the Peony-doula empirical grounding** (see vision seed §2). Route: `_reference/psych/` when the doula design note starts. Verdict: high value, dormant until then.
- **Meta-learning/multi-agent arXiv batch (~15 PDFs, 2026-06-03)** — meta-verifiers, metacognitive consolidation, meta plan optimization, decentralized MAML, hierarchical skill meta-evolution. Route: `_reference/ai-ml/`; feeds Layer 4.6 harness-optimization research. Note: titles overlap the self-improvement cluster file 01 §3 warns about — read with the NOVA contamination trap in hand.
- **Full-Stack Alignment: Co-Aligning AI and Institutions with Thick Models of Value.pdf (998 KB, 2026-05-28)** — directly relevant to kernel north-star; candidate for a future research digestion.
- **Internet Voting Maturity Framework.pdf (600 KB, 2026-05-29)** — governance/consensus-protocol adjacent.
- **Math/physics/EE textbooks (2026-06-07, ~85 MB)** — personal reference library; not project intake.
- **AI.md + AI (1)–(8).md (Jan/Mar 2026)** — multi-model synthesis exports; pairs (1)≈(5), (3)≈(6), (4)≈(7) are near-duplicates. Route: `ai-conversations/` corpus if kept; stale relative to current canon. Low priority.
- **pieces_copilot_message_export_march_2_2026.md** — `ai-conversations/` corpus candidate.
- **Noise (not project material): 92 zip, 48 exe, 35 torrent, 4 msi, games/media/installers** — no action; flagging only that `kimi_3.0.15.exe` and `klcp_update_*.exe` are unverified binaries (standard caution, not project scope).
- **Downloads README.md** — US national-parks data-rescue note; unrelated to FLOSS.

## 6. Forward path

Per intake convention: copied files at `C:\~shit\` await `watch_intake`/`process_intake_events` (or manual digestion next Code session) → `docs/research/` or matching subdirectory. This manifest itself is the digestion record for the *triage*; the copied files still need *content* digestion. Heartbeat has been quiet since 2026-06-03 — the intake pipeline will not pick these up until it runs again.
