# Specification: Cross-Agent Chat Ingestion — Transcripts → Source Chain

**Version:** 0.1
**Date:** 2026-06-10
**Status:** Draft — ⚠️ Specified, pending consensus claim (submit via gateway before implementation)
**Authors:** kalisam + Claude (Cowork session, single-model draft — needs multi-model review per diversity policy)
**Truth status of this document:** ⚠️ Specified. Survey claims in §3 are ✅ Verified against repo state 2026-06-10. Everything in §4+ is design intent.

---

## 1. Context & Motivation

Observed NOW pain (evidence gate):

1. The daily digest task (`daily-research-task-digest`, Cowork scheduled task, 2026-06-10) consolidates email, calendar, GitHub, repo threads, and Claude session transcripts — but **cannot see conversations held with other AI surfaces** (ChatGPT, Gemini, Grok, DeepSeek, Mistral) or human-to-human threads. Unresolved threads in those conversations silently rot.
2. `FLOSS/ai-conversations/` holds a ~1 GB static corpus of multi-model exports (March 2026 vintage) that is **dead weight**: unindexed, un-provenance'd, invisible to the consensus flow. It is intake that was never digested.
3. The harness-roster invariant already mandates: *"Load-bearing cross-agent handoffs require provenance packet evidence when they bind System/Substrate claims"* and *"load-bearing conclusions must be promoted through repo memory, working todo, specs, ADRs, or source-chain claims"* (`.agent-surface/harness/AI_ROSTER.md`). There is currently **no defined path** from a chat transcript to a source-chain claim. This spec defines that path.
4. `docs/specs/provenance-packet.spec.md` v1.4 explicitly scopes itself to *"local agent surfaces and the consensus gateway before any Plane B/Holochain source-chain ingestion"* — anticipating exactly this bridge.

## 2. Core Principles

1. **No new top-level entry type.** Follows the ADR-9 pattern (ContinuityPayload wrapped in existing wire format). Raw transcripts ride the existing `memory` entry type (`packages/source_chain/cell.py` already accepts `entry_type="memory"`); extracted open threads ride the existing `Claim` type via the gateway. Zero schema files added.
2. **Transcripts are evidence, not proposals.** A conversation is archived as memory + artifact refs. Only *extracted, reviewable assertions* (open threads, decisions implied, action items) become Claims — and they submit as `Unverified`, like every Claim (`claim_schema.py` INV: truth_status must be Unverified on submission).
3. **Logic validates, neural assists.** LLM extraction generates *candidates only*. Nothing extracted becomes load-bearing without the normal vote/decision flow. Multi-AI agreement on an extraction is not verification — one quote-span check against the archived transcript outweighs model consensus.
4. **Consent before propagation.** Chats contain human participants. Nothing leaves the local node, and no extracted claim names a human participant, without an explicit consent reference (consent zomes exist in the live workspace; packets carry `consent_ref`).
5. **Many observers, one writer per surface** (filewatch metaharness rule). The ingestion adapter is the single writer for chat-derived entries.
6. **Holochain-forward.** Entries are content-addressed (SHA256 filename = entry hash, `cell.py`), so migration to Holochain actions requires no structural rework.

## 3. What Already Exists (verified 2026-06-10)

| Component | Path | State |
|---|---|---|
| Claim/Vote/Decision wire format | `packages/orchestrator/claim_schema.py` | ✅ Verified (UUID v7, analog votes ∈ [−0.999, +0.999], evidence types incl. `provenance_packet`) |
| File-based source chain, `memory` entry type | `packages/source_chain/cell.py` | ✅ Verified (append_entry, content-addressed, locked) |
| Gateway tool surface | `packages/metacoordinator_mcp/tools.py` | ✅ Verified (submit_claim, cast_vote, list_pending, run_consensus_round) |
| Live cell | `~/.floss_agent/cells/000…000/` | ⚠️ Unverified this session (outside mounted folders; referenced by context router) |
| Provenance packets v1.4, in active use | `docs/specs/provenance-packet.spec.md`, `.agent-surface/provenance/2026-05-2*/` | ✅ Verified (spec + daily packet folders exist) |
| Intake event pipeline | `scripts/watch_intake.py`, `scripts/process_intake_events.py`, `docs/specs/intake-event.schema.json` | ✅ Verified (files exist; runtime behavior not exercised this session) |
| Static chat corpus | `ai-conversations/{chatgpt-export-markdown, gemini-google, grok_3-20-2026-all_exports, deepseek_data-2026-03-19, mistral_chat-export_3-18-2026, old}/` | ✅ Verified (formats sampled, see §6) |
| Claude/Cowork live transcripts | `session_info` MCP (list_sessions, read_transcript) | ✅ Verified available in Cowork |
| agentmemory recall surface | `AGENTMEMORY.md`, localhost:3111 | ⚠️ Unverified this session; per roster invariant it is recall infra, **not** the load-bearing target |
| Audio chat logs | 821 `.wav` files in corpus; Deepgram MCP connected in Cowork | ⚠️ Out of scope v0.1 (see §9) |

