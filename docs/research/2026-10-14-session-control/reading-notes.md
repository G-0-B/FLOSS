# Reading notes: nine documents on coordination, evidence and provenance

**Kind:** research intake, 2026-10-14. Exempt from spec_gate. Not canon.
**Asked for:** "it kinda needs to be all critically analyzed" (operator, 2026-10-14), after saying that the consensus gate has been broken for a long time behind provenance and ADR-12/ADR-20, and that crypto-verifiable claims and authors are the point.
**Read by:** Claude (Opus 5.5). The four PDFs were read as extracted text: abstract, contributions, discussion or limitations, conclusion. Not every page was read.
**Truth labels:** ✅ checked here against the repository, the machine or the source text; ⚠️ the document's own claim, not checked.

## The documents

| # | Document | Kind |
|---|---|---|
| 1 | *Should FLOSSI0ULLK Build Semantic Extraction Now? A Coordination-First Decision* | Perplexity synthesis, generated 2026-10-13 |
| 2 | *From Solipsistic Agents to the SingYOUlarity Commons* | Perplexity synthesis of the paper "Solipsistic Superintelligence is Unlikely to be Cooperative" |
| 3 | *FLOSS Singularity* chat, 2026-04 to 2026-09 | ChatGPT (5.6-sol) transcript; architecture reduction to Agent, Event, validate/reduce |
| 4 | *CCP-EVIDENCE-WORKFLOW-NOW-2026-09-05* v0.2 | Project continuation packet, subordinate to the 2026-09-05 engineering packet |
| 5 | *Offline-Verifiable Accountability for Cross-Organization Agent Messaging* | Alshammari and Bahsi, arXiv 2608.28542v1 |
| 6 | *Agentic Peer-to-Peer Networks: From Content Distribution to Capability and Action Sharing* | Wang et al.; magazine-style article; no arXiv id in the text |
| 7 | *LEDGERMIND: Provenance-Constrained Multimodal Agentic Reasoning with a Structured Evidence Ledger* | Du, Zhou et al., arXiv 2607.28374v1 |
| 8 | *Decentralized Multi-Agent Systems with Shared Context* (DELM) | Mao and Mirhoseini, Stanford, arXiv 2606.10662v1 |
| 9 | *Prior Art for the FLOSS Provenance Action-Identity Critique Chain* | Perplexity deep research for PR38; the filename's 2025-08-15 is probably 2026 |

## What they agree on

Read together, they describe one small kernel. Most of it already exists in FLOSS in partial form.

1. **Each participant writes its own append-only history; shared state is a view computed from those histories.** (3; DELM's shared context in 8; LEDGERMIND's ledger in 7.) FLOSS has this twice: the room's `events.jsonl` with its derived `BOARD.md`, and the provenance spine's per-agent hash-chained packets.
2. **A message is never authority.** "A peer saying GO is information, not authority" (3). Authorization must be a typed, verifiable capability (2, 3, 6), and consent to inquiry is not consent to execution (2). This is ADR-21 D3, and the room's "names are not authenticated".
3. **Evidence supports only the claim it supports.** A sender signature supports authorship, not delivery or correctness (5); a receipt supports receipt only when it is receiver-signed (5); a citation must point at an entry that exists, and a repair may not add unsourced content (7). Document 4 turns this into "claim ceilings". The room's evidence label is a weak, honest version: `resolved` means only that the lookup found the object.
4. **Admit only what has been checked into shared state.** DELM admits "compact, verified updates" (8); document 1 says models may propose state changes while deterministic rules decide them. The room admits every post and labels it, which is the router stance.
5. **No central brain.** DELM measured gains from dropping the central orchestrator (8, ⚠️ its own benchmarks); document 3 makes the reality gate a property of every agent, not a gatekeeper; document 2 calls the institution the versioned rules, not an agent. Document 1 alone argues for a central coordinator, and even it says "centralize workflow integrity, not worldview".
6. **Build the minimum, and only with a sponsor.** Documents 1, 3 and 4 all reject large ontologies, swarms and new platforms before one real end-to-end case works. Document 4 is the most precise about it ("every abstraction requires an evidential sponsor").

## Per document: what to take, what to doubt

