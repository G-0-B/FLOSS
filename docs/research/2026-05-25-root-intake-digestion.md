# 2026-05-25 Root Intake Digestion

**Pass id:** root-intake-2026-05-25
**Executor:** Claude Code (stabilization sweep — Phase 2)
**Prior passes:** [2026-05-19](2026-05-19-root-intake-digestion.md), [2026-05-22](2026-05-22-root-intake-digestion.md)
**Move log:** [.agent-surface/intake/root-intake-moves-2026-05-25.json](../../../.agent-surface/intake/root-intake-moves-2026-05-25.json)
**Truth status:** Specified (the digestion *map* is verified; the distillations it points to are written next)

---

## Scope

Drops landed at `C:\~shit\` after the 2026-05-22 intake pass — 7 files (≈233 KB md + 9 MB pdf). Plus one root duplicate of canonical ADR-3 left in place pending P2.3 reconciliation.

Canonical root-surface files (`INDEX.md`, `AGENTMEMORY.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `HEARTBEAT.md`, `IDENTITY.md`, `SOUL.md`, `TOOLS.md`, `USER.md`) were **not touched** — those are operator-surface state, not intake.

## Per-file disposition

| File | Size | Leverage | Bucket | Next distillation |
|---|--:|---|---|---|
| `Levin Corpus Deep Analysis  Individual Texts & Holistic Synthesis.md` | 48 KB | **HIGH** | reports/ | `2026-05-25-levin-corpus-cces-implications.md` — map each text's relevance to CCES n+3 layers + ADR cross-refs |
| `Open Distributed Intelligence Research Scan.md` | 62 KB | **HIGH** | reports/ | `2026-05-25-odi-scan-delta-vs-landscape.md` — delta against existing LANDSCAPE-ENTRY ODI and the 2026-05-22 ODI digestion |
| `LANDSCAPE-ENTRY_open-distributed-intelligence-2026-05.md` | 23 KB | MEDIUM | reports/ | Fold into the ODI delta distillation as a companion, not standalone |
| `info_firehose_ingestion.md` | 26 KB | MEDIUM | reports/ | Candidate for governance/personal-meta-harness annex on noise-reduction discipline |
| `how can i host an ad4m instance for flossioullk  f.md` | 50 KB | MEDIUM | reports/ | Pair with 2026-05-09 AD4M audit-delta; promote a deployment recipe only if pursuing a remote AD4M node |
| `Use the _recent-open-distributed-intelligence-rese.md` | 24 KB | LOW | reports/ | Fold relevant snippets into the recent-open-distributed-intelligence-research skill's references — don't promote standalone |
| `InfoQ-emag-124-Architecting-Automony2-1779098796985.pdf` | 9 MB | MEDIUM | reference/ | Skim for adoption candidates; do not distill wholesale |

## Left at root for separate handling

- **`ADR-003-Metaprompt-Kernelization.md`** — root-drop duplicate of canonical `FLOSS/docs/adr/ADR-3-metaprompt-kernelization.md`. Handled in P2.3.
- **`floss_plane_rewritten_bootstrap.tar.gz.terabox.uploading.cfg`** (690 B) — Terabox upload state file from an interrupted upload. Operational artifact, not intake. Operator decides.

## Anti-pattern guards re-applied this pass

Per the doc-explosion finding ([doc-explosion-acknowledged](../agent-memory/project/doc-explosion-acknowledged.md), [2026-05-09 AD4M audit-delta §K](2026-05-09-ad4m-coasys-audit-delta.md)):

- ✅ Intake material lives in `intake_raw/`, not in canonical `architecture/` or `adr/`. Promotion to canon requires explicit truth-status + multi-agent review, not just "I read it and it seemed important."
- ✅ Default position: do not add a doc unless it lands in an existing surface OR genuinely advances an open work-stream named in `2026-05-15-working-todo-list.md`.
- ✅ Hashes pre-recorded so future audits can detect content drift.

## High-ROI immediate next distillations

1. **Levin Corpus → CCES implications** (P2.4). The Levin corpus is the strongest n+3 substrate available; mapping each text into L1 (collective bio-cognition), L2 (basal cognition), and L5 (sense-making) is the highest leverage move from this pass.
2. **ODI Scan → landscape delta** (P2.5). Two prior ODI passes exist; the delta lens prevents accumulation and forces a "what's *actually new* since 2026-05-22?" framing.
3. AD4M hosting → defer until the operator decides whether to spin up a remote node. The 2026-05-09 AD4M fit-check froze new AD4M expansion until the sidecar spike records pass/fail evidence; hosting work is downstream of that gate.

## Pass close

After P2.4 + P2.5 land, the working-todo §A.3 entry should be updated with this pass's outcome + the two distillation files. The 2026-05-25 root drops are then digested.
