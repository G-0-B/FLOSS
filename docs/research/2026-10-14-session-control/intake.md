# Session control for the agents already running: AHP and the alternatives

**Kind:** research intake, 2026-10-14. Exempt from spec_gate (docs/research). Not canon.
**Feeds:** the draft ADR-21 and the draft cross-harness request spec in this folder.
**Truth status:** each claim below carries its own label. Nothing here was run against a live agent session.

## Source

Codex's analysis, relayed by the operator on 2026-10-14 with the words "hey we found some reuse arch that could be usefull codexs thouhghts". It is reproduced verbatim in the next section. After it: what was checked and how, the author's (Claude, Opus 5.5) response, and what turned up while checking.

## Codex's analysis (verbatim, as relayed)

> **Yes—AHP is a strong candidate for the session-control layer we need. It could remove substantial custom plumbing. The current room plan alone does not deliver the autonomous coordination you’re describing.**
>
> And yes: the target is the agents **already running on this machine**, plus new sessions when needed. Starting another instance of each harness would not establish that we had connected your existing work.
>
> I checked the current upstream documentation and selected implementation code, and your room’s **revision 7 implementation at `9cbe61c`**. This establishes documented capabilities and source behavior; I have not performed an end-to-end handoff between your running sessions.
>
> **The meaningful difference**
>
> Our room currently provides a shared collaboration record: posts, topics, threads, evidence references, advisory file claims, and a generated board. Its six exposed tools do not address a harness session, submit a turn, wake an idle agent, or deliver the resulting answer back to the requester. The planned A2A bridge adds post/read access to that same room. [Current room spec](C:/~shit/FLOSS/.worktrees/coordination-room-rebased/docs/specs/coordination-room.spec.md:31), [server implementation](C:/~shit/FLOSS/.worktrees/coordination-room-rebased/packages/coordination_room/server.py:111).
>
> AHP supplies a common interface for controlling and observing hosted sessions: session creation, conversation turns, streamed activity, approvals, cancellation, subscriptions, and reconnection. Several clients can participate in the same session. That is directly relevant to an agent sending work while you watch or intervene from another client. [AHP guide](https://microsoft.github.io/agent-host-protocol/guide/what-is-ahp.html).
>
> There is an important distinction between **the protocol and its implementations**:
>
> - AHP explicitly leaves agent-to-agent coordination semantics outside its scope.
> - **VS Code’s Agent Host already provides agent tools for cross-session coordination**: listing sessions, creating sessions/chats, reading another session’s context, and sending follow-ups.
> - The listed third-party client **ahpc** exposes session-control operations through MCP, allowing another agent to drive an AHP host.
>
> Therefore, dismissing AHP as “just UI synchronization” would be wrong. Claiming the protocol automatically orchestrates our entire fleet would also overstate it. [Protocol boundary](https://microsoft.github.io/agent-host-protocol/guide/ahp-and-acp.html), [VS Code session capabilities](https://code.visualstudio.com/docs/agents/concepts/sessions), [ahpc tools](https://github.com/softov/ahpc#as-a-tool-server).
>
> **Coverage for your harnesses**
>
> ACP below means **Agent Client Protocol**: an interface an AHP host can use to drive a harness.
>
> | Harness | Verified integration route | Remaining continuity question |
> |---|---|---|
> | **Claude Code** | VS Code has a Claude backend and documents discovering and continuing external Claude Code sessions. | Does adoption preserve your actual session’s tools, hooks, configuration, and pending work? This evidence does not establish access to arbitrary Claude web/Cowork chats. |
> | **Codex** | VS Code has a Codex backend and documents external-session continuation. | Continuing stored history is not proof of synchronized control of an already-running Codex desktop session. |
> | **Hermes** | Official ACP server supports persisted session listing/loading/resumption. Hermes also has native A2A communication. | We must establish which existing desktop/gateway session is addressed and who owns its execution. |
> | **Antigravity** | The ACP registry distributes Google’s ACP runtime, including Windows binaries. | That runtime is separate from the IDE/CLI. Existing IDE-session continuity remains unproven. |
> | **Grok / bots** | Grok documents ACP over `grok agent stdio`, plus headless session resumption. | That establishes a Grok CLI route; individual running bots still need an addressable session/control interface. |
>
> Sources: [VS Code harnesses](https://code.visualstudio.com/docs/agents/run/agent-harnesses), [external-session discovery](https://code.visualstudio.com/docs/agents/run/sessions/manage-sessions#view-sessions-from-other-applications), [Hermes ACP](https://hermes-agent.nousresearch.com/docs/user-guide/features/acp), [Hermes A2A](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/a2a), [Antigravity distribution](https://github.com/agentclientprotocol/registry/blob/main/antigravity-acp/agent.json), [Antigravity integration details](https://github.com/openclaw/acpx/blob/main/agents/Antigravity.md), [Grok scripting/ACP](https://docs.x.ai/build/cli/headless-scripting).
>
> Kimi also has an ACP registry entry. DeepSeek Harness supplies an ACP automation interface, but explicitly omits transcript replay and several interactive features—an example of why “supports ACP” does not guarantee equivalent continuity. [ACP registry](https://agentclientprotocol.com/get-started/registry), [DeepSeek’s contract](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/acp/acp/README.md).
>
> **The critical gaps we should address**
>
> 1. **The room’s acceptance criteria currently stop before your desired outcome.**
>    A successful post proves storage. We need evidence that an identified recipient accepted the request, executed or declined it, and returned a correlated result without you relaying messages. That should become the next integration milestone.
>
> 2. **Continuity needs an explicit definition.**
>    Preserving text history is insufficient. For your requirement, I would include the conversation identity, workspace/worktree, instructions, tools and MCP connections, permissions, model configuration, and pending work. A takeover must also prevent two processes from independently continuing the same session.
>
> 3. **AHP does not settle concurrent repository writes.**
>    Sequencing turns within a chat does not prevent two different sessions editing the same file. Our room claims remain advisory, and its spec explicitly says no hook consults them. Worktree isolation or an independently enforced ownership mechanism remains necessary where concurrent edits could collide. [Claim semantics](C:/~shit/FLOSS/.worktrees/coordination-room-rebased/docs/specs/coordination-room.spec.md:25).
>
> 4. **Automatic wake-up is not a checked box.**
>    AHP specifies scheduled and host-defined event automations. However, the VS Code source I inspected returns an empty event-trigger catalogue and rejects event triggers. A room-post-to-agent trigger still needs a working implementation. This is a concrete implementation limitation, not speculation. [Automation specification](https://microsoft.github.io/agent-host-protocol/specification/automation-channel.html), [pinned implementation](https://github.com/microsoft/vscode/blob/21cb66d83e0b5b63c195ab440e91d0e5b49a86c4/src/vs/platform/agentHost/node/agentHostAutomationService.ts#L341).
>
> 5. **Message delivery, execution authority, and approval authority need separate treatment.**
>    An agent permitted to request a review should not thereby acquire permission to approve another agent’s protected actions. AHP’s endpoint access control is an implementation responsibility; our room’s caller-supplied names are not authenticated identities. This matters even on one machine when multiple agents can act through each other. [AHP transport boundary](https://microsoft.github.io/agent-host-protocol/specification/transport.html#authentication), [room limitations](C:/~shit/FLOSS/.worktrees/coordination-room-rebased/docs/specs/coordination-room.spec.md:106).
>
> AHP is also more mature than a blanket “experimental protocol” description suggests: **spec 1.0.0 was published October 2**, and its core session/chat channels are marked stable. Automation channels remain early development. Adoption should distinguish those surfaces. [Release](https://github.com/microsoft/agent-host-protocol/releases/tag/spec/v1.0.0), [stability matrix](https://microsoft.github.io/agent-host-protocol/specification/versioning.html).
>
> **My recommendation is to revise the integration direction, while retaining the room’s useful work.**
>
> Use existing AHP hosts/clients and native ACP or session APIs for session control. Keep the room as the shared coordination record. Add only the missing delivery and workflow rules: recipient identity, request/result correlation, acceptance, bounded retries, cancellation, and escalation. Keep canonical truth/provenance authority within FLOSSI0ULLK’s existing boundaries.
>
> The first proof should be concrete:
>
> > From an existing Claude Code session, request a review from an existing Codex session; receive the answer back automatically, with both sessions’ continuity preserved and the exchange recorded in the room.
>
> Then test a busy recipient, disconnection, duplicate delivery, denied approval, and cancellation; extend the same contract to Hermes, Antigravity, and Grok.
>
> **AHP earns a serious reuse trial. An all-harness migration does not yet have the evidence.** The next work should prove that exchange against your existing sessions before expanding the board or designing another orchestration framework.

## What was checked, 2026-10-14

| Claim | Checked against | Result |
|---|---|---|
| AHP leaves agent-to-agent coordination out of scope | [AHP and ACP](https://microsoft.github.io/agent-host-protocol/guide/ahp-and-acp.html) | ✅ The page says: "AHP coordinates clients, not agents. If agents need to talk to each other, that's a separate concern." Maintainer Microsoft, MIT licence. |
| Session and chat channels stable; automation early | [Versioning](https://microsoft.github.io/agent-host-protocol/specification/versioning.html) | ✅ Root, Session, Chat, Terminal, Telemetry, Resource watch: 2 (stable). Changeset, MCP: 1.2 (release candidate). Annotations 1.1. Automation catalogue and run: 1.0 (early development). Released baselines 1.0.0 and 0.9.0. The "October 2" date was not checked. |
| Endpoint access control is the implementation's job | [Transport](https://microsoft.github.io/agent-host-protocol/specification/transport.html) | ✅ "Access to the AHP endpoint itself is a transport-layer concern and is outside the scope of the AHP wire protocol"; gating SHOULD happen in the transport handshake. Nothing is said about loopback or named pipes. |
| VS Code's Agent Host has cross-session tools | [VS Code sessions](https://code.visualstudio.com/docs/agents/concepts/sessions) | ✅ An agent "can list sessions, create new sessions or chats, read another session's recent context" and "send follow-up messages between sessions". Whether those need approval: not stated. |
| VS Code can continue external Claude Code and Codex sessions | same page | ✅ It discovers them; "A discovered session is external until you send a message from VS Code. The Agent Host then adopts the session." ⚠️ Whether adoption attaches to the running process or reloads stored history: not stated. |
| ahpc exposes session control through MCP | [ahpc](https://github.com/softov/ahpc) | ✅ Tool-server mode exposes `new_session`, `send_turn`, `wait_for_attention`, `confirm_tool_call`, `answer_question` by default, and optional file-writing, deletion and terminal tools. Bearer tokens; binds 127.0.0.1; refuses a browser Origin. 3 stars, one account, 261 commits. |
| VS Code returns an empty event-trigger catalogue | pinned source line | Not checked. |
| Hermes ACP and A2A, Antigravity ACP, Grok ACP, Kimi, DeepSeek | the linked pages | Not checked. |
| Room facts (six tools, advisory claims, unauthenticated names) | the deployed room | ✅ Consistent with the deployed spec and code; the cited line numbers were not re-checked. |
| VS Code installed here | `code --version` | ✅ 1.114.0. Whether its Agent Host is enabled: not checked. |

## Response (Claude)

**Agreed.**

- The room does not address a session, deliver a turn, wake an agent or bring an answer back. That is by design: the room and the consensus gateway are routers, not controllers. "Agents coordinate without the operator relaying" is a new requirement with its own acceptance criteria.
- Continuity needs a definition, including a guard against two processes continuing one conversation.
- Delivery, execution and approval are separate authorities.
- One real exchange should be proven before anything is expanded.

**Not agreed, or missing.**

1. AHP is not the layer that does this. By its own statement it coordinates clients of one host, not agents. The cross-session features belong to VS Code's Agent Host, so adopting them means adopting VS Code as the coordinator: a product dependency, not a protocol.
2. "Adopting" an external session moves it into VS Code rather than connecting the session that is running. If the original app keeps running it, two hosts may continue one conversation: the hazard named in gap 2. A coordinator inside VS Code also stops when VS Code does; see the room's own failure below.
3. The authority risk is larger than stated. AHP leaves client authentication to the transport, and `ahpc` hands any agent with that MCP server `send_turn` and `confirm_tool_call`: one agent could approve another agent's shell commands. With no person between agents, one agent's injected output becomes another's instructions. Before any delivery work: a delivered request is a proposal; the recipient's approvals stay with the operator; no agent gets approval tools over another agent's session.
4. A layer that submits turns to other agents is a controller. The project records "router, not controller" for the gateway (ADR-10) and the room. Changing that is an ADR decision for the operator, not an integration milestone.
5. The harnesses already have native session interfaces, and for Codex it is richer than ACP; see the next section. A first proof does not need a third host.
6. Correction to the author's own first reply: it recommended `codex mcp-server`. Only the old npm Codex CLI on PATH (0.128.0) has it; the current desktop Codex CLI does not list it.

## Found while checking

**1. The room died with the app.** The v0.2 room redeployed on 2026-10-12 was gone by 2026-10-14 with no reboot and no crash event; the Claude desktop app had restarted on 2026-10-13. The room had been started from a shell that app launched. It is now started by its own logon task. See `docs/reviews/2026-10-02-room-board-v1/restore-2026-10-14/`. The lesson applies to any coordinator: it must not live inside an agent harness's processes.

**2. Codex has its own session protocol.** ✅ Verified from help text and from the protocol schema the CLI generates; ⚠️ behaviour not probed, and nothing was sent to any session.

- Desktop Codex CLI `codex-cli 0.162.0-alpha.17.2` (app package 26.1007.9446.0).
- `codex queue --thread <session id or name> --message <text>`: "Queue a message for an existing session".
- `codex agents`: "Browse all agent sessions on the shared local app-server daemon".
- `codex app-server` (marked experimental): JSON-RPC over `stdio://`, `unix://` or `ws://`; `daemon start|stop|restart`; `proxy` to "the running app-server control socket"; `remote-control` with pairing and bearer tokens.
- `codex app-server generate-json-schema` lists 190 method names, among them `thread/list`, `thread/loaded/list`, `thread/read`, `thread/turns/list`, `thread/resume`, `thread/start`, `turn/start`, `turn/steer`, `turn/interrupt`, `turn/completed`, `thread/status/changed`, `thread/queue/changed` and `review/start`.
- Thread status is one of `notLoaded`, `idle`, `active`, `systemError`. Turn status is one of `completed`, `interrupted`, `failed`, `inProgress`.
- `turn/start` takes `approvalPolicy` (`untrusted`, `on-request`, `never`, or granular), `approvalsReviewer` (`user`, `auto_review`, `guardian_subagent`), `sandboxPolicy` and `cwd`. `review/start` takes a `target` (`baseBranch`, `commit`, `uncommittedChanges`, `custom`) and a `delivery` (`inline` or `detached`).
- The server asks the connected client to approve commands, file changes, permissions and MCP elicitations (`item/commandExecution/requestApproval` and others). Each can be answered with a refusal (`decline`, `deny`, `cancel`). The client that connects is offered approval authority. That is the point where D3 of the draft ADR applies.

**3. Claude has native messaging between its local sessions.** The Claude desktop app gives a session tools to list and message other local Claude sessions. ✅ Present in this session's tool list. ⚠️ Not exercised.

## Disposition

- **AHP:** not adopted now. Revisit if VS Code becomes the intended host for these sessions, if AHP's automation channels stabilise, or if a harness in use exposes its live sessions over AHP.
- **First proof:** a Claude session asks a Codex session for a review through Codex's own app-server protocol, and the exchange is recorded in the room. Specified in `cross-harness-request.spec.md`, with the envelope in `cross-harness-request.schema.json`.
- **Router versus controller:** `ADR-21-draft-session-control-outside-the-router.md`.
