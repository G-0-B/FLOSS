# Codex session-protocol probes, 2026-10-14

Run at the operator's request ("yes run the probes on a throwaway session") to answer the open questions Q1 to Q6 of `../cross-harness-request.spec.md`. Author receipts, not a review.

`codex_probe.py` starts its own `codex app-server` (desktop CLI `codex-cli 0.162.0-alpha.17.2`) in a temporary git repository. It creates one new thread, names it "FLOSS throwaway probe 2026-10-14 (safe to archive)", runs at most three one-word turns, refuses every approval or input request, and archives the thread when done. It never resumed, read or wrote any other session. Thread listings are logged as counts only: no titles, previews, names, paths or working directories.

- `run1/`: Q1 and Q2; Q3 stopped the run (see below). Thread `01a1391e-4007-71a3-af98-f32315923856`, archived.
- `run2/`: Q3 (detached, then inline) and Q4. Thread `01a1391f-480e-74b3-bcda-399a6a199ea5`, archived.

Each holds `summary.json`, `transcript.jsonl` (every JSON-RPC message, listings redacted) and `server-stderr.txt`. The model was `gpt-6.1-sol` (the account default). No approval requests arrived, so none were refused.

## Answers

| Question | Answer | Evidence |
|---|---|---|
| **Q1.** Can another process see the desktop app's sessions? | It sees all of them (50 on the first page, more pages), originator "Codex Desktop", every one reported `notLoaded`. A session the desktop app is running looks the same as one nobody has open. A second process could `thread/resume` any of them and become a second host for it. | run1 `q1` |
| **Q2.** Do `turn/start`'s sandbox and approval settings apply only to that turn? | No. A thread started with workspace-write and on-request reported read-only and never after one turn that asked for those. No `thread/settings/updated` notification was sent. | run1 `q2` |
| **Q3.** What do `review/start`'s deliveries do? | `detached` is refused for new threads: "paginated threads do not support detached review" (every new thread here was `paginated`). `inline` runs in the target thread and adds turns to its history (0 to 2). | run1 error, run2 `q3` |
| **Q4.** How does `codex queue` relate to a running thread? | A separate `codex queue` process queued a message for a thread that another app-server (the probe's) had loaded and idle. That server started a turn on its own and completed it ("QUEUED"). No `thread/queue/changed` notification reached it. | run2 `q4` |
| **Q5.** Who may connect, with what authentication? | Nothing beyond being the same Windows user: a plain stdio app-server listed every session, could have resumed any of them, and `codex queue` delivered without a token. A named pipe `codex-ipc` exists; it was not opened. | Q1 and Q4 above; pipe listing |
| **Q6.** What does the operator see in the Codex app while another client runs a turn? | Not answered: needs someone looking at the app while it happens. | |

## What follows for the draft spec

- Delivering into an **existing** session cannot use `thread/resume`, `turn/start` or `review/start` from outside. Resume makes a second host (Q1); the per-turn settings would rewrite the operator's session settings (Q2); a review adds turns to its history (Q3).
- `codex queue` is the native way to put a request into an existing session (Q4). The session's own host runs it with the session's own settings, and any approval prompt goes to that session's own window. That is what ADR-21 D3 asks for. The requester cannot make it read-only, so the request is a proposal the operator's session decides on.
- A **new** session the requester creates itself can use `turn/start` with read-only and never: nobody else's settings change. That is the cleanest first proof.
- Any process running as this Windows user can already read every Codex session and queue messages into any of them (Q5). That channel exists today, whatever FLOSS builds.

Side note: the probe's server warned that `~/.codex/config.toml` has 9 settings Codex ignores (`mcp_servers.*.type`), most likely written by the shared agent surface. They do nothing.