## 4. Architecture — Three Stages

```
[exports / live sessions / human notes]
        │  Stage A: ACQUIRE (per-source adapters)
        ▼
[canonical thread JSON + media refs]
        │  Stage B: NORMALIZE + ARCHIVE
        │    • canonical_serialize → sha256 → memory entry on source chain
        │    • one provenance packet per ingestion batch
        ▼
[archived, content-addressed threads]
        │  Stage C: EXTRACT + PROMOTE (LLM-assisted, gated)
        │    • candidate open-threads/insights w/ quote spans
        │    • submit_claim via gateway (Unverified, blast_radius=Local)
        ▼
[claims pending votes] ──→ daily digest reads list_pending (already wired)
```

Stage C closes the loop with zero digest changes: `daily-research-task-digest` already checks the source chain for claims pending votes.

## 5. Wire Shapes (reusing existing envelopes)

**Stage B memory entry** — `append_entry(entry_type="memory", author_did=<adapter DID>, content=…)`:

```json
{
  "kind": "chat_thread/v0.1",
  "source_system": "chatgpt|gemini|grok|deepseek|mistral|claude-cowork|human",
  "source_export_ref": {"path": "ai-conversations/…", "sha256": "…"},
  "thread_id_native": "<provider-native id or filename>",
  "started_at": "ISO-8601|null",
  "participants": [{"role": "human|assistant|tool", "label": "anonymized-or-consented name", "consent_ref": null}],
  "message_count": 0,
  "messages_ref": {"path": "<archived canonical JSON>", "sha256": "…"},
  "media_refs": [{"path": "…", "sha256": "…", "transcribed": false}],
  "ingest_batch": "<provenance packet SAID>"
}
```

Messages stay in the referenced artifact, not inline — keeps chain entries small; the hash binds them immutably.

**Stage C claim** — standard `Claim`, no schema change:

- `proposal_type`: `Other`; `blast_radius`: `Local`; `truth_status`: `Unverified` (enforced)
- `summary`: one-line open thread (≤200 chars, enforced)
- `body`: extracted thread + **verbatim quote span(s)** + suggested next action
- `evidence`: `[{type: "provenance_packet", ref: <batch SAID>}, {type: "url"|"commit"|…}]` with the memory entry hash referenced in body

Original chat authorship lives in `content.participants` and packet `a[].source_systems`; `author_did` is the ingesting adapter (per packet spec: cross-agent lineage via `evidence_refs`, never via `p`).

## 6. Source Adapter Inventory (formats verified by sampling)

| Adapter | Input shape | Notes |
|---|---|---|
| `chatgpt_md` | one `.md` per conversation, `#### You:` / `#### ChatGPT:` headers | Frequent `\[Unsupported Content]` placeholders — record as gaps, never paraphrase over them |
| `gemini_takeout` | `conversations.json`, `memories.json`, `projects.json` | |
| `grok_export` | `conversations.json` + `conv_N_msg_M_{human,assistant}.txt` | JSON is index; txt files are message bodies |
| `deepseek_export` | `conversations.json` + `user.json` | |
| `mistral_export` | `chat-<uuid>.json` + sibling `…-files/` attachment dirs | Attachments → `media_refs` by hash |
| `claude_cowork` | `session_info` MCP transcripts | The only *live* adapter in v0.1; others are batch |
| `human_note` | files dropped in root intake mouth | Rides existing intake-event flow |

## 7. Pipeline Integration

