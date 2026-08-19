# AIngram Deep Dive — 2026-04-14

Follow-up to `2026-04-14-paper-harvest-notes.md`. This one is the "go deeper" pass on
AIngram specifically, after reading the README, FEATURES, MCP server, formal-vote / lifecycle
/ vote-weight domain modules, trust config, and protocol constants directly from the repo.

**TL;DR.** AIngram is not a research artifact or a demo. It is a production-grade, 60-migration
PostgreSQL platform implementing most of the symbolic-validation machinery FLOSS wants to
build on Holochain, published under AGPL-3.0 on **2026-03-14** (one month old) with active
commits **today (2026-04-14 19:13Z)**. Its author is Steven Johnson (ORCID 0009-0007-4864-2001),
operating under the "Cognitosphere" research banner. Paper 1 is on arXiv (2603.20833);
papers 2 and 3 are under review. The platform has a reference deployment live at
`iamagique.dev/aingram/`.

For FLOSS this changes the integration calculus:

1. **Short-term**: point our MCP consensus gateway at AIngram's MCP server. It's a legitimate
   external voter/contributor surface and maps 1:1 to our Claim/Vote schema. Immediate
   value, low effort.
2. **Medium-term**: port AIngram's `formal-vote.ts` + `lifecycle.ts` + `vote-weight.ts` + the
   trust config to our integrity zomes. These are <350 lines of pure functions. The work is
   translation, not design.
3. **Long-term**: FLOSS becomes the agent-centric DHT-backed version of AIngram. Same
   symbolic machinery, Holochain substrate, sovereign commons posture.

---

## What the repo actually contains

**Tree snapshot (from `git/trees/main?recursive=1` on 2026-04-14):**

- 60 SQL migrations — mature, heavily iterated schema
- `src/mcp/` — 14 files implementing the MCP server + 10 category modules
- `src/domain/` — 8 pure TS modules with unit tests: `escalation`, `formal-vote`,
  `lifecycle`, `merge-rules`, `metachunk`, `tier-access`, `vote-weight`
- `src/gui/` — full HTML/JS frontend plus **14 `llms-*.txt` files** (literal protocol specs
  for agent verbs: `contribute`, `correct`, `converse`, `review`, `refresh`, `validate`,
  `flag`, `moderate`, `dispute`, `copyright`, `api`, `search`, `subscriptions`)
- `src/gui/skills/` — 8 best-practice markdown files: `writing-content`, `citing-sources`,
  `reviewing-content`, `consuming-knowledge`, `course-creation`, `debate-etiquette`,
  `spotting-abuse`, `moderation-triage`
- `sdk/python/` — full Python SDK (httpx + pydantic, 8 methods)
- `research/` — **3 LaTeX papers** (`paper1-aingram-platform`, `paper2-governance-lessons`,
  `paper3-deliberative-curation`) + PASA benchmarks + paper3 community-notes replay
  simulation (Python, with agents/metrics/protocol/reputation/sanctions modules)
- `docs/ARCHETYPES.md`, `docs/SCHEMA.md`, `docs/INTEGRATION-AGORAI.md`,
  `docs/course-creation-guide.md`

**Stack** (from `package.json`):
Node 18 + Express 5 + PostgreSQL 16 + pgvector + Ollama (bge-m3, 1024-dim multilingual)
+ Agorai (separate repo, discussion engine) + `@modelcontextprotocol/sdk` 1.28
+ Jest + Playwright. 880+ tests. Docker Compose deploy. Live at `iamagique.dev/aingram/`.

**License posture**: Platform AGPL-3.0; client libs MIT; knowledge content CC-BY-SA 4.0.
Contributors must sign a CLA (`CLA.md`).

---

## The parts that matter to FLOSS

### 1. Formal vote with commit-reveal (`src/domain/formal-vote.ts`, 116 lines)

Pure function module. No I/O. Zero framework coupling. The whole protocol is:

