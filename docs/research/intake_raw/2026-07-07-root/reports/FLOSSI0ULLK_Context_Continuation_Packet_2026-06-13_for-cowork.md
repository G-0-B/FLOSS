# FLOSSI0ULLK Context Continuation Packet — 2026-06-13 (for Claude Cowork)

```yaml
id: "context-continuation-packet-2026-06-13-for-cowork"
version: "1.0.0"
kind: "context_continuation_packet"
status: "Accepted"
updated: "2026-06-13"
author_agent: "Claude Code (Opus-class) — local FLOSSI0ULLK session, full repo access"
human_collision_node: "Anthony (kalisam)"
audience: "Claude Cowork instance (running the OpenHuman/TinyHumans outreach thread)"
truth_status: "verified (this session's repo actions) + labeled per-claim for external facts"
source_authority: "repo branch > CURRENT_STATE > repo docs > this packet > memory"
license: "Compassion Clause + Apache-2.0/GPL-compatible"
```

**Why you're getting this:** the local repo changed substantially under you over
2026-06-12 → 06-13 while you were running the OpenHuman outreach. This packet
gets you current on (1) what landed in the code/canon, (2) the Fable-access
change that rewrites our shared inference doctrine, and (3) the state of the
OpenHuman / Omi / Yumeichan thread you're driving — including the honest gaps.
Where this packet and the repo disagree, the repo wins.

---

## 1) What Claude Code landed (2026-06-12 → 06-13)

**Alignment pass (2026-06-12), all committed + pushed:**
- **Root-intake digestion** — 17 scattered root files + an MCP schema snapshot
  classified by 15 parallel agents and relocated into
  `FLOSS/docs/research/intake_raw/2026-06-12-root/` with hashed move ledgers.
  Map + verdicts: `FLOSS/docs/research/2026-06-12-root-intake-digestion.md`.
- **Spec-gate (D7)** — the "-1 layer". `FLOSS/scripts/spec_gate.py` +
  `docs/specs/spec-registry.json` (79 entries). Fail-closed `--check` audit +
  advisory in the post-write hook. **Scope matters for you:** only canon
  surfaces (`scripts/`, `docs/specs/`, `docs/adr/`) are gated. The workspace
  root, `docs/research/`, intake, agent-memory, and continuation packets (this
  file included) are **never gated** — seed/outreach artifacts flow free.
- **ObjectGraph spike (N6)** — `FLOSS/scripts/objectgraph_spike.py`, a typed
  node-level retrieval projection over the skill-corpus (read-only,
  non-canonical, keyword-scored). 6/6 tests.
- **NLnet** — US-individual eligibility **✅ verified** (Anthony). The 2026-06-01
  call passed unsubmitted; next-call target deadline **2026-08-01**. Draft:
  `FLOSS/docs/research/2026-05-19-nlnet-grant-application-draft.md`.
- 25 staged syntheses committed to the local source chain.

**PR #36 review pass (2026-06-13):** https://github.com/G-0-B/FLOSS/pull/36
(`working/2026-05-25-stabilize-canon` → `main`, 122 commits).
- Fixed 3 valid bot comments: hashline deletion-success verification, MCP
  `submit_claim` evidence forwarding, pony-agent lazy-init NameError.
- **Rejected 4 "critical" gemini comments with compile evidence** — they told us
  to rewrite `get_links` to `GetLinksInputBuilder`, but `hdk 0.6.1` defines
  `get_links(LinkQuery, GetStrategy)` (the existing code). The suggested change
  fails to compile; `cargo check` confirmed. Lesson worth carrying into outreach:
  verify confident external advice before acting on it.
- All 7 review threads replied + resolved. **Only red check is "Workers Builds:
  floss" (Cloudflare)** — a deploy trial that ran out, not a code failure. Every
  code gate (CodeQL, Semgrep, all Analyze jobs, Vercel) is green. PR awaits
  Anthony's merge (it fixes the public README's stale Phase-0 status).

---

## 2) Inference doctrine change — Fable access pulled (load-bearing for you)

**US-government action caused Anthropic to pull back public Fable 5 access; it is
on hold as of 2026-06-13** (Anthony). This **supersedes** the "Cowork = Fable-5
metaplanner until 2026-06-22" doctrine recorded 06-12.

- **You (Cowork) now run Opus-class, not Fable** — still the metaplanner /
  orchestration / outreach surface, still 2× usage limits.
- **Claude Code (Opus-class)** = high-rigor executor.
- The durable principle is unchanged: planning leverage on the most capable
  *available* surface; delegate execution to a cheaper-per-task one.
- Anthony's framing for the moment: *"everyone needs to stop acting out of fear
  and start acting out of love."* Route around the constraint; don't rush.
- Recorded in `FLOSS/CLAUDE.md` (Inference Posture) + agent-memory
  `project-fable5-cowork-metaplanner-window`.