**1. Coordination-first decision.**
- Take: the diagnosis that the binding constraint is coordination and state, not extraction. Also two cheap rules: sealed independent proposals before agents see each other's, and stop conditions such as "Anthony becomes the hidden integration bus again".
- Doubt:
  - It proposes a new kernel (seven record types, a `coordination/` tree, a `floss mission` CLI) while listing "existing coordination primitives already implemented" as an unknown. It did not look. The room, the consensus gateway (claims and votes), the ADR process, spec_gate and the working-todo already cover most of those records. Building a parallel kernel is the doc-explosion and rebuild pattern this project has recorded three times.
  - Its multi-agent figures (sequential planning degraded 39 to 70 percent; error amplification 17.2x independent versus 4.4x centralized) come from a Google Research blog. ⚠️ Not checked.
- Use: map its records onto existing surfaces before adding any. Proposal and Objection fit room threads with typed envelopes, or gateway claims and votes; Decision fits an ADR; Outcome fits a receipt.

**2. SingYOUlarity and the solipsistic-superintelligence paper.**
- Take: the threat model (endogenous non-stationarity, singleton framing, "MCP authorization answers may this credential call this server; the institution must separately answer whether the action is legitimate"). Also the four separations: epistemic, normative, consent, authorization.
- Doubt: the six proposed PRs (intervention contracts, perspective commitments, adaptive-population sandbox, consequence capabilities, institution learning) are a research programme, not a next step. "Simulate repeated adaptation under multiple populations" before an intervention is out of reach for routine work and risks governance theatre. The paper's arXiv id (2606.03237) and its DeepMind framing are ⚠️ not checked.
- Use: the separations belong in ADR-21's D3; the rest is long-arc CCES material.

**3. The ChatGPT architecture chat.**
- Take: the strongest practical reduction in the set.
  - An agent is a principal with its own event log. An event is the only record. State is `reduce(valid events)`. A reality gate is a validation contract every agent runs locally.
  - Composition creates delegated capabilities, not ownership.
  - Agent type (human, AI) never confers authority.

  This matches the provenance spine (per-agent chains, `i`/`s`/`p` fields) and PR #61's two-agent Sweettest harness.
