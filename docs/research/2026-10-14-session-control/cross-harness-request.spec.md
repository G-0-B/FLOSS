# Cross-harness request, first proof (Claude asks Codex for a review)

```yaml
id: "cross-harness-request-spec"
version: "0.1.0-draft"
kind: "spec"
status: "Draft"
created: "2026-10-14"
truth_status: "Specified. Codex interface facts verified from its generated protocol schema (codex-cli 0.162.0-alpha.17.2); behaviour unprobed; nothing built."
schema: "cross-harness-request.schema.json"
decision: "ADR-21 (draft) in this folder"
approval: "none yet; lives in docs/research until promoted"
```

## What this is

The smallest piece that lets one agent ask another for work and get the answer back without the operator relaying, with the exchange on record. Version 0.1 covers one direction and one kind of work: a Claude session asks a Codex session for a **review**.

Three parts, kept separate (ADR-21 D1 to D4):

- the **requester**: a small program the requesting agent runs. It delivers the request through Codex's own session interface, waits for the outcome, and records both in the room;
- the **recipient**: a Codex session, existing or new, which decides what to do with the request;
- the **room**: the record. It delivers nothing.

## Not in this version

- Requests that may write files or run commands with side effects.
- Any harness but Codex as recipient.
- Any delivery caused by a room post (no wake-up).
- Any agent approving anything for another agent, ever (ADR-21 D3).

## Roles and names

- `request_id`: a version-4 UUID the requester generates. It identifies one request everywhere: both room rows, the Codex turn (`clientUserMessageId`), and the requester's log.
- `from.agent_id`: the name the requester posts under. Like every room name it is unauthenticated, and the spec relies on it for nothing but attribution.
- `to.session`: a Codex thread id, or null for a new session.

## Lifecycle

```
requested ──► delivered ──► completed
    │             ├──────► declined     (the recipient said no)
    │             ├──────► failed       (an error after delivery)
    │             ├──────► cancelled    (the requester interrupted it)
    │             └──────► timed_out    (no outcome in time; interrupted)
    ├──────────────────────► busy         (target session not idle; nothing delivered)
    └──────────────────────► undeliverable (no route to the recipient; nothing delivered)
```

Two room rows record it: a request row before delivery, and a result row with the outcome. `busy` and `undeliverable` mean nothing reached the recipient, and the result row says so.

## Room records

Both rows go to the v0.2 room through its ordinary tools; nothing in the room changes.

- **Request row:** `room_broadcast` with `topic: "inquiries"`. The `text` is the envelope (below). `evidence_refs` may cite the review target as `commit:<sha>`.
- **Result row:** `room_broadcast` with `reply_to` set to the request row's seq. The `text` is the result envelope.
- **Envelope:** the `text` is exactly `xhr/0.1 ` followed by one JSON object valid against `cross-harness-request.schema.json`. The room caps text at 4096 bytes, so the envelope carries a summary and a digest of the full answer, not the answer itself. The requester saves the full answer in its own workspace and names the path. The schema's length limits count characters, so the requester also checks that the whole text fits in 4096 UTF-8 bytes, and shortens the summary if it does not. With ASCII text, the largest valid result envelope is about 2.2 KB.
- The requester posts both rows. The result row reports what the requester observed (session id, turn id, turn status); it is not the recipient's statement. A recipient that has the room's tools may post its own reply in the same thread.

## Delivery to Codex

Through Codex's app-server protocol, JSON-RPC, reached with `codex app-server proxy` (standard input and output to the running daemon's control socket). Method and field names are those of the protocol schema that `codex app-server generate-json-schema` produced on 2026-10-14.