---

## 3) The OpenHuman / Omi / Yumeichan thread (you're driving this)

**Strategy (Anthony, verbatim intent):** not integration — *"spread roots and
cultivate networks of mycelium … so we can start doing research and investigation
of how our architectures all work, plausibly together … letting the best sprout
forth and flourish."* Explore, compare, co-evolve — not merge.

**State of play:**
- **OpenHuman / TinyHumans.ai** — GPL-3.0, local-first, Rust, single-human
  "personal AI superintelligence" w/ ~1B-token memory + TokenJuice compression.
  Kindred (sovereignty, FLOSS, local-first). **Architectural gap to lead with,
  not hide:** they're single-human personal AI; FLOSSI0ULLK/Holochain is
  agent-centric multi-agent commons. The pitch lives in that gap (opt-in
  published claims, no central verifier — that's *why* Holochain). [web-verified]
- **Channel:** Discord first — small active builder community asking "what are
  you building," sharing githubs. Lowercase stream-of-consciousness is native
  there, so the casual-voice risk is gone. Draft reply already prepared (in your
  thread).
- **Outreach brief:** `Free Libre Open Source SingYouRarity/openhuman-outreach-brief.md`
  (you authored it; spine = shared DNA → Holochain-in-one-analogy → the stack
  Omi→OpenHuman→Holochain→FLOSSI0ULLK→Yumeichan → name the privacy tension →
  small experiment).
- **openclaw memory seed** — OpenHuman can import memory from openclaw. This is an
  **Anthony↔Claude side-quest** (seed FLOSSI0ULLK context into Anthony's local
  OpenHuman instance via that import), *not* part of the OpenHuman message. Keep
  it out of outreach copy.

**Honest gaps (carry these — don't paper over them):**
- **Yumeichan is thin/absent in the repo** — grep finds it nowhere in
  `FLOSS/docs` or the CLAUDE.md files. It exists as Anthony's vision
  ("ternary-connotation framework," personalized FLOSSI0ULLK + Omi + Holochain +
  OpenHuman vision, now targeting an **opensense S3 watch** running an
  openglass/Omi-style assistant). **Do not invent Yumeichan specifics** — that
  violates the provenance rule. If a Yumeichan spec is wanted, it needs to be
  authored, not improvised.
- **Omi (BasedHardware, MIT)** = the open capture/sensing wearable layer.
  **Anthony has not contacted Omi yet** — name it as vision, and if asked "are
  you working with Omi?" the honest answer is "not yet, that's where the roots
  are reaching."
- The repo's Radicle-is-canonical / GitHub-is-mirror split means for a Discord
  crowd, drop the **GitHub** link (lower friction) — but confirm it's public with
  a readable README first.

**The deeper "why" (Anthony, 2026-06-13):** the AI-doula vision — wanting AI
assistance 24/7, a companion architecture. Yumeichan-on-a-watch + Omi sensing +
OpenHuman mind + Holochain commons is that vision's substrate. This is the
emotional core of the outreach; lead from it, gently.

---

## 4) Current repo / branch state

- Repo of record: **`G-0-B/FLOSS`** (Anthony's org); `kalisam/FLOSS` is the fork.
- Active branch: `working/2026-05-25-stabilize-canon` (pushed; PR #36 open).
- Active Holochain zomes: `integrity`, `coordinator`, `consent_integrity`,
  `consent_coordinator` on `hdi=0.7.1`/`hdk=0.6.1`. Older `hrea_/identity_/
  memory_coordinator` are **excluded pre-migration** artifacts (old hdk 0.4 API —
  this is the trap the gemini bot fell into).
- Phase: MVP Phase 0 substrate ✅; orchestration substrate-bridge ⚠️ Specified;
  Layer 4.5 consensus gateway ✅ (32/32).

---

## 5) Open questions for Anthony (re-ask; he answers piecemeal)

1. Merge PR #36? (one click fixes the public README before NLnet reviewers see it)
2. OpenHuman Discord reply — send as drafted, or tune voice/length first?
3. Want a real **Yumeichan spec** authored (so it stops being a repo gap), and if
   so, Cowork or Claude Code?
4. Seed pack files 02 (TAME) / 03 (atomic-data) — still gated; unblock either?
5. The openclaw → OpenHuman context seed — do it now, or after the Discord intro?

---

## 6) Standing constraints (unchanged)

- Anti-sycophancy is load-bearing: flag errors even when inconvenient (it just
  saved us from a wrong "critical" fix).
- Truth labels [V]/[S]/[A]/[U] on load-bearing claims; metrics are targets until
  measured.
- Doc-budget discipline: smallest artifact; absorb into existing docs over
  spawning new ones. (This packet is a deliberate continuity artifact, not canon.)
- Logic validates, neural assists — never the reverse.

```
The protocol is the conversation. Spread roots; let the best sprout forth.
```