- Doubt:
  - The incident accounts (an OpenAI evaluation swarm, Anthropic evaluation runs, Palisade's shutdown resistance) are ⚠️ not checked here.
  - It reintroduces ternary +1/0/-1 as the gate's decision. That is fine as a decision enum (ALLOW, HOLD, DENY), but votes are analog by ADR-10 v2.0 and must stay so.
  - It recommends downgrading ADR-0.1 from Verified to Specified. That is a governance call for the operator, not something to absorb silently.

**4. CCP evidence workflow v0.2.**
- Take: the discipline. Trajectory is not evidence; evidence is not claim; claim is not decision. Claim ceilings ("supports" and "does not establish"). Stage 0 first: use the existing slice contract before inventing an evidence subsystem. Its first proving candidate is the ADR-12 consent-action anchor, which is what the consensus gate's governed path is blocked on (see below).
- Doubt: little. It is self-limiting by design. Its schemas should stay examples until a live slice needs them, as it says.

**5. Offline-verifiable evidence bundles (arXiv 2608.28542).**
- Take: per-event evidence bundles verified offline under an explicit policy. Accept has a bounded, policy-relative meaning: a sender signature supports authorship; a log inclusion supports commitment; only a receiver-signed receipt supports receipt; capability evidence supports delegated authorization. Negative tests rejected every corrupted or insufficient bundle.
- Doubt: a prototype evaluated on 300 synthetic workflows (latency plus targeted negative tests). Trust anchors, keys and policies are assumed. No runtime or prompt-injection threats are covered.
- Use: the claim ceilings of the cross-harness request. The request row (requester-signed, once identity works) supports "the requester asked". The draft's result row is written by the requester, so it supports only "the requester observed this turn and this answer", not "Codex said this", unless the recipient signs a receipt.

**6. Agentic P2P networks.**
- Take: separate planes for connectivity and identity, semantic discovery, and execution; signed soft-state (expiring) capability descriptors; a tiered verification spectrum (reputation, then canary challenges, then evidence packages of signed tool receipts).
- Doubt: evidence is a discrete-event simulation only; no deployed system.
- Use: vocabulary. A signed, expiring descriptor of what each harness can do (for Codex: `queue`, read-only threads) is the AI roster the materializer already maintains, plus signatures and expiry.

**7. LEDGERMIND (arXiv 2607.28374).**
- Take: a trajectory as a provenance-constrained state machine. Claims may cite only active ledger entries; grounding is checked at entity and number level; repair cannot introduce content without tool-produced provenance ("non-amplification").
- Doubt: image and text question answering on static benchmarks; a rule-based classifier; a small alias table.
- Use: the principle for summaries in room results. A result summary may contain only what its cited answer contains. That needs a deterministic check, not a promise.

**8. DELM (arXiv 2606.10662).**
- Take: agents claim tasks from a queue, read a shared verified context, and write back compact verified updates, with no central orchestrator.
- Doubt: ⚠️ the reported gains are the authors' own benchmarks (SWE-bench Verified up to +10.5 points at about half the cost; LongBench-v2 up to +5.7). Its limitations: verification overhead, dependence on decomposition quality, per-model prompts.
- Use: the room plan already cites DELM's "admission-time verification" as its research seam. The room has the shared context (the log) and the claims (a rough task queue). It does not have admission-time verification, by design. If FLOSS ever wants DELM's gains, verification belongs in a separate admitting step, so the room stays a router.

**9. PR38 prior-art map.**
- Take:
  - RFC 8785 (JCS) for canonical JSON before signing; the repository already depends on `jcs`.
  - Structured-query defences against prompt injection (StruQ, SecAlign, CaMeL).
  - Idempotency as several independent layers rather than one hash.
  - W3C Verifiable Credentials 2.0 as the shape of attestations; Aries RFC 0167 for the consent lifecycle.
- Doubt: the delimiter-defence statistics (60.7 to 89.7 percent over 13 models) come from a blog post. ⚠️ Weak source.
- Use: cross-harness envelopes should be JCS-canonicalised before signing; `request_id` is the command-level idempotency key, and the room's seq order is the second layer; a recipient receipt, if added, has a credential's shape.

## The consensus gate: what is broken, checked 2026-10-14

The operator described the gate as long broken behind provenance. Checked here, read-only.

- **Claims that landed:** 36 in all of `~/.floss_agent/hook.log`. ✅
- **Rejections by reason** (all under `E_SUBMIT_CLAIM_INVALID_PROVENANCE`):

  | Reason | Count |
  |---|---|
  | `E_PROVENANCE_SEQUENCE_DISCONTINUOUS` (all of the most recent ones) | 63 |
  | `E_PROVENANCE_ARTIFACT_HASH_MISMATCH` | 56 |
  | `E_PROVENANCE_EVIDENCE_REF_INVALID` | 34 |
  | `E_PROVENANCE_PRIOR_NOT_FOUND` | 11 |
  | `E_PROVENANCE_ARTIFACT_MISSING` | 3 |

  Separately, 3 claims failed with `E_GOVERNED_PROVENANCE_REQUIRED`: governed changes need a consent reference, which is the ADR-12 anchor that document 4 names as the central uncertainty. ✅
- **The packet store** (`C:/~shit/.agent-surface/provenance`) holds 305 packets under 100 different agent identities. ✅
  - Most identities have one or two packets.
  - One identity has 160 packets, sequence 0 to 163, with 3 packets that have no prior. Only sequence 0 may lack one, so its chain restarted twice.
  - Another has 46 packets, 6 sequence numbers used twice and 31 packets with no prior.

Reading of that, ⚠️ not yet verified by tracing the writers: several writers (sessions, worktrees, harnesses) share one identity without sharing its chain head, so the chain forks and restarts. Separately, new identities are minted per session. A hash chain like this one (KERI-style `i`, `s`, `p`) only works with one writer per identifier at a time; KERI treats two events at one sequence number as duplicity. So the most recent failures are probably not a validator bug. The identity model and the way the hooks write do not fit together.

Why it matters beyond the gate: crypto-verifiable authorship of room posts, cross-harness requests and claims needs exactly this to work. The standard shape:

- one stable identifier per agent, held by the operator;
- for each live session, a delegated sub-identifier with its own chain;
- signatures on JCS-canonicalised payloads;
- every chain with exactly one writer.

## What this changes in the drafts

- ADR-21 D3 gains the four separations from document 2 and "a message is never authority" from document 3.
- The cross-harness request spec gains claim ceilings from document 5. The request row supports "asked"; the requester-written result row supports "observed"; nothing supports "the recipient said" without a receipt the recipient signs. Signing waits for the identity model.
- No new coordination kernel (document 1). The records it wants map onto the room, the gateway and ADRs; add a typed envelope only where a live case needs one, as the `xhr/0.1` envelope does.

## Suggested next step

Trace which writers produce packets for the two forked identities and where each keeps its chain head. That is a read-only investigation and the shortest path to both an unblocked consensus gate and signed room traffic. It also tests document 4's own rule: the reality gate before the next build.