1. **Connect.** If the daemon is not running: for an existing session the outcome is `undeliverable`; the requester does not start the operator's daemon. For a new session it may run a private `codex app-server --listen stdio://`.
2. **Check the target.** `thread/read` for the thread. Deliver only if its status is `idle`. `active` gives `busy`; `notLoaded` gives `undeliverable` for version 0.1; `systemError` gives `failed`. Nothing is delivered in those cases.
3. **Deliver.** `turn/start` with:
   - `threadId`;
   - `input`: the review instructions as text;
   - `sandboxPolicy` read-only;
   - `approvalPolicy: "never"` and `approvalsReviewer: "user"`;
   - `clientUserMessageId` set to the `request_id`.

   Not `review/start` in version 0.1: it takes no sandbox or approval settings, so the review would run with whatever the session already allows.
4. **Wait.** For the `turn/completed` notification whose turn id matches. Turn status `completed` gives `completed`, with the final agent message as the answer. `failed` gives `failed`; `interrupted` gives `cancelled` or `timed_out`, as the requester caused.
5. **Refuse every approval request.** If the server asks the requester to approve anything (`item/commandExecution/requestApproval`, `item/fileChange/requestApproval`, `item/permissions/requestApproval`, `mcpServer/elicitation/request`, or any other), the requester answers with that request's refusal (`decline`, `deny` or `cancel`) and counts it. Its approval handler has no code path that can accept.
6. **Time out.** On `timeout_seconds` without an outcome: `turn/interrupt`, then outcome `timed_out`.
7. **Never redeliver blind.** If the connection drops after `turn/start` was sent and before an outcome, the outcome is `failed` with the error "delivery state unknown". The requester does not retry; the operator decides.
8. **No duplicates.** Before delivering, the requester reads the room's `inquiries` topic. If a request row with this `request_id` already exists, it does not deliver again.

## Continuity

ADR-21 D5, applied to Codex: the request goes into the existing thread, by `turn/start`, only while the thread is idle. History is never copied into a new session. Apart from the per-turn sandbox and approval settings above, the requester changes nothing about the session.

Whether those per-turn settings stay on the thread afterwards is not known; see Q2. Until that is answered, the requester records the thread's settings before and after, and the result row reports any difference.

## Acceptance for the proof

Each is shown by a recorded run or a test, with the room rows to match.

1. **Happy path.** From a running Claude session, a review request to an idle Codex session returns `completed` with an answer. Two room rows share the `request_id` and are linked by `reply_to`. The Codex session's history shows the turn, and its settings afterwards equal those before, or the difference is recorded.
2. **Busy.** A target whose status is `active` gives `busy`, and its turn count does not change.
3. **No route.** With the daemon unreachable, the outcome is `undeliverable` and nothing is delivered.
4. **Duplicate.** Running the same `request_id` twice delivers once.
5. **Refused approval.** Against a stand-in server that raises each kind of approval request, the requester refuses every one and the result row counts them. Covered by tests; no real session is asked to request approval.
6. **Timeout.** A short timeout sends `turn/interrupt`, the turn ends `interrupted`, and the outcome is `timed_out`.
7. **No approval path.** No requester code path accepts an approval, and no tool offered to any agent can approve for another agent's session. Shown by test and by review.

## Open questions to probe before building

All of these touch real Codex sessions. Probe them on a new throwaway session first, never on one of the operator's sessions without asking.

- **Q1.** Does a session open in the Codex desktop app live on the shared app-server daemon, so that `thread/loaded/list` and `thread/read` see it?
- **Q2.** Do `turn/start`'s sandbox and approval settings apply only to that turn, or stay on the thread?
- **Q3.** What do `review/start`'s `delivery: "detached"` and `"inline"` do to the target thread?
- **Q4.** How does `codex queue` relate to `turn/start`: does a queued message wait until the thread is idle, and should version 0.2 prefer it?
- **Q5.** Who may connect to the daemon's control socket, and with what authentication? Any process that connects is offered the approval requests.
- **Q6.** What does the operator see in the Codex app while another client runs a turn in an open session?

## Falsifiers

Retire or revise if any of these happens:

- something is delivered because of a room post;
- the requester accepts an approval;
- a request reaches a thread that was not idle;
- the room rows and Codex's thread disagree about which turn answered which request;
- one request yields two turns;
- the requester changes a session setting without recording it.
