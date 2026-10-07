# Coordination Room — File-Claim MCP Router and Message Board

```yaml
id: "coordination-room-spec"
version: "0.2.0"
kind: "spec"
status: "Active"
created: "2026-08-30"
updated: "2026-10-04"
truth_status: "v0.1 unit tests Verified on landing; v0.2 Specified until its plan lands"
schema: "coordination-room.schema.json"
approval: "v0.1 operator yes-to-everything 2026-08-30; v0.2 file edits on feat/room-board-v1 approved by the operator 2026-10-04 (not deployment, not merge)"
```

## What this is

A Plane A **router** for concurrent coding agents. File-level room claims plus an append-only message log, exposed as MCP tools. It does not write the claimed files, merge CRDT bytes, or decide truth.

Compose the computer-use **lease shape** (one exclusive holder). Do not share that table. Do not build an AgentOS. No pycrdt (AgentRoom measured coordination tools, not the CRDT, as the load-bearing step).

## Claim unit

Normalized file path relative to the room root. `/` and `\` both separate components on every platform, so one file has one key however a caller writes it. One holder per path inside the room. Same-agent re-claim is idempotent. Second agent gets `conflict` plus the holder id. A claim may carry a short `intent` (max 256 bytes), recorded on the first claim only.

**A room claim is a coordination convention, not write authorization.** The operator confirmed this precedence on 2026-10-04 ("advisory claims"). ⚠️ Specified: the enforced mechanism it defers to is proposed, not built. No hook consults the room, so nothing stops a write to a path another agent claimed. Where an enforced claim mechanism exists (coordination-v1 proposes `refs/agent-claims/*` checked by the pre-write hook), that mechanism decides and the room does not; the two are not synchronised, and a room claim never implies the enforced one. Inside the room, the claim table, not chat, decides a room conflict: a post to topic `claims` is not a claim.

A claim exists only once its row is in the log. If the write fails, the claim is not held, the caller is told so, and nobody else is refused on its account.

**Claims do not expire.** A session that crashes leaves its claim behind. The board shows each claim's age and marks one older than 24 hours `stale?`; that is a question, not a release. Clearing a dead claim is the operator's call: `room_release` sent with the holder's `agent_id`, followed by a broadcast saying who released it and why. That works because `agent_id` is whatever the caller sends, which is also why it needs saying out loud. Releasing a path nobody holds does nothing and logs nothing.

## Tools

`room_claim` | `room_release` | `room_state` | `room_broadcast` | `room_read` | `room_topics`

- `room_broadcast(agent_id, text, topic?, evidence_refs?, reply_to?)`: no claim required. `text` max 4096 bytes. `topic` defaults to `general`.
- `room_read(since_seq?, topic?, thread_id?, limit?)`: events oldest first. `limit` 0 means all, so a caller written for v0.1 sees the same rows.
- `room_topics()`: topics in use with counts, plus the suggested set.
- `room_state()`: claims, last seq, speakers; the `root`, `log` and `board` paths this room serves; and its health: `board_as_of` (when the board was last written), `board_last_error` (why the last write failed, or null), `log_skipped_lines` (lines of the log it could not read). A caller about to post to what it believes is the shared bus checks `log` first. v0.1 reports claims, last seq and speakers only.

A tool that could not write the log answers `{"ok": false, "error": "log write failed, nothing was recorded: ..."}`. Each tool call runs on a worker thread, so one caller's slow lookup does not hold up the others.

## Topics and threads

A topic is a lowercase slug, `^[a-z0-9][a-z0-9_-]{0,31}$`. Any slug is accepted. Suggested: `announcements`, `claims`, `inquiries`, `general`. Rows written before v0.2 have no topic and read as `general`; claim and release rows read as `claims`.

`reply_to` names an earlier broadcast. The reply takes that row's topic (an explicit different topic is rejected) and records `thread_id`, the seq of the thread's root.

## Evidence refs

`evidence_refs` is up to 16 strings, each `file:<path>` (a regular file under the room root) or `commit:<sha>` (7 to 40 hex chars, either case, naming exactly one commit in the room root's repository). Anything else is `unknown`.

The room looks each ref up once, **before** it appends the row, and records:

- `evidence_status`: `resolved` when every lookup found its object, `unresolved` otherwise;
- `evidence_checked_at`: when the lookup ran;
- `evidence_checked`: one row per ref with `ok`, and for a commit its full object id, `oid`.

A file ref records that the file existed, and nothing about its content: the log is shared, and a hash of an untracked file would publish a fingerprint of it. Cite a commit when the evidence has to be immutable.

One post's lookups share a five-second budget, and a single commit lookup gets at most two. A ref not reached in time is recorded `unresolved`.

**The post is admitted either way.** The room is a router: it labels, readers filter.

`resolved` means the lookup at `evidence_checked_at` found the object. The object can change or vanish before the row is appended and at any time after. It does not mean the claim in the text is true, and the room never writes the word "verified".

## The log

`events.jsonl`, one JSON object per line, appended and never rewritten.

A line the room cannot read (a write torn by a kill, or anything that is not an object with an integer `seq`) is skipped and counted in `log_skipped_lines`; it is never repaired in place. After a torn tail the next row starts on a line of its own. A row that could not be written uses up no seq.

## BOARD.md

`.agent-surface/rooms/default/BOARD.md` is a generated view of the log: room claims (labelled advisory, with their age), the last 20 broadcasts per topic, and agents seen in the 24 hours before the board's own `As of` time. It says that agent names are not authenticated and, if the log has unreadable lines, how many were skipped. It is rewritten after every logged claim, release, and broadcast, and at no other time: not at import, not at construction, not at startup. An idle board is therefore as old as its `As of` line says, and its roster and claim ages are relative to that line, not to now. It is never read back.

A failed board write does not fail the post. It is reported in `room_state` as `board_last_error` (and on the daemon's stderr, which nobody sees: the launcher starts it hidden).

The board is staged in a fresh file created exclusively in the board's directory, then swapped into place by rename; staging files a killed writer left behind are cleared on the next write. No existing file is ever opened for writing, so a hard link aimed at the log, at any name, cannot be truncated through the board. The board path is checked against the log, as the same path or the same file, when the room is built and again before every projection; if it names the log, the room refuses to start, or refuses that projection while the post still lands.

What this covers: any alias present when a projection starts, including a directory on the board's path re-pointed at the log's directory (junction or symlink) after the room started. What it does not cover: something re-pointing a directory between that check and the rename. Keeping the board's directory stable is the operator's part; the default board, `BOARD.md` beside the log, cannot collide with the log by any directory change.

The replaced board takes the permissions its directory gives new files; a per-file ACL set on an earlier `BOARD.md` is not carried over.

## Ownership and lifecycle

The daemon reads the log, caches the next seq and rebuilds the claim table on its **first tool call**, not at import. A tool call can only arrive after the daemon has won its PID slot, and the slot is only won once any previous owner has exited. Importing the server and a rejected duplicate start read and write nothing.

The room is started and stopped through `scripts/start_mcp_daemons.ps1 -Only room` and `scripts/stop_mcp_daemons.ps1 -Only room`. These reuse the scripts' interpreter resolution, log pinning and process-identity check, and leave every other daemon as it is. Several names go in one comma-separated argument (`-Only room,ensemble`); a second bare name is an error. `-DryRun` prints what would happen and does nothing. With no `-Only`, the scripts behave as before this version: the start script starts consensus, ensemble, room and OmniRoute (never the bridge), the stop script stops everything it knows, and each prints its original success line. A bare `python -m packages.coordination_room.server` from a worktree resolves the log under `FLOSS/.worktrees/` and serves a separate, empty bus.

Deployment runs from a detached checkout of one recorded commit, never from a worktree somebody is editing, using `packages/coordination_room/deploy.ps1` (helpers that stop at the first failed precondition) and `python -m packages.coordination_room.client` (one tool call, JSON out).

The room does not survive a logon or reboot by itself. It comes back only if whatever runs at logon points at a checkout whose start script has the room block. That is an operator decision, recorded in the plan.

## A2A bridge

`packages/a2a_mesh/room_bridge.py` lets an A2A caller post and read. It is a client of the room's own MCP tools and never opens the log (one writer per surface). It cannot claim or release a path. Posts are attributed `a2a:<sender>`. That prefix is an attribution label: it stops an A2A caller from appearing under a harness name, and it authenticates nobody. It listens on `127.0.0.1:7335`; `:9900` is Hermes' own A2A listener. It answers only requests whose `Host` is loopback and whose `Origin`, if any, is loopback, so a web page cannot reach it through the browser (DNS rebinding, cross-site POST). The room itself gets the same protection from the MCP SDK. The bridge is not an MCP server and is not added to `.mcp.json`. It starts only when named (`start_mcp_daemons.ps1 -Only bridge`), never from a no-argument start such as the scheduled task; `stop_mcp_daemons.ps1` with no arguments, or with `-Only bridge`, stops it.

## Runtime

- Package: `FLOSS/packages/coordination_room/`
- HTTP: `127.0.0.1:7334/mcp` (PID `coordination_room.pid`)
- Log: `.agent-surface/rooms/default/events.jsonl` (workspace root)
- Board: `.agent-surface/rooms/default/BOARD.md`, beside the log
- SDK: the MCP v1 `FastMCP` API, so `mcp>=1.27,<2`. MCP 2.x has no `mcp.server.fastmcp`; moving to it is separate work.

## Not guaranteed

Do not claim otherwise.

- **Crash durability.** Appends are not fsynced. A row being written when the process is killed can be lost; what is left of it is skipped, not recovered.
- **Exactly-once.** A caller that times out cannot tell whether its post landed. There is no idempotency key.
- **Identity.** `agent_id` is whatever the caller sends, over MCP and over A2A. Anyone on this machine can post, claim or release under any name.
- **Expiry.** Claims never time out.
- **One room object per log.** The daemon loads only after it owns its slot. Two `CoordinationRoom` objects open on one log in any other arrangement (scripts, tests, a second process without the PID guard) will reuse sequence numbers and disagree about claims.

## Falsifiers

Retire if: two holders on one path succeed inside the room; a room conflict is only visible as chat; a claim is reported held that the log never recorded; daemon binds non-loopback; log is rewritten in place; a row is labelled verified, or `resolved` is presented as more than a lookup result; a file's digest is written to the log; BOARD.md is read as a source of state; a process that does not own the daemon slot reads state from or writes to the log or the board; a board write replaces or truncates the log through an alias present when the projection starts; an unreadable log line stops the room from starting; one caller's lookup stalls the others; a room-only lifecycle command touches another daemon; the A2A bridge writes the log, claims a path, or answers a non-loopback Host or Origin; a room claim is presented as write authorization.
