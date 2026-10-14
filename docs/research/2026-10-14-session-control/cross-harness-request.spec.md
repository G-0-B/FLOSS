# Cross-harness request, first proof (Claude asks Codex for a review)

```yaml
id: "cross-harness-request-spec"
version: "0.1.1-draft"
kind: "spec"
status: "Draft"
created: "2026-10-14"
truth_status: "Specified. Codex interface facts verified from its generated protocol schema and, for Q1 to Q5, by probes against throwaway threads (codex-cli 0.162.0-alpha.17.2, 2026-10-14); nothing built."
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

Two room rows record it: a request row before delivery, and a result row with the outcome. In mode `existing` version 0.1 writes only the request row and marks it delivered (see Delivery to Codex). `busy` and `undeliverable` mean nothing reached the recipient, and the result row says so.

## Room records

Both rows go to the v0.2 room through its ordinary tools; nothing in the room changes.

- **Request row:** `room_broadcast` with `topic: "inquiries"`. The `text` is the envelope (below). `evidence_refs` may cite the review target as `commit:<sha>`.
- **Result row:** `room_broadcast` with `reply_to` set to the request row's seq. The `text` is the result envelope.
- **Envelope:** the `text` is exactly `xhr/0.1 ` followed by one JSON object valid against `cross-harness-request.schema.json`. The room caps text at 4096 bytes, so the envelope carries a summary and a digest of the full answer, not the answer itself. The requester saves the full answer in its own workspace and names the path. The schema's length limits count characters, so the requester also checks that the whole text fits in 4096 UTF-8 bytes, and shortens the summary if it does not. With ASCII text, the largest valid result envelope is about 2.2 KB.
- The requester posts both rows. The result row reports what the requester observed (session id, turn id, turn status); it is not the recipient's statement. A recipient that has the room's tools may post its own reply in the same thread.

## Delivery to Codex

Revised 2026-10-14 after the probes in `probes-2026-10-14/`. Method and field names are those of the protocol schema that `codex app-server generate-json-schema` produced that day (desktop CLI `codex-cli 0.162.0-alpha.17.2`).

What the probes showed, and why the first draft's plan had to change:

- Another process sees every saved session as `notLoaded`, whether or not the desktop app is running it (Q1).
- `turn/start`'s sandbox and approval settings stay on the thread afterwards, silently (Q2).
- `review/start` with `detached` is refused for new threads; `inline` adds turns to the target's history (Q3).
- `codex queue` puts a message into a session that another process holds, and that process runs it (Q4).

So there are two modes, and they use different routes.

### Mode `new`: a session the requester creates (the first proof)

The requester runs its own `codex app-server` (standard input and output), with the room's checkout or the target worktree as `cwd`.

1. `thread/start` with `sandbox: "read-only"`, `approvalPolicy: "never"`, `approvalsReviewer: "user"`; name the thread after the `request_id` with `thread/name/set`.
2. `turn/start` with the review instructions as text input and `clientUserMessageId` set to the `request_id`. The settings are the thread's own from step 1, so changing them changes nobody else's session.
3. Wait for `turn/completed` with the matching turn id. Turn status `completed` gives `completed`, with the final agent message as the answer. `failed` gives `failed`; `interrupted` gives `cancelled` or `timed_out`, as the requester caused.
4. Refuse every approval or input request: `decline`, `deny` or `cancel` as the request accepts, or a JSON-RPC error for any other kind. Count them. The handler has no path that accepts.
5. Time out with `turn/interrupt`. Never redeliver when the outcome is unknown.
6. Archive the thread when the result row is written. Nothing is deleted.

### Mode `existing`: a session the operator already has

Only through `codex queue --thread <id> --message <text>`. The requester never calls `thread/resume`, `turn/start` or `review/start` on a session it did not create: the first makes a second host for it (Q1), the second rewrites its settings (Q2), the third adds review turns to its history (Q3).

- The session's own host runs the queued message, with the session's own settings. Any approval prompt goes to that session's own window, so approval stays with the operator (ADR-21 D3).
- The requester cannot make the work read-only. The request text says what is asked ("review only, do not edit") and the session decides.
- Whether the session is busy cannot be seen from outside (Q1). A queued message waits its turn by design, so there is no `busy` outcome in this mode.
- Getting the answer back is not solved yet. `codex queue` prints only the queued message id. Reading the result means reading that session's saved history for the turn that answered the message, which reads the operator's session. Version 0.1 therefore records `existing` requests as `delivered` with no result row until the operator chooses how results may be read.
- The operator names the sessions that may receive requests. Nothing is queued into a session that was not named.

## Continuity

ADR-21 D5, applied to Codex: a request reaches an existing session only by `codex queue`, never by resuming it elsewhere or by copying its history into a new session, and the requester changes none of its settings. In mode `new` there is no prior session to preserve.

## Acceptance for the proof

Each is shown by a recorded run or a test, with the room rows to match.

1. **Happy path, mode `new`.** From a running Claude session, a review request goes to a Codex thread the requester creates (read-only, approvals never) and returns `completed` with an answer. Two room rows share the `request_id` and are linked by `reply_to`. The thread is archived afterwards.
2. **Mode `existing`.** A request queued into a session the operator named appears in that session and is recorded as delivered. The requester's transcript shows no `thread/resume`, `turn/start` or `review/start` call for that session.
3. **No route.** If the Codex app-server cannot be started (mode `new`) or `codex queue` fails (mode `existing`), the outcome is `undeliverable` and nothing is delivered. `busy` does not arise for Codex in version 0.1: mode `new` uses a fresh thread, and a queued message waits by design.
4. **Duplicate.** Running the same `request_id` twice delivers once.
5. **Refused approval.** Against a stand-in server that raises each kind of approval request, the requester refuses every one and the result row counts them. Covered by tests; no real session is asked to request approval.
6. **Timeout.** A short timeout sends `turn/interrupt`, the turn ends `interrupted`, and the outcome is `timed_out`.
7. **No approval path.** No requester code path accepts an approval, and no tool offered to any agent can approve for another agent's session. Shown by test and by review.

## Probe results and what is still open

Q1 to Q5 were answered on 2026-10-14 against two throwaway threads, both archived: see `probes-2026-10-14/README.md`. Two facts beyond the questions:

- Q5: nothing authenticates a connecting process beyond its Windows user. Any process running as this user can list every Codex session, load any of them, and queue messages into any of them. That channel exists today, whatever FLOSS builds.
- Every new thread here was `paginated`.

Still open:

- **Q6.** What does the operator see in the Codex app while another client runs a turn in a session it has open? Needs the operator watching the app while it happens.
- **Q7.** How may the requester read the answer to a queued message in mode `existing` without reading more of the operator's session than that answer?

## Falsifiers

Retire or revise if any of these happens:

- something is delivered because of a room post;
- the requester accepts an approval;
- a request reaches a thread that was not idle;
- the room rows and Codex's thread disagree about which turn answered which request;
- one request yields two turns;
- the requester changes a session setting without recording it.