- **Watch domain:** reuse `watch_domain: "other"` in v0.1 to avoid touching `intake-event.schema.json`. If chat intake proves high-volume (≥3-case pattern), propose enum extension `chat-intake` as a separate one-line schema claim. Flagged, not buried.
- **Trigger:** new files under `ai-conversations/` (or designated drop dir) → intake event → ingestion adapter run. Backfill is a manual batch invocation of the same adapter.
- **Idempotence:** content-addressing gives near-free dedupe — re-ingesting an identical export yields identical entry hashes; adapter must treat existing-hash as no-op, so re-runs append nothing.
- **One writer:** the adapter process holds the cell lock per append (`cell.py` `.lock` semantics); observers never write.

## 8. Consent & Privacy Gate

1. Default participant labels are pseudonymous (`human-1`) unless a `consent_ref` exists.
2. Stage C redaction pass runs **before** claim submission: no emails, phone numbers, third-party names, credentials in `summary`/`body`. The bound artifact retains the full text locally; redaction applies to what circulates.
3. Anything crossing to another agent surface requires the batch provenance packet; System/Substrate-bound claims additionally require explicit `consent_ref` (per packet spec — governed bindings blocked without it).

## 9. Phasing

- **v0.1 — Backfill, dry-run first:** adapters parse the five static corpora; emit *counts and samples only* (no writes); human reviews; then archive-only run (Stage B). Exit: corpus archived, packet per batch, zero duplicate hashes on re-run.
- **v0.2 — Live tail + extraction:** `claude_cowork` adapter on a schedule; Stage C extraction on new threads only; claims flow to digest. Exit: an open thread from a non-Claude chat appears in the morning digest with quote-span evidence.
- **v0.3 — Media + bridge:** Deepgram transcription for the 821 wav files (connector already available in Cowork); alignment with Holochain Cell migration; consent zome enforcement replaces local convention.

## 10. Acceptance Criteria & Verification Floor

1. `pytest FLOSS/packages/source_chain/tests/test_cell.py` and `python FLOSS/packages/metacoordinator_mcp/tests/test_tools.py` stay green (skill verification floor).
2. New adapter tests: each sampled format parses to `chat_thread/v0.1`; malformed input → explicit skip log, never a fabricated thread.
3. Idempotence test: double ingestion of one export ⇒ chain length unchanged on second run.
4. Every Stage C claim carries ≥1 `provenance_packet` evidence ref and ≥1 verbatim quote span resolvable in the archived artifact.
5. Redaction test: seeded PII in a fixture transcript never appears in submitted claim text.

## 11. Risks, Failure Modes, Alternatives

- **Doc/scope explosion (dominant historical failure mode):** this spec adds one file and zero schemas; v0.1 is read-mostly. If implementation grows a second design doc, that is the failure signal — fold it back here.
- **LLM extraction hallucination:** mitigated by quote-span requirement + Unverified status + vote gate. Residual risk: plausible-but-wrong summaries pass votes from models sharing training bias — the quote-span check is the symbolic backstop; spot-audit against archived text.
- **Consent hazard (highest severity):** chats include third parties who never opted in. v0.1 archive stage is local-only; the redaction gate is mandatory before any claim circulates. If in doubt, the thread stays archived and unpromoted.
- **3 GB corpus / 821 wav cost:** batch backfill is cheap (text); audio deferred. The 982 MB zip is treated as opaque until the loose dirs are done.
- **Alternative considered — ingest into agentmemory instead:** rejected for load-bearing use; roster invariant names agentmemory as recall infrastructure, with promotion through source-chain claims. agentmemory may *index* archived threads for recall (complementary, not the system of record).
- **Alternative considered — extraction without archival:** rejected; loses the provenance bind that makes extractions auditable.

## 12. Open Questions (carried forward)

1. Adapter DID scheme: one DID for the ingestion daemon, or one per source adapter? (Leaning: one daemon DID; `source_system` is payload-level.)
2. Drop directory: keep `ai-conversations/` as the chat intake mouth, or a new watched `intake/chats/`? (Leaning: keep `ai-conversations/` — it already is the mouth.)
3. Does the live cell at `~/.floss_agent/` carry state that constrains backfill ordering? (Unverified this session — check head before first write.)
4. Extraction model roster: Groq/Cerebras per inference posture (cheap background), with what sampling rate for spot-audits?

---

*Submit this spec as a `SpecChange` claim (blast_radius: Module) through the gateway before implementation. Per the diversity policy, the poll should span ≥3 provider surfaces and ≥4 model families — this draft is single-model and must not self-approve.*