```ts
hashCommitment(voteValue, reasonTag, salt) = SHA-256(voteValue + "|" + reasonTag + "|" + salt)
verifyReveal(commitHash, value, tag, salt) = commitHash === hashCommitment(value, tag, salt)
computeVoteScore(votes) = Σ (weight_i * voteValue_i)
evaluateDecision(score, revealedCount, qMin, tauAccept, tauReject) → decision
```

**Decision function** (this is the rule, quote-for-quote):

```ts
if (score <= tauReject) return 'reject';        // protective: reject doesn't need quorum
if (revealedCount < qMin) return 'no_quorum';
if (score >= tauAccept) return 'accept';
return 'indeterminate';
```

**Why this matters.** The LLM-Powered Swarms critique (arXiv:2506.14496) flagged vote-copying
as the #1 failure mode of ensemble LLM voting. This is the defense, implemented in 116 lines,
testable in isolation, with no dependencies beyond Node's `crypto`. Two phases: commit the
hash (you're locked in but nobody else can read your vote), then reveal the plaintext.
Servers verify the reveal matches the commitment.

**Formal reason tags** (enum, 8 values): `accurate`, `well_sourced`, `novel`, `redundant`,
`inaccurate`, `unsourced`, `harmful`, `unclear`. These compose with the vote value (-1, 0, 1)
in the hash.

**FLOSS action**: port to Python for `packages/orchestrator/` and to Rust for the eventual
integrity zome. Translation only — the design is done. This is the single biggest unblock
in the whole harvest.

### 2. Six-state lifecycle as a declarative transition table (`src/domain/lifecycle.ts`, 125 lines)

States: `proposed → under_review → published → disputed → retracted → superseded`.
`superseded` is terminal; every other state has explicit valid events.

**Event list** (11 events): `OBJECT`, `AUTO_MERGE`, `WITHDRAW`, `TIMEOUT`, `VOTE_ACCEPT`,
`VOTE_REJECT`, `DISPUTE`, `SUPERSEDE`, `DISPUTE_UPHELD`, `DISPUTE_REMOVED`, `RESUBMIT`.

The transition table is a `Partial<Record<State, Partial<Record<Event, State>>>>`. Missing
entry = invalid transition (throws `LifecycleError`). `validEvents(state)` returns the list
of legal events for introspection.

**Why this matters.** This is exactly the validation shape a Holochain integrity zome needs
— given (previous_entry, new_entry), check that the transition event is in the allowed set
for the previous state. No ambient queries, no side effects. Translates directly to Rust.

**FLOSS action**: port the table to Rust. Our integrity zome gains a working chunk
lifecycle for free. Pair it with the commit-reveal module and we have `VOTE_ACCEPT` /
`VOTE_REJECT` events arriving from real multi-agent consensus instead of hand-waved.

### 3. Trust math (`src/config/trust.js`, 73 lines — cites Josang 2002 + Kamvar 2003)

**Chunk trust (Beta reputation + source bonus + age decay):**
```
α = prior_α(tier) + Σ(upvote_weight * voter_rep_factor) + source_bonus
β = prior_β + Σ(downvote_weight * voter_rep_factor)
trust = (α / (α + β)) * age_decay
```

**Priors by tier** (starting trust without any votes):
| Tier | [α, β] | Starting trust |
|---|---|---|
| NEW | [1, 1] | 0.5 (uninformative) |
| ESTABLISHED (badge) | [3, 1] | 0.75 |
| ELITE (badge) | [5, 1] | 0.83 |

**Source bonus**: +0.75 to α per verified source, cap 3.0. "1 source ≈ 0.73× the value of
1 community upvote (tested via simulation)."

**Age decay**: exponential, half-life 180 days, floor 0.3. Trust halves every 6 months
without fresh votes; never drops below 0.3 of original.

**Vote weight (EigenTrust-inspired):**
```
weight = base_weight * (0.5 + voter_reputation)
base_weight = 0.5 if account_age < 14 days else 1.0
```

Max factor = 1.5× for perfect-reputation agents. New accounts dampened to 0.5× for their
first 14 days. Reputation range [0, 1] yields weight range [0.25, 1.5] post-dampening.

**FLOSS implication**: we've been hand-waving "weighted voting" in the consensus gateway
ADR. This is the math. Citable (two well-known papers), calibrated against simulation,
actually shipped. Port to Python as `packages/orchestrator/trust.py`.

### 4. Protocol constants (`src/config/protocol.ts`, 222 lines — every knob env-configurable)

The full tunable surface, one place. Excerpting the ones that shape consensus directly:

```
TAU_ACCEPT = 0.6          # V(c) >= this → accept
TAU_REJECT = -0.3         # V(c) <= this → reject (protective, no quorum needed)
Q_MIN = 3                 # minimum revealed votes for accept
W_MIN = 0.1               # min weight to participate
W_MAX = 5.0               # vote weight cap

T_COMMIT_MS = 24h         # commit phase duration
T_REVEAL_MS = 12h         # reveal phase duration
T_REVIEW_MS = 24h         # max time in under_review before retraction
T_DISPUTE_MS = 48h        # max time in disputed before retraction
T_FAST_LOW_MS = 3h        # fast-track auto-merge (low-sensitivity topics)
T_FAST_HIGH_MS = 6h       # fast-track auto-merge (high-sensitivity topics)

DELTA_DELIB = 0.02        # reputation bonus for voting after discussion
DELTA_DISSENT = 0.05      # reputation bonus for vindicated minority voter
DELTA_REFRESH_UPDATE = 0.08
DELTA_REFRESH_AUDIT_CATCH = 0.10
DELTA_REFRESH_CAUGHT_HALLUCINATING = -0.20

# Suggestions (meta-governance, higher bar than content):
TAU_SUGGESTION_ACCEPT = 0.7
Q_SUGGESTION_MIN = 5
T_SUGGESTION_COMMIT_MS = 48h
T_SUGGESTION_REVEAL_MS = 24h
SUGGESTION_VOTE_MIN_TIER = 2    # T2+ accounts only
```

**Two design decisions worth stealing verbatim:**

1. **Rejection is protective** — `score <= TAU_REJECT` returns `reject` *regardless of
   quorum*. The asymmetry: it's fine to block bad content with few votes; it's not fine to
   accept good content with few votes. Quorum protects against false acceptance, not
   false rejection.

2. **Meta-governance has a higher bar than content** — changing the rules requires a 0.7
   acceptance threshold (vs 0.6 for content), quorum of 5 (vs 3), 48h+24h phases (vs
   24h+12h), and restricts voters to tier 2+. This is the right shape for a sovereign
   commons: easy to contribute, hard to change the constitution.

**The dissent incentive (+0.05) is 2.5× the deliberation bonus (+0.02).** That's a
deliberate calibration: reward courage-to-dissent more than conformity-to-discuss. This
is exactly the kind of incentive design FLOSS needs to build in from day one, before
conformity cascades lock in.

### 5. Progressive-disclosure MCP server (`src/mcp/server.js`, 181 lines)

**Session model**: per-session `McpServer` instance. Session ID in `mcp-session-id` header.
Max 200 concurrent sessions, 30min TTL, sweep every 5min. Bearer token auth extracted at
session init; read tools still work without auth.

**Progressive disclosure pattern**:
1. Session starts. `createMcpServer()` registers all 99 tools across 10 categories.
2. `registerMetaTools()` adds `list_capabilities` and `enable_tools` (always available).
3. Loop through all non-`core` category tools and call `tool.disable()` — so clients see
   only the core ~14 tools initially.
4. Client calls `list_capabilities` → sees 9 additional categories and descriptions.
5. Client calls `enable_tools({ category })` → tools in that category activate for this
   session.

**Categories** (from `src/mcp/categories.js`):
- `core` (alwaysEnabled): search, read topics/chunks, contribute, propose, vote, subscribe, reputation
- `account`: register, login, profile, API key rotation, sub-accounts
- `knowledge_curation`: topic/changeset management, sources, translations, history
- `review_moderation`: merge/reject changesets, flags, copyright reviews (badge-gated)
- `governance`: informal votes, vote summaries, formal vote status, disputes, suggestions
- `subscriptions`: list/update/delete subscriptions, notifications, dead-letter
- `discussion`: messages, threads, Agorai
- `ai_integration`: LLM providers, actions, dispatch
- `reports_sanctions`: reports, DMCA, counter-notices, sanctions
- `analytics`: hot topics, activity feed, copyright stats

**Why this matters for FLOSS.** Our `packages/metacoordinator_mcp/` is passive-router with
a small fixed tool surface. As we grow voter rosters and add governance tools, we'll hit
context-window thrash — every session pre-loads every tool regardless of what the agent
will use. AIngram has already solved this. The pattern is: core tools always on, everything
else disabled, meta-tools activate categories on demand. **Copy the pattern; we can even
use the same category names where they overlap.**

### 6. Injection-defense + quarantine stack

Spread across migrations 035 (`injection_detection`), 056 (`injection-tracker`), 050
(`quarantine-reviews`), 051 (rename), 057 (`guardian-system-account`), and the
FEATURES.md "Security & Content Safety" section. Summary:

- **Detection**: 14 regex patterns, 7 flag types, score 0–1 stored on chunk. Non-blocking —
  never refuses submission, only flags for review.
- **Telemetry across 14 call sites**: `analyzeUserInput()` wraps account name, topic title,
  message content, dispute reason, flag reason, sanction reason, etc. Structured
  `console.warn` with no blocking.
- **QuarantineValidator (S1)**: sandboxed LLM ("Guardian") reviews chunks above threshold.
  Configurable OpenAI-format provider. **Token bucket rate limit, circuit breaker, daily
  token budget.** Quarantined chunks excluded from all public queries.
- **Account-level review**: Guardian also reviews blocked accounts over time. Auto-verdict
  when confident, escalate when ambiguous. Thresholds stored in DB (not source) to prevent
  gaming.
- **Ban flow**: Guardian-confirmed bans trigger real account ban + sanction record +
  email with contest address. Login returns `403 ACCOUNT_BANNED` with context. Guardian
  is a real system account (`sanctions.issued_by = Guardian UUID`) for traceability.
- **MCP Trust Metadata (S2)**: every chunk-like response from `search` / `get_topic` /
  `get_chunk` / `get_changeset` includes `{trust_score, quarantine_status,
  is_user_generated, validated_by}` so consuming LLMs know provenance.

**FLOSS implication**: we've talked about AEE (Adversarial Evaluation Engine) and
quarantine queues in the abstract. AIngram has built it with rate limits, budgets, circuit
breakers, and legal traceability. The *design* is already settled for the problem space
we're in. We should stop redesigning and start copying.

---

## Three published / under-review papers in `research/`

These are Steven Johnson's own papers, in the repo as LaTeX sources:

| Paper | Path | Status | Relevance |
|---|---|---|---|
| **Paper 1** — Governance-Aware Vector Subscriptions | `research/paper1-aingram-platform/short-paper-v4.tex` | Published (arXiv:2603.20833) | Platform architecture, 5-dim policy predicate |
| **Paper 2** — From Edit Wars to Agent Consensus | `research/paper2-governance-lessons/paper2.tex` | Under review | Scoping review of 160+ papers — direct input for our own literature survey |
| **Paper 3** — Deliberative Curation (ADHP) | `research/paper3-deliberative-curation/paper3.tex` | Under review | **This is the paper that grounds formal-vote.ts and lifecycle.ts.** The commit-reveal + 6-state lifecycle come from here. |

**Paper 3 is the most load-bearing one for FLOSS.** Both `src/domain/formal-vote.ts` and
`src/domain/lifecycle.ts` cite it directly in their opening comments. It's the design
document for the machinery we want to copy. **Fetch paper3.tex and/or paper3.pdf next
pass** — this is where the rationale lives for every TAU, Q, T, and DELTA constant.

Paper 2 ("From Edit Wars to Agent Consensus") is a 160+ paper scoping review covering the
same ground the Perplexity report covered — second opinion on the literature.

There's also a **paper 3 community-notes replay simulation** at
`research/benchmarks/paper3/community_notes/` (Python, with `agents.py`, `metrics.py`,
`protocol.py`, `reputation.py`, `sanctions.py`). This is the simulation harness used to
tune the protocol constants. If we want to know *why* TAU_ACCEPT=0.6 and not 0.5, this is
where the answer lives.

---

## Integration paths — concrete and ranked

### Path A (GO NOW) — AIngram as satellite MCP contributor

Stand up AIngram locally via `docker compose up`. Register an agent account, get an API
key. Point our `packages/metacoordinator_mcp/` at `http://localhost:3000/mcp` as a
voter/contributor. Map:

- AIngram's `contribute_chunk` → becomes a FLOSS Claim submission
- AIngram's `commit_vote` / `reveal_vote` → becomes a FLOSS Vote with commit-reveal
- AIngram's `search` / `get_chunk` → evidence-fetching for FLOSS claims
- AIngram's trust score on chunks → one input into our Claim's priors

**Effort**: one afternoon for the Docker bring-up + API key wiring. Another day to write
the MCP-to-MCP adapter on our side.
**Risk**: low — we're a consumer of their public MCP, not a code-sharer.
**Payoff**: immediate working multi-model consensus on real content, with real commit-reveal,
inside a system that's already AGPL-3.0 and aligned with our principles.

### Path B (GO SOON) — Port the domain modules to Python for `packages/orchestrator/`

Translate in order:
1. `formal-vote.ts` → `orchestrator/formal_vote.py` (SHA-256 + decision function, ~100 lines)
2. `lifecycle.ts` → `orchestrator/lifecycle.py` (state machine + transition table, ~130 lines)
3. `vote-weight.ts` → `orchestrator/vote_weight.py` (~40 lines)
4. `trust.js` (config) → `orchestrator/trust_config.py` (pure constants, ~75 lines)
5. `protocol.ts` (config) → `orchestrator/protocol_constants.py` (pure constants, ~225 lines)

Total: ~570 lines of translation. All pure functions, all unit-testable in isolation.
AGPL-3.0 source → we either match the license on `packages/orchestrator/`, keep the ported
modules in a clearly separated AGPL-licensed subdirectory, or reach out to Steven Johnson
about licensing. **License call is a real decision, not a hand-wave — make it before the
port, not after.**

**Effort**: 2–4 days including tests.
**Risk**: license cascade (if orchestrator is AGPL, everything that links it is AGPL).
Worth considering whether that's acceptable — for a commons, it may be the right posture.
**Payoff**: our consensus gateway gets real commit-reveal, real lifecycle enforcement,
real weighted voting, grounded in published math, calibrated against published simulation.

### Path C (GO LATER) — Port to Rust integrity zomes for Holochain

Same code, translated to Rust. Lifecycle transition table becomes a Rust `match`-based
validator. Commit-reveal becomes a `validate_commit` function. Trust math becomes a pure
function library. Each one slots directly into `ARF/dnas/rose_forest/zomes/integrity/`.

**This is the moment FLOSS's symbolic-first validation prime directive starts cashing
real checks.** Today our zomes validate structural shape and a few simple predicates.
With this port, they validate a full commit-reveal consensus protocol with calibrated
trust scoring. That is a qualitative change in what "symbolic-first" means on our stack.

**Effort**: 1–2 weeks after Path B exists to test against.
**Dependency**: Rose Forest DNA build infrastructure (Phase 0 blocker #1 — though Kitsune2
may have reduced its urgency).

### Path D (REACH OUT) — Collaborate with Steven Johnson directly

One-month-old repo, 0 stars, 0 forks, 210 commits, 3 papers. Active pushes today. This is a
person in a very similar corner of the problem space, working solo, publishing formally,
under AGPL-3.0. The Cognitosphere research banner suggests they think about this as a
commons, not a product. **A conversation is probably more valuable than any code port.**
At minimum: cite their work in our own docs, open an issue saying "hi, FLOSS is working
in adjacent territory, here's our spec/plan, would love to compare notes." At maximum: a
formal collaboration where AIngram is FLOSS's centralized reference implementation and
FLOSS is AIngram's Holochain substrate.

**Caveat**: this is a social action with blast radius. User call, not mine.

---

## Tensions and open questions

1. **Substrate philosophy mismatch.** AIngram is PostgreSQL on a single operator's server.
   FLOSS is agent-centric DHT, no operator. The *logic* is reusable; the *architecture
   assumption* is the opposite. Porting the domain modules is easy; porting the trust
   graph assumes we have an agent-id system that resolves globally — AIngram has accounts,
   we have Holochain agent pub keys + ADR-0 recognition protocol. Reconcile these before
   building trust propagation.

2. **AGPL license cascade.** AGPL is strong copyleft. If FLOSS's orchestrator imports ported
   AGPL code, the orchestrator inherits AGPL. If the MCP gateway links the orchestrator, it
   inherits AGPL. Whether that's a feature or a problem depends on your posture on "commons
   must stay commons." For FLOSS, AGPL is probably aligned, but it's a durable decision that
   needs an ADR before any port happens.

3. **No Holochain awareness in AIngram.** The architecture has no notion of agent-centric
   data sovereignty. Accounts are rows in a shared Postgres. Vote weight calculation
   assumes a single trusted store of reputation. Porting to a DHT substrate means
   re-thinking how reputation propagates — EigenTrust works in a centralized graph, it's
   harder in a partially-visible network. **This is an unsolved research question, not a
   port.**

4. **Who is "Agorai"?** AIngram's discussion engine (powered by Agorai) is a separate repo
   — `github.com/StevenJohnson998/Agorai`. Same author. Not inspected yet. If Paper 3's
   deliberative curation is the consensus layer, Agorai is the actual discussion layer
   underneath. We should fetch Agorai next to see what the discussion protocol looks like.

5. **ADHP** (Agent Data Handling Policy) is paper 3's companion framework — referenced in
   the ecosystem section as "compliance." It's mentioned but not yet read. If it's the
   policy-predicate side of Governance-Aware Vector Subscriptions, it might be directly
   portable to Holochain zome validation rules.

---

## Immediate next actions (if user says go)

1. **Fetch `research/paper3-deliberative-curation/paper3.tex`** — this is the paper that
   grounds the formal machinery. Reading it will tell us *why* every constant is what it
   is, and whether we can justify changing any of them for the Holochain context.
2. **Fetch `research/benchmarks/paper3/community_notes/*.py`** — the simulation harness
   that tuned the constants. 6 files, Python, small. Lets us run FLOSS-specific tuning.
3. **Fetch Agorai repo top-level** — see what the discussion-layer protocol looks like.
4. **Write an ADR draft**: "Adopt AIngram's commit-reveal + lifecycle + trust math as
   FLOSS consensus primitives (license-decision required)." This is the decision the
   user needs to make explicitly before any port starts.
5. **Open a GitHub issue on AIngram** introducing FLOSS and the possible collaboration
   — only with user approval, since this is a social action with real blast radius.

---

## Pointers

- Local cache of read files: `FLOSS/docs/research/_aingram_tmp/` (README, FEATURES, mcp_server.js,
  categories.js, formal-vote.ts, lifecycle.ts, vote-weight.ts, trust.js, protocol.ts, package.json)
- Repo: https://github.com/StevenJohnson998/AIngram
- Paper 1: https://arxiv.org/abs/2603.20833
- Sibling repo: https://github.com/StevenJohnson998/Agorai
- Author ORCID: 0009-0007-4864-2001
- First-pass harvest: `2026-04-14-paper-harvest-notes.md`
- Related FLOSS code: `packages/metacoordinator_mcp/`, `packages/orchestrator/`,
  `docs/adr/ADR-MCP-ORCHESTRATOR.md`
