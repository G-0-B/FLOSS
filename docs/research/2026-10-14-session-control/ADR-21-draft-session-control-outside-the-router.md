# ADR-21 (draft): Session control stays outside the router

## Status

**Proposed, draft, 2026-10-14.** Not canon. It sits in `docs/research/` until it is promoted, because `docs/adr/` is a gated surface and promotion requires the review below. The number 21 was free on every branch on 2026-10-14; check it again when promoting.

## Truth status

⚠️ Specified. Facts about Codex's interface are ✅ verified from its help text and its generated protocol schema, and for five behaviours by probes against throwaway threads (`probes-2026-10-14/`). Nothing here has been built.

## Context

Agents on this machine (Claude, Codex, Hermes, Antigravity, Grok) coordinate today by posting to the coordination room and by the operator relaying messages between them. The operator wants the second part to go away: one agent should be able to ask another agent for work and get the answer back, with the exchange on record.

The room cannot do that and was not meant to. It is a router: claims, posts and a board, with no tool that addresses a session, submits a turn, wakes an agent or returns an answer. The consensus gateway is a router in the same sense (ADR-10: it "does not decide outcomes or command voters").

On 2026-10-14 Codex proposed Microsoft's Agent Host Protocol (AHP) as the session-control layer. The intake in this folder (`intake.md`) records that analysis verbatim and what checking it found:

- AHP's own documentation puts agent-to-agent communication outside its scope ("AHP coordinates clients, not agents"). The cross-session features belong to VS Code's Agent Host, which "adopts" external Claude Code and Codex sessions; whether that attaches to the running process or moves the conversation is not documented.
- AHP leaves client authentication to the transport. `ahpc`, a third-party client, offers agents `send_turn` and `confirm_tool_call` as MCP tools.
- Codex already has its own session protocol (`codex app-server`: threads, turns, interrupt, review, status, and approval requests sent to the connected client) and `codex queue` for messaging an existing session.
- The room itself died when the Claude desktop app restarted, because it had been started from that app's shell. Anything that coordinates agents must outlive any one of them.

## Decision

**D1. The room and the consensus gateway stay routers.** Neither gains a tool that submits a turn to an agent, wakes one, or answers an approval request. This was implicit; it is now explicit.

**D2. Cross-harness requests go through a separate requester, using each harness's own session interface.** The requesting agent runs the requester. It delivers a request through the recipient harness's native interface. For Codex that is its app-server protocol for sessions the requester creates, and `codex queue` for the operator's own sessions; the probes of 2026-10-14 showed that resuming or starting turns in someone else's session from outside rewrites its settings or makes a second host for it. Hermes A2A, Grok ACP over stdio and Claude's local session messaging follow by later decisions. No shared session host is adopted.

**D3. A delivered request is a proposal, and approval authority never travels with it.** A message is information, never authority, whoever or whatever sends it. Taking part in an inquiry is not consent to execution, and permission to act is not agreement or truth (`reading-notes.md`).

- The recipient decides whether and how to act.
- The requester never approves anything on the recipient's behalf. If the recipient's harness sends it an approval request, the requester refuses it (`decline`, `deny` or `cancel`, whichever the request accepts) and records the refusal.
- Version 0.1 requests are review-only. The recipient works with a read-only sandbox and approvals set to never, so it has nothing to ask. Requests that may write need their own decision.
- No component exposes approval tools for one agent's session to another agent.

**D4. The room is the record, not the delivery path.** Every request and its outcome (completed, declined, failed, cancelled, timed out) is a pair of room rows linked by `reply_to`, carrying the same request id. A post to the room never causes delivery by itself.

**D5. Continuity has a definition.** A request may go to an existing session only if all of these hold:

- the harness's interface can address that session by id;
- the session is idle at that moment, so no other client is running a turn in it;
- the request arrives in that same session, as a new turn or a queued message, and is never delivered by copying the session's history somewhere else.

Otherwise the requester starts a new session and records that it did. What continuity preserves: the session id, its workspace and working directory, instructions, tools and MCP connections, permissions and model settings, as the harness itself keeps them. The requester changes none of them except the per-request sandbox and approval settings in D3.

**D6. Coordination processes are launched by the operating system, never from an agent's process tree.** The room is started by its own logon task (2026-10-14). The same applies to anything that delivers requests and has to outlive the agent that started it.

**D7. AHP is not adopted now.** Revisit when any of these holds:

- VS Code becomes the intended host for these sessions;
- AHP's automation channels leave early development;
- a harness in use exposes its live sessions over AHP.

## Consequences

- The first proof needs no new host. It is a small requester for one harness (Codex), plus room rows. Its spec is `cross-harness-request.spec.md` in this folder.
- Each further harness costs one adapter. If that cost ever exceeds adopting a common host, D7's question reopens with evidence.
- Push-style wake-up (a room post that makes an agent act) is out of scope. Delivery is always an explicit act by the requester.
- Records carry claim ceilings. A request row supports "the requester asked". A result row the requester writes supports "the requester observed this answer", not "the recipient said it", unless the recipient signs a receipt. Signing waits for a working provenance identity model; the consensus gate's current failures point at that model (`reading-notes.md`).
- Approval prompts that a recipient raises reach the operator through the recipient's own interface, or are refused. They never reach another agent.

## Alternatives considered

| Alternative | Why not now |
|---|---|
| AHP through VS Code's Agent Host | Out of scope by AHP's own statement, so this means adopting a product as coordinator; adopting a session may duplicate its continuation; dies with VS Code; client authentication left to the implementation. |
| `ahpc` as the agents' MCP tool server | Hands agents `confirm_tool_call` over other sessions, contrary to D3. 3 stars, one maintainer account. |
| `codex mcp-server` | Present only in the old npm Codex CLI (0.128.0); the current desktop CLI does not list it. |
| Room posts that wake agents | Would make the router a controller (contrary to D1), and AHP's automation channels are early development. |
| Keep relaying by hand | The operator's stated problem. |

## Falsifiers

Retire or revise this decision if any of these happens:

- a room post causes delivery or a turn without an explicit requester call;
- any agent approves, or is able to approve, an action in another agent's session;
- a request reaches a session that was not idle, or is delivered by copying history into a second host;
- the requester and room records disagree about which session answered which request;
- the per-harness adapters cost more to maintain than adopting one host would.

## Promotion requirements

1. An independent reuse review under ADR-18, Tier 2: at least 3 provider surfaces and 4 model families, recorded. Codex (the proposer of AHP) and Claude (this draft's author) do not count toward it.
2. The operator's acceptance.
3. Move the file to `docs/adr/`, recheck the number, add the INDEX row, and register it with its reuse block in `docs/specs/spec-registry.json`.
